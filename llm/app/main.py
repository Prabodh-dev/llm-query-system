"""FastAPI application: POST /generate answers questions about a PDF."""

from __future__ import annotations

import hmac
import json
import logging
import sys
import time
import uuid

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .chunking import chunk_pages
from .config import Settings
from .errors import AppError, UnauthorizedError
from .llm import AnswerGenerator, GeminiAnswerGenerator
from .pdf import Fetcher, download_pdf, extract_pages
from .retrieval import BM25Index
from .schemas import GenerateRequest, GenerateResponse
from .security import validate_public_url

log = logging.getLogger("llm.api")

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED})
        return json.dumps(payload, default=str)


def _configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


def create_app(
    settings: Settings | None = None,
    generator: AnswerGenerator | None = None,
    fetcher: Fetcher = download_pdf,
) -> FastAPI:
    load_dotenv()
    settings = settings or Settings.from_env()
    _configure_logging(settings.log_level)

    app = FastAPI(title="LLM Query System - Document QA", version="2.0.0")
    app.state.settings = settings
    app.state.generator = generator
    app.state.fetcher = fetcher

    def get_generator() -> AnswerGenerator:
        if app.state.generator is None:
            if not settings.google_api_key:
                raise AppError("GOOGLE_API_KEY is not configured")
            app.state.generator = GeminiAnswerGenerator(settings)
        return app.state.generator

    def require_token(request: Request) -> None:
        if not settings.service_token:
            return
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(
            token.encode(), settings.service_token.encode()
        ):
            raise UnauthorizedError("Unauthorized")

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": round((time.perf_counter() - started) * 1000),
            },
        )
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError):
        if exc.status_code >= 500:
            log.error("request failed", extra={"code": exc.code, "error": exc.message})
        return JSONResponse(
            status_code=exc.status_code, content={"error": exc.message, "code": exc.code}
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        message = f"Invalid request: {where} {first.get('msg', '')}".strip()
        return JSONResponse(status_code=400, content={"error": message, "code": "invalid_request"})

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        log.exception("unhandled error")
        return JSONResponse(
            status_code=500, content={"error": "Internal server error", "code": "internal_error"}
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Synchronous handler: FastAPI runs it in a worker thread, so blocking I/O
    # (PDF download, Gemini call) does not stall the event loop.
    @app.post("/generate", response_model=GenerateResponse, dependencies=[Depends(require_token)])
    def generate(body: GenerateRequest) -> GenerateResponse:
        if len(body.questions) > settings.max_questions:
            raise _too_many(settings.max_questions)
        if any(len(q) > settings.max_question_chars for q in body.questions):
            raise _too_long(settings.max_question_chars)

        validate_public_url(body.documents)
        pdf_bytes = app.state.fetcher(body.documents, settings)
        pages = extract_pages(pdf_bytes, settings)
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        index = BM25Index(chunks)
        contexts = [index.search(q, settings.top_k) for q in body.questions]

        answers = get_generator().answer(body.questions, contexts)
        log.info(
            "answered",
            extra={"questions": len(body.questions), "chunks": len(chunks), "pages": len(pages)},
        )
        return GenerateResponse(answers=answers)

    return app


class _BadRequest(AppError):
    status_code = 400
    code = "invalid_request"


def _too_many(limit: int) -> AppError:
    return _BadRequest(f"At most {limit} questions are allowed per request")


def _too_long(limit: int) -> AppError:
    return _BadRequest(f"Each question must be at most {limit} characters")


app = create_app()
