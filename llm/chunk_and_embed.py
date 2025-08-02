from PyPDF2 import PdfReader
from schemas import Clause

def load_pdf_clauses(pdf_path: str) -> list[Clause]:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    # Naive chunking: every paragraph as one clause
    raw_clauses = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 30]
    clauses = [Clause(title=f"Clause {i+1}", content=clause) for i, clause in enumerate(raw_clauses)]
    return clauses
