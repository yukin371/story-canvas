from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from story_harness_cli.commands.export import write_volume_review_packet_for_chapter
from story_harness_cli.commands.review_support import build_world_check_payload
from story_harness_cli.protocol import chapter_path, ensure_project_root, load_project_state, save_state
from story_harness_cli.utils import now_iso, stable_hash
from story_harness_cli.utils.text import extract_tag_mentions

WORLD_CATALOG_KEYS = (
    ("worldRules", "world-rule"),
    ("factions", "faction"),
    ("locations", "location"),
    ("artifacts", "artifact"),
    ("mysteries", "mystery"),
)
WORLD_KIND_TO_STATE_KEY = {
    "world-rule": "worldRules",
    "faction": "factions",
    "location": "locations",
    "artifact": "artifacts",
    "mystery": "mysteries",
}
POWER_CUE_TERMS = (
    "修为",
    "境界",
    "突破",
    "冲击",
    "晋入",
    "晋升",
    "进阶",
    "破境",
    "灵台",
    "筑基",
    "金丹",
    "元婴",
)


def _parse_extra_fields(field_values: list[str]) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    for raw in field_values:
        if "=" not in raw:
            raise SystemExit(f"额外字段必须使用 key=value 形式: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise SystemExit(f"额外字段 key 不能为空: {raw}")
        try:
            extra[key] = json.loads(value)
        except json.JSONDecodeError:
            extra[key] = value
    return extra


def _normalize_aliases(values: list[str]) -> list[str]:
    aliases: list[str] = []
    for value in values:
        alias = str(value or "").strip()
        if alias and alias not in aliases:
            aliases.append(alias)
    return aliases


def _compact_world_item(kind: str, item: dict[str, Any]) -> dict[str, Any]:
    if kind == "world-rule":
        name = str(item.get("label") or item.get("name") or item.get("id") or "").strip()
        summary = str(item.get("summary") or item.get("rule") or "").strip()
    else:
        name = str(item.get("name") or item.get("title") or item.get("label") or item.get("id") or "").strip()
        summary = str(item.get("summary") or item.get("description") or item.get("rule") or "").strip()
    return {
        "id": item.get("id", ""),
        "kind": kind,
        "name": name,
        "summary": summary,
        "aliases": [alias for alias in item.get("aliases", []) if isinstance(alias, str)],
        "updatedAt": item.get("updatedAt", ""),
    }


def _find_world_item(items: list[dict[str, Any]], kind: str, item_id: str, name: str) -> dict[str, Any] | None:
    normalized_name = name.strip()
    for item in items:
        if not isinstance(item, dict):
            continue
        if item_id and item.get("id") == item_id:
            return item
        candidate_names = [
            value.strip()
            for value in (
                item.get("name"),
                item.get("title"),
                item.get("label"),
            )
            if isinstance(value, str) and value.strip()
        ]
        aliases = [alias.strip() for alias in item.get("aliases", []) if isinstance(alias, str) and alias.strip()]
        if normalized_name and normalized_name in candidate_names + aliases:
            return item
    return None


def _world_item_id(kind: str, name: str, explicit_id: str | None) -> str:
    if explicit_id:
        return explicit_id
    prefix = "rule" if kind == "world-rule" else kind
    return f"{prefix}-{stable_hash(f'{prefix}:{name}:{now_iso()}')}"


def _progression_id(label: str, explicit_id: str | None) -> str:
    if explicit_id:
        return explicit_id
    return f"progression-{stable_hash(f'{label}:{now_iso()}')}"


def _compact_progression(item: dict[str, Any]) -> dict[str, Any]:
    stages = item.get("stages", []) if isinstance(item.get("stages"), list) else []
    return {
        "id": item.get("id", ""),
        "kind": "progression",
        "label": item.get("label", ""),
        "stageCount": len(stages),
        "stages": [
            {
                "name": stage.get("name", ""),
                "nextStage": stage.get("nextStage", ""),
                "aliases": [alias for alias in stage.get("aliases", []) if isinstance(alias, str)],
                "breakthroughRequirements": [
                    value for value in stage.get("breakthroughRequirements", []) if isinstance(value, str)
                ],
                "bottleneck": stage.get("bottleneck", ""),
            }
            for stage in stages
            if isinstance(stage, dict)
        ],
        "updatedAt": item.get("updatedAt", ""),
    }


def _ordered_outline_chapters(state: dict[str, Any]) -> list[dict[str, Any]]:
    outline = state.get("outline", {})
    volumes = outline.get("volumes", [])
    if volumes:
        chapters: list[dict[str, Any]] = []
        for volume in volumes:
            chapters.extend(volume.get("chapters", []))
        return chapters
    return outline.get("chapters", [])


def _resolve_target_chapter_id(state: dict[str, Any], explicit_chapter_id: str | None) -> str | None:
    if explicit_chapter_id:
        return explicit_chapter_id
    active_chapter_id = state.get("project", {}).get("activeChapterId")
    if active_chapter_id:
        return active_chapter_id
    context_chapter_id = state.get("context_lens", {}).get("currentChapterId")
    if context_chapter_id:
        return context_chapter_id
    for chapter in _ordered_outline_chapters(state):
        chapter_id = chapter.get("id")
        if chapter_id:
            return chapter_id
    return None


def _find_volume_for_chapter(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    if not chapter_id:
        return {}
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return {}


def _build_target_volume_summary(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    volume = _find_volume_for_chapter(state, chapter_id)
    if not volume:
        return {
            "exists": False,
            "volumeId": "",
            "title": "",
            "theme": "",
            "chapterCount": 0,
            "currentChapterIndex": None,
        }
    chapters = volume.get("chapters", [])
    current_index = None
    for index, chapter in enumerate(chapters, start=1):
        if chapter.get("id") == chapter_id:
            current_index = index
            break
    return {
        "exists": True,
        "volumeId": volume.get("id", ""),
        "title": volume.get("title", ""),
        "theme": volume.get("theme", ""),
        "chapterCount": len(chapters),
        "currentChapterIndex": current_index,
    }


def _chapter_number(chapter_ref: str) -> int | None:
    match = re.search(r"(\d+)(?!.*\d)", chapter_ref or "")
    if not match:
        return None
    return int(match.group(1))


def _worldbook_has_content(worldbook: dict[str, Any]) -> bool:
    for key in ("premiseFacts", "worldRules", "powerProgressions", "factions", "locations", "artifacts", "mysteries"):
        values = worldbook.get(key, [])
        if isinstance(values, list) and values:
            return True
    return False


def _build_world_catalog(state: dict[str, Any]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    worldbook = state.get("worldbook", {})
    for key, kind in WORLD_CATALOG_KEYS:
        for index, item in enumerate(worldbook.get(key, []), start=1):
            if not isinstance(item, dict):
                continue
            canonical_name = ""
            for field in ("name", "title", "label"):
                value = item.get(field)
                if isinstance(value, str) and value.strip():
                    canonical_name = value.strip()
                    break
            if not canonical_name:
                continue
            names = [canonical_name]
            names.extend(alias for alias in item.get("aliases", []) if isinstance(alias, str) and alias.strip())
            catalog.append(
                {
                    "id": item.get("id") or f"{key}-{index}",
                    "canonicalName": canonical_name,
                    "names": names,
                    "kind": kind,
                    "source": f"worldbook.{key}",
                    "summary": item.get("summary") or item.get("description") or item.get("rule") or "",
                    "raw": item,
                }
            )
    return catalog


def _tagged_occurrence_count(text: str, names: list[str]) -> int:
    count = 0
    tagged_mentions = extract_tag_mentions(text)
    for mention in tagged_mentions:
        if mention in names:
            count += 1
    return count


def _quote_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    patterns = [
        ("“", "”"),
        ("‘", "’"),
        ("「", "」"),
        ('"', '"'),
    ]
    for opening, closing in patterns:
        start = 0
        while True:
            left = text.find(opening, start)
            if left < 0:
                break
            right = text.find(closing, left + len(opening))
            if right < 0:
                break
            ranges.append((left, right + len(closing)))
            start = right + len(closing)
    ranges.sort()
    return ranges


def _range_contains(ranges: list[tuple[int, int]], start: int, end: int) -> bool:
    for left, right in ranges:
        if start >= left and end <= right:
            return True
    return False


def _collect_unwrapped_mentions(text: str, names: list[str], quote_ranges: list[tuple[int, int]]) -> tuple[int, int]:
    plain_count = 0
    quoted_count = 0
    for name in sorted({item for item in names if item}, key=len, reverse=True):
        for match in re.finditer(re.escape(name), text):
            start = match.start()
            end = match.end()
            if start > 0 and text[start - 1] == "@":
                continue
            if start > 1 and text[start - 2:start] == "@{":
                continue
            if end < len(text) and text[end:end + 1] == "}":
                continue
            if _range_contains(quote_ranges, start, end):
                quoted_count += 1
            else:
                plain_count += 1
    return plain_count, quoted_count


def _collect_world_mentions(text: str, catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    quote_ranges = _quote_ranges(text)
    mentions: list[dict[str, Any]] = []
    for item in catalog:
        tagged_count = _tagged_occurrence_count(text, item["names"])
        plain_count, quoted_count = _collect_unwrapped_mentions(text, item["names"], quote_ranges)
        if tagged_count == 0 and plain_count == 0 and quoted_count == 0:
            continue
        mentions.append(
            {
                "id": item["id"],
                "name": item["canonicalName"],
                "kind": item["kind"],
                "source": item["source"],
                "summary": item["summary"],
                "taggedCount": tagged_count,
                "plainCount": plain_count,
                "quotedCount": quoted_count,
                "raw": item["raw"],
            }
        )
    mentions.sort(key=lambda item: (-(item["taggedCount"] + item["plainCount"]), item["name"]))
    return mentions


def _collect_volume_world_mentions(root: Path, volume: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not volume:
        return []

    aggregated: dict[tuple[str, str], dict[str, Any]] = {}
    for chapter in volume.get("chapters", []):
        chapter_id = chapter.get("id")
        if not chapter_id:
            continue
        file_path = chapter_path(root, chapter_id)
        if not file_path.exists():
            continue
        chapter_text = file_path.read_text(encoding="utf-8")
        for item in _collect_world_mentions(chapter_text, catalog):
            key = (item["source"], item["id"])
            entry = aggregated.setdefault(
                key,
                {
                    "id": item["id"],
                    "name": item["name"],
                    "kind": item["kind"],
                    "source": item["source"],
                    "summary": item["summary"],
                    "taggedCount": 0,
                    "plainCount": 0,
                    "quotedCount": 0,
                    "mentionedChapterCount": 0,
                    "mentionedChapterIds": [],
                },
            )
            entry["taggedCount"] += item["taggedCount"]
            entry["plainCount"] += item["plainCount"]
            entry["quotedCount"] += item["quotedCount"]
            if chapter_id not in entry["mentionedChapterIds"]:
                entry["mentionedChapterIds"].append(chapter_id)
                entry["mentionedChapterCount"] += 1

    result = list(aggregated.values())
    result.sort(key=lambda item: (-item["mentionedChapterCount"], -(item["taggedCount"] + item["plainCount"]), item["name"]))
    return result[:10]


def _module_policy_summary(state: dict[str, Any]) -> dict[str, Any]:
    story_template = state.get("project", {}).get("storyTemplate", {})
    module_policy = story_template.get("modulePolicy", {})
    if not isinstance(module_policy, dict):
        module_policy = {}
    required = [name for name, mode in module_policy.items() if mode == "required"]

    worldbook = state.get("worldbook", {})
    missing: list[str] = []
    if module_policy.get("worldbook") == "required" and not _worldbook_has_content(worldbook):
        missing.append("worldbook")
    if module_policy.get("worldRules") == "required" and not worldbook.get("worldRules", []):
        missing.append("worldRules")
    if module_policy.get("factions") == "required" and not worldbook.get("factions", []):
        missing.append("factions")

    return {
        "requiredModules": required,
        "missingRequiredModules": missing,
    }


def _worldbook_coverage(state: dict[str, Any]) -> dict[str, Any]:
    worldbook = state.get("worldbook", {})
    return {
        "worldRulesCount": len(worldbook.get("worldRules", [])),
        "powerProgressionCount": len(worldbook.get("powerProgressions", [])),
        "factionCount": len(worldbook.get("factions", [])),
        "locationCount": len(worldbook.get("locations", [])),
        "artifactCount": len(worldbook.get("artifacts", [])),
        "mysteryCount": len(worldbook.get("mysteries", [])),
        "hasAnyWorldbookContent": _worldbook_has_content(worldbook),
    }


def _extract_power_cue_evidence(chapter_text: str, state: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    lines = [line.strip() for line in chapter_text.splitlines() if line.strip()]
    for line in lines:
        if any(term in line for term in POWER_CUE_TERMS):
            evidence.append(line[:120])
            if len(evidence) >= 3:
                break
    if evidence:
        return evidence

    for entity in state.get("entities", {}).get("entities", []):
        if not isinstance(entity, dict):
            continue
        entity_state = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
        power_level = entity_state.get("powerLevel", {}) if isinstance(entity_state.get("powerLevel"), dict) else {}
        labels = [value for value in power_level.values() if isinstance(value, str) and value]
        if labels:
            evidence.append(f"{entity.get('name', entity.get('id', '实体'))} 已登记战力状态: {' / '.join(labels[:2])}")
            break
    return evidence


def _build_onboarding_gaps(
    chapter_id: str,
    chapter_text: str,
    state: dict[str, Any],
    chapter_mentions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    worldbook = state.get("worldbook", {})
    module_summary = _module_policy_summary(state)
    gaps: list[dict[str, Any]] = []

    for module_name in module_summary["missingRequiredModules"]:
        gaps.append(
            {
                "code": f"missing-required-{module_name}",
                "severity": "warning",
                "message": f"storyTemplate 要求 {module_name}，但当前世界真相层仍未补齐。",
                "evidence": [module_name],
                "suggestion": "先补齐必需模块，再让写前上下文和写后审查消费这些约束。",
            }
        )

    chapter_num = _chapter_number(chapter_id)
    early_chapter = chapter_num is not None and chapter_num <= 3
    referenced_names = [item["name"] for item in chapter_mentions if item["taggedCount"] or item["plainCount"]]
    if early_chapter and referenced_names and not worldbook.get("worldRules", []):
        gaps.append(
            {
                "code": "thin-early-world-onboarding",
                "severity": "warning",
                "message": "前几章已经引入世界名词，但 worldRules 仍为空，核心概念和制度解释容易偏薄。",
                "evidence": referenced_names[:3],
                "suggestion": "至少补一条当前卷正在兑现的世界规则、制度代价或底层运行逻辑。",
            }
        )

    power_cue_evidence = _extract_power_cue_evidence(chapter_text, state)
    if power_cue_evidence and not worldbook.get("powerProgressions", []):
        gaps.append(
            {
                "code": "missing-power-progressions",
                "severity": "warning",
                "message": "正文已经出现修炼/突破/境界信号，但 worldbook.powerProgressions 为空。",
                "evidence": power_cue_evidence,
                "suggestion": "补最小突破链：当前阶段 -> 下一阶段 -> 瓶颈/条件，避免后续战力推进失控。",
            }
        )

    return gaps


def _build_faction_registry_gaps(chapter_mentions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for item in chapter_mentions:
        if item.get("kind") != "faction":
            continue
        raw = item.get("raw", {})
        missing_fields: list[str] = []
        if not any(raw.get(field) for field in ("level", "tier", "rank", "grade", "hierarchy", "order")):
            missing_fields.append("hierarchy")
        if not any(raw.get(field) for field in ("status", "stance")):
            missing_fields.append("status")
        if not any(raw.get(field) for field in ("type", "category")):
            missing_fields.append("type")
        if not any(raw.get(field) for field in ("territory", "domain", "region", "base", "seat")):
            missing_fields.append("territory")
        if len(missing_fields) < 2:
            continue
        gaps.append(
            {
                "factionId": item.get("id", ""),
                "name": item.get("name", ""),
                "missingFields": missing_fields,
                "message": f"{item.get('name', '该势力')} 已登场，但建档仍缺少 {', '.join(missing_fields)}。",
                "suggestion": "至少补齐层级、状态、类型或地盘中的关键信息，支撑上下位压制和势力行为逻辑。",
            }
        )
    return gaps


def command_world_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    worldbook = state.get("worldbook", {})

    kind = args.kind or "all"
    counts = {
        "world-rule": len(worldbook.get("worldRules", [])),
        "faction": len(worldbook.get("factions", [])),
        "location": len(worldbook.get("locations", [])),
        "artifact": len(worldbook.get("artifacts", [])),
        "mystery": len(worldbook.get("mysteries", [])),
        "progression": len(worldbook.get("powerProgressions", [])),
    }

    items: list[dict[str, Any]] = []
    if kind in ("all", "world-rule"):
        items.extend(_compact_world_item("world-rule", item) for item in worldbook.get("worldRules", []) if isinstance(item, dict))
    if kind in ("all", "faction"):
        items.extend(_compact_world_item("faction", item) for item in worldbook.get("factions", []) if isinstance(item, dict))
    if kind in ("all", "location"):
        items.extend(_compact_world_item("location", item) for item in worldbook.get("locations", []) if isinstance(item, dict))
    if kind in ("all", "artifact"):
        items.extend(_compact_world_item("artifact", item) for item in worldbook.get("artifacts", []) if isinstance(item, dict))
    if kind in ("all", "mystery"):
        items.extend(_compact_world_item("mystery", item) for item in worldbook.get("mysteries", []) if isinstance(item, dict))
    if kind in ("all", "progression"):
        items.extend(_compact_progression(item) for item in worldbook.get("powerProgressions", []) if isinstance(item, dict))

    payload = {
        "kind": kind,
        "counts": counts,
        "items": items,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_world_add(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    kind = args.kind
    state_key = WORLD_KIND_TO_STATE_KEY[kind]
    worldbook = state.setdefault("worldbook", {})
    items = worldbook.setdefault(state_key, [])
    if not isinstance(items, list):
        raise SystemExit(f"worldbook.{state_key} 必须是列表")

    name = str(args.name or "").strip()
    if not name:
        raise SystemExit("缺少名称")
    extra_fields = _parse_extra_fields(args.field or [])
    aliases = _normalize_aliases(args.alias or [])
    existing = _find_world_item(items, kind, args.id or "", name)
    if existing and not args.upsert:
        raise SystemExit(f"{kind} 已存在，请改用 --upsert 或更换名称/ID: {name}")

    timestamp = now_iso()
    if kind == "world-rule":
        rule_text = str(args.rule or args.summary or "").strip()
        if not rule_text:
            raise SystemExit("world-rule 需要 --rule 或 --summary")
        payload: dict[str, Any] = {
            "id": _world_item_id(kind, name, args.id),
            "label": name,
            "rule": rule_text,
            "summary": str(args.summary or "").strip(),
            "aliases": aliases,
            "updatedAt": timestamp,
        }
    else:
        payload = {
            "id": _world_item_id(kind, name, args.id),
            "name": name,
            "summary": str(args.summary or "").strip(),
            "aliases": aliases,
            "updatedAt": timestamp,
        }
    payload.update(extra_fields)

    if existing:
        created_at = existing.get("createdAt", "")
        existing.clear()
        existing.update(payload)
        if created_at:
            existing["createdAt"] = created_at
        action = "updated"
        result_item = existing
    else:
        payload["createdAt"] = timestamp
        items.append(payload)
        action = "created"
        result_item = payload

    state.setdefault("project", {})["updatedAt"] = timestamp
    save_state(root, state)
    print(
        json.dumps(
            {
                "action": action,
                "kind": kind,
                "item": _compact_world_item(kind, result_item),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_world_mention_adopt(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    chapter_id = _resolve_target_chapter_id(state, args.chapter_id)
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    name = str(args.name or "").strip()
    if not name:
        raise SystemExit("缺少名称")
    kind = args.kind
    state_key = WORLD_KIND_TO_STATE_KEY[kind]
    worldbook = state.setdefault("worldbook", {})
    items = worldbook.setdefault(state_key, [])
    if not isinstance(items, list):
        raise SystemExit(f"worldbook.{state_key} 必须是列表")

    chapter_text = chapter_file.read_text(encoding="utf-8")
    tagged_mentions = set(extract_tag_mentions(chapter_text))
    if name not in tagged_mentions:
        if not args.allow_plain or name not in chapter_text:
            raise SystemExit(f"章节 {chapter_id} 中未找到可采纳的 mention: {name}")

    existing = _find_world_item(items, kind, args.id or "", name)
    if existing and not args.upsert:
        raise SystemExit(f"{kind} 已存在，请改用 --upsert 或更换名称/ID: {name}")

    extra_fields = _parse_extra_fields(args.field or [])
    aliases = _normalize_aliases(args.alias or [])
    timestamp = now_iso()

    if kind == "world-rule":
        rule_text = str(args.rule or args.summary or "").strip()
        if not rule_text:
            raise SystemExit("world-rule 需要 --rule 或 --summary")
        payload: dict[str, Any] = {
            "id": _world_item_id(kind, name, args.id),
            "label": name,
            "rule": rule_text,
            "summary": str(args.summary or "").strip(),
            "aliases": aliases,
            "updatedAt": timestamp,
        }
    else:
        payload = {
            "id": _world_item_id(kind, name, args.id),
            "name": name,
            "summary": str(args.summary or "").strip(),
            "aliases": aliases,
            "updatedAt": timestamp,
        }
    payload.update(extra_fields)

    if existing:
        created_at = existing.get("createdAt", "")
        existing.clear()
        existing.update(payload)
        if created_at:
            existing["createdAt"] = created_at
        action = "updated"
        result_item = existing
    else:
        payload["createdAt"] = timestamp
        items.append(payload)
        action = "created"
        result_item = payload

    state.setdefault("project", {})["updatedAt"] = timestamp
    save_state(root, state)
    review_packet_file = ""
    review_packet_refreshed = False
    review_packet_refresh_error = ""
    try:
        packet_path = write_volume_review_packet_for_chapter(root, state, chapter_id)
        if packet_path is not None:
            review_packet_file = str(packet_path)
            review_packet_refreshed = True
    except OSError as exc:
        review_packet_refresh_error = str(exc)
    print(
        json.dumps(
            {
                "action": action,
                "chapterId": chapter_id,
                "mentionSource": "tagged" if name in tagged_mentions else "plain",
                "kind": kind,
                "reviewPacketFile": review_packet_file,
                "reviewPacketRefreshed": review_packet_refreshed,
                "reviewPacketRefreshError": review_packet_refresh_error,
                "item": _compact_world_item(kind, result_item),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_world_progression_add(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    label = str(args.label or "").strip()
    if not label:
        raise SystemExit("缺少 progression label")
    progressions = state.setdefault("worldbook", {}).setdefault("powerProgressions", [])
    if not isinstance(progressions, list):
        raise SystemExit("worldbook.powerProgressions 必须是列表")
    extra_fields = _parse_extra_fields(args.field or [])
    existing = None
    for item in progressions:
        if not isinstance(item, dict):
            continue
        if args.id and item.get("id") == args.id:
            existing = item
            break
        if item.get("label") == label:
            existing = item
            break
    if existing and not args.upsert:
        raise SystemExit(f"power progression 已存在，请改用 --upsert 或更换 id/label: {label}")

    timestamp = now_iso()
    payload = {
        "id": _progression_id(label, args.id),
        "label": label,
        "stages": list(existing.get("stages", [])) if isinstance(existing, dict) else [],
        "updatedAt": timestamp,
    }
    payload.update(extra_fields)

    if existing:
        created_at = existing.get("createdAt", "")
        existing.clear()
        existing.update(payload)
        if created_at:
            existing["createdAt"] = created_at
        action = "updated"
        result = existing
    else:
        payload["createdAt"] = timestamp
        progressions.append(payload)
        action = "created"
        result = payload

    state.setdefault("project", {})["updatedAt"] = timestamp
    save_state(root, state)
    print(json.dumps({"action": action, "progression": _compact_progression(result)}, ensure_ascii=False, indent=2))
    return 0


def _find_progression(progressions: list[dict[str, Any]], progression_ref: str) -> dict[str, Any] | None:
    for item in progressions:
        if not isinstance(item, dict):
            continue
        if item.get("id") == progression_ref or item.get("label") == progression_ref:
            return item
    return None


def command_world_progression_stage_add(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    progressions = state.setdefault("worldbook", {}).setdefault("powerProgressions", [])
    if not isinstance(progressions, list):
        raise SystemExit("worldbook.powerProgressions 必须是列表")
    progression = _find_progression(progressions, args.progression_id)
    if not progression:
        raise SystemExit(f"未找到 power progression: {args.progression_id}")

    stages = progression.setdefault("stages", [])
    if not isinstance(stages, list):
        raise SystemExit("power progression.stages 必须是列表")

    stage_name = str(args.stage_name or "").strip()
    if not stage_name:
        raise SystemExit("缺少 stage name")

    extra_fields = _parse_extra_fields(args.field or [])
    aliases = _normalize_aliases(args.alias or [])
    requirements = _normalize_aliases(args.requirement or [])
    existing = None
    for item in stages:
        if not isinstance(item, dict):
            continue
        candidate_names = [item.get("name")] + [alias for alias in item.get("aliases", []) if isinstance(alias, str)]
        if stage_name in [value for value in candidate_names if isinstance(value, str)]:
            existing = item
            break
    if existing and not args.upsert:
        raise SystemExit(f"stage 已存在，请改用 --upsert 或更换名称: {stage_name}")

    payload = {
        "name": stage_name,
        "nextStage": str(args.next_stage or "").strip(),
        "aliases": aliases,
        "breakthroughRequirements": requirements,
        "bottleneck": str(args.bottleneck or "").strip(),
    }
    payload.update(extra_fields)

    if existing:
        existing.clear()
        existing.update(payload)
        action = "updated"
        stage_result = existing
    else:
        stages.append(payload)
        action = "created"
        stage_result = payload

    timestamp = now_iso()
    progression["updatedAt"] = timestamp
    if not progression.get("createdAt"):
        progression["createdAt"] = timestamp
    state.setdefault("project", {})["updatedAt"] = timestamp
    save_state(root, state)
    print(
        json.dumps(
            {
                "action": action,
                "progressionId": progression.get("id", ""),
                "progressionLabel": progression.get("label", ""),
                "stage": {
                    "name": stage_result.get("name", ""),
                    "nextStage": stage_result.get("nextStage", ""),
                    "aliases": [alias for alias in stage_result.get("aliases", []) if isinstance(alias, str)],
                    "breakthroughRequirements": [
                        value for value in stage_result.get("breakthroughRequirements", []) if isinstance(value, str)
                    ],
                    "bottleneck": stage_result.get("bottleneck", ""),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_world_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_target_chapter_id(state, args.chapter_id)
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    payload = build_world_check_payload(root, state, chapter_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def register_world_commands(subparsers) -> None:
    world_parser = subparsers.add_parser("world", help="World-scale and concept onboarding checks")
    world_sub = world_parser.add_subparsers(dest="world_action")

    list_cmd = world_sub.add_parser("list", help="List worldbook entries and power progressions")
    list_cmd.add_argument("--root", required=True)
    list_cmd.add_argument(
        "--kind",
        choices=["world-rule", "faction", "location", "artifact", "mystery", "progression", "all"],
        default="all",
    )
    list_cmd.set_defaults(func=command_world_list)

    add_cmd = world_sub.add_parser("add", help="Add or upsert a worldbook entry")
    add_cmd.add_argument("--root", required=True)
    add_cmd.add_argument("--kind", choices=sorted(WORLD_KIND_TO_STATE_KEY.keys()), required=True)
    add_cmd.add_argument("--id")
    add_cmd.add_argument("--name", required=True)
    add_cmd.add_argument("--summary", default="")
    add_cmd.add_argument("--rule", default="")
    add_cmd.add_argument("--alias", action="append", default=[])
    add_cmd.add_argument("--field", action="append", default=[], help="Extra JSON-compatible key=value field")
    add_cmd.add_argument("--upsert", action="store_true")
    add_cmd.set_defaults(func=command_world_add)

    mention_adopt = world_sub.add_parser(
        "mention-adopt",
        help="Adopt one mention from a chapter into worldbook after explicit confirmation",
    )
    mention_adopt.add_argument("--root", required=True)
    mention_adopt.add_argument("--chapter-id")
    mention_adopt.add_argument("--kind", choices=sorted(WORLD_KIND_TO_STATE_KEY.keys()), required=True)
    mention_adopt.add_argument("--id")
    mention_adopt.add_argument("--name", required=True)
    mention_adopt.add_argument("--summary", default="")
    mention_adopt.add_argument("--rule", default="")
    mention_adopt.add_argument("--alias", action="append", default=[])
    mention_adopt.add_argument("--field", action="append", default=[], help="Extra JSON-compatible key=value field")
    mention_adopt.add_argument("--allow-plain", action="store_true")
    mention_adopt.add_argument("--upsert", action="store_true")
    mention_adopt.set_defaults(func=command_world_mention_adopt)

    progression_add = world_sub.add_parser("progression-add", help="Add or upsert a power progression shell")
    progression_add.add_argument("--root", required=True)
    progression_add.add_argument("--id")
    progression_add.add_argument("--label", required=True)
    progression_add.add_argument("--field", action="append", default=[], help="Extra JSON-compatible key=value field")
    progression_add.add_argument("--upsert", action="store_true")
    progression_add.set_defaults(func=command_world_progression_add)

    stage_add = world_sub.add_parser("progression-stage-add", help="Add or upsert a stage under a power progression")
    stage_add.add_argument("--root", required=True)
    stage_add.add_argument("--progression-id", required=True)
    stage_add.add_argument("--stage-name", required=True)
    stage_add.add_argument("--next-stage", default="")
    stage_add.add_argument("--alias", action="append", default=[])
    stage_add.add_argument("--requirement", action="append", default=[])
    stage_add.add_argument("--bottleneck", default="")
    stage_add.add_argument("--field", action="append", default=[], help="Extra JSON-compatible key=value field")
    stage_add.add_argument("--upsert", action="store_true")
    stage_add.set_defaults(func=command_world_progression_stage_add)

    check_cmd = world_sub.add_parser(
        "check",
        help="Check world onboarding, faction coverage, and power-scale signals for a chapter",
    )
    check_cmd.add_argument("--root", required=True)
    check_cmd.add_argument("--chapter-id")
    check_cmd.set_defaults(func=command_world_check)
