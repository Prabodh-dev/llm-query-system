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
        # Parse JSON body safely
        try:
            body = await request.json()
            print("✅ Received JSON:", body)
        except Exception as json_error:
            print("❌ Invalid JSON body:", str(json_error))
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid JSON format",
                    "details": str(json_error)
                }
            )

        pdf_url = body.get("documents")
        questions = body.get("questions")

        print("📄 Document URL:", pdf_url)
        print("❓ Questions:", questions)

        if not pdf_url or not questions:
            return JSONResponse(status_code=400, content={"error": "Missing documents or questions"})

        # Download PDF
        print("🌐 Downloading PDF from:", pdf_url)
        pdf_response = requests.get(pdf_url)
        print("📥 PDF Status Code:", pdf_response.status_code)

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

        # ✅ FINAL RESPONSE FORMAT
        return JSONResponse(
            status_code=200,
            content={
                "answers": answers
            }
        )

    except Exception as e:
        print("❌ Error in /generate:", str(e))
        return JSONResponse(
            content={"answers": [f"LLM error: {str(e)}"]},
            status_code=500
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
