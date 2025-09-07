#!/usr/bin/env python
from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import httpx
import yaml


API = os.getenv("API_URL", "http://localhost:8000")
TOP_K = int(os.getenv("EVAL_TOP_K", os.getenv("TOP_K", "5")))


def metrics_at_k(ranked_texts: List[str], expected_contains: str) -> Dict[str, float]:
    # Simple contains-based relevance
    relevant = [1 if expected_contains.lower() in t.lower() else 0 for t in ranked_texts]
    # hit@k
    hit = 1.0 if any(relevant[:TOP_K]) else 0.0
    # MRR
    try:
        first = relevant.index(1) + 1
        mrr = 1.0 / first
    except ValueError:
        mrr = 0.0
    # nDCG
    import math

    dcg = 0.0
    for i, rel in enumerate(relevant[:TOP_K], start=1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    idcg = 1.0  # best case: one relevant at rank 1
    ndcg = dcg / idcg if idcg else 0.0
    return {"hit@k": hit, "mrr": mrr, "ndcg": ndcg}


def main() -> int:
    fixtures = Path("tests/eval/fixtures.yaml")
    if not fixtures.exists():
        print("fixtures not found", file=sys.stderr)
        return 1
    data = yaml.safe_load(fixtures.read_text())

    rows: List[Dict[str, str]] = []
    summary = {"hit@k": 0.0, "mrr": 0.0, "ndcg": 0.0, "n": 0}

    with httpx.Client(timeout=30) as client:
        for case in data:
            q = case["query"]
            expect = case["expect"].get("contains")
            resp = client.post(f"{API}/query", json={"query": q, "top_k": TOP_K})
            resp.raise_for_status()
            results = resp.json().get("results", [])
            texts = [r.get("text", "") for r in results]
            m = metrics_at_k(texts, expect)
            summary["hit@k"] += m["hit@k"]
            summary["mrr"] += m["mrr"]
            summary["ndcg"] += m["ndcg"]
            summary["n"] += 1
            rows.append({"query": q, **{k: str(v) for k, v in m.items()}})

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    csv_path = reports / f"eval_{ts}.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query", "hit@k", "mrr", "ndcg"])
        w.writeheader()
        w.writerows(rows)

    avg = {k: (summary[k] / summary["n"] if summary["n"] else 0.0) for k in ("hit@k", "mrr", "ndcg")}
    md_path = reports / "summary.md"
    md_path.write_text(
        f"# Eval Summary\n\nN={summary['n']} TOP_K={TOP_K}\n\n"
        f"- hit@k: {avg['hit@k']:.3f}\n- MRR: {avg['mrr']:.3f}\n- nDCG: {avg['ndcg']:.3f}\n"
    )
    print(f"Wrote {csv_path} and {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

