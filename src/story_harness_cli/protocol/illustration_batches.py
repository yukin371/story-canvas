from __future__ import annotations

import re
from pathlib import Path


def illustration_batch_manifest_dir(root: Path) -> Path:
    return root / "logs" / "illustration-batches"


def default_illustration_batch_manifest_path(root: Path, label: str) -> Path:
    slug = _slugify(label) or "illustration-batch"
    return illustration_batch_manifest_dir(root) / f"{slug}.json"


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip()).strip("-_")
    return normalized.lower()
