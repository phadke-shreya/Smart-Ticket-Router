from typing import Literal
from pydantic import BaseModel, Field

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
    """Exact shape required for ONE classified issue."""
    category: AllowedCategory
    priority: AllowedPriority
    reasoning: str


class LLMTicketOutputList(BaseModel):
    """
    Top-level shape the LLM must return: always a list of 1+ issues.
    A single-issue ticket is just a list with one item. A ticket mixing
    genuinely separate issues (e.g. shipping delay + account locked) can
    return multiple items, each routed to its own team.
    """
    tickets: list[LLMTicketOutput] = Field(..., min_length=1)


class TicketResult(BaseModel):
    """Final result for ONE issue — team is added by our code, not the LLM."""
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
