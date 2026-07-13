from pydantic import ValidationError

from ticket_router.llm_client import call_llm, LLMCallError, MalformedResponseError
from ticket_router.schema import LLMTicketOutput, TicketResult, build_ticket_result

MAX_VALIDATION_RETRIES = 2

_cache: dict[str, dict] = {}


class TicketRoutingError(Exception):
    """Raised when a ticket cannot be classified, even after all retries."""


def clear_cache() -> None:
    """Clears the in-memory result cache. Mainly used by tests to avoid cross-test pollution."""
    _cache.clear()


def classify_ticket(ticket_text: str) -> dict:
    """
    Reusable service function: given raw support ticket text, returns a dict
    with category, priority, team, and reasoning.

    Identical ticket text (exact match) returns the cached result instantly
    instead of calling the LLM again — guarantees the same ticket always
    gets the same answer, and saves an API call on repeats.

    Raises TicketRoutingError if classification fails after all retries —
    callers (the web form, a CLI, tests) are expected to catch this and
    show an error to the user.
    """
    if not ticket_text or not ticket_text.strip():
        raise TicketRoutingError("Ticket text is empty.")

    normalized = ticket_text.strip()

    if normalized in _cache:
        return _cache[normalized]

    last_error = None

    for attempt in range(1, MAX_VALIDATION_RETRIES + 1):
        try:
            raw_response = call_llm(ticket_text)
        except (LLMCallError, MalformedResponseError) as exc:
            raise TicketRoutingError(str(exc)) from exc

        try:
            llm_output = LLMTicketOutput(**raw_response)
        except ValidationError as exc:
            last_error = exc
            continue  # got JSON back, but wrong shape/values — ask the LLM again

        result: TicketResult = build_ticket_result(llm_output)
        _cache[normalized] = result.model_dump()
        return _cache[normalized]

    raise TicketRoutingError(
        f"LLM returned invalid category/priority values after {MAX_VALIDATION_RETRIES} attempts: {last_error}"
    )
