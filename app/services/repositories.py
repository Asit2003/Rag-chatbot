from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApiKey, AppSetting, Document


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


class SettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self) -> AppSetting:
        row = self.db.get(AppSetting, 1)
        if row is None:
            row = AppSetting(id=1)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row

    def save(self, row: AppSetting) -> AppSetting:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def set_api_key(self, provider: str, encrypted_key: str) -> None:
        row = self.db.get(ApiKey, provider)
        if row is None:
            row = ApiKey(provider=provider, encrypted_key=encrypted_key)
        else:
            row.encrypted_key = encrypted_key
        self.db.add(row)
        self.db.commit()

    def remove_api_key(self, provider: str) -> bool:
        row = self.db.get(ApiKey, provider)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def get_api_key(self, provider: str) -> ApiKey | None:
        return self.db.get(ApiKey, provider)

    def api_key_status(self) -> dict[str, bool]:
        rows = self.db.scalars(select(ApiKey)).all()
        return {row.provider: True for row in rows}
