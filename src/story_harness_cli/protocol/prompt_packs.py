from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Dict, List

from .io import dump_json_compatible_yaml, load_json_compatible_yaml

PACK_ALIAS_TO_ID = {
    "default": "story-canvas/default",
    "light-novel": "story-canvas/light-novel",
    "web-serial": "story-canvas/web-serial",
}

BUILTIN_PROMPT_PACKS: List[Dict[str, Any]] = [
    {
        "id": "story-canvas/default",
        "version": "1.0",
        "label": "Default Narrative Pack",
        "description": "基础叙事型模板包，适合角色设定图和章节场景图。",
        "supports": {
            "modes": ["text-to-image", "image-to-image", "inpaint"],
            "commercial": True,
        },
        "templates": [
            {
                "id": "character-standard",
                "label": "角色设定图",
                "useCase": "character",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: polished narrative illustration, readable silhouette\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "character-repaint",
                "label": "角色图重绘",
                "useCase": "character",
                "complexity": "standard",
                "mode": "image-to-image",
                "promptTemplate": "{subject}\nkeep character identity and costume continuity\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "scene-standard",
                "label": "章节场景图",
                "useCase": "chapter-scene",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: cinematic scene illustration, strong focal action, readable environment\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "scene-repaint",
                "label": "章节图重绘",
                "useCase": "chapter-scene",
                "complexity": "standard",
                "mode": "image-to-image",
                "promptTemplate": "{subject}\npreserve scene continuity and existing visual anchors\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "promo-standard",
                "label": "宣传图",
                "useCase": "promo",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: market-facing poster illustration, strong composition, clean typography-safe space\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
        ],
        "modifierGroups": [
            {
                "id": "style-cinematic",
                "group": "style",
                "label": "电影感",
                "promptFragment": "cinematic framing, layered depth, dramatic atmosphere",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "lighting-night",
                "group": "lighting",
                "label": "夜景",
                "promptFragment": "night lighting, wet reflections, practical light sources",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "composition-portrait",
                "group": "composition",
                "label": "角色近景",
                "promptFragment": "portrait-focused composition, clear face read, chest-up framing",
                "negativeFragment": "",
                "commercialTags": [],
            },
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": "default-safe",
                    "label": "默认负向",
                    "negativePrompt": "low quality, blurry, distorted hands, duplicate limbs, unreadable face",
                }
            ],
            "commercialPolicies": [
                {
                    "id": "personal-default",
                    "label": "个人默认",
                    "mode": "personal",
                    "extraPrompt": "",
                    "restrictions": [],
                },
                {
                    "id": "commercial-default",
                    "label": "商用默认",
                    "mode": "commercial",
                    "extraPrompt": "clean deliverable, commercially usable presentation, avoid trademarked elements",
                    "restrictions": ["no-logo-imitation"],
                },
            ],
        },
    },
    {
        "id": "story-canvas/light-novel",
        "version": "1.0",
        "label": "Light Novel Pack",
        "description": "偏轻小说与角色驱动场景的模板包。",
        "supports": {
            "modes": ["text-to-image", "image-to-image"],
            "commercial": True,
        },
        "templates": [
            {
                "id": "character-standard",
                "label": "轻小说角色图",
                "useCase": "character",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: anime character illustration, expressive pose, clean line art\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "scene-standard",
                "label": "轻小说场景图",
                "useCase": "chapter-scene",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: anime key visual, bright focal characters, readable emotional beat\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
        ],
        "modifierGroups": [
            {
                "id": "style-anime",
                "group": "style",
                "label": "动漫",
                "promptFragment": "anime illustration, clean line art, expressive face",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "lighting-soft",
                "group": "lighting",
                "label": "柔光",
                "promptFragment": "soft lighting, gentle highlights, readable skin tones",
                "negativeFragment": "",
                "commercialTags": [],
            },
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": "default-safe",
                    "label": "默认负向",
                    "negativePrompt": "blurry, extra fingers, warped anatomy, muddy colors",
                }
            ],
            "commercialPolicies": [
                {
                    "id": "personal-default",
                    "label": "个人默认",
                    "mode": "personal",
                    "extraPrompt": "",
                    "restrictions": [],
                }
            ],
        },
    },
    {
        "id": "story-canvas/web-serial",
        "version": "1.0",
        "label": "Web Serial Pack",
        "description": "偏商业连载、强钩子、强戏剧场面的模板包。",
        "supports": {
            "modes": ["text-to-image", "image-to-image", "inpaint"],
            "commercial": True,
        },
        "templates": [
            {
                "id": "scene-standard",
                "label": "连载高潮场景",
                "useCase": "chapter-scene",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: commercial web-serial key art, strong hook moment, high-contrast atmosphere\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "promo-standard",
                "label": "连载宣传图",
                "useCase": "promo",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\nvisual direction: striking serial promo illustration, strong branding space, immediate hook read\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
        ],
        "modifierGroups": [
            {
                "id": "lighting-neon-night",
                "group": "lighting",
                "label": "霓虹夜景",
                "promptFragment": "neon accents, rain reflections, high-contrast night lighting",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "camera-action",
                "group": "camera",
                "label": "动作镜头",
                "promptFragment": "dynamic angle, motion energy, foreground-background separation",
                "negativeFragment": "",
                "commercialTags": [],
            },
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": "default-safe",
                    "label": "默认负向",
                    "negativePrompt": "flat composition, low detail, blurry motion, broken anatomy",
                }
            ],
            "commercialPolicies": [
                {
                    "id": "commercial-default",
                    "label": "商用默认",
                    "mode": "commercial",
                    "extraPrompt": "clean deliverable, commercially safe presentation, avoid trademarked motifs",
                    "restrictions": ["no-logo-imitation"],
                }
            ],
        },
    },
]


