from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from app.config import settings


class VectorStoreError(Exception):
    pass


class VectorStore:
    def __init__(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)

        embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

        self.store = Chroma(
            collection_name="documents",
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_dir),
            collection_metadata={"hnsw:space": "cosine"},
        )

    def add_document_chunks(self, doc_id: str, filename: str, chunks: list[str]) -> None:
        if not chunks:
            return

        docs = [
            Document(
                page_content=chunk,
                metadata={"doc_id": doc_id, "filename": filename, "chunk_index": idx},
            )
            for idx, chunk in enumerate(chunks)
        ]
        ids = [f"{doc_id}:{idx}" for idx in range(len(chunks))]

        try:
            self.store.add_documents(documents=docs, ids=ids)
        except Exception as exc:
            raise VectorStoreError(
                "Embedding/indexing failed. Ensure Ollama is running and the embedding model is available."
            ) from exc

    def delete_document(self, doc_id: str) -> None:
        try:
            raw = self.store.get(where={"doc_id": doc_id}, include=[])
            ids = raw.get("ids", []) if isinstance(raw, dict) else []
            if ids:
                self.store.delete(ids=ids)
        except Exception:
            # Keep deletion best-effort so file metadata cleanup can still proceed.
            return

    def retrieve(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        if self.is_empty():
            return []

        try:
            results = self.store.similarity_search_with_score(query=query, k=limit)
        except Exception as exc:
            raise VectorStoreError(
                "Vector search failed. Confirm embedding service and vector store are healthy."
            ) from exc

        hits: list[dict[str, Any]] = []
        for doc, distance in results:
            score = 1.0 / (1.0 + float(distance))
            metadata = doc.metadata or {}
            hits.append(
                {
                    "text": doc.page_content,
                    "filename": str(metadata.get("filename", "unknown")),
                    "doc_id": str(metadata.get("doc_id", "")),
                    "score": score,
                }
            )
        return hits

    def is_empty(self) -> bool:
        try:
            return self.store._collection.count() == 0
        except Exception:
            return True
