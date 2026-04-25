from __future__ import annotations

from typing import Callable

from .base import OptionalDependencyUnavailableError, load_optional_attribute


SimilarityScorer = Callable[[str, str], float]


def load_style_similarity_scorer() -> tuple[SimilarityScorer | None, str]:
    """Return a RapidFuzz-backed scorer when available, else builtin fallback."""
    try:
        ratio = load_optional_attribute("rapidfuzz", "style-local", "fuzz.ratio")
    except OptionalDependencyUnavailableError:
        return None, "builtin"

    def score(left: str, right: str) -> float:
        return float(ratio(left, right))

    return score, "rapidfuzz"
