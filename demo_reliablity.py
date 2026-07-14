from unittest.mock import patch

from ticket_router.router import classify_ticket, TicketRoutingError, clear_cache
from ticket_router.llm_client import LLMCallError, MalformedResponseError
import ticket_router.router as router_module


def demo_retry_then_succeed():
    print("\n--- DEMO 1: LLM returns an invalid category once, then succeeds on retry ---")
    clear_cache()
    calls = {"count": 0}

    def flaky_call_llm(ticket_text):
        calls["count"] += 1
        if calls["count"] == 1:
            print("  Attempt 1: LLM returned an invalid category ('Delivery Issue') -> validation fails, retrying...")
            return {"category": "Delivery Issue", "priority": "Medium", "reasoning": "bad"}
        print("  Attempt 2: LLM returned a valid response.")
        return {"category": "Shipping", "priority": "Medium", "reasoning": "Delivery delay reported."}

    with patch.object(router_module, "call_llm", flaky_call_llm):
        result = classify_ticket("My package is late.")
    print(f"  Final result: {result}")


def demo_max_retries_exceeded():
    print("\n--- DEMO 2: LLM keeps returning invalid values -> gives up after max retries ---")
    clear_cache()

    def always_invalid(ticket_text):
        return {"category": "Not A Real Category", "priority": "High", "reasoning": "bad"}

    with patch.object(router_module, "call_llm", always_invalid):
        try:
            classify_ticket("Some ticket that keeps failing validation.")
        except TicketRoutingError as exc:
            print(f"  Gave up after max retries, returned a clean error instead of crashing: {exc}")


def demo_api_failure():
    print("\n--- DEMO 3: the OpenAI API itself fails (e.g. network issue / rate limit) ---")
    clear_cache()

    def raise_api_error(ticket_text):
        raise LLMCallError("Simulated: OpenAI API unreachable after 3 attempts")

    with patch.object(router_module, "call_llm", raise_api_error):
        try:
            classify_ticket("Any ticket text.")
        except TicketRoutingError as exc:
            print(f"  Caught the API failure, returned a clean error instead of crashing: {exc}")


def demo_malformed_json():
    print("\n--- DEMO 4: LLM returns unparseable text repeatedly ---")
    clear_cache()

    def raise_malformed(ticket_text):
        raise MalformedResponseError("Simulated: LLM returned unparseable text 3 times in a row")

    with patch.object(router_module, "call_llm", raise_malformed):
        try:
            classify_ticket("Any ticket text.")
        except TicketRoutingError as exc:
            print(f"  Caught the malformed JSON failure, returned a clean error instead of crashing: {exc}")


if __name__ == "__main__":
    demo_retry_then_succeed()
    demo_max_retries_exceeded()
    demo_api_failure()
    demo_malformed_json()
    print("\nAll reliability scenarios demonstrated without touching the real OpenAI API.\n")
