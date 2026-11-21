"""Runtime configuration, read once from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int(env: dict, key: str, default: int) -> int:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{key} must be positive, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    service_token: str = ""

    max_pdf_bytes: int = 25 * 1024 * 1024
    max_pdf_pages: int = 500
    max_redirects: int = 3
    download_timeout_s: int = 30

    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 5

    max_questions: int = 50
    max_question_chars: int = 1000

    llm_timeout_s: int = 90
    llm_max_attempts: int = 3

    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env: dict | None = None) -> "Settings":
        env = dict(os.environ if env is None else env)
        return cls(
            google_api_key=env.get("GOOGLE_API_KEY", ""),
            gemini_model=env.get("GEMINI_MODEL") or cls.gemini_model,
            service_token=env.get("LLM_SERVICE_TOKEN", ""),
            max_pdf_bytes=_int(env, "MAX_PDF_BYTES", cls.max_pdf_bytes),
            max_pdf_pages=_int(env, "MAX_PDF_PAGES", cls.max_pdf_pages),
            max_redirects=_int(env, "MAX_REDIRECTS", cls.max_redirects),
            download_timeout_s=_int(env, "DOWNLOAD_TIMEOUT_S", cls.download_timeout_s),
            chunk_size=_int(env, "CHUNK_SIZE", cls.chunk_size),
            chunk_overlap=_int(env, "CHUNK_OVERLAP", cls.chunk_overlap),
            top_k=_int(env, "TOP_K", cls.top_k),
            max_questions=_int(env, "MAX_QUESTIONS", cls.max_questions),
            max_question_chars=_int(env, "MAX_QUESTION_CHARS", cls.max_question_chars),
            llm_timeout_s=_int(env, "LLM_TIMEOUT_S", cls.llm_timeout_s),
            llm_max_attempts=_int(env, "LLM_MAX_ATTEMPTS", cls.llm_max_attempts),
            log_level=(env.get("LOG_LEVEL") or "INFO").upper(),
        )
