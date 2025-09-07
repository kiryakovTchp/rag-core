from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from core.embeddings import get_embeddings
from core.models import models_ready
from db.base import engine


router = APIRouter(prefix="", tags=["health"]) 


@router.get("/healthz")
async def healthz():
    db_ok = False
    vector_ok = False
    embed_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
            res = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')"))
            vector_ok = bool(res.scalar())
    except Exception:
        db_ok = False

    try:
        _ = get_embeddings()
        embed_ok = True
    except Exception:
        embed_ok = False

    return {"db": db_ok, "pgvector": vector_ok, "embeddings_model": embed_ok, "models_ready": models_ready()}
