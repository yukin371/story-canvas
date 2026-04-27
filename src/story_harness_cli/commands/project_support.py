from __future__ import annotations

from pathlib import Path
from typing import Any


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