def prompt_pack_name_from_ref(pack_ref: Dict[str, Any]) -> str:
    pack_id = str(pack_ref.get("packId") or "").strip()
    if not pack_id:
        return ""
    return pack_id.rsplit("/", 1)[-1]


def default_pack_ref_from_name(name: str, version: str | None = None) -> Dict[str, Any]:
    normalized_name = str(name or "").strip() or "default"
    pack_id = PACK_ALIAS_TO_ID.get(normalized_name, normalized_name)
    return {
        "source": "builtin",
        "packId": pack_id,
        "version": version or _builtin_pack_version(pack_id) or "builtin",
    }


def load_available_prompt_packs(root: Path) -> List[Dict[str, Any]]:
    packs_by_id: dict[str, Dict[str, Any]] = {}
    for pack in BUILTIN_PROMPT_PACKS:
        normalized = _normalize_prompt_pack(pack, source="builtin")
        pack_id = str(normalized.get("id") or "").strip()
        if pack_id:
            packs_by_id[pack_id] = normalized
    for pack in _load_project_prompt_packs(root):
        pack_id = str(pack.get("id") or "").strip()
        if not pack_id:
            continue
        packs_by_id[pack_id] = pack
    return sorted(packs_by_id.values(), key=lambda item: str(item.get("label") or item.get("id") or ""))


def summarize_prompt_pack(pack: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": pack.get("id", ""),
        "name": prompt_pack_name_from_ref({"packId": pack.get("id", "")}),
        "version": pack.get("version", ""),
        "label": pack.get("label", ""),
        "description": pack.get("description", ""),
        "source": pack.get("source", ""),
        "sourceFile": pack.get("sourceFile", ""),
        "supports": pack.get("supports", {}),
        "templates": [
            {
                "id": template.get("id", ""),
                "label": template.get("label", ""),
                "useCase": template.get("useCase", ""),
                "mode": template.get("mode", ""),
                "complexity": template.get("complexity", ""),
                "defaultNegativePolicyRef": template.get("defaultNegativePolicyRef", ""),
                "defaultCommercialPolicyRef": template.get("defaultCommercialPolicyRef", ""),
            }
            for template in pack.get("templates", [])
            if isinstance(template, dict)
        ],
        "modifierGroups": [
            {
                "id": item.get("id", ""),
                "group": item.get("group", ""),
                "label": item.get("label", ""),
                "negativeFragment": item.get("negativeFragment", ""),
            }
            for item in pack.get("modifierGroups", [])
            if isinstance(item, dict)
        ],
        "negativePolicies": [
            {
                "id": item.get("id", ""),
                "label": item.get("label", ""),
                "negativePrompt": item.get("negativePrompt", ""),
            }
            for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("negativePolicies", []))
            if isinstance(item, dict)
        ],
        "commercialPolicies": [
            {
                "id": item.get("id", ""),
                "label": item.get("label", ""),
                "mode": item.get("mode", ""),
                "restrictions": item.get("restrictions", []),
            }
            for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("commercialPolicies", []))
            if isinstance(item, dict)
        ],
    }


