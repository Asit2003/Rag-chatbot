from __future__ import annotations

from typing import Generator

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.services.settings_service import EffectiveSettings


class LLMServiceError(Exception):
    pass


def _to_langchain_messages(messages: list[dict[str, str]]) -> list[BaseMessage]:
    converted: list[BaseMessage] = []
    for item in messages:
        role = item.get("role", "")
        content = item.get("content", "")
        if not content:
            continue
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted


def _chunk_text(chunk: object) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return ""


class LLMService:
    def _build_model(self, settings: EffectiveSettings, api_key: str | None):
        provider = settings.provider
        common = {"model": settings.model, "temperature": settings.temperature}

        if provider == "ollama":
            return ChatOllama(**common, base_url=settings.ollama_base_url)

        if not api_key:
            raise LLMServiceError(f"API key missing for provider '{provider}'.")

        if provider == "openai":
            return ChatOpenAI(**common, api_key=api_key)
        if provider == "anthropic":
            return ChatAnthropic(**common, anthropic_api_key=api_key)
        if provider == "gemini":
            return ChatGoogleGenerativeAI(**common, google_api_key=api_key)
        if provider == "groq":
            return ChatGroq(**common, groq_api_key=api_key)

        raise LLMServiceError(f"Unsupported provider '{provider}'.")

    def stream_completion(
        self,
        settings: EffectiveSettings,
        api_key: str | None,
        messages: list[dict[str, str]],
    ) -> Generator[str, None, None]:
        lc_messages = _to_langchain_messages(messages)
        model = self._build_model(settings=settings, api_key=api_key)

        try:
            for chunk in model.stream(lc_messages):
                text = _chunk_text(chunk)
                if text:
                    yield text
        except httpx.ConnectError as exc:
            raise LLMServiceError(
                "Could not connect to Ollama server. Make sure Ollama is running and reachable."
            ) from exc
        except Exception as exc:
            raise LLMServiceError(str(exc)) from exc
