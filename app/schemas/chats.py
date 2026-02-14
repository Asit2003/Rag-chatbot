from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionOut(BaseModel):
    id: str
    title: str
    preview: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    preview: str = Field(default="", max_length=400)
