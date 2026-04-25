from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_harness_cli.protocol import (
    chapter_path,
    ensure_project_root,
    load_project_state,
    resolve_state_path,
    save_state,
)
from story_harness_cli.services import (
    advance_workflow_progress,
    build_workflow_progress,
    export_workflow_payload,
    hydrate_workflow_progress,
    infer_workflow_status,
    reset_workflow_progress,
)
from story_harness_cli.utils import now_iso


def _collect_chapter_files(root: Path, state: dict[str, Any], explicit_chapter_id: str | None) -> dict[str, bool]:
    chapter_ids = {
        item.get("id")
        for item in state.get("outline", {}).get("chapters", [])
        if item.get("id")
    }
    if explicit_chapter_id:
        chapter_ids.add(explicit_chapter_id)
    return {chapter_id: chapter_path(root, chapter_id).exists() for chapter_id in chapter_ids if chapter_id}


def _infer(root: Path, state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    return infer_workflow_status(
        state,
        chapter_id=chapter_id,
        chapter_files=_collect_chapter_files(root, state, chapter_id),
    )


def _workflow_path(root: Path) -> Path:
    return resolve_state_path(root, "workflow_progress")


def command_workflow_status(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    workflow_path = _workflow_path(root)
    inferred = _infer(root, state, args.chapter_id)
    workflow_progress = hydrate_workflow_progress(state.get("workflow_progress", {}), inferred)

    payload = {
        "workflowFile": str(workflow_path),
        "workflowFileExists": workflow_path.exists(),
        "stateSource": "persisted" if workflow_path.exists() else "inferred",
        "inferredCurrentStage": inferred["currentStage"],
        "inferredWorkflowStatus": inferred["workflowStatus"],
        "projectGate": inferred["projectGate"],
        "targetChapterTitle": inferred["targetChapterTitle"],
        **workflow_progress,
        "stageOrder": inferred["stageOrder"],
        "currentGateDecision": workflow_progress["stageResults"][workflow_progress["currentStage"]]["gateDecision"],
        "currentRuleJudgements": workflow_progress["stageResults"][workflow_progress["currentStage"]]["ruleJudgements"],
        "nextActions": workflow_progress["stageResults"][workflow_progress["currentStage"]]["nextActions"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_workflow_run(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    workflow_path = _workflow_path(root)
    inferred = _infer(root, state, args.chapter_id)

    try:
        state["workflow_progress"] = build_workflow_progress(
            inferred,
            state.get("workflow_progress", {}),
            now_iso=now_iso(),
            run_mode="non-interactive" if args.non_interactive else "interactive",
            resume_from=args.resume_from,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    save_state(root, state)

    payload = {
        "saved": True,
        "mode": state["workflow_progress"]["lastRunMode"],
        "workflowFile": str(workflow_path),
        "workflow": export_workflow_payload(state["workflow_progress"], inferred),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_workflow_advance(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    inferred = _infer(root, state, args.chapter_id)
    workflow_progress = hydrate_workflow_progress(state.get("workflow_progress", {}), inferred)

    try:
        result = advance_workflow_progress(
            workflow_progress,
            inferred,
            gate_id=args.gate,
            decision=args.decision,
            feedback=args.feedback or "",
            now_iso=now_iso(),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    state["workflow_progress"] = result["workflowProgress"]
    save_state(root, state)
    payload = {
        "saved": True,
        **result,
        "workflow": export_workflow_payload(state["workflow_progress"], inferred),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_workflow_reset(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    inferred = _infer(root, state, args.chapter_id)
    workflow_progress = hydrate_workflow_progress(state.get("workflow_progress", {}), inferred)
    from_gate = args.from_gate or workflow_progress["currentStage"]

    try:
        result = reset_workflow_progress(
            workflow_progress,
            inferred,
            from_gate=from_gate,
            now_iso=now_iso(),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    state["workflow_progress"] = result["workflowProgress"]
    save_state(root, state)
    payload = {
        "saved": True,
        **result,
        "workflow": export_workflow_payload(state["workflow_progress"], inferred),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_workflow_export(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    inferred = _infer(root, state, args.chapter_id)
    workflow_progress = hydrate_workflow_progress(state.get("workflow_progress", {}), inferred)
    payload = export_workflow_payload(workflow_progress, inferred)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def register_workflow_commands(subparsers) -> None:
    workflow_parser = subparsers.add_parser("workflow", help="Inspect and drive the workflow state machine")
    workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command", required=True)

    status_parser = workflow_subparsers.add_parser("status", help="Show workflow status for a project")
    status_parser.add_argument("--root", required=True)
    status_parser.add_argument("--chapter-id")
    status_parser.set_defaults(func=command_workflow_status)

    run_parser = workflow_subparsers.add_parser("run", help="Initialize or refresh workflow.yaml from inferred state")
    run_parser.add_argument("--root", required=True)
    run_parser.add_argument("--chapter-id")
    run_parser.add_argument("--resume-from")
    run_parser.add_argument("--non-interactive", action="store_true")
    run_parser.set_defaults(func=command_workflow_run)

    advance_parser = workflow_subparsers.add_parser("advance", help="Record a gate decision and move the workflow")
    advance_parser.add_argument("--root", required=True)
    advance_parser.add_argument("--chapter-id")
    advance_parser.add_argument("--gate", required=True)
    advance_parser.add_argument("--decision", required=True, choices=["accept", "modify", "reject"])
    advance_parser.add_argument("--feedback")
    advance_parser.set_defaults(func=command_workflow_advance)

    reset_parser = workflow_subparsers.add_parser("reset", help="Reset workflow decisions from one gate onward")
    reset_parser.add_argument("--root", required=True)
    reset_parser.add_argument("--chapter-id")
    reset_parser.add_argument("--from-gate")
    reset_parser.set_defaults(func=command_workflow_reset)

    export_parser = workflow_subparsers.add_parser("export", help="Export the current workflow snapshot")
    export_parser.add_argument("--root", required=True)
    export_parser.add_argument("--chapter-id")
    export_parser.add_argument("-o", "--output")
    export_parser.set_defaults(func=command_workflow_export)
