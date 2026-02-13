from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from app.services.llm_service import LLMService, LLMServiceError
from app.services.settings_service import SettingsService
from app.services.vector_store import VectorStore, VectorStoreError


class RagService:
    def __init__(self, db: Session, vector_store: VectorStore) -> None:
        self.settings_service = SettingsService(db)
        self.vector_store = vector_store
        self.llm_service = LLMService()

    def stream_answer(self, message: str, history: list[dict[str, str]]) -> Generator[str, None, None]:
        if self.vector_store.is_empty():
            fallback = (
                "I do not have any indexed documents yet. "
                "Please upload PDF, DOCX, or TXT files in Data Management so I can answer using your data."
            )
            for token in fallback.split(" "):
                yield token + " "
            return

        try:
            hits = self.vector_store.retrieve(query=message, limit=6)
        except VectorStoreError:
            fallback = (
                "I could not access the retrieval service right now. "
                "Please verify Ollama is running for embeddings and try again."
            )
            for token in fallback.split(" "):
                yield token + " "
            return
        if not hits:
            fallback = (
                "I could not find relevant context in your indexed files for that question. "
                "Please try a more specific query or upload additional documents."
            )
            for token in fallback.split(" "):
                yield token + " "
            return

        context_blocks = []
        for index, hit in enumerate(hits, start=1):
            context_blocks.append(f"[{index}] File: {hit['filename']}\n{hit['text']}")

        context_text = "\n\n".join(context_blocks)

        system_prompt = (
            "You are a precise enterprise assistant. "
            "Answer only from the provided context. "
            "If context is insufficient, say what is missing and ask a focused follow-up."
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "system",
                "content": f"Use this retrieved context:\n\n{context_text}",
            },
        ]

        for item in history[-10:]:
            role = item.get("role")
            content = item.get("content", "")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        active_settings = self.settings_service.get_effective_settings()
        api_key = self.settings_service.get_api_key(active_settings.provider)

        if active_settings.provider != "ollama" and not api_key:
            hint = f"API key for provider '{active_settings.provider}' is missing. Add it in Settings."
            for token in hint.split(" "):
                yield token + " "
            return

        try:
            for chunk in self.llm_service.stream_completion(
                settings=active_settings,
                api_key=api_key,
                messages=messages,
            ):
                yield chunk
        except LLMServiceError as exc:
            err = f"Model request failed: {exc}"
            for token in err.split(" "):
                yield token + " "
