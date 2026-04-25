from __future__ import annotations

from typing import Any, Dict, Iterable

from story_harness_cli.services.outline_guard import (
    evaluate_chapter_outline_readiness,
    evaluate_project_story_gate,
)
from story_harness_cli.services.rule_semantics import build_rule_judgement, chapter_scope_ref


WORKFLOW_STAGE_ORDER = (
    "project_contract",
    "outline_ready",
    "chapter_review_ready",
    "scene_review_ready",
    "export_ready",
)

WORKFLOW_DECISIONS = ("accept", "modify", "reject")

_STAGE_METADATA_FIELDS = (
    "lastDecision",
    "feedback",
    "decidedAt",
    "accepted",
)


def infer_workflow_status(
    state: Dict[str, Any],
    *,
    chapter_id: str | None = None,
    chapter_files: Dict[str, bool] | None = None,
) -> Dict[str, Any]:
    target_chapter_id = _resolve_target_chapter_id(state, chapter_id)
    project_gate = evaluate_project_story_gate(state)
    outline_gate = _build_outline_stage(state, target_chapter_id)
    chapter_exists = bool((chapter_files or {}).get(target_chapter_id, False)) if target_chapter_id else False

    chapter_reviews = _reviews_for_chapter(
        state.get("story_reviews", {}).get("chapterReviews", []),
        target_chapter_id,
    )
    scene_reviews = _reviews_for_chapter(
        state.get("story_reviews", {}).get("sceneReviews", []),
        target_chapter_id,
    )

    stage_results = {
        "project_contract": {
            "stageId": "project_contract",
            "completed": project_gate["ready"],
            "status": "ready" if project_gate["ready"] else "missing-project-gate",
            "missing": project_gate["missing"],
            "nextActions": project_gate["nextActions"],
        },
        "outline_ready": outline_gate,
        "chapter_review_ready": _build_chapter_review_stage(
            target_chapter_id,
            chapter_exists=chapter_exists,
            chapter_review_count=len(chapter_reviews),
        ),
        "scene_review_ready": _build_scene_review_stage(
            target_chapter_id,
            chapter_exists=chapter_exists,
            scene_review_count=len(scene_reviews),
        ),
    }
    stage_results["export_ready"] = _build_export_stage(
        target_chapter_id,
        chapter_exists=chapter_exists,
        chapter_review_count=len(chapter_reviews),
        scene_review_count=len(scene_reviews),
    )
    stage_results["project_contract"] = _attach_gate_semantics(stage_results["project_contract"], scope="project")
    stage_results["outline_ready"] = _attach_gate_semantics(stage_results["outline_ready"], scope="chapter")
    stage_results["chapter_review_ready"] = _attach_gate_semantics(stage_results["chapter_review_ready"], scope="chapter")
    stage_results["scene_review_ready"] = _attach_gate_semantics(stage_results["scene_review_ready"], scope="scene")
    stage_results["export_ready"] = _attach_gate_semantics(stage_results["export_ready"], scope="export")

    current_stage = first_incomplete_stage(stage_results)
    workflow_status = "completed" if all(item["completed"] for item in stage_results.values()) else "in_progress"

    return {
        "targetChapterId": target_chapter_id,
        "targetChapterTitle": _chapter_title(state, target_chapter_id),
        "currentStage": current_stage,
        "workflowStatus": workflow_status,
        "stageOrder": list(WORKFLOW_STAGE_ORDER),
        "projectGate": project_gate,
        "stageResults": stage_results,
        "currentGateDecision": stage_results[current_stage]["gateDecision"],
        "currentRuleJudgements": stage_results[current_stage]["ruleJudgements"],
        "nextActions": stage_results[current_stage]["nextActions"],
    }


def hydrate_workflow_progress(
    workflow_progress: Dict[str, Any],
    inferred: Dict[str, Any],
) -> Dict[str, Any]:
    current_stage = workflow_progress.get("currentStage") or inferred["currentStage"]
    workflow_status = workflow_progress.get("workflowStatus") or inferred["workflowStatus"]
    stage_results = _merge_stage_results(
        inferred["stageResults"],
        workflow_progress.get("stageResults", {}),
    )
    if current_stage not in stage_results:
        current_stage = inferred["currentStage"]
    return {
        "currentStage": current_stage,
        "targetChapterId": workflow_progress.get("targetChapterId") or inferred["targetChapterId"],
        "workflowStatus": workflow_status,
        "gateHistory": list(workflow_progress.get("gateHistory", [])),
        "stageResults": stage_results,
        "updatedAt": workflow_progress.get("updatedAt", ""),
        "lastRunMode": workflow_progress.get("lastRunMode", ""),
    }


