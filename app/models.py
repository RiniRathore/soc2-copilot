from typing import Literal, Optional
from pydantic import BaseModel


class ResourceConfig(BaseModel):
    """The single normalized shape every input adapter must produce.

    Both the Terraform adapter and the live cloud API adapter output
    a list of these. Nothing downstream (retrieval, reasoning) needs
    to know or care where the data came from.
    """

    resource_type: str          # e.g. "aws_s3_bucket", "aws_security_group"
    name: str                   # resource name/id
    config: dict                # raw properties relevant to compliance checks
    source: Literal["terraform", "live_api"]


class ControlChunk(BaseModel):
    """A retrieved chunk of policy text from the vector store."""

    control_id: str             # e.g. "CC6.1", "CIS-2.1.1"
    framework: str              # "SOC2" | "CIS_AWS"
    text: str
    similarity: float
    # False for organizational/process controls (board oversight, vendor
    # risk management, incident-response programs, ...) that no infra scan
    # can ever confirm or violate -- see app/knowledge_base/*.md's [ORG]
    # tag. Drives the honest coverage summary in ScanResponse; a control
    # tagged False is never something a "zero findings" result implies is
    # actually satisfied.
    checkable: bool = True


class Finding(BaseModel):
    resource_type: str
    resource_name: str
    control_id: str
    framework: str
    violation: bool
    severity: Literal["low", "medium", "high", "critical"]
    reasoning: str
    cited_control_text: str
    remediation: str            # only meaningful when violation is True


class VerifiedFinding(Finding):
    verification_status: Literal["confirmed", "rejected", "uncertain"]
    verification_note: str


class CoverageSummary(BaseModel):
    """Honest accounting of what a scan can and can't tell you -- see
    README: most SOC2 controls are organizational/process, not
    infrastructure. Zero violations found does NOT mean "SOC2 compliant";
    it means "no violations found among the controls this tool can
    actually evaluate from infrastructure config.\""""

    total_controls_in_knowledge_base: int
    infra_checkable_controls_in_knowledge_base: int
    organizational_controls_in_knowledge_base: int  # can't be evaluated by this tool at all
    unique_controls_evaluated_this_scan: int
    note: str = (
        "This tool evaluates infrastructure configuration only. Organizational/"
        "process controls (board oversight, vendor risk management, incident-"
        "response programs, etc.) require evidence this tool cannot see, and a "
        "clean scan does not mean full SOC2 compliance -- only that no "
        "violations were found among the infra-checkable controls above."
    )
