from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from core.embeddings import get_embeddings
from core.settings import settings

logger = logging.getLogger(__name__)

_models_ready = False


def warmup() -> None:
    global _models_ready
    t0 = time.time()
    try:
        # Embeddings
        _ = get_embeddings()
        logger.info("embeddings_warmup_completed")
        # Optional reranker warmup
        try:
            from sentence_transformers import CrossEncoder  # noqa: F401

            # Do not instantiate here to avoid heavy cost if not used; import ensures availability
            logger.info("reranker_import_ready")
        except Exception:
            logger.info("reranker_not_available")
        _models_ready = True
    finally:
        logger.info("models_warmup_time", extra={"duration": round(time.time() - t0, 3)})


def warmup_async() -> None:
    th = threading.Thread(target=warmup, daemon=True)
    th.start()


def models_ready() -> bool:
    return _models_ready

