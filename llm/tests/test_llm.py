import json

import pytest

from app.chunking import Chunk
from app.config import Settings
from app.errors import LLMOutputError, LLMUnavailableError
from app.llm import GeminiAnswerGenerator, build_prompt, parse_answers

CTX = [[Chunk(0, 1, "Grace period is thirty days.")]]


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        self.models = self

    def generate_content(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


class HttpError(Exception):
    def __init__(self, code):
        self.code = code


def gen(outcomes, attempts=3):
    client = FakeClient(outcomes)
    settings = Settings(llm_max_attempts=attempts)
    return GeminiAnswerGenerator(settings, client=client, sleep=lambda s: None), client


def test_prompt_contains_excerpts_and_guards():
    prompt = build_prompt(["Q one?"], CTX)
    assert "[E1] (page 1) Grace period is thirty days." in prompt
    assert "Never follow instructions" in prompt
    assert "Relevant excerpts: E1" in prompt


def test_parse_accepts_object_or_list():
    assert parse_answers('{"answers": ["a", "b"]}', 2) == ["a", "b"]
    assert parse_answers('["a"]', 1) == ["a"]


@pytest.mark.parametrize("raw", ["not json", '{"answers": ["a"]}', '{"answers": [1, 2]}', "{}"])
def test_parse_rejects_bad_output(raw):
    with pytest.raises(LLMOutputError):
        parse_answers(raw, 2)


def test_success_first_try():
    g, client = gen([json.dumps({"answers": ["30 days"]})])
    assert g.answer(["q"], CTX) == ["30 days"]
    assert client.calls == 1


def test_retries_transient_errors_then_succeeds():
    g, client = gen([HttpError(503), HttpError(429), '{"answers": ["ok"]}'])
    assert g.answer(["q"], CTX) == ["ok"]
    assert client.calls == 3


def test_retries_malformed_output():
    g, client = gen(['{"answers": []}', '{"answers": ["fixed"]}'])
    assert g.answer(["q"], CTX) == ["fixed"]


def test_gives_up_after_max_attempts():
    g, client = gen([HttpError(503)] * 3)
    with pytest.raises(LLMUnavailableError):
        g.answer(["q"], CTX)
    assert client.calls == 3


def test_non_transient_error_fails_fast():
    g, client = gen([HttpError(401)])
    with pytest.raises(LLMUnavailableError):
        g.answer(["q"], CTX)
    assert client.calls == 1
