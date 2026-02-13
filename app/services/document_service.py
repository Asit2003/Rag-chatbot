from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Document
from app.services.document_parser import SUPPORTED_EXTENSIONS, DocumentParseError, parse_document
from app.services.repositories import DocumentRepository
from app.services.text_chunker import chunk_text
from app.services.vector_store import VectorStore


class DocumentServiceError(Exception):
    pass


class DocumentService:
    def __init__(self, db: Session, vector_store: VectorStore) -> None:
        self.repo = DocumentRepository(db)
        self.vector_store = vector_store
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    def list_documents(self) -> list[Document]:
        return self.repo.list_documents()

    def get_document(self, doc_id: str) -> Document | None:
        return self.repo.get(doc_id)

    async def upload(self, upload_file: UploadFile) -> Document:
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
        stored_name = f"{doc_id}{ext}"
        stored_path = settings.uploads_dir / stored_name

        stored_path.write_bytes(content)

        try:
            raw_text = parse_document(stored_path)
            chunks = chunk_text(raw_text)
            if not chunks:
                raise DocumentServiceError("No readable text found in this file.")
            self.vector_store.add_document_chunks(doc_id=doc_id, filename=original_name, chunks=chunks)

            document = Document(
                id=doc_id,
                original_name=original_name,
                stored_name=stored_name,
                file_type=ext.replace(".", ""),
                size_bytes=len(content),
                chunk_count=len(chunks),
            )
            return self.repo.upsert(document)
        except DocumentParseError as exc:
            stored_path.unlink(missing_ok=True)
            self.vector_store.delete_document(doc_id)
            raise DocumentServiceError(f"Unable to parse file: {exc}") from exc
        except DocumentServiceError:
            stored_path.unlink(missing_ok=True)
            self.vector_store.delete_document(doc_id)
            raise
        except Exception as exc:
            stored_path.unlink(missing_ok=True)
            self.vector_store.delete_document(doc_id)
            raise DocumentServiceError(f"Failed to index file: {exc}") from exc

    async def replace(self, doc_id: str, upload_file: UploadFile) -> Document:
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

        old_stored = settings.uploads_dir / row.stored_name
        new_stored_name = f"{doc_id}{ext}"
        new_path = settings.uploads_dir / new_stored_name

        old_chunks: list[str] = []
        if old_stored.exists():
            try:
                old_chunks = chunk_text(parse_document(old_stored))
            except Exception:
                old_chunks = []

        temp_backup: bytes | None = None
        if old_stored.exists():
            temp_backup = old_stored.read_bytes()

        new_path.write_bytes(content)

        try:
            text = parse_document(new_path)
            chunks = chunk_text(text)
            if not chunks:
                raise DocumentServiceError("No readable text found in replacement file.")

            self.vector_store.delete_document(doc_id)
            self.vector_store.add_document_chunks(doc_id=doc_id, filename=original_name, chunks=chunks)

            if old_stored != new_path and old_stored.exists():
                old_stored.unlink(missing_ok=True)

            row.original_name = original_name
            row.stored_name = new_stored_name
            row.file_type = ext.replace(".", "")
            row.size_bytes = len(content)
            row.chunk_count = len(chunks)
            return self.repo.upsert(row)
        except Exception as exc:
            if old_stored != new_path:
                new_path.unlink(missing_ok=True)
            if temp_backup is not None:
                old_stored.write_bytes(temp_backup)
            if old_chunks:
                self.vector_store.delete_document(doc_id)
                self.vector_store.add_document_chunks(doc_id=doc_id, filename=row.original_name, chunks=old_chunks)
            raise DocumentServiceError(f"Failed to replace document: {exc}") from exc

    def delete(self, doc_id: str) -> None:
        row = self.repo.get(doc_id)
        if row is None:
            raise DocumentServiceError("Document not found.")

        file_path = settings.uploads_dir / row.stored_name
        self.vector_store.delete_document(doc_id)
        file_path.unlink(missing_ok=True)
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
