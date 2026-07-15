from typing import Literal
from pydantic import BaseModel

AllowedCategory = Literal[
    "order_issue",
    "delivery_logistics",
    "returns_refunds",
    "payments_billing",
    "product_issue",
    "account_access",
    "wallet_offers",
    "seller_related",
    "warranty_installation",
    "technical_platform",
    "fraud_security",
    "feedback_complaints",
    "general_inquiry",
    "unclassified",
]

AllowedPriority = Literal["High", "Medium", "Low"]

AllowedTeam = Literal[
    "Order Management",
    "Logistics & Delivery Ops",
    "Returns & Refunds Team",
    "Payments & Billing",
    "Product Quality Support",
    "Account & Identity Support",
    "Rewards & Promotions",
    "Marketplace Trust",
    "Warranty & Installation",
    "Platform Engineering",
    "Trust & Security",
    "Customer Experience",
    "Customer Support Desk",
    "Unassigned",
]

class TicketResult(BaseModel):
    category: AllowedCategory
    priority: AllowedPriority
    assigned_team: AllowedTeam
    reasoning: str
