from rag_core.config import settings
from rag_core.storage.base import DocumentStorage, DocumentStorageError, StoredDocument
from rag_core.storage.local import LocalStorage
from rag_core.storage.supabase import SupabaseStorage


def get_storage_backend() -> DocumentStorage:
    backend = (settings.doc_storage_backend or "").lower()

    if backend == "supabase":
        return SupabaseStorage()
    if backend == "local":
        return LocalStorage()

    if settings.supabase_url and settings.supabase_service_key:
        try:
            return SupabaseStorage()
        except DocumentStorageError:
            return LocalStorage()

    return LocalStorage()


__all__ = [
    "DocumentStorage",
    "DocumentStorageError",
    "StoredDocument",
    "LocalStorage",
    "SupabaseStorage",
    "get_storage_backend",
]
