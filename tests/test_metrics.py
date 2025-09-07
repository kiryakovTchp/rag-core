from __future__ import annotations

import os
from fastapi.testclient import TestClient

os.environ.setdefault("ENABLE_METRICS", "true")

from app.main import app  # noqa: E402


def test_metrics_endpoint_available():
    with TestClient(app) as client:
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "requests" in r.text
