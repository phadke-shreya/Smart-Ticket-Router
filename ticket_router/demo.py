import json
import time

from ticket_router.router import classify_ticket, TicketRoutingError

MANUAL_SECONDS_PER_TICKET = 180  # assumption: ~3 minutes for a human agent to read, categorize,
                                  # decide priority, and route one ticket manually


def load_tickets(path="sample_tickets.json"):
    with open(path) as f:
        return json.load(f)


def run_timed_demo(tickets):
    """Runs classify_ticket() over all tickets, timing the batch. Returns (per_ticket_results, ai_elapsed_seconds)."""
    per_ticket_results = []
    start = time.perf_counter()
    for ticket in tickets:
        try:
            result = classify_ticket(ticket["text"])
            per_ticket_results.append({"id": ticket["id"], "text": ticket["text"], "result": result, "error": None})
        except TicketRoutingError as exc:
            per_ticket_results.append({"id": ticket["id"], "text": ticket["text"], "result": None, "error": str(exc)})
    ai_elapsed = time.perf_counter() - start
    return per_ticket_results, ai_elapsed


def manual_estimate_seconds(num_tickets):
    return MANUAL_SECONDS_PER_TICKET * num_tickets
