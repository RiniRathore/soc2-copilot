from fastapi import FastAPI
from pydantic import BaseModel

from app.adapters.cloud_api_adapter import pull_all as pull_live_aws
from app.adapters.terraform_adapter import load_terraform_state
from app.github_pr import open_findings_pr
from app.reasoning_agent import evaluate_resource
from app.retrieval import retrieve_relevant_controls
from app.self_check import verify_finding
from app.tracing import log_reasoning, log_retrieval, log_self_check, new_trace
from app.agent_loop import run_agentic_scan
from app.runtime_config import RuntimeConfig, get_runtime_config, set_runtime_config

app = FastAPI(title="SOC 2 Copilot")


class ScanRequest(BaseModel):
    source: str = "terraform"          # "terraform" | "live_api"
    terraform_state_path: str | None = "seed_data/sample.tfstate.json"
    open_pr: bool = True


class ScanResponse(BaseModel):
    findings: list[dict]
    pr_url: str | None
    pr_error: str | None = None


def run_scan(req: ScanRequest) -> ScanResponse:
    trace = new_trace(name=f"soc2-scan-{req.source}")

    if req.source == "terraform":
        resources = load_terraform_state(req.terraform_state_path)
    elif req.source == "live_api":
        resources = pull_live_aws()
    else:
        raise ValueError(f"unknown source: {req.source}")

    verified_findings = []
    for resource in resources:
        controls = retrieve_relevant_controls(resource)
        log_retrieval(trace, resource.name, controls)

        for control in controls:
            finding = evaluate_resource(resource, control)
            log_reasoning(trace, finding)

            verified = verify_finding(finding)
            log_self_check(trace, verified)

            if verified.violation:  # only surface actual violations
                verified_findings.append(verified)

    pr_url = None
    pr_error = None
    if req.open_pr and verified_findings:
        try:
            pr_url = open_findings_pr(verified_findings)
        except Exception as e:  # noqa: BLE001 -- a PR failure shouldn't discard findings already verified above
            pr_error = str(e)

    return ScanResponse(
        findings=[f.model_dump() for f in verified_findings],
        pr_url=pr_url,
        pr_error=pr_error,
    )


@app.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    return run_scan(req)


@app.post("/scan/agentic", response_model=ScanResponse)
def scan_agentic():
    """Second demo path: automatic function calling -- the SDK lets the
    model decide which tool to call and when to stop, instead of this
    fixed pipeline. Kept separate from /scan so the working deterministic
    demo is never at risk if this one has issues."""
    result = run_agentic_scan()
    return ScanResponse(findings=result["findings"], pr_url=result["pr_url"])


@app.post("/configure")
def configure(config: RuntimeConfig):
    """Accepts credentials from the Streamlit settings panel. Held in
    server-side memory only for this process's lifetime -- never
    written to disk or logged. See app/runtime_config.py for the
    honest caveat on why this isn't real secrets management."""
    set_runtime_config(config)
    # Echo back which fields are set (not their values) so the UI can
    # confirm without ever re-displaying a secret.
    return {
        "configured": [k for k, v in config.model_dump().items() if v]
    }


@app.get("/configure")
def get_configure_status():
    """Lets the frontend check what's currently configured without
    ever receiving the actual secret values back."""
    current = get_runtime_config().model_dump()
    return {"configured": [k for k, v in current.items() if v]}


@app.get("/health")
def health():
    return {"status": "ok"}
