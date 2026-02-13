from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
SECRETS_DIR = DATA_DIR / "secrets"


@dataclass(frozen=True)
class AppSettings:
    app_name: str = os.getenv("APP_NAME", "RAG Chatbot")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    database_url: str = os.getenv("SUPABASE_DB_URL") or os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@db.<project-ref>.supabase.co:5432/postgres?sslmode=require",
    )
    uploads_dir: Path = UPLOAD_DIR
    chroma_dir: Path = CHROMA_DIR
    secrets_dir: Path = SECRETS_DIR
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


settings = AppSettings()
