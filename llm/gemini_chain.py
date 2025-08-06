import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from typing import List
from schemas import Clause

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def run_gemini_chain(questions: List[str], clauses: List[Clause]) -> List[str]:
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")

        # Prepare context from clause text
        context = "\n\n".join([c.clause_text for c in clauses])
        question_str = "\n".join(questions)

        # Medium 1–2 line answers prompt
        prompt = (
            "You are a document assistant. Based on the insurance policy clauses below, "
            "answer each user question in 1–2 lines. Be accurate, concise, and complete. "
            "Return a JSON array with one string per answer, preserving the order of questions. "
            "No extra labels or formatting.\n\n"
            f"Policy Clauses:\n{context}\n\n"
            f"Questions:\n{question_str}"
        )

        print(" Sending prompt to Gemini:\n", prompt[:500])
        response = model.generate_content(prompt)

        text = response.text.strip()
        print(" Gemini Raw Response:", text[:500])

        # Extract JSON array from model output
        start = text.find("[")
        end = text.rfind("]") + 1

        if start == -1 or end == -1:
            return [f"LLM error: Invalid output\n{text}"]

        return json.loads(text[start:end])

    except Exception as e:
        print(" Error in Gemini:", str(e))
        return [f"LLM error: {str(e)}"]