def build_workflow_progress(
    inferred: Dict[str, Any],
    existing: Dict[str, Any] | None = None,
    *,
    now_iso: str,
    run_mode: str,
    resume_from: str | None = None,
) -> Dict[str, Any]:
    hydrated = hydrate_workflow_progress(existing or {}, inferred)
    if resume_from:
        _validate_stage_id(resume_from)
        reset_payload = reset_workflow_progress(
            hydrated,
            inferred,
            from_gate=resume_from,
            now_iso=now_iso,
        )
        hydrated = reset_payload["workflowProgress"]

    hydrated["targetChapterId"] = inferred["targetChapterId"]
    hydrated["stageResults"] = _merge_stage_results(
        inferred["stageResults"],
        hydrated.get("stageResults", {}),
    )
    hydrated["currentStage"] = resume_from or inferred["currentStage"]
    hydrated["workflowStatus"] = (
        "completed" if hydrated["currentStage"] == WORKFLOW_STAGE_ORDER[-1] and inferred["workflowStatus"] == "completed" else "in_progress"
    )
    hydrated["updatedAt"] = now_iso
    hydrated["lastRunMode"] = run_mode
    return hydrated


def advance_workflow_progress(
    workflow_progress: Dict[str, Any],
    inferred: Dict[str, Any],
    *,
    gate_id: str,
    decision: str,
    feedback: str,
    now_iso: str,
) -> Dict[str, Any]:
    _validate_stage_id(gate_id)
    if decision not in WORKFLOW_DECISIONS:
        raise ValueError(f"未知 decision: {decision}")

    stage_results = _merge_stage_results(inferred["stageResults"], workflow_progress.get("stageResults", {}))
    current_stage = workflow_progress.get("currentStage") or inferred["currentStage"]
    if gate_id != current_stage:
        raise ValueError(f"当前 gate 为 {current_stage}，不能直接推进 {gate_id}")

    gate_result = stage_results[gate_id]
    if decision == "accept" and not gate_result.get("completed", False):
        raise ValueError(f"当前 gate 尚未满足推进条件: {gate_id}")

    gate_result["lastDecision"] = decision
    gate_result["feedback"] = feedback
    gate_result["decidedAt"] = now_iso
    gate_result["accepted"] = decision == "accept"

    next_stage = gate_id
    workflow_status = "in_progress"
    if decision == "accept":
        next_stage = next_stage_after(gate_id)
        if next_stage == gate_id:
            workflow_status = "completed"
    elif decision == "modify":
        workflow_status = "needs_changes"
    else:
        workflow_status = "rejected"

    gate_history = list(workflow_progress.get("gateHistory", []))
    gate_history.append(
        {
            "gateId": gate_id,
            "decision": decision,
            "feedback": feedback,
            "timestamp": now_iso,
        }
    )

    updated = {
        "currentStage": next_stage,
        "targetChapterId": workflow_progress.get("targetChapterId") or inferred["targetChapterId"],
        "workflowStatus": workflow_status,
        "gateHistory": gate_history,
        "stageResults": stage_results,
        "updatedAt": now_iso,
        "lastRunMode": workflow_progress.get("lastRunMode", ""),
    }
    return {
        "workflowProgress": updated,
        "advancedGate": gate_id,
        "decision": decision,
        "currentStage": updated["currentStage"],
        "workflowStatus": updated["workflowStatus"],
    }


def reset_workflow_progress(
    workflow_progress: Dict[str, Any],
    inferred: Dict[str, Any],
    *,
    from_gate: str,
    now_iso: str,
) -> Dict[str, Any]:
    _validate_stage_id(from_gate)
    stage_results = _merge_stage_results(inferred["stageResults"], workflow_progress.get("stageResults", {}))
    reset_index = _stage_index(from_gate)

    for stage_id in WORKFLOW_STAGE_ORDER[reset_index:]:
        for field in _STAGE_METADATA_FIELDS:
            stage_results[stage_id].pop(field, None)

    gate_history = [
        item
        for item in workflow_progress.get("gateHistory", [])
        if _stage_index(item.get("gateId", from_gate)) < reset_index
    ]

    updated = {
        "currentStage": from_gate,
        "targetChapterId": workflow_progress.get("targetChapterId") or inferred["targetChapterId"],
        "workflowStatus": "in_progress",
        "gateHistory": gate_history,
        "stageResults": stage_results,
        "updatedAt": now_iso,
        "lastRunMode": workflow_progress.get("lastRunMode", ""),
    }
    return {
        "workflowProgress": updated,
        "resetFromGate": from_gate,
        "currentStage": from_gate,
        "workflowStatus": "in_progress",
    }


