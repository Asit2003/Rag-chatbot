from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/chat")


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("chat.html", {"request": request, "active": "chat"})


@router.get("/data-management", response_class=HTMLResponse)
def data_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("data_management.html", {"request": request, "active": "data"})


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("settings.html", {"request": request, "active": "settings"})
