import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def run_openai_chain(query, clauses):
    context = "\n\n".join([f"{c.title}: {c.content}" for c in clauses])
    prompt = f"Answer the following query using the insurance clauses below:\n\n{context}\n\nQuery: {query}"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content

'''
def run_openai_chain(query, clauses):
    print("DEBUG - Clause object contents:", clauses)
    prompt = f"Query: {query}\n\nRelevant Policy Clauses:\n" + "\n".join([clause.content for clause in clauses])
    # 🧪 MOCKING RESPONSE
    return f"[MOCKED RESPONSE] Based on the clauses provided for: '{query}'"
'''