def serialize_prompt_pack_document(pack: Dict[str, Any], *, include_runtime_meta: bool = True) -> Dict[str, Any]:
    document = {
        "id": pack.get("id", ""),
        "version": pack.get("version", ""),
        "label": pack.get("label", ""),
        "description": pack.get("description", ""),
        "supports": deepcopy(pack.get("supports", {})),
        "templates": [
            {
                "id": template.get("id", ""),
                "label": template.get("label", ""),
                "useCase": template.get("useCase", ""),
                "mode": template.get("mode", ""),
                "complexity": template.get("complexity", ""),
                "promptTemplate": template.get("promptTemplate", ""),
                "defaultNegativePolicyRef": template.get("defaultNegativePolicyRef", ""),
                "defaultCommercialPolicyRef": template.get("defaultCommercialPolicyRef", ""),
            }
            for template in pack.get("templates", [])
            if isinstance(template, dict)
        ],
        "modifierGroups": [
            {
                "id": item.get("id", ""),
                "group": item.get("group", ""),
                "label": item.get("label", ""),
                "promptFragment": item.get("promptFragment", ""),
                "negativeFragment": item.get("negativeFragment", ""),
                "commercialTags": deepcopy(item.get("commercialTags", [])),
            }
            for item in pack.get("modifierGroups", [])
            if isinstance(item, dict)
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": item.get("id", ""),
                    "label": item.get("label", ""),
                    "negativePrompt": item.get("negativePrompt", ""),
                }
                for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("negativePolicies", []))
                if isinstance(item, dict)
            ],
            "commercialPolicies": [
                {
                    "id": item.get("id", ""),
                    "label": item.get("label", ""),
                    "mode": item.get("mode", ""),
                    "extraPrompt": item.get("extraPrompt", ""),
                    "restrictions": deepcopy(item.get("restrictions", [])),
                }
                for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("commercialPolicies", []))
                if isinstance(item, dict)
            ],
        },
    }
    if include_runtime_meta:
        document["name"] = prompt_pack_name_from_ref({"packId": pack.get("id", "")})
        document["source"] = pack.get("source", "")
        document["sourceFile"] = pack.get("sourceFile", "")
        document["writable"] = str(pack.get("source") or "") != "builtin"
    return document


def save_prompt_pack_document(root: Path, raw_pack: Dict[str, Any], *, file_name: str = "") -> Dict[str, Any]:
    packs_dir = root.resolve() / "prompts" / "illustration-packs"
    raw_pack_id = str(raw_pack.get("id") or "").strip()
    if raw_pack_id and _is_builtin_pack_id(raw_pack_id):
        raise ValueError(f"用户模板不能复用系统 pack id: {raw_pack_id}")
    pack_path = _resolve_prompt_pack_save_path(packs_dir, raw_pack, file_name)
    normalized = _normalize_prompt_pack(
        raw_pack,
        source="project",
        source_file=pack_path,
        fallback_pack_id=_derive_project_pack_id(pack_path),
    )
    if not normalized:
        raise ValueError("prompt pack 至少需要可推导的 id、label 或文件名")
    dump_json_compatible_yaml(pack_path, serialize_prompt_pack_document(normalized, include_runtime_meta=False))
    return normalized


def resolve_prompt_pack(root: Path, illustrations_state: Dict[str, Any], requested_pack_name: str = "") -> Dict[str, Any]:
    available_packs = load_available_prompt_packs(root)
    prompt_system = illustrations_state.get("promptSystem", {})
    pack_ref = prompt_system.get("defaultPack", {}) if isinstance(prompt_system, dict) else {}
    requested_name = str(requested_pack_name or "").strip()
    if requested_name:
        for pack in available_packs:
            candidate_ref = {"packId": pack.get("id", "")}
            if pack.get("id") == requested_name or prompt_pack_name_from_ref(candidate_ref) == requested_name:
                selected_ref = {
                    "source": str(pack.get("source") or "builtin"),
                    "packId": str(pack.get("id", "")),
                    "version": str(pack.get("version", "") or "builtin"),
                }
                return {
                    "pack": pack,
                    "packRef": selected_ref,
                    "packName": prompt_pack_name_from_ref(selected_ref) or requested_name,
                }
        selected_ref = default_pack_ref_from_name(requested_name)
    else:
        selected_ref = {
            "source": str(pack_ref.get("source") or "builtin"),
            "packId": str(pack_ref.get("packId") or default_pack_ref_from_name("default")["packId"]),
            "version": str(pack_ref.get("version") or default_pack_ref_from_name("default")["version"]),
        }

    selected_pack_id = selected_ref["packId"]
    selected_name = prompt_pack_name_from_ref(selected_ref) or "default"
    for pack in available_packs:
        if pack.get("id") == selected_pack_id or prompt_pack_name_from_ref({"packId": pack.get("id", "")}) == selected_name:
            selected_ref["version"] = str(pack.get("version") or selected_ref.get("version") or "")
            return {
                "pack": pack,
                "packRef": selected_ref,
                "packName": selected_name,
            }

    fallback_pack = deepcopy(BUILTIN_PROMPT_PACKS[0])
    fallback_ref = {
        "source": "builtin",
        "packId": fallback_pack["id"],
        "version": fallback_pack["version"],
    }
    return {
        "pack": fallback_pack,
        "packRef": fallback_ref,
        "packName": prompt_pack_name_from_ref(fallback_ref) or "default",
    }


