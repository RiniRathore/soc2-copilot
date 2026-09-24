import json

from google.genai import types

from app.config import settings
from app.gemini_client import GeminiCallError, generate_and_parse
from app.models import ControlChunk, Finding, ResourceConfig

SYSTEM_PROMPT = """You are a SOC 2 compliance analyst. You are given one \
infrastructure resource's configuration and the text of the control(s) \
most relevant to it. Decide whether this specific resource violates the \
control, and explain why in plain English.

Respond ONLY with a JSON object, no other text, in this exact shape:
{
  "violation": true|false,
  "severity": "low"|"medium"|"high"|"critical",
  "reasoning": "one or two sentences explaining your decision, referencing \
the specific config values that led to it"
}

Base your decision strictly on the control text provided and the resource \
config provided. Do not invent config values that are not present. If the \
config is genuinely ambiguous or insufficient to decide, say so in the \
reasoning and set severity to "low"."""


def evaluate_resource(resource: ResourceConfig, control: ControlChunk) -> Finding:
    user_prompt = f"""Control ({control.framework} {control.control_id}):
{control.text}

Resource:
type: {resource.resource_type}
name: {resource.name}
config: {json.dumps(resource.config, default=str)}
"""

    try:
        parsed = generate_and_parse(
            model=settings.reasoning_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",  # forces valid JSON back
                # gemini-3.x reasoning models spend part of this budget on internal
                # "thinking" tokens before the JSON answer -- observed 100-250+ in
                # testing -- so this needs real headroom above the answer's own size.
                max_output_tokens=2048,
            ),
        )
        violation, severity, reasoning = parsed["violation"], parsed["severity"], parsed["reasoning"]
    except (GeminiCallError, KeyError) as e:
        # Fail closed: skip this one pair (whether Gemini was unreachable/
        # overloaded or just returned something unusable) rather than crash
        # the whole scan. Not a violation, so it won't surface as a false
        # finding -- just silently under-reports here.
        violation, severity, reasoning = False, "low", f"Could not evaluate this resource/control pair: {e}"

    return Finding(
        resource_type=resource.resource_type,
        resource_name=resource.name,
        control_id=control.control_id,
        framework=control.framework,
        violation=violation,
        severity=severity,
        reasoning=reasoning,
        cited_control_text=control.text,
    )