def export_workflow_payload(
    workflow_progress: Dict[str, Any],
    inferred: Dict[str, Any],
) -> Dict[str, Any]:
    hydrated = hydrate_workflow_progress(workflow_progress, inferred)
    current_stage = hydrated["currentStage"]
    return {
        "currentStage": current_stage,
        "workflowStatus": hydrated["workflowStatus"],
        "targetChapterId": hydrated["targetChapterId"],
        "targetChapterTitle": inferred["targetChapterTitle"],
        "inferredCurrentStage": inferred["currentStage"],
        "inferredWorkflowStatus": inferred["workflowStatus"],
        "stageOrder": list(WORKFLOW_STAGE_ORDER),
        "gateHistory": hydrated["gateHistory"],
        "stageResults": hydrated["stageResults"],
        "currentGateDecision": hydrated["stageResults"][current_stage]["gateDecision"],
        "currentRuleJudgements": hydrated["stageResults"][current_stage]["ruleJudgements"],
        "nextActions": hydrated["stageResults"][current_stage]["nextActions"],
        "updatedAt": hydrated["updatedAt"],
        "lastRunMode": hydrated["lastRunMode"],
    }


def first_incomplete_stage(stage_results: Dict[str, Dict[str, Any]]) -> str:
    for stage_id in WORKFLOW_STAGE_ORDER:
        if not stage_results[stage_id]["completed"]:
            return stage_id
    return WORKFLOW_STAGE_ORDER[-1]


def next_stage_after(stage_id: str) -> str:
    index = _stage_index(stage_id)
    if index >= len(WORKFLOW_STAGE_ORDER) - 1:
        return stage_id
    return WORKFLOW_STAGE_ORDER[index + 1]


def _resolve_target_chapter_id(state: Dict[str, Any], chapter_id: str | None) -> str | None:
    if chapter_id:
        return chapter_id
    active_chapter_id = state.get("project", {}).get("activeChapterId")
    if active_chapter_id:
        return active_chapter_id
    for item in state.get("outline", {}).get("chapters", []):
        candidate = item.get("id")
        if candidate:
            return candidate
    return None


def _chapter_title(state: Dict[str, Any], chapter_id: str | None) -> str:
    if not chapter_id:
        return ""
    for item in state.get("outline", {}).get("chapters", []):
        if item.get("id") == chapter_id:
            return item.get("title", chapter_id)
    return chapter_id


def _build_outline_stage(state: Dict[str, Any], chapter_id: str | None) -> Dict[str, Any]:
    if not chapter_id:
        return {
            "stageId": "outline_ready",
            "completed": False,
            "status": "missing-chapter-entry",
            "missing": [{"code": "missing-chapter-id", "message": "缺少可评估的目标章节"}],
            "nextActions": ["先在项目中明确 activeChapterId 或创建至少一个 outline chapter"],
            "chapterId": None,
            "title": "",
        }

    report = evaluate_chapter_outline_readiness(
        state,
        chapter_id,
        require_beats=True,
        require_scene_plans=True,
        require_project_gate=True,
    )
    return {
        "stageId": "outline_ready",
        "completed": report["ready"],
        "status": report["status"],
        "missing": report["missing"],
        "nextActions": report["nextActions"],
        "chapterId": report["chapterId"],
        "title": report["title"],
    }


def _build_chapter_review_stage(
    chapter_id: str | None,
    *,
    chapter_exists: bool,
    chapter_review_count: int,
) -> Dict[str, Any]:
    missing = []
    next_actions = []
    if not chapter_exists:
        missing.append({"code": "missing-chapter-file", "message": "缺少目标章节正文文件"})
        next_actions.append("先补正文章节文件，再进入 review chapter")
    elif chapter_review_count == 0:
        missing.append({"code": "missing-chapter-review", "message": "缺少章节级评审结果"})
        next_actions.append("先运行 review chapter，为目标章节生成章节级评审")

    return {
        "stageId": "chapter_review_ready",
        "completed": chapter_exists and chapter_review_count > 0,
        "status": (
            "ready"
            if chapter_exists and chapter_review_count > 0
            else ("missing-chapter-file" if not chapter_exists else "missing-chapter-review")
        ),
        "chapterId": chapter_id,
        "chapterFileExists": chapter_exists,
        "chapterReviewCount": chapter_review_count,
        "missing": missing,
        "nextActions": next_actions,
    }


