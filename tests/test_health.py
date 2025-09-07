from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_keys_present():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert set(["db", "pgvector", "embeddings_model", "models_ready"]).issubset(data.keys())
