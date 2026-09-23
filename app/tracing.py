from langfuse import Langfuse

from app.config import settings

_langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


def new_trace(name: str):
    """Call once per scan run. Log retrieval hits, reasoning output, and
    self-check results as spans/generations under this trace so you can
    show the full decision path live in a demo."""
    return _langfuse.trace(name=name)


def log_retrieval(trace, resource_name: str, controls: list):
    trace.span(
        name="retrieval",
        input={"resource": resource_name},
        output={"controls": [c.control_id for c in controls]},
    )


def log_reasoning(trace, finding):
    trace.generation(
        name="reasoning_agent",
        input={"resource": finding.resource_name, "control": finding.control_id},
        output=finding.model_dump(),
    )


def log_self_check(trace, verified_finding):
    trace.span(
        name="self_check",
        input={"finding": verified_finding.reasoning},
        output={
            "status": verified_finding.verification_status,
            "note": verified_finding.verification_note,
        },
    )
