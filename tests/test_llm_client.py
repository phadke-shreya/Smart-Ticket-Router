import json
import pytest

from ticket_router import llm_client
from ticket_router.llm_client import call_llm, MalformedResponseError


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


def test_call_llm_returns_parsed_json_on_success(monkeypatch):
    valid_json = json.dumps({"category": "Shipping", "priority": "Medium", "reasoning": "delay"})
    monkeypatch.setattr(llm_client.client.chat.completions, "create", lambda **kwargs: FakeResponse(valid_json))

    result = call_llm("my package is late")
    assert result["category"] == "Shipping"


def test_call_llm_retries_on_malformed_json_then_succeeds(monkeypatch):
    calls = {"count": 0}
    valid_json = json.dumps({"category": "Shipping", "priority": "Medium", "reasoning": "delay"})

    def fake_create(**kwargs):
        calls["count"] += 1
        return FakeResponse("not valid json" if calls["count"] == 1 else valid_json)

    monkeypatch.setattr(llm_client.client.chat.completions, "create", fake_create)
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)  # skip real waiting in tests

    result = call_llm("my package is late")
    assert calls["count"] == 2
    assert result["category"] == "Shipping"


def test_call_llm_raises_after_max_retries_on_malformed_json(monkeypatch):
    monkeypatch.setattr(llm_client.client.chat.completions, "create", lambda **kwargs: FakeResponse("not valid json"))
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)

    with pytest.raises(MalformedResponseError):
        call_llm("my package is late")


def test_call_llm_raises_on_empty_response(monkeypatch):
    monkeypatch.setattr(llm_client.client.chat.completions, "create", lambda **kwargs: FakeResponse(""))
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)

    with pytest.raises(MalformedResponseError):
        call_llm("my package is late")
