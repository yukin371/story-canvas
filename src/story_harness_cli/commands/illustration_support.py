from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_output_path(output_path: Path, extension: str) -> Path:
    normalized_extension = f".{extension.lstrip('.')}"
    if output_path.suffix.lower() == normalized_extension.lower():
        return output_path
    return output_path.with_suffix(normalized_extension)


def resolve_output_path_for_index(output_path: Path, index: int, extension: str) -> Path:
    base_path = resolve_output_path(output_path, extension)
    if index == 0:
        return base_path
    return base_path.with_name(f"{base_path.stem}_{index + 1:02d}{base_path.suffix}")


def asset_records_from_entry(root: Path, entry: dict[str, Any]) -> list[dict[str, Any]]:
    records = entry.get("artifacts", [])
    if records:
        normalized = []
        for record in records:
            path = Path(record.get("filePath", ""))
            exists = path.exists() if path else False
            normalized.append(
                {
                    "index": record.get("index", len(normalized)),
                    "filePath": str(path) if path else "",
                    "exists": exists,
                    "bytes": record.get("bytes", 0),
                    "source": record.get("source", ""),
                    "extension": record.get("extension", ""),
                    "isPrimary": bool(record.get("isPrimary", False)),
                }
            )
        return normalized

    file_path = entry.get("filePath", "")
    if not file_path:
        return []
    path = Path(file_path)
    return [
        {
            "index": 0,
            "filePath": str(path),
            "exists": path.exists(),
            "bytes": entry.get("metadata", {}).get("asset", {}).get("bytes", 0),
            "source": entry.get("metadata", {}).get("asset", {}).get("source", ""),
            "extension": entry.get("metadata", {}).get("asset", {}).get("extension", ""),
            "isPrimary": True,
        }
    ]


def decorate_generated_entry(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    decorated = dict(entry)
    assets = asset_records_from_entry(root, entry)
    decorated["artifacts"] = assets
    decorated["assetCount"] = len(assets)
    decorated["existingAssetCount"] = sum(1 for asset in assets if asset["exists"])
    decorated["allAssetsPresent"] = bool(assets) and decorated["assetCount"] == decorated["existingAssetCount"]
    return decorated
