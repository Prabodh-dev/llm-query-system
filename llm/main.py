from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import shutil
from schemas import OutputAnswer, Clause
from chunk_and_embed import load_pdf_clauses
from gemini_chain import   run_gemini_chain
import os

app = FastAPI()

@app.post("/generate")
async def generate(file: UploadFile, query: str = Form(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        clauses = load_pdf_clauses(temp_path)
        os.remove(temp_path)

        answers = run_gemini_chain(query, clauses)

        return {
            "answers": answers,
            "relevant_clauses": [c.dict() for c in clauses]
        }

    except Exception as e:
        return JSONResponse(content={"answers": [f"LLM error: {str(e)}"]}, status_code=500)
