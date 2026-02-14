from __future__ import annotations

from typing import Generator

from rag_core.llm_service import LLMService, LLMServiceError
from rag_core.settings_service import SettingsService
from rag_core.vector_store import VectorStore, VectorStoreError


class RagService:
    def __init__(self, vector_store: VectorStore) -> None:
        self.settings_service = SettingsService()
        self.vector_store = vector_store
        self.llm_service = LLMService()

    def stream_answer(self, message: str, history: list[dict[str, str]]) -> Generator[str, None, None]:
        if self.vector_store.is_empty():
            fallback = (
                "I do not have any sources connected yet. "
                "Please add your documents in Data Management so I can answer using your content."
            )
            for token in fallback.split(" "):
                yield token + " "
            return

        try:
            hits = self.vector_store.retrieve(query=message, limit=6)
        except VectorStoreError:
            fallback = (
                "I could not access your knowledge sources right now. "
                "Please try again in a moment."
            )
            for token in fallback.split(" "):
                yield token + " "
            return
        if not hits:
            fallback = (
                "I could not find relevant information in your connected sources for that question. "
                "Please try a more specific query or tell me which document or section to use."
            )
            for token in fallback.split(" "):
                yield token + " "
            return

        context_blocks = []
        for index, hit in enumerate(hits, start=1):
            context_blocks.append(f"[{index}] File: {hit['filename']}\n{hit['text']}")

        context_text = "\n\n".join(context_blocks)

        # system_prompt = (
        #     "You are a precise enterprise assistant for end users. "
        #     "Answer only from the provided context. Do not add or infer facts that are not in the context. "
        #     "If the context is insufficient, say so plainly and politely, explain what is missing, "
        #     "and ask one or two focused follow-up questions. "
        #     "Never mention internal systems (vector databases, embeddings, retrieval) or file formats. "
        #     "When the user asks for information that is not in the context, "
        #     "suggest the next step in plain language, such as adding the relevant documents in Data Management. "
        #     "Keep responses concise and structured."
        # )
        system_prompt = (
    "You are a precise and helpful enterprise assistant for users.\n"

    "PRIMARY RULES:\n"
    "- If relevant context is provided, answer using only that context.\n"
    "- Do not add, assume, or invent facts that are not in the context.\n"

    "WHEN CONTEXT IS SUFFICIENT:\n"
    "- Give a clear, concise, and structured answer grounded in the context.\n"

    "WHEN CONTEXT IS PARTIAL:\n"
    "- Answer the part supported by context.\n"
    "- Ask 1–2 focused follow-up questions, if required.\n"

    "WHEN NO RELEVANT CONTEXT IS AVAILABLE:\n"
    "- Do NOT say you lack context or documents.\n"
    "- Provide general guidance based on common best practices.\n"
    "- Clearly signal uncertainty with phrases like "
    "'Typically', 'In general', or 'This may depend on your setup'.\n"
    "politely handle requests for information not in the context. \n"

    "STYLE:\n"
    "- Be concise, neutral, and helpful.\n"
    "- Prefer bullet points or short paragraphs.\n"
    "- Focus on solving the user's problem."
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
