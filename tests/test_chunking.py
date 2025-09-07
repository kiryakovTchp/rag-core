from __future__ import annotations

from core.chunking import chunk_pages


def test_token_based_chunking_is_stable_by_spaces():
    text_a = "word " * 1000
    text_b = ("word\n" * 500) + ("word  " * 500)
    pages_a = [{"content": text_a, "page": 1, "meta": {"source": "txt"}}]
    pages_b = [{"content": text_b, "page": 1, "meta": {"source": "txt"}}]

    chunks_a = chunk_pages(pages_a, chunk_size=200, chunk_overlap=50)
    chunks_b = chunk_pages(pages_b, chunk_size=200, chunk_overlap=50)

    # Token-based splitter should produce roughly similar counts regardless of whitespace distribution
    assert abs(len(chunks_a) - len(chunks_b)) <= 2

