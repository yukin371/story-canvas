from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from story_harness_cli.protocol.io import load_json_compatible_yaml


def get_default_review_rule_profiles() -> Dict[str, Dict[str, Any]]:
    return {
        "default": {
            "enabledRules": [],
            "exemptions": [],
        }
    }


def get_default_review_rules_config() -> Dict[str, Any]:
    return {
        "activeProfile": "default",
        "profiles": get_default_review_rule_profiles(),
    }


def merge_review_rules_with_defaults(custom: Dict[str, Any]) -> Dict[str, Any]:
    config = get_default_review_rules_config()
    if not isinstance(custom, dict):
        return config

    active_profile = custom.get("activeProfile")
    if isinstance(active_profile, str) and active_profile.strip():
        config["activeProfile"] = active_profile.strip()

    custom_profiles = custom.get("profiles", {})
    if not isinstance(custom_profiles, dict):
        return config

    for profile_name, payload in custom_profiles.items():
        name = str(profile_name).strip()
        if not name or not isinstance(payload, dict):
            continue
        merged = dict(config["profiles"].get(name, {}))
        merged["enabledRules"] = _normalize_string_list(
            payload.get("enabledRules", merged.get("enabledRules", []))
        )
        merged["exemptions"] = _normalize_exemptions(
            payload.get("exemptions", merged.get("exemptions", []))
        )
        config["profiles"][name] = merged
    return config


def load_review_rules(root: Path) -> Dict[str, Any]:
    config_path = root / "review-rules.yaml"
    if not config_path.exists():
        return get_default_review_rules_config()
    raw_payload = load_json_compatible_yaml(config_path, {})
    return merge_review_rules_with_defaults(raw_payload)


def resolve_review_rule_profile_name(config: Dict[str, Any]) -> Tuple[str, str]:
    profiles = config.get("profiles", {}) if isinstance(config, dict) else {}
    requested = str(config.get("activeProfile", "default")).strip() or "default"
    if isinstance(profiles, dict) and requested in profiles:
        return requested, requested
    return requested, "default"


def resolve_review_rule_profile(root: Path, profile_name: str = "") -> Tuple[Dict[str, Any], str, str]:
    config_path = root / "review-rules.yaml"
    raw_payload: Dict[str, Any] = {}
    if config_path.exists():
        raw_payload = load_json_compatible_yaml(config_path, {})
    config = merge_review_rules_with_defaults(raw_payload)
    requested, resolved = resolve_review_rule_profile_name(
        {
            "activeProfile": profile_name or config.get("activeProfile", "default"),
            "profiles": config.get("profiles", {}),
        }
    )
    profiles = config.get("profiles", {})
    profile = profiles.get(resolved, get_default_review_rule_profiles()["default"])
    custom_profiles = raw_payload.get("profiles", {}) if isinstance(raw_payload, dict) else {}
    source = "project" if isinstance(custom_profiles, dict) and resolved in custom_profiles else "builtin"
    return profile, resolved, source


def _normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_scope(scope: Any) -> Dict[str, list[str]]:
    if not isinstance(scope, dict):
        return {"chapterIds": [], "volumeIds": [], "scenePlanIds": []}
    return {
        "chapterIds": _normalize_string_list(scope.get("chapterIds", [])),
        "volumeIds": _normalize_string_list(scope.get("volumeIds", [])),
        "scenePlanIds": _normalize_string_list(scope.get("scenePlanIds", [])),
    }


def _normalize_allow_when(allow_when: Any) -> Dict[str, Any]:
    if not isinstance(allow_when, dict):
        return {"quotedOnly": False, "matchPatterns": []}
    return {
        "quotedOnly": bool(allow_when.get("quotedOnly", False)),
        "matchPatterns": _normalize_string_list(allow_when.get("matchPatterns", [])),
    }


def _normalize_exemptions(exemptions: Any) -> list[Dict[str, Any]]:
    if not isinstance(exemptions, list):
        return []
    normalized: list[Dict[str, Any]] = []
    for item in exemptions:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("ruleId", "")).strip()
        if not rule_id:
            continue
        normalized.append(
            {
                "ruleId": rule_id,
                "scope": _normalize_scope(item.get("scope", {})),
                "allowWhen": _normalize_allow_when(item.get("allowWhen", {})),
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return normalized
