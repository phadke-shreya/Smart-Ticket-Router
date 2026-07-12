from pydantic import ValidationError

from ticket_router.llm_client import call_llm, LLMCallError, MalformedResponseError
from ticket_router.schema import LLMTicketOutput, TicketResult, build_ticket_result

MAX_VALIDATION_RETRIES = 2


class TicketRoutingError(Exception):
    """Raised when a ticket cannot be classified, even after all retries."""


def classify_ticket(ticket_text: str) -> dict:
    """
    Reusable service function: given raw support ticket text, returns a dict
    with category, priority, team, and reasoning.

    Raises TicketRoutingError if classification fails after all retries —
    callers (the web form, a CLI, tests) are expected to catch this and
    show an error to the user.
    """
    if not ticket_text or not ticket_text.strip():
        raise TicketRoutingError("Ticket text is empty.")

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
        return result.model_dump()

    raise TicketRoutingError(
        f"LLM returned invalid category/priority values after {MAX_VALIDATION_RETRIES} attempts: {last_error}"
    )
