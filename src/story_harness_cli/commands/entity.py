from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.commands.export import write_volume_review_packet_for_chapter
from story_harness_cli.protocol import chapter_path, ensure_project_root, load_project_state, save_state
from story_harness_cli.protocol.keywords import load_keywords
from story_harness_cli.commands.review_support import (
    build_mention_check_payload as shared_build_mention_check_payload,
    build_mention_plan_payload as shared_build_mention_plan_payload,
    build_volume_mention_plan_payload as shared_build_volume_mention_plan_payload,
    find_volume as shared_find_volume,
)
from story_harness_cli.services.analyzer import chapter_title, resolve_named_reference
from story_harness_cli.services.entity_enricher import enrich_entities
from story_harness_cli.services.reference_mentions import (
    build_reference_catalog as svc_build_reference_catalog,
    collect_tag_replacements as svc_collect_tag_replacements,
)
from story_harness_cli.utils import now_iso, stable_hash
from story_harness_cli.utils.text import extract_tag_mentions, find_malformed_entity_tags, set_keywords


def _normalize_strings(values: list[str]) -> list[str]:
    items: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if normalized and normalized not in items:
            items.append(normalized)
    return items


def _entity_id(name: str, explicit_id: str | None) -> str:
    if explicit_id:
        return explicit_id
    return f"entity-{stable_hash(f'{name}:{now_iso()}')}"


def _compact_entity(entity: dict) -> dict:
    state_info = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
    current_state = entity.get("currentState", {}) if isinstance(entity.get("currentState"), dict) else {}
    return {
        "id": entity.get("id", ""),
        "name": entity.get("name", ""),
        "type": entity.get("type", "character"),
        "source": entity.get("source", ""),
        "aliases": [alias for alias in entity.get("aliases", []) if isinstance(alias, str)],
        "summary": entity.get("summary", ""),
        "statusTags": [tag for tag in state_info.get("statusTags", []) if isinstance(tag, str)],
        "location": current_state.get("location", ""),
        "lastUpdatedChapter": current_state.get("lastUpdatedChapter"),
    }


def _find_entity(entities: list[dict], entity_id: str, name: str) -> dict | None:
    normalized_name = str(name or "").strip()
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        if entity_id and entity.get("id") == entity_id:
            return entity
        aliases = [alias for alias in entity.get("aliases", []) if isinstance(alias, str)]
        if normalized_name and (entity.get("name") == normalized_name or normalized_name in aliases):
            return entity
    return None


def _build_entity_payload(
    *,
    existing: dict | None,
    explicit_id: str | None,
    name: str,
    entity_type: str,
    source: str,
    summary: str,
    aliases: list[str],
    archetype: str,
    personality: str,
    motivation: str,
    background: str,
    status: str,
    location: str,
    status_tags: list[str],
    physical_state: list[str],
    emotional_state: list[str],
    power_public: str,
    power_true: str,
    chapter_id: str | None,
    timestamp: str,
) -> dict:
    return {
        "id": _entity_id(name, explicit_id),
        "name": name,
        "type": entity_type,
        "source": source,
        "aliases": aliases,
        "summary": summary,
        "seed": {
            "archetype": archetype,
            "personality": personality,
            "motivation": motivation,
            "background": background,
        },
        "profile": {
            "appearance": [],
            "abilities": [],
            "speech": [],
            "relationships": [],
        },
        "state": {
            "statusTags": status_tags,
            "powerLevel": {
                "publicLevel": power_public,
                "trueLevel": power_true,
            },
            "injuries": [],
        },
        "currentState": {
            "status": status,
            "physicalState": physical_state,
            "emotionalState": emotional_state,
            "location": location,
            "lastUpdatedChapter": chapter_id,
            "powerLevel": power_public,
        },
        "changeLog": list(existing.get("changeLog", [])) if isinstance(existing, dict) else [],
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }


