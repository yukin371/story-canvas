from __future__ import annotations

import re
from typing import Any, Dict

from story_harness_cli.services.analyzer import chapter_title, entity_registry
from story_harness_cli.services.projection_engine import upsert_by_key
from story_harness_cli.utils import now_iso


def _chapter_number(chapter_ref: str) -> int | None:
    match = re.search(r"(\d+)(?!.*\d)", chapter_ref or "")
    if not match:
        return None
    return int(match.group(1))


def _chapter_in_window(chapter_id: str, window: Dict[str, Any]) -> bool:
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


def _compact_world_rule(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "label": item.get("label"),
        "rule": item.get("rule"),
        "scope": item.get("scope", ""),
    }


def _compact_faction(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "type": item.get("type", ""),
        "status": item.get("status", ""),
    }


def _compact_thread(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "label": item.get("label"),
        "type": item.get("type", ""),
        "status": item.get("status", ""),
        "targetPayoffScope": item.get("targetPayoffScope", ""),
        "relatedForeshadows": item.get("relatedForeshadows", [])[:5],
    }


def _compact_foreshadow(item: Dict[str, Any]) -> Dict[str, Any]:
    payoff_plan = item.get("payoffPlan", {})
    window = payoff_plan.get("window", {}) if isinstance(payoff_plan, dict) else {}
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "status": item.get("status", ""),
        "originType": (item.get("origin", {}) or {}).get("type", ""),
        "payoffWindowType": window.get("type", ""),
        "readerRealizationMode": payoff_plan.get("readerRealizationMode", ""),
        "payoffStyle": payoff_plan.get("style", ""),
        "emotionGoal": item.get("emotionGoal", [])[:3],
    }


def _foreshadow_due_in_chapter(item: Dict[str, Any], chapter_id: str) -> bool:
    if item.get("plannedPayoffChapter") == chapter_id:
        return True
    for payoff_point in item.get("payoffPoints", []):
        if payoff_point.get("chapterId") == chapter_id:
            return True
    payoff_plan = item.get("payoffPlan", {})
    if not isinstance(payoff_plan, dict):
        return False
    return _chapter_in_window(chapter_id, payoff_plan.get("window", {}))


def _select_active_threads(state: Dict[str, Dict[str, Any]], chapter_id: str, active_entity_ids: list[str]) -> list[Dict[str, Any]]:
    active_entity_set = set(active_entity_ids)
    active_threads = []
    for item in state.get("threads", {}).get("threads", []):
        if not isinstance(item, dict):
            continue
        related_entities = set(item.get("relatedEntities", []))
        related_chapters = set(item.get("relatedChapters", []))
        if (
            item.get("status") == "active"
            or chapter_id in related_chapters
            or item.get("targetChapterId") == chapter_id
            or bool(active_entity_set.intersection(related_entities))
        ):
            active_threads.append(_compact_thread(item))
    return active_threads[:5]


def _chapter_plan_hints(items: list[Any], *, fields: tuple[str, ...]) -> list[str]:
    hints: list[str] = []
    for item in items:
        text = ""
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            for field in fields:
                value = item.get(field)
                if isinstance(value, str) and value.strip():
                    text = value.strip()
                    break
        if text and text not in hints:
            hints.append(text)
        if len(hints) >= 3:
            break
    return hints


