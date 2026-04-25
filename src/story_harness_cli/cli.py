from __future__ import annotations

import argparse
from typing import List

from story_harness_cli.commands import (
    register_arc_commands,
    register_brainstorm_commands,
    register_causality_commands,
    register_chapter_commands,
    register_consistency_commands,
    register_context_commands,
    register_doctor_commands,
    register_entity_commands,
    register_export_commands,
    register_foreshadow_commands,
    register_illustration_commands,
    register_outline_commands,
    register_projection_commands,
    register_project_commands,
    register_review_commands,
    register_stats_commands,
    register_structure_commands,
    register_timeline_commands,
    register_search_commands,
    register_style_commands,
    register_thread_commands,
    register_workflow_commands,
    register_migrate_commands,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Story Harness CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_arc_commands(subparsers)
    register_brainstorm_commands(subparsers)
    register_causality_commands(subparsers)
    register_project_commands(subparsers)
    register_chapter_commands(subparsers)
    register_review_commands(subparsers)
    register_outline_commands(subparsers)
    register_projection_commands(subparsers)
    register_context_commands(subparsers)
    register_doctor_commands(subparsers)
    register_consistency_commands(subparsers)
    register_entity_commands(subparsers)
    register_export_commands(subparsers)
    register_foreshadow_commands(subparsers)
    register_illustration_commands(subparsers)
    register_stats_commands(subparsers)
    register_timeline_commands(subparsers)
    register_search_commands(subparsers)
    register_style_commands(subparsers)
    register_thread_commands(subparsers)
    register_workflow_commands(subparsers)
    register_structure_commands(subparsers)
    register_migrate_commands(subparsers)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
