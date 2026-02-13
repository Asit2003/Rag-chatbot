from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore


router = APIRouter(prefix="/api/chat", tags=["chat"])
vector_store = VectorStore()


def _as_ndjson(generator):
    for chunk in generator:
        payload = {"type": "token", "data": chunk}
        yield json.dumps(payload, ensure_ascii=True) + "\n"
    yield json.dumps({"type": "done"}) + "\n"


@router.post("/stream")
def chat_stream(body: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    rag = RagService(db, vector_store)
    generator = rag.stream_answer(message=body.message, history=[m.model_dump() for m in body.history])
    return StreamingResponse(_as_ndjson(generator), media_type="application/x-ndjson")