def _load_project_prompt_packs(root: Path) -> List[Dict[str, Any]]:
    packs_dir = root / "prompts" / "illustration-packs"
    if not packs_dir.exists():
        return []
    packs: List[Dict[str, Any]] = []
    for path in sorted(packs_dir.glob("*.yaml")):
        raw = load_json_compatible_yaml(path, {})
        if isinstance(raw, dict):
            normalized = _normalize_prompt_pack(
                raw,
                source="project",
                source_file=path,
                fallback_pack_id=_derive_project_pack_id(path),
            )
            if normalized.get("id"):
                packs.append(normalized)
    return packs


def _builtin_pack_version(pack_id: str) -> str:
    for pack in BUILTIN_PROMPT_PACKS:
        if pack.get("id") == pack_id:
            return str(pack.get("version") or "")
    return ""


def _derive_project_pack_id(path: Path) -> str:
    stem = re.sub(r"[^a-z0-9-]+", "-", path.stem.strip().lower())
    stem = re.sub(r"-{2,}", "-", stem).strip("-")
    if not stem:
        stem = "custom-pack"
    return f"project/{stem}"


def _is_builtin_pack_id(pack_id: str) -> bool:
    normalized = pack_id.strip()
    if not normalized:
        return False
    return normalized in {str(item.get("id") or "").strip() for item in BUILTIN_PROMPT_PACKS}


def _resolve_prompt_pack_save_path(packs_dir: Path, raw_pack: Dict[str, Any], file_name: str) -> Path:
    existing_source_file = Path(str(raw_pack.get("sourceFile") or "")).expanduser() if raw_pack.get("sourceFile") else None
    if existing_source_file is not None:
        existing_path = existing_source_file.resolve()
        if _path_is_within(existing_path, packs_dir.resolve()) and existing_path.suffix.lower() == ".yaml":
            return existing_path
    stem_source = file_name.strip()
    if not stem_source:
        stem_source = str(raw_pack.get("id") or raw_pack.get("name") or raw_pack.get("label") or "").strip()
    stem = _slugify_prompt_pack_file_stem(stem_source)
    return packs_dir / f"{stem}.yaml"


def _slugify_prompt_pack_file_stem(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("/", "-"))
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "custom-pack"


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _normalize_prompt_pack(
    raw_pack: Dict[str, Any],
    *,
    source: str,
    source_file: Path | None = None,
    fallback_pack_id: str = "",
) -> Dict[str, Any]:
    pack_id = str(raw_pack.get("id") or fallback_pack_id).strip()
    if not pack_id:
        return {}
    version = str(raw_pack.get("version") or ("builtin" if source == "builtin" else "project")).strip()
    description = str(raw_pack.get("description") or "").strip()
    templates = _normalize_templates(raw_pack.get("templates"), pack_id)
    modifier_groups = _normalize_modifier_groups(raw_pack.get("modifierGroups"))
    policies = _normalize_policies(raw_pack.get("policies"))
    supports = _normalize_supports(raw_pack.get("supports"), templates)
    label = str(raw_pack.get("label") or prompt_pack_name_from_ref({"packId": pack_id}) or pack_id).strip()
    normalized = {
        "id": pack_id,
        "version": version or "builtin",
        "label": label,
        "description": description,
        "source": source,
        "supports": supports,
        "templates": templates,
        "modifierGroups": modifier_groups,
        "policies": policies,
    }
    if source_file is not None:
        normalized["sourceFile"] = str(source_file)
    return normalized


