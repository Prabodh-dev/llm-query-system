from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    documents: str = Field(..., min_length=1, max_length=2048, description="Public PDF URL")
    questions: list[str] = Field(..., min_length=1)

    @field_validator("questions")
    @classmethod
    def _strip_and_require_text(cls, value: list[str]) -> list[str]:
        cleaned = [q.strip() for q in value]
        if any(not q for q in cleaned):
            raise ValueError("questions must be non-empty strings")
        return cleaned


class GenerateResponse(BaseModel):
    answers: list[str]
