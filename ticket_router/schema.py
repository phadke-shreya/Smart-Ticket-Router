from typing import Literal
from pydantic import BaseModel

# Single source of truth: category -> team.
# We do NOT ask the LLM to pick the team. The LLM only judges things that
# require understanding (category, priority, reasoning). Team assignment is
# a fixed business rule, so we derive it in code — this guarantees the team
# is always correct even if the LLM misjudges something else.
CATEGORY_TEAM_MAP = {
    "Order Issue": "Order Operations",
    "Payments": "Finance",
    "Returns and Refunds": "Returns Team",
    "Shipping": "Logistics",
    "Account": "Customer Support",
    "Product Inquiry": "Customer Support",
    "General Inquiry": "Customer Support",
}

AllowedCategory = Literal[
    "Order Issue",
    "Payments",
    "Returns and Refunds",
    "Shipping",
    "Account",
    "Product Inquiry",
    "General Inquiry",
]

AllowedPriority = Literal["High", "Medium", "Low"]


class LLMTicketOutput(BaseModel):
    """Exact shape we require the LLM to return."""
    category: AllowedCategory
    priority: AllowedPriority
    reasoning: str


class TicketResult(BaseModel):
    """Final result returned to the caller — team is added by our code, not the LLM."""
    category: AllowedCategory
    priority: AllowedPriority
    team: str
    reasoning: str


def build_ticket_result(llm_output: LLMTicketOutput) -> TicketResult:
    team = CATEGORY_TEAM_MAP[llm_output.category]
    return TicketResult(
        category=llm_output.category,
        priority=llm_output.priority,
        team=team,
        reasoning=llm_output.reasoning,
    )
