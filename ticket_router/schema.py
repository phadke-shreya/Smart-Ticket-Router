from typing import Literal
from pydantic import BaseModel

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
    category: AllowedCategory
    priority: AllowedPriority
    reasoning: str


class TicketResult(BaseModel):
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