def command_entity_add(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    entities = state.setdefault("entities", {}).setdefault("entities", [])
    if not isinstance(entities, list):
        raise SystemExit("entities.entities 必须是列表")

    name = str(args.name or "").strip()
    if not name:
        raise SystemExit("缺少实体名称")
    aliases = _normalize_strings(args.alias or [])
    status_tags = _normalize_strings(args.status_tag or [])
    physical_state = _normalize_strings(args.physical_state or [])
    emotional_state = _normalize_strings(args.emotional_state or [])
    current_location = str(args.location or "").strip()

    existing = _find_entity(entities, args.id or "", name)
    if existing and not args.upsert:
        raise SystemExit(f"实体已存在，请改用 --upsert 或更换名称/ID: {name}")

    timestamp = now_iso()
    payload = _build_entity_payload(
        existing=existing,
        explicit_id=args.id,
        name=name,
        entity_type=str(args.type or "character").strip() or "character",
        source=str(args.source or "manual").strip() or "manual",
        summary=str(args.summary or "").strip(),
        aliases=aliases,
        archetype=str(args.archetype or "").strip(),
        personality=str(args.personality or "").strip(),
        motivation=str(args.motivation or "").strip(),
        background=str(args.background or "").strip(),
        status=str(args.status or "").strip(),
        location=current_location,
        status_tags=status_tags,
        physical_state=physical_state,
        emotional_state=emotional_state,
        power_public=str(args.power_public or "").strip(),
        power_true=str(args.power_true or "").strip(),
        chapter_id=args.chapter_id or None,
        timestamp=timestamp,
    )

    if existing:
        original_created_at = existing.get("createdAt", "")
        original_change_log = existing.get("changeLog", []) if isinstance(existing.get("changeLog"), list) else []
        existing.clear()
        existing.update(payload)
        if original_created_at:
            existing["createdAt"] = original_created_at
        existing["changeLog"] = original_change_log
        action = "updated"
        entity = existing
    else:
        entities.append(payload)
        action = "created"
        entity = payload

    state.setdefault("project", {})["updatedAt"] = timestamp
    save_state(root, state)
    print(json.dumps({"action": action, "entity": _compact_entity(entity)}, ensure_ascii=False, indent=2))
    return 0


def command_entity_mention_adopt(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    name = str(args.name or "").strip()
    if not name:
        raise SystemExit("缺少实体名称")
    chapter_text = chapter_file.read_text(encoding="utf-8")
    tagged_mentions = extract_tag_mentions(chapter_text)
    if name not in tagged_mentions:
        if not args.allow_plain or name not in chapter_text:
            raise SystemExit(f"章节 {chapter_id} 中未找到可采纳的 mention: {name}")

    entities = state.setdefault("entities", {}).setdefault("entities", [])
    if not isinstance(entities, list):
        raise SystemExit("entities.entities 必须是列表")
    existing = _find_entity(entities, args.id or "", name)
    if existing and not args.upsert:
        raise SystemExit(f"实体已存在，请改用 --upsert 或更换名称/ID: {name}")
    if resolve_named_reference(state, name) and not existing:
        raise SystemExit(f"名称已在其他真相层建档，请先确认是否应继续作为 entity 建档: {name}")

    aliases = _normalize_strings(args.alias or [])
    timestamp = now_iso()
    payload = _build_entity_payload(
        existing=existing,
        explicit_id=args.id,
        name=name,
        entity_type=str(args.type or "character").strip() or "character",
        source=str(args.source or ("tagged-mention" if name in tagged_mentions else "plain-mention")).strip(),
        summary=str(args.summary or "").strip(),
        aliases=aliases,
        archetype=str(args.archetype or "").strip(),
        personality=str(args.personality or "").strip(),
        motivation=str(args.motivation or "").strip(),
        background=str(args.background or "").strip(),
        status=str(args.status or "").strip(),
        location=str(args.location or "").strip(),
        status_tags=_normalize_strings(args.status_tag or []),
        physical_state=_normalize_strings(args.physical_state or []),
        emotional_state=_normalize_strings(args.emotional_state or []),
        power_public=str(args.power_public or "").strip(),
        power_true=str(args.power_true or "").strip(),
        chapter_id=chapter_id,
        timestamp=timestamp,
    )

    if existing:
        original_created_at = existing.get("createdAt", "")
        original_change_log = existing.get("changeLog", []) if isinstance(existing.get("changeLog"), list) else []
        existing.clear()
        existing.update(payload)
        if original_created_at:
            existing["createdAt"] = original_created_at
        existing["changeLog"] = original_change_log
        action = "updated"
        entity = existing
    else:
        entities.append(payload)
        action = "created"
        entity = payload

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
                "reviewPacketFile": review_packet_file,
                "reviewPacketRefreshed": review_packet_refreshed,
                "reviewPacketRefreshError": review_packet_refresh_error,
                "entity": _compact_entity(entity),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_entity_mention_tag_apply(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")
    chapter_text = chapter_file.read_text(encoding="utf-8")
    catalog = svc_build_reference_catalog(state)

    target_name = str(args.name or "").strip()
    replacements = svc_collect_tag_replacements(
        chapter_text,
        catalog,
        target_name=target_name,
    )
    if target_name and not replacements:
        raise SystemExit(f"当前章中未找到可修正的 plain mention: {target_name}")
    if not target_name and not args.all_known_unwrapped:
        raise SystemExit("批量修正需显式传入 --all-known-unwrapped，或使用 --name 定向修正")
    if not replacements:
        post_apply_check = _build_mention_post_apply_check(state, chapter_id, chapter_text, [])
        print(
            json.dumps(
                {
                    "chapterId": chapter_id,
                    "updated": False,
                    "replacementCount": 0,
                    "reviewPacketFile": "",
                    "reviewPacketRefreshed": False,
                    "reviewPacketRefreshError": "",
                    "postApplyCheck": post_apply_check,
                    "replacements": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    updated_text = _apply_tag_replacements(chapter_text, replacements)
    post_apply_check = _build_mention_post_apply_check(state, chapter_id, updated_text, replacements)
    _ensure_mention_post_apply_safe(post_apply_check)
    if updated_text != chapter_text:
        chapter_file.write_text(updated_text, encoding="utf-8")
    review_packet_file = ""
    review_packet_refreshed = False
    review_packet_refresh_error = ""
    if updated_text != chapter_text:
        try:
            packet_path = write_volume_review_packet_for_chapter(root, state, chapter_id)
            if packet_path is not None:
                review_packet_file = str(packet_path)
                review_packet_refreshed = True
        except OSError as exc:
            review_packet_refresh_error = str(exc)

    payload = {
        "chapterId": chapter_id,
        "updated": updated_text != chapter_text,
        "replacementCount": len(replacements),
        "reviewPacketFile": review_packet_file,
        "reviewPacketRefreshed": review_packet_refreshed,
        "reviewPacketRefreshError": review_packet_refresh_error,
        "postApplyCheck": post_apply_check,
        "replacements": [
            {
                "name": item["canonicalName"],
                "matchedName": item["matchedName"],
                "kind": item["kind"],
                "source": item["source"],
                "replacement": item["replacement"],
            }
            for item in replacements
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_entity_state_update(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    entities = state.setdefault("entities", {}).setdefault("entities", [])
    if not isinstance(entities, list):
        raise SystemExit("entities.entities 必须是列表")

    entity = _find_entity(entities, args.entity_id or "", args.name or "")
    if not entity:
        raise SystemExit("找不到实体")

    state_info = entity.setdefault("state", {})
    if not isinstance(state_info, dict):
        entity["state"] = {}
        state_info = entity["state"]
    current_state = entity.setdefault("currentState", {})
    if not isinstance(current_state, dict):
        entity["currentState"] = {}
        current_state = entity["currentState"]
    change_log = entity.setdefault("changeLog", [])
    if not isinstance(change_log, list):
        entity["changeLog"] = []
        change_log = entity["changeLog"]

    timestamp = now_iso()
    chapter_id = args.chapter_id or current_state.get("lastUpdatedChapter")
    reason = str(args.reason or "").strip()
    entity_id = str(entity.get("id", ""))

    if args.status_tag:
        state_info["statusTags"] = _normalize_strings(args.status_tag)
        change_log.append(
            {
                "id": f"chg-{stable_hash(f'{entity_id}:statusTags:{timestamp}')}",
                "chapterId": chapter_id,
                "field": "state.statusTags",
                "reason": reason or "更新状态标签",
            }
        )
    if args.status is not None:
        current_state["status"] = str(args.status).strip()
        change_log.append(
            {
                "id": f"chg-{stable_hash(f'{entity_id}:status:{timestamp}')}",
                "chapterId": chapter_id,
                "field": "currentState.status",
                "reason": reason or "更新当前状态",
            }
        )
    if args.location is not None:
        current_state["location"] = str(args.location).strip()
        change_log.append(
            {
                "id": f"chg-{stable_hash(f'{entity_id}:location:{timestamp}')}",
                "chapterId": chapter_id,
                "field": "currentState.location",
                "reason": reason or "更新所在位置",
            }
        )
    if args.physical_state:
        current_state["physicalState"] = _normalize_strings(args.physical_state)
        change_log.append(
            {
                "id": f"chg-{stable_hash(f'{entity_id}:physical:{timestamp}')}",
                "chapterId": chapter_id,
                "field": "currentState.physicalState",
                "reason": reason or "更新身体状态",
            }
        )
    if args.emotional_state:
        current_state["emotionalState"] = _normalize_strings(args.emotional_state)
        change_log.append(
            {
                "id": f"chg-{stable_hash(f'{entity_id}:emotional:{timestamp}')}",
                "chapterId": chapter_id,
                "field": "currentState.emotionalState",
                "reason": reason or "更新情绪状态",
            }
        )
    if args.power_public is not None or args.power_true is not None:
        power_level = state_info.setdefault("powerLevel", {})
        if not isinstance(power_level, dict):
            state_info["powerLevel"] = {}
            power_level = state_info["powerLevel"]
        if args.power_public is not None:
            power_level["publicLevel"] = str(args.power_public).strip()
            current_state["powerLevel"] = str(args.power_public).strip()
        if args.power_true is not None:
            power_level["trueLevel"] = str(args.power_true).strip()
        change_log.append(
            {
                "id": f"chg-{stable_hash(f'{entity_id}:power:{timestamp}')}",
                "chapterId": chapter_id,
                "field": "state.powerLevel",
                "reason": reason or "更新战力阶段",
            }
        )

    current_state["lastUpdatedChapter"] = chapter_id
    entity["updatedAt"] = timestamp
    state.setdefault("project", {})["updatedAt"] = timestamp
    save_state(root, state)
    print(json.dumps({"action": "updated", "entity": _compact_entity(entity)}, ensure_ascii=False, indent=2))
    return 0


def command_entity_enrich(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    set_keywords(load_keywords(root))
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    result = enrich_entities(state, chapter_id, root=root)
    save_state(root, state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_entity_review(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    proposals = state["entities"].setdefault("enrichmentProposals", [])
    decision = args.decision
    changed = 0

    for proposal in proposals:
        if proposal.get("status") != "pending":
            continue
        if not args.all_pending and (not args.proposal_id or proposal.get("id") not in args.proposal_id):
            continue
        proposal["status"] = decision
        proposal["updatedAt"] = now_iso()
        changed += 1

        if decision == "accepted":
            entity_id = proposal.get("entityId")
            field = proposal.get("field")
            detail = proposal.get("detail", "")
            evidence = proposal.get("evidence", "")
            chapter_id = proposal.get("chapterId", "")

            for entity in state["entities"].get("entities", []):
                if entity.get("id") == entity_id:
                    profile = entity.setdefault("profile", {})
                    field_list = profile.setdefault(field, [])
                    entry = {"detail": detail, "source": chapter_id, "evidence": evidence, "confidence": proposal.get("confidence", 0.8)}
                    field_list.append(entry)
                    break

    save_state(root, state)
    print(json.dumps({"updated": changed, "decision": decision}, ensure_ascii=False, indent=2))
    return 0


def command_entity_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    entities = state.get("entities", {}).get("entities", [])

    summaries = []
    for entity in entities:
        if args.type and entity.get("type", "character") != args.type:
            continue
        if args.source and entity.get("source") != args.source:
            continue
        seed = entity.get("seed")
        archetype = seed.get("archetype") if isinstance(seed, dict) else None
        summaries.append({
            "id": entity.get("id"),
            "name": entity.get("name"),
            "source": entity.get("source"),
            "seed": seed if not isinstance(seed, dict) else True,
            "archetype": archetype,
            "status": entity.get("currentState", {}).get("status") if isinstance(entity.get("currentState"), dict) else None,
            "lastChapter": entity.get("currentState", {}).get("lastUpdatedChapter") if isinstance(entity.get("currentState"), dict) else None,
        })

    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


def command_entity_show(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    entity_id = getattr(args, "entity_id", None)
    name = getattr(args, "name", None)
    if not entity_id and not name:
        raise SystemExit("必须指定 --entity-id 或 --name")

    entities = state.get("entities", {}).get("entities", [])
    entity = None
    for e in entities:
        if entity_id and e.get("id") == entity_id:
            entity = e
            break
        if name and e.get("name") == name:
            entity = e
            break

    if entity is None:
        raise SystemExit("找不到实体")

    result = {
        "id": entity.get("id"),
        "name": entity.get("name"),
        "type": entity.get("type", "character"),
        "source": entity.get("source"),
        "aliases": entity.get("aliases", []),
        "seed": entity.get("seed", {}),
        "profile": entity.get("profile", {}),
        "currentState": entity.get("currentState", {}),
    }

    # latestProjection
    projections = state.get("projection", {}).get("snapshotProjections", [])
    latest = None
    for proj in projections:
        if proj.get("entityId") == result["id"]:
            latest = proj
    if latest is not None:
        result["latestProjection"] = {
            "scopeRef": latest.get("scopeRef"),
            "state": latest.get("currentState"),
        }
    else:
        result["latestProjection"] = None

    # relations
    relation_projections = state.get("projection", {}).get("relationProjections", [])
    relations = []
    for rel in relation_projections:
        if rel.get("fromId") == result["id"] or rel.get("toId") == result["id"]:
            other_id = rel.get("toId") if rel.get("fromId") == result["id"] else rel.get("fromId")
            other_name = None
            for e in entities:
                if e.get("id") == other_id:
                    other_name = e.get("name")
                    break
            relations.append({
                "withName": other_name,
                "label": rel.get("label"),
                "scopeRef": rel.get("scopeRef"),
            })
    result["relations"] = relations

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_entity_graph(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    fmt = args.format
    chapter_id = getattr(args, "chapter_id", None)

    relation_projections = state.get("projection", {}).get("relationProjections", [])
    entities = state.get("entities", {}).get("entities", [])

    if chapter_id:
        relations = [r for r in relation_projections if r.get("scopeRef") == chapter_id]
    else:
        # Deduplicate: keep latest label per pair
        seen = {}
        for r in sorted(relation_projections, key=lambda x: x.get("updatedAt", "")):
            key = (r.get("fromId"), r.get("toId"))
            seen[key] = r
        relations = list(seen.values())

    # Collect all entity names involved (including isolated nodes from entity list)
    name_map = {e.get("id"): e.get("name", e.get("id")) for e in entities}
    node_ids = set()
    for r in relations:
        node_ids.add(r.get("fromId"))
        node_ids.add(r.get("toId"))

    # Add isolated entity nodes when no chapter filter
    if not chapter_id:
        for e in entities:
            node_ids.add(e.get("id"))

    nodes = {}
    for nid in node_ids:
        nodes[nid] = name_map.get(nid, nid.replace("inferred::", ""))

    if fmt == "dot":
        output = _render_dot(nodes, relations)
    else:
        output = _render_mermaid(nodes, relations)

    print(output)
    return 0


def _resolve_chapter_id(args, state: dict) -> str:
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    return chapter_id


def _find_volume(state: dict, volume_id: str | None) -> dict | None:
    return shared_find_volume(state, volume_id)


def _apply_tag_replacements(text: str, replacements: list[dict]) -> str:
    if not replacements:
        return text
    chunks: list[str] = []
    cursor = 0
    for item in sorted(replacements, key=lambda match: match["start"]):
        start = item["start"]
        end = item["end"]
        chunks.append(text[cursor:start])
        chunks.append(item["replacement"])
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks)


def _reference_key_from_replacement(item: dict) -> tuple[str, str]:
    return (
        str(item.get("source", "")),
        str(item.get("id", "") or item.get("canonicalName", "")),
    )


def _reference_key_from_action(item: dict) -> tuple[str, str]:
    return (
        str(item.get("source", "")),
        str(item.get("referenceId", "") or item.get("name", "")),
    )


def _build_mention_post_apply_check(state: dict, chapter_id: str, chapter_text: str, replacements: list[dict]) -> dict:
    malformed_tags = find_malformed_entity_tags(chapter_text)
    mention_plan = _build_mention_plan_payload(state, chapter_id, chapter_text)
    touched_keys = {_reference_key_from_replacement(item) for item in replacements}
    remaining_touched_actions = [
        {
            "actionId": item.get("actionId", ""),
            "name": item.get("name", ""),
            "source": item.get("source", ""),
            "occurrenceCount": item.get("occurrenceCount", 0),
        }
        for item in mention_plan.get("knownUnwrappedActions", [])
        if _reference_key_from_action(item) in touched_keys
    ]
    needs_manual_review = bool(malformed_tags or remaining_touched_actions)
    reasons: list[str] = []
    if malformed_tags:
        reasons.append("修补结果包含非法 @{...} 标签")
    if remaining_touched_actions:
        reasons.append("本次触达的引用仍有未包裹 plain mention")
    return {
        "valid": not needs_manual_review,
        "needsManualReview": needs_manual_review,
        "manualReviewReasons": reasons,
        "malformedTagCount": len(malformed_tags),
        "malformedTags": malformed_tags[:5],
        "remainingKnownUnwrappedActionCount": mention_plan.get("summary", {}).get("knownUnwrappedActionCount", 0),
        "remainingTaggedMissingActionCount": mention_plan.get("summary", {}).get("taggedMissingActionCount", 0),
        "remainingTotalActionCount": mention_plan.get("summary", {}).get("totalActionCount", 0),
        "remainingTouchedKnownUnwrappedActions": remaining_touched_actions,
    }


def _ensure_mention_post_apply_safe(post_apply_check: dict) -> None:
    if int(post_apply_check.get("malformedTagCount", 0)) > 0:
        raise SystemExit("mention 修补结果包含非法 @{...} 标签，已拒绝写入")


def _build_mention_check_payload(state: dict, chapter_id: str, chapter_text: str) -> dict:
    return shared_build_mention_check_payload(state, chapter_id, chapter_text)


def _build_mention_plan_payload(state: dict, chapter_id: str, chapter_text: str) -> dict:
    return shared_build_mention_plan_payload(state, chapter_id, chapter_text)


def _build_volume_mention_plan_payload(state: dict, root: Path, volume: dict) -> dict:
    return shared_build_volume_mention_plan_payload(state, root, volume)


def command_entity_mention_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    chapter_text = chapter_file.read_text(encoding="utf-8")
    payload = _build_mention_check_payload(state, chapter_id, chapter_text)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_entity_mention_plan(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    if args.chapter_id and args.volume_id:
        raise SystemExit("`--chapter-id` 与 `--volume-id` 不能同时使用")

    volume = _find_volume(state, args.volume_id) if getattr(args, "volume_id", None) else None
    if volume is not None:
        payload = _build_volume_mention_plan_payload(state, root, volume)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    chapter_id = _resolve_chapter_id(args, state)

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    chapter_text = chapter_file.read_text(encoding="utf-8")
    payload = _build_mention_plan_payload(state, chapter_id, chapter_text)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_entity_mention_apply(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    chapter_text = chapter_file.read_text(encoding="utf-8")
    plan = _build_mention_plan_payload(state, chapter_id, chapter_text)
    tag_actions = {item["actionId"]: item for item in plan["knownUnwrappedActions"]}
    adopt_actions = {item["actionId"]: item for item in plan["taggedMissingActions"]}

    selected_action_ids = list(dict.fromkeys(args.action_id or []))
    if args.all_known_unwrapped:
        selected_actions = list(tag_actions.values())
    else:
        if not selected_action_ids:
            raise SystemExit("缺少 action id；请先运行 entity mention-plan，或显式传 --all-known-unwrapped")
        unknown_action_ids = [action_id for action_id in selected_action_ids if action_id not in tag_actions and action_id not in adopt_actions]
        if unknown_action_ids:
            raise SystemExit(f"未找到这些 action id: {', '.join(unknown_action_ids)}")
        adopt_only_action_ids = [action_id for action_id in selected_action_ids if action_id in adopt_actions]
        if adopt_only_action_ids:
            raise SystemExit(
                "这些 action 需要显式建档，不能由 mention-apply 直接执行: "
                + ", ".join(adopt_only_action_ids)
                + "；请改用 entity mention-adopt 或 world mention-adopt"
            )
        selected_actions = [tag_actions[action_id] for action_id in selected_action_ids]

    if not selected_actions:
        post_apply_check = _build_mention_post_apply_check(state, chapter_id, chapter_text, [])
        print(
            json.dumps(
                {
                    "chapterId": chapter_id,
                    "updated": False,
                    "appliedActionCount": 0,
                    "replacementCount": 0,
                    "postApplyCheck": post_apply_check,
                    "appliedActions": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    catalog = svc_build_reference_catalog(state)
    available_replacements = svc_collect_tag_replacements(chapter_text, catalog)
    replacements: list[dict] = []
    seen_ranges: set[tuple[int, int, str]] = set()
    for action in selected_actions:
        for item in available_replacements:
            replacement_key = (item["start"], item["end"], item["replacement"])
            if replacement_key in seen_ranges:
                continue
            if item.get("source", "") != action.get("source", ""):
                continue
            item_reference_id = item.get("id", "") or item.get("canonicalName", "")
            action_reference_id = action.get("referenceId", "") or action.get("name", "")
            if item_reference_id != action_reference_id:
                continue
            replacements.append(item)
            seen_ranges.add(replacement_key)

    if not replacements:
        post_apply_check = _build_mention_post_apply_check(state, chapter_id, chapter_text, [])
        print(
            json.dumps(
                {
                    "chapterId": chapter_id,
                    "updated": False,
                    "appliedActionCount": len(selected_actions),
                    "replacementCount": 0,
                    "reviewPacketFile": "",
                    "reviewPacketRefreshed": False,
                    "reviewPacketRefreshError": "",
                    "postApplyCheck": post_apply_check,
                    "appliedActions": selected_actions,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    updated_text = _apply_tag_replacements(chapter_text, replacements)
    post_apply_check = _build_mention_post_apply_check(state, chapter_id, updated_text, replacements)
    _ensure_mention_post_apply_safe(post_apply_check)
    if updated_text != chapter_text:
        chapter_file.write_text(updated_text, encoding="utf-8")
    review_packet_file = ""
    review_packet_refreshed = False
    review_packet_refresh_error = ""
    if updated_text != chapter_text:
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
                "chapterId": chapter_id,
                "updated": updated_text != chapter_text,
                "appliedActionCount": len(selected_actions),
                "replacementCount": len(replacements),
                "reviewPacketFile": review_packet_file,
                "reviewPacketRefreshed": review_packet_refreshed,
                "reviewPacketRefreshError": review_packet_refresh_error,
                "postApplyCheck": post_apply_check,
                "appliedActions": selected_actions,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _render_mermaid(nodes: dict, relations: list) -> str:
    lines = ["graph LR"]
    for r in relations:
        from_name = nodes.get(r.get("fromId"), r.get("fromId", "?"))
        to_name = nodes.get(r.get("toId"), r.get("toId", "?"))
        label = r.get("label", "")
        # Mermaid-safe: replace spaces and special chars
        safe_from = _mermaid_id(from_name)
        safe_to = _mermaid_id(to_name)
        lines.append(f"  {safe_from}[\"{from_name}\"] -->|\"{label}\"| {safe_to}[\"{to_name}\"]")

    # Isolated nodes
    linked_ids = set()
    for r in relations:
        linked_ids.add(r.get("fromId"))
        linked_ids.add(r.get("toId"))
    for nid, name in nodes.items():
        if nid not in linked_ids:
            safe = _mermaid_id(name)
            lines.append(f"  {safe}[\"{name}\"]")

    return "\n".join(lines)


def _render_dot(nodes: dict, relations: list) -> str:
    lines = ["digraph relations {"]
    for r in relations:
        from_name = nodes.get(r.get("fromId"), r.get("fromId", "?"))
        to_name = nodes.get(r.get("toId"), r.get("toId", "?"))
        label = r.get("label", "")
        lines.append(f'  "{from_name}" -> "{to_name}" [label="{label}"];')
    lines.append("}")
    return "\n".join(lines)


def _mermaid_id(name: str) -> str:
    """Create a Mermaid-safe node ID."""
    import re
    return re.sub(r'[^\w]', '_', name)


def register_entity_commands(subparsers) -> None:
    entity_parser = subparsers.add_parser("entity", help="Entity and character card commands")
    entity_sub = entity_parser.add_subparsers(dest="entity_command", required=True)

    add_parser = entity_sub.add_parser("add", help="Create or upsert an entity card")
    add_parser.add_argument("--root", required=True)
    add_parser.add_argument("--id")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--type", default="character")
    add_parser.add_argument("--source", default="manual")
    add_parser.add_argument("--summary", default="")
    add_parser.add_argument("--alias", action="append", default=[])
    add_parser.add_argument("--archetype", default="")
    add_parser.add_argument("--personality", default="")
    add_parser.add_argument("--motivation", default="")
    add_parser.add_argument("--background", default="")
    add_parser.add_argument("--status", default="")
    add_parser.add_argument("--location", default="")
    add_parser.add_argument("--status-tag", action="append", default=[])
    add_parser.add_argument("--physical-state", action="append", default=[])
    add_parser.add_argument("--emotional-state", action="append", default=[])
    add_parser.add_argument("--power-public", default="")
    add_parser.add_argument("--power-true", default="")
    add_parser.add_argument("--chapter-id")
    add_parser.add_argument("--upsert", action="store_true")
    add_parser.set_defaults(func=command_entity_add)

    state_update_parser = entity_sub.add_parser("state-update", help="Update entity state and append change log")
    state_update_parser.add_argument("--root", required=True)
    state_update_parser.add_argument("--entity-id", dest="entity_id")
    state_update_parser.add_argument("--name")
    state_update_parser.add_argument("--chapter-id")
    state_update_parser.add_argument("--reason", default="")
    state_update_parser.add_argument("--status")
    state_update_parser.add_argument("--location")
    state_update_parser.add_argument("--status-tag", action="append", default=[])
    state_update_parser.add_argument("--physical-state", action="append", default=[])
    state_update_parser.add_argument("--emotional-state", action="append", default=[])
    state_update_parser.add_argument("--power-public")
    state_update_parser.add_argument("--power-true")
    state_update_parser.set_defaults(func=command_entity_state_update)

    enrich_parser = entity_sub.add_parser("enrich", help="Extract character details from chapter")
    enrich_parser.add_argument("--root", required=True)
    enrich_parser.add_argument("--chapter-id")
    enrich_parser.set_defaults(func=command_entity_enrich)

    review_parser = entity_sub.add_parser("review", help="Review enrichment proposals")
    review_parser.add_argument("--root", required=True)
    review_parser.add_argument("--decision", required=True, choices=["accepted", "ignored"])
    review_parser.add_argument("--proposal-id", action="append")
    review_parser.add_argument("--all-pending", action="store_true")
    review_parser.set_defaults(func=command_entity_review)

    list_parser = entity_sub.add_parser("list", help="List entity summaries")
    list_parser.add_argument("--root", required=True)
    list_parser.add_argument("--type", choices=["character", "location", "item"], help="Filter by entity type")
    list_parser.add_argument("--source", choices=["seed", "inferred"], help="Filter by entity source")
    list_parser.set_defaults(func=command_entity_list)

    show_parser = entity_sub.add_parser("show", help="Show full entity card")
    show_parser.add_argument("--root", required=True)
    show_parser.add_argument("--entity-id", dest="entity_id")
    show_parser.add_argument("--name")
    show_parser.set_defaults(func=command_entity_show)

    graph_parser = entity_sub.add_parser("graph", help="Export relationship graph")
    graph_parser.add_argument("--root", required=True)
    graph_parser.add_argument("--chapter-id", help="Filter relations by chapter")
    graph_parser.add_argument("--format", choices=["mermaid", "dot"], default="mermaid", help="Graph format")
    graph_parser.set_defaults(func=command_entity_graph)

    mention_check_parser = entity_sub.add_parser(
        "mention-check",
        help="Inspect one chapter for wrapped entity coverage, unwrapped known mentions, and missing registry entries",
    )
    mention_check_parser.add_argument("--root", required=True)
    mention_check_parser.add_argument("--chapter-id")
    mention_check_parser.set_defaults(func=command_entity_mention_check)

    mention_plan_parser = entity_sub.add_parser(
        "mention-plan",
        help="Preview deterministic tag actions and explicit adopt candidates for one chapter",
    )
    mention_plan_parser.add_argument("--root", required=True)
    mention_plan_parser.add_argument("--chapter-id")
    mention_plan_parser.add_argument("--volume-id")
    mention_plan_parser.set_defaults(func=command_entity_mention_plan)

    mention_adopt_parser = entity_sub.add_parser(
        "mention-adopt",
        help="Adopt one mention from a chapter into entities after explicit confirmation",
    )
    mention_adopt_parser.add_argument("--root", required=True)
    mention_adopt_parser.add_argument("--chapter-id")
    mention_adopt_parser.add_argument("--id")
    mention_adopt_parser.add_argument("--name", required=True)
    mention_adopt_parser.add_argument("--type", default="character")
    mention_adopt_parser.add_argument("--source", default="")
    mention_adopt_parser.add_argument("--summary", default="")
    mention_adopt_parser.add_argument("--alias", action="append", default=[])
    mention_adopt_parser.add_argument("--archetype", default="")
    mention_adopt_parser.add_argument("--personality", default="")
    mention_adopt_parser.add_argument("--motivation", default="")
    mention_adopt_parser.add_argument("--background", default="")
    mention_adopt_parser.add_argument("--status", default="")
    mention_adopt_parser.add_argument("--location", default="")
    mention_adopt_parser.add_argument("--status-tag", action="append", default=[])
    mention_adopt_parser.add_argument("--physical-state", action="append", default=[])
    mention_adopt_parser.add_argument("--emotional-state", action="append", default=[])
    mention_adopt_parser.add_argument("--power-public", default="")
    mention_adopt_parser.add_argument("--power-true", default="")
    mention_adopt_parser.add_argument("--allow-plain", action="store_true")
    mention_adopt_parser.add_argument("--upsert", action="store_true")
    mention_adopt_parser.set_defaults(func=command_entity_mention_adopt)

    mention_tag_apply_parser = entity_sub.add_parser(
        "mention-tag-apply",
        help="Wrap known unwrapped mentions in one chapter with canonical @{...} tags",
    )
    mention_tag_apply_parser.add_argument("--root", required=True)
    mention_tag_apply_parser.add_argument("--chapter-id")
    mention_tag_apply_parser.add_argument("--name")
    mention_tag_apply_parser.add_argument("--all-known-unwrapped", action="store_true")
    mention_tag_apply_parser.set_defaults(func=command_entity_mention_tag_apply)

    mention_apply_parser = entity_sub.add_parser(
        "mention-apply",
        help="Apply selected plan actions for known unwrapped mentions in one chapter",
    )
    mention_apply_parser.add_argument("--root", required=True)
    mention_apply_parser.add_argument("--chapter-id")
    mention_apply_parser.add_argument("--action-id", action="append", default=[])
    mention_apply_parser.add_argument("--all-known-unwrapped", action="store_true")
    mention_apply_parser.set_defaults(func=command_entity_mention_apply)
