from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.schemas import DocumentItem
from db.base import SessionLocal
from db.models import Chunk, Document


router = APIRouter(prefix="", tags=["documents"])


@router.get("/documents")
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="Filter by filename substring"),
) -> list[DocumentItem]:
    with SessionLocal() as session:
        query = (
            select(
                Document.id,
                Document.filename,
                Document.created_at,
                Document.meta,
                func.count(Chunk.id).label("chunks"),
            )
            .join(Chunk, Chunk.document_id == Document.id, isouter=True)
            .group_by(Document.id)
            .order_by(Document.created_at.desc())
        )
        if q:
            # Case-insensitive substring match
            query = query.where(Document.filename.ilike(f"%{q}%"))
        query = query.limit(limit).offset(offset)
        rows = session.execute(query).all()

    items: list[DocumentItem] = []
    for r in rows:
        items.append(
            DocumentItem(
                id=str(r.id),
                filename=r.filename,
                created_at=(r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at)),
                chunks=int(r.chunks),
                meta=r.meta,
            )
        )
    return items
