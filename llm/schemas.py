from pydantic import BaseModel, Field
from typing import List, Optional

class QueryInput(BaseModel):
    text: str = Field(..., description="The extracted and cleaned text from the file")
    query: str = Field(..., description="The user's search query")

class Clause(BaseModel):
    clause_id: Optional[str] = None
    clause_text: str
    confidence_score: Optional[float] = None

class OutputAnswer(BaseModel):
    answer_summary: str
    relevant_clauses: List[Clause]
    source_metadata: Optional[dict] = None
