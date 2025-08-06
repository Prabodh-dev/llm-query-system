from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os
import uvicorn
from tempfile import NamedTemporaryFile

from schemas import Clause
from chunk_and_embed import load_pdf_clauses
from gemini_chain import run_gemini_chain

app = FastAPI()

@app.post("/generate")
async def generate(request: Request):
    try:
        body = await request.json()
        pdf_url = body.get("documents")
        questions = body.get("questions")

        print("📥 Received request")
        print("📄 Document URL:", pdf_url)
        print("❓ Questions:", questions)

        if not pdf_url or not questions:
            return JSONResponse(status_code=400, content={"error": "Missing documents or questions"})

        # Download PDF
        pdf_response = requests.get(pdf_url)
        if pdf_response.status_code != 200:
            return JSONResponse(status_code=400, content={"error": "Unable to download PDF"})

        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_response.content)
            temp_path = tmp.name

        print("✅ PDF downloaded:", temp_path)

        # Extract clauses
        clauses = load_pdf_clauses(temp_path)
        os.remove(temp_path)

        print(f"🔍 Extracted {len(clauses)} clauses")

        # Run Gemini chain
        answers = run_gemini_chain(questions, clauses)

        print("✅ Gemini answers:", answers)

        return {
            "answers": answers,
            "relevant_clauses": [c.dict() for c in clauses]
        }

    except Exception as e:
        print("❌ Error in /generate:", str(e))
        return JSONResponse(content={"answers": [f"LLM error: {str(e)}"]}, status_code=500)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
