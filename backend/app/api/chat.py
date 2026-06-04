from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.clients.chat_gateway import ChatGatewayClient, ChatGatewayError
from app.config import settings
from app.models.chat import ChatCompletionRequest, ChatModel, ChatModelsResponse

router = APIRouter(prefix="/chat", tags=["chat"])


def _error_response(exc: ChatGatewayError, status_code: int = 502) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": exc.message, "code": exc.code})


def get_chat_gateway(request: Request) -> ChatGatewayClient:
    return request.app.state.chat_gateway_client


@router.get("/models", response_model=ChatModelsResponse)
async def get_chat_models(
    gateway: Annotated[ChatGatewayClient, Depends(get_chat_gateway)],
) -> ChatModelsResponse | JSONResponse:
    try:
        raw_models = await gateway.fetch_models()
    except ChatGatewayError as exc:
        return _error_response(exc)

    models = [
        ChatModel(id=item["id"], name=item["name"], owned_by=item["owned_by"])
        for item in raw_models
    ]
    return ChatModelsResponse(data=models, default_model=settings.chat_gateway_default_model)


@router.post("/completions", response_model=None)
async def create_chat_completion(
    body: ChatCompletionRequest,
    gateway: Annotated[ChatGatewayClient, Depends(get_chat_gateway)],
) -> StreamingResponse | JSONResponse:
    try:
        gateway.ensure_configured()
    except ChatGatewayError as exc:
        return _error_response(exc)

    payload: dict[str, object] = body.model_dump(mode="json", exclude_none=True)
    payload["stream"] = True
    if settings.chat_gateway_web_search_enabled:
        payload["tools"] = [{"type": "web_search"}]

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            async with gateway.stream_chat(payload) as response:
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
        except ChatGatewayError as exc:
            yield f'data: {{"error":"{exc.message}","code":"{exc.code}"}}\n\n'.encode()
            yield b"data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
