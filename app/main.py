from __future__ import annotations

import logging
from typing import Callable

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from core.logging import configure_json_logging, new_request_id, request_id_ctx
from core.settings import settings
from core.metrics import init_counters
from core import models as core_models

from app.routers import ingest, query, documents, health


if settings.json_logs:
    configure_json_logging(settings.log_level)
else:
    logging.basicConfig(level=settings.log_level)

app = FastAPI(title="RAG Core", version="0.1.0")


@app.middleware("http")
async def add_request_id(request: Request, call_next: Callable):
    rid = request.headers.get("X-Request-ID") or new_request_id()
    token = request_id_ctx.set(rid)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        request_id_ctx.reset(token)


app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(documents.router)
app.include_router(health.router)


@app.on_event("startup")
async def startup_event() -> None:
    # Metrics
    init_counters(settings.enable_metrics)
    if settings.enable_metrics:
        Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")

    # Models warmup in background
    if settings.warmup_models:
        core_models.warmup_async()
