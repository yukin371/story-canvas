from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Sequence

from .base import EmbeddingProviderClient, OptionalDependencyUnavailableError, ProviderError, load_optional_attribute

_DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_DEFAULT_DIMENSION = 384
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")


def resolve_model_name(cli_value: str = "", configured_value: str = "") -> str:
    """Resolve the embedding model name from explicit and environment sources."""

    for candidate in (
        cli_value.strip(),
        configured_value.strip(),
        os.environ.get("EMBEDDING_PROVIDER_MODEL", "").strip(),
        os.environ.get("EMBEDDING_MODEL", "").strip(),
        _DEFAULT_MODEL,
    ):
        if candidate:
            return candidate
    return _DEFAULT_MODEL


def load_embedding_provider(model_name: str | None = None) -> EmbeddingProviderClient:
    """Load a sentence-transformers provider when available, else use a builtin fallback."""

    resolved_model_name = resolve_model_name(model_name or "")
    try:
        sentence_transformer_cls = load_optional_attribute(
            "sentence_transformers",
            "embedding-local",
            "SentenceTransformer",
        )
        return SentenceTransformerEmbeddingClient(sentence_transformer_cls(resolved_model_name), resolved_model_name)
    except OptionalDependencyUnavailableError:
        return BuiltinEmbeddingClient()
    except Exception:
        return BuiltinEmbeddingClient()


@dataclass(slots=True)
class SentenceTransformerEmbeddingClient:
    """Sentence-transformers backed embedding client."""

    model: Any
    model_name: str
    provider_name: str = "sentence-transformers"
    dimension: int = field(init=False)

    def __post_init__(self) -> None:
        self.dimension = int(getattr(self.model, "get_sentence_embedding_dimension", lambda: 0)() or 0)
        if self.dimension <= 0:
            self.dimension = _DEFAULT_DIMENSION

    def embed_texts(self, texts: list[str]) -> dict[str, Any]:
        if not texts:
            return {
                "provider": self.provider_name,
                "model": self.model_name,
                "dimension": self.dimension,
                "embeddings": [],
            }
        try:
            vectors = self.model.encode(
                [text or "" for text in texts],
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as exc:  # pragma: no cover - depends on optional dependency runtime
            raise ProviderError(f"Embedding request failed: {exc}") from exc

        embeddings = _normalize_embedding_batch(vectors)
        if embeddings and not self.dimension:
            self.dimension = len(embeddings[0])
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "dimension": self.dimension,
            "embeddings": embeddings,
        }


@dataclass(slots=True)
class BuiltinEmbeddingClient:
    """Stdlib-only fallback embedding client based on hashed token features."""

    provider_name: str = "builtin-hash"
    model_name: str = "builtin-hash-384"
    dimension: int = _DEFAULT_DIMENSION

    def embed_texts(self, texts: list[str]) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "dimension": self.dimension,
            "embeddings": [_normalize_vector(_hash_text_vector(text or "", self.dimension)) for text in texts],
        }


def _normalize_embedding_batch(vectors: Any) -> list[list[float]]:
    if vectors is None:
        return []
    if hasattr(vectors, "tolist"):
        vectors = vectors.tolist()
    if not isinstance(vectors, Sequence):
        return []
    normalized: list[list[float]] = []
    for vector in vectors:
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        if not isinstance(vector, Sequence):
            continue
        normalized.append(_normalize_vector([float(value) for value in vector]))
    return normalized


def _hash_text_vector(text: str, dimension: int) -> list[float]:
    values = [0.0] * dimension
    tokens = _TOKEN_PATTERN.findall(text.lower().strip())
    if not tokens:
        tokens = [text.strip()] if text.strip() else []
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:8], "big") % dimension
        sign = 1.0 if digest[8] % 2 == 0 else -1.0
        weight = 1.0 + min(len(token), 12) / 12.0
        values[bucket] += sign * weight
        if len(token) > 1:
            for offset in range(len(token) - 1):
                gram = token[offset : offset + 2]
                digest = hashlib.sha256(gram.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:8], "big") % dimension
                sign = 1.0 if digest[8] % 2 == 0 else -1.0
                values[bucket] += sign * 0.5
    return values


def _normalize_vector(values: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0:
        return [0.0 for _ in values]
    return [float(value) / norm for value in values]
