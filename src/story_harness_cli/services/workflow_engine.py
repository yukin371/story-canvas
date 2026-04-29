from __future__ import annotations

from typing import Any, Dict, Iterable

from story_harness_cli.services.outline_guard import (
    evaluate_chapter_outline_readiness,
    evaluate_project_story_gate,
)
from story_harness_cli.services.rule_semantics import build_rule_judgement, chapter_scope_ref
from story_harness_cli.utils import stable_hash


WORKFLOW_STAGE_ORDER = (
    "project_contract",
    "outline_ready",
    "context_ready",
    "chapter_review_ready",
    "scene_review_ready",
    "export_ready",
)
VOLUME_WORKFLOW_STAGE_ORDER = (
    "volume_preflight_ready",
    "volume_tooling_gate",
    "human_review_ready",
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
        "context_ready": _build_context_stage(
            state,
            target_chapter_id,
            chapter_exists=chapter_exists,
        ),
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
    stage_results["context_ready"] = _attach_gate_semantics(stage_results["context_ready"], scope="chapter")
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
    if _stage_index(current_stage) > _stage_index(inferred["currentStage"]):
        current_stage = inferred["currentStage"]
    if workflow_status == "completed" and inferred["workflowStatus"] != "completed":
        workflow_status = inferred["workflowStatus"]
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


def infer_volume_preflight_workflow(
    preflight_payload: Dict[str, Any],
    volume_self_review: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if preflight_payload.get("scope") != "volume":
        raise ValueError("volume workflow 需要 volume scope 的 preflight payload")

    summary = preflight_payload.get("summary", {})
    stage_results = {
        "volume_preflight_ready": _attach_volume_gate_semantics(
            _build_volume_preflight_stage(preflight_payload),
            scope="volume",
        ),
        "volume_tooling_gate": _attach_volume_gate_semantics(
            _build_volume_tooling_gate(preflight_payload),
            scope="volume",
        ),
        "human_review_ready": _attach_volume_gate_semantics(
            _build_volume_human_review_gate(
                preflight_payload,
                volume_self_review or {},
            ),
            scope="volume",
        ),
    }
    current_stage = _first_incomplete_stage(stage_results, VOLUME_WORKFLOW_STAGE_ORDER)
    workflow_status = "completed" if all(item["completed"] for item in stage_results.values()) else "in_progress"
    return {
        "scope": "volume",
        "workflowKind": "volume_preflight_gate",
        "volumeId": preflight_payload.get("volumeId", ""),
        "volumeTitle": preflight_payload.get("volumeTitle", ""),
        "chapterCount": preflight_payload.get("chapterCount", 0),
        "currentStage": current_stage,
        "workflowStatus": workflow_status,
        "stageOrder": list(VOLUME_WORKFLOW_STAGE_ORDER),
        "stageResults": stage_results,
        "currentGateDecision": stage_results[current_stage]["gateDecision"],
        "currentRuleJudgements": stage_results[current_stage]["ruleJudgements"],
        "nextActions": stage_results[current_stage]["nextActions"],
        "changeRequestDrafts": _build_volume_change_request_drafts(
            current_stage=current_stage,
            stage_result=stage_results[current_stage],
            preflight_payload=preflight_payload,
            volume_self_review=volume_self_review or {},
        ),
        "volumeStructureCheck": preflight_payload.get("volumeStructureCheck", {}),
        "preflightSummary": {
            "chapterPreflightCount": summary.get("chapterPreflightCount", 0),
            "chapterFileMissingCount": summary.get("chapterFileMissingCount", 0),
            "mentionActionCount": summary.get("mentionActionCount", 0),
            "dueForeshadowCount": summary.get("dueForeshadowCount", 0),
            "overdueForeshadowCount": summary.get("overdueForeshadowCount", 0),
            "unresolvedWithoutScheduleCount": summary.get("unresolvedWithoutScheduleCount", 0),
            "worldOnboardingGapCount": summary.get("worldOnboardingGapCount", 0),
            "factionRegistryGapCount": summary.get("factionRegistryGapCount", 0),
            "capabilityTaskRiskCount": summary.get("capabilityTaskRiskCount", 0),
            "powerProgressionConflictCount": summary.get("powerProgressionConflictCount", 0),
        },
        "volumeSelfReview": {
            "present": bool(volume_self_review),
            "generatedAt": (volume_self_review or {}).get("generatedAt", ""),
            "closureStatus": (volume_self_review or {}).get("conclusion", {}).get("closureStatus", ""),
            "declaredAllowHumanReview": (volume_self_review or {}).get("conclusion", {}).get("allowHumanReview"),
            "finalAllowHumanReview": (volume_self_review or {}).get("finalAllowHumanReview"),
            "editorPassCompleted": (volume_self_review or {}).get("editorPass", {}).get("completed"),
            "editorMode": (volume_self_review or {}).get("editorPass", {}).get("mode", ""),
            "editorContextIsolation": (volume_self_review or {}).get("editorPass", {}).get("contextIsolation", ""),
            "editorVerdict": (volume_self_review or {}).get("editorAssessment", {}).get("overallVerdict", ""),
            "gateFailureCount": len((volume_self_review or {}).get("gateFailures", [])),
            "repairCoverageStatus": (volume_self_review or {}).get("repairCoverage", {}).get("status", ""),
            "weakDimensionLabels": list(
                (volume_self_review or {}).get("repairCoverage", {}).get("weakDimensionLabels", [])
            ),
            "uncoveredWeakDimensionLabels": list(
                (volume_self_review or {}).get("repairCoverage", {}).get("uncoveredWeakDimensionLabels", [])
            ),
        },
    }


def first_incomplete_stage(stage_results: Dict[str, Dict[str, Any]]) -> str:
    for stage_id in WORKFLOW_STAGE_ORDER:
        if not stage_results[stage_id]["completed"]:
            return stage_id
    return WORKFLOW_STAGE_ORDER[-1]


def _first_incomplete_stage(stage_results: Dict[str, Dict[str, Any]], stage_order: Iterable[str]) -> str:
    ordered = list(stage_order)
    for stage_id in ordered:
        if not stage_results[stage_id]["completed"]:
            return stage_id
    return ordered[-1]


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


def _build_context_stage(
    state: Dict[str, Any],
    chapter_id: str | None,
    *,
    chapter_exists: bool,
) -> Dict[str, Any]:
    context_lens = state.get("context_lens", {})
    matching_lens = next(
        (
            item
            for item in reversed(context_lens.get("lenses", []))
            if item.get("chapterId") == chapter_id
        ),
        None,
    )

    missing = []
    next_actions = []
    if not chapter_exists:
        missing.append({"code": "missing-chapter-file", "message": "缺少目标章节正文文件"})
        next_actions.append("先补正文章节文件，再进入 context refresh")
    elif not matching_lens:
        missing.append({"code": "missing-context-refresh", "message": "缺少当前章节的上下文刷新结果"})
        next_actions.extend(
            [
                "先运行 chapter analyze，生成本章分析基础",
                "再运行 chapter suggest / review apply / projection apply，把结构化建议与投影入账",
                "最后运行 context refresh，为目标章节生成可复用上下文",
            ]
        )

    completed = chapter_exists and bool(matching_lens)
    return {
        "stageId": "context_ready",
        "completed": completed,
        "status": "ready" if completed else ("missing-chapter-file" if not chapter_exists else "missing-context-refresh"),
        "chapterId": chapter_id,
        "chapterFileExists": chapter_exists,
        "contextExists": bool(matching_lens),
        "contextUpdatedAt": matching_lens.get("updatedAt", "") if matching_lens else "",
        "missing": missing,
        "nextActions": next_actions,
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
    stage_id = str(stage_result.get("stageId", ""))
    judgements: list[Dict[str, Any]] = []
    for item in stage_result.get("missing", []):
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("code", "workflow-gate-blocked"))
        message = str(item.get("message", stage_result.get("status", "当前 workflow gate 尚未满足推进条件")))
        tags = ["workflow"]
        if stage_id:
            tags.append(stage_id)
        judgements.append(
            build_rule_judgement(
                rule_id=rule_id,
                scope=scope,
                kind="gate",
                severity="warning",
                message=message,
                suggestion=next_actions[0] if next_actions else "",
                evidence=[message],
                scope_ref=scope_ref,
                payload=item,
                tags=tags,
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


def _build_volume_preflight_stage(preflight_payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = preflight_payload.get("summary", {})
    missing_count = int(summary.get("chapterFileMissingCount", 0) or 0)
    missing: list[Dict[str, Any]] = []
    next_actions: list[str] = []
    if missing_count > 0:
        missing.append(
            {
                "code": "missing-volume-chapter-file",
                "message": f"当前卷仍有 {missing_count} 个章节文件缺失，无法完成卷级预检。",
            }
        )
        next_actions.append("先补齐缺失的章节文件，再重新运行 review preflight / workflow status --volume-id")
    else:
        next_actions.append("卷级预检已生成，可继续查看工具侧阻塞项并准备卷级 AI 自审。")
    return {
        "stageId": "volume_preflight_ready",
        "completed": missing_count == 0,
        "status": "ready" if missing_count == 0 else "missing-chapter-files",
        "volumeId": preflight_payload.get("volumeId", ""),
        "volumeTitle": preflight_payload.get("volumeTitle", ""),
        "missing": missing,
        "nextActions": next_actions,
    }


def _build_volume_tooling_gate(preflight_payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = preflight_payload.get("summary", {})
    issue_specs = [
        (
            "volume-mention-hygiene-pending",
            int(summary.get("mentionActionCount", 0) or 0),
            "当前卷仍有 {count} 项 mention hygiene 动作未闭环。",
            "先处理实体/世界名词的包裹或建档闭环，再做卷级 AI 自审。",
        ),
        (
            "volume-due-foreshadow-pending",
            int(summary.get("dueForeshadowCount", 0) or 0),
            "当前卷有 {count} 个伏笔已经到窗但尚未处理。",
            "先确认这些到窗伏笔是要兑现、延后还是明确接受风险。",
        ),
        (
            "volume-overdue-foreshadow",
            int(summary.get("overdueForeshadowCount", 0) or 0),
            "当前卷有 {count} 个伏笔已经逾期未回收。",
            "先补回收、重排窗口或显式记录为接受风险。",
        ),
        (
            "volume-unscheduled-foreshadow",
            int(summary.get("unresolvedWithoutScheduleCount", 0) or 0),
            "当前卷有 {count} 个未排期伏笔。",
            "先补最小 payoff window，避免卷级自审时无法判断是否应回收。",
        ),
        (
            "volume-world-onboarding-gap",
            int(summary.get("worldOnboardingGapCount", 0) or 0),
            "当前卷累计暴露 {count} 个世界 onboarding 缺口。",
            "先补底层设定、制度代价或世界规则解释，再进入整卷审查。",
        ),
        (
            "volume-faction-registry-gap",
            int(summary.get("factionRegistryGapCount", 0) or 0),
            "当前卷累计暴露 {count} 个势力建档薄弱项。",
            "先补势力层级、地盘或状态，避免势力行为逻辑失真。",
        ),
        (
            "volume-capability-task-risk",
            int(summary.get("capabilityTaskRiskCount", 0) or 0),
            "当前卷累计暴露 {count} 个能力与任务门槛风险。",
            "先补保护条件、例外说明或调整任务强度。",
        ),
        (
            "volume-power-progression-conflict",
            int(summary.get("powerProgressionConflictCount", 0) or 0),
            "当前卷累计暴露 {count} 个突破链冲突。",
            "先修正战力推进链或补足破格条件。",
        ),
    ]

    missing: list[Dict[str, Any]] = []
    next_actions: list[str] = []
    for code, count, message_template, suggestion in issue_specs:
        if count <= 0:
            continue
        missing.append(
            {
                "code": code,
                "message": message_template.format(count=count),
                "count": count,
            }
        )
        next_actions.append(suggestion)

    if not next_actions:
        next_actions.append("工具侧卷级预检已清，可继续执行卷级 AI 自审，并在必要修正后进入人工审查。")

    return {
        "stageId": "volume_tooling_gate",
        "completed": not missing,
        "status": "ready" if not missing else "blocked-by-volume-signals",
        "volumeId": preflight_payload.get("volumeId", ""),
        "volumeTitle": preflight_payload.get("volumeTitle", ""),
        "missing": missing,
        "nextActions": next_actions,
    }


def _build_volume_human_review_gate(
    preflight_payload: Dict[str, Any],
    volume_self_review: Dict[str, Any],
) -> Dict[str, Any]:
    if not volume_self_review:
        return {
            "stageId": "human_review_ready",
            "completed": False,
            "status": "missing-volume-self-review",
            "volumeId": preflight_payload.get("volumeId", ""),
            "volumeTitle": preflight_payload.get("volumeTitle", ""),
            "missing": [
                {
                    "code": "missing-volume-self-review",
                    "message": "当前卷还没有卷级 AI 自审结果，不能进入人工审查。",
                }
            ],
            "nextActions": [
                "先执行 review volume-self 持久化卷级 AI 自审结果，再决定是否进入人工审查。"
            ],
        }

    gate_failures = []
    for item in volume_self_review.get("gateFailures", []):
        if isinstance(item, dict):
            gate_failures.append(item)

    repair_coverage = volume_self_review.get("repairCoverage", {})
    uncovered_weak_labels = [
        str(item).strip()
        for item in repair_coverage.get("uncoveredWeakDimensionLabels", [])
        if str(item).strip()
    ]
    weak_labels = [
        str(item).strip()
        for item in repair_coverage.get("weakDimensionLabels", [])
        if str(item).strip()
    ]
    if uncovered_weak_labels:
        gate_failures.append(
            {
                "code": "volume-self-review-repair-coverage-incomplete",
                "message": (
                    "卷级自审仍有未覆盖弱项："
                    + " / ".join(uncovered_weak_labels)
                    + "；当前 issues / repairSuggestions 还没有明确对应修复动作。"
                ),
                "uncoveredWeakDimensionLabels": uncovered_weak_labels,
            }
        )

    if gate_failures:
        next_actions: list[str] = []
        gate_failure_codes = {
            str(item.get("code", "")).strip()
            for item in gate_failures
            if isinstance(item, dict)
        }
        if "volume-self-review-editor-pass-incomplete" in gate_failure_codes:
            next_actions.append(
                "先补做独立编辑审查；若宿主支持 subagent 或新线程，优先使用无上下文独立通道。"
            )
        if "volume-self-review-editor-verdict-blocking" in gate_failure_codes:
            next_actions.append(
                "先处理独立编辑判定为 revise/block 的问题，再重新提交卷级自审。"
            )
        if uncovered_weak_labels:
            next_actions.append(
                "先把以下弱项明确写进 issues / repairSuggestions 并落实修稿："
                + " / ".join(uncovered_weak_labels)
                + "。"
            )
        elif weak_labels:
            next_actions.append(
                "优先复核当前低分弱项是否已被真实修复："
                + " / ".join(weak_labels)
                + "。"
            )
        next_actions.extend(str(item) for item in volume_self_review.get("repairSuggestions", []) if str(item).strip())
        deduped_next_actions: list[str] = []
        for item in next_actions:
            if item not in deduped_next_actions:
                deduped_next_actions.append(item)
        next_actions = deduped_next_actions
        if not next_actions:
            next_actions = [
                "先根据卷级自审暴露的问题修稿并复检，再重新提交卷级 AI 自审。"
            ]
        return {
            "stageId": "human_review_ready",
            "completed": False,
            "status": "blocked-by-volume-self-review",
            "volumeId": preflight_payload.get("volumeId", ""),
            "volumeTitle": preflight_payload.get("volumeTitle", ""),
            "generatedAt": volume_self_review.get("generatedAt", ""),
            "finalAllowHumanReview": volume_self_review.get("finalAllowHumanReview", False),
            "missing": gate_failures,
            "nextActions": next_actions,
        }

    return {
        "stageId": "human_review_ready",
        "completed": True,
        "status": "ready",
        "volumeId": preflight_payload.get("volumeId", ""),
        "volumeTitle": preflight_payload.get("volumeTitle", ""),
        "generatedAt": volume_self_review.get("generatedAt", ""),
        "finalAllowHumanReview": volume_self_review.get("finalAllowHumanReview", False),
        "missing": [],
        "nextActions": [
            "卷级 AI 自审已通过，可导出 review-packet --volume-id 并进入人工审查。"
        ],
    }


def _build_volume_change_request_drafts(
    *,
    current_stage: str,
    stage_result: Dict[str, Any],
    preflight_payload: Dict[str, Any],
    volume_self_review: Dict[str, Any],
) -> list[Dict[str, Any]]:
    if stage_result.get("completed"):
        return []
    volume_id = str(preflight_payload.get("volumeId", ""))
    volume_title = str(preflight_payload.get("volumeTitle", volume_id or "volume"))
    if not volume_id:
        return []
    if current_stage == "volume_tooling_gate":
        return _dedupe_volume_change_request_drafts(
            _build_volume_tooling_change_request_drafts(
                stage_result=stage_result,
                preflight_payload=preflight_payload,
                volume_id=volume_id,
                volume_title=volume_title,
            )
            + _build_volume_structure_change_request_drafts(
                preflight_payload=preflight_payload,
                volume_id=volume_id,
                volume_title=volume_title,
            )
        )
    if current_stage == "human_review_ready":
        if not volume_self_review:
            return _build_volume_structure_change_request_drafts(
                preflight_payload=preflight_payload,
                volume_id=volume_id,
                volume_title=volume_title,
            )
        return _build_volume_human_review_change_request_drafts(
            stage_result=stage_result,
            volume_id=volume_id,
            volume_title=volume_title,
            volume_self_review=volume_self_review,
        )
    return []


def _build_volume_tooling_change_request_drafts(
    *,
    stage_result: Dict[str, Any],
    preflight_payload: Dict[str, Any],
    volume_id: str,
    volume_title: str,
) -> list[Dict[str, Any]]:
    drafts: list[Dict[str, Any]] = []
    for item in stage_result.get("missing", []):
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "volume-tooling-gate"))
        message = str(item.get("message", stage_result.get("status", ""))).strip()
        if not message:
            continue
        target_ids, evidence = _collect_volume_rule_targets_and_evidence(
            preflight_payload=preflight_payload,
            rule_code=code,
        )
        fingerprint = f"volume-workflow::{volume_id}::{stage_result.get('stageId', '')}::{code}"
        drafts.append(
            {
                "id": f"draft-{stable_hash(fingerprint)}",
                "volumeId": volume_id,
                "kind": "volume_workflow",
                "severity": "important",
                "title": f"修复卷级工具侧阻塞：{volume_title} / {code}",
                "summary": message,
                "evidence": evidence or [message],
                "targetIds": target_ids,
                "confidence": 0.9,
                "suggestedPayload": {
                    "stageId": stage_result.get("stageId", ""),
                    "ruleId": code,
                    "volumeId": volume_id,
                    "count": item.get("count"),
                    "chapterIds": target_ids,
                    "suggestedAction": next(
                        (action for action in stage_result.get("nextActions", []) if action),
                        "",
                    ),
                },
                "status": "draft",
                "projectionStatus": "n/a",
                "fingerprint": fingerprint,
            }
        )
    return drafts


def _build_volume_human_review_change_request_drafts(
    *,
    stage_result: Dict[str, Any],
    volume_id: str,
    volume_title: str,
    volume_self_review: Dict[str, Any],
) -> list[Dict[str, Any]]:
    drafts: list[Dict[str, Any]] = []
    repair_coverage = volume_self_review.get("repairCoverage", {})
    uncovered_labels = [
        str(item).strip()
        for item in repair_coverage.get("uncoveredWeakDimensionLabels", [])
        if str(item).strip()
    ]
    issue_target_ids, issue_ref_evidence, issue_text_evidence = _collect_volume_issue_refs(volume_self_review)
    if uncovered_labels:
        labels_text = " / ".join(uncovered_labels)
        fingerprint = f"volume-workflow::{volume_id}::human_review_ready::repair-coverage::{labels_text}"
        drafts.append(
            {
                "id": f"draft-{stable_hash(fingerprint)}",
                "volumeId": volume_id,
                "kind": "volume_workflow",
                "severity": "important",
                "title": f"补齐卷级弱项修复闭环：{volume_title}",
                "summary": f"当前仍有未覆盖弱项：{labels_text}。",
                "evidence": (
                    (issue_ref_evidence + issue_text_evidence)[:3]
                    or [f"卷级自审的 issues / repairSuggestions 尚未明确覆盖：{labels_text}。"]
                ),
                "targetIds": issue_target_ids,
                "confidence": 0.95,
                "suggestedPayload": {
                    "stageId": stage_result.get("stageId", ""),
                    "ruleId": "volume-self-review-repair-coverage-incomplete",
                    "volumeId": volume_id,
                    "weakDimensionLabels": uncovered_labels,
                    "chapterIds": issue_target_ids,
                    "suggestedAction": (
                        "先把这些弱项写进 issues / repairSuggestions，并落实到实际修稿。"
                    ),
                },
                "status": "draft",
                "projectionStatus": "n/a",
                "fingerprint": fingerprint,
            }
        )

    seen_repair_suggestions: set[str] = set()
    for suggestion in volume_self_review.get("repairSuggestions", []):
        suggestion_text = str(suggestion).strip()
        if not suggestion_text or suggestion_text in seen_repair_suggestions:
            continue
        seen_repair_suggestions.add(suggestion_text)
        evidence_messages: list[str] = []
        for item in stage_result.get("missing", []):
            if not isinstance(item, dict):
                continue
            message = str(item.get("message", "")).strip()
            if message and message not in evidence_messages:
                evidence_messages.append(message)
        merged_evidence = []
        for item in issue_ref_evidence + evidence_messages + issue_text_evidence:
            if item and item not in merged_evidence:
                merged_evidence.append(item)
        fingerprint = f"volume-workflow::{volume_id}::human_review_ready::repair::{suggestion_text}"
        drafts.append(
            {
                "id": f"draft-{stable_hash(fingerprint)}",
                "volumeId": volume_id,
                "kind": "volume_workflow",
                "severity": "suggestion",
                "title": f"执行卷级修稿动作：{volume_title}",
                "summary": suggestion_text,
                "evidence": merged_evidence[:3],
                "targetIds": issue_target_ids,
                "confidence": 0.8,
                "suggestedPayload": {
                    "stageId": stage_result.get("stageId", ""),
                    "ruleId": "volume-self-review-repair-suggestion",
                    "volumeId": volume_id,
                    "repairSuggestion": suggestion_text,
                    "chapterIds": issue_target_ids,
                },
                "status": "draft",
                "projectionStatus": "n/a",
                "fingerprint": fingerprint,
            }
        )
    return drafts


def _build_volume_structure_change_request_drafts(
    *,
    preflight_payload: Dict[str, Any],
    volume_id: str,
    volume_title: str,
) -> list[Dict[str, Any]]:
    structure_check = preflight_payload.get("volumeStructureCheck", {})
    if not isinstance(structure_check, dict):
        return []
    drafts: list[Dict[str, Any]] = []
    for item in structure_check.get("checklist", []):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip()
        if status not in {"risk", "missing"}:
            continue
        check_id = str(item.get("id", "")).strip()
        if check_id == "foreshadow-debt":
            continue
        label = str(item.get("label", check_id or "卷级结构检查")).strip() or "卷级结构检查"
        message = str(item.get("message", "")).strip()
        suggestion = str(item.get("suggestion", "")).strip()
        if not message:
            continue
        target_ids = [
            str(target_id).strip()
            for target_id in item.get("targetChapterIds", [])
            if str(target_id).strip()
        ]
        evidence = [
            str(evidence_item).strip()
            for evidence_item in item.get("evidence", [])
            if str(evidence_item).strip()
        ]
        rule_id = f"volume-structure-{check_id or 'check'}"
        fingerprint = f"volume-workflow::{volume_id}::structure::{rule_id}::{status}"
        drafts.append(
            {
                "id": f"draft-{stable_hash(fingerprint)}",
                "volumeId": volume_id,
                "kind": "volume_workflow",
                "severity": "important" if status == "missing" else "suggestion",
                "title": f"补卷级结构信号：{volume_title} / {label}",
                "summary": message,
                "evidence": evidence or [message],
                "targetIds": target_ids,
                "confidence": 0.75 if status == "risk" else 0.85,
                "suggestedPayload": {
                    "stageId": "volume_structure_check",
                    "ruleId": rule_id,
                    "volumeId": volume_id,
                    "checkId": check_id,
                    "checkStatus": status,
                    "chapterIds": target_ids,
                    "suggestedAction": suggestion,
                },
                "status": "draft",
                "projectionStatus": "n/a",
                "fingerprint": fingerprint,
            }
        )
    return drafts


def _dedupe_volume_change_request_drafts(drafts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    deduped: list[Dict[str, Any]] = []
    seen_fingerprints: set[str] = set()
    for item in drafts:
        if not isinstance(item, dict):
            continue
        fingerprint = str(item.get("fingerprint", "")).strip()
        if fingerprint and fingerprint in seen_fingerprints:
            continue
        if fingerprint:
            seen_fingerprints.add(fingerprint)
        deduped.append(item)
    return deduped


def _collect_volume_rule_targets_and_evidence(
    *,
    preflight_payload: Dict[str, Any],
    rule_code: str,
) -> tuple[list[str], list[str]]:
    target_ids: list[str] = []
    evidence: list[str] = []
    for entry in preflight_payload.get("chapterPreflights", []):
        if not isinstance(entry, dict):
            continue
        chapter_id = str(entry.get("chapterId", "")).strip()
        chapter_title = str(entry.get("chapterTitle", chapter_id)).strip() or chapter_id
        chapter_evidence = _collect_chapter_evidence_for_rule(entry, rule_code)
        if not chapter_evidence:
            continue
        if chapter_id:
            target_ids.append(chapter_id)
        for item in chapter_evidence:
            if item and item not in evidence:
                evidence.append(f"{chapter_id}《{chapter_title}》: {item}" if chapter_id else f"{chapter_title}: {item}")
    return target_ids, evidence[:5]


def _collect_chapter_evidence_for_rule(
    entry: Dict[str, Any],
    rule_code: str,
) -> list[str]:
    mention_plan = entry.get("mentionPlan", {}) if isinstance(entry.get("mentionPlan", {}), dict) else {}
    foreshadow_check = entry.get("foreshadowCheck", {}) if isinstance(entry.get("foreshadowCheck", {}), dict) else {}
    world_check = entry.get("worldCheck", {}) if isinstance(entry.get("worldCheck", {}), dict) else {}
    evidence: list[str] = []

    if rule_code == "volume-mention-hygiene-pending":
        known_actions = mention_plan.get("knownUnwrappedActions", [])
        missing_actions = mention_plan.get("taggedMissingActions", [])
        parts: list[str] = []
        if known_actions:
            names = [str(item.get("name", "")).strip() for item in known_actions[:2] if str(item.get("name", "")).strip()]
            summary = f"待补包裹 {len(known_actions)} 项"
            if names:
                summary += f"（{' / '.join(names)}）"
            parts.append(summary)
        if missing_actions:
            names = [str(item.get("name", "")).strip() for item in missing_actions[:2] if str(item.get("name", "")).strip()]
            summary = f"待补建档 {len(missing_actions)} 项"
            if names:
                summary += f"（{' / '.join(names)}）"
            parts.append(summary)
        if parts:
            evidence.append("；".join(parts))
        return evidence

    if rule_code == "volume-due-foreshadow-pending":
        return _format_foreshadow_titles("到窗伏笔", foreshadow_check.get("dueForeshadows", []))
    if rule_code == "volume-overdue-foreshadow":
        return _format_foreshadow_titles("逾期伏笔", foreshadow_check.get("overdueForeshadows", []))
    if rule_code == "volume-unscheduled-foreshadow":
        return _format_foreshadow_titles("未排期伏笔", foreshadow_check.get("unresolvedWithoutSchedule", []))
    if rule_code == "volume-world-onboarding-gap":
        gaps = world_check.get("onboardingGaps", [])
        messages = [
            str(item.get("message", "")).strip()
            for item in gaps[:2]
            if isinstance(item, dict) and str(item.get("message", "")).strip()
        ]
        return messages
    if rule_code == "volume-faction-registry-gap":
        gaps = world_check.get("scaleRisks", {}).get("factionRegistryGaps", [])
        messages = [
            str(item.get("message", "")).strip()
            for item in gaps[:2]
            if isinstance(item, dict) and str(item.get("message", "")).strip()
        ]
        return messages
    if rule_code == "volume-capability-task-risk":
        risks = world_check.get("scaleRisks", {}).get("capabilityTaskRisks", [])
        for item in risks[:2]:
            if not isinstance(item, dict):
                continue
            entity = str(item.get("entityName", "")).strip()
            task = str(item.get("taskLabel", "")).strip()
            if entity or task:
                evidence.append(f"{entity or '角色'} 承担 {task or '高风险任务'} 的合理性不足")
        return evidence
    if rule_code == "volume-power-progression-conflict":
        conflicts = world_check.get("scaleRisks", {}).get("powerProgressionConflicts", [])
        for item in conflicts[:2]:
            if not isinstance(item, dict):
                continue
            entity = str(item.get("entityName", "")).strip()
            expected_stage = str(item.get("expectedNextStage", "")).strip()
            target_stage = str(item.get("targetStage", "")).strip()
            if entity or expected_stage or target_stage:
                evidence.append(
                    f"{entity or '角色'} 应先到 {expected_stage or '下一阶段'}，正文却直冲 {target_stage or '更高阶段'}"
                )
        return evidence
    return evidence


def _format_foreshadow_titles(label: str, items: list[Any]) -> list[str]:
    titles = [
        str(item.get("title", "")).strip()
        for item in items[:3]
        if isinstance(item, dict) and str(item.get("title", "")).strip()
    ]
    if not titles:
        return []
    return [f"{label}: {' / '.join(titles)}"]


def _collect_volume_issue_refs(volume_self_review: Dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    target_ids: list[str] = []
    ref_evidence: list[str] = []
    text_evidence: list[str] = []
    for item in volume_self_review.get("issues", []):
        if not isinstance(item, dict):
            continue
        for chapter_id in item.get("chapterRefs", []):
            chapter_ref = str(chapter_id).strip()
            if chapter_ref and chapter_ref not in target_ids:
                target_ids.append(chapter_ref)
        for evidence_ref in item.get("evidenceRefs", []):
            evidence_ref_text = str(evidence_ref).strip()
            if evidence_ref_text and evidence_ref_text not in ref_evidence:
                ref_evidence.append(evidence_ref_text)
            chapter_ref = _chapter_id_from_evidence_ref(evidence_ref_text)
            if chapter_ref and chapter_ref not in target_ids:
                target_ids.append(chapter_ref)
        issue = str(item.get("issue", "")).strip()
        impact = str(item.get("impact", "")).strip()
        fix_action = str(item.get("fixAction", "")).strip()
        evidence_lines = [
            str(evidence).strip()
            for evidence in item.get("evidence", [])
            if str(evidence).strip()
        ]
        combined = "；".join(
            part
            for part in [issue, impact, fix_action] + evidence_lines[:1]
            if part
        )
        if combined and combined not in text_evidence:
            text_evidence.append(combined)
    return target_ids, ref_evidence, text_evidence


def _chapter_id_from_evidence_ref(evidence_ref: str) -> str:
    text = str(evidence_ref).strip()
    if not text:
        return ""
    if text.startswith("chapter-") and "#" in text:
        return text.split("#", 1)[0]
    if text.startswith("review-packet:"):
        parts = text.split(":")
        if len(parts) == 3 and parts[2].startswith("chapter-"):
            return parts[2]
    return ""


def _attach_volume_gate_semantics(stage_result: Dict[str, Any], *, scope: str) -> Dict[str, Any]:
    enriched = dict(stage_result)
    next_actions = [str(item) for item in stage_result.get("nextActions", []) if item]
    stage_id = str(stage_result.get("stageId", ""))
    volume_id = str(stage_result.get("volumeId", ""))
    judgements: list[Dict[str, Any]] = []
    for item in stage_result.get("missing", []):
        if not isinstance(item, dict):
            continue
        message = str(item.get("message", stage_result.get("status", "当前卷级 workflow gate 尚未满足推进条件")))
        tags = ["workflow", "volume-review-gate"]
        if stage_id:
            tags.append(stage_id)
        judgements.append(
            build_rule_judgement(
                rule_id=str(item.get("code", "volume-workflow-gate-blocked")),
                source="core",
                scope=scope,
                kind="gate",
                severity="warning",
                message=message,
                suggestion=next_actions[0] if next_actions else "",
                evidence=[message],
                scope_ref={"volumeId": volume_id} if volume_id else {},
                payload=item,
                tags=tags,
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
