from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import LLMUnavailableError
from app.main import create_app

URL = "https://example.com/policy.pdf"


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_generate_returns_answers_in_order(client, generator):
    qs = ["What is the grace period?", "Is maternity covered?"]
    res = client.post("/generate", json={"documents": URL, "questions": qs})
    assert res.status_code == 200
    assert res.json() == {"answers": [f"answer to: {q}" for q in qs]}
    assert "x-request-id" in res.headers
    # retrieval fed the matching chunk to the model for the first question
    _, contexts = generator.calls[0]
    assert "thirty days" in contexts[0][0].text


def test_missing_fields_are_rejected(client):
    res = client.post("/generate", json={"documents": URL})
    assert res.status_code == 400
    assert res.json()["code"] == "invalid_request"


def test_blank_question_rejected(client):
    res = client.post("/generate", json={"documents": URL, "questions": ["  "]})
    assert res.status_code == 400


def test_too_many_questions_rejected(client):
    res = client.post("/generate", json={"documents": URL, "questions": ["q"] * 51})
    assert res.status_code == 400


def test_non_pdf_is_422(settings, generator):
    app = create_app(settings, generator=generator, fetcher=lambda u, s: b"<html></html>")
    import app.main as m

    m.validate_public_url, orig = (lambda u: None), m.validate_public_url
    try:
        res = TestClient(app).post("/generate", json={"documents": URL, "questions": ["q"]})
    finally:
        m.validate_public_url = orig
    assert res.status_code == 422
    assert res.json()["code"] == "invalid_document"


def test_private_url_blocked(settings, generator):
    app = create_app(settings, generator=generator)
    res = TestClient(app).post(
        "/generate", json={"documents": "http://127.0.0.1:8000/x.pdf", "questions": ["q"]}
    )
    assert res.status_code == 400
    assert res.json()["code"] == "unsafe_url"


def test_llm_failure_is_502_not_200(client, generator):
    def boom(q, c):
        raise LLMUnavailableError("The language model request failed")

    generator.answer = boom
    res = client.post("/generate", json={"documents": URL, "questions": ["q"]})
    assert res.status_code == 502
    assert res.json()["code"] == "llm_unavailable"


def test_service_token_enforced(generator):
    settings = Settings(service_token="s3cret", log_level="WARNING")
    app = create_app(settings, generator=generator)
    c = TestClient(app)
    body = {"documents": URL, "questions": ["q"]}
    assert c.post("/generate", json=body).status_code == 401
    assert c.post("/generate", json=body, headers={"Authorization": "Bearer nope"}).status_code == 401
    assert c.get("/health").status_code == 200
