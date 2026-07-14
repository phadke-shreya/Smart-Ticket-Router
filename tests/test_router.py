import pytest
from pydantic import ValidationError

from ticket_router.schema import LLMTicketOutput, build_ticket_result, CATEGORY_TEAM_MAP
from ticket_router.llm_client import LLMCallError, MalformedResponseError
from ticket_router.router import classify_ticket, TicketRoutingError
import ticket_router.router as router_module


@pytest.fixture(autouse=True)
def _clear_router_cache():
    router_module.clear_cache()
    yield
    router_module.clear_cache()


def test_valid_llm_output_builds_correct_team():
    output = LLMTicketOutput(category="Shipping", priority="Medium", reasoning="Delivery delay reported.")
    result = build_ticket_result(output)
    assert result.team == CATEGORY_TEAM_MAP["Shipping"]
    assert result.category == "Shipping"
    assert result.priority == "Medium"


def test_invalid_category_is_rejected():
    with pytest.raises(ValidationError):
        LLMTicketOutput(category="Delivery Issue", priority="Medium", reasoning="not a real category")


def test_invalid_priority_is_rejected():
    with pytest.raises(ValidationError):
        LLMTicketOutput(category="Shipping", priority="Urgent", reasoning="not a real priority")


VALID_RESPONSE = {
    "category": "Payments",
    "priority": "High",
    "reasoning": "Customer was charged but the order failed.",
}

INVALID_CATEGORY_RESPONSE = {
    "category": "Not A Real Category",
    "priority": "High",
    "reasoning": "bad category",
}


def test_classify_ticket_success(monkeypatch):
    monkeypatch.setattr(router_module, "call_llm", lambda text: VALID_RESPONSE)
    result = classify_ticket("I was charged but my order never went through.")
    assert result["category"] == "Payments"
    assert result["team"] == "Finance"
    assert result["priority"] == "High"


def test_classify_ticket_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}

    def fake_call_llm(text):
        calls["count"] += 1
        return INVALID_CATEGORY_RESPONSE if calls["count"] == 1 else VALID_RESPONSE

    monkeypatch.setattr(router_module, "call_llm", fake_call_llm)
    result = classify_ticket("some ticket")
    assert calls["count"] == 2
    assert result["category"] == "Payments"


def test_classify_ticket_raises_after_max_schema_retries(monkeypatch):
    monkeypatch.setattr(router_module, "call_llm", lambda text: INVALID_CATEGORY_RESPONSE)
    with pytest.raises(TicketRoutingError):
        classify_ticket("some ticket")


def test_classify_ticket_wraps_llm_call_error(monkeypatch):
    def raise_error(text):
        raise LLMCallError("simulated API failure")

    monkeypatch.setattr(router_module, "call_llm", raise_error)
    with pytest.raises(TicketRoutingError):
        classify_ticket("some ticket")


def test_classify_ticket_wraps_malformed_response_error(monkeypatch):
    def raise_error(text):
        raise MalformedResponseError("simulated bad JSON")

    monkeypatch.setattr(router_module, "call_llm", raise_error)
    with pytest.raises(TicketRoutingError):
        classify_ticket("some ticket")


def test_classify_ticket_rejects_empty_text():
    with pytest.raises(TicketRoutingError):
        classify_ticket("   ")
