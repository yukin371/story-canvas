from __future__ import annotations

from typing import Any, Dict, List

from .rule_registry import resolve_rule_metadata


def build_rule_judgement(
    *,
    rule_id: str,
    source: str | None = None,
    scope: str | None = None,
    kind: str | None = None,
    severity: str | None = None,
    status: str = "triggered",
    message: str,
    suggestion: str = "",
    evidence: List[str] | None = None,
    scope_ref: Dict[str, Any] | None = None,
    payload: Dict[str, Any] | None = None,
    tags: List[str] | None = None,
) -> Dict[str, Any]:
    metadata = resolve_rule_metadata(
        rule_id,
        source=source,
        scope=scope,
        kind=kind,
        severity=severity,
        tags=tags,
    )
    return {
        "ruleId": rule_id,
        "source": metadata["source"],
        "scope": metadata["scope"],
        "kind": metadata["kind"],
        "severity": metadata["severity"],
        "status": status,
        "message": message,
        "suggestion": suggestion,
        "evidence": list(evidence or [])[:5],
        "scopeRef": dict(scope_ref or {}),
        "payload": dict(payload or {}),
        "tags": metadata["tags"],
    }


def chapter_scope_ref(chapter_id: str, paragraph_index: int | None = None) -> Dict[str, Any]:
    scope_ref: Dict[str, Any] = {"chapterId": chapter_id}
    if paragraph_index is not None:
        scope_ref["paragraphIndex"] = paragraph_index
    return scope_ref


def scene_scope_ref(
    chapter_id: str,
    start_paragraph: int | None = None,
    end_paragraph: int | None = None,
) -> Dict[str, Any]:
    scope_ref: Dict[str, Any] = {"chapterId": chapter_id}
    if start_paragraph is not None:
        scope_ref["startParagraph"] = start_paragraph
    if end_paragraph is not None:
        scope_ref["endParagraph"] = end_paragraph
    return scope_ref
