"""Application errors, each carrying the HTTP status it maps to."""

from __future__ import annotations


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UnsafeURLError(AppError):
    status_code = 400
    code = "unsafe_url"


class DocumentFetchError(AppError):
    status_code = 400
    code = "document_fetch_failed"


class DocumentTooLargeError(AppError):
    status_code = 413
    code = "document_too_large"


class InvalidDocumentError(AppError):
    status_code = 422
    code = "invalid_document"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class LLMUnavailableError(AppError):
    status_code = 502
    code = "llm_unavailable"


class LLMTimeoutError(AppError):
    status_code = 504
    code = "llm_timeout"


class LLMOutputError(AppError):
    status_code = 502
    code = "llm_invalid_output"
