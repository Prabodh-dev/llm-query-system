from PyPDF2 import PdfReader
from schemas import Clause

def load_pdf_clauses(pdf_path: str) -> list[Clause]:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    raw_clauses = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 30]
    clauses = [Clause(clause_text=clause) for clause in raw_clauses]
    return clauses