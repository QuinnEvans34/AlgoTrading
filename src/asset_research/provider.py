"""Provider boundary and OpenAI Responses implementation for asset research."""

from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from .errors import AssetResearchProviderError, AssetResearchUnavailableError


class AssetResearchProvider(Protocol):
    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]: ...


def _extract_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                text = content_item.get("text")
                if isinstance(text, str) and text.strip():
                    return text
    raise AssetResearchProviderError("OpenAI Responses API returned no structured text output.")


class OpenAIResponsesAssetResearchProvider:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str | None,
        timeout_seconds: int,
        base_url: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self._client = client

    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._api_key or not self._model:
            raise AssetResearchUnavailableError(
                "Grounded AI research is not configured. Set OPENAI_API_KEY and OPENAI_MODEL."
            )
        own_client = self._client is None
        client = self._client or httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        )
        try:
            response = client.post(
                "/responses",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "store": False,
                    "instructions": instructions,
                    "input": input_text,
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": schema_name,
                            "strict": True,
                            "schema": schema,
                        }
                    },
                },
            )
        except httpx.HTTPError as exc:
            raise AssetResearchProviderError(f"OpenAI request failed: {exc}") from exc
        finally:
            if own_client:
                client.close()
        if response.status_code >= 400:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = None
            message = "OpenAI request failed."
            if isinstance(error_payload, dict):
                inner = error_payload.get("error")
                if isinstance(inner, dict) and isinstance(inner.get("message"), str):
                    message = inner["message"]
            raise AssetResearchProviderError(message)
        try:
            payload = response.json()
        except ValueError as exc:
            raise AssetResearchProviderError(
                "OpenAI Responses API returned invalid JSON."
            ) from exc
        try:
            return json.loads(_extract_output_text(payload))
        except json.JSONDecodeError as exc:
            raise AssetResearchProviderError(
                "OpenAI Responses API returned invalid structured output."
            ) from exc
