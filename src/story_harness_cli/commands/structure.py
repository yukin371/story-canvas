from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.commands.project_support import build_project_advisories
from story_harness_cli.protocol import ensure_project_root, load_project_state, save_state
from story_harness_cli.services.structure import (
    apply_template,
    check_structure,
    list_templates,
    scaffold_structure_to_outline,
    show_structure,
)


def _with_project_advisories(root: Path, payload: dict) -> dict:
    payload["projectAdvisories"] = build_project_advisories(root, include_prd_content=True)
    return payload


def command_structure_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)

    result = list_templates()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_structure_apply(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    try:
        result = apply_template(state, template_id=args.template)
    except ValueError as exc:
        print(json.dumps(_with_project_advisories(root, {"error": str(exc)}), ensure_ascii=False, indent=2))
        return 1

    save_state(root, state)
    print(json.dumps(_with_project_advisories(root, result), ensure_ascii=False, indent=2))
    return 0


def command_structure_show(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    result = show_structure(state)
    print(json.dumps(_with_project_advisories(root, result), ensure_ascii=False, indent=2))
    return 0


def command_structure_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    result = check_structure(state)
    print(json.dumps(_with_project_advisories(root, result), ensure_ascii=False, indent=2))
    return 0


def command_structure_map(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    structures = state.setdefault("structures", {"activeStructure": None, "mappings": []})
    if not structures.get("activeStructure"):
        print(
            json.dumps(
                _with_project_advisories(root, {"error": "No active structure. Run 'structure apply' first."}),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    mappings = structures.get("mappings", [])
    found = False
    for m in mappings:
        if m["beatName"] == args.beat:
            m["chapterId"] = args.chapter_id
            found = True
            break

    if not found:
        print(
            json.dumps(
                _with_project_advisories(root, {"error": f"Beat '{args.beat}' not found in active structure"}),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    save_state(root, state)
    print(
        json.dumps(
            _with_project_advisories(root, {"beatName": args.beat, "chapterId": args.chapter_id}),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_structure_scaffold(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    try:
        result = scaffold_structure_to_outline(
            state,
            mapped_only=args.mapped_only,
            replace_directions=args.replace_directions,
        )
    except ValueError as exc:
        print(json.dumps(_with_project_advisories(root, {"error": str(exc)}), ensure_ascii=False, indent=2))
        return 1

    save_state(root, state)
    print(json.dumps(_with_project_advisories(root, result), ensure_ascii=False, indent=2))
    return 0


def register_structure_commands(subparsers) -> None:
    structure_parser = subparsers.add_parser("structure", help="Narrative structure templates")
    structure_sub = structure_parser.add_subparsers(dest="structure_command", required=True)

    # structure list
    list_parser = structure_sub.add_parser("list", help="List all available structure templates")
    list_parser.add_argument("--root", required=True)
    list_parser.set_defaults(func=command_structure_list)

    # structure apply
    apply_parser = structure_sub.add_parser("apply", help="Activate a structure template")
    apply_parser.add_argument("--root", required=True)
    apply_parser.add_argument("--template", required=True, help="Template id (e.g. three-act)")
    apply_parser.set_defaults(func=command_structure_apply)

    # structure show
    show_parser = structure_sub.add_parser("show", help="Show active template with mappings")
    show_parser.add_argument("--root", required=True)
    show_parser.set_defaults(func=command_structure_show)

    # structure check
    check_parser = structure_sub.add_parser("check", help="Validate structure coverage")
    check_parser.add_argument("--root", required=True)
    check_parser.set_defaults(func=command_structure_check)

    # structure map
    map_parser = structure_sub.add_parser("map", help="Map a beat to a chapter")
    map_parser.add_argument("--root", required=True)
    map_parser.add_argument("--beat", required=True, help="Beat name to map")
    map_parser.add_argument("--chapter-id", required=True, help="Chapter id to map to")
    map_parser.set_defaults(func=command_structure_map)

    # structure scaffold
    scaffold_parser = structure_sub.add_parser("scaffold", help="Scaffold outline beats and directions from active structure")
    scaffold_parser.add_argument("--root", required=True)
    scaffold_parser.add_argument(
        "--mapped-only",
        action="store_true",
        help="Only scaffold beats that have explicit structure map bindings",
    )
    scaffold_parser.add_argument(
        "--replace-directions",
        action="store_true",
        help="Overwrite existing manual chapter directions with generated structure directions",
    )
    scaffold_parser.set_defaults(func=command_structure_scaffold)
