from __future__ import annotations

import base64
import json
import mimetypes
import os
import posixpath
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..base import ProviderError


def _normalize_base_url(value: str) -> str:
    text = value.strip().rstrip("/")
    if text.endswith("/v1"):
        return text
    return f"{text}/v1"


def _guess_mime_type(path: Path) -> str:
    guessed = mimetypes.guess_type(path.name)[0]
    return guessed or "application/octet-stream"


def _path_to_data_url(path: Path) -> str:
    return f"data:{_guess_mime_type(path)};base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"


@dataclass(slots=True)
class OpenAIImageHTTPClient:
    """Stdlib-only image client using Responses API + image_generation."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: int = 300

    @property
    def responses_url(self) -> str:
        return f"{_normalize_base_url(self.base_url)}/responses"

    def build_generation_request(
        self,
        prompt: str,
        *,
        model: str,
        size: str,
        quality: str,
        response_model: str = "gpt-5.4",
    ) -> dict[str, Any]:
        return {
            "endpoint": self.responses_url,
            "transport": "json",
            "stream": True,
            "json": {
                "model": response_model,
                "input": prompt,
                "stream": True,
                "tools": [
                    {
                        "type": "image_generation",
                        "model": model,
                        "size": size,
                        "quality": quality,
                        "output_format": "png",
                    }
                ],
                "tool_choice": {"type": "image_generation"},
            },
        }

    def build_edit_request(
        self,
        prompt: str,
        *,
        model: str,
        size: str,
        quality: str,
        input_images: list[str],
        mask_path: str = "",
        response_model: str = "gpt-5.4",
    ) -> dict[str, Any]:
        if not input_images:
            raise ProviderError("OpenAI 图生图至少需要一张 input image")

        content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        for index, image_path in enumerate(input_images, start=1):
            path = Path(image_path)
            if not path.exists():
                raise ProviderError(f"OpenAI image upload file does not exist: {path}")
            content.append(
                {
                    "type": "input_text",
                    "text": f"Input image {index}: primary reference image. Preserve identity/layout unless the prompt explicitly changes it.",
                }
            )
            content.append({"type": "input_image", "image_url": _path_to_data_url(path)})

        if mask_path:
            path = Path(mask_path)
            if not path.exists():
                raise ProviderError(f"OpenAI mask file does not exist: {path}")
            content.append(
                {
                    "type": "input_text",
                    "text": "Mask image: treat the following input image as the edit mask reference. Change only the masked/indicated region and preserve everything else.",
                }
            )
            content.append({"type": "input_image", "image_url": _path_to_data_url(path)})

        return {
            "endpoint": self.responses_url,
            "transport": "json",
            "stream": True,
            "json": {
                "model": response_model,
                "input": [{"role": "user", "content": content}],
                "stream": True,
                "tools": [
                    {
                        "type": "image_generation",
                        "model": model,
                        "size": size,
                        "quality": quality,
                        "output_format": "png",
                        "action": "edit",
                    }
                ],
                "tool_choice": {"type": "image_generation"},
            },
        }

    def generate_image(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("transport") != "json":
            raise ProviderError(f"Unsupported OpenAI image transport: {request.get('transport')}")

        body = json.dumps(request.get("json", {})).encode("utf-8")
        http_request = urllib.request.Request(
            request.get("endpoint", self.responses_url),
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
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
                response_payload = self._read_sse_response(response)
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"OpenAI image request failed: HTTP {exc.code}: {response_body or exc.reason}") from exc
        except Exception as exc:  # pragma: no cover - exercised through command-side mocking later
            raise ProviderError(f"OpenAI image request failed: {exc}") from exc

        return {
            "provider": "openai-http",
            "artifacts": self._extract_artifacts(response_payload),
            "payload": response_payload,
        }

    def build_payload(
        self,
        prompt: str,
        *,
        model: str,
        size: str,
        quality: str,
        response_model: str = "gpt-5.4",
    ) -> dict[str, Any]:
        return self.build_generation_request(
            prompt,
            model=model,
            size=size,
            quality=quality,
            response_model=response_model,
        )

    def materialize_artifacts(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        artifacts = result.get("artifacts", [])
        if not artifacts:
            raise ProviderError("OpenAI image response did not contain any generated artifacts")

        materialized: list[dict[str, Any]] = []
        for artifact in artifacts:
            output_format = str(artifact.get("outputFormat") or "png").lower()
            if artifact.get("b64Json"):
                try:
                    content = base64.b64decode(artifact["b64Json"])
                except Exception as exc:
                    raise ProviderError("OpenAI image artifact b64_json decode failed") from exc
                materialized.append(
                    {
                        "content": content,
                        "extension": self._normalize_extension(output_format),
                        "source": "b64_json",
                        "revisedPrompt": artifact.get("revisedPrompt", ""),
                        "index": artifact.get("index", len(materialized)),
                    }
                )
                continue

            image_url = artifact.get("url", "")
            if image_url:
                try:
                    with urllib.request.urlopen(image_url, timeout=self.timeout_seconds) as response:
                        content = response.read()
                        content_type = response.headers.get("Content-Type", "")
                except Exception as exc:  # pragma: no cover - requires live provider URL
                    raise ProviderError(f"OpenAI image artifact download failed: {exc}") from exc
                materialized.append(
                    {
                        "content": content,
                        "extension": self._normalize_extension(
                            self._infer_extension_from_url_or_type(image_url, content_type, fallback=output_format)
                        ),
                        "source": "url",
                        "revisedPrompt": artifact.get("revisedPrompt", ""),
                        "index": artifact.get("index", len(materialized)),
                    }
                )
                continue

            raise ProviderError("OpenAI image response did not include b64_json or url")

        return materialized

    def materialize_first_artifact(self, result: dict[str, Any]) -> dict[str, Any]:
        return self.materialize_artifacts(result)[0]

    def _read_sse_response(self, response: Any) -> dict[str, Any]:
        response_id = ""
        image_items: list[dict[str, Any]] = []
        response_error: dict[str, Any] | None = None
        event_lines: list[str] = []
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if line:
                event_lines.append(line)
                continue

            event_name, data = self._parse_sse_event(event_lines)
            event_lines = []
            if not event_name:
                continue
            payload = json.loads(data) if data else {}
            if event_name == "response.created":
                response_id = payload.get("response", {}).get("id", response_id)
                continue
            if event_name == "response.output_item.done":
                item = payload.get("item", {})
                if item.get("type") == "image_generation_call" and item.get("result"):
                    image_items.append(item)
                continue
            if event_name == "response.failed":
                response_error = payload.get("response", {}).get("error") or {
                    "code": "unknown_error",
                    "message": "Responses API image_generation failed.",
                }

        if response_error is not None:
            raise ProviderError(
                f"{response_error.get('code', 'unknown_error')}: {response_error.get('message', 'Responses API image_generation failed.')}"
            )

        output_data = []
        for item in image_items:
            output_data.append(
                {
                    "type": "image_generation_call",
                    "result": item.get("result", ""),
                    "revised_prompt": item.get("revised_prompt", ""),
                    "output_format": item.get("output_format", "png"),
                }
            )

        return {
            "id": response_id,
            "output": output_data,
            "data": [
                {
                    "b64_json": item.get("result", ""),
                    "revised_prompt": item.get("revised_prompt", ""),
                    "output_format": item.get("output_format", "png"),
                }
                for item in image_items
            ],
        }

    def _parse_sse_event(self, lines: list[str]) -> tuple[str, str]:
        event_name = ""
        data_parts: list[str] = []
        for line in lines:
            if line.startswith("event:"):
                event_name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_parts.append(line[len("data:") :].strip())
        return event_name, "\n".join(data_parts)

    def _extract_artifacts(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        payload_output_format = payload.get("output_format") or "png"
        for index, item in enumerate(payload.get("data", [])):
            if not isinstance(item, dict):
                continue
            artifacts.append(
                {
                    "index": index,
                    "b64Json": item.get("b64_json", "") or item.get("result", ""),
                    "url": item.get("url", ""),
                    "revisedPrompt": item.get("revised_prompt", ""),
                    "outputFormat": item.get("output_format") or payload_output_format,
                }
            )
        return artifacts

    def _infer_extension_from_url_or_type(self, image_url: str, content_type: str, *, fallback: str) -> str:
        parsed = urlparse(image_url)
        suffix = Path(posixpath.basename(parsed.path)).suffix.lower()
        if suffix:
            return suffix.lstrip(".")

        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip() or "")
        if guessed:
            return guessed.lstrip(".")
        return fallback

    def _normalize_extension(self, value: str) -> str:
        normalized = value.lower().strip().lstrip(".")
        if normalized == "jpg":
            return "jpeg"
        if normalized in {"png", "webp", "jpeg"}:
            return normalized
        return "png"


def resolve_api_key(cli_value: str) -> str:
    if cli_value.strip():
        return cli_value.strip()
    for env_name in ("IMAGEGEN_API_KEY", "OPENAI_API_KEY", "API_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return ""


def resolve_base_url(cli_value: str, configured_value: str = "") -> str:
    for candidate in (
        cli_value.strip(),
        configured_value.strip(),
        os.environ.get("IMAGEGEN_BASE_URL", "").strip(),
        os.environ.get("OPENAI_BASE_URL", "").strip(),
        os.environ.get("BASE_URL", "").strip(),
        "https://api.openai.com/v1",
    ):
        if candidate:
            return _normalize_base_url(candidate)
    return "https://api.openai.com/v1"
