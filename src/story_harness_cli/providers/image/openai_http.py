from __future__ import annotations

import base64
import json
import mimetypes
import posixpath
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from ..base import ProviderError


@dataclass(slots=True)
class OpenAIImageHTTPClient:
    """Minimal stdlib-only OpenAI image client."""

    api_key: str
    generations_url: str = "https://api.openai.com/v1/images/generations"
    edits_url: str = "https://api.openai.com/v1/images/edits"
    timeout_seconds: int = 60

    def build_generation_request(
        self,
        prompt: str,
        *,
        model: str,
        size: str,
        quality: str,
    ) -> dict[str, Any]:
        return {
            "endpoint": self.generations_url,
            "transport": "json",
            "json": {
                "model": model,
                "prompt": prompt,
                "size": size,
                "quality": quality,
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
    ) -> dict[str, Any]:
        if not input_images:
            raise ProviderError("OpenAI 图生图至少需要一张 input image")

        files = [{"field": "image[]", "path": path} for path in input_images]
        if mask_path:
            files.append({"field": "mask", "path": mask_path})
        return {
            "endpoint": self.edits_url,
            "transport": "multipart",
            "fields": {
                "model": model,
                "prompt": prompt,
                "size": size,
                "quality": quality,
            },
            "files": files,
        }

    def generate_image(self, request: dict[str, Any]) -> dict[str, Any]:
        transport = request.get("transport")
        if transport == "json":
            body = json.dumps(request.get("json", {})).encode("utf-8")
            content_type = "application/json"
        elif transport == "multipart":
            body, content_type = self._build_multipart_body(
                request.get("fields", {}),
                request.get("files", []),
            )
        else:
            raise ProviderError(f"Unsupported OpenAI image transport: {transport}")

        http_request = urllib.request.Request(
            request.get("endpoint", self.generations_url),
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": content_type,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - exercised through command-side mocking later
            raise ProviderError(f"OpenAI image request failed: {exc}") from exc

        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI image response was not valid JSON") from exc

        return {
            "provider": "openai-http",
            "artifacts": self._extract_artifacts(payload),
            "payload": payload,
        }

    def build_payload(
        self,
        prompt: str,
        *,
        model: str,
        size: str,
        quality: str,
    ) -> dict[str, Any]:
        return self.build_generation_request(
            prompt,
            model=model,
            size=size,
            quality=quality,
        )

    def _build_multipart_body(
        self,
        fields: dict[str, Any],
        files: list[dict[str, str]],
    ) -> tuple[bytes, str]:
        boundary = f"----story-harness-{uuid4().hex}"
        body = bytearray()

        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

        for item in files:
            file_path = Path(item["path"])
            if not file_path.exists():
                raise ProviderError(f"OpenAI image upload file does not exist: {file_path}")
            mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(
                (
                    f'Content-Disposition: form-data; name="{item["field"]}"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode("utf-8")
            )
            body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
            body.extend(file_path.read_bytes())
            body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        return bytes(body), f"multipart/form-data; boundary={boundary}"

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

    def _extract_artifacts(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        payload_output_format = payload.get("output_format") or "png"
        for index, item in enumerate(payload.get("data", [])):
            if not isinstance(item, dict):
                continue
            artifacts.append(
                {
                    "index": index,
                    "b64Json": item.get("b64_json", ""),
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
