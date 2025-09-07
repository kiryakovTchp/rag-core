from __future__ import annotations

from typing import Any, Dict, List

from core.settings import settings
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging
from time import perf_counter

from core.vectorstore import similarity_search_with_score
from core.metrics import inc_rerank_timeout
from core.bm25 import bm25_scores
from core.settings import settings


logger = logging.getLogger(__name__)


def _normalize(scores: list[float]) -> list[float]:
    if not scores:
        return []
    mn, mx = min(scores), max(scores)
    if mx - mn < 1e-9:
        return [0.5 for _ in scores]
    return [(s - mn) / (mx - mn) for s in scores]


def retrieve(
    query: str,
    top_k: int,
    rerank: bool = False,
    filters: Dict[str, Any] | None = None,
    hybrid: bool | None = None,
) -> List[Dict[str, Any]]:
    req_hybrid = settings.hybrid_enabled if hybrid is None else hybrid
    # First pass with vector similarity
    initial_k = max(top_k, settings.hybrid_topn) if (rerank or req_hybrid) else top_k
    metadata_filter: Dict[str, Any] | None = None
    if filters:
        metadata_filter = {}
        if filters.get("doc_id"):
            metadata_filter["doc_id"] = str(filters["doc_id"])
        if filters.get("source"):
            metadata_filter["source"] = filters["source"]
        if filters.get("section"):
            metadata_filter["section"] = filters["section"]

    docs_scores = similarity_search_with_score(query, k=initial_k, metadata_filter=metadata_filter)

    results = [
        {
            "text": doc.page_content,
            "score": float(score),
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
            "section": doc.metadata.get("section"),
            "doc_id": doc.metadata.get("doc_id"),
        }
        for doc, score in docs_scores
    ]

    # Optional hybrid fusion with BM25 over candidates (or small global sample)
    if req_hybrid:
        t_h0 = perf_counter()
        texts = [r["text"] for r in results]
        if len(texts) < max(10, top_k):
            # Fallback: expand with more corpus by querying more vectors
            extra = similarity_search_with_score(query, k=settings.hybrid_topn * 2, metadata_filter=filters)
            texts = list({*texts, *[d.page_content for d, _ in extra]})
        bm25 = bm25_scores(query, texts)
        # Normalize both
        # Approximate cosine similarity from vector score (distance -> similarity)
        vec_scores = [r["score"] for r in results]
        vec_sims = _normalize([1.0 / (1.0 + s) for s in vec_scores]) if vec_scores else []
        bm25_norm = _normalize(bm25)
        # Align lengths
        L = min(len(vec_sims), len(bm25_norm))
        fused = []
        alpha = settings.hybrid_weight
        for i in range(L):
            fused.append(alpha * vec_sims[i] + (1 - alpha) * bm25_norm[i])
        # Apply fused scores back (scale to 0..1)
        for i in range(L):
            results[i]["score"] = float(fused[i])
        results.sort(key=lambda x: x["score"], reverse=True)
        logger.info("hybrid_fusion_completed")

    if rerank:
        def _do_rerank() -> List[float]:
            from sentence_transformers import CrossEncoder

            model = CrossEncoder(settings.rerank_model)
            pairs = [(query, r["text"]) for r in results]
            return list(map(float, model.predict(pairs)))

        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_do_rerank)
                scores = fut.result(timeout=settings.rerank_timeout_seconds)
            for r, s in zip(results, scores):
                r["score"] = float(s)
            results.sort(key=lambda x: x["score"], reverse=True)
        except (TimeoutError, Exception):
            # Fallback to vector scores on timeout or any failure
            inc_rerank_timeout()
            logger.warning("rerank_timeout_or_failure")

    return results[:top_k]
