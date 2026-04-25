from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_harness_cli.protocol import (
    chapter_path,
    ensure_project_root,
    load_project_state,
    resolve_style_profile,
)
from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services import (
    analyze_style_text,
    build_style_change_request_drafts,
    build_style_repair_prompt,
    build_style_report,
)


def _resolve_chapter_id(args, state: dict[str, Any]) -> str:
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    return chapter_id


def _load_chapter_text(root: Path, chapter_id: str) -> str:
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")
    return chapter_file.read_text(encoding="utf-8")


def _build_style_report(
    chapter_id: str,
    chapter_text: str,
    *,
    profile_name: str,
    profile_config: dict[str, Any],
) -> dict[str, Any]:
    scorer, source = load_style_similarity_scorer()
    report = analyze_style_text(
        chapter_text,
        opener_similarity_scorer=scorer,
        repetition_source=source,
        profile_name=profile_name,
        profile_config=profile_config,
    )
    report["chapterId"] = chapter_id
    report["source"] = source
    return report


def _target_chapter_ids(state: dict[str, Any], volume_id: str | None) -> tuple[list[str], str]:
    outline = state.get("outline", {})
    if volume_id:
        for volume in outline.get("volumes", []):
            if volume.get("id") == volume_id:
                return [item["id"] for item in volume.get("chapters", []) if item.get("id")], volume_id
        raise SystemExit(f"volume 不存在: {volume_id}")

    chapter_ids = [item["id"] for item in outline.get("chapters", []) if item.get("id")]
    if chapter_ids:
        return chapter_ids, ""
    return [], ""


def command_style_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)
    chapter_text = _load_chapter_text(root, chapter_id)
    profile_config, profile_source = resolve_style_profile(root, args.profile)
    report = _build_style_report(
        chapter_id,
        chapter_text,
        profile_name=args.profile,
        profile_config=profile_config,
    )
    report["profileSource"] = profile_source
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_style_constraints(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)
    chapter_text = _load_chapter_text(root, chapter_id)
    profile_config, profile_source = resolve_style_profile(root, args.profile)
    report = _build_style_report(
        chapter_id,
        chapter_text,
        profile_name=args.profile,
        profile_config=profile_config,
    )
    payload = {
        "chapterId": chapter_id,
        "profile": report["profile"],
        "profileSource": profile_source,
        "source": report["source"],
        "constraints": report["constraints"],
        "summary": report["styleAnalysis"]["summary"],
        "totalDeduction": report["styleAnalysis"]["totalDeduction"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_style_report(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_ids, resolved_volume_id = _target_chapter_ids(state, args.volume_id)
    if not chapter_ids:
        raise SystemExit("没有可生成 style report 的章节")

    chapter_reports = []
    missing_chapters = []
    profile_config, profile_source = resolve_style_profile(root, args.profile)
    for chapter_id in chapter_ids:
        chapter_file = chapter_path(root, chapter_id)
        if not chapter_file.exists():
            missing_chapters.append(chapter_id)
            continue
        report = _build_style_report(
            chapter_id,
            chapter_file.read_text(encoding="utf-8"),
            profile_name=args.profile,
            profile_config=profile_config,
        )
        chapter_reports.append(
            {
                "chapterId": chapter_id,
                "overallScore": report["styleAnalysis"]["overallScore"],
                "totalDeduction": report["styleAnalysis"]["totalDeduction"],
                "detectedPatterns": [
                    item["label"] for item in report["styleAnalysis"]["patternResults"] if item.get("detected")
                ],
                "source": report["source"],
                "styleAnalysis": report["styleAnalysis"],
            }
        )

    aggregate = build_style_report(chapter_reports, volume_id=resolved_volume_id, profile_name=args.profile)
    payload = {
        "profile": args.profile,
        "profileSource": profile_source,
        "volumeId": resolved_volume_id,
        "chapterCount": len(chapter_reports),
        "missingChapters": missing_chapters,
        "chapters": [
            {
                "chapterId": item["chapterId"],
                "overallScore": item["overallScore"],
                "totalDeduction": item["totalDeduction"],
                "detectedPatterns": item["detectedPatterns"],
                "source": item["source"],
            }
            for item in chapter_reports
        ],
        "aggregate": aggregate,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_style_repair(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)
    chapter_text = _load_chapter_text(root, chapter_id)
    profile_config, profile_source = resolve_style_profile(root, args.profile)
    report = _build_style_report(
        chapter_id,
        chapter_text,
        profile_name=args.profile,
        profile_config=profile_config,
    )

    if args.format == "change-requests":
        payload = {
            "chapterId": chapter_id,
            "profile": report["profile"],
            "profileSource": profile_source,
            "source": report["source"],
            "summary": report["styleAnalysis"]["summary"],
            "changeRequests": build_style_change_request_drafts(chapter_id, report),
        }
    else:
        payload = {
            "chapterId": chapter_id,
            "profile": report["profile"],
            "profileSource": profile_source,
            "source": report["source"],
            "summary": report["styleAnalysis"]["summary"],
            "constraints": report["constraints"],
            "repairPrompt": build_style_repair_prompt(
                chapter_text,
                report,
                chapter_id=chapter_id,
            ),
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def register_style_commands(subparsers) -> None:
    style_parser = subparsers.add_parser("style", help="Analyze AI-typical prose style patterns")
    style_subparsers = style_parser.add_subparsers(dest="style_command", required=True)

    check_parser = style_subparsers.add_parser("check", help="Analyze one chapter for AI-style patterns")
    check_parser.add_argument("--root", required=True)
    check_parser.add_argument("--chapter-id")
    check_parser.add_argument("--profile", default="default")
    check_parser.set_defaults(func=command_style_check)

    constraints_parser = style_subparsers.add_parser("constraints", help="Generate rewrite constraints for one chapter")
    constraints_parser.add_argument("--root", required=True)
    constraints_parser.add_argument("--chapter-id")
    constraints_parser.add_argument("--profile", default="default")
    constraints_parser.set_defaults(func=command_style_constraints)

    report_parser = style_subparsers.add_parser("report", help="Aggregate style analysis across chapters")
    report_parser.add_argument("--root", required=True)
    report_parser.add_argument("--volume-id")
    report_parser.add_argument("--profile", default="default")
    report_parser.set_defaults(func=command_style_report)

    repair_parser = style_subparsers.add_parser("repair", help="Build repair guidance from style analysis")
    repair_parser.add_argument("--root", required=True)
    repair_parser.add_argument("--chapter-id")
    repair_parser.add_argument("--profile", default="default")
    repair_parser.add_argument("--format", choices=["prompt", "change-requests"], default="prompt")
    repair_parser.set_defaults(func=command_style_repair)
