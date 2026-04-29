from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from story_harness_cli.commands.project_support import build_project_advisories
from story_harness_cli.protocol import (
    chapter_path,
    choose_style_profile_name,
    resolve_review_rule_profile,
    resolve_style_profile,
)
from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services import (
    analyze_style_text,
    build_style_report,
    chapter_title,
    check_consistency,
)
from story_harness_cli.services.reference_mentions import (
    build_reference_catalog as svc_build_reference_catalog,
    build_reference_mention_report as svc_build_reference_mention_report,
    collect_tag_replacements as svc_collect_tag_replacements,
)
from story_harness_cli.utils import stable_hash
from story_harness_cli.utils.text import count_words, extract_tag_mentions

WORLD_CATALOG_KEYS = (
    ("worldRules", "world-rule"),
    ("factions", "faction"),
    ("locations", "location"),
    ("artifacts", "artifact"),
    ("mysteries", "mystery"),
)
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


def find_volume(state: dict, volume_id: str | None) -> dict | None:
    if not volume_id:
        return None
    for volume in state.get("outline", {}).get("volumes", []):
        if volume.get("id") == volume_id:
            return volume
    raise SystemExit(f"volume 不存在: {volume_id}")


def build_mention_check_payload(state: dict, chapter_id: str, chapter_text: str) -> dict:
    report = svc_build_reference_mention_report(state, chapter_text)
    return {
        "chapterId": chapter_id,
        "chapterTitle": chapter_title(state.get("outline", {}), chapter_id),
        "taggedCovered": report["taggedCovered"],
        "taggedMissing": report["taggedMissing"],
        "knownUnwrapped": report["knownUnwrapped"],
        "ignoredQuotedKnownMentions": report["ignoredQuotedKnownMentions"],
        "relatedContext": report["relatedContext"],
        "summary": report["summary"],
    }


def _build_known_unwrapped_actions(chapter_id: str, replacements: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], dict] = {}
    for item in replacements:
        key = (item.get("source", ""), item.get("id", "") or item.get("canonicalName", ""))
        action_seed = f"{chapter_id}:{item.get('source', '')}:{item.get('id', '')}:{item.get('canonicalName', '')}"
        action = grouped.setdefault(
            key,
            {
                "actionId": f"tag-{stable_hash(action_seed)}",
                "actionType": "tag-known-reference",
                "referenceId": item.get("id", ""),
                "name": item.get("canonicalName", ""),
                "kind": item.get("kind", ""),
                "source": item.get("source", ""),
                "replacement": item.get("replacement", ""),
                "matchedNames": [],
                "occurrenceCount": 0,
            },
        )
        action["occurrenceCount"] += 1
        matched_name = item.get("matchedName", "")
        if matched_name and matched_name not in action["matchedNames"]:
            action["matchedNames"].append(matched_name)

    actions = list(grouped.values())
    actions.sort(key=lambda item: (-item["occurrenceCount"], item["name"], item["source"]))
    return actions


def _build_tagged_missing_actions(chapter_id: str, tagged_missing: list[dict]) -> list[dict]:
    actions: list[dict] = []
    for item in tagged_missing:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        suggested_targets = item.get("suggestedTargets", [])
        action_seed = f"{chapter_id}:{name}"
        actions.append(
            {
                "actionId": f"adopt-{stable_hash(action_seed)}",
                "actionType": "adopt-missing-reference",
                "name": name,
                "occurrenceCount": item.get("occurrenceCount", 1),
                "suggestion": item.get("suggestion", ""),
                "suggestedTargets": suggested_targets,
                "commandHints": [
                    f"entity mention-adopt --root <root> --chapter-id {chapter_id} --name {name}",
                    f"world mention-adopt --root <root> --chapter-id {chapter_id} --kind <kind> --name {name}",
                ],
            }
        )
    actions.sort(key=lambda item: (-item["occurrenceCount"], item["name"]))
    return actions


def build_mention_plan_payload(state: dict, chapter_id: str, chapter_text: str) -> dict:
    mention_payload = build_mention_check_payload(state, chapter_id, chapter_text)
    catalog = svc_build_reference_catalog(state)
    replacements = svc_collect_tag_replacements(chapter_text, catalog)
    known_unwrapped_actions = _build_known_unwrapped_actions(chapter_id, replacements)
    tagged_missing_actions = _build_tagged_missing_actions(chapter_id, mention_payload["taggedMissing"])
    return {
        "chapterId": chapter_id,
        "chapterTitle": mention_payload["chapterTitle"],
        "knownUnwrapped": mention_payload["knownUnwrapped"],
        "taggedMissing": mention_payload["taggedMissing"],
        "ignoredQuotedKnownMentions": mention_payload["ignoredQuotedKnownMentions"],
        "relatedContext": mention_payload["relatedContext"],
        "knownUnwrappedActions": known_unwrapped_actions,
        "taggedMissingActions": tagged_missing_actions,
        "reviewSummary": mention_payload["summary"],
        "summary": {
            "knownUnwrappedActionCount": len(known_unwrapped_actions),
            "taggedMissingActionCount": len(tagged_missing_actions),
            "totalActionCount": len(known_unwrapped_actions) + len(tagged_missing_actions),
        },
    }


