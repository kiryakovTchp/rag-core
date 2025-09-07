from __future__ import annotations

from fastapi import APIRouter

from app.schemas import QueryRequest, QueryResponse, QueryResult
from core.retrieval import retrieve


router = APIRouter(prefix="", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest) -> QueryResponse:
    filters = {
        k: v
        for k, v in {
            "doc_id": body.doc_id,
            "source": body.source,
            "section": body.section,
        }.items()
        if v is not None
    }
    results_raw = retrieve(
        body.query,
        top_k=body.top_k,
        rerank=body.rerank,
        filters=filters or None,
        hybrid=body.hybrid,
    )
    results = [QueryResult(**r) for r in results_raw]
    return QueryResponse(results=results)
