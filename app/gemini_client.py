"""Shared Gemini client construction + retry for transient API errors.

Extracted because reasoning_agent.py, self_check.py, and agent_loop.py each
built their own client identically, and a live scan makes dozens of
sequential calls -- transient 503 (model overloaded) / 429 (rate limited)
responses are routine at that volume, not exceptional.
"""
import time

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

    Retries ServerError (5xx, e.g. "model overloaded") and 429 rate-limit
    ClientErrors. Anything else (bad request, auth failure, etc.) raises
    immediately -- retrying those would just waste time on a call that can
    never succeed.
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
