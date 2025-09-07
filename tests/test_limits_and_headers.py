from __future__ import annotations

import os
from fastapi.testclient import TestClient


os.environ.setdefault("MAX_UPLOAD_MB", "0")  # force tiny limit to trigger 413 easily
from app.main import app  # noqa: E402


def test_413_on_large_upload(tmp_path):
    client = TestClient(app)
    fpath = tmp_path / "big.txt"
    fpath.write_bytes(b"x" * 1024)  # 1KB exceeds 0MB limit
    with fpath.open("rb") as f:
        r = client.post("/ingest", files={"file": ("big.txt", f, "text/plain")})
    assert r.status_code == 413


def test_415_on_unsupported_content_type(tmp_path):
    client = TestClient(app)
    fpath = tmp_path / "bad.bin"
    fpath.write_bytes(b"test")
    with fpath.open("rb") as f:
        r = client.post("/ingest", files={"file": ("bad.bin", f, "application/octet-stream")})
    assert r.status_code == 415


def test_x_request_id_header_present():
    client = TestClient(app)
    r = client.post("/query", json={"query": "ping", "top_k": 1})
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers

