from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.integration


def require_postgres() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("postgresql")


@pytest.mark.skipif(not require_postgres(), reason="Postgres required for integration test")
def test_txt_ingest_and_query(tmp_path):
    client = TestClient(app)
    sample = tmp_path / "sample.txt"
    sample.write_text("Python is a programming language. FastAPI is a Python framework.")

    with sample.open("rb") as f:
        r = client.post("/ingest", files={"file": ("sample.txt", f, "text/plain")})
    assert r.status_code == 200, r.text
    doc = r.json()["doc_id"]
    assert doc

    r = client.post("/query", json={"query": "What is FastAPI?", "top_k": 3})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "results" in data
    assert len(data["results"]) >= 1


@pytest.mark.skipif(not require_postgres(), reason="Postgres required for integration test")
def test_docx_ingest(tmp_path):
    client = TestClient(app)

    # Minimal DOCX generation without external files
    try:
        from docx import Document as DocxDocument
    except Exception:
        pytest.skip("python-docx not available")

    docx_path = tmp_path / "sample.docx"
    d = DocxDocument()
    d.add_paragraph("Hello DOCX world. This is a test document.")
    d.save(docx_path)

    with docx_path.open("rb") as f:
        r = client.post(
            "/ingest",
            files={
                "file": (
                    "sample.docx",
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["doc_id"]
