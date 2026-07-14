import json

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ticket_router.router import classify_ticket, TicketRoutingError
from ticket_router.demo import load_tickets, run_timed_demo, manual_estimate_seconds, MANUAL_SECONDS_PER_TICKET

app = FastAPI(title="Smart Ticket Router")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CATEGORY_ICONS = {
    "Order Issue": "📦",
    "Payments": "💳",
    "Returns and Refunds": "🔄",
    "Shipping": "🚚",
    "Account": "🔐",
    "Product Inquiry": "🛍️",
    "General Inquiry": "❓",
}

class ClassifyRequest(BaseModel):
    ticket_text: str


@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"result": None, "result_json": None, "error": None, "ticket_text": ""},
    )


@app.post("/route", response_class=HTMLResponse)
def route_ticket(request: Request, ticket_text: str = Form(...)):
    result = None
    result_json = None
    error = None
    try:
        result = classify_ticket(ticket_text)
        result_json = json.dumps(result, indent=2)
    except TicketRoutingError as exc:
        print(f"[classify_ticket error] {exc}")  # full technical detail logged server-side, for developers
        error = "We couldn't process this ticket right now. Please try again in a moment."

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": result,
            "result_json": result_json,
            "error": error,
            "ticket_text": ticket_text,
            "category_icons": CATEGORY_ICONS,
        },
    )


@app.post("/api/classify")
def classify_api(payload: ClassifyRequest):
    try:
        return classify_ticket(payload.ticket_text)
    except TicketRoutingError as exc:
        return {"error": str(exc)}


@app.get("/demo", response_class=HTMLResponse)
def run_demo(request: Request):
    tickets = load_tickets()
    per_ticket_results, ai_elapsed = run_timed_demo(tickets)
    manual_seconds = manual_estimate_seconds(len(tickets))

    return templates.TemplateResponse(
        request,
        "demo.html",
        {
            "per_ticket_results": per_ticket_results,
            "ai_elapsed": f"{ai_elapsed:.2f}",
            "manual_minutes": f"{manual_seconds / 60:.1f}",
            "speedup": f"{manual_seconds / ai_elapsed:.0f}",
            "manual_seconds_per_ticket": MANUAL_SECONDS_PER_TICKET,
            "category_icons": CATEGORY_ICONS,
        },
    )
