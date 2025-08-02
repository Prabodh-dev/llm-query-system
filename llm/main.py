from chunk_and_embed import load_pdf_clauses
from openai_chain import run_openai_chain

query = "What is the procedure for filing a claim in case of accidental damage?"
clauses = load_pdf_clauses("insurance_policy.pdf")  # replace with your file

response = run_openai_chain(query, clauses)
print("\n🔹 Response:\n", response)