def _compact_handoff_chapter(chapter: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(chapter, dict):
        return None
    return {
        "id": chapter.get("id"),
        "title": chapter.get("title") or chapter.get("id", ""),
        "direction": (chapter.get("direction") or "").strip(),
        "beatHints": _chapter_plan_hints(chapter.get("beats", []), fields=("summary", "goal", "title", "beat")),
        "sceneGoals": _chapter_plan_hints(chapter.get("scenePlans", []), fields=("goal", "summary", "title")),
    }


def _chapter_triplet(outline: Dict[str, Any], chapter_id: str) -> tuple[Dict[str, Any] | None, Dict[str, Any] | None, Dict[str, Any] | None]:
    chapters = outline.get("chapters", [])
    for index, chapter in enumerate(chapters):
        if isinstance(chapter, dict) and chapter.get("id") == chapter_id:
            previous_chapter = chapters[index - 1] if index > 0 else None
            next_chapter = chapters[index + 1] if index + 1 < len(chapters) else None
            return previous_chapter, chapter, next_chapter
    return None, None, None


def build_chapter_handoff_context(
    state: Dict[str, Dict[str, Any]],
    chapter_id: str,
    *,
    active_entity_ids: list[str] | None = None,
) -> Dict[str, Any]:
    outline = state.get("outline", {})
    previous_chapter, current_chapter, next_chapter = _chapter_triplet(outline, chapter_id)
    previous_id = previous_chapter.get("id") if isinstance(previous_chapter, dict) else None
    active_entity_set = {item for item in (active_entity_ids or []) if item}

    carry_over_entity_changes = []
    if previous_id:
        for entity in state.get("entities", {}).get("entities", []):
            if not isinstance(entity, dict):
                continue
            if active_entity_set and entity.get("id") not in active_entity_set:
                continue
            change_log = entity.get("changeLog", []) if isinstance(entity.get("changeLog", []), list) else []
            matched_change = next(
                (
                    change
                    for change in reversed(change_log)
                    if isinstance(change, dict) and change.get("chapterId") == previous_id
                ),
                None,
            )
            if not matched_change:
                continue
            entity_state = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
            carry_over_entity_changes.append(
                {
                    "entityId": entity.get("id"),
                    "name": entity.get("name", entity.get("id", "")),
                    "fromChapterId": previous_id,
                    "field": matched_change.get("field", ""),
                    "reason": matched_change.get("reason", ""),
                    "stateTags": entity_state.get("statusTags", [])[:4]
                    if isinstance(entity_state.get("statusTags", []), list)
                    else [],
                }
            )
            if len(carry_over_entity_changes) >= 5:
                break

    active_thread_labels: list[str] = []
    for thread in state.get("threads", {}).get("threads", []):
        if not isinstance(thread, dict):
            continue
        related_entities = set(thread.get("relatedEntities", []))
        related_chapters = set(thread.get("relatedChapters", []))
        target_chapter_id = thread.get("targetChapterId")
        label = str(thread.get("label") or "").strip()
        if not label:
            continue
        if (
            chapter_id in related_chapters
            or previous_id in related_chapters
            or target_chapter_id in {chapter_id, previous_id}
            or bool(active_entity_set and active_entity_set.intersection(related_entities))
        ) and label not in active_thread_labels:
            active_thread_labels.append(label)
        if len(active_thread_labels) >= 4:
            break

    return {
        "previousChapter": _compact_handoff_chapter(previous_chapter),
        "currentChapter": _compact_handoff_chapter(current_chapter)
        or {"id": chapter_id, "title": chapter_title(outline, chapter_id), "direction": "", "beatHints": [], "sceneGoals": []},
        "nextChapter": _compact_handoff_chapter(next_chapter),
        "carryOverEntityChanges": carry_over_entity_changes,
        "activeThreadLabels": active_thread_labels,
    }


def refresh_context_lens(state: Dict[str, Dict[str, Any]], chapter_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    project = state["project"]
    projection = state["projection"]
    entities_by_id = entity_registry(state["entities"])
    raw_entities_by_id = {
        item.get("id"): item
        for item in state.get("entities", {}).get("entities", [])
        if isinstance(item, dict) and item.get("id")
    }
    worldbook = state.get("worldbook", {})
    foreshadowing = state.get("foreshadowing", {})

    scope = next(
        (item for item in projection.get("sceneScopeProjections", []) if item.get("chapterId") == chapter_id),
        None,
    )
    active_entity_ids = (scope or {}).get("activeEntityIds") or analysis.get("sceneScope", {}).get("activeEntityIds", [])
    snapshot_index = {
        (item.get("entityId"), item.get("scopeRef")): item
        for item in projection.get("snapshotProjections", [])
    }

    active_characters = []
    for entity_id in active_entity_ids[:6]:
        entity = raw_entities_by_id.get(entity_id) or entities_by_id.get(entity_id) or {
            "id": entity_id,
            "name": entity_id.replace("inferred::", ""),
            "currentState": "",
        }
        snapshot = snapshot_index.get((entity_id, chapter_id))
        entity_state = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
        status_tags = entity_state.get("statusTags", []) if isinstance(entity_state.get("statusTags", []), list) else []
        current_state = (snapshot or {}).get("currentState") or entity.get("currentState", "") or "；".join(status_tags[:3])
        change_log = entity.get("changeLog", []) if isinstance(entity.get("changeLog", []), list) else []
        recent_change = None
        for change in reversed(change_log):
            if change.get("chapterId") == chapter_id:
                recent_change = change
                break
        if recent_change is None and change_log:
            recent_change = change_log[-1]
        active_characters.append(
            {
                "id": entity_id,
                "name": entity.get("name", entity_id),
                "currentState": current_state,
                "stateTags": status_tags[:4],
                "powerLevel": entity_state.get("powerLevel", {}),
                "injuries": entity_state.get("injuries", [])[:3],
                "recentChange": (
                    {
                        "chapterId": recent_change.get("chapterId"),
                        "field": recent_change.get("field"),
                        "reason": recent_change.get("reason"),
                    }
                    if isinstance(recent_change, dict)
                    else None
                ),
            }
        )

    active_set = set(active_entity_ids)
    active_relations = [
        {
            "fromId": item.get("fromId"),
            "fromName": item.get("fromName"),
            "toId": item.get("toId"),
            "toName": item.get("toName"),
            "label": item.get("label"),
        }
        for item in projection.get("relationProjections", [])
        if item.get("scopeRef") == chapter_id
        and item.get("fromId") in active_set
        and item.get("toId") in active_set
    ]

    pending_requests = [
        item
        for item in state["reviews"].get("changeRequests", [])
        if item.get("chapterId") == chapter_id and item.get("status") in {"pending", "deferred"}
    ]
    active_threads = _select_active_threads(state, chapter_id, active_entity_ids)
    active_thread_ids = {item.get("id") for item in active_threads if item.get("id")}

    active_world_rules = [
        _compact_world_rule(item)
        for item in worldbook.get("worldRules", [])
        if isinstance(item, dict) and item.get("status") != "inactive"
    ][:5]
    active_factions = [
        _compact_faction(item)
        for item in worldbook.get("factions", [])
        if isinstance(item, dict) and item.get("status") != "inactive"
    ][:5]

    active_foreshadows = []
    due_foreshadows = []
    for item in foreshadowing.get("foreshadows", []):
        if not isinstance(item, dict):
            continue
        line_binding = item.get("lineBinding", {}) if isinstance(item.get("lineBinding", {}), dict) else {}
        related_entities = set(line_binding.get("entities", []))
        related_threads = set(line_binding.get("threads", []))
        planted_in_chapter = any(
            plant_point.get("chapterId") == chapter_id
            for plant_point in item.get("plantPoints", [])
            if isinstance(plant_point, dict)
        )
        if planted_in_chapter or active_set.intersection(related_entities) or active_thread_ids.intersection(related_threads):
            active_foreshadows.append(_compact_foreshadow(item))
        if _foreshadow_due_in_chapter(item, chapter_id):
            due_foreshadows.append(_compact_foreshadow(item))

    lens = {
        "chapterId": chapter_id,
        "chapterTitle": chapter_title(state["outline"], chapter_id),
        "emotionalContract": project.get("emotionalContract", {}),
        "storyTemplate": project.get("storyTemplate", {}),
        "chapterHandoff": build_chapter_handoff_context(state, chapter_id, active_entity_ids=active_entity_ids),
        "activeCharacters": active_characters,
        "activeRelations": active_relations,
        "activeWorldRules": active_world_rules,
        "activeFactions": active_factions,
        "activeThreads": active_threads,
        "activeForeshadows": active_foreshadows[:5],
        "dueForeshadows": due_foreshadows[:5],
        "pendingChangeRequestCount": len(pending_requests),
        "pendingChangeRequests": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "kind": item.get("kind"),
                "status": item.get("status"),
            }
            for item in pending_requests[:5]
        ],
        "updatedAt": now_iso(),
    }

    lenses = state["context_lens"].setdefault("lenses", [])
    upsert_by_key(lenses, ["chapterId"], lens)
    state["context_lens"]["currentChapterId"] = chapter_id
    return lens
