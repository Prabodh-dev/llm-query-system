from pydantic import BaseModel
from typing import List

class Clause(BaseModel):
    title: str
    content: str
