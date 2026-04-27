from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.commands.project_support import build_project_advisories
from story_harness_cli.protocol import ensure_project_root, load_project_state, save_state
from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.services import refresh_context_lens
from story_harness_cli.utils import now_iso


def _decorate_context_lens(root: Path, lens: dict) -> dict:
    return {
        **lens,
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
    }


def command_context_refresh(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    analysis = load_json_compatible_yaml(root / "logs" / (f"analysis-{chapter_id}.yaml" if chapter_id else "latest-analysis.yaml"), {})
    if not analysis:
        analysis = load_json_compatible_yaml(root / "logs" / "latest-analysis.yaml", {})

    lens = refresh_context_lens(state, chapter_id, analysis)
    state["project"]["activeChapterId"] = chapter_id
    state["project"]["updatedAt"] = now_iso()
    save_state(root, state)
    print(json.dumps(_decorate_context_lens(root, lens), ensure_ascii=False, indent=2))
    return 0


def command_context_show(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id or state["context_lens"].get("currentChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id 且没有活跃章节")
    for lens in state["context_lens"].get("lenses", []):
        if lens.get("chapterId") == chapter_id:
            print(json.dumps(_decorate_context_lens(root, lens), ensure_ascii=False, indent=2))
            return 0
    raise SystemExit(f"章节 {chapter_id} 尚无 context lens，请先运行 context refresh")


def register_context_commands(subparsers) -> None:
    context_parser = subparsers.add_parser("context", help="Context lens commands")
    context_subparsers = context_parser.add_subparsers(dest="context_command", required=True)

    refresh_parser = context_subparsers.add_parser("refresh", help="Refresh local writing context")
    refresh_parser.add_argument("--root", required=True)
    refresh_parser.add_argument("--chapter-id")
    refresh_parser.set_defaults(func=command_context_refresh)

    show_parser = context_subparsers.add_parser("show", help="Show current context lens for a chapter")
    show_parser.add_argument("--root", required=True)
    show_parser.add_argument("--chapter-id")
    show_parser.set_defaults(func=command_context_show)

