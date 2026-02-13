from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import KeyCipher
from app.services.repositories import SettingsRepository


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
    def __init__(self, db: Session) -> None:
        self.repo = SettingsRepository(db)
        self.cipher = KeyCipher(settings.secrets_dir / "fernet.key")

    def get_settings_payload(self) -> dict:
        row = self.repo.get_or_create()
        status = {provider: False for provider in SUPPORTED_PROVIDERS if provider != "ollama"}
        status.update(self.repo.api_key_status())
        return {
            "provider": row.provider,
            "model": row.model,
            "ollama_base_url": row.ollama_base_url,
            "temperature": row.temperature,
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

        row = self.repo.get_or_create()
        row.provider = provider
        row.model = model or DEFAULT_MODELS[provider]
        row.ollama_base_url = ollama_base_url
        row.temperature = temperature
        self.repo.save(row)
        return self.get_settings_payload()

    def save_api_key(self, provider: str, plain_key: str) -> None:
        if provider not in SUPPORTED_PROVIDERS or provider == "ollama":
            raise ValueError("Invalid provider for API key storage.")
        encrypted = self.cipher.encrypt(plain_key)
        self.repo.set_api_key(provider=provider, encrypted_key=encrypted)

    def remove_api_key(self, provider: str) -> bool:
        if provider not in SUPPORTED_PROVIDERS or provider == "ollama":
            raise ValueError("Invalid provider.")
        return self.repo.remove_api_key(provider)

    def has_api_key(self, provider: str) -> bool:
        row = self.repo.get_api_key(provider)
        return row is not None

    def get_api_key(self, provider: str) -> str | None:
        if provider == "ollama":
            return None
        row = self.repo.get_api_key(provider)
        if row is None:
            return None
        return self.cipher.decrypt(row.encrypted_key)

    def get_effective_settings(self) -> EffectiveSettings:
        row = self.repo.get_or_create()
        return EffectiveSettings(
            provider=row.provider,
            model=row.model,
            ollama_base_url=row.ollama_base_url or settings.ollama_base_url,
            temperature=row.temperature,
        )
