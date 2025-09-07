from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from core.settings import settings


@lru_cache(maxsize=1)
def get_embeddings() -> Any:
    model_name = settings.embedding_model
    return HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

