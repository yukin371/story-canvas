from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from story_harness_cli.protocol import chapter_path
from story_harness_cli.protocol.io import dump_json_compatible_yaml
from story_harness_cli.utils import now_iso, stable_hash
from story_harness_cli.utils.text import (
    extract_tag_mentions,
    paragraphs_from_text,
    relation_for_paragraph,
    state_tags_for_paragraph,
)


def chapter_title(outline: Dict[str, Any], chapter_id: str) -> str:
    for chapter in outline.get("chapters", []):
        if chapter.get("id") == chapter_id:
            return str(chapter.get("title") or chapter_id)
    return chapter_id


def entity_registry(entities_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for entity in entities_state.get("entities", []):
        entity_id = str(entity.get("id") or "")
        name = str(entity.get("name") or "").strip()
        if not entity_id or not name:
            continue
        result[entity_id] = {
            "id": entity_id,
            "name": name,
            "type": entity.get("type") or "character",
            "aliases": [alias for alias in entity.get("aliases", []) if isinstance(alias, str)],
            "summary": entity.get("summary") or "",
            "currentState": entity.get("currentState") or "",
        }
    return result


def inferred_entities_from_tags(text: str) -> Dict[str, Dict[str, Any]]:
    found: Dict[str, Dict[str, Any]] = {}
    for name in sorted(extract_tag_mentions(text)):
        entity_id = f"inferred::{name}"
        found[entity_id] = {
            "id": entity_id,
            "name": name,
            "type": "character",
            "aliases": [],
            "summary": "",
            "currentState": "",
        }
    return found


def resolve_entities(text: str, entities_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    registry = entity_registry(entities_state)
    inferred = inferred_entities_from_tags(text)
    tag_mentions = set(extract_tag_mentions(text))
    resolved: Dict[str, Dict[str, Any]] = {}

    for entity_id, entity in registry.items():
        names = [entity["name"], *entity.get("aliases", [])]
        if any(name and (name in text or name in tag_mentions) for name in names):
            resolved[entity_id] = entity

    for entity_id, entity in inferred.items():
        if entity["name"] not in tag_mentions:
            continue
        existing = next(
            (
                item
                for item in resolved.values()
                if entity["name"] == item["name"] or entity["name"] in item.get("aliases", [])
            ),
            None,
        )
        if existing is None:
            resolved[entity_id] = entity

    return resolved


def resolve_named_reference(state: Dict[str, Dict[str, Any]], name: str) -> Dict[str, Any] | None:
    entities_state = state.get("entities", {})
    for entity in entities_state.get("entities", []):
        if not isinstance(entity, dict):
            continue
        aliases = [alias for alias in entity.get("aliases", []) if isinstance(alias, str)]
        if name == entity.get("name") or name in aliases:
            return {
                "name": name,
                "kind": entity.get("type", "character"),
                "id": entity.get("id", ""),
                "source": "entities",
            }

    worldbook = state.get("worldbook", {})
    for key, kind in (
        ("factions", "faction"),
        ("artifacts", "artifact"),
        ("locations", "location"),
        ("mysteries", "mystery"),
    ):
        for item in worldbook.get(key, []):
            if not isinstance(item, dict):
                continue
            candidate_names = [
                value for value in (item.get("name"), item.get("title"), item.get("label"))
                if isinstance(value, str) and value
            ]
            aliases = [alias for alias in item.get("aliases", []) if isinstance(alias, str)]
            if name in candidate_names or name in aliases:
                return {
                    "name": name,
                    "kind": kind,
                    "id": item.get("id", ""),
                    "source": f"worldbook.{key}",
                }
    return None


def analyze_chapter(root: Path, state: Dict[str, Dict[str, Any]], chapter_id: str) -> Dict[str, Any]:
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    text = chapter_file.read_text(encoding="utf-8")
    paragraphs = paragraphs_from_text(text)
    resolved_entities = resolve_entities(text, state["entities"])
    mention_map: Dict[str, int] = {entity_id: 0 for entity_id in resolved_entities}
    snapshot_candidates: List[Dict[str, Any]] = []
    relation_candidates: List[Dict[str, Any]] = []

    for paragraph in paragraphs:
        paragraph_tag_mentions = set(extract_tag_mentions(paragraph))
        paragraph_entities = [
            entity
            for entity in resolved_entities.values()
            if (
                entity["name"] in paragraph_tag_mentions
                or f"@{entity['name']}" in paragraph
                or f"@{entity['name']}" in paragraph.replace("@{", "@").replace("}", "")
                or (
                    not entity["id"].startswith("inferred::")
                    and entity["name"] in paragraph
                )
                or (
                    not entity["id"].startswith("inferred::")
                    and any(alias in paragraph or alias in paragraph_tag_mentions for alias in entity.get("aliases", []))
                )
            )
        ]
        for entity in paragraph_entities:
            mention_map[entity["id"]] = mention_map.get(entity["id"], 0) + 1
            tags = state_tags_for_paragraph(paragraph)
            if tags:
                proposed_state = "；".join(sorted(set(tags)))
                snapshot_candidates.append(
                    {
                        "candidateId": f"snapshot::{chapter_id}::{entity['id']}::{stable_hash(paragraph)}",
                        "entityId": entity["id"],
                        "entityName": entity["name"],
                        "proposedState": proposed_state,
                        "stateTags": sorted(set(tags)),
                        "evidence": paragraph,
                        "confidence": 0.92 if entity["name"] in paragraph_tag_mentions else 0.78,
                    }
                )

        if len(paragraph_entities) >= 2:
            relation_label, severity = relation_for_paragraph(paragraph)
            if relation_label:
                for idx, left in enumerate(paragraph_entities):
                    for right in paragraph_entities[idx + 1 :]:
                        relation_candidates.append(
                            {
                                "candidateId": f"relation::{chapter_id}::{left['id']}::{right['id']}::{stable_hash(paragraph)}",
                                "fromId": left["id"],
                                "fromName": left["name"],
                                "toId": right["id"],
                                "toName": right["name"],
                                "label": relation_label,
                                "severity": severity,
                                "evidence": paragraph,
                                "confidence": 0.84,
                            }
                        )

    active_entities = [
        {
            "id": entity["id"],
            "name": entity["name"],
            "mentionCount": mention_map.get(entity["id"], 0),
            "source": "registry" if not entity["id"].startswith("inferred::") else "inferred",
        }
        for entity in sorted(
            resolved_entities.values(),
            key=lambda item: (-mention_map.get(item["id"], 0), item["name"]),
        )
        if mention_map.get(entity["id"], 0) > 0
    ]

    analysis = {
        "chapterId": chapter_id,
        "chapterTitle": chapter_title(state["outline"], chapter_id),
        "analyzedAt": now_iso(),
        "activeEntities": active_entities,
        "snapshotCandidates": snapshot_candidates,
        "relationCandidates": relation_candidates,
        "sceneScope": {
            "activeEntityIds": [item["id"] for item in active_entities[:6]],
            "activeEntityNames": [item["name"] for item in active_entities[:6]],
        },
    }
    dump_json_compatible_yaml(root / "logs" / "latest-analysis.yaml", analysis)
    dump_json_compatible_yaml(root / "logs" / f"analysis-{chapter_id}.yaml", analysis)
    return analysis