def _normalize_templates(raw_templates: Any, pack_id: str) -> List[Dict[str, Any]]:
    templates: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in raw_templates if isinstance(raw_templates, list) else []:
        if not isinstance(raw, dict):
            continue
        template_id = str(raw.get("id") or "").strip()
        use_case = str(raw.get("useCase") or "").strip()
        if not template_id or not use_case:
            continue
        if template_id in seen_ids:
            continue
        seen_ids.add(template_id)
        mode = str(raw.get("mode") or "text-to-image").strip() or "text-to-image"
        complexity = str(raw.get("complexity") or "standard").strip() or "standard"
        prompt_template = str(raw.get("promptTemplate") or "{subject}\n{styleModifiers}\n{userExtraPrompt}").strip()
        templates.append(
            {
                "id": template_id,
                "label": str(raw.get("label") or template_id).strip() or template_id,
                "useCase": use_case,
                "complexity": complexity,
                "mode": mode,
                "promptTemplate": prompt_template,
                "defaultNegativePolicyRef": str(raw.get("defaultNegativePolicyRef") or "").strip(),
                "defaultCommercialPolicyRef": str(raw.get("defaultCommercialPolicyRef") or "").strip(),
                "packId": pack_id,
            }
        )
    return templates


def _normalize_modifier_groups(raw_modifiers: Any) -> List[Dict[str, Any]]:
    modifiers: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in raw_modifiers if isinstance(raw_modifiers, list) else []:
        if not isinstance(raw, dict):
            continue
        modifier_id = str(raw.get("id") or "").strip()
        if not modifier_id or modifier_id in seen_ids:
            continue
        seen_ids.add(modifier_id)
        modifiers.append(
            {
                "id": modifier_id,
                "group": str(raw.get("group") or "style").strip() or "style",
                "label": str(raw.get("label") or modifier_id).strip() or modifier_id,
                "promptFragment": str(raw.get("promptFragment") or "").strip(),
                "negativeFragment": str(raw.get("negativeFragment") or "").strip(),
                "commercialTags": [
                    str(item).strip()
                    for item in raw.get("commercialTags", [])
                    if str(item).strip()
                ]
                if isinstance(raw.get("commercialTags"), list)
                else [],
            }
        )
    return modifiers


def _normalize_policies(raw_policies: Any) -> Dict[str, List[Dict[str, Any]]]:
    policies = raw_policies if isinstance(raw_policies, dict) else {}
    negative_policies: List[Dict[str, Any]] = []
    commercial_policies: List[Dict[str, Any]] = []
    seen_negative: set[str] = set()
    seen_commercial: set[str] = set()

    for raw in policies.get("negativePolicies", []) if isinstance(policies.get("negativePolicies"), list) else []:
        if not isinstance(raw, dict):
            continue
        policy_id = str(raw.get("id") or "").strip()
        if not policy_id or policy_id in seen_negative:
            continue
        seen_negative.add(policy_id)
        negative_policies.append(
            {
                "id": policy_id,
                "label": str(raw.get("label") or policy_id).strip() or policy_id,
                "negativePrompt": str(raw.get("negativePrompt") or "").strip(),
            }
        )

    for raw in policies.get("commercialPolicies", []) if isinstance(policies.get("commercialPolicies"), list) else []:
        if not isinstance(raw, dict):
            continue
        policy_id = str(raw.get("id") or "").strip()
        if not policy_id or policy_id in seen_commercial:
            continue
        seen_commercial.add(policy_id)
        commercial_policies.append(
            {
                "id": policy_id,
                "label": str(raw.get("label") or policy_id).strip() or policy_id,
                "mode": str(raw.get("mode") or "personal").strip() or "personal",
                "extraPrompt": str(raw.get("extraPrompt") or "").strip(),
                "restrictions": [
                    str(item).strip()
                    for item in raw.get("restrictions", [])
                    if str(item).strip()
                ]
                if isinstance(raw.get("restrictions"), list)
                else [],
            }
        )

    return {
        "negativePolicies": negative_policies,
        "commercialPolicies": commercial_policies,
    }


def _normalize_supports(raw_supports: Any, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
    supports = raw_supports if isinstance(raw_supports, dict) else {}
    raw_modes = supports.get("modes")
    modes: List[str] = []
    if isinstance(raw_modes, list):
        for item in raw_modes:
            normalized = str(item or "").strip()
            if normalized and normalized not in modes:
                modes.append(normalized)
    if not modes:
        for template in templates:
            mode = str(template.get("mode") or "").strip()
            if mode and mode not in modes:
                modes.append(mode)
    if not modes:
        modes = ["text-to-image"]
    return {
        "modes": modes,
        "commercial": bool(supports.get("commercial", False)),
    }
