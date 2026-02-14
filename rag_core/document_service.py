from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from rag_core.config import settings
from rag_core.document_parser import SUPPORTED_EXTENSIONS, DocumentParseError, parse_document_bytes
from rag_core.repositories import DocumentRepository
from rag_core.storage import DocumentStorage, DocumentStorageError
from rag_core.text_chunker import chunk_text
from rag_core.vector_store import VectorStore


class DocumentServiceError(Exception):
    pass


class DocumentService:
    def __init__(self, db: Session, vector_store: VectorStore, storage: DocumentStorage) -> None:
        self.repo = DocumentRepository(db)
        self.vector_store = vector_store
        self.storage = storage
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    def list_documents(self) -> list:
        return self.repo.list_documents()

    def get_document(self, doc_id: str):
        return self.repo.get(doc_id)

    async def upload(self, upload_file: UploadFile):
        original_name = (upload_file.filename or "").strip()
        if not original_name:
            raise DocumentServiceError("Missing filename.")

        ext = Path(original_name).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise DocumentServiceError(f"Unsupported file type '{ext}'. Allowed: PDF, DOCX, TXT.")

        content = await upload_file.read()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) == 0:
            raise DocumentServiceError("Uploaded file is empty.")
        if len(content) > max_bytes:
            raise DocumentServiceError(f"File exceeds {settings.max_upload_size_mb} MB limit.")

        doc_id = str(uuid4())

        try:
            raw_text = parse_document_bytes(ext, content)
            chunks = chunk_text(raw_text)
            if not chunks:
                raise DocumentServiceError("No readable text found in this file.")

            stored = self.storage.save_bytes(doc_id=doc_id, ext=ext, content=content)
            self.vector_store.add_document_chunks(doc_id=doc_id, filename=original_name, chunks=chunks)

            from rag_core.db.models import Document

            document = Document(
                id=doc_id,
                original_name=original_name,
                stored_name=stored.stored_name,
                file_type=ext.replace(".", ""),
                size_bytes=stored.size_bytes,
                chunk_count=len(chunks),
            )
            return self.repo.upsert(document)
        except DocumentParseError as exc:
            self.storage.delete(f"{doc_id}{ext}")
            self.vector_store.delete_document(doc_id)
            raise DocumentServiceError(f"Unable to parse file: {exc}") from exc
        except DocumentStorageError as exc:
            self.vector_store.delete_document(doc_id)
            raise DocumentServiceError(f"Storage error: {exc}") from exc
        except DocumentServiceError:
            self.storage.delete(f"{doc_id}{ext}")
            self.vector_store.delete_document(doc_id)
            raise
        except Exception as exc:
            self.storage.delete(f"{doc_id}{ext}")
            self.vector_store.delete_document(doc_id)
            raise DocumentServiceError(f"Failed to index file: {exc}") from exc

    async def replace(self, doc_id: str, upload_file: UploadFile):
        row = self.repo.get(doc_id)
        if row is None:
            raise DocumentServiceError("Document not found.")

        original_name = (upload_file.filename or "").strip()
        if not original_name:
            raise DocumentServiceError("Missing filename.")

        ext = Path(original_name).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise DocumentServiceError(f"Unsupported file type '{ext}'.")

        content = await upload_file.read()
        if len(content) == 0:
            raise DocumentServiceError("Replacement file is empty.")

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise DocumentServiceError(f"File exceeds {settings.max_upload_size_mb} MB limit.")

        old_stored_name = row.stored_name

        old_bytes: bytes | None = None
        try:
            old_bytes = self.storage.read_bytes(old_stored_name)
        except Exception:
            old_bytes = None

        new_stored_name: str | None = None
        try:
            text = parse_document_bytes(ext, content)
            chunks = chunk_text(text)
            if not chunks:
                raise DocumentServiceError("No readable text found in replacement file.")

            stored = self.storage.save_bytes(doc_id=doc_id, ext=ext, content=content)
            new_stored_name = stored.stored_name
            self.vector_store.delete_document(doc_id)
            self.vector_store.add_document_chunks(doc_id=doc_id, filename=original_name, chunks=chunks)

            if old_stored_name != stored.stored_name:
                self.storage.delete(old_stored_name)

            row.original_name = original_name
            row.stored_name = stored.stored_name
            row.file_type = ext.replace(".", "")
            row.size_bytes = stored.size_bytes
            row.chunk_count = len(chunks)
            return self.repo.upsert(row)
        except Exception as exc:
            if new_stored_name and new_stored_name != old_stored_name:
                self.storage.delete(new_stored_name)
            try:
                if old_bytes is not None:
                    old_ext = Path(old_stored_name).suffix.lower()
                    old_text = parse_document_bytes(old_ext, old_bytes)
                    old_chunks = chunk_text(old_text)
                    if old_chunks:
                        self.vector_store.delete_document(doc_id)
                        self.vector_store.add_document_chunks(
                            doc_id=doc_id,
                            filename=row.original_name,
                            chunks=old_chunks,
                        )
                    self.storage.save_bytes(doc_id=doc_id, ext=old_ext, content=old_bytes)
            except Exception:
                pass
            raise DocumentServiceError(f"Failed to replace document: {exc}") from exc

    def delete(self, doc_id: str) -> None:
        row = self.repo.get(doc_id)
        if row is None:
            raise DocumentServiceError("Document not found.")

        self.vector_store.delete_document(doc_id)
        self.storage.delete(row.stored_name)
        self.repo.delete(row)

    def total_documents(self) -> int:
        return len(self.repo.list_documents())

    def storage_stats(self) -> dict[str, int]:
        docs = self.repo.list_documents()
        total_size = sum(d.size_bytes for d in docs)
        return {
            "count": len(docs),
            "bytes": total_size,
        }
