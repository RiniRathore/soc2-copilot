"""
An ALTERNATIVE to main.py's fixed pipeline, using Gemini's "Automatic
Function Calling" (Python SDK only): real Python functions are passed
directly as tools, and the SDK detects calls, executes them, and loops
until the model produces a final text response -- no manual response
parsing, no manual role/id bookkeeping required.

This replaces an earlier draft that manually parsed function_call parts
and hand-rolled the back-and-forth loop -- checking that draft against
Google's official docs surfaced real bugs (wrong role name on the
function-result message, missing id round-trip). Automatic function
calling sidesteps all of that by letting the SDK manage the protocol.
"""
from google.genai import types

from app.adapters.terraform_adapter import load_terraform_state
from app.config import settings
from app.gemini_client import get_client
from app.github_pr import open_findings_pr
from app.reasoning_agent import evaluate_resource
from app.retrieval import retrieve_relevant_controls
from app.self_check import verify_finding

# Module-level state the tool functions read/write. The SDK calls these
# functions directly (real side effects), it does not just simulate them.
_resources = []
_controls_cache = {}   # resource_index -> list of ControlChunk
_findings = []         # list of VerifiedFinding
_pr_url = None


def load_resources() -> list[str]:
    """Loads all infrastructure resources from the seeded Terraform state file.

    Call this first, before anything else. Each resource gets an index
    (0, 1, 2, ...) matching its position in the returned list -- use that
    index in later tool calls.

    Returns:
        A list of resource descriptions like "aws_s3_bucket:customer_uploads".
    """
    global _resources
    _resources = load_terraform_state("seed_data/sample.tfstate.json")
    return [f"{r.resource_type}:{r.name}" for r in _resources]


def retrieve_controls_for_resource(resource_index: int) -> list[str]:
    """Retrieves the SOC2/CIS controls most relevant to one resource.

    Args:
        resource_index: Index into the list returned by load_resources.

    Returns:
        A list of control descriptions like "CIS_AWS CIS-2.1.5". Each
        control's position in this list is its control_index for the
        next tool call.
    """
    global _controls_cache
    controls = retrieve_relevant_controls(_resources[resource_index])
    _controls_cache[resource_index] = controls
    return [f"{c.framework} {c.control_id}" for c in controls]


def evaluate_and_verify_resource(resource_index: int, control_index: int) -> dict:
    """Checks one resource against one retrieved control, then verifies
    the finding is actually supported by the control text before keeping it.

    Args:
        resource_index: Index into the resources from load_resources.
        control_index: Index into the controls returned for that resource
            by retrieve_controls_for_resource.

    Returns:
        A dict with violation (bool), severity, reasoning, and
        verification_status ("confirmed"/"rejected"/"uncertain").
    """
    global _findings
    finding = evaluate_resource(
        _resources[resource_index], _controls_cache[resource_index][control_index]
    )
    verified = verify_finding(finding)
    if verified.violation and verified.verification_status == "confirmed":
        _findings.append(verified)
    return verified.model_dump()


def open_pr_with_findings() -> dict:
    """Opens a GitHub PR with all confirmed violations found so far.

    Only call this once you've checked all the resources you think are
    worth checking -- not before.

    Returns:
        A dict with pr_url and findings_count.
    """
    global _pr_url
    _pr_url = open_findings_pr(_findings) if _findings else None
    return {"pr_url": _pr_url, "findings_count": len(_findings)}


SYSTEM_PROMPT = """You are a SOC 2 compliance scanning agent. Work through \
the infrastructure resources: load them, retrieve relevant controls for \
each, evaluate/verify each resource against its most relevant control(s), \
then open a PR once you've checked what's worth checking. You decide how \
many controls per resource are worth checking -- not every resource needs \
every control checked."""


def run_agentic_scan() -> dict:
    global _resources, _controls_cache, _findings, _pr_url
    _resources, _controls_cache, _findings, _pr_url = [], {}, [], None

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[
            load_resources,
            retrieve_controls_for_resource,
            evaluate_and_verify_resource,
            open_pr_with_findings,
        ],
    )

    # Automatic function calling: the SDK detects tool calls in the
    # model's response, runs the real Python functions above, feeds
    # results back, and repeats -- until the model returns final text.
    response = get_client().models.generate_content(
        model=settings.reasoning_model,
        contents="Begin the scan.",
        config=config,
    )

    return {
        "findings": [f.model_dump() for f in _findings],
        "pr_url": _pr_url,
        "final_text": response.text,
    }
