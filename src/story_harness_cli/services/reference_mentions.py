from __future__ import annotations

import re

from story_harness_cli.services.analyzer import resolve_named_reference
from story_harness_cli.utils.text import extract_tag_mentions

WORLD_KIND_HINT_SUFFIXES = {
    "faction": ("宗", "门", "派", "盟", "会", "朝", "国", "教", "殿", "阁", "司", "府", "军", "团"),
    "location": ("山", "谷", "岭", "峰", "原", "泽", "海", "河", "湖", "城", "镇", "村", "岛", "洲", "域", "集", "坊", "宫"),
    "artifact": ("灯", "剑", "刀", "印", "鼎", "符", "盘", "镜", "珠", "石", "图", "牌", "卷", "匣", "钟"),
    "mystery": ("案", "谜", "劫", "局", "咒"),
}
WORLD_KIND_HINT_MESSAGES = {
    "faction": "名称后缀更像势力或组织，可优先考虑 worldbook.factions。",
    "location": "名称后缀更像地点或区域，可优先考虑 worldbook.locations。",
    "artifact": "名称后缀更像器物或特殊物件，可优先考虑 worldbook.artifacts。",
    "mystery": "名称后缀更像谜团或事件，可优先考虑 worldbook.mysteries。",
}


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


def _tagged_occurrence_count(text: str, names: list[str]) -> int:
    count = 0
    tagged_mentions = extract_tag_mentions(text)
    for mention in tagged_mentions:
        if mention in names:
            count += 1
    return count


def build_reference_catalog(state: dict) -> list[dict]:
    catalog: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for entity in state.get("entities", {}).get("entities", []):
        if not isinstance(entity, dict):
            continue
        canonical_name = str(entity.get("name") or "").strip()
        if not canonical_name:
            continue
        names = [canonical_name]
        names.extend(alias for alias in entity.get("aliases", []) if isinstance(alias, str) and alias.strip())
        entry = {
            "id": entity.get("id", ""),
            "canonicalName": canonical_name,
            "names": names,
            "kind": entity.get("type", "character"),
            "source": "entities",
            "summary": entity.get("summary", ""),
            "aliases": [alias for alias in entity.get("aliases", []) if isinstance(alias, str)],
            "currentState": entity.get("currentState", {}),
        }
        key = (entry["source"], entry["id"])
        if key not in seen:
            catalog.append(entry)
            seen.add(key)

    for key, kind in (
        ("factions", "faction"),
        ("artifacts", "artifact"),
        ("locations", "location"),
        ("mysteries", "mystery"),
    ):
        for item in state.get("worldbook", {}).get(key, []):
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
            entry = {
                "id": item.get("id", ""),
                "canonicalName": canonical_name,
                "names": names,
                "kind": kind,
                "source": f"worldbook.{key}",
                "summary": item.get("summary") or item.get("description") or item.get("rule") or "",
                "aliases": [alias for alias in item.get("aliases", []) if isinstance(alias, str)],
                "currentState": {},
            }
            key_tuple = (entry["source"], entry["id"] or canonical_name)
            if key_tuple not in seen:
                catalog.append(entry)
                seen.add(key_tuple)
    return catalog


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


def _iter_unwrapped_matches(
    text: str,
    names: list[str],
    quote_ranges: list[tuple[int, int]],
) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []
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
                continue
            matches.append((start, end, name))
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    return matches


def collect_tag_replacements(
    text: str,
    catalog: list[dict],
    *,
    target_name: str = "",
) -> list[dict]:
    quote_ranges = _quote_ranges(text)
    candidates: list[dict] = []
    occupied_until = -1

    raw_matches: list[dict] = []
    for item in catalog:
        canonical_name = str(item.get("canonicalName", "")).strip()
        if target_name and canonical_name != target_name and target_name not in item.get("names", []):
            continue
        names = [name for name in item.get("names", []) if isinstance(name, str) and name]
        for start, end, matched_name in _iter_unwrapped_matches(text, names, quote_ranges):
            raw_matches.append(
                {
                    "start": start,
                    "end": end,
                    "id": item.get("id", ""),
                    "matchedName": matched_name,
                    "canonicalName": canonical_name,
                    "kind": item.get("kind", ""),
                    "source": item.get("source", ""),
                    "replacement": f"@{{{canonical_name}}}",
                }
            )

    raw_matches.sort(key=lambda item: (item["start"], -(item["end"] - item["start"])))
    for item in raw_matches:
        if item["start"] < occupied_until:
            continue
        candidates.append(item)
        occupied_until = item["end"]
    return candidates


