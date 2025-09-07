from __future__ import annotations

from typing import Any, Iterable, List, Tuple

from langchain_postgres.vectorstores import PGVector

from core.embeddings import get_embeddings
from core.settings import settings


def get_pgvector() -> PGVector:
    return PGVector(
        connection_string=settings.database_url,
        collection_name=settings.pgvector_collection,
        embedding_function=get_embeddings(),
        use_jsonb=True,
    )


def add_texts(texts: List[str], metadatas: List[dict[str, Any]]) -> List[str]:
    vs = get_pgvector()
    ids = vs.add_texts(texts=texts, metadatas=metadatas)
    return ids


def similarity_search_with_score(query: str, k: int, metadata_filter: dict | None = None) -> List[Tuple[Any, float]]:
    vs = get_pgvector()
    return vs.similarity_search_with_score(query, k=k, filter=metadata_filter)
