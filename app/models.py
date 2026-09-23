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


class Finding(BaseModel):
    resource_type: str
    resource_name: str
    control_id: str
    framework: str
    violation: bool
    severity: Literal["low", "medium", "high", "critical"]
    reasoning: str
    cited_control_text: str


class VerifiedFinding(Finding):
    verification_status: Literal["confirmed", "rejected", "uncertain"]
    verification_note: str
