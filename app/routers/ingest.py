from __future__ import annotations

import hashlib
import io
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from sqlalchemy import func, select

from core.chunking import chunk_pages
from core.parsing import parse_pdf, parse_txt, parse_docx
from core.vectorstore import add_texts
from db.base import SessionLocal
from db.models import Chunk, Document


logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["ingest"])


ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


@router.post("/ingest")
async def ingest(request: Request, file: UploadFile = File(...)):
    # Validate content length (header-based)
    try:
        cl = int(request.headers.get("content-length", "0"))
    except ValueError:
        cl = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if cl and cl > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.max_upload_mb}MB")
    filename = file.filename
    raw = await file.read()
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.max_upload_mb}MB")
    size = len(raw)
    sha256 = hashlib.sha256(raw).hexdigest()

    # Idempotency: (filename, size, hash)
    with SessionLocal() as session:
        existing = session.execute(
            select(Document).where(
                func.coalesce(Document.meta["sha256"].astext, "") == sha256,
            )
        ).scalars().first()
        if existing:
            chunks_count = session.execute(
                select(func.count()).select_from(Chunk).where(Chunk.document_id == existing.id)
            ).scalar_one()
            return {"doc_id": str(existing.id), "stats": {"chunks": chunks_count, "tokens": None}}

    # Parse
    content_type = file.content_type or ""
    ext = os.path.splitext(filename or "")[1].lower()
    pages: List[Dict[str, Any]]
    try:
        if ext == ".pdf" or content_type == "application/pdf":
            pages = parse_pdf(raw)
        elif ext in (".txt", "") or content_type.startswith("text/"):
            pages = parse_txt(raw.decode("utf-8", errors="ignore"))
        elif ext in (".docx",) or (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            pages = parse_docx(raw)
        else:
            # Strict content-type validation
            if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}")
            raise HTTPException(status_code=415, detail="Unsupported file type")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Parsing failed")
        raise HTTPException(status_code=400, detail=f"Parsing failed: {e}")

    chunks = chunk_pages(pages)
    approx_tokens = sum(len((c["content"] or "").split()) for c in chunks)

    # Persist
    from uuid import uuid4

    with SessionLocal() as session:
        doc = Document(
            id=uuid4(),
            filename=filename,
            meta={"sha256": sha256, "size": size},
        )
        session.add(doc)
        session.flush()

        chunk_rows: List[Chunk] = []
        for c in chunks:
            chunk_rows.append(
                Chunk(
                    id=uuid4(),
                    document_id=doc.id,
                    content=c["content"],
                    page=c.get("page"),
                    meta=c.get("meta"),
                )
            )
        session.add_all(chunk_rows)
        session.commit()

    # Store vectors via PGVector
    texts = [c["content"] for c in chunks]
    metas = [
        {
            **(c.get("meta") or {}),
            "doc_id": str(doc.id),
            "page": c.get("page"),
            "source": (c.get("meta") or {}).get("source"),
        }
        for c in chunks
    ]
    try:
        add_texts(texts, metas)
    except Exception:
        logger.exception("Failed to add to vectorstore")
        # best-effort: keep DB state consistent even if vectorstore fails

    return {"doc_id": str(doc.id), "stats": {"chunks": len(chunks), "tokens": approx_tokens}}