def _build_scene_review_stage(
    chapter_id: str | None,
    *,
    chapter_exists: bool,
    scene_review_count: int,
) -> Dict[str, Any]:
    missing = []
    next_actions = []
    if not chapter_exists:
        missing.append({"code": "missing-chapter-file", "message": "缺少目标章节正文文件"})
        next_actions.append("先补正文章节文件，再进入 review scene")
    elif scene_review_count == 0:
        missing.append({"code": "missing-scene-review", "message": "缺少场景级评审结果"})
        next_actions.append("先运行 review scene，为目标章节生成场景级评审")

    return {
        "stageId": "scene_review_ready",
        "completed": chapter_exists and scene_review_count > 0,
        "status": (
            "ready"
            if chapter_exists and scene_review_count > 0
            else ("missing-chapter-file" if not chapter_exists else "missing-scene-review")
        ),
        "chapterId": chapter_id,
        "chapterFileExists": chapter_exists,
        "sceneReviewCount": scene_review_count,
        "missing": missing,
        "nextActions": next_actions,
    }


def _build_export_stage(
    chapter_id: str | None,
    *,
    chapter_exists: bool,
    chapter_review_count: int,
    scene_review_count: int,
) -> Dict[str, Any]:
    missing = []
    next_actions = []
    if not chapter_exists:
        missing.append({"code": "missing-chapter-file", "message": "缺少目标章节正文文件"})
        next_actions.append("先补正文章节文件")
    if chapter_review_count == 0:
        missing.append({"code": "missing-chapter-review", "message": "缺少章节级评审结果"})
        next_actions.append("先完成 review chapter")
    if scene_review_count == 0:
        missing.append({"code": "missing-scene-review", "message": "缺少场景级评审结果"})
        next_actions.append("先完成 review scene")
    if chapter_exists and chapter_review_count > 0 and scene_review_count > 0:
        next_actions.append("当前章节已具备导出前的最小 review 信号，可继续 export 或转入下一章")

    completed = chapter_exists and chapter_review_count > 0 and scene_review_count > 0
    return {
        "stageId": "export_ready",
        "completed": completed,
        "status": "ready" if completed else "pending-review-signals",
        "chapterId": chapter_id,
        "chapterFileExists": chapter_exists,
        "chapterReviewCount": chapter_review_count,
        "sceneReviewCount": scene_review_count,
        "missing": missing,
        "nextActions": next_actions,
    }


def _attach_gate_semantics(stage_result: Dict[str, Any], *, scope: str) -> Dict[str, Any]:
    enriched = dict(stage_result)
    chapter_id = stage_result.get("chapterId")
    scope_ref = chapter_scope_ref(chapter_id) if chapter_id else {}
    next_actions = [str(item) for item in stage_result.get("nextActions", []) if item]
    judgements: list[Dict[str, Any]] = []
    for item in stage_result.get("missing", []):
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("code", "workflow-gate-blocked"))
        message = str(item.get("message", stage_result.get("status", "当前 workflow gate 尚未满足推进条件")))
        judgements.append(
            build_rule_judgement(
                rule_id=rule_id,
                source="core",
                scope=scope,
                kind="gate",
                severity="warning",
                message=message,
                suggestion=next_actions[0] if next_actions else "",
                evidence=[message],
                scope_ref=scope_ref,
                payload=item,
                tags=["workflow", str(stage_result.get("stageId", ""))],
            )
        )
    enriched["ruleJudgements"] = judgements
    enriched["gateDecision"] = {
        "gateId": stage_result.get("stageId", ""),
        "status": "ready" if stage_result.get("completed") else "blocked",
        "blockingRules": [item["ruleId"] for item in judgements],
        "notes": next_actions[:3],
    }
    return enriched


def _reviews_for_chapter(reviews: Iterable[Dict[str, Any]], chapter_id: str | None) -> list[Dict[str, Any]]:
    if not chapter_id:
        return []
    return [item for item in reviews if item.get("chapterId") == chapter_id]


def _merge_stage_results(
    inferred_stage_results: Dict[str, Dict[str, Any]],
    existing_stage_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for stage_id, inferred in inferred_stage_results.items():
        combined = dict(inferred)
        existing = existing_stage_results.get(stage_id, {})
        for field in _STAGE_METADATA_FIELDS:
            if field in existing:
                combined[field] = existing[field]
        merged[stage_id] = combined
    return merged


def _stage_index(stage_id: str) -> int:
    _validate_stage_id(stage_id)
    return WORKFLOW_STAGE_ORDER.index(stage_id)


def _validate_stage_id(stage_id: str) -> None:
    if stage_id not in WORKFLOW_STAGE_ORDER:
        raise ValueError(f"未知 workflow gate: {stage_id}")
