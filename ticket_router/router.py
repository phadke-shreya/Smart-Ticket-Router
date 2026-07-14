from pydantic import ValidationError

from ticket_router.llm_client import call_llm, LLMCallError, MalformedResponseError
from ticket_router.schema import LLMTicketOutputList, build_ticket_result

MAX_VALIDATION_RETRIES = 2

_cache: dict[str, list[dict]] = {}


class TicketRoutingError(Exception):
    """Raised when a ticket cannot be classified, even after all retries."""


def clear_cache() -> None:
    """Clears the in-memory result cache. Mainly used by tests to avoid cross-test pollution."""
    _cache.clear()


def classify_ticket(ticket_text: str) -> list[dict]:
    """
    Reusable service function: given raw support ticket text, returns a LIST
    of one or more classified issues (each with category, priority, team,
    reasoning). A single-issue ticket returns a list with one item; a ticket
    mixing genuinely separate issues can return multiple items, each routed
    to its own team.

    Identical ticket text (exact match) returns the cached result instantly.

    Raises TicketRoutingError if classification fails after all retries.
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
            parsed = LLMTicketOutputList(**raw_response)
        except ValidationError as exc:
            last_error = exc
            continue  # got JSON back, but wrong shape/values — ask the LLM again

        results = [build_ticket_result(item).model_dump() for item in parsed.tickets]
        _cache[normalized] = results
        return results

    raise TicketRoutingError(
        f"LLM returned invalid ticket data after {MAX_VALIDATION_RETRIES} attempts: {last_error}"
    )
