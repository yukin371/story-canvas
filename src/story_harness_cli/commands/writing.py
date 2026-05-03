from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from story_harness_cli.protocol import ensure_project_root
from story_harness_cli.protocol.files import chapter_path
from story_harness_cli.protocol.io import load_state
from story_harness_cli.services.reference_mentions import (
    build_reference_catalog,
    build_reference_mention_report,
    collect_tag_replacements,
)
from story_harness_cli.services.relation_tracker import track_relation_changes
from story_harness_cli.utils import now_iso
from story_harness_cli.utils.text import find_malformed_entity_tags


def command_writing_assist(args: argparse.Namespace) -> int:
    root, state, chapter_id, chapter_text = _load_chapter_context(args)
    assistance = build_writing_assistance(
        state,
        chapter_id,
        chapter_text,
        assistance_type=args.assistance_type or "full",
    )
    print(json.dumps(assistance, ensure_ascii=False, indent=2))
    return 0


def command_writing_mention_check(args: argparse.Namespace) -> int:
    root, state, chapter_id, chapter_text = _load_chapter_context(args)
    replacements = collect_tag_replacements(chapter_text, build_reference_catalog(state))

    if args.auto_apply:
        payload = _apply_or_preview_mentions(
            root=root,
            state=state,
            chapter_id=chapter_id,
            chapter_text=chapter_text,
            replacements=replacements,
            dry_run=False,
        )
    else:
        report = build_reference_mention_report(state, chapter_text)
        payload = {
            "chapterId": chapter_id,
            "suggestionCount": len(report.get("knownUnwrapped", [])),
            "suggestions": _mention_suggestions_from_report(report),
            "summary": report.get("summary", {}),
        }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_writing_relation_track(args: argparse.Namespace) -> int:
    _root, state, chapter_id, chapter_text = _load_chapter_context(args)
    result = track_relation_changes(
        state,
        chapter_id,
        chapter_text,
        auto_detect=args.auto_detect,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_writing_auto_wrap(args: argparse.Namespace) -> int:
    root, state, chapter_id, chapter_text = _load_chapter_context(args)
    replacements = collect_tag_replacements(chapter_text, build_reference_catalog(state))
    payload = _apply_or_preview_mentions(
        root=root,
        state=state,
        chapter_id=chapter_id,
        chapter_text=chapter_text,
        replacements=replacements,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_writing_wrap_history(args: argparse.Namespace) -> int:
    _root, state, chapter_id, chapter_text = _load_chapter_context(args)
    report = build_reference_mention_report(state, chapter_text)
    payload = {
        "chapterId": chapter_id,
        "status": "not-persisted",
        "message": "writing wrap-history 当前只返回现时 mention 摘要；包裹历史尚未作为独立真相源持久化。",
        "summary": report.get("summary", {}),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_writing_assistance(
    state: dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    assistance_type: str = "full",
) -> dict[str, Any]:
    normalized_type = "mention-only" if assistance_type == "entity-only" else assistance_type
    assistance = {
        "chapterId": chapter_id,
        "timestamp": now_iso(),
        "assistanceType": normalized_type,
        "mentionSuggestions": [],
        "relationSuggestions": [],
        "foreshadowSuggestions": [],
        "consistencyWarnings": [],
    }

    if normalized_type in {"full", "mention-only"}:
        report = build_reference_mention_report(state, chapter_text)
        assistance["mentionSuggestions"] = _mention_suggestions_from_report(report)
        assistance["mentionSummary"] = report.get("summary", {})

    if normalized_type in {"full", "relation-only"}:
        relation_result = track_relation_changes(state, chapter_id, chapter_text, auto_detect=True)
        assistance["relationSuggestions"] = relation_result.get("detectedChanges", [])

    return assistance


def _load_chapter_context(args: argparse.Namespace) -> tuple[Path, dict[str, Any], str, str]:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_state(root)
    chapter_id = args.chapter_id or state.get("project", {}).get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节文件不存在: {chapter_file}")
    return root, state, chapter_id, chapter_file.read_text(encoding="utf-8")


def _mention_suggestions_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    for item in report.get("knownUnwrapped", []):
        plain_count = int(item.get("plainCount", 0) or 0)
        suggestions.append(
            {
                "entityId": item.get("id", ""),
                "name": item.get("name", ""),
                "kind": item.get("kind", ""),
                "source": item.get("source", ""),
                "plainCount": plain_count,
                "suggestedTag": item.get("suggestedTag", ""),
                "priority": "high" if plain_count > 3 else "medium",
                "autoActionable": True,
            }
        )
    return suggestions


def _apply_or_preview_mentions(
    *,
    root: Path,
    state: dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    replacements: list[dict[str, Any]],
    dry_run: bool,
) -> dict[str, Any]:
    updated_text = _apply_tag_replacements(chapter_text, replacements)
    post_apply_check = _build_post_apply_check(state, chapter_id, updated_text)
    if int(post_apply_check.get("malformedTagCount", 0)) > 0:
        raise SystemExit("mention 修补结果包含非法 @{...} 标签，已拒绝写入")

    updated = updated_text != chapter_text
    if updated and not dry_run:
        chapter_path(root, chapter_id).write_text(updated_text, encoding="utf-8")

    return {
        "chapterId": chapter_id,
        "dryRun": dry_run,
        "updated": updated and not dry_run,
        "wouldUpdate": updated,
        "replacementCount": len(replacements),
        "postApplyCheck": post_apply_check,
        "replacements": [
            {
                "name": item.get("canonicalName", ""),
                "matchedName": item.get("matchedName", ""),
                "kind": item.get("kind", ""),
                "source": item.get("source", ""),
                "replacement": item.get("replacement", ""),
            }
            for item in replacements
        ],
    }


def _apply_tag_replacements(text: str, replacements: list[dict[str, Any]]) -> str:
    if not replacements:
        return text
    chunks: list[str] = []
    cursor = 0
    for item in sorted(replacements, key=lambda match: int(match["start"])):
        start = int(item["start"])
        end = int(item["end"])
        chunks.append(text[cursor:start])
        chunks.append(str(item["replacement"]))
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks)


def _build_post_apply_check(state: dict[str, Any], chapter_id: str, chapter_text: str) -> dict[str, Any]:
    malformed_tags = find_malformed_entity_tags(chapter_text)
    report = build_reference_mention_report(state, chapter_text)
    summary = report.get("summary", {})
    needs_manual_review = bool(malformed_tags)
    reasons: list[str] = []
    if malformed_tags:
        reasons.append("修补结果包含非法 @{...} 标签")
    return {
        "valid": not needs_manual_review,
        "needsManualReview": needs_manual_review,
        "manualReviewReasons": reasons,
        "malformedTagCount": len(malformed_tags),
        "malformedTags": malformed_tags[:5],
        "remainingKnownUnwrappedActionCount": summary.get("knownUnwrappedCount", 0),
        "remainingTaggedMissingActionCount": summary.get("taggedMissingCount", 0),
        "remainingTotalActionCount": int(summary.get("knownUnwrappedCount", 0) or 0)
        + int(summary.get("taggedMissingCount", 0) or 0),
    }


def register_writing_commands(subparsers) -> None:
    writing_parser = subparsers.add_parser("writing", help="写作辅助命令")
    writing_subparsers = writing_parser.add_subparsers(dest="writing_command", required=True)

    auto_wrap_parser = writing_subparsers.add_parser("auto-wrap", help="自动包裹实体")
    auto_wrap_parser.add_argument("--root", required=True, help="项目根目录")
    auto_wrap_parser.add_argument("--chapter-id", type=str, help="章节ID")
    auto_wrap_parser.add_argument("--dry-run", action="store_true", help="预览包裹结果，不实际修改")
    auto_wrap_parser.set_defaults(func=command_writing_auto_wrap)

    history_parser = writing_subparsers.add_parser("wrap-history", help="查看包裹摘要")
    history_parser.add_argument("--root", required=True, help="项目根目录")
    history_parser.add_argument("--chapter-id", type=str, help="章节ID")
    history_parser.set_defaults(func=command_writing_wrap_history)

    assist_parser = writing_subparsers.add_parser("assist", help="写作辅助")
    assist_parser.add_argument("--root", required=True, help="项目根目录")
    assist_parser.add_argument("--chapter-id", type=str, help="章节ID")
    assist_parser.add_argument(
        "--assistance-type",
        choices=["full", "mention-only", "entity-only", "relation-only"],
        help="辅助类型；entity-only 是 mention-only 的兼容别名",
    )
    assist_parser.set_defaults(func=command_writing_assist)

    mention_parser = writing_subparsers.add_parser("mention-check", help="检查/应用@{}包裹")
    mention_parser.add_argument("--root", required=True, help="项目根目录")
    mention_parser.add_argument("--chapter-id", type=str, help="章节ID")
    mention_parser.add_argument("--auto-apply", action="store_true", help="自动应用建议")
    mention_parser.set_defaults(func=command_writing_mention_check)

    relation_parser = writing_subparsers.add_parser("relation-track", help="追踪角色关系变化")
    relation_parser.add_argument("--root", required=True, help="项目根目录")
    relation_parser.add_argument("--chapter-id", type=str, help="章节ID")
    relation_parser.add_argument("--auto-detect", action="store_true", help="自动检测关系变化")
    relation_parser.set_defaults(func=command_writing_relation_track)
