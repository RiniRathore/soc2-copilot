"""
Run once (or whenever the source docs change) to (re)build the knowledge base.

    python -m app.knowledge_base.ingest

This is deliberately NOT part of the runtime scan pipeline. Infra config
never touches this table -- only static policy/control text lives here.
"""
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

from app.config import settings

KB_DIR = Path(__file__).parent
SOURCES = {
    "SOC2": KB_DIR / "controls_soc2.md",
    "CIS_AWS": KB_DIR / "controls_cis_aws.md",
}

# Header is "## CONTROL_ID" or "## CONTROL_ID [ORG]" -- the optional [ORG]
# tag marks an organizational/process control (board oversight, vendor risk
# management, etc.) that no infra scan can ever confirm or violate. Drives
# ControlChunk.checkable / the honest coverage summary in ScanResponse.
CONTROL_HEADER_RE = re.compile(r"^##\s+(\S+?)(?:\s+\[(\w+)\])?\s*$", re.MULTILINE)


def parse_controls(md_text: str) -> list[tuple[str, str, bool]]:
    """Split a markdown file into (control_id, control_body, checkable) chunks.

    Chunking is per-control, not per-character-count -- each control is
    a coherent unit of meaning, so that's the right chunk boundary here.
    """
    parts = CONTROL_HEADER_RE.split(md_text)
    # parts[0] is anything before the first header (should be empty/whitespace)
    chunks = []
    for i in range(1, len(parts), 3):
        control_id = parts[i].strip()
        tag = parts[i + 1]
        body = parts[i + 2].strip()
        chunks.append((control_id, body, tag != "ORG"))
    return chunks


def ensure_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS control_chunks (
                    id SERIAL PRIMARY KEY,
                    control_id TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    text TEXT NOT NULL,
                    checkable BOOLEAN NOT NULL DEFAULT TRUE,
                    embedding vector({settings.embedding_dim})
                );
                """
            )
        )
        # idempotent migration for a table created before `checkable` existed
        conn.execute(
            text("ALTER TABLE control_chunks ADD COLUMN IF NOT EXISTS checkable BOOLEAN NOT NULL DEFAULT TRUE;")
        )


def main():
    print(f"Loading embedding model: {settings.embedding_model_name}")
    model = SentenceTransformer(settings.embedding_model_name)

    engine = create_engine(settings.database_url)
    ensure_schema(engine)

    with engine.begin() as conn:
        # idempotent: wipe and reload on every run of this script
        conn.execute(text("DELETE FROM control_chunks;"))

        for framework, path in SOURCES.items():
            md_text = path.read_text()
            for control_id, body, checkable in parse_controls(md_text):
                embedding = model.encode(body).tolist()
                conn.execute(
                    text(
                        """
                        INSERT INTO control_chunks (control_id, framework, text, checkable, embedding)
                        VALUES (:control_id, :framework, :text, :checkable, :embedding)
                        """
                    ),
                    {
                        "control_id": control_id,
                        "framework": framework,
                        "text": body,
                        "checkable": checkable,
                        "embedding": embedding,
                    },
                )
                print(f"  ingested {framework} {control_id}{'' if checkable else ' [ORG]'}")

    print("Knowledge base ready.")


if __name__ == "__main__":
    main()