def build_volume_mention_plan_payload(state: dict, root: Path, volume: dict) -> dict:
    chapter_plans: list[dict] = []
    total_known_unwrapped_actions = 0
    total_tagged_missing_actions = 0
    total_actions = 0
    for chapter in volume.get("chapters", []):
        chapter_id = chapter.get("id")
        if not chapter_id:
            continue
        chapter_file = chapter_path(root, chapter_id)
        if not chapter_file.exists():
            chapter_plans.append(
                {
                    "chapterId": chapter_id,
                    "chapterTitle": chapter_title(state.get("outline", {}), chapter_id),
                    "chapterFileExists": False,
                    "knownUnwrapped": [],
                    "taggedMissing": [],
                    "ignoredQuotedKnownMentions": [],
                    "relatedContext": [],
                    "knownUnwrappedActions": [],
                    "taggedMissingActions": [],
                    "reviewSummary": {
                        "taggedCount": 0,
                        "taggedCoveredCount": 0,
                        "taggedMissingCount": 0,
                        "knownUnwrappedCount": 0,
                        "ignoredQuotedKnownMentionCount": 0,
                    },
                    "summary": {
                        "knownUnwrappedActionCount": 0,
                        "taggedMissingActionCount": 0,
                        "totalActionCount": 0,
                    },
                }
            )
            continue
        chapter_text = chapter_file.read_text(encoding="utf-8")
        payload = build_mention_plan_payload(state, chapter_id, chapter_text)
        payload["chapterFileExists"] = True
        chapter_plans.append(payload)
        total_known_unwrapped_actions += payload["summary"]["knownUnwrappedActionCount"]
        total_tagged_missing_actions += payload["summary"]["taggedMissingActionCount"]
        total_actions += payload["summary"]["totalActionCount"]

    return {
        "scope": "volume",
        "volumeId": volume.get("id", ""),
        "volumeTitle": volume.get("title", ""),
        "chapterCount": len([item for item in volume.get("chapters", []) if item.get("id")]),
        "chapterPlans": chapter_plans,
        "summary": {
            "chapterPlanCount": len(chapter_plans),
            "knownUnwrappedActionCount": total_known_unwrapped_actions,
            "taggedMissingActionCount": total_tagged_missing_actions,
            "totalActionCount": total_actions,
        },
    }


def _chapter_number(chapter_ref: str) -> int | None:
    match = re.search(r"(\d+)(?!.*\d)", chapter_ref or "")
    if not match:
        return None
    return int(match.group(1))


def _chapter_in_window(chapter_id: str, window: dict) -> bool:
    if not isinstance(window, dict):
        return False
    target_chapter = window.get("targetChapter")
    if target_chapter:
        return target_chapter == chapter_id

    start = window.get("targetChapterStart")
    end = window.get("targetChapterEnd")
    if not start and not end:
        return False

    current_num = _chapter_number(chapter_id)
    start_num = _chapter_number(start) if start else None
    end_num = _chapter_number(end) if end else None
    if current_num is not None and (start_num is not None or end_num is not None):
        if start_num is not None and current_num < start_num:
            return False
        if end_num is not None and current_num > end_num:
            return False
        return True

    if start and chapter_id < start:
        return False
    if end and chapter_id > end:
        return False
    return True


def _chapter_after(target: str, chapter_id: str) -> bool:
    target_num = _chapter_number(target)
    current_num = _chapter_number(chapter_id)
    if target_num is not None and current_num is not None:
        return current_num > target_num
    return chapter_id > target


def _window_ended_before_chapter(window: dict, chapter_id: str) -> bool:
    if not isinstance(window, dict):
        return False
    target_chapter = window.get("targetChapter")
    if target_chapter:
        return _chapter_after(target_chapter, chapter_id)
    end = window.get("targetChapterEnd")
    if end:
        return _chapter_after(end, chapter_id)
    return False


def _foreshadow_title(item: dict) -> str:
    return str(item.get("title") or item.get("description") or item.get("id") or "").strip()


def _foreshadow_due_in_chapter(item: dict, chapter_id: str) -> bool:
    if item.get("status") == "resolved":
        return False
    if item.get("plannedPayoffChapter") == chapter_id:
        return True
    for payoff_point in item.get("payoffPoints", []):
        if payoff_point.get("chapterId") == chapter_id:
            return True
    payoff_plan = item.get("payoffPlan", {})
    if not isinstance(payoff_plan, dict):
        return False
    return _chapter_in_window(chapter_id, payoff_plan.get("window", {}))


def _foreshadow_overdue_for_chapter(item: dict, chapter_id: str) -> bool:
    if item.get("status") == "resolved":
        return False
    planned_payoff = item.get("plannedPayoffChapter")
    if isinstance(planned_payoff, str) and planned_payoff and _chapter_after(planned_payoff, chapter_id):
        return True
    payoff_plan = item.get("payoffPlan", {})
    if isinstance(payoff_plan, dict) and _window_ended_before_chapter(payoff_plan.get("window", {}), chapter_id):
        return True
    return False


def _foreshadow_schedule_summary(item: dict) -> dict:
    payoff_plan = item.get("payoffPlan", {}) if isinstance(item.get("payoffPlan", {}), dict) else {}
    window = payoff_plan.get("window", {}) if isinstance(payoff_plan, dict) else {}
    return {
        "plannedPayoffChapter": item.get("plannedPayoffChapter"),
        "window": window,
        "payoffPointCount": len(item.get("payoffPoints", [])),
    }


def _compact_foreshadow(item: dict) -> dict:
    return {
        "id": item.get("id", ""),
        "title": _foreshadow_title(item),
        "status": item.get("status", ""),
        "plantedChapter": item.get("plantedChapter")
        or (item.get("plantPoints", [{}])[0].get("chapterId") if item.get("plantPoints") else ""),
        "schedule": _foreshadow_schedule_summary(item),
    }


