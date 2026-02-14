from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from rag_core.db.models import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_documents(self) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get(self, doc_id: str) -> Document | None:
        return self.db.get(Document, doc_id)

    def upsert(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()

