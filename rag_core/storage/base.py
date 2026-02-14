from __future__ import annotations

from dataclasses import dataclass


class DocumentStorageError(Exception):
    pass


@dataclass(frozen=True)
class StoredDocument:
    stored_name: str
    size_bytes: int


class DocumentStorage:
    def save_bytes(self, doc_id: str, ext: str, content: bytes) -> StoredDocument:
        raise NotImplementedError

    def delete(self, stored_name: str) -> None:
        raise NotImplementedError

    def read_bytes(self, stored_name: str) -> bytes:
        raise NotImplementedError