def build_foreshadow_check_payload(state: dict, chapter_id: str) -> dict:
    foreshadows = state.get("foreshadowing", {}).get("foreshadows", [])
    due = []
    overdue = []
    unresolved_without_schedule = []
    resolved = []

    for item in foreshadows:
        if not isinstance(item, dict):
            continue
        compact = _compact_foreshadow(item)
        if item.get("status") == "resolved":
            resolved.append(compact)
            continue
        has_schedule = bool(item.get("plannedPayoffChapter")) or bool(item.get("payoffPoints")) or bool(
            isinstance(item.get("payoffPlan"), dict) and item.get("payoffPlan", {}).get("window")
        )
        if _foreshadow_due_in_chapter(item, chapter_id):
            due.append(compact)
        elif _foreshadow_overdue_for_chapter(item, chapter_id):
            overdue.append(compact)
        elif not has_schedule:
            unresolved_without_schedule.append(compact)

    return {
        "chapterId": chapter_id,
        "projectActiveChapterId": state.get("project", {}).get("activeChapterId"),
        "dueForeshadows": due,
        "overdueForeshadows": overdue,
        "unresolvedWithoutSchedule": unresolved_without_schedule,
        "summary": {
            "foreshadowCount": len(foreshadows),
            "resolvedCount": len(resolved),
            "dueCount": len(due),
            "overdueCount": len(overdue),
            "unresolvedWithoutScheduleCount": len(unresolved_without_schedule),
        },
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


def resolve_target_chapter_id(state: dict[str, Any], explicit_chapter_id: str | None) -> str | None:
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


def find_volume_for_chapter(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    if not chapter_id:
        return {}
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return {}


def build_target_volume_summary(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    volume = find_volume_for_chapter(state, chapter_id)
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
            if start > 1 and text[start - 2 : start] == "@{":
                continue
            if end < len(text) and text[end : end + 1] == "}":
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


def build_volume_world_context_payload(root: Path, state: dict[str, Any], volume: dict[str, Any]) -> dict:
    catalog = _build_world_catalog(state)
    return {
        "exists": bool(volume),
        "volumeId": volume.get("id", "") if volume else "",
        "title": volume.get("title", "") if volume else "",
        "referencedItems": _collect_volume_world_mentions(root, volume, catalog),
    }


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


def build_world_check_payload(root: Path, state: dict[str, Any], chapter_id: str) -> dict:
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")
    chapter_text = chapter_file.read_text(encoding="utf-8")

    volume = find_volume_for_chapter(state, chapter_id)
    catalog = _build_world_catalog(state)
    chapter_mentions = _collect_world_mentions(chapter_text, catalog)
    volume_world_context = build_volume_world_context_payload(root, state, volume)
    onboarding_gaps = _build_onboarding_gaps(chapter_id, chapter_text, state, chapter_mentions)
    faction_registry_gaps = _build_faction_registry_gaps(chapter_mentions)
    consistency = check_consistency(state, chapter_text, chapter_id)

    return {
        "chapterId": chapter_id,
        "chapterTitle": chapter_title(state.get("outline", {}), chapter_id),
        "targetVolume": build_target_volume_summary(state, chapter_id),
        "modulePolicy": _module_policy_summary(state),
        "worldbookCoverage": _worldbook_coverage(state),
        "chapterWorldContext": {
            "referencedItems": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "kind": item["kind"],
                    "source": item["source"],
                    "summary": item["summary"],
                    "taggedCount": item["taggedCount"],
                    "plainCount": item["plainCount"],
                    "quotedCount": item["quotedCount"],
                }
                for item in chapter_mentions
            ],
        },
        "volumeWorldContext": volume_world_context,
        "onboardingGaps": onboarding_gaps,
        "scaleRisks": {
            "factionRegistryGaps": faction_registry_gaps,
            "capabilityTaskRisks": consistency.get("capabilityTaskRisks", []),
            "powerProgressionConflicts": consistency.get("powerProgressionConflicts", []),
        },
        "summary": {
            "chapterReferencedItemCount": len(chapter_mentions),
            "volumeReferencedItemCount": len(volume_world_context.get("referencedItems", [])),
            "onboardingGapCount": len(onboarding_gaps),
            "factionRegistryGapCount": len(faction_registry_gaps),
            "capabilityTaskRiskCount": len(consistency.get("capabilityTaskRisks", [])),
            "powerProgressionConflictCount": len(consistency.get("powerProgressionConflicts", [])),
        },
    }


def build_review_preflight_payload(
    root: Path,
    state: dict[str, Any],
    *,
    chapter_id: str | None = None,
    volume_id: str | None = None,
) -> dict:
    if chapter_id and volume_id:
        raise SystemExit("`--chapter-id` 与 `--volume-id` 不能同时使用")

    if volume_id:
        volume = find_volume(state, volume_id)
        if volume is None:
            raise SystemExit("缺少 volume id")
        mention_plan = build_volume_mention_plan_payload(state, root, volume)
        chapter_preflights: list[dict[str, Any]] = []
        summary = {
            "chapterPreflightCount": 0,
            "chapterFileMissingCount": 0,
            "knownUnwrappedActionCount": mention_plan["summary"]["knownUnwrappedActionCount"],
            "taggedMissingActionCount": mention_plan["summary"]["taggedMissingActionCount"],
            "mentionActionCount": mention_plan["summary"]["totalActionCount"],
            "dueForeshadowCount": 0,
            "overdueForeshadowCount": 0,
            "unresolvedWithoutScheduleCount": 0,
            "worldOnboardingGapCount": 0,
            "factionRegistryGapCount": 0,
            "capabilityTaskRiskCount": 0,
            "powerProgressionConflictCount": 0,
        }
        mention_plan_by_chapter = {item["chapterId"]: item for item in mention_plan["chapterPlans"]}
        for chapter in volume.get("chapters", []):
            chapter_id = chapter.get("id")
            if not chapter_id:
                continue
            summary["chapterPreflightCount"] += 1
            chapter_mention_plan = mention_plan_by_chapter.get(chapter_id, {})
            foreshadow_check = build_foreshadow_check_payload(state, chapter_id)
            chapter_file = chapter_path(root, chapter_id)
            chapter_word_count = 0
            if chapter_file.exists():
                chapter_word_count = count_words(chapter_file.read_text(encoding="utf-8"))
            chapter_summary = {
                "knownUnwrappedActionCount": chapter_mention_plan.get("summary", {}).get("knownUnwrappedActionCount", 0),
                "taggedMissingActionCount": chapter_mention_plan.get("summary", {}).get("taggedMissingActionCount", 0),
                "mentionActionCount": chapter_mention_plan.get("summary", {}).get("totalActionCount", 0),
                "dueForeshadowCount": foreshadow_check["summary"]["dueCount"],
                "overdueForeshadowCount": foreshadow_check["summary"]["overdueCount"],
                "unresolvedWithoutScheduleCount": foreshadow_check["summary"]["unresolvedWithoutScheduleCount"],
                "worldOnboardingGapCount": 0,
                "factionRegistryGapCount": 0,
                "capabilityTaskRiskCount": 0,
                "powerProgressionConflictCount": 0,
                "wordCount": chapter_word_count,
            }
            entry = {
                "chapterId": chapter_id,
                "chapterTitle": (
                    chapter.get("title")
                    or chapter_mention_plan.get("chapterTitle")
                    or chapter_title(state.get("outline", {}), chapter_id)
                ),
                "chapterFileExists": bool(chapter_mention_plan.get("chapterFileExists")),
                "mentionPlan": chapter_mention_plan,
                "foreshadowCheck": foreshadow_check,
                "summary": chapter_summary,
            }
            if not entry["chapterFileExists"]:
                summary["chapterFileMissingCount"] += 1
                entry["worldCheck"] = {
                    "chapterId": chapter_id,
                    "chapterTitle": entry["chapterTitle"],
                    "available": False,
                    "reason": "chapter-file-missing",
                }
            else:
                world_check = build_world_check_payload(root, state, chapter_id)
                chapter_summary["worldOnboardingGapCount"] = world_check["summary"]["onboardingGapCount"]
                chapter_summary["factionRegistryGapCount"] = world_check["summary"]["factionRegistryGapCount"]
                chapter_summary["capabilityTaskRiskCount"] = world_check["summary"]["capabilityTaskRiskCount"]
                chapter_summary["powerProgressionConflictCount"] = world_check["summary"]["powerProgressionConflictCount"]
                entry["worldCheck"] = {
                    "chapterId": world_check["chapterId"],
                    "chapterTitle": world_check["chapterTitle"],
                    "targetVolume": world_check["targetVolume"],
                    "modulePolicy": world_check["modulePolicy"],
                    "worldbookCoverage": world_check["worldbookCoverage"],
                    "chapterWorldContext": world_check["chapterWorldContext"],
                    "onboardingGaps": world_check["onboardingGaps"],
                    "scaleRisks": world_check["scaleRisks"],
                    "summary": world_check["summary"],
                }
            summary["dueForeshadowCount"] += chapter_summary["dueForeshadowCount"]
            summary["overdueForeshadowCount"] += chapter_summary["overdueForeshadowCount"]
            summary["unresolvedWithoutScheduleCount"] += chapter_summary["unresolvedWithoutScheduleCount"]
            summary["worldOnboardingGapCount"] += chapter_summary["worldOnboardingGapCount"]
            summary["factionRegistryGapCount"] += chapter_summary["factionRegistryGapCount"]
            summary["capabilityTaskRiskCount"] += chapter_summary["capabilityTaskRiskCount"]
            summary["powerProgressionConflictCount"] += chapter_summary["powerProgressionConflictCount"]
            chapter_preflights.append(entry)

        volume_structure_check = _build_volume_structure_check_payload(state, volume, chapter_preflights, summary)
        review_evidence = _build_volume_review_evidence(root, state, volume)
        return {
            "scope": "volume",
            "volumeId": volume.get("id", ""),
            "volumeTitle": volume.get("title", ""),
            "chapterCount": mention_plan["chapterCount"],
            "projectAdvisories": build_project_advisories(root, include_prd_content=True),
            "mentionPlan": mention_plan,
            "volumeWorldContext": build_volume_world_context_payload(root, state, volume),
            "volumeStructureCheck": volume_structure_check,
            "chapterPreflights": chapter_preflights,
            "reviewEvidence": review_evidence,
            "summary": summary,
        }

    target_chapter_id = resolve_target_chapter_id(state, chapter_id)
    if not target_chapter_id:
        raise SystemExit("缺少 chapter id")
    chapter_file = chapter_path(root, target_chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")
    chapter_text = chapter_file.read_text(encoding="utf-8")
    mention_plan = build_mention_plan_payload(state, target_chapter_id, chapter_text)
    foreshadow_check = build_foreshadow_check_payload(state, target_chapter_id)
    world_check = build_world_check_payload(root, state, target_chapter_id)
    return {
        "scope": "chapter",
        "chapterId": target_chapter_id,
        "chapterTitle": mention_plan["chapterTitle"],
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
        "targetVolume": world_check["targetVolume"],
        "mentionPlan": mention_plan,
        "foreshadowCheck": foreshadow_check,
        "worldCheck": world_check,
        "summary": {
            "knownUnwrappedActionCount": mention_plan["summary"]["knownUnwrappedActionCount"],
            "taggedMissingActionCount": mention_plan["summary"]["taggedMissingActionCount"],
            "mentionActionCount": mention_plan["summary"]["totalActionCount"],
            "dueForeshadowCount": foreshadow_check["summary"]["dueCount"],
            "overdueForeshadowCount": foreshadow_check["summary"]["overdueCount"],
            "unresolvedWithoutScheduleCount": foreshadow_check["summary"]["unresolvedWithoutScheduleCount"],
            "worldOnboardingGapCount": world_check["summary"]["onboardingGapCount"],
            "factionRegistryGapCount": world_check["summary"]["factionRegistryGapCount"],
            "capabilityTaskRiskCount": world_check["summary"]["capabilityTaskRiskCount"],
            "powerProgressionConflictCount": world_check["summary"]["powerProgressionConflictCount"],
        },
    }


def _build_volume_review_evidence(root: Path, state: dict[str, Any], volume: dict[str, Any]) -> dict[str, Any]:
    chapter_ids = [
        str(item.get("id", "")).strip()
        for item in volume.get("chapters", [])
        if str(item.get("id", "")).strip()
    ]
    chapter_reviews = _latest_reviews_by_chapter(
        state.get("story_reviews", {}).get("chapterReviews", []),
        chapter_ids=chapter_ids,
    )
    scene_reviews = _latest_scene_reviews_by_scope(
        state.get("story_reviews", {}).get("sceneReviews", []),
        chapter_ids=chapter_ids,
    )
    style_evidence = _build_volume_style_evidence(
        root,
        state,
        chapter_ids,
        volume_id=str(volume.get("id", "")),
    )
    return {
        "chapterReviewSummaries": [
            _compact_chapter_review(item)
            for item in chapter_reviews
        ],
        "lowSceneReviews": [
            _compact_scene_review(item)
            for item in _select_low_scene_reviews(scene_reviews)
        ],
        "styleAggregate": style_evidence.get("aggregate", {}),
        "styleFlaggedChapters": style_evidence.get("flaggedChapters", []),
        "topRuleJudgements": _collect_top_rule_judgements(chapter_reviews, scene_reviews),
        "contractAlignmentRisks": _collect_unique_risks(chapter_reviews, "contractAlignment"),
        "commercialAlignmentRisks": _collect_unique_risks(chapter_reviews, "commercialAlignment"),
        "reviewPacketRefs": [
            f"review-packet:{volume.get('id', '')}:{chapter_id}"
            for chapter_id in chapter_ids
        ],
    }


def _latest_reviews_by_chapter(reviews: list[dict[str, Any]], *, chapter_ids: list[str]) -> list[dict[str, Any]]:
    chapter_id_set = set(chapter_ids)
    latest_by_chapter: dict[str, dict[str, Any]] = {}
    for review in reviews:
        chapter_id = str(review.get("chapterId", "")).strip()
        if chapter_id not in chapter_id_set:
            continue
        existing = latest_by_chapter.get(chapter_id)
        generated_at = str(review.get("generatedAt", ""))
        if existing is None or generated_at >= str(existing.get("generatedAt", "")):
            latest_by_chapter[chapter_id] = review
    return [
        latest_by_chapter[chapter_id]
        for chapter_id in chapter_ids
        if chapter_id in latest_by_chapter
    ]


def _filter_scene_reviews(reviews: list[dict[str, Any]], *, chapter_ids: list[str]) -> list[dict[str, Any]]:
    chapter_id_set = set(chapter_ids)
    return [
        item
        for item in reviews
        if str(item.get("chapterId", "")).strip() in chapter_id_set
    ]


def _latest_scene_reviews_by_scope(reviews: list[dict[str, Any]], *, chapter_ids: list[str]) -> list[dict[str, Any]]:
    chapter_id_set = set(chapter_ids)
    latest_by_scope: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for review in reviews:
        chapter_id = str(review.get("chapterId", "")).strip()
        if chapter_id not in chapter_id_set:
            continue
        scene_range = review.get("sceneRange", {}) if isinstance(review.get("sceneRange", {}), dict) else {}
        scene_index = str(scene_range.get("sceneIndex", "") or "")
        if scene_index:
            scope_key = (chapter_id, scene_index, "", "")
        else:
            scope_key = (
                chapter_id,
                "",
                str(scene_range.get("startParagraph", "") or ""),
                str(scene_range.get("endParagraph", "") or ""),
            )
        existing = latest_by_scope.get(scope_key)
        generated_at = str(review.get("generatedAt", ""))
        if existing is None or generated_at >= str(existing.get("generatedAt", "")):
            latest_by_scope[scope_key] = review
    return sorted(
        latest_by_scope.values(),
        key=lambda item: (
            chapter_ids.index(str(item.get("chapterId", "")).strip())
            if str(item.get("chapterId", "")).strip() in chapter_ids
            else 999,
            int((item.get("sceneRange", {}) or {}).get("sceneIndex", 999) or 999),
            str(item.get("generatedAt", "")),
        ),
    )


def _build_volume_style_evidence(
    root: Path,
    state: dict[str, Any],
    chapter_ids: list[str],
    *,
    volume_id: str,
) -> dict[str, Any]:
    if not chapter_ids:
        return {"aggregate": {}, "flaggedChapters": []}
    profile_name = choose_style_profile_name(state.get("project", {}))
    profile_config, _profile_source = resolve_style_profile(root, profile_name)
    review_rule_config, review_rule_profile_name, _review_rule_source = resolve_review_rule_profile(root)
    scorer, source = load_style_similarity_scorer()
    chapter_reports: list[dict[str, Any]] = []
    for chapter_id in chapter_ids:
        chapter_file = chapter_path(root, chapter_id)
        if not chapter_file.exists():
            continue
        volume = find_volume_for_chapter(state, chapter_id)
        style_report = analyze_style_text(
            chapter_file.read_text(encoding="utf-8"),
            opener_similarity_scorer=scorer,
            repetition_source=source,
            profile_name=profile_name,
            profile_config=profile_config,
            review_rule_profile_name=review_rule_profile_name,
            review_rule_config=review_rule_config,
            review_rule_scope={
                "chapterId": chapter_id,
                "volumeId": str(volume.get("id", "")),
                "scenePlanId": "",
            },
        )
        chapter_reports.append(
            {
                "chapterId": chapter_id,
                "styleAnalysis": style_report["styleAnalysis"],
                "stylePayload": style_report,
            }
        )
    aggregate = build_style_report(chapter_reports, volume_id=volume_id, profile_name=profile_name)
    summary_by_chapter = {
        item["chapterId"]: item["stylePayload"].get("styleAnalysis", {}).get("summary", "")
        for item in chapter_reports
    }
    flagged = []
    for item in aggregate.get("flaggedChapters", []):
        flagged.append(
            {
                "chapterId": item.get("chapterId", ""),
                "overallScore": item.get("overallScore"),
                "totalDeduction": item.get("totalDeduction"),
                "detectedPatterns": item.get("detectedPatterns", []),
                "summary": summary_by_chapter.get(item.get("chapterId", ""), ""),
            }
        )
    return {
        "aggregate": aggregate,
        "flaggedChapters": flagged,
    }


def _compact_chapter_review(review: dict[str, Any]) -> dict[str, Any]:
    style_analysis = review.get("styleAnalysis", {}).get("styleAnalysis", {})
    return {
        "chapterId": review.get("chapterId", ""),
        "chapterTitle": review.get("chapterTitle", ""),
        "generatedAt": review.get("generatedAt", ""),
        "rating": review.get("rating", ""),
        "totalScore": review.get("scores", {}).get("total"),
        "weightedTotal": review.get("weightedScores", {}).get("total"),
        "summary": review.get("summary", ""),
        "priorityActions": list(review.get("priorityActions", []))[:3],
        "styleSummary": style_analysis.get("summary", ""),
        "ruleJudgementIds": [
            item.get("ruleId", "")
            for item in review.get("ruleJudgements", [])
            if item.get("ruleId")
        ][:5],
    }


def _select_low_scene_reviews(scene_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for review in scene_reviews:
        total = review.get("scores", {}).get("total")
        rating = str(review.get("rating", "")).strip().lower()
        if isinstance(total, (int, float)) and total <= 80:
            selected.append(review)
            continue
        if rating and rating not in {"solid", "strong"}:
            selected.append(review)
    selected.sort(
        key=lambda item: (
            item.get("scores", {}).get("total", 999),
            str(item.get("chapterId", "")),
            int(item.get("sceneRange", {}).get("sceneIndex", 999) or 999),
        )
    )
    return selected[:8]


def _compact_scene_review(review: dict[str, Any]) -> dict[str, Any]:
    scene_range = review.get("sceneRange", {})
    return {
        "chapterId": review.get("chapterId", ""),
        "generatedAt": review.get("generatedAt", ""),
        "rating": review.get("rating", ""),
        "totalScore": review.get("scores", {}).get("total"),
        "summary": review.get("summary", ""),
        "sceneIndex": scene_range.get("sceneIndex"),
        "startParagraph": scene_range.get("startParagraph"),
        "endParagraph": scene_range.get("endParagraph"),
        "priorityActions": list(review.get("priorityActions", []))[:3],
    }


def _collect_top_rule_judgements(
    chapter_reviews: list[dict[str, Any]],
    scene_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], dict[str, Any]] = {}
    for review in [*chapter_reviews, *scene_reviews]:
        for item in review.get("ruleJudgements", []):
            rule_id = str(item.get("ruleId", "")).strip()
            message = str(item.get("message", "")).strip()
            key = (rule_id, message)
            entry = counts.setdefault(
                key,
                {
                    "ruleId": rule_id,
                    "message": message,
                    "severity": item.get("severity", ""),
                    "hits": 0,
                },
            )
            entry["hits"] += 1
    ranked = sorted(
        counts.values(),
        key=lambda item: (-int(item.get("hits", 0)), str(item.get("ruleId", "")), str(item.get("message", ""))),
    )
    return ranked[:8]


def _collect_unique_risks(chapter_reviews: list[dict[str, Any]], field_name: str) -> list[str]:
    risks: list[str] = []
    seen: set[str] = set()
    for review in chapter_reviews:
        payload = review.get(field_name, {})
        for item in payload.get("risks", []):
            value = str(item).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            risks.append(value)
    return risks[:8]


def _build_volume_structure_check_payload(
    state: dict[str, Any],
    volume: dict[str, Any],
    chapter_preflights: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    ordered_volumes = state.get("outline", {}).get("volumes", [])
    volume_ids = [str(item.get("id", "")).strip() for item in ordered_volumes if isinstance(item, dict)]
    current_volume_id = str(volume.get("id", "")).strip()
    is_intro_volume = bool(volume_ids) and volume_ids[0] == current_volume_id
    role = "intro-volume" if is_intro_volume else "standard-volume"

    phase_assignments = _build_volume_phase_assignments(chapter_preflights)
    checklist = [
        _build_outline_coverage_check(volume, chapter_preflights),
        _build_intro_onboarding_check(chapter_preflights, enabled=is_intro_volume),
        _build_foreshadow_debt_check(summary, chapter_preflights),
        _build_closure_readiness_check(volume, chapter_preflights, summary),
    ]
    summary_payload = {
        "passCount": sum(1 for item in checklist if item["status"] == "pass"),
        "riskCount": sum(1 for item in checklist if item["status"] == "risk"),
        "missingCount": sum(1 for item in checklist if item["status"] == "missing"),
        "notApplicableCount": sum(1 for item in checklist if item["status"] == "not_applicable"),
    }
    return {
        "role": role,
        "phaseAssignments": phase_assignments,
        "checklist": checklist,
        "summary": summary_payload,
    }


def _build_volume_phase_assignments(chapter_preflights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(chapter_preflights)
    if total <= 0:
        return []
    if total == 1:
        phase_names = ["opening"]
    elif total == 2:
        phase_names = ["opening", "close"]
    elif total == 3:
        phase_names = ["opening", "build", "close"]
    elif total == 4:
        phase_names = ["opening", "build", "climax", "close"]
    else:
        phase_names = ["opening"] + ["build"] * (total - 3) + ["climax", "close"]
        turn_index = total // 2
        phase_names[turn_index] = "turn"
    return [
        {
            "chapterId": item.get("chapterId", ""),
            "chapterTitle": item.get("chapterTitle", ""),
            "phase": phase_names[index],
        }
        for index, item in enumerate(chapter_preflights)
    ]


def _build_outline_coverage_check(
    volume: dict[str, Any],
    chapter_preflights: list[dict[str, Any]],
) -> dict[str, Any]:
    chapter_map = {
        str(item.get("chapterId", "")).strip(): item
        for item in chapter_preflights
        if isinstance(item, dict)
    }
    total = 0
    covered = 0
    missing_ids: list[str] = []
    missing_titles: list[str] = []
    for chapter in volume.get("chapters", []):
        if not isinstance(chapter, dict):
            continue
        chapter_id = str(chapter.get("id", "")).strip()
        if not chapter_id:
            continue
        total += 1
        has_direction = bool(str(chapter.get("direction", "")).strip())
        has_beats = bool(chapter.get("beats", []))
        has_scene_plans = bool(chapter.get("scenePlans", []))
        if has_direction or has_beats or has_scene_plans:
            covered += 1
            continue
        missing_ids.append(chapter_id)
        title = chapter_map.get(chapter_id, {}).get("chapterTitle") or chapter.get("title") or chapter_id
        missing_titles.append(str(title))
    if total == 0:
        return {
            "id": "outline-coverage",
            "label": "卷级结构明示度",
            "status": "missing",
            "message": "当前卷还没有可用章节，无法判断结构明示度。",
            "evidence": [],
            "targetChapterIds": [],
            "suggestion": "先补出卷内章节骨架，再进入卷级结构审查。",
        }
    if covered == total:
        return {
            "id": "outline-coverage",
            "label": "卷级结构明示度",
            "status": "pass",
            "message": f"当前卷 {covered}/{total} 章都已具备 direction / beats / scenePlans 中的至少一项结构信号。",
            "evidence": [],
            "targetChapterIds": [],
            "suggestion": "",
        }
    if covered == 0:
        status = "missing"
    else:
        status = "risk"
    return {
        "id": "outline-coverage",
        "label": "卷级结构明示度",
        "status": status,
        "message": f"当前卷仅 {covered}/{total} 章具备显式结构信号，仍有 {len(missing_titles)} 章接近空壳。",
        "evidence": missing_titles[:5],
        "targetChapterIds": missing_ids[:5],
        "suggestion": "至少给缺失章节补 direction、beats 或 scenePlans，避免卷审只看到材料堆积却看不到结构职责。",
    }


def _build_intro_onboarding_check(
    chapter_preflights: list[dict[str, Any]],
    *,
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {
            "id": "intro-world-onboarding",
            "label": "引入卷 onboarding",
            "status": "not_applicable",
            "message": "当前卷不是第一卷，引入卷 onboarding 检查跳过。",
            "evidence": [],
            "targetChapterIds": [],
            "suggestion": "",
        }
    early_chapters = chapter_preflights[:3]
    gap_count = sum(int(item.get("summary", {}).get("worldOnboardingGapCount", 0) or 0) for item in early_chapters)
    if gap_count == 0:
        return {
            "id": "intro-world-onboarding",
            "label": "引入卷 onboarding",
            "status": "pass",
            "message": "前几章没有暴露额外 world onboarding 缺口。",
            "evidence": [],
            "targetChapterIds": [],
            "suggestion": "",
        }
    target_ids = [
        str(item.get("chapterId", "")).strip()
        for item in early_chapters
        if int(item.get("summary", {}).get("worldOnboardingGapCount", 0) or 0) > 0
        and str(item.get("chapterId", "")).strip()
    ]
    evidence = [
        f"{item.get('chapterTitle', item.get('chapterId', ''))}: onboarding gaps {item.get('summary', {}).get('worldOnboardingGapCount', 0)}"
        for item in early_chapters
        if int(item.get("summary", {}).get("worldOnboardingGapCount", 0) or 0) > 0
    ]
    return {
        "id": "intro-world-onboarding",
        "label": "引入卷 onboarding",
        "status": "risk",
        "message": f"前 {len(early_chapters)} 章累计暴露 {gap_count} 个世界 onboarding 缺口，引入卷解释压力偏高。",
        "evidence": evidence,
        "targetChapterIds": target_ids,
        "suggestion": "把核心概念、制度代价和读者必须先懂的底板前置到黄金三章附近，不要只靠后续伏笔兜底。",
    }


def _build_foreshadow_debt_check(
    summary: dict[str, Any],
    chapter_preflights: list[dict[str, Any]],
) -> dict[str, Any]:
    due_count = int(summary.get("dueForeshadowCount", 0) or 0)
    overdue_count = int(summary.get("overdueForeshadowCount", 0) or 0)
    unscheduled_count = int(summary.get("unresolvedWithoutScheduleCount", 0) or 0)
    if due_count == 0 and overdue_count == 0 and unscheduled_count == 0:
        return {
            "id": "foreshadow-debt",
            "label": "伏笔债务",
            "status": "pass",
            "message": "当前卷没有积压的到窗 / 逾期 / 未排期伏笔。",
            "evidence": [],
            "targetChapterIds": [],
            "suggestion": "",
        }
    target_ids = [
        str(item.get("chapterId", "")).strip()
        for item in chapter_preflights
        if (
            int(item.get("summary", {}).get("dueForeshadowCount", 0) or 0) > 0
            or int(item.get("summary", {}).get("overdueForeshadowCount", 0) or 0) > 0
            or int(item.get("summary", {}).get("unresolvedWithoutScheduleCount", 0) or 0) > 0
        )
        and str(item.get("chapterId", "")).strip()
    ]
    return {
        "id": "foreshadow-debt",
        "label": "伏笔债务",
        "status": "risk",
        "message": f"当前卷存在伏笔债务：到窗 {due_count}，逾期 {overdue_count}，未排期 {unscheduled_count}。",
        "evidence": [],
        "targetChapterIds": target_ids,
        "suggestion": "先决定本卷必须回收的短线伏笔，再区分哪些长线可以明确带到下一卷。",
    }


def _build_closure_readiness_check(
    volume: dict[str, Any],
    chapter_preflights: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    if not chapter_preflights:
        return {
            "id": "closure-readiness",
            "label": "卷尾收束准备度",
            "status": "missing",
            "message": "当前卷没有可检查章节，无法判断卷尾收束准备度。",
            "evidence": [],
            "targetChapterIds": [],
            "suggestion": "先补最小卷骨架，再判断闭环是否成立。",
        }
    last_chapter_entry = chapter_preflights[-1]
    last_chapter_id = str(last_chapter_entry.get("chapterId", "")).strip()
    volume_chapters = [item for item in volume.get("chapters", []) if isinstance(item, dict)]
    last_outline_chapter = volume_chapters[-1] if volume_chapters else {}
    last_status = str(last_outline_chapter.get("status", "")).strip()
    last_file_exists = bool(last_chapter_entry.get("chapterFileExists"))
    blocking_foreshadows = (
        int(summary.get("overdueForeshadowCount", 0) or 0)
        + int(summary.get("unresolvedWithoutScheduleCount", 0) or 0)
    )
    if not last_file_exists:
        return {
            "id": "closure-readiness",
            "label": "卷尾收束准备度",
            "status": "missing",
            "message": "卷尾章节文件仍缺失，当前还谈不上卷级收束。",
            "evidence": [str(last_chapter_entry.get("chapterTitle", last_chapter_entry.get("chapterId", "")))],
            "targetChapterIds": [last_chapter_id] if last_chapter_id else [],
            "suggestion": "先补齐卷尾正文，再判断这一卷是否形成完整小故事单元。",
        }
    if last_status != "completed" or blocking_foreshadows > 0:
        return {
            "id": "closure-readiness",
            "label": "卷尾收束准备度",
            "status": "risk",
            "message": (
                f"卷尾章节状态 `{last_status or 'unknown'}`，"
                f"同时仍有 {blocking_foreshadows} 项逾期/未排期伏笔，卷级收束准备不足。"
            ),
            "evidence": [str(last_chapter_entry.get("chapterTitle", last_chapter_entry.get("chapterId", "")))],
            "targetChapterIds": [last_chapter_id] if last_chapter_id else [],
            "suggestion": "至少先补一轮卷尾收束与短线回收，再进入卷级自审或人工审查。",
        }
    return {
        "id": "closure-readiness",
        "label": "卷尾收束准备度",
        "status": "pass",
        "message": "卷尾章节已落正文且没有明显逾期/未排期伏笔，具备进入卷级闭环判断的最低前提。",
        "evidence": [str(last_chapter_entry.get("chapterTitle", last_chapter_entry.get("chapterId", "")))],
        "targetChapterIds": [],
        "suggestion": "",
    }
