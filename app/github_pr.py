import time

from github import Github

from app.config import settings
from app.models import VerifiedFinding
from app.runtime_config import get_runtime_config


def _format_finding_markdown(finding: VerifiedFinding) -> str:
    return f"""### {finding.resource_type} `{finding.resource_name}`
- **Control:** {finding.framework} {finding.control_id}
- **Severity:** {finding.severity}
- **Verification:** {finding.verification_status}

{finding.reasoning}

<details><summary>Cited control text</summary>

{finding.cited_control_text}

</details>
"""


def open_findings_pr(findings: list[VerifiedFinding]) -> str:
    """Opens a single PR summarizing all CONFIRMED violations from one scan.

    Day-one scope: this writes a markdown report file, not an automatic
    infra fix -- generating a safe, correct Terraform diff per violation
    type is real future work, not something to fake for a demo.
    """
    confirmed = [f for f in findings if f.violation and f.verification_status == "confirmed"]
    if not confirmed:
        return ""

    rc = get_runtime_config()
    token = rc.github_token or settings.github_token
    repo_name = rc.github_repo or settings.github_repo

    gh = Github(token)
    repo = gh.get_repo(repo_name)

    branch_name = f"soc2-copilot/scan-{int(time.time())}"
    base = repo.get_branch(repo.default_branch)
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)

    report_lines = ["# SOC 2 Copilot findings\n"] + [
        _format_finding_markdown(f) for f in confirmed
    ]
    report_path = "soc2-copilot-findings.md"

    try:
        existing = repo.get_contents(report_path, ref=branch_name)
        repo.update_file(
            report_path,
            "Update SOC 2 Copilot findings",
            "\n".join(report_lines),
            existing.sha,
            branch=branch_name,
        )
    except Exception:  # noqa: BLE001 -- file doesn't exist yet on this branch
        repo.create_file(
            report_path,
            "Add SOC 2 Copilot findings",
            "\n".join(report_lines),
            branch=branch_name,
        )

    pr = repo.create_pull(
        title=f"SOC 2 Copilot: {len(confirmed)} confirmed finding(s)",
        body="Automated scan results. Each finding cites the exact control "
        "it violates and has passed a self-check verification pass "
        "before being included here.",
        head=branch_name,
        base=repo.default_branch,
    )
    return pr.html_url
