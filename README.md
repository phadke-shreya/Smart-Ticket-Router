# Smart Ticket Router

An AI-powered support ticket classifier for an e-commerce marketplace. Given any raw support message (email, chat, or short text), it returns structured JSON with **category**, **priority**, **assigned team**, and a one-line **reasoning** — built with FastAPI, OpenAI, and Pydantic.

## What it does

1. A support ticket comes in as plain text (any language, any tone, any length).
2. The system builds a structured prompt, sends it to an LLM, and gets back JSON.
3. The JSON is validated against a strict schema — only real category/priority/team values are accepted.
4. If the LLM's response is malformed or invalid, it automatically retries.
5. If a ticket describes more than one issue, the highest-priority issue is selected, and the other issue is still mentioned in the reasoning.
6. Identical tickets are cached, so repeat submissions return the exact same result instantly.

## Architecture

| File | Role |
|---|---|
| `ticket_router/schema.py` | Defines the 14 allowed categories, 14 teams, and 3 priority levels. Enforces valid JSON shape via Pydantic. |
| `ticket_router/prompts.py` | Builds the system prompt: category definitions, priority rules, a numbered decision process, and rules for ambiguous/unclear tickets (refund ambiguity, broken/crash ambiguity, vague issues, insufficient information, multi-issue handling, irrelevant content, security/privacy, prompt-injection resistance, multi-language support). |
| `ticket_router/llm_client.py` | Calls the OpenAI API (`temperature=0` for consistency), with retries on API errors, empty responses, or malformed JSON. |
| `ticket_router/router.py` | The reusable `classify_ticket()` function — orchestrates prompt → LLM call → validation → retries → in-memory caching. |
| `ticket_router/demo.py` | Shared logic for running all 20 sample tickets and timing the batch — used by both the CLI script and the in-browser demo. |
| `app.py` + `templates/` | FastAPI web form to test tickets interactively (with a dropdown to instantly try any of the 20 demo tickets), a `/demo` page showing all 20 with timing, dark mode support, and a `/api/classify` JSON endpoint. |
| `sample_tickets.json` | 20 demo tickets covering all categories and required edge cases. |
| `demo_timing.py` | CLI before/after script: times AI routing of all 20 tickets vs. an estimated manual-routing baseline. |
| `demo_reliablity.py` | Narrated script that simulates API failures, malformed JSON, and retry/recovery live in the terminal — proof the reliability handling actually works, without touching the real API. |
| `tests/` | Automated tests (mocked LLM calls — no real API cost) proving retry/validation logic works. |

### A key design decision: who decides the team?

The LLM outputs `assigned_team` directly (not derived from category by our code). This was a deliberate tradeoff: it keeps the prompt's category→team mapping in one place and trusts the model to follow it, in exchange for giving up the stronger guarantee of always deriving the team in code. Pydantic still validates that `assigned_team` is one of the 14 real team names, so a wildly invented team is caught — but a category/team mismatch is not.

### How this maps to the required flowchart

User enters ticket → build_messages() in prompts.py
↓
Send to LLM → call_llm() in llm_client.py
↓
Is valid JSON? → handled inside call_llm() (retries on malformed/empty JSON, gives up after 3 attempts)
↓ yes
Validate values (category/priority/team) → TicketResult in schema.py, checked in classify_ticket()
↓ invalid → retry (up to 2 more attempts, re-calling the LLM)
↓ valid
Display JSON → returned to the web form / API caller



## Categories, priorities, and teams

| Category | Team |
|---|---|
| order_issue | Order Management |
| delivery_logistics | Logistics & Delivery Ops |
| returns_refunds | Returns & Refunds Team |
| payments_billing | Payments & Billing |
| product_issue | Product Quality Support |
| account_access | Account & Identity Support |
| wallet_offers | Rewards & Promotions |
| seller_related | Marketplace Trust |
| warranty_installation | Warranty & Installation |
| technical_platform | Platform Engineering |
| fraud_security | Trust & Security |
| feedback_complaints | Customer Experience |
| general_inquiry | Customer Support Desk |
| unclassified | Unassigned |

**Priority:** High / Medium / Low, with an escalation rule — anger, strong frustration, sarcasm (including positive words used ironically, e.g. "so happy that my order got lost"), or urgency raises priority one level, capped at High. `feedback_complaints` and `unclassified` never escalate, since there's no concrete symptom to justify it.

## Edge cases handled

- **Angry tone / sarcasm** (including ironic positive phrasing) → priority escalation
- **Insufficient information** — a single bare word or greeting ("hacked", "crash", "hi") → `unclassified`, distinct from a full sentence naming an actual event
- **Irrelevant/off-topic content** — ignored when mixed with a real issue; the whole ticket becomes `unclassified` if there's no genuine issue at all
- **Ambiguous refund** (Payments vs. Returns) — resolved by whether a return was already initiated
- **Ambiguous "broken"/"crashed"** — defaults to `technical_platform` if named in a sentence, `product_issue` if a physical item is referenced, `unclassified` if it's a bare word
- **Vague complaints with no named symptom** ("this again?!") → `feedback_complaints`, always Low
- **Multi-issue tickets** — the highest-priority issue is selected; the reasoning still names the other issue and why it wasn't chosen
- **Security/fraud precedence** — a described compromise/unauthorized-transaction event is always High (`fraud_security`), even downplayed by the customer; a bare security-sounding word alone is not enough
- **Payment discrepancy scale** — <₹100 Low, ₹100–1000 Medium, ₹1000+ High; full payment failures/duplicate charges are always High regardless of amount
- **Lost or "delivered but not received" packages** → High, distinct from a plain delivery delay (Medium)
- **Prompt injection attempts** — ticket text is always treated as data, never as an instruction
- **Non-English tickets** — classified correctly regardless of language; responses always in English
- **Malformed/empty LLM responses, API failures** — automatic retries, with a clear error after max attempts
- **Repeat identical tickets** — served from an in-memory cache for guaranteed consistency

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Create a .env file (see .env.example) with your OpenAI key:


OPENAI_API_KEY=sk-...
Running the web app

uvicorn app:app --reload
Open http://127.0.0.1:8000 in your browser. Pick a ticket from the dropdown for an instant demo, or paste your own. The page respects your system's light/dark mode automatically.

Running tests

pytest
All LLM calls are mocked, so tests run instantly with no API cost.

Running the before/after demo

python demo_timing.py
Or click "Run 20-Ticket Demo" on the web page for the same thing in the browser, with reasoning shown for every ticket.

Runs all 20 sample tickets through the AI pipeline and compares the measured AI time against an estimated manual-routing baseline (default assumption: 3 minutes/ticket for a human agent to read, categorize, and route a ticket).

Running the reliability demo

python demo_reliablity.py

Narrates, live in the terminal, what happens when the LLM returns invalid data, when the API fails, and when JSON is malformed — showing the retry logic and clean error handling working, without touching the real OpenAI API.
