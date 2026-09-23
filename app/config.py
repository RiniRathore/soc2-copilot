import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM (Gemini free tier -- see app/reasoning_agent.py / self_check.py)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    reasoning_model: str = os.getenv("REASONING_MODEL", "gemini-flash-lite-latest")

    # DB
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://soc2:soc2@localhost:5432/soc2_copilot"
    )

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
