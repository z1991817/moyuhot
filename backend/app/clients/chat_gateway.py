from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from app.config import settings


class ChatGatewayError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ChatGatewayClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_ids: str | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = (api_key if api_key is not None else settings.chat_gateway_api_key).strip()
        self._model_ids = model_ids if model_ids is not None else settings.chat_gateway_models
        self._client = client or httpx.AsyncClient(
            base_url=(base_url or settings.chat_gateway_base_url).rstrip("/"),
            timeout=httpx.Timeout(60.0, connect=8.0, read=60.0),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def ensure_configured(self) -> None:
        if not self._api_key:
            raise ChatGatewayError("CHAT_GATEWAY_KEY_MISSING", "聊天网关密钥未配置")

    def _headers(self) -> dict[str, str]:
        self.ensure_configured()
        return {"Authorization": f"Bearer {self._api_key}"}

    def _static_models(self) -> list[dict[str, str]]:
        model_ids = [model.strip() for model in self._model_ids.split(",") if model.strip()]
        return [
            {"id": model_id, "name": model_id, "owned_by": "configured"} for model_id in model_ids
        ]

    async def fetch_models(self) -> list[dict[str, str]]:
        if static_models := self._static_models():
            return static_models

        try:
            response = await self._client.get("/models", headers=self._headers())
            response.raise_for_status()
            payload: object = response.json()
        except ChatGatewayError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ChatGatewayError("CHAT_GATEWAY_MODELS_FAILED", "模型列表获取失败") from exc

        raw_models = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(raw_models, list):
            return []

        models: list[dict[str, str]] = []
        for item in raw_models:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if not isinstance(model_id, str) or not model_id.strip():
                continue
            owned_by = item.get("owned_by")
            models.append(
                {
                    "id": model_id.strip(),
                    "name": model_id.strip(),
                    "owned_by": owned_by if isinstance(owned_by, str) else "",
                }
            )
        return models

    @asynccontextmanager
    async def stream_chat(
        self,
        payload: dict[str, object],
    ) -> AsyncIterator[httpx.Response]:
        try:
            async with self._client.stream(
                "POST",
                "/chat/completions",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
            ) as response:
                response.raise_for_status()
                yield response
        except ChatGatewayError:
            raise
        except httpx.HTTPStatusError as exc:
            raise ChatGatewayError(
                "CHAT_GATEWAY_REQUEST_FAILED",
                f"聊天网关请求失败：{exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            raise ChatGatewayError("CHAT_GATEWAY_REQUEST_FAILED", "聊天网关请求失败") from exc
