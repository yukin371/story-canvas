from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_harness_cli.commands.project_support import build_chapter_start_guide, build_project_advisories
from story_harness_cli.commands.review_support import build_review_preflight_payload
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
    infer_volume_preflight_workflow,
    infer_workflow_status,
    latest_volume_self_review,
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


def _validate_scope_args(chapter_id: str | None, volume_id: str | None) -> None:
    if chapter_id and volume_id:
        raise SystemExit("`--chapter-id` 与 `--volume-id` 不能同时使用")


def _append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _build_volume_orchestration_plan(root: Path, workflow: dict[str, Any]) -> dict[str, Any]:
    volume_id = str(workflow.get("volumeId", ""))
    root_arg = f'"{root}"'
    volume_arg = f"--volume-id {volume_id}" if volume_id else ""
    current_stage = str(workflow.get("currentStage", ""))
    commands: list[str] = []
    notes: list[str] = []

    def add(command: str) -> None:
        _append_once(commands, command)

    add(f"story-canvas workflow status --root {root_arg} {volume_arg}".strip())

    if current_stage == "volume_preflight_ready":
        notes.append("当前优先处理卷级预检输入；缺章节文件时需先补正文文件。")
        add(f"story-canvas review preflight --root {root_arg} {volume_arg}".strip())
    elif current_stage == "volume_tooling_gate":
        notes.append("当前优先处理工具侧阻塞项；先看卷级 mention plan，再回到 workflow status 复检。")
        add(f"story-canvas entity mention-plan --root {root_arg} {volume_arg}".strip())
        add(f"story-canvas review preflight --root {root_arg} {volume_arg}".strip())
    elif current_stage == "human_review_ready":
        volume_self = workflow.get("volumeSelfReview", {})
        if not volume_self.get("present"):
            draft_path = root / "reviews" / f"{volume_id}-self-review.draft.yaml"
            notes.append("当前缺卷级 AI 自审；先生成 draft，补齐后再写入卷级自审结果。")
            add(f"story-canvas review volume-self-template --root {root_arg} {volume_arg} --output \"{draft_path}\"".strip())
            add(f"story-canvas review volume-self --root {root_arg} {volume_arg} --input \"{draft_path}\"".strip())
        elif workflow.get("workflowStatus") == "completed":
            packet_path = root / "reviews" / f"{volume_id}-review-packet.md"
            notes.append("卷级 gate 已通过；刷新审查包后进入人工审查。")
            add(f"story-canvas export --root {root_arg} {volume_arg} --format review-packet --output \"{packet_path}\"".strip())
        else:
            notes.append("卷级自审仍有阻塞项；按 changeRequestDrafts 修稿后重新生成并写入自审结果。")
            add(f"story-canvas review volume-self-template --root {root_arg} {volume_arg}".strip())
            add(f"story-canvas review volume-self --root {root_arg} {volume_arg} --input <volume-self-review.yaml>".strip())

    add(f"story-canvas workflow status --root {root_arg} {volume_arg}".strip())
    return {
        "scope": "volume",
        "volumeId": volume_id,
        "currentStage": current_stage,
        "workflowStatus": workflow.get("workflowStatus", ""),
        "notes": notes,
        "suggestedCommands": commands,
    }


def _build_volume_workflow_payload(root: Path, state: dict[str, Any], volume_id: str) -> dict[str, Any]:
    preflight_payload = build_review_preflight_payload(root, state, volume_id=volume_id)
    volume_self_review = latest_volume_self_review(state.get("story_reviews", {}), volume_id)
    workflow = infer_volume_preflight_workflow(preflight_payload, volume_self_review)
    orchestration_plan = _build_volume_orchestration_plan(root, workflow)
    return {
        "scope": "volume",
        "stateSource": "inferred",
        "workflowFile": "",
        "workflowFileExists": False,
        "volumeId": workflow["volumeId"],
        "volumeTitle": workflow["volumeTitle"],
        "chapterCount": workflow["chapterCount"],
        "preflight": preflight_payload,
        "latestVolumeSelfReview": volume_self_review or None,
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
        "orchestrationPlan": orchestration_plan,
        **workflow,
    }


