#!/usr/bin/env bash
set -euo pipefail

TS=$(date +%Y%m%d_%H%M%S)
OUT="reports/verify_${TS}"
mkdir -p "$OUT"

echo "1) Environment and containers" | tee -a "$OUT/steps.log"
cp -v .env.example .env | tee -a "$OUT/prep.log"
sed -i.bak 's/^ENABLE_METRICS=.*/ENABLE_METRICS=true/' .env
sed -i.bak 's/^HYBRID_ENABLED=.*/HYBRID_ENABLED=true/' .env
docker compose up --build -d | tee -a "$OUT/docker_up.log"

echo "2) Migrations" | tee -a "$OUT/steps.log"
alembic -c db/alembic.ini upgrade head | tee -a "$OUT/migrations.log"

echo "3) DB checks (extensions and indexes)" | tee -a "$OUT/steps.log"
docker compose exec -T db psql -U postgres -d postgres -c "\dx" | tee "$OUT/psql_extensions.txt"
docker compose exec -T db psql -U postgres -d postgres -c "\d+ documents" | tee "$OUT/psql_documents.txt"
docker compose exec -T db psql -U postgres -d postgres -c "\d+ chunks" | tee "$OUT/psql_chunks.txt"
docker compose exec -T db psql -U postgres -d postgres -c "\di+ ux_documents_sha256" | tee "$OUT/psql_index_sha256.txt"
docker compose exec -T db psql -U postgres -d postgres -c "\di+ ix_documents_created_at" | tee "$OUT/psql_index_created_at.txt"
docker compose exec -T db psql -U postgres -d postgres -c "\di+ ix_chunks_document_id" | tee "$OUT/psql_index_chunks_fk.txt"

echo "4) Health and warmup" | tee -a "$OUT/steps.log"
for i in {1..30}; do
  curl -s http://localhost:8000/healthz > "$OUT/healthz_${i}.json" || true
  jq . "$OUT/healthz_${i}.json" 2>/dev/null || cat "$OUT/healthz_${i}.json"
  if grep -q '"models_ready": true' "$OUT/healthz_${i}.json"; then
    break
  fi
  sleep 1
done

echo "5) Limits and content-type" | tee -a "$OUT/steps.log"
MAX_MB=$(grep '^MAX_UPLOAD_MB=' .env | cut -d= -f2)
BIG=$((MAX_MB+5))
dd if=/dev/zero of="$OUT/big.txt" bs=1M count=$BIG status=none
curl -s -o "$OUT/resp_413.json" -w "%{http_code}\n" -F "file=@$OUT/big.txt;type=text/plain" http://localhost:8000/ingest | tee "$OUT/http_413.txt"
echo 'test' > "$OUT/bad.bin"
curl -s -o "$OUT/resp_415.json" -w "%{http_code}\n" -F "file=@$OUT/bad.bin;type=application/octet-stream" http://localhost:8000/ingest | tee "$OUT/http_415.txt"

echo "6) Ingest TXT/PDF/DOCX and idempotency" | tee -a "$OUT/steps.log"
echo 'FastAPI is a modern, fast web framework for building APIs with Python.' > "$OUT/sample.txt"
curl -s -F "file=@$OUT/sample.txt;type=text/plain" http://localhost:8000/ingest | tee "$OUT/ingest_txt_1.json"
DOC_ID=$(jq -r '.doc_id' "$OUT/ingest_txt_1.json")
curl -s -F "file=@$OUT/sample.txt;type=text/plain" http://localhost:8000/ingest | tee "$OUT/ingest_txt_2.json"

# Create small PDF via PyMuPDF
python - "$OUT/sample.pdf" <<'PY'
import sys, fitz
path = sys.argv[1]
doc = fitz.open()
page = doc.new_page()
page.insert_text((72,72), "Sample PDF with Markdown mention.")
doc.save(path)
doc.close()
PY
curl -s -F "file=@$OUT/sample.pdf;type=application/pdf" http://localhost:8000/ingest | tee "$OUT/ingest_pdf.json"

# Create DOCX
python - "$OUT/sample.docx" <<'PY'
from docx import Document
import sys
d = Document()
d.add_paragraph("Hello DOCX world. This is a test document.")
d.save(sys.argv[1])
PY
curl -s -F "file=@$OUT/sample.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" http://localhost:8000/ingest | tee "$OUT/ingest_docx.json"

echo "7) Documents pagination and search" | tee -a "$OUT/steps.log"
curl -s "http://localhost:8000/documents?limit=5&offset=0" | tee "$OUT/documents_page1.json"
curl -s "http://localhost:8000/documents?limit=5&offset=5" | tee "$OUT/documents_page2.json"
curl -s "http://localhost:8000/documents?q=sample" | tee "$OUT/documents_search.json"

echo "8) Query with and without filters" | tee -a "$OUT/steps.log"
curl -s -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"query":"FastAPI", "top_k":5}' | tee "$OUT/query_base.json"
curl -s -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"query":"FastAPI", "top_k":5, "doc_id":"'"$DOC_ID"'"}' | tee "$OUT/query_doc_filter.json"
curl -s -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"query":"Markdown", "top_k":5, "source":"pdf"}' | tee "$OUT/query_meta_filter.json"

echo "9) Hybrid retrieval and eval" | tee -a "$OUT/steps.log"
curl -s -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"query":"FastAPI", "top_k":5, "hybrid": true}' | tee "$OUT/query_hybrid.json"
python scripts/eval.py | tee "$OUT/eval_run.log"
cp -v reports/*.csv "$OUT/" 2>/dev/null || true
cp -v reports/summary.md "$OUT/" 2>/dev/null || true

echo "10) Metrics scrape" | tee -a "$OUT/steps.log"
curl -s http://localhost:8000/metrics | tee "$OUT/metrics.txt" >/dev/null

echo "11) X-Request-ID propagation check" | tee -a "$OUT/steps.log"
curl -s -D "$OUT/query_headers.txt" -o "$OUT/query_with_header.json" -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"query":"FastAPI", "top_k":3}' >/dev/null
REQ_ID=$(grep -i '^X-Request-ID:' "$OUT/query_headers.txt" | awk '{print $2}' | tr -d '\r')
echo "Captured X-Request-ID: $REQ_ID" | tee -a "$OUT/steps.log"

echo "Done. Artifacts in $OUT" | tee -a "$OUT/steps.log"

