from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.schemas.chats import ChatSessionCreate, ChatSessionOut
from rag_core.rag_service import RagService
from rag_core.db.session import get_db
from rag_core.repositories import ChatRepository
from rag_core.vector_store import VectorStore


router = APIRouter(prefix="/api/chat", tags=["chat"])
vector_store = VectorStore()


def _as_ndjson(generator):
    for chunk in generator:
        payload = {"type": "token", "data": chunk}
        yield json.dumps(payload, ensure_ascii=True) + "\n"
    yield json.dumps({"type": "done"}) + "\n"


@router.post("/stream")
def chat_stream(body: ChatRequest) -> StreamingResponse:
    rag = RagService(vector_store)
    generator = rag.stream_answer(message=body.message, history=[m.model_dump() for m in body.history])
    return StreamingResponse(_as_ndjson(generator), media_type="application/x-ndjson")


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_chat_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ChatSessionOut]:
    repo = ChatRepository(db)
    rows = repo.list_chats(limit=limit, offset=offset)
    return [ChatSessionOut.model_validate(row) for row in rows]


@router.post("/sessions", response_model=ChatSessionOut)
def create_chat_session(body: ChatSessionCreate, db: Session = Depends(get_db)) -> ChatSessionOut:
    repo = ChatRepository(db)
    row = repo.create_chat(title=body.title, preview=body.preview)
    return ChatSessionOut.model_validate(row)
