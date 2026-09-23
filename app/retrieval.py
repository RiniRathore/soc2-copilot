from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

from app.config import settings
from app.models import ControlChunk, ResourceConfig

_engine = create_engine(settings.database_url)
_model = SentenceTransformer(settings.embedding_model_name)  # loaded once, reused


def _resource_to_query_text(resource: ResourceConfig) -> str:
    """Turn a structured resource into a short natural-language query.

    This is the one place structured infra data touches the embedding
    model -- only to EMBED A QUERY, not to store the resource itself.
    Nothing about this resource gets written back into control_chunks.
    """
    return f"{resource.resource_type} named {resource.name} with config {resource.config}"


def retrieve_relevant_controls(
    resource: ResourceConfig, top_k: int | None = None
) -> list[ControlChunk]:
    top_k = top_k or settings.retrieval_top_k
    query_text = _resource_to_query_text(resource)
    query_embedding = _model.encode(query_text).tolist()

    with _engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT control_id, framework, text,
                       1 - (embedding <=> (:query_embedding)::vector) AS similarity
                FROM control_chunks
                ORDER BY embedding <=> (:query_embedding)::vector
                LIMIT :top_k
                """
            ),
            {"query_embedding": query_embedding, "top_k": top_k},
        ).fetchall()

    return [
        ControlChunk(
            control_id=row.control_id,
            framework=row.framework,
            text=row.text,
            similarity=float(row.similarity),
        )
        for row in rows
    ]
