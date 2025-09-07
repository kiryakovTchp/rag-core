#!/usr/bin/env python
from __future__ import annotations

import httpx


def main() -> int:
    api = "http://localhost:8000"
    docs = [
        ("doc1.txt", b"FastAPI is a modern, fast web framework for building APIs with Python."),
        ("doc2.txt", b"This sample document mentions Markdown and PDF to test parsing searches."),
    ]
    with httpx.Client(timeout=60) as client:
        for name, data in docs:
            files = {"file": (name, data, "text/plain")}
            r = client.post(f"{api}/ingest", files=files)
            r.raise_for_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