def _build_related_context(reference_items: list[dict]) -> list[dict]:
    result = []
    seen: set[tuple[str, str]] = set()
    for item in reference_items:
        key = (item.get("source", ""), item.get("id", "") or item.get("canonicalName", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "id": item.get("id", ""),
                "name": item.get("canonicalName", ""),
                "kind": item.get("kind", ""),
                "source": item.get("source", ""),
                "aliases": item.get("aliases", []),
                "summary": item.get("summary", ""),
                "currentState": item.get("currentState", {}),
            }
        )
    return result


def _infer_missing_reference_targets(name: str) -> list[dict]:
    normalized = str(name or "").strip()
    world_hint = None
    for kind, suffixes in WORLD_KIND_HINT_SUFFIXES.items():
        if normalized.endswith(suffixes):
            world_hint = kind
            break

    targets: list[dict] = []
    if world_hint:
        targets.append(
            {
                "target": "world",
                "kind": world_hint,
                "reason": WORLD_KIND_HINT_MESSAGES[world_hint],
            }
        )
    targets.append(
        {
            "target": "entity",
            "kind": "character",
            "reason": "默认实体入口，适合人物、代称或暂未确认归属的称呼。",
        }
    )
    if not world_hint:
        targets.append(
            {
                "target": "world",
                "kind": "location",
                "reason": "若它并非人物而是地点/势力/物件，应改走 world mention-adopt 并确认 kind。",
            }
        )
    return targets


def build_reference_mention_report(state: dict, chapter_text: str) -> dict:
    tagged_mentions = extract_tag_mentions(chapter_text)
    quote_ranges = _quote_ranges(chapter_text)
    catalog = build_reference_catalog(state)

    tagged_covered = []
    tagged_missing = []
    known_unwrapped = []
    ignored_quoted_mentions = []
    related_context_refs = []

    for item in catalog:
        names = [name for name in item.get("names", []) if isinstance(name, str) and name]
        tagged_count = _tagged_occurrence_count(chapter_text, names)
        plain_count, quoted_count = _collect_unwrapped_mentions(chapter_text, names, quote_ranges)

        if tagged_count > 0:
            tagged_covered.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("canonicalName", ""),
                    "kind": item.get("kind", ""),
                    "source": item.get("source", ""),
                    "taggedCount": tagged_count,
                }
            )
            related_context_refs.append(item)

        if plain_count > 0:
            known_unwrapped.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("canonicalName", ""),
                    "kind": item.get("kind", ""),
                    "source": item.get("source", ""),
                    "plainCount": plain_count,
                    "suggestedTag": f"@{{{item.get('canonicalName', '')}}}",
                }
            )
            related_context_refs.append(item)

        if quoted_count > 0:
            ignored_quoted_mentions.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("canonicalName", ""),
                    "kind": item.get("kind", ""),
                    "source": item.get("source", ""),
                    "quotedCount": quoted_count,
                    "reason": "quoted-mention-ignored",
                }
            )
            related_context_refs.append(item)

    tagged_missing_by_name: dict[str, dict] = {}
    known_tagged_names = {item["name"] for item in tagged_covered}
    for mention in tagged_mentions:
        if mention in known_tagged_names:
            continue
        resolved = resolve_named_reference(state, mention)
        if resolved:
            continue
        item = tagged_missing_by_name.setdefault(
            mention,
            {
                "name": mention,
                "occurrenceCount": 0,
                "suggestion": "补建档或核对是否应作为实体/势力/物品进入真相层",
                "suggestedTargets": _infer_missing_reference_targets(mention),
            },
        )
        item["occurrenceCount"] += 1

    tagged_missing = sorted(tagged_missing_by_name.values(), key=lambda item: (-item["occurrenceCount"], item["name"]))

    return {
        "taggedCovered": tagged_covered,
        "taggedMissing": tagged_missing,
        "knownUnwrapped": known_unwrapped,
        "ignoredQuotedKnownMentions": ignored_quoted_mentions,
        "relatedContext": _build_related_context(related_context_refs),
        "summary": {
            "taggedCount": len(tagged_mentions),
            "taggedCoveredCount": len(tagged_covered),
            "taggedMissingCount": len(tagged_missing),
            "knownUnwrappedCount": len(known_unwrapped),
            "ignoredQuotedKnownMentionCount": len(ignored_quoted_mentions),
        },
    }
