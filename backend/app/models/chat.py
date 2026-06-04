from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import APIModel


class ChatModel(APIModel):
    id: str
    name: str
    owned_by: str = ""


class ChatModelsResponse(APIModel):
    data: list[ChatModel]
    default_model: str


class ChatCompletionMessage(APIModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(APIModel):
    model: str
    messages: list[ChatCompletionMessage]
    stream: bool = True
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
