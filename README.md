# Smart Ticket Router

An AI-powered support ticket classifier for an e-commerce use case. Given any raw support message (email, chat, or short text), it returns structured JSON with **category**, **priority**, **assigned team**, and a one-line **reasoning** — built with FastAPI, OpenAI, and Pydantic.

## What it does

1. A support ticket comes in as plain text (any language, any tone, any length).
2. The system builds a structured prompt, sends it to an LLM, and gets back JSON.
3. The JSON is validated against a strict schema (only real categories/priorities allowed).
4. If the LLM's response is malformed or invalid, it automatically retries.
5. The correct team is derived from the category using a fixed business-rule mapping (not left to the LLM's guess).
6. If a ticket contains genuinely separate issues (e.g. a shipping delay *and* a locked account), it's split into multiple classifications — each routed to its own team.
7. Identical tickets are cached, so repeat submissions return the exact same result instantly.

## Architecture

| File | Role |
|---|---|
| `ticket_router/schema.py` | Defines allowed categories/priorities and the category→team mapping. Enforces valid JSON shape via Pydantic. |
| `ticket_router/prompts.py` | Builds the system prompt: category definitions, priority rules, edge-case handling (ambiguous tickets, vague messages, multi-issue splitting, prompt-injection resistance, multi-language support). |
| `ticket_router/llm_client.py` | Calls the OpenAI API (`temperature=0` for consistency), with retries on API errors, empty responses, or malformed JSON. |
| `ticket_router/router.py` | The reusable `classify_ticket()` function — orchestrates prompt → LLM call → validation → retries → team assignment → in-memory caching. |
| `app.py` + `templates/index.html` | FastAPI web form to test tickets interactively, plus a `/api/classify` JSON endpoint. |
| `sample_tickets.json` | 20 demo tickets covering all 7 categories and required edge cases. |
| `demo_timing.py` | Before/after script: times AI routing of all 20 tickets vs. an estimated manual-routing baseline. |
| `tests/` | Automated tests (mocked LLM calls — no real API cost) proving retry/validation logic works. |

### How this maps to the required flowchart

User enters ticket → build_messages() in prompts.py
↓
Send to LLM → call_llm() in llm_client.py
↓
Is valid JSON? → handled inside call_llm() (retries on malformed/empty JSON, gives up after 3 attempts)
↓ yes
Validate values (category/priority/team) → LLMTicketOutputList in schema.py, checked in classify_ticket()
↓ invalid → retry (up to 2 more attempts, re-calling the LLM)
↓ valid
Display JSON → returned to the web form / API caller


## Categories, priorities, and teams

| Category | Team |
|---|---|
| Order Issue | Order Operations |
| Payments | Finance |
| Returns and Refunds | Returns Team |
| Shipping | Logistics |
| Account | Customer Support |
| Product Inquiry | Customer Support |
| General Inquiry | Customer Support |

**Priority:** High / Medium / Low, with an escalation rule — if the customer expresses anger, frustration, or urgency, priority is raised one level (capped at High).

## Edge cases handled

- **Angry tone** → priority escalation rule
- **Very short / vague messages** → defaults to General Inquiry / Low
- **Ambiguous tickets** (e.g. refund status could be Payments or Returns) → explicit tie-breaker rules in the prompt
- **Multiple distinct issues in one ticket** → split into separate classifications, each with its own team
- **Prompt injection attempts** (ticket text trying to manipulate the classifier) → explicit instruction to treat ticket text as data, never as commands
- **Non-English tickets** → classified correctly regardless of input language; responses always returned in English
- **Malformed/empty LLM responses, API failures** → automatic retries, with a clear error after max attempts
- **Repeat identical tickets** → served from an in-memory cache for guaranteed consistency

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Create a .env file (see .env.example) with your OpenAI key:
OPENAI_API_KEY=sk-...

Running the web app

uvicorn app:app --reload
Open http://127.0.0.1:8000 in your browser.

Running tests

pytest
All LLM calls are mocked, so tests run instantly with no API cost.

Running the before/after demo

python demo_timing.py
Runs all 20 sample tickets through the AI pipeline and compares the measured AI time against an estimated manual-routing baseline (default assumption: 3 minutes/ticket for a human agent to read, categorize, and route a ticket).

Latest result: ~24 seconds to route 20 tickets with AI vs. an estimated 60 minutes manually — roughly a 148x speedup.