import json

from google.genai import types

from app.config import settings
from app.gemini_client import generate_with_retry
from app.models import Finding, VerifiedFinding

SYSTEM_PROMPT = """You are a strict reviewer checking another analyst's \
compliance finding for accuracy. You will be shown a finding (violation \
decision + reasoning) and the exact control text it was supposed to be \
based on.

Check: does the reasoning actually follow from the cited control text? Is \
the analyst inventing a requirement the control doesn't state? Is the \
severity reasonable given the control?

Respond ONLY with a JSON object, no other text:
{
  "verification_status": "confirmed"|"rejected"|"uncertain",
  "verification_note": "one sentence explaining your check"
}

Use "rejected" if the reasoning clearly doesn't follow from the control \
text. Use "uncertain" only if you genuinely cannot tell either way."""


def verify_finding(finding: Finding) -> VerifiedFinding:
    user_prompt = f"""Control text:
{finding.cited_control_text}

Finding to check:
resource: {finding.resource_type} ({finding.resource_name})
violation: {finding.violation}
severity: {finding.severity}
reasoning: {finding.reasoning}
"""

    response = generate_with_retry(
        model=settings.reasoning_model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            # see reasoning_agent.py -- thinking tokens eat into this budget too
            max_output_tokens=1024,
        ),
    )

    parsed = json.loads(response.text)

    return VerifiedFinding(
        **finding.model_dump(),
        verification_status=parsed["verification_status"],
        verification_note=parsed["verification_note"],
    )
