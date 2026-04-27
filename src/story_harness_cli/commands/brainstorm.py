from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.commands.project_support import build_project_advisories
from story_harness_cli.services.inspiration import (
    generate_character_suggestions,
    generate_outline_skeleton,
    generate_world_suggestions,
)


def command_brainstorm_character(args) -> int:
    count = args.count or 3
    suggestions = generate_character_suggestions(count=count)
    print(json.dumps({"suggestions": suggestions}, ensure_ascii=False, indent=2))
    return 0


def command_brainstorm_world(args) -> int:
    count = args.count or 3
    suggestions = generate_world_suggestions(count=count)
    print(json.dumps({"suggestions": suggestions}, ensure_ascii=False, indent=2))
    return 0


def command_brainstorm_outline(args) -> int:
    root_hint = args.root
    project_advisories = []
    volumes_input = []
    vol_count = args.volumes or 1
    chap_per_vol = args.chapters_per_volume or 5
    for i in range(1, vol_count + 1):
        volumes_input.append({
            "title": f"第{i}卷",
            "chapterCount": chap_per_vol,
        })
    skeleton = generate_outline_skeleton(volumes_input)

    if root_hint:
        root = Path(root_hint).resolve()
        project_advisories = build_project_advisories(root, include_prd_content=True)
        outline_path = root / "outline.yaml"
        if outline_path.exists():
            outline = json.loads(outline_path.read_text(encoding="utf-8"))
        else:
            outline = {"volumes": [], "chapters": [], "chapterDirections": []}
        outline["volumes"] = skeleton
        outline_path.parent.mkdir(parents=True, exist_ok=True)
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"volumes": skeleton, "projectAdvisories": project_advisories}, ensure_ascii=False, indent=2))
    return 0


def register_brainstorm_commands(subparsers) -> None:
    brainstorm_parser = subparsers.add_parser("brainstorm", help="Brainstorm creative elements")
    bs_sub = brainstorm_parser.add_subparsers(dest="brainstorm_command", required=True)

    char_parser = bs_sub.add_parser("character", help="Generate character suggestions")
    char_parser.add_argument("--random", action="store_true", help="Random generation mode")
    char_parser.add_argument("--count", type=int, default=3)
    char_parser.set_defaults(func=command_brainstorm_character)

    world_parser = bs_sub.add_parser("world", help="Generate world element suggestions")
    world_parser.add_argument("--random", action="store_true", help="Random generation mode")
    world_parser.add_argument("--count", type=int, default=3)
    world_parser.set_defaults(func=command_brainstorm_world)

    outline_parser = bs_sub.add_parser("outline", help="Generate outline skeleton")
    outline_parser.add_argument("--root", required=False)
    outline_parser.add_argument("--volumes", type=int, default=1)
    outline_parser.add_argument("--chapters-per-volume", type=int, default=5)
    outline_parser.set_defaults(func=command_brainstorm_outline)
