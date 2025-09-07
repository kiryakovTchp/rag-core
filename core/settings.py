import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv(override=False)


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "y"}


@dataclass
class Settings:
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    json_logs: bool = _get_bool("JSON_LOGS", True)

    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/postgres"
    )
    pgvector_collection: str = os.getenv("PGVECTOR_COLLECTION", "rag_embeddings")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    rerank_model: str = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "75"))
    top_k: int = int(os.getenv("TOP_K", "5"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    rerank_timeout_seconds: int = int(os.getenv("RERANK_TIMEOUT_SECONDS", "10"))
    enable_metrics: bool = _get_bool("ENABLE_METRICS", True)

    # Hybrid retrieval
    hybrid_enabled: bool = _get_bool("HYBRID_ENABLED", False)
    hybrid_weight: float = float(os.getenv("HYBRID_WEIGHT", "0.6"))
    hybrid_topn: int = int(os.getenv("HYBRID_TOPN", "50"))

    # Eval
    eval_top_k: int = int(os.getenv("EVAL_TOP_K", "5"))

    # Models
    warmup_models: bool = _get_bool("WARMUP_MODELS", True)


settings = Settings()
