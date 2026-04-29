from __future__ import annotations

from pathlib import Path
from typing import Any

from story_harness_cli.protocol import chapter_path
from story_harness_cli.utils.text import paragraphs_from_text


_PRD_BOOTSTRAP_PLACEHOLDERS = {
    "- 卷目标: TBD": "卷目标",
    "- 读者钩子: TBD": "读者钩子",
    "- 压制源与预期爆发点: TBD": "压制源与预期爆发点",
    "- 关键设定 onboarding: TBD": "关键设定 onboarding",
    "- 本章承接点: TBD": "本章承接点",
    "- 本章交付点: TBD": "本章交付点",
}


def _summarize_unresolved_items(items: list[str], *, limit: int = 6) -> str:
    visible = items[:limit]
    if len(items) <= limit:
        return "、".join(visible)
    return f"{'、'.join(visible)} 等 {len(items)} 项"


def _build_missing_prd_advisory() -> dict[str, Any]:
    return {
        "ruleId": "missing-project-prd",
        "scope": "project",
        "severity": "warning",
        "path": "PRD.md",
        "message": "项目根目录缺少 PRD.md；当前缺少明确的立项/卷职责文档入口。",
        "nextAction": "补项目 PRD.md，明确立项、卷目标与当前章节交付。",
    }


def _build_incomplete_prd_advisories(prd_path: Path) -> list[dict[str, Any]]:
    text = prd_path.read_text(encoding="utf-8")
    unresolved_items = [
        label for marker, label in _PRD_BOOTSTRAP_PLACEHOLDERS.items() if marker in text
    ]
    if not unresolved_items:
        return []
    return [
        {
            "ruleId": "project-prd-incomplete",
            "scope": "project",
            "severity": "warning",
            "path": "PRD.md",
            "message": (
                "PRD.md 仍包含未填启动占位项："
                f"{_summarize_unresolved_items(unresolved_items)}；当前不应把它视为已完成的项目/卷职责文档。"
            ),
            "nextAction": "补齐卷目标、读者钩子、承接点与交付点等启动焦点，避免沿用模板占位直接开写。",
            "details": {
                "unresolvedItems": unresolved_items,
            },
        }
    ]


def build_project_advisories(root: Path, *, include_prd_content: bool = False) -> list[dict[str, Any]]:
    prd_path = root / "PRD.md"
    if prd_path.exists():
        return _build_incomplete_prd_advisories(prd_path) if include_prd_content else []
    return [_build_missing_prd_advisory()]


def _append_once(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def build_chapter_start_guide(
    root: Path,
    chapter_id: str,
    *,
    missing_codes: list[str] | None = None,
) -> dict[str, Any]:
    chapter_file = chapter_path(root, chapter_id)
    chapter_text = chapter_file.read_text(encoding="utf-8") if chapter_file.exists() else ""
    has_body_paragraphs = bool(paragraphs_from_text(chapter_text)) if chapter_text else False
    startup_codes = {"missing-direction", "missing-beats", "missing-scene-plans"}
    codes = startup_codes if missing_codes is None else {code for code in missing_codes if code in startup_codes}

    notes: list[str] = []
    suggested_commands: list[str] = []
    root_arg = f'"{root}"'

    if not has_body_paragraphs:
        notes.append("当前章节正文仍为空；先在章节文件里按场景写 1 段骨架，再继续 scenePlans 闭环。")

    if "missing-direction" in codes or "missing-beats" in codes:
        notes.append("如果还没定章节结构，先用 structure 模板落一版 direction/beats；已有明确想法时再手工补 beat。")
        _append_once(suggested_commands, f"story-canvas structure list --root {root_arg}")
        _append_once(suggested_commands, f"story-canvas structure apply --root {root_arg} --template three-act")
        _append_once(suggested_commands, f"story-canvas structure scaffold --root {root_arg}")
        if "missing-beats" in codes:
            _append_once(
                suggested_commands,
                f'story-canvas outline beat-add --root {root_arg} --chapter-id {chapter_id} --summary "补一条本章关键推进 beat"',
            )

    if "missing-scene-plans" in codes:
        if has_body_paragraphs:
            notes.append("当前章节已经有正文段落，可以直接用 scene-detect 生成首版 scenePlans。")
            _append_once(suggested_commands, f"story-canvas outline scene-detect --root {root_arg} --chapter-id {chapter_id}")
        else:
            notes.append("scenePlans 当前依赖段落边界；如果还没正文，先在章节文件中为每个计划 scene 写一段骨架。")
        _append_once(suggested_commands, f"story-canvas outline scene-list --root {root_arg} --chapter-id {chapter_id}")

    if not codes:
        if has_body_paragraphs:
            notes.append("当前章节起步门禁已齐备，可继续 analyze / suggest / context / review 闭环。")
            _append_once(suggested_commands, f"story-canvas chapter analyze --root {root_arg} --chapter-id {chapter_id}")
            _append_once(suggested_commands, f"story-canvas chapter suggest --root {root_arg} --chapter-id {chapter_id}")
            _append_once(
                suggested_commands,
                f"story-canvas review apply --root {root_arg} --all-pending --decision accepted",
            )
            _append_once(suggested_commands, f"story-canvas projection apply --root {root_arg} --chapter-id {chapter_id}")
            _append_once(suggested_commands, f"story-canvas context refresh --root {root_arg} --chapter-id {chapter_id}")
            _append_once(suggested_commands, f"story-canvas review chapter --root {root_arg} --chapter-id {chapter_id}")
            _append_once(suggested_commands, f"story-canvas outline scene-list --root {root_arg} --chapter-id {chapter_id}")
            _append_once(
                suggested_commands,
                f"story-canvas review scene --root {root_arg} --chapter-id {chapter_id} --scene-index 1",
            )
        else:
            notes.append("当前章节结构门禁已齐备，但正文仍为空；先按 beats / scenePlans 写出首版正文。")
            _append_once(suggested_commands, f"story-canvas outline scene-list --root {root_arg} --chapter-id {chapter_id}")
    else:
        _append_once(suggested_commands, f"story-canvas outline check --root {root_arg} --chapter-id {chapter_id}")
    _append_once(suggested_commands, f"story-canvas status --root {root_arg} --chapter-id {chapter_id}")

    return {
        "chapterId": chapter_id,
        "chapterFile": str(chapter_file),
        "chapterFileExists": chapter_file.exists(),
        "hasBodyParagraphs": has_body_paragraphs,
        "missingCodes": sorted(codes),
        "notes": notes,
        "suggestedCommands": suggested_commands,
    }
