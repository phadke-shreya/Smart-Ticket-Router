import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from ticket_router.prompts import build_messages

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5


class LLMCallError(Exception):
    """Raised when the OpenAI API itself fails after all retries (network/rate-limit/server errors)."""


class MalformedResponseError(Exception):
    """Raised when the LLM's response isn't valid JSON (or is empty) after all retries."""


def call_llm(ticket_text: str) -> dict:
    """
    Sends the ticket to the LLM and returns a parsed JSON dict (not yet schema-validated).
    Retries on API errors and on malformed/empty responses.
    """
    messages = build_messages(ticket_text)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0,                              # same ticket -> same answer, every time
                response_format={"type": "json_object"},    # forces syntactically valid JSON
            )
        except (APIError, APIConnectionError, RateLimitError) as exc:
            last_error = exc
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue

        content = response.choices[0].message.content

        if not content or not content.strip():
            last_error = ValueError("Empty response from LLM")
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            last_error = exc
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue

    if isinstance(last_error, (APIError, APIConnectionError, RateLimitError)):
        raise LLMCallError(f"OpenAI API call failed after {MAX_RETRIES} attempts: {last_error}")
    raise MalformedResponseError(f"LLM did not return valid JSON after {MAX_RETRIES} attempts: {last_error}")
