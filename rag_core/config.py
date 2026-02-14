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
CONFIG_DIR = DATA_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required. This project is configured to use Supabase only.")
    return value


@dataclass(frozen=True)
class AppSettings:
    app_name: str = os.getenv("APP_NAME", "RAG Chatbot")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    database_url: str = _required_env("SUPABASE_DB_URL")

    uploads_dir: Path = UPLOAD_DIR
    chroma_dir: Path = CHROMA_DIR
    secrets_dir: Path = SECRETS_DIR
    config_dir: Path = CONFIG_DIR
    settings_file: Path = SETTINGS_FILE

    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")

    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    supabase_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "documents")
    supabase_storage_prefix: str = os.getenv("SUPABASE_STORAGE_PREFIX", "documents")

    doc_storage_backend: str = os.getenv("DOC_STORAGE_BACKEND", "").strip().lower()


settings = AppSettings()
