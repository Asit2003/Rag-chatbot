from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.settings import ApiKeyUpdate, SettingsOut, SettingsUpdate
from app.services.settings_service import MODEL_CATALOG, SUPPORTED_PROVIDERS, SettingsService


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)) -> SettingsOut:
    payload = SettingsService(db).get_settings_payload()
    return SettingsOut(**payload)


@router.put("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)) -> SettingsOut:
    service = SettingsService(db)
    try:
        updated = service.update_settings(
            provider=payload.provider,
            model=payload.model,
            ollama_base_url=payload.ollama_base_url,
            temperature=payload.temperature,
        )
        return SettingsOut(**updated)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api-keys/{provider}")
def save_api_key(provider: str, body: ApiKeyUpdate, db: Session = Depends(get_db)) -> dict[str, str]:
    service = SettingsService(db)
    try:
        service.save_api_key(provider=provider, plain_key=body.api_key)
        return {"message": f"API key saved for {provider}."}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api-keys/{provider}")
def remove_api_key(provider: str, db: Session = Depends(get_db)) -> dict[str, str]:
    service = SettingsService(db)
    try:
        deleted = service.remove_api_key(provider=provider)
        if not deleted:
            raise HTTPException(status_code=404, detail="API key not found.")
        return {"message": f"API key removed for {provider}."}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ollama-models")
def list_ollama_models(
    base_url: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    if not base_url:
        payload = SettingsService(db).get_settings_payload()
        base_url = payload["ollama_base_url"]
    try:
        with httpx.Client(timeout=8) as client:
            response = client.get(f"{base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            payload = response.json()
        names = [item.get("name") for item in payload.get("models", []) if item.get("name")]
        return {"models": names}
    except Exception:
        return {"models": []}


@router.get("/provider-models/{provider}")
def list_provider_models(
    provider: str,
    base_url: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    service = SettingsService(db)
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not supported.")

    if provider == "ollama":
        if not base_url:
            payload = service.get_settings_payload()
            base_url = payload["ollama_base_url"]
        try:
            with httpx.Client(timeout=8) as client:
                response = client.get(f"{base_url.rstrip('/')}/api/tags")
                response.raise_for_status()
                payload = response.json()
            names = [item.get("name") for item in payload.get("models", []) if item.get("name")]
            return {"models": names}
        except Exception:
            return {"models": MODEL_CATALOG["ollama"]}

    if provider == "groq":
        api_key = service.get_api_key("groq")
        if api_key:
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                with httpx.Client(timeout=10) as client:
                    response = client.get("https://api.groq.com/openai/v1/models", headers=headers)
                    response.raise_for_status()
                    payload = response.json()
                names = sorted({item.get("id", "") for item in payload.get("data", []) if item.get("id")})
                if names:
                    return {"models": names}
            except Exception:
                pass
        return {"models": MODEL_CATALOG["groq"]}

    return {"models": MODEL_CATALOG.get(provider, [])}
