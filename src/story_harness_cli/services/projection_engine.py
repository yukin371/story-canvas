from __future__ import annotations

from typing import Any, Dict, Iterable, List

from story_harness_cli.utils import now_iso, stable_hash


def upsert_by_key(items: List[Dict[str, Any]], key_fields: Iterable[str], payload: Dict[str, Any]) -> None:
    for item in items:
        if all(item.get(field) == payload.get(field) for field in key_fields):
            item.update(payload)
            return
    items.append(payload)


def apply_projection(
    state: Dict[str, Dict[str, Any]],
    analysis: Dict[str, Any],
    chapter_id: str | None,
    consistency_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    applied_changes = 0
    applied_premise_facts = 0
    requests = state["reviews"].setdefault("changeRequests", [])
    projection = state["projection"]
    log_entries = state["projection_log"].setdefault("projectionChanges", [])

    for request in requests:
        if request.get("status") != "accepted":
            continue
        if request.get("projectionStatus") == "applied":
            continue
        if chapter_id and request.get("chapterId") != chapter_id:
            continue

        if request.get("kind") == "snapshot":
            payload = request.get("suggestedPayload", {})
            upsert_by_key(
                projection.setdefault("snapshotProjections", []),
                ["entityId", "scopeRef"],
                {
                    "entityId": payload.get("entityId"),
                    "entityName": payload.get("entityName"),
                    "scopeRef": request.get("chapterId"),
                    "currentState": payload.get("state"),
                    "sourceChangeIds": [request.get("id")],
                    "updatedAt": now_iso(),
                },
            )
        elif request.get("kind") == "relation":
            payload = request.get("suggestedPayload", {})
            upsert_by_key(
                projection.setdefault("relationProjections", []),
                ["fromId", "toId", "scopeRef"],
                {
                    "fromId": payload.get("fromId"),
                    "fromName": payload.get("fromName"),
                    "toId": payload.get("toId"),
                    "toName": payload.get("toName"),
                    "scopeRef": request.get("chapterId"),
                    "label": payload.get("label"),
                    "sourceChangeIds": [request.get("id")],
                    "updatedAt": now_iso(),
                },
            )

        log_entries.append(
            {
                "id": f"projection-{stable_hash(request.get('id', '') + now_iso())}",
                "sourceType": "change-request",
                "sourceId": request.get("id"),
                "chapterId": request.get("chapterId"),
                "kind": request.get("kind"),
                "createdAt": now_iso(),
            }
        )
        request["projectionStatus"] = "applied"
        request["projectionAppliedAt"] = now_iso()
        request["updatedAt"] = now_iso()
        applied_changes += 1

    proposals = state["proposals"].setdefault("draftProposals", [])
    for proposal in proposals:
        if proposal.get("status") != "applied":
            continue
        if proposal.get("projectionStatus") == "applied":
            continue
        if chapter_id and proposal.get("chapterId") not in {None, chapter_id}:
            continue
        log_entries.append(
            {
                "id": f"projection-{stable_hash(proposal.get('id', '') + now_iso())}",
                "sourceType": "draft-proposal",
                "sourceId": proposal.get("id"),
                "chapterId": proposal.get("chapterId"),
                "kind": proposal.get("kind"),
                "createdAt": now_iso(),
            }
        )
        proposal["projectionStatus"] = "applied"
        proposal["updatedAt"] = now_iso()

    active_entity_ids = analysis.get("sceneScope", {}).get("activeEntityIds", [])
    if chapter_id and active_entity_ids:
        upsert_by_key(
            projection.setdefault("sceneScopeProjections", []),
            ["chapterId"],
            {
                "chapterId": chapter_id,
                "activeEntityIds": active_entity_ids,
                "sourceChangeIds": [
                    request.get("id")
                    for request in requests
                    if request.get("chapterId") == chapter_id and request.get("status") == "accepted"
                ],
                "updatedAt": now_iso(),
            },
        )

    if consistency_result and chapter_id:
        applied_premise_facts = _apply_setting_candidates_to_worldbook(
            state,
            consistency_result,
            chapter_id,
            log_entries,
        )

    return {
        "appliedChangeRequests": applied_changes,
        "appliedPremiseFacts": applied_premise_facts,
        "chapterId": chapter_id,
    }


def _apply_setting_candidates_to_worldbook(
    state: Dict[str, Dict[str, Any]],
    consistency_result: Dict[str, Any],
    chapter_id: str,
    log_entries: List[Dict[str, Any]],
) -> int:
    candidates = consistency_result.get("settingCandidates", [])
    conflicts = consistency_result.get("settingConflicts", [])
    conflict_labels = {
        item.get("label")
        for item in conflicts
        if isinstance(item, dict) and item.get("label")
    }
    premise_facts = state.setdefault("worldbook", {}).setdefault("premiseFacts", [])
    applied = 0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        label = candidate.get("label", "")
        fact = candidate.get("fact", "")
        confidence = float(candidate.get("confidence", 0))
        if not label or not fact:
            continue
        if label in conflict_labels or confidence < 0.75:
            continue

        existing = next((item for item in premise_facts if item.get("label") == label), None)
        if existing and existing.get("fact") == fact:
            continue

        now = now_iso()
        upsert_by_key(
            premise_facts,
            ["label"],
            {
                "id": (existing or {}).get("id") or f"wf-{stable_hash(label)}",
                "label": label,
                "fact": fact,
                "sourceChapterId": chapter_id,
                "confidence": confidence,
                "updatedAt": now,
                "createdAt": (existing or {}).get("createdAt", now),
            },
        )
        log_entries.append(
            {
                "id": f"projection-{stable_hash(label + fact + now)}",
                "sourceType": "setting-candidate",
                "sourceId": label,
                "chapterId": chapter_id,
                "kind": "premise-fact",
                "createdAt": now,
            }
        )
        applied += 1
    return applied
