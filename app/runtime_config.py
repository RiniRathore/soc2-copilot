"""
Holds credentials/config supplied at runtime via the Streamlit settings
panel, as an alternative to editing .env by hand.

IMPORTANT, be honest with yourself about this: this is in-memory only,
lives for as long as the FastAPI process runs, and is never written to
disk or logged. That's a reasonable trade-off for a single-user local
demo. It is NOT how you'd handle secrets in a real multi-tenant SaaS --
that needs a proper secrets manager (e.g. AWS Secrets Manager, GCP
Secret Manager, Vault) with encryption at rest, per-tenant isolation,
and audit logging. Don't carry this pattern into the real product
without that upgrade.
"""
from pydantic import BaseModel


class RuntimeConfig(BaseModel):
    gemini_api_key: str | None = None
    github_token: str | None = None
    github_repo: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str | None = None
    gcp_project_id: str | None = None
    gcp_service_account_json: str | None = None  # pasted JSON, not a file path


# Single in-memory instance. Overwritten wholesale by POST /configure.
_current = RuntimeConfig()


def set_runtime_config(config: RuntimeConfig) -> None:
    global _current
    _current = config


def get_runtime_config() -> RuntimeConfig:
    return _current
