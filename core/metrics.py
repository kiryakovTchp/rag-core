from __future__ import annotations

from typing import Optional

from prometheus_client import Counter


# Counters (no PII in labels)
rerank_timeouts: Optional[Counter] = None


def init_counters(enable: bool) -> None:
    global rerank_timeouts
    if enable:
        if rerank_timeouts is None:
            rerank_timeouts = Counter(
                "rag_rerank_timeouts_total",
                "Number of reranker timeouts",
                labelnames=("component",),
            )
    else:
        rerank_timeouts = None


def inc_rerank_timeout() -> None:
    if rerank_timeouts is not None:
        rerank_timeouts.labels(component="cross_encoder").inc()

