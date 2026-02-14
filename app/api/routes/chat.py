from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from rag_core.rag_service import RagService
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
