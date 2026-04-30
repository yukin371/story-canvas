from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from ..base import ProviderError


def _normalize_base_url(value: str) -> str:
    text = value.strip().rstrip("/")
    if text.endswith("/v1"):
        return text
    return f"{text}/v1"


@dataclass(slots=True)
class OpenAITextHTTPClient:
    """Stdlib-only text client using the Responses API."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: int = 300

    @property
    def responses_url(self) -> str:
        return f"{_normalize_base_url(self.base_url)}/responses"

    def build_response_request(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            "text": {"format": {"type": "json_object"}},
        }
        if temperature is not None:
            payload["temperature"] = temperature
        return {
            "endpoint": self.responses_url,
            "transport": "json",
            "json": payload,
        }

    def generate_text(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("transport") != "json":
            raise ProviderError(f"Unsupported OpenAI text transport: {request.get('transport')}")
        body = json.dumps(request.get("json", {})).encode("utf-8")
        http_request = urllib.request.Request(
            request.get("endpoint", self.responses_url),
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "story-harness-cli/1.0",
            },
            method="POST",
        )
        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            )
            with opener.open(http_request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"OpenAI text request failed: HTTP {exc.code}: {response_body or exc.reason}") from exc
        except Exception as exc:  # pragma: no cover - requires live provider
            raise ProviderError(f"OpenAI text request failed: {exc}") from exc

        return {
            "provider": "openai-text-http",
            "responseId": response_payload.get("id", ""),
            "text": self._extract_output_text(response_payload),
            "payload": response_payload,
        }

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        chunks: list[str] = []
        for item in payload.get("output", []):
            if not isinstance(item, dict):
                continue
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if not isinstance(content, dict):
                        continue
                    text = content.get("text")
                    if isinstance(text, str) and text:
                        chunks.append(text)
            text = item.get("text")
            if isinstance(text, str) and text:
                chunks.append(text)
        if chunks:
            return "\n".join(chunks)

        choices = payload.get("choices", [])
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str):
                return content
        raise ProviderError("OpenAI text response did not contain output text")


def resolve_api_key(cli_value: str) -> str:
    if cli_value.strip():
        return cli_value.strip()
    for env_name in ("TEXT_PROVIDER_API_KEY", "OPENAI_API_KEY", "API_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return ""


def resolve_base_url(cli_value: str, configured_value: str = "") -> str:
    for candidate in (
        cli_value.strip(),
        configured_value.strip(),
        os.environ.get("TEXT_PROVIDER_BASE_URL", "").strip(),
        os.environ.get("OPENAI_BASE_URL", "").strip(),
        os.environ.get("BASE_URL", "").strip(),
        "https://api.openai.com/v1",
    ):
        if candidate:
            return _normalize_base_url(candidate)
    return "https://api.openai.com/v1"
