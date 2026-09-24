"""Shared Gemini client construction + retry for transient API errors.

Extracted because reasoning_agent.py, self_check.py, and agent_loop.py each
built their own client identically, and a live scan makes dozens of
sequential calls -- transient 503 (model overloaded) / 429 (rate limited)
responses are routine at that volume, not exceptional.
"""
import json
import time

import httpx
from google import genai
from google.genai import errors

from app.config import settings
from app.runtime_config import get_runtime_config

MAX_ATTEMPTS = 4
BACKOFF_SECONDS = 2
MAX_RATE_LIMIT_WAIT = 65  # free-tier RPM windows reset within ~60s


def get_client() -> genai.Client:
    """Built per-call (not once at import) so a key entered in the
    settings panel after the app started still gets picked up."""
    rc = get_runtime_config()
    return genai.Client(api_key=rc.gemini_api_key or settings.gemini_api_key)


def _retry_delay_seconds(e) -> float | None:
    """429 responses carry the server's own suggested wait (RetryInfo)
    -- e.g. free-tier RPM limits reset in ~60s, far longer than our
    exponential backoff would wait on its own. Prefer it when present."""
    details = (e.details or {}).get("error", {}).get("details", [])
    for d in details:
        if d.get("@type", "").endswith("RetryInfo"):
            raw = d.get("retryDelay", "")
            if raw.endswith("s"):
                try:
                    return float(raw[:-1])
                except ValueError:
                    return None
    return None


def generate_with_retry(**kwargs):
    """Calls client.models.generate_content, retrying transient failures.

    Retries ServerError (5xx, e.g. "model overloaded"), 429 rate-limit
    ClientErrors, and httpx.TransportError (connection drops, timeouts --
    seen live: "Server disconnected without sending a response" mid-scan).
    Anything else (bad request, auth failure, etc.) raises immediately --
    retrying those would just waste time on a call that can never succeed.
    """
    client = get_client()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.models.generate_content(**kwargs)
        except errors.ServerError:
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(BACKOFF_SECONDS * attempt)
        except errors.ClientError as e:
            if e.code != 429 or attempt == MAX_ATTEMPTS:
                raise
            wait = _retry_delay_seconds(e)
            time.sleep(min(wait, MAX_RATE_LIMIT_WAIT) if wait else BACKOFF_SECONDS * attempt)
        except httpx.TransportError:
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(BACKOFF_SECONDS * attempt)


def parse_json_response(response) -> dict:
    """response_mime_type="application/json" makes malformed JSON rare,
    but not impossible -- a safety block, MAX_TOKENS truncation, or a
    RECITATION finish reason all come back as empty/partial text. Raises
    ValueError with a clear message; callers should catch it and degrade
    one finding gracefully rather than crash the whole scan over it.
    """
    if not response.text:
        reason = response.candidates[0].finish_reason if response.candidates else None
        raise ValueError(f"empty response from Gemini (finish_reason={reason})")
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini response was not valid JSON: {e}") from e


class GeminiCallError(Exception):
    """Raised for any failure calling Gemini or parsing its response --
    a transient error that outlasted generate_with_retry's attempt budget,
    or a response that came back empty/malformed. Callers catch this one
    type and degrade a single (resource, control) pair gracefully instead
    of crashing the whole scan."""


def generate_and_parse(**kwargs) -> dict:
    """The single entry point reasoning_agent.py / self_check.py should use.

    Deliberately catches Exception, not just errors.APIError -- this is an
    external network boundary, and the whole point of this function is to
    guarantee that *nothing* about a single Gemini call (a structured API
    error, a raw connection drop, an unexpected SDK exception) can escape
    and crash the caller. Every failure becomes one GeminiCallError.
    """
    try:
        response = generate_with_retry(**kwargs)
    except Exception as e:
        raise GeminiCallError(f"Gemini API call failed: {e}") from e
    try:
        return parse_json_response(response)
    except ValueError as e:
        raise GeminiCallError(str(e)) from e
