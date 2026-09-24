import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # API auth -- required on every endpoint except /health. See
    # app/main.py's require_api_key. Not set = the app refuses requests
    # rather than running open to anyone who can reach it.
    api_key: str = os.getenv("API_KEY", "")

    # LLM (Gemini free tier -- see app/reasoning_agent.py / self_check.py)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    # Pinned, not a "-latest" alias -- an alias can silently repoint to a
    # different underlying model (different quota, different behavior)
    # with no code change on our end. Confirmed this actually happens:
    # gemini-flash-lite-latest resolved to a different model 13 days
    # after this project started. Upgrading the pin is a deliberate,
    # tested decision, not something that should happen by itself.
    reasoning_model: str = os.getenv("REASONING_MODEL", "gemini-3.5-flash-lite")

    # DB
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://soc2:soc2@localhost:5432/soc2_copilot"
    )

    # Terraform state files may only be read from within this directory --
    # /scan's terraform_state_path is client-supplied, so without this the
    # endpoint would let any caller read arbitrary files off the server.
    terraform_state_dir: str = os.getenv("TERRAFORM_STATE_DIR", "seed_data")

    # GitHub
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")

    # Cloud provider
    cloud_provider: str = os.getenv("CLOUD_PROVIDER", "aws")
    aws_profile: str = os.getenv("AWS_PROFILE", "default")
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")

    # Langfuse
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # Embeddings
    embedding_model_name: str = "all-MiniLM-L6-v2"  # 384-dim, fast, local
    embedding_dim: int = 384
    retrieval_top_k: int = 3


settings = Settings()
