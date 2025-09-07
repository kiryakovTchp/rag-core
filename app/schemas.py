from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class IngestResponse(BaseModel):
    doc_id: str
    stats: dict


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    rerank: bool = False
    doc_id: Optional[str] = None
    source: Optional[str] = None
    section: Optional[str] = None
    hybrid: Optional[bool] = None


class QueryResult(BaseModel):
    text: str
    score: float
    source: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    doc_id: Optional[str] = None


class QueryResponse(BaseModel):
    results: List[QueryResult]


class DocumentItem(BaseModel):
    id: str
    filename: str
    created_at: str
    chunks: int
    meta: Any | None = None
