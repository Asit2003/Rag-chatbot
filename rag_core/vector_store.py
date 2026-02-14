from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from rag_core.config import settings
from rag_core.settings_service import SettingsService


class VectorStoreError(Exception):
    pass


def _probe_embeddings(embeddings) -> bool:
    try:
        embeddings.embed_query("healthcheck")
        return True
    except Exception:
        return False


def _select_embeddings():
    ollama_embeddings = OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )
    if _probe_embeddings(ollama_embeddings):
        return ollama_embeddings

    settings_service = SettingsService()
    gemini_key = settings_service.get_api_key("gemini")
    if gemini_key:
        gemini_embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=gemini_key,
        )
        if _probe_embeddings(gemini_embeddings):
            return gemini_embeddings

    openai_key = settings_service.get_api_key("openai")
    if openai_key:
        openai_embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=openai_key,
        )
        if _probe_embeddings(openai_embeddings):
            return openai_embeddings

    raise VectorStoreError(
        "No embedding provider available. Start Ollama or configure Gemini/OpenAI API keys for embeddings."
    )


class VectorStore:
    def __init__(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._store: Chroma | None = None

    def _get_store(self) -> Chroma:
        if self._store is not None:
            return self._store

        embeddings = _select_embeddings()
        self._store = Chroma(
            collection_name="documents",
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_dir),
            collection_metadata={"hnsw:space": "cosine"},
        )
        return self._store

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
            self._get_store().add_documents(documents=docs, ids=ids)
        except Exception as exc:
            raise VectorStoreError(
                "Embedding/indexing failed. Ensure Ollama is running and the embedding model is available."
            ) from exc

    def delete_document(self, doc_id: str) -> None:
        try:
            raw = self._get_store().get(where={"doc_id": doc_id}, include=[])
            ids = raw.get("ids", []) if isinstance(raw, dict) else []
            if ids:
                self._get_store().delete(ids=ids)
        except Exception:
            return

    def retrieve(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        if self.is_empty():
            return []

        try:
            results = self._get_store().similarity_search_with_score(query=query, k=limit)
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
            return self._get_store()._collection.count() == 0
        except VectorStoreError:
            return False
        except Exception:
            return True
