from __future__ import annotations

from dataclasses import dataclass

from rag_core.settings_store import SettingsStore


SUPPORTED_PROVIDERS = ["ollama", "openai", "anthropic", "gemini", "groq"]
DEFAULT_MODELS = {
    "ollama": "llama3.1:8b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
}
MODEL_CATALOG = {
    "ollama": [],
    "openai": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
    "anthropic": ["claude-3-5-haiku-latest", "claude-3-7-sonnet-latest"],
    "gemini": ["gemini-1.5-flash", "gemini-1.5-pro"],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "gemma-7b-it",
        "qwen-2.5-32b",
        "qwen-2.5-coder-32b",
        "deepseek-r1-distill-llama-70b",
        "deepseek-r1-distill-qwen-32b",
        "llama-guard-3-8b",
        "allam-2-7b",
        "compound-beta",
        "moonshotai/kimi-k2-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    ],
}


@dataclass
class EffectiveSettings:
    provider: str
    model: str
    ollama_base_url: str
    temperature: float


class SettingsService:
    def __init__(self) -> None:
        self.store = SettingsStore()

    def get_settings_payload(self) -> dict:
        data = self.store.load()
        status = {provider: False for provider in SUPPORTED_PROVIDERS if provider != "ollama"}
        status.update(self.store.api_key_status())
        return {
            "provider": data.provider,
            "model": data.model,
            "ollama_base_url": data.ollama_base_url,
            "temperature": data.temperature,
            "available_providers": SUPPORTED_PROVIDERS,
            "default_models": DEFAULT_MODELS,
            "model_catalog": MODEL_CATALOG,
            "api_key_status": status,
        }

    def update_settings(self, provider: str, model: str, ollama_base_url: str, temperature: float) -> dict:
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError("Unsupported provider.")
        if provider != "ollama" and not self.has_api_key(provider):
            raise ValueError(f"API key required for provider '{provider}'.")

        data = self.store.update(
            provider=provider,
            model=model or DEFAULT_MODELS[provider],
            ollama_base_url=ollama_base_url,
            temperature=temperature,
        )
        return self.get_settings_payload()

    def save_api_key(self, provider: str, plain_key: str) -> None:
        if provider not in SUPPORTED_PROVIDERS or provider == "ollama":
            raise ValueError("Invalid provider for API key storage.")
        self.store.save_api_key(provider=provider, plain_key=plain_key)

    def remove_api_key(self, provider: str) -> bool:
        if provider not in SUPPORTED_PROVIDERS or provider == "ollama":
            raise ValueError("Invalid provider.")
        return self.store.remove_api_key(provider)

    def has_api_key(self, provider: str) -> bool:
        return self.store.get_api_key(provider) is not None

    def get_api_key(self, provider: str) -> str | None:
        if provider == "ollama":
            return None
        return self.store.get_api_key(provider)

    def get_effective_settings(self) -> EffectiveSettings:
        data = self.store.load()
        return EffectiveSettings(
            provider=data.provider,
            model=data.model or DEFAULT_MODELS[data.provider],
            ollama_base_url=data.ollama_base_url,
            temperature=data.temperature,
        )

