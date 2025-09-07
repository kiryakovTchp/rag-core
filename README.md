RAG-CORE

Minimal RAG core with FastAPI, PostgreSQL (pgvector), and LangChain.

Features
- Ingest endpoint for txt/pdf: parsing → chunking → embeddings → pgvector store
- Query endpoint with topK similarity search and optional rerank
- Documents listing and health checks
- Alembic migrations with pgvector extension
- Docker Compose for local dev
- JSON logs with request_id
 - Prometheus metrics (optional) at /metrics

Quick Start
1) Create env file:
   cp .env.example .env

2) Build and run:
   docker compose up --build

3) Open API docs:
   http://localhost:8000/docs

Database Migrations
- To apply migrations inside Docker: they run on app start.
- To run locally:
  alembic -c db/alembic.ini upgrade head

Testing
- Run unit tests:
  pytest -q

- Integration tests (require running Postgres with pgvector and embedding models accessible):
  DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/postgres pytest -m integration -q

Conventions
- Conventional Commits
- ruff, black, mypy via pre-commit

Directory Structure
- /app            FastAPI app (routes, schemas)
- /core           Core: parsing, chunking, embeddings, vectorstore, retrieval
- /core/parsing   PDF/TXT parsers
- /db             Alembic config and migrations
- /tests          Tests
- /docs/adr       Architecture Decision Records
- /scripts        Entry points and helpers

API Examples

- Ingest TXT:
  curl -X POST -F "file=@/path/to/file.txt;type=text/plain" http://localhost:8000/ingest

- Ingest PDF:
  curl -X POST -F "file=@/path/to/file.pdf;type=application/pdf" http://localhost:8000/ingest

- Ingest DOCX:
  curl -X POST -F "file=@/path/to/file.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" http://localhost:8000/ingest

- Query (with filters):
  curl -X POST http://localhost:8000/query \
    -H 'Content-Type: application/json' \
    -d '{"query":"what is FastAPI?", "top_k":5, "rerank":false, "source":"pdf"}'

- Documents (pagination and search by filename):
  curl "http://localhost:8000/documents?limit=10&offset=0&q=report"

Limits & Errors
- Max upload: 25MB → returns 413 if exceeded
- Strict content-type validation → returns 415 for unsupported types

Observability
- Enable metrics with `ENABLE_METRICS=true`. Exposed at `/metrics` with request counts, latency histograms, response sizes, error codes.
- Custom counter: `rag_rerank_timeouts_total` increments when reranker times out.
- Logs are JSON and include `request_id`; the same `X-Request-ID` header is returned in responses.

Hybrid Retrieval
- Optional BM25 + vector fusion. Enable via `HYBRID_ENABLED=true` or per-request `{ "hybrid": true }`.
- Fusion score: `alpha * norm_vector + (1-alpha) * norm_bm25` with `HYBRID_WEIGHT` (default 0.6). Vector candidates topN via `HYBRID_TOPN`.

Eval
- Fixtures: `tests/eval/fixtures.yaml` (query and expected contains).
- Run local eval against running API:
  python scripts/eval.py
- Reports saved to `reports/` (CSV and summary.md). CI uploads as artifact.

Verification
- Prep:
  - cp .env.example .env
  - Set: `ENABLE_METRICS=true`, `HYBRID_ENABLED=true`, `HYBRID_WEIGHT=0.6`, `HYBRID_TOPN=50`
  - docker compose up --build -d
  - alembic -c db/alembic.ini upgrade head

- Automated script (artifacts in `reports/verify_{ts}`):
  bash scripts/verify.sh

- Manual checks (examples):
  - Health: curl -s :8000/healthz | jq .
  - Metrics: curl -s :8000/metrics | head -n 50
  - Ingest TXT: curl -F "file=@sample.txt;type=text/plain" :8000/ingest
  - Query hybrid: curl -X POST :8000/query -H 'Content-Type: application/json' -d '{"query":"FastAPI","top_k":5,"hybrid":true}'

SLO (MVP targets, no strict enforcement)
- /query without rerank p95 ≤ 350ms; with rerank p95 ≤ 1.2s (topN=50)
- /ingest TXT 1MB ≤ 2s; PDF 10MB ≤ 20s
- 5xx ≤ 1% per hour; reranker timeouts ≤ 5% when rerank=true

Security (MVP)
- API key and CORS are not enabled by default; add in a follow-up iteration if required. Docker image runs as root in dev for simplicity.