def command_workflow_status(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    _validate_scope_args(args.chapter_id, args.volume_id)
    if args.volume_id:
        payload = _build_volume_workflow_payload(root, state, args.volume_id)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
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
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
        "targetChapterTitle": inferred["targetChapterTitle"],
        **workflow_progress,
        "stageOrder": inferred["stageOrder"],
        "currentGateDecision": workflow_progress["stageResults"][workflow_progress["currentStage"]]["gateDecision"],
        "currentRuleJudgements": workflow_progress["stageResults"][workflow_progress["currentStage"]]["ruleJudgements"],
        "nextActions": workflow_progress["stageResults"][workflow_progress["currentStage"]]["nextActions"],
        "startGuide": (
            build_chapter_start_guide(
                root,
                workflow_progress.get("targetChapterId") or args.chapter_id or "",
                missing_codes=list(
                    workflow_progress["stageResults"][workflow_progress["currentStage"]]["gateDecision"].get(
                        "blockingRules", []
                    )
                ),
            )
            if (workflow_progress.get("targetChapterId") or args.chapter_id)
            else {}
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_workflow_run(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    _validate_scope_args(args.chapter_id, args.volume_id)
    if args.volume_id:
        raise SystemExit("当前 volume scope 仅支持 workflow status/export，只读卷级 gate 尚未接入持久化 run")
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
    _validate_scope_args(args.chapter_id, args.volume_id)
    if args.volume_id:
        raise SystemExit("当前 volume scope 仅支持 workflow status/export，只读卷级 gate 尚未接入 advance")
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
    _validate_scope_args(args.chapter_id, args.volume_id)
    if args.volume_id:
        raise SystemExit("当前 volume scope 仅支持 workflow status/export，只读卷级 gate 尚未接入 reset")
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
    _validate_scope_args(args.chapter_id, args.volume_id)
    if args.volume_id:
        payload = _build_volume_workflow_payload(root, state, args.volume_id)
    else:
        inferred = _infer(root, state, args.chapter_id)
        workflow_progress = hydrate_workflow_progress(state.get("workflow_progress", {}), inferred)
        payload = export_workflow_payload(workflow_progress, inferred)
        payload["projectAdvisories"] = build_project_advisories(root, include_prd_content=True)

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
    status_parser.add_argument("--volume-id")
    status_parser.set_defaults(func=command_workflow_status)

    run_parser = workflow_subparsers.add_parser("run", help="Initialize or refresh workflow.yaml from inferred state")
    run_parser.add_argument("--root", required=True)
    run_parser.add_argument("--chapter-id")
    run_parser.add_argument("--volume-id")
    run_parser.add_argument("--resume-from")
    run_parser.add_argument("--non-interactive", action="store_true")
    run_parser.set_defaults(func=command_workflow_run)

    advance_parser = workflow_subparsers.add_parser("advance", help="Record a gate decision and move the workflow")
    advance_parser.add_argument("--root", required=True)
    advance_parser.add_argument("--chapter-id")
    advance_parser.add_argument("--volume-id")
    advance_parser.add_argument("--gate", required=True)
    advance_parser.add_argument("--decision", required=True, choices=["accept", "modify", "reject"])
    advance_parser.add_argument("--feedback")
    advance_parser.set_defaults(func=command_workflow_advance)

    reset_parser = workflow_subparsers.add_parser("reset", help="Reset workflow decisions from one gate onward")
    reset_parser.add_argument("--root", required=True)
    reset_parser.add_argument("--chapter-id")
    reset_parser.add_argument("--volume-id")
    reset_parser.add_argument("--from-gate")
    reset_parser.set_defaults(func=command_workflow_reset)

    export_parser = workflow_subparsers.add_parser("export", help="Export the current workflow snapshot")
    export_parser.add_argument("--root", required=True)
    export_parser.add_argument("--chapter-id")
    export_parser.add_argument("--volume-id")
    export_parser.add_argument("-o", "--output")
    export_parser.set_defaults(func=command_workflow_export)
