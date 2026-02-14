from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rag_core.config import settings
from rag_core.security import KeyCipher


@dataclass
class StoredSettings:
    provider: str
    model: str
    ollama_base_url: str
    temperature: float
    api_keys: dict[str, str]


class SettingsStore:
    def __init__(self, settings_path: Path | None = None) -> None:
        self.path = settings_path or settings.settings_file
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cipher = KeyCipher(settings.secrets_dir / "fernet.key")

    def _default_settings(self) -> StoredSettings:
        return StoredSettings(
            provider="ollama",
            model="llama3.1:8b",
            ollama_base_url=settings.ollama_base_url,
            temperature=0.2,
            api_keys={},
        )

    def load(self) -> StoredSettings:
        if not self.path.exists():
            defaults = self._default_settings()
            self.save(defaults)
            return defaults

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            defaults = self._default_settings()
            self.save(defaults)
            return defaults
        return StoredSettings(
            provider=raw.get("provider", "ollama"),
            model=raw.get("model", "llama3.1:8b"),
            ollama_base_url=raw.get("ollama_base_url", settings.ollama_base_url),
            temperature=float(raw.get("temperature", 0.2)),
            api_keys=dict(raw.get("api_keys", {})),
        )

    def save(self, data: StoredSettings) -> None:
        payload = {
            "provider": data.provider,
            "model": data.model,
            "ollama_base_url": data.ollama_base_url,
            "temperature": data.temperature,
            "api_keys": data.api_keys,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def update(
        self,
        provider: str,
        model: str,
        ollama_base_url: str,
        temperature: float,
    ) -> StoredSettings:
        current = self.load()
        updated = StoredSettings(
            provider=provider,
            model=model,
            ollama_base_url=ollama_base_url,
            temperature=temperature,
            api_keys=current.api_keys,
        )
        self.save(updated)
        return updated

    def api_key_status(self) -> dict[str, bool]:
        current = self.load()
        return {provider: True for provider in current.api_keys}

    def save_api_key(self, provider: str, plain_key: str) -> None:
        current = self.load()
        encrypted = self.cipher.encrypt(plain_key)
        current.api_keys[provider] = encrypted
        self.save(current)

    def remove_api_key(self, provider: str) -> bool:
        current = self.load()
        if provider not in current.api_keys:
            return False
        current.api_keys.pop(provider, None)
        self.save(current)
        return True

    def get_api_key(self, provider: str) -> str | None:
        current = self.load()
        encrypted = current.api_keys.get(provider)
        if not encrypted:
            return None
        return self.cipher.decrypt(encrypted)
