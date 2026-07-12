import json

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ticket_router.router import classify_ticket, TicketRoutingError

app = FastAPI(title="Smart Ticket Router")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ClassifyRequest(BaseModel):
    ticket_text: str


@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result_json": None, "result": None, "error": None, "ticket_text": ""},
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
        error = str(exc)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "result_json": result_json,
            "error": error,
            "ticket_text": ticket_text,
        },
    )


@app.post("/api/classify")
def classify_api(payload: ClassifyRequest):
    """Plain JSON API — used later for batch/automated demo scripts, not just the web form."""
    try:
        return classify_ticket(payload.ticket_text)
    except TicketRoutingError as exc:
        return {"error": str(exc)}
