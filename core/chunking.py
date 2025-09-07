from __future__ import annotations

from typing import Any, Dict, Iterable, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.settings import settings


def chunk_pages(
    pages: Iterable[Dict[str, Any]],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Split pages into chunks preserving metadata.
    Returns [{content, page, meta}]
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        disallowed_special=(),
    )
    chunks: List[Dict[str, Any]] = []
    for page in pages:
        text = page["content"]
        page_num = page.get("page")
        meta = dict(page.get("meta") or {})
        for part in splitter.split_text(text):
            chunks.append({
                "content": part,
                "page": page_num,
                "meta": meta,
            })
    return chunks
