from __future__ import annotations

import mimetypes

from supabase import Client, create_client

from rag_core.config import settings
from rag_core.storage.base import DocumentStorage, DocumentStorageError, StoredDocument


class SupabaseStorage(DocumentStorage):
    def __init__(
        self,
        url: str | None = None,
        service_key: str | None = None,
        bucket: str | None = None,
        prefix: str | None = None,
    ) -> None:
        self.url = url or settings.supabase_url
        self.service_key = service_key or settings.supabase_service_key
        self.bucket = bucket or settings.supabase_bucket
        self.prefix = (prefix or settings.supabase_storage_prefix or "").strip("/")

        if not self.url or not self.service_key:
            raise DocumentStorageError("Supabase URL/key missing for storage backend.")

        self.client: Client = create_client(self.url, self.service_key)
        self.storage = self.client.storage.from_(self.bucket)

    def _object_path(self, stored_name: str) -> str:
        if self.prefix:
            return f"{self.prefix}/{stored_name}"
        return stored_name

    def save_bytes(self, doc_id: str, ext: str, content: bytes) -> StoredDocument:
        stored_name = f"{doc_id}{ext}"
        object_path = self._object_path(stored_name)
        content_type, _ = mimetypes.guess_type(stored_name)
        try:
            response = self.storage.upload(
                object_path,
                content,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "upsert": "true",
                },
            )
            if isinstance(response, dict) and response.get("error"):
                raise DocumentStorageError(str(response["error"]))
        except Exception as exc:
            raise DocumentStorageError(f"Supabase upload failed: {exc}") from exc
        return StoredDocument(stored_name=stored_name, size_bytes=len(content))

    def delete(self, stored_name: str) -> None:
        object_path = self._object_path(stored_name)
        try:
            self.storage.remove([object_path])
        except Exception:
            return

    def read_bytes(self, stored_name: str) -> bytes:
        object_path = self._object_path(stored_name)
        try:
            data = self.storage.download(object_path)
        except Exception as exc:
            raise DocumentStorageError(f"Supabase download failed: {exc}") from exc
        if isinstance(data, bytes):
            return data
        if hasattr(data, "read"):
            return data.read()
        raise DocumentStorageError("Supabase download returned unexpected payload.")
