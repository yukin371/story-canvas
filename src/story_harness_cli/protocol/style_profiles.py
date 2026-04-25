from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.utils.project_meta import normalize_machine_label, normalize_primary_genre


def get_default_style_profiles() -> Dict[str, Dict[str, Any]]:
    return {
        "default": {
            "patternThresholds": {},
            "extraPatterns": {},
        },
        "web-serial-zh": {
            "patternThresholds": {
                "hedgeAdverbs": 6.0,
                "formulaicTransition": 3.0,
            },
            "extraPatterns": {
                "formulaicTransition": [r"下一刻", r"下一秒", r"话音未落"],
            },
        },
        "literary-zh": {
            "patternThresholds": {
                "simileDensity": 2.5,
                "hedgeAdverbs": 4.0,
                "formulaicTransition": 1.5,
            },
            "extraPatterns": {
                "tellingEmotion": [r"灵魂深处[^。，？！\n]{1,12}", r"某种[^。，？！\n]{1,10}情绪"],
            },
        },
    }


def merge_with_defaults(custom: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    profiles = get_default_style_profiles()
    custom_profiles = custom.get("profiles", {}) if isinstance(custom, dict) else {}
    for profile_name, payload in custom_profiles.items():
        if not isinstance(payload, dict):
            continue
        merged = dict(profiles.get(profile_name, {}))
        for key, value in payload.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        profiles[profile_name] = merged
    return profiles


def load_style_profiles(root: Path) -> Dict[str, Dict[str, Any]]:
    profile_path = root / "style-profiles.yaml"
    if profile_path.exists():
        custom = load_json_compatible_yaml(profile_path, {})
        if custom:
            return merge_with_defaults(custom)
    return get_default_style_profiles()


def resolve_style_profile(root: Path, profile_name: str) -> Tuple[Dict[str, Any], str]:
    profiles = load_style_profiles(root)
    if profile_name not in profiles:
        raise SystemExit(f"style profile 不存在: {profile_name}")

    profile_path = root / "style-profiles.yaml"
    if profile_path.exists():
        custom = load_json_compatible_yaml(profile_path, {})
        custom_profiles = custom.get("profiles", {}) if isinstance(custom, dict) else {}
        if profile_name in custom_profiles:
            return profiles[profile_name], "project"
    return profiles[profile_name], "builtin"


def choose_style_profile_name(project: Dict[str, Any]) -> str:
    positioning = project.get("positioning", {})
    primary_genre = normalize_primary_genre(positioning.get("primaryGenre", ""))
    style_tags = [normalize_machine_label(item) for item in positioning.get("styleTags", []) if item]

    if "web-serial" in style_tags:
        return "web-serial-zh"
    if primary_genre == "literary":
        return "literary-zh"
    return "default"
