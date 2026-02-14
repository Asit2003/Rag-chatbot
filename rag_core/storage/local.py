from __future__ import annotations

from pathlib import Path

from rag_core.config import settings
from rag_core.storage.base import DocumentStorage, DocumentStorageError, StoredDocument


class LocalStorage(DocumentStorage):
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or settings.uploads_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, doc_id: str, ext: str, content: bytes) -> StoredDocument:
        stored_name = f"{doc_id}{ext}"
        stored_path = self.root_dir / stored_name
        try:
            stored_path.write_bytes(content)
        except Exception as exc:
            raise DocumentStorageError(f"Failed to write file locally: {exc}") from exc
        return StoredDocument(stored_name=stored_name, size_bytes=len(content))

    def delete(self, stored_name: str) -> None:
        try:
            (self.root_dir / stored_name).unlink(missing_ok=True)
        except Exception:
            return

    def read_bytes(self, stored_name: str) -> bytes:
        path = self.root_dir / stored_name
        if not path.exists():
            raise DocumentStorageError("Stored file not found.")
        try:
            return path.read_bytes()
        except Exception as exc:
            raise DocumentStorageError(f"Failed to read file: {exc}") from exc

