from PyPDF2 import PdfReader
from schemas import Clause

def load_pdf_clauses(pdf_path: str) -> list[Clause]:
    reader = PdfReader(pdf_path)
    clauses = []

    clause_id = 1
    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue

        # Split line-by-line and filter junk
        for line in text.split("\n"):
            clean_line = line.strip()
            if len(clean_line) > 30: 
                clauses.append(Clause(clause_id=str(clause_id), clause_text=clean_line))
                clause_id += 1

    print(f"🧾 Total Clauses Extracted: {len(clauses)}")
    return clauses
