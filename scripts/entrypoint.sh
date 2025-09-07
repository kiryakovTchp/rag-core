#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for database..."
python - <<'PY'
import os, time
import psycopg

dsn = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/postgres")
dsn_native = dsn.replace("+psycopg", "")
for _ in range(60):
    try:
        with psycopg.connect(dsn_native) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print("DB ready")
                raise SystemExit(0)
    except Exception as e:
        print("DB not ready yet:", e)
        time.sleep(2)
raise SystemExit(1)
PY

echo "Running migrations..."
alembic -c db/alembic.ini upgrade head

echo "Starting app..."
exec uvicorn app.main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}

