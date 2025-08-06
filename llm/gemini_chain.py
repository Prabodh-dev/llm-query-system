import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def run_gemini_chain(query, clauses):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")

        context = "\n\n".join([c.clause_text for c in clauses])

        prompt = (
            "You are a document assistant. Based on the insurance policy clauses below, answer each user question clearly and concisely. "
            "Return a JSON array with one answer per question. "
            "Each answer must be a **single-line** string, even if long. "
            "Do not return extra text, explanation, or labels.\n\n"
            f"Policy Clauses:\n{context}\n\n"
            f"Questions:\n{query}"
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Try to extract JSON-like list from the model output
        import json
        start = text.find("[")
        end = text.rfind("]") + 1

        if start == -1 or end == -1:
            return [f"LLM error: Invalid output\n{text}"]

        return json.loads(text[start:end])

    except Exception as e:
        return [f"LLM error: {str(e)}"]
