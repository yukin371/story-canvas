from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_harness_cli.protocol import (
    chapter_path,
    choose_style_profile_name,
    ensure_project_root,
    load_project_state,
    resolve_review_rule_profile,
    resolve_style_profile,
)
from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services.rule_semantics import chapter_scope_ref
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


def _resolve_profile_name(args_profile: str | None, state: dict[str, Any]) -> str:
    if args_profile:
        return args_profile
    return choose_style_profile_name(state.get("project", {}))


def _build_style_report(
    chapter_id: str,
    chapter_text: str,
    *,
    profile_name: str,
    profile_config: dict[str, Any],
    review_rule_profile_name: str,
    review_rule_config: dict[str, Any],
    review_rule_source: str,
    review_rule_scope: dict[str, str],
) -> dict[str, Any]:
    scorer, source = load_style_similarity_scorer()
    report = analyze_style_text(
        chapter_text,
        opener_similarity_scorer=scorer,
        repetition_source=source,
        profile_name=profile_name,
        profile_config=profile_config,
        review_rule_profile_name=review_rule_profile_name,
        review_rule_config=review_rule_config,
        review_rule_scope=review_rule_scope,
    )
    report["judgements"] = _attach_chapter_scope(report.get("judgements", []), chapter_id)
    report["chapterId"] = chapter_id
    report["source"] = source
    report["reviewRuleProfile"] = review_rule_profile_name
    report["reviewRuleProfileSource"] = review_rule_source
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


def _attach_chapter_scope(judgements: list[dict[str, Any]], chapter_id: str) -> list[dict[str, Any]]:
    scoped: list[dict[str, Any]] = []
    for item in judgements:
        enriched = dict(item)
        scope_ref = dict(item.get("scopeRef", {}))
        if "chapterId" not in scope_ref:
            scope_ref.update(chapter_scope_ref(chapter_id))
        enriched["scopeRef"] = scope_ref
        scoped.append(enriched)
    return scoped


def _find_volume_for_chapter(state: dict[str, Any], chapter_id: str) -> dict[str, Any]:
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return {}


def command_style_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = _resolve_chapter_id(args, state)
    chapter_text = _load_chapter_text(root, chapter_id)
    profile_name = _resolve_profile_name(args.profile, state)
    profile_config, profile_source = resolve_style_profile(root, profile_name)
    volume = _find_volume_for_chapter(state, chapter_id)
    review_rule_config, review_rule_profile_name, review_rule_source = resolve_review_rule_profile(root)
    report = _build_style_report(
        chapter_id,
        chapter_text,
        profile_name=profile_name,
        profile_config=profile_config,
        review_rule_profile_name=review_rule_profile_name,
        review_rule_config=review_rule_config,
        review_rule_source=review_rule_source,
        review_rule_scope={
            "chapterId": chapter_id,
            "volumeId": str(volume.get("id", "")),
            "scenePlanId": "",
        },
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
    profile_name = _resolve_profile_name(args.profile, state)
    profile_config, profile_source = resolve_style_profile(root, profile_name)
    volume = _find_volume_for_chapter(state, chapter_id)
    review_rule_config, review_rule_profile_name, review_rule_source = resolve_review_rule_profile(root)
    report = _build_style_report(
        chapter_id,
        chapter_text,
        profile_name=profile_name,
        profile_config=profile_config,
        review_rule_profile_name=review_rule_profile_name,
        review_rule_config=review_rule_config,
        review_rule_source=review_rule_source,
        review_rule_scope={
            "chapterId": chapter_id,
            "volumeId": str(volume.get("id", "")),
            "scenePlanId": "",
        },
    )
    payload = {
        "chapterId": chapter_id,
        "profile": report["profile"],
        "profileSource": profile_source,
        "reviewRuleProfile": report["reviewRuleProfile"],
        "reviewRuleProfileSource": report["reviewRuleProfileSource"],
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
    profile_name = _resolve_profile_name(args.profile, state)
    profile_config, profile_source = resolve_style_profile(root, profile_name)
    review_rule_config, review_rule_profile_name, review_rule_source = resolve_review_rule_profile(root)
    for chapter_id in chapter_ids:
        chapter_file = chapter_path(root, chapter_id)
        if not chapter_file.exists():
            missing_chapters.append(chapter_id)
            continue
        volume = _find_volume_for_chapter(state, chapter_id)
        report = _build_style_report(
            chapter_id,
            chapter_file.read_text(encoding="utf-8"),
            profile_name=profile_name,
            profile_config=profile_config,
            review_rule_profile_name=review_rule_profile_name,
            review_rule_config=review_rule_config,
            review_rule_source=review_rule_source,
            review_rule_scope={
                "chapterId": chapter_id,
                "volumeId": str(volume.get("id", "")),
                "scenePlanId": "",
            },
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

    aggregate = build_style_report(chapter_reports, volume_id=resolved_volume_id, profile_name=profile_name)
    payload = {
        "profile": profile_name,
        "profileSource": profile_source,
        "reviewRuleProfile": review_rule_profile_name,
        "reviewRuleProfileSource": review_rule_source,
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
    profile_name = _resolve_profile_name(args.profile, state)
    profile_config, profile_source = resolve_style_profile(root, profile_name)
    volume = _find_volume_for_chapter(state, chapter_id)
    review_rule_config, review_rule_profile_name, review_rule_source = resolve_review_rule_profile(root)
    report = _build_style_report(
        chapter_id,
        chapter_text,
        profile_name=profile_name,
        profile_config=profile_config,
        review_rule_profile_name=review_rule_profile_name,
        review_rule_config=review_rule_config,
        review_rule_source=review_rule_source,
        review_rule_scope={
            "chapterId": chapter_id,
            "volumeId": str(volume.get("id", "")),
            "scenePlanId": "",
        },
    )

    if args.format == "change-requests":
        payload = {
            "chapterId": chapter_id,
            "profile": report["profile"],
            "profileSource": profile_source,
            "reviewRuleProfile": report["reviewRuleProfile"],
            "reviewRuleProfileSource": report["reviewRuleProfileSource"],
            "source": report["source"],
            "summary": report["styleAnalysis"]["summary"],
            "changeRequests": build_style_change_request_drafts(chapter_id, report),
        }
    else:
        payload = {
            "chapterId": chapter_id,
            "profile": report["profile"],
            "profileSource": profile_source,
            "reviewRuleProfile": report["reviewRuleProfile"],
            "reviewRuleProfileSource": report["reviewRuleProfileSource"],
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
    check_parser.add_argument("--profile")
    check_parser.set_defaults(func=command_style_check)

    constraints_parser = style_subparsers.add_parser("constraints", help="Generate rewrite constraints for one chapter")
    constraints_parser.add_argument("--root", required=True)
    constraints_parser.add_argument("--chapter-id")
    constraints_parser.add_argument("--profile")
    constraints_parser.set_defaults(func=command_style_constraints)

    report_parser = style_subparsers.add_parser("report", help="Aggregate style analysis across chapters")
    report_parser.add_argument("--root", required=True)
    report_parser.add_argument("--volume-id")
    report_parser.add_argument("--profile")
    report_parser.set_defaults(func=command_style_report)

    repair_parser = style_subparsers.add_parser("repair", help="Build repair guidance from style analysis")
    repair_parser.add_argument("--root", required=True)
    repair_parser.add_argument("--chapter-id")
    repair_parser.add_argument("--profile")
    repair_parser.add_argument("--format", choices=["prompt", "change-requests"], default="prompt")
    repair_parser.set_defaults(func=command_style_repair)
