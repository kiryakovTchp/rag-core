from __future__ import annotations

import os
import yaml

import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.eval


def require_postgres() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("postgresql")


@pytest.mark.skipif(not require_postgres(), reason="Postgres required for eval test")
def test_hybrid_not_worse_hit_at_5(tmp_path):
    client = TestClient(app)

    # Seed small set
    files = [
        ("doc1.txt", b"FastAPI is a modern, fast web framework for building APIs with Python."),
        ("doc2.txt", b"This sample document mentions Markdown and PDF to test parsing searches."),
    ]
    for name, data in files:
        r = client.post("/ingest", files={"file": (name, data, "text/plain")})
        assert r.status_code == 200

    fixtures_path = os.path.join("tests", "eval", "fixtures.yaml")
    cases = yaml.safe_load(open(fixtures_path, "r").read())

    def hit_at_5(hybrid: bool) -> float:
        hits = 0
        for c in cases:
            q = c["query"]
            expect = c["expect"]["contains"].lower()
            r = client.post("/query", json={"query": q, "top_k": 5, "hybrid": hybrid})
            assert r.status_code == 200
            texts = [x["text"].lower() for x in r.json().get("results", [])]
            hits += 1 if any(expect in t for t in texts[:5]) else 0
        return hits / max(1, len(cases))

    base = hit_at_5(False)
    hyb = hit_at_5(True)
    assert hyb >= base

