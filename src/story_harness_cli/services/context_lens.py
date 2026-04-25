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
