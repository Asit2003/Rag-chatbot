from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    provider: str
    model: str
    ollama_base_url: str
    temperature: float
    available_providers: list[str]
    default_models: dict[str, str]
    model_catalog: dict[str, list[str]]
    api_key_status: dict[str, bool]


class SettingsUpdate(BaseModel):
    provider: str = Field(min_length=2, max_length=32)
    model: str = Field(min_length=1, max_length=128)
    ollama_base_url: str = Field(min_length=10, max_length=512)
    temperature: float = Field(ge=0, le=2)


class ApiKeyUpdate(BaseModel):
    api_key: str = Field(min_length=10, max_length=500)
