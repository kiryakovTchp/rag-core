from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> List[str]:
    return [t for t in text.lower().split() if t]


def bm25_scores(query: str, docs: List[str]) -> List[float]:
    tokenized_corpus = [_tokenize(d) for d in docs]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(_tokenize(query))
    return list(map(float, scores))

