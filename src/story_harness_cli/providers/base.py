from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Protocol


class ProviderError(RuntimeError):
    """Base error for provider failures."""


@dataclass(slots=True)
class OptionalDependencyUnavailableError(ProviderError):
    """Raised when an optional dependency cannot be imported."""

    module_name: str
    extra_name: str

    def __str__(self) -> str:
        return (
            f"Optional dependency '{self.module_name}' is unavailable. "
            f"Install extra '{self.extra_name}' to enable this capability."
        )


class ImageProviderClient(Protocol):
    """Protocol for image generation clients."""

    def generate_image(self, request: dict[str, Any]) -> dict[str, Any]:
        ...


class TextProviderClient(Protocol):
    """Protocol for text generation clients."""

    def generate_text(self, request: dict[str, Any]) -> dict[str, Any]:
        ...


def load_optional_attribute(module_name: str, extra_name: str, attribute_path: str) -> Any:
    """Load an attribute from an optional dependency."""
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise OptionalDependencyUnavailableError(module_name, extra_name) from exc

    value: Any = module
    for part in attribute_path.split("."):
        value = getattr(value, part)
    return value
