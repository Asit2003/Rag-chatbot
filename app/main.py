from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import chat, files, pages, settings
from rag_core.config import settings as app_settings
from rag_core.db import Base
from rag_core.db.session import engine


def ensure_dirs() -> None:
    for path in [
        app_settings.uploads_dir,
        app_settings.chroma_dir,
        app_settings.secrets_dir,
        app_settings.config_dir,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def create_app() -> FastAPI:
    ensure_dirs()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title=app_settings.app_name, version="1.0.0")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(pages.router)
    app.include_router(files.router)
    app.include_router(settings.router)
    app.include_router(chat.router)

    return app


app = create_app()
