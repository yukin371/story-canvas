from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Iterable


VOLUME_SELF_REVIEW_RUBRIC_VERSION = "volume-self-review-v1"
VOLUME_SELF_REVIEW_DIMENSIONS = (
    ("volumeClosure", "卷级闭环"),
    ("openingOnboarding", "开篇 onboarding"),
    ("worldLogic", "世界与制度逻辑"),
    ("chapterHandoff", "章间承接"),
    ("characterContinuity", "角色连续性"),
    ("antagonistShaping", "对手塑造"),
    ("conflictEscalation", "冲突升级"),
    ("payoffDelivery", "爽点兑现"),
    ("foreshadowRhythm", "伏笔与回收节奏"),
    ("styleReadability", "风格与可读性"),
)
VOLUME_SELF_REVIEW_DIMENSION_LABELS = {
    dimension_id: label for dimension_id, label in VOLUME_SELF_REVIEW_DIMENSIONS
}
VOLUME_SELF_REVIEW_CAUSES = (
    "generation_miss",
    "self_review_miss",
    "tooling_miss",
    "false_positive",
    "accepted_risk",
)
VOLUME_SELF_REVIEW_EDITOR_MODES = (
    "independent_agent",
    "human_editor",
    "fresh_thread",
    "same_agent_fallback",
)
VOLUME_SELF_REVIEW_EDITOR_CONTEXTS = (
    "no_context_proxy",
    "fresh_thread",
    "human_manual",
    "same_thread",
    "not_available",
)
VOLUME_SELF_REVIEW_EDITOR_VERDICTS = (
    "pass",
    "revise",
    "block",
    "not_provided",
)
HUMAN_REVIEW_MINIMUM_SCORES = {
    "volumeClosure": 3,
    "chapterHandoff": 3,
    "styleReadability": 3,
}
VOLUME_SELF_REVIEW_PLACEHOLDERS = {
    "待填写",
}
VOLUME_SELF_REVIEW_DIMENSION_KEYWORDS = {
    "volumeClosure": ("闭环", "收束", "收尾", "完成感", "阶段性交付"),
    "openingOnboarding": ("开篇", "引入", "解释", "设定说明", "读者理解"),
    "worldLogic": ("世界", "制度", "规则", "逻辑", "运作"),
    "chapterHandoff": ("承接", "过渡", "衔接", "章间", "断裂"),
    "characterContinuity": ("角色", "人物", "人格", "连续", "动机"),
    "antagonistShaping": ("反派", "对手", "敌手", "行为逻辑", "目标"),
    "conflictEscalation": ("冲突", "升级", "张力", "压迫", "推进"),
    "payoffDelivery": ("爽点", "兑现", "回收", "爆发", "胜负感"),
    "foreshadowRhythm": ("伏笔", "回收", "节奏", "疑点", "钩子"),
    "styleReadability": ("风格", "可读", "ai味", "AI味", "段落", "语句"),
}
CHAPTER_EVIDENCE_REF_RE = re.compile(
    r"^(chapter-[a-z0-9_-]+)#(scene-\d+|paragraph-\d+|[a-z0-9][a-z0-9-]*)$",
    re.IGNORECASE,
)
REVIEW_PACKET_EVIDENCE_REF_RE = re.compile(
    r"^review-packet:(volume-[a-z0-9_-]+):(chapter-[a-z0-9_-]+)$",
    re.IGNORECASE,
)


def normalize_volume_self_review(
    raw_payload: Dict[str, Any],
    *,
    volume_id: str,
    volume_title: str,
    generated_at: str,
) -> Dict[str, Any]:
    if not isinstance(raw_payload, dict):
        raise ValueError("卷级自审输入必须是对象。")
    if not volume_id:
        raise ValueError("缺少 volumeId。")

    conclusion_payload = _require_dict(raw_payload.get("conclusion"), "conclusion")
    closure_assessment = _require_dict(raw_payload.get("closureAssessment"), "closureAssessment")

    normalized_scores = _normalize_scores(raw_payload.get("scores"))
    score_by_dimension = {
        item["dimensionId"]: item["score"]
        for item in normalized_scores
    }
    editor_pass = _normalize_editor_pass(raw_payload.get("editorPass"))
    editor_assessment = _normalize_editor_assessment(
        raw_payload.get("editorAssessment"),
        completed=editor_pass["completed"],
    )
    issues = _normalize_issues(raw_payload.get("issues", []))
    repair_suggestions = _normalize_string_list(
        raw_payload.get("repairSuggestions", []),
        "repairSuggestions",
        allow_empty=True,
    )
    accepted_risks = _normalize_string_list(
        raw_payload.get("acceptedRisks", []),
        "acceptedRisks",
        allow_empty=True,
    )

    closure_status = _require_choice(
        conclusion_payload.get("closureStatus"),
        "conclusion.closureStatus",
        ("closed", "not_closed"),
    )
    declared_allow_human_review = _require_bool(
        conclusion_payload.get("allowHumanReview"),
        "conclusion.allowHumanReview",
    )
    delivered = _normalize_string_list(
        closure_assessment.get("delivered", []),
        "closureAssessment.delivered",
        allow_empty=True,
    )
    missing = _normalize_string_list(
        closure_assessment.get("missing", []),
        "closureAssessment.missing",
        allow_empty=True,
    )
    _validate_review_substance(
        normalized_scores,
        closure_status=closure_status,
        declared_allow_human_review=declared_allow_human_review,
        delivered=delivered,
        missing=missing,
        editor_pass=editor_pass,
        editor_assessment=editor_assessment,
        issues=issues,
        repair_suggestions=repair_suggestions,
    )

    gate_failures = []
    if closure_status != "closed":
        gate_failures.append(
            {
                "code": "volume-self-review-not-closed",
                "message": "卷级自审结论仍为未闭环，不能进入人工审查。",
            }
        )
    for dimension_id, minimum_score in HUMAN_REVIEW_MINIMUM_SCORES.items():
        actual_score = score_by_dimension.get(dimension_id, 0)
        if actual_score < minimum_score:
            gate_failures.append(
                {
                    "code": f"volume-self-review-{dimension_id}-below-threshold",
                    "message": (
                        f"{VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id]}"
                        f" 当前仅 {actual_score}/5，低于人工审查门槛 {minimum_score}/5。"
                    ),
                    "dimensionId": dimension_id,
                    "score": actual_score,
                    "requiredScore": minimum_score,
                }
            )
    if not declared_allow_human_review:
        gate_failures.append(
            {
                "code": "volume-self-review-declared-blocked",
                "message": "卷级自审明确判定当前版本暂不建议进入人工审查。",
            }
        )
    if not editor_pass["completed"]:
        gate_failures.append(
            {
                "code": "volume-self-review-editor-pass-incomplete",
                "message": "独立编辑审查尚未完成，当前版本不应进入人工审查。",
            }
        )
    elif editor_assessment["overallVerdict"] != "pass":
        gate_failures.append(
            {
                "code": "volume-self-review-editor-verdict-blocking",
                "message": (
                    "独立编辑审查尚未给出可放行结论，当前 verdict 为 "
                    f"{editor_assessment['overallVerdict']}。"
                ),
            }
        )

    final_allow_human_review = not gate_failures
    ordered_scores = [
        _score_entry_by_dimension(normalized_scores, dimension_id)
        for dimension_id, _ in VOLUME_SELF_REVIEW_DIMENSIONS
    ]
    strongest_dimension = max(ordered_scores, key=lambda item: item["score"])
    weakest_score = min(item["score"] for item in ordered_scores)
    weakest_dimensions = [
        item["label"] for item in ordered_scores if item["score"] == weakest_score
    ]
    repair_coverage = _build_repair_coverage(
        ordered_scores,
        editor_scores=editor_assessment.get("scores", []),
        issues=issues,
        repair_suggestions=repair_suggestions,
        extra_coverage_texts=(
            editor_assessment.get("topProblems", [])
            + editor_assessment.get("improvementPoints", [])
        ),
    )

    return {
        "rubricVersion": VOLUME_SELF_REVIEW_RUBRIC_VERSION,
        "volumeId": volume_id,
        "volumeTitle": volume_title,
        "generatedAt": _require_non_empty_string(
            raw_payload.get("generatedAt", generated_at),
            "generatedAt",
        ),
        "conclusion": {
            "closureStatus": closure_status,
            "allowHumanReview": declared_allow_human_review,
            "strongestPoint": _require_non_empty_string(
                conclusion_payload.get("strongestPoint"),
                "conclusion.strongestPoint",
            ),
            "biggestRisk": _require_non_empty_string(
                conclusion_payload.get("biggestRisk"),
                "conclusion.biggestRisk",
            ),
        },
        "editorPass": editor_pass,
        "editorAssessment": editor_assessment,
        "scores": ordered_scores,
        "issues": issues,
        "closureAssessment": {
            "mainProblem": _require_non_empty_string(
                closure_assessment.get("mainProblem"),
                "closureAssessment.mainProblem",
            ),
            "delivered": delivered,
            "missing": missing,
            "reasoning": _require_non_empty_string(
                closure_assessment.get("reasoning"),
                "closureAssessment.reasoning",
            ),
        },
        "repairSuggestions": repair_suggestions,
        "acceptedRisks": accepted_risks,
        "gateFailures": gate_failures,
        "finalAllowHumanReview": final_allow_human_review,
        "scoreSummary": {
            "average": round(sum(item["score"] for item in ordered_scores) / len(ordered_scores), 2),
            "lowestScore": weakest_score,
            "lowestDimensions": weakest_dimensions,
            "strongestDimension": {
                "dimensionId": strongest_dimension["dimensionId"],
                "label": strongest_dimension["label"],
                "score": strongest_dimension["score"],
            },
        },
        "repairCoverage": repair_coverage,
    }


def validate_volume_self_review_refs(
    normalized_review: Dict[str, Any],
    *,
    chapter_anchor_index: Dict[str, Any],
    volume_id: str,
) -> None:
    chapter_map = chapter_anchor_index.get("chapters", {})
    for score_index, item in enumerate(normalized_review.get("scores", []), start=1):
        for ref_index, chapter_ref in enumerate(item.get("chapterRefs", []), start=1):
            _validate_issue_chapter_ref(
                str(chapter_ref),
                field_name=f"scores[{score_index}].chapterRefs[{ref_index}]",
                chapter_map=chapter_map,
            )
        for ref_index, evidence_ref in enumerate(item.get("evidenceRefs", []), start=1):
            _validate_issue_evidence_ref(
                str(evidence_ref),
                field_name=f"scores[{score_index}].evidenceRefs[{ref_index}]",
                chapter_map=chapter_map,
                volume_id=volume_id,
            )
    for score_index, item in enumerate(
        normalized_review.get("editorAssessment", {}).get("scores", []),
        start=1,
    ):
        for ref_index, chapter_ref in enumerate(item.get("chapterRefs", []), start=1):
            _validate_issue_chapter_ref(
                str(chapter_ref),
                field_name=f"editorAssessment.scores[{score_index}].chapterRefs[{ref_index}]",
                chapter_map=chapter_map,
            )
        for ref_index, evidence_ref in enumerate(item.get("evidenceRefs", []), start=1):
            _validate_issue_evidence_ref(
                str(evidence_ref),
                field_name=f"editorAssessment.scores[{score_index}].evidenceRefs[{ref_index}]",
                chapter_map=chapter_map,
                volume_id=volume_id,
            )
    for issue_index, item in enumerate(normalized_review.get("issues", []), start=1):
        for ref_index, chapter_ref in enumerate(item.get("chapterRefs", []), start=1):
            _validate_issue_chapter_ref(
                str(chapter_ref),
                field_name=f"issues[{issue_index}].chapterRefs[{ref_index}]",
                chapter_map=chapter_map,
            )
        for ref_index, evidence_ref in enumerate(item.get("evidenceRefs", []), start=1):
            _validate_issue_evidence_ref(
                str(evidence_ref),
                field_name=f"issues[{issue_index}].evidenceRefs[{ref_index}]",
                chapter_map=chapter_map,
                volume_id=volume_id,
            )


def latest_volume_self_review(
    story_reviews: Dict[str, Any],
    volume_id: str,
) -> Dict[str, Any]:
    if not volume_id:
        return {}
    latest: Dict[str, Any] = {}
    for item in story_reviews.get("volumeSelfReviews", []):
        if item.get("volumeId") == volume_id:
            latest = item
    return latest


def merge_volume_self_review_payload(
    base_payload: Dict[str, Any],
    overlay_payload: Dict[str, Any],
    *,
    sections: Iterable[str] | None = None,
) -> Dict[str, Any]:
    if not isinstance(base_payload, dict):
        raise ValueError("卷级自审基础输入必须是对象。")
    if not isinstance(overlay_payload, dict):
        raise ValueError("卷级自审覆盖输入必须是对象。")
    merged = deepcopy(base_payload)
    if sections is None:
        target_keys = overlay_payload.keys()
    else:
        target_keys = sections
    for key in target_keys:
        if key not in overlay_payload:
            continue
        merged[key] = _merge_payload_value(merged.get(key), overlay_payload.get(key))
    return merged


def build_volume_self_review_template(
    preflight_payload: Dict[str, Any],
    *,
    generated_at: str,
    latest_review: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if preflight_payload.get("scope") != "volume":
        raise ValueError("卷级自审模板需要 volume scope 的 preflight payload。")

    chapter_signals = _build_chapter_signals(preflight_payload)
    blocking_signals = _build_blocking_signals(preflight_payload)
    suggested_repairs = _build_suggested_repairs(preflight_payload, blocking_signals)
    review_evidence = preflight_payload.get("reviewEvidence", {})
    latest_review = latest_review or {}
    draft_autofill = _build_template_autofill(
        preflight_payload,
        blocking_signals=blocking_signals,
        review_evidence=review_evidence,
    )

    template = {
        "generatedAt": generated_at,
        "conclusion": {
            "closureStatus": "not_closed",
            "allowHumanReview": False,
            "strongestPoint": draft_autofill["strongestPoint"],
            "biggestRisk": draft_autofill["biggestRisk"],
        },
        "editorPass": {
            "completed": False,
            "reviewerRole": "editor",
            "mode": "independent_agent",
            "contextIsolation": "no_context_proxy",
            "notes": "待填写",
        },
        "editorAssessment": {
            "overallVerdict": "revise",
            "summaryComment": "待填写",
            "topProblems": [],
            "improvementPoints": [],
            "scores": [
                {
                    "dimensionId": dimension_id,
                    "score": 0,
                    "conclusion": "待填写",
                    "chapterRefs": [],
                    "evidenceRefs": [],
                }
                for dimension_id, _ in VOLUME_SELF_REVIEW_DIMENSIONS
            ],
        },
        "scores": [
            dict(item)
            for item in draft_autofill["scores"]
        ],
        "issues": [dict(item) for item in draft_autofill["issues"]],
        "closureAssessment": dict(draft_autofill["closureAssessment"]),
        "repairSuggestions": suggested_repairs,
        "acceptedRisks": [],
        "_templateHints": {
            "scoreScale": "all score fields must be integers in 0..5",
            "rootScoresPurpose": "author or primary volume self-review scores; use the shared 10-dimension rubric",
            "editorScoresPurpose": "independent editor scores; usually mirrors the same 10 dimensions with editor conclusions",
            "autofillPolicy": "root scores / issues / closureAssessment are heuristically prefilled from current preflight and review evidence; review before saving.",
            "topProblemsType": "string[]",
            "improvementPointsType": "string[]",
            "issuesType": "object[]",
            "issuesRequiredFields": [
                "issue",
                "evidence",
                "impact",
                "primaryCause",
                "fixAction",
            ],
            "issuesOptionalButRecommendedFields": [
                "secondaryCauses",
                "whyToolingMissed",
                "whySelfReviewMissed",
                "optimizationAction",
                "detectedBy",
                "ruleIds",
                "verificationCommands",
                "chapterRefs",
                "evidenceRefs",
            ],
            "issueExample": {
                "issue": "卷尾阶段性交付不足",
                "evidence": [
                    "第二章结尾更像抬出下一条主线，而不是完成本卷回合。"
                ],
                "impact": "会削弱本卷闭环感，暂不适合进入人工终审。",
                "primaryCause": "generation_miss",
                "secondaryCauses": [
                    "self_review_miss",
                    "tooling_miss"
                ],
                "fixAction": "补一层明确的阶段性兑现或输赢结果。",
                "whyToolingMissed": "现有工具更擅长判断前提是否齐备，不够擅长判断卷尾兑现厚度。",
                "whySelfReviewMissed": "AI 自审容易把继续抬线索误判为已完成闭环。",
                "optimizationAction": "把 promised / delivered / missing 的对照写进卷审模板。",
                "chapterRefs": [
                    "chapter-002"
                ],
                "evidenceRefs": [
                    "chapter-002#scene-2",
                    f"review-packet:{preflight_payload.get('volumeId', '')}:chapter-002",
                ],
            },
        },
        "_templateContext": {
            "scope": "volume",
            "volumeId": preflight_payload.get("volumeId", ""),
            "volumeTitle": preflight_payload.get("volumeTitle", ""),
            "chapterCount": preflight_payload.get("chapterCount", 0),
            "projectAdvisories": preflight_payload.get("projectAdvisories", []),
            "preflightSummary": preflight_payload.get("summary", {}),
            "volumeStructureCheck": preflight_payload.get("volumeStructureCheck", {}),
            "blockingSignals": blocking_signals,
            "chapterSignals": chapter_signals,
            "chapterReviewSummaries": review_evidence.get("chapterReviewSummaries", []),
            "lowSceneReviews": review_evidence.get("lowSceneReviews", []),
            "styleAggregate": review_evidence.get("styleAggregate", {}),
            "styleFlaggedChapters": review_evidence.get("styleFlaggedChapters", []),
            "topRuleJudgements": review_evidence.get("topRuleJudgements", []),
            "contractAlignmentRisks": review_evidence.get("contractAlignmentRisks", []),
            "commercialAlignmentRisks": review_evidence.get("commercialAlignmentRisks", []),
            "reviewPacketRefs": review_evidence.get("reviewPacketRefs", []),
            "draftAutofill": {
                "used": True,
                "strongestPointSource": draft_autofill.get("strongestPointSource", ""),
                "biggestRiskSource": draft_autofill.get("biggestRiskSource", ""),
                "issueCount": len(draft_autofill["issues"]),
                "weakDimensionIds": draft_autofill.get("weakDimensionIds", []),
            },
            "incrementalReviewOnly": {
                "latestPersistedReview": _compact_latest_review(latest_review),
                "warning": "独立盲审模式默认不要先读取上一轮自审摘要；只有增量复审才使用这里的上下文。",
            },
            "evidenceRefExamples": [
                "chapter-001#scene-1",
                "chapter-001#paragraph-4",
                "chapter-001#world-rule-onboarding",
                "chapter-002#handoff-gap",
                f"review-packet:{preflight_payload.get('volumeId', '')}:chapter-001",
            ],
            "independentEditorExpectation": {
                "requiredRole": "editor",
                "preferredMode": "independent_agent",
                "preferredContextIsolation": "no_context_proxy",
                "fallbackModes": [
                    "human_editor",
                    "fresh_thread",
                    "same_agent_fallback",
                ],
                "fallbackContextIsolation": [
                    "human_manual",
                    "fresh_thread",
                    "not_available",
                ],
                "checklist": [
                    "独立编辑评分与 AI 自审评分使用同一套 10 维 rubric。",
                    "优先使用无上下文代理；若宿主不支持，至少切到新线程或明确记录 fallback。",
                    "每个主要问题都要补‘为什么工具没报’、‘为什么 AI 自审漏看’、‘怎么优化’。",
                ],
            },
            "recommendedCommands": [
                f"review preflight --root <root> --volume-id {preflight_payload.get('volumeId', '')}",
                f"workflow status --root <root> --volume-id {preflight_payload.get('volumeId', '')}",
                f"export --root <root> --format review-packet --volume-id {preflight_payload.get('volumeId', '')}",
            ],
        },
    }
    return template


def _build_template_autofill(
    preflight_payload: Dict[str, Any],
    *,
    blocking_signals: list[Dict[str, Any]],
    review_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    observations = _collect_template_observations(
        preflight_payload,
        blocking_signals=blocking_signals,
        review_evidence=review_evidence,
    )
    volume_id = str(preflight_payload.get("volumeId", "")).strip()
    negatives_by_dimension: dict[str, list[Dict[str, Any]]] = {}
    positives_by_dimension: dict[str, list[Dict[str, Any]]] = {}
    for observation in observations:
        target = (
            negatives_by_dimension
            if observation.get("kind") == "negative"
            else positives_by_dimension
        )
        target.setdefault(str(observation.get("dimensionId", "")), []).append(observation)

    scores = []
    for dimension_id, label in VOLUME_SELF_REVIEW_DIMENSIONS:
        negatives = negatives_by_dimension.get(dimension_id, [])
        positives = positives_by_dimension.get(dimension_id, [])
        chosen = negatives[0] if negatives else positives[0] if positives else {}
        chapter_refs = _normalize_template_refs(chosen.get("chapterRefs", []))
        evidence_refs = _normalize_template_refs(chosen.get("evidenceRefs", []))
        if not evidence_refs and chapter_refs:
            evidence_refs = _review_packet_refs_for_chapters(volume_id, chapter_refs)
        score = _draft_score_for_dimension(dimension_id, negatives=negatives, positives=positives)
        scores.append(
            {
                "dimensionId": dimension_id,
                "score": score,
                "conclusion": _draft_score_conclusion(
                    dimension_id,
                    score=score,
                    chosen_observation=chosen,
                ),
                "chapterRefs": chapter_refs,
                "evidenceRefs": evidence_refs,
            }
        )

    issues = _build_template_issues(observations, volume_id=volume_id)
    strongest_dimension = max(scores, key=lambda item: item["score"])
    strongest_positive = positives_by_dimension.get(strongest_dimension["dimensionId"], [])
    strongest_point = (
        strongest_positive[0].get("summary", "").strip()
        if strongest_positive
        else strongest_dimension["conclusion"]
    ) or "当前卷至少已有一项基础能力未被工具链判为阻塞。"
    strongest_point_source = (
        strongest_positive[0].get("source", "").strip()
        if strongest_positive
        else "draft-score"
    )
    biggest_risk = (
        issues[0]["issue"]
        if issues
        else (blocking_signals[0]["message"] if blocking_signals else "当前仍需人工判断本卷是否形成完整小故事闭环。")
    )
    biggest_risk_source = issues[0].get("detectedBy", ["draft-score"])[0] if issues else "blocking-signal"
    weak_dimension_ids = [
        item["dimensionId"]
        for item in scores
        if int(item.get("score", 0) or 0) <= 2
    ]
    closure_assessment = _build_template_closure_assessment(
        scores,
        issues=issues,
        strongest_point=strongest_point,
        biggest_risk=biggest_risk,
    )
    return {
        "strongestPoint": strongest_point,
        "strongestPointSource": strongest_point_source,
        "biggestRisk": biggest_risk,
        "biggestRiskSource": biggest_risk_source,
        "scores": scores,
        "issues": issues,
        "closureAssessment": closure_assessment,
        "weakDimensionIds": weak_dimension_ids,
    }


def _collect_template_observations(
    preflight_payload: Dict[str, Any],
    *,
    blocking_signals: list[Dict[str, Any]],
    review_evidence: Dict[str, Any],
) -> list[Dict[str, Any]]:
    volume_id = str(preflight_payload.get("volumeId", "")).strip()
    chapter_signals = preflight_payload.get("chapterSignals") or _build_chapter_signals(preflight_payload)
    structure_check = preflight_payload.get("volumeStructureCheck", {})
    observations: list[Dict[str, Any]] = []

    for signal in blocking_signals:
        code = str(signal.get("code", "")).strip()
        dimension_id = _dimension_for_signal_code(code)
        chapter_refs = _chapter_refs_for_signal(code, chapter_signals)
        observations.append(
            {
                "kind": "negative",
                "dimensionId": dimension_id,
                "summary": str(signal.get("message", "")).strip(),
                "chapterRefs": chapter_refs,
                "evidenceRefs": _review_packet_refs_for_chapters(volume_id, chapter_refs),
                "impact": _generic_issue_impact(dimension_id),
                "fixAction": str(signal.get("suggestion", "")).strip() or _generic_issue_fix_action(dimension_id),
                "source": "preflight-summary",
                "priority": 100,
                "ruleIds": [],
            }
        )

    for item in structure_check.get("checklist", []):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip()
        if status == "not_applicable":
            continue
        dimension_id = _dimension_for_structure_check(item)
        chapter_refs = _normalize_template_refs(item.get("targetChapterIds", []))
        observation = {
            "kind": "positive" if status == "pass" else "negative",
            "dimensionId": dimension_id,
            "summary": str(item.get("message", "")).strip(),
            "chapterRefs": chapter_refs,
            "evidenceRefs": _review_packet_refs_for_chapters(volume_id, chapter_refs),
            "impact": _generic_issue_impact(dimension_id),
            "fixAction": str(item.get("suggestion", "")).strip() or _generic_issue_fix_action(dimension_id),
            "source": f"volume-structure:{item.get('id', '')}",
            "priority": 95 if status != "pass" else 40,
            "ruleIds": [],
        }
        observations.append(observation)

    for item in review_evidence.get("styleFlaggedChapters", []):
        if not isinstance(item, dict):
            continue
        chapter_id = str(item.get("chapterId", "")).strip()
        summary = str(item.get("summary", "")).strip()
        patterns = item.get("detectedPatterns", [])
        if not summary and patterns:
            summary = " / ".join(str(value).strip() for value in patterns[:3] if str(value).strip())
        if not summary:
            continue
        chapter_refs = [chapter_id] if chapter_id else []
        observations.append(
            {
                "kind": "negative",
                "dimensionId": "styleReadability",
                "summary": summary,
                "chapterRefs": chapter_refs,
                "evidenceRefs": _review_packet_refs_for_chapters(volume_id, chapter_refs),
                "impact": _generic_issue_impact("styleReadability"),
                "fixAction": "先处理重复出现的 AI 味、长段和可读性负担，再复检 style report。",
                "source": "style-aggregate",
                "priority": 90,
                "ruleIds": [],
            }
        )

    for item in review_evidence.get("lowSceneReviews", []):
        if not isinstance(item, dict):
            continue
        chapter_id = str(item.get("chapterId", "")).strip()
        scene_index = item.get("sceneIndex")
        summary = str(item.get("summary", "")).strip()
        if not summary:
            continue
        dimension_id = _guess_dimension_id(
            summary,
            default="conflictEscalation",
        )
        evidence_refs = []
        if chapter_id and isinstance(scene_index, int):
            evidence_refs.append(f"{chapter_id}#scene-{scene_index}")
        evidence_refs.extend(_review_packet_refs_for_chapters(volume_id, [chapter_id] if chapter_id else []))
        observations.append(
            {
                "kind": "negative",
                "dimensionId": dimension_id,
                "summary": summary,
                "chapterRefs": [chapter_id] if chapter_id else [],
                "evidenceRefs": evidence_refs,
                "impact": _generic_issue_impact(dimension_id),
                "fixAction": "优先把低分 scene 的主要问题前推到卷级修稿清单。",
                "source": "scene-review",
                "priority": 88,
                "ruleIds": [],
            }
        )

    for item in review_evidence.get("topRuleJudgements", []):
        if not isinstance(item, dict):
            continue
        message = str(item.get("message", "")).strip()
        rule_id = str(item.get("ruleId", "")).strip()
        if not message and not rule_id:
            continue
        dimension_id = _guess_dimension_id(
            " ".join(part for part in (rule_id, message) if part),
            default="styleReadability",
        )
        observations.append(
            {
                "kind": "negative",
                "dimensionId": dimension_id,
                "summary": message or f"规则 {rule_id} 在当前卷中重复出现。",
                "chapterRefs": [],
                "evidenceRefs": [],
                "impact": _generic_issue_impact(dimension_id),
                "fixAction": _generic_issue_fix_action(dimension_id),
                "source": "rule-judgement",
                "priority": 72,
                "ruleIds": [rule_id] if rule_id else [],
            }
        )

    for field_name, source, default_dimension in (
        ("contractAlignmentRisks", "chapter-review:contract", "conflictEscalation"),
        ("commercialAlignmentRisks", "chapter-review:commercial", "payoffDelivery"),
    ):
        for message in review_evidence.get(field_name, []):
            text = str(message).strip()
            if not text:
                continue
            dimension_id = _guess_dimension_id(text, default=default_dimension)
            chapter_refs = _chapter_refs_for_review_risk(review_evidence, text)
            observations.append(
                {
                    "kind": "negative",
                    "dimensionId": dimension_id,
                    "summary": text,
                    "chapterRefs": chapter_refs,
                    "evidenceRefs": _review_packet_refs_for_chapters(volume_id, chapter_refs),
                    "impact": _generic_issue_impact(dimension_id),
                    "fixAction": _generic_issue_fix_action(dimension_id),
                    "source": source,
                    "priority": 75,
                    "ruleIds": [],
                }
            )

    return observations


def _draft_score_for_dimension(
    dimension_id: str,
    *,
    negatives: list[Dict[str, Any]],
    positives: list[Dict[str, Any]],
) -> int:
    if negatives:
        if any(item.get("source", "").startswith("preflight-summary") for item in negatives):
            return 2
        if len(negatives) >= 2:
            return 2
        return 2
    if positives:
        return 3
    return 3


def _draft_score_conclusion(
    dimension_id: str,
    *,
    score: int,
    chosen_observation: Dict[str, Any],
) -> str:
    summary = str(chosen_observation.get("summary", "")).strip()
    if summary:
        return summary
    label = VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id]
    if score <= 2:
        return f"当前工具信号提示 {label} 仍有明显短板，进入人工审查前应先补一轮。"
    return f"当前工具信号未暴露明确的 {label} 阻塞，但仍需结合卷目标人工复核。"


def _build_template_issues(
    observations: list[Dict[str, Any]],
    *,
    volume_id: str,
) -> list[Dict[str, Any]]:
    negatives = [
        item
        for item in observations
        if item.get("kind") == "negative"
    ]
    negatives.sort(
        key=lambda item: (
            -int(item.get("priority", 0) or 0),
            str(item.get("dimensionId", "")),
            str(item.get("summary", "")),
        )
    )
    issues = []
    used_dimensions: set[str] = set()
    for item in negatives:
        dimension_id = str(item.get("dimensionId", "")).strip()
        if not dimension_id or dimension_id in used_dimensions:
            continue
        used_dimensions.add(dimension_id)
        chapter_refs = _normalize_template_refs(item.get("chapterRefs", []))
        evidence_refs = _normalize_template_refs(item.get("evidenceRefs", []))
        if not evidence_refs and chapter_refs:
            evidence_refs = _review_packet_refs_for_chapters(volume_id, chapter_refs)
        issue_title = _draft_issue_title(dimension_id, item)
        issues.append(
            {
                "issue": issue_title,
                "evidence": [str(item.get("summary", "")).strip()],
                "impact": str(item.get("impact", "")).strip() or _generic_issue_impact(dimension_id),
                "primaryCause": "generation_miss",
                "secondaryCauses": ["self_review_miss"] if item.get("source") != "preflight-summary" else [],
                "fixAction": str(item.get("fixAction", "")).strip() or _generic_issue_fix_action(dimension_id),
                "whyToolingMissed": "现有工具已经给出相关风险信号，但还不能替代作者判断最终是否需要改稿或改到什么强度。",
                "whySelfReviewMissed": "这一项已由模板预填，仍需要作者结合卷目标逐条确认而不是直接照抄。",
                "optimizationAction": "把这类高频风险继续回灌到卷级自审模板和 workflow gate 的下一步提示里。",
                "detectedBy": [str(item.get("source", "")).strip()] if str(item.get("source", "")).strip() else [],
                "ruleIds": _normalize_template_refs(item.get("ruleIds", [])),
                "verificationCommands": _verification_commands_for_issue(volume_id, chapter_refs),
                "chapterRefs": chapter_refs,
                "evidenceRefs": evidence_refs,
            }
        )
        if len(issues) >= 4:
            break
    return issues


def _build_template_closure_assessment(
    scores: list[Dict[str, Any]],
    *,
    issues: list[Dict[str, Any]],
    strongest_point: str,
    biggest_risk: str,
) -> Dict[str, Any]:
    delivered = []
    for item in scores:
        if int(item.get("score", 0) or 0) < 3:
            continue
        delivered.append(item.get("conclusion", ""))
        if len(delivered) >= 3:
            break
    missing = [issue.get("issue", "") for issue in issues[:3] if issue.get("issue")]
    main_problem = missing[0] if missing else biggest_risk
    reasoning = (
        f"当前模板已根据 preflight 与 review evidence 预填。"
        f"从工具信号看，较强项集中在：{strongest_point}；"
        f"但当前最需要先确认的是：{biggest_risk}。"
        "因此默认保持 `not_closed`，需要作者补完或明确接受风险后再决定是否放行。"
    )
    return {
        "mainProblem": main_problem or "当前仍需确认本卷是否形成完整小故事闭环。",
        "delivered": delivered,
        "missing": missing,
        "reasoning": reasoning,
    }


def _dimension_for_signal_code(code: str) -> str:
    mapping = {
        "chapter-file-missing": "volumeClosure",
        "mention-hygiene-pending": "characterContinuity",
        "due-foreshadow-pending": "foreshadowRhythm",
        "overdue-foreshadow-pending": "foreshadowRhythm",
        "unscheduled-foreshadow-pending": "foreshadowRhythm",
        "world-onboarding-gap": "openingOnboarding",
        "faction-registry-gap": "worldLogic",
        "capability-task-risk": "worldLogic",
        "power-progression-conflict": "worldLogic",
    }
    return mapping.get(code, "volumeClosure")


def _dimension_for_structure_check(item: Dict[str, Any]) -> str:
    check_id = str(item.get("id", "")).strip()
    mapping = {
        "outline-coverage": "volumeClosure",
        "intro-world-onboarding": "openingOnboarding",
        "foreshadow-debt": "foreshadowRhythm",
        "closure-readiness": "volumeClosure",
    }
    if check_id in mapping:
        return mapping[check_id]
    text = " ".join(
        str(item.get(field, "")).strip()
        for field in ("label", "message", "suggestion")
    )
    return _guess_dimension_id(text, default="volumeClosure")


def _guess_dimension_id(text: str, *, default: str) -> str:
    lowered = str(text or "").lower()
    explicit_mapping = {
        "chapter-handoff-weak": "chapterHandoff",
        "paragraphreadability": "styleReadability",
        "clusteredaiphrasing": "styleReadability",
        "sensoryvariety": "styleReadability",
        "metaleakage": "styleReadability",
        "povoverreach": "styleReadability",
        "张力兑现": "conflictEscalation",
        "张力偏弱": "conflictEscalation",
        "章末牵引": "foreshadowRhythm",
        "追读": "foreshadowRhythm",
        "钩子": "foreshadowRhythm",
    }
    for needle, dimension_id in explicit_mapping.items():
        if needle in lowered:
            return dimension_id
    for dimension_id, _label in VOLUME_SELF_REVIEW_DIMENSIONS:
        if _dimension_keywords_hit(dimension_id, [text]):
            return dimension_id
    return default


def _chapter_refs_for_signal(code: str, chapter_signals: list[Dict[str, Any]]) -> list[str]:
    field_mapping = {
        "chapter-file-missing": "chapterFileExists",
        "mention-hygiene-pending": "mentionActionCount",
        "due-foreshadow-pending": "dueForeshadowCount",
        "overdue-foreshadow-pending": "overdueForeshadowCount",
        "unscheduled-foreshadow-pending": "unresolvedWithoutScheduleCount",
        "world-onboarding-gap": "worldOnboardingGapCount",
        "faction-registry-gap": "factionRegistryGapCount",
        "capability-task-risk": "capabilityTaskRiskCount",
        "power-progression-conflict": "powerProgressionConflictCount",
    }
    field_name = field_mapping.get(code, "")
    chapter_refs = []
    for item in chapter_signals:
        chapter_id = str(item.get("chapterId", "")).strip()
        if not chapter_id:
            continue
        if code == "chapter-file-missing":
            if not bool(item.get("chapterFileExists")):
                chapter_refs.append(chapter_id)
            continue
        count = int(item.get(field_name, 0) or 0) if field_name else 0
        if count > 0:
            chapter_refs.append(chapter_id)
    return chapter_refs[:3]


def _chapter_refs_for_review_risk(review_evidence: Dict[str, Any], text: str) -> list[str]:
    chapter_refs = []
    candidates = [
        item
        for item in review_evidence.get("chapterReviewSummaries", [])
        if isinstance(item, dict) and str(item.get("chapterId", "")).strip()
    ]
    for item in review_evidence.get("chapterReviewSummaries", []):
        if not isinstance(item, dict):
            continue
        summary = str(item.get("summary", "")).strip()
        chapter_id = str(item.get("chapterId", "")).strip()
        if not summary or not chapter_id:
            continue
        if any(keyword.lower() in summary.lower() for keyword in str(text).split()):
            chapter_refs.append(chapter_id)
        if len(chapter_refs) >= 3:
            break
    if not chapter_refs and len(candidates) == 1:
        chapter_refs.append(str(candidates[0].get("chapterId", "")).strip())
    return chapter_refs


def _review_packet_refs_for_chapters(volume_id: str, chapter_refs: Iterable[str]) -> list[str]:
    refs = []
    seen = set()
    for chapter_id in chapter_refs:
        chapter_id = str(chapter_id).strip()
        if not chapter_id or chapter_id in seen:
            continue
        seen.add(chapter_id)
        refs.append(f"review-packet:{volume_id}:{chapter_id}")
    return refs


def _normalize_template_refs(values: Iterable[Any]) -> list[str]:
    normalized = []
    seen = set()
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _draft_issue_title(dimension_id: str, observation: Dict[str, Any]) -> str:
    summary = str(observation.get("summary", "")).strip()
    if summary:
        return summary
    return f"{VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id]} 仍需补强"


def _generic_issue_impact(dimension_id: str) -> str:
    label = VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id]
    return f"会直接拉低{label}，默认不建议把当前版本直接送入人工审查。"


def _generic_issue_fix_action(dimension_id: str) -> str:
    fixes = {
        "volumeClosure": "补一处更明确的阶段性交付、收束或卷尾回合完成感。",
        "openingOnboarding": "把读者必须先懂的前提、规则或处境解释再前置一层。",
        "worldLogic": "补制度代价、世界规则或能力边界，让设定更能自洽落地。",
        "chapterHandoff": "补上一章结果对下一章开头的具体承接，而不是只靠话题延续。",
        "characterContinuity": "补角色动机、反应或状态延续，让选择链更完整。",
        "antagonistShaping": "把对手从线索或名词推进成有动作、有目标的在场压力。",
        "conflictEscalation": "补更硬的阻力、误判、失败边缘或选择代价，拉开升级台阶。",
        "payoffDelivery": "补一处更明确的兑现、输赢结果或读者可感知的回报。",
        "foreshadowRhythm": "明确哪些短线本卷要回收，哪些长线要带着责任进入下一卷。",
        "styleReadability": "优先处理 AI 味、长段和重复句式，再复检可读性。",
    }
    return fixes[dimension_id]


def _verification_commands_for_issue(volume_id: str, chapter_refs: list[str]) -> list[str]:
    commands = [f"workflow status --root <root> --volume-id {volume_id}"]
    if chapter_refs:
        commands.append(
            f"export --root <root> --format review-packet --volume-id {volume_id}"
        )
    return commands


def _normalize_scores(raw_scores: Any, *, field_name: str = "scores") -> list[Dict[str, Any]]:
    if not isinstance(raw_scores, list):
        raise ValueError(f"{field_name} 必须是数组。")
    normalized_by_id: Dict[str, Dict[str, Any]] = {}
    for index, item in enumerate(raw_scores, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{field_name}[{index}] 必须是对象。")
        dimension_id = _require_choice(
            item.get("dimensionId"),
            f"{field_name}[{index}].dimensionId",
            tuple(VOLUME_SELF_REVIEW_DIMENSION_LABELS.keys()),
        )
        if dimension_id in normalized_by_id:
            raise ValueError(f"{field_name} 中存在重复维度: {dimension_id}")
        score = item.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > 5:
            raise ValueError(f"{field_name}[{index}].score 必须是 0..5 的整数。")
        normalized_by_id[dimension_id] = {
            "dimensionId": dimension_id,
            "label": VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id],
            "score": score,
            "conclusion": _require_non_empty_string(
                item.get("conclusion"),
                f"{field_name}[{index}].conclusion",
            ),
            "chapterRefs": _normalize_string_list(
                item.get("chapterRefs", []),
                f"{field_name}[{index}].chapterRefs",
                allow_empty=True,
            ),
            "evidenceRefs": _normalize_evidence_refs(
                item.get("evidenceRefs", []),
                f"{field_name}[{index}].evidenceRefs",
            ),
        }
    missing_dimension_ids = [
        dimension_id
        for dimension_id, _ in VOLUME_SELF_REVIEW_DIMENSIONS
        if dimension_id not in normalized_by_id
    ]
    if missing_dimension_ids:
        raise ValueError(
            f"{field_name} 缺少必填维度: " + ", ".join(missing_dimension_ids)
        )
    return list(normalized_by_id.values())


def _score_entry_by_dimension(
    normalized_scores: Iterable[Dict[str, Any]],
    dimension_id: str,
) -> Dict[str, Any]:
    for item in normalized_scores:
        if item.get("dimensionId") == dimension_id:
            return dict(item)
    raise ValueError(f"未找到评分维度: {dimension_id}")


def _normalize_issues(raw_issues: Any) -> list[Dict[str, Any]]:
    if not isinstance(raw_issues, list):
        raise ValueError("issues 必须是数组。")
    normalized = []
    for index, item in enumerate(raw_issues, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"issues[{index}] 必须是对象。")
        normalized.append(
            {
                "issue": _require_non_empty_string(item.get("issue"), f"issues[{index}].issue"),
                "evidence": _normalize_string_list(
                    item.get("evidence", []),
                    f"issues[{index}].evidence",
                    allow_empty=False,
                ),
                "impact": _require_non_empty_string(item.get("impact"), f"issues[{index}].impact"),
                "primaryCause": _require_choice(
                    item.get("primaryCause"),
                    f"issues[{index}].primaryCause",
                    VOLUME_SELF_REVIEW_CAUSES,
                ),
                "secondaryCauses": _normalize_choice_list(
                    item.get("secondaryCauses", []),
                    f"issues[{index}].secondaryCauses",
                    VOLUME_SELF_REVIEW_CAUSES,
                ),
                "fixAction": _require_non_empty_string(
                    item.get("fixAction"),
                    f"issues[{index}].fixAction",
                ),
                "whyToolingMissed": _normalize_optional_string(
                    item.get("whyToolingMissed"),
                    f"issues[{index}].whyToolingMissed",
                    default="未补充：需说明该问题为何没有被现有工具稳定暴露。",
                ),
                "whySelfReviewMissed": _normalize_optional_string(
                    item.get("whySelfReviewMissed"),
                    f"issues[{index}].whySelfReviewMissed",
                    default="未补充：需说明 AI 自审为何没有及时注意到该问题。",
                ),
                "optimizationAction": _normalize_optional_string(
                    item.get("optimizationAction"),
                    f"issues[{index}].optimizationAction",
                    default="未补充：需说明应补哪条规则、提示或复检流程。",
                ),
                "detectedBy": _normalize_string_list(
                    item.get("detectedBy", []),
                    f"issues[{index}].detectedBy",
                    allow_empty=True,
                ),
                "ruleIds": _normalize_string_list(
                    item.get("ruleIds", []),
                    f"issues[{index}].ruleIds",
                    allow_empty=True,
                ),
                "verificationCommands": _normalize_string_list(
                    item.get("verificationCommands", []),
                    f"issues[{index}].verificationCommands",
                    allow_empty=True,
                ),
                "chapterRefs": _normalize_string_list(
                    item.get("chapterRefs", []),
                    f"issues[{index}].chapterRefs",
                    allow_empty=True,
                ),
                "evidenceRefs": _normalize_evidence_refs(
                    item.get("evidenceRefs", []),
                    f"issues[{index}].evidenceRefs",
                ),
            }
        )
    return normalized


def _normalize_evidence_refs(raw_value: Any, field_name: str) -> list[str]:
    refs = _normalize_string_list(raw_value, field_name, allow_empty=True)
    return [
        _normalize_evidence_ref(item, f"{field_name}[{index}]")
        for index, item in enumerate(refs, start=1)
    ]


def _normalize_evidence_ref(raw_value: str, field_name: str) -> str:
    value = raw_value.strip()
    chapter_match = CHAPTER_EVIDENCE_REF_RE.match(value)
    if chapter_match:
        chapter_id = chapter_match.group(1).lower()
        anchor = chapter_match.group(2).lower()
        return f"{chapter_id}#{anchor}"
    packet_match = REVIEW_PACKET_EVIDENCE_REF_RE.match(value)
    if packet_match:
        return (
            f"review-packet:{packet_match.group(1).lower()}:{packet_match.group(2).lower()}"
        )
    if value.startswith("chapter-") or value.startswith("review-packet:"):
        raise ValueError(
            f"{field_name} 格式无效。推荐使用 `chapter-001#scene-1`、`chapter-001#paragraph-4`、"
            "`chapter-001#world-rule-onboarding`、`chapter-002#handoff-gap` 或 "
            "`review-packet:volume-001:chapter-001`。"
        )
    return value


def _validate_issue_chapter_ref(
    chapter_ref: str,
    *,
    field_name: str,
    chapter_map: Dict[str, Any],
) -> None:
    if not chapter_ref:
        return
    if chapter_ref not in chapter_map:
        raise ValueError(f"{field_name} 指向的章节不存在或不属于当前卷: {chapter_ref}")


def _validate_issue_evidence_ref(
    evidence_ref: str,
    *,
    field_name: str,
    chapter_map: Dict[str, Any],
    volume_id: str,
) -> None:
    chapter_match = CHAPTER_EVIDENCE_REF_RE.match(evidence_ref)
    if chapter_match:
        chapter_id = chapter_match.group(1).lower()
        anchor = chapter_match.group(2).lower()
        chapter_entry = chapter_map.get(chapter_id)
        if not chapter_entry:
            raise ValueError(f"{field_name} 指向的章节不存在或不属于当前卷: {chapter_id}")
        if anchor.startswith("paragraph-"):
            paragraph_number = int(anchor.split("-", 1)[1])
            paragraph_count = int(chapter_entry.get("paragraphCount", 0) or 0)
            if paragraph_number < 1 or paragraph_number > paragraph_count:
                raise ValueError(
                    f"{field_name} 指向的段落不存在: {evidence_ref}；当前正文仅有 {paragraph_count} 个段落。"
                )
        elif anchor.startswith("scene-"):
            scene_number = int(anchor.split("-", 1)[1])
            available_scene_numbers = set(chapter_entry.get("sceneNumbers", []))
            if scene_number not in available_scene_numbers:
                if available_scene_numbers:
                    available = ", ".join(f"scene-{item}" for item in sorted(available_scene_numbers))
                    message = (
                        f"{field_name} 指向的场景不存在: {evidence_ref}；当前章节可用 scene 为 {available}。"
                    )
                else:
                    message = f"{field_name} 指向的场景不存在: {evidence_ref}；当前章节没有可用 scenePlans。"
                raise ValueError(
                    message
                )
            reviewed_scene_numbers = set(chapter_entry.get("reviewedSceneNumbers", []))
            if scene_number not in reviewed_scene_numbers:
                if reviewed_scene_numbers:
                    reviewed = ", ".join(f"scene-{item}" for item in sorted(reviewed_scene_numbers))
                    message = (
                        f"{field_name} 指向的场景尚未映射到已持久化的 scene review: {evidence_ref}；"
                        f"当前章节已审查场景为 {reviewed}。"
                    )
                else:
                    message = (
                        f"{field_name} 指向的场景尚未映射到已持久化的 scene review: {evidence_ref}；"
                        "当前章节还没有可用的 scene review 结果。"
                    )
                raise ValueError(message)
        else:
            semantic_anchors = set(chapter_entry.get("semanticAnchors", []))
            if anchor not in semantic_anchors:
                if semantic_anchors:
                    available = ", ".join(sorted(semantic_anchors))
                    message = (
                        f"{field_name} 指向的语义锚点不存在: {evidence_ref}；"
                        f"当前章节可用语义锚点为 {available}。"
                    )
                else:
                    message = (
                        f"{field_name} 指向的语义锚点不存在: {evidence_ref}；"
                        "当前章节没有可用语义锚点。"
                    )
                raise ValueError(message)
        return

    packet_match = REVIEW_PACKET_EVIDENCE_REF_RE.match(evidence_ref)
    if packet_match:
        packet_volume_id = packet_match.group(1).lower()
        chapter_id = packet_match.group(2).lower()
        if packet_volume_id != volume_id.lower():
            raise ValueError(
                f"{field_name} 指向的 review-packet 卷 id 与当前卷不一致: {evidence_ref}"
            )
        if chapter_id not in chapter_map:
            raise ValueError(f"{field_name} 指向的章节不存在或不属于当前卷: {chapter_id}")


def _normalize_string_list(raw_value: Any, field_name: str, *, allow_empty: bool) -> list[str]:
    if not isinstance(raw_value, list):
        raise ValueError(f"{field_name} 必须是字符串数组。")
    values = []
    for index, item in enumerate(raw_value, start=1):
        values.append(_require_non_empty_string(item, f"{field_name}[{index}]"))
    if not allow_empty and not values:
        raise ValueError(f"{field_name} 不能为空。")
    return values


def _normalize_choice_list(raw_value: Any, field_name: str, choices: Iterable[str]) -> list[str]:
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        raise ValueError(f"{field_name} 必须是字符串数组。")
    values = []
    for index, item in enumerate(raw_value, start=1):
        values.append(_require_choice(item, f"{field_name}[{index}]", choices))
    return values


def _normalize_optional_string(raw_value: Any, field_name: str, *, default: str = "") -> str:
    if raw_value is None:
        return default
    if not isinstance(raw_value, str):
        raise ValueError(f"{field_name} 必须是字符串。")
    value = raw_value.strip()
    if not value:
        return default
    if value in VOLUME_SELF_REVIEW_PLACEHOLDERS:
        raise ValueError(f"{field_name} 仍是模板占位值，请先填写真实内容。")
    return value


def _require_dict(raw_value: Any, field_name: str) -> Dict[str, Any]:
    if not isinstance(raw_value, dict):
        raise ValueError(f"{field_name} 必须是对象。")
    return raw_value


def _require_non_empty_string(raw_value: Any, field_name: str) -> str:
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError(f"{field_name} 不能为空字符串。")
    value = raw_value.strip()
    if value in VOLUME_SELF_REVIEW_PLACEHOLDERS:
        raise ValueError(f"{field_name} 仍是模板占位值，请先填写真实内容。")
    return value


def _require_choice(raw_value: Any, field_name: str, choices: Iterable[str]) -> str:
    value = _require_non_empty_string(raw_value, field_name)
    if value not in choices:
        raise ValueError(f"{field_name} 必须是以下值之一: {', '.join(choices)}")
    return value


def _require_bool(raw_value: Any, field_name: str) -> bool:
    if not isinstance(raw_value, bool):
        raise ValueError(f"{field_name} 必须是布尔值。")
    return raw_value


def _validate_review_substance(
    normalized_scores: list[Dict[str, Any]],
    *,
    closure_status: str,
    declared_allow_human_review: bool,
    delivered: list[str],
    missing: list[str],
    editor_pass: Dict[str, Any],
    editor_assessment: Dict[str, Any],
    issues: list[Dict[str, Any]],
    repair_suggestions: list[str],
) -> None:
    if all(item.get("score", 0) == 0 for item in normalized_scores):
        raise ValueError("scores 不能全部为 0，请至少给出真实的维度判断。")
    if declared_allow_human_review and closure_status != "closed":
        raise ValueError("conclusion.allowHumanReview=true 时，conclusion.closureStatus 必须为 closed。")
    if declared_allow_human_review:
        for dimension_id, minimum_score in HUMAN_REVIEW_MINIMUM_SCORES.items():
            actual_score = next(
                item.get("score", 0)
                for item in normalized_scores
                if item.get("dimensionId") == dimension_id
            )
            if actual_score < minimum_score:
                raise ValueError(
                    "conclusion.allowHumanReview=true 与评分门槛不一致："
                    f"{VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id]} 当前仅 {actual_score}/5。"
                )
    if declared_allow_human_review and not editor_pass.get("completed"):
        raise ValueError(
            "conclusion.allowHumanReview=true 时，editorPass.completed 必须为 true。"
        )
    if declared_allow_human_review and editor_assessment.get("overallVerdict") != "pass":
        raise ValueError(
            "conclusion.allowHumanReview=true 时，editorAssessment.overallVerdict 必须为 pass。"
        )
    if editor_pass.get("completed") and not editor_assessment.get("scores"):
        raise ValueError("editorAssessment.scores 不能为空；独立编辑审查必须给出评分。")
    if editor_pass.get("completed") and not editor_assessment.get("summaryComment"):
        raise ValueError("editorAssessment.summaryComment 不能为空；独立编辑审查必须给出评语。")
    if editor_pass.get("completed") and not editor_assessment.get("improvementPoints"):
        raise ValueError(
            "editorAssessment.improvementPoints 不能为空；独立编辑审查必须给出改进点。"
        )
    if closure_status == "closed" and not delivered:
        raise ValueError("closureAssessment.delivered 不能为空；已闭环必须写明本卷实际交付了什么。")
    if closure_status == "not_closed" and not missing:
        raise ValueError("closureAssessment.missing 不能为空；未闭环必须写明仍缺什么。")
    if closure_status == "not_closed" and not issues:
        raise ValueError("issues 不能为空；未闭环时至少要明确一项主要问题与归因。")
    if any(item.get("score", 0) <= 2 for item in normalized_scores) and not issues:
        raise ValueError("issues 不能为空；存在 0-2 分的弱项时至少要明确一项主要问题与归因。")
    if issues and not repair_suggestions:
        raise ValueError("repairSuggestions 不能为空；存在 issues 时至少要给出一条修后建议。")
    weak_dimensions = [
        item.get("dimensionId", "")
        for item in normalized_scores
        if item.get("score", 0) <= 2
    ]
    uncovered_weak_dimensions = _find_uncovered_weak_dimensions(
        weak_dimensions,
        issues=issues,
        repair_suggestions=repair_suggestions,
    )
    if uncovered_weak_dimensions:
        labels = [VOLUME_SELF_REVIEW_DIMENSION_LABELS[item] for item in uncovered_weak_dimensions]
        raise ValueError(
            "以下低分维度还没有被 issues / repairSuggestions 明确覆盖："
            + "、".join(labels)
        )
    missing_score_refs = _find_low_score_dimensions_without_refs(
        normalized_scores,
        issues=issues,
    )
    if missing_score_refs:
        labels = [VOLUME_SELF_REVIEW_DIMENSION_LABELS[item] for item in missing_score_refs]
        raise ValueError(
            "以下低分维度还缺少可核对的章节或证据锚点："
            + "、".join(labels)
        )


def _build_blocking_signals(preflight_payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    summary = preflight_payload.get("summary", {})
    issue_specs = [
        (
            "chapter-file-missing",
            int(summary.get("chapterFileMissingCount", 0) or 0),
            "当前卷仍有 {count} 个章节文件缺失。",
            "先补齐缺失章节，再做卷级自审。",
        ),
        (
            "mention-hygiene-pending",
            int(summary.get("mentionActionCount", 0) or 0),
            "当前卷仍有 {count} 项实体或世界名词闭环动作未完成。",
            "先处理包裹或建档缺口，再做卷级自审。",
        ),
        (
            "due-foreshadow-pending",
            int(summary.get("dueForeshadowCount", 0) or 0),
            "当前卷有 {count} 个伏笔已经到窗但尚未处理。",
            "先决定兑现、延后还是接受风险。",
        ),
        (
            "overdue-foreshadow-pending",
            int(summary.get("overdueForeshadowCount", 0) or 0),
            "当前卷有 {count} 个伏笔已经逾期未回收。",
            "先补回收或重排窗口。",
        ),
        (
            "unscheduled-foreshadow-pending",
            int(summary.get("unresolvedWithoutScheduleCount", 0) or 0),
            "当前卷有 {count} 个伏笔仍未排期。",
            "先补最小 payoff window。",
        ),
        (
            "world-onboarding-gap",
            int(summary.get("worldOnboardingGapCount", 0) or 0),
            "当前卷累计暴露 {count} 个世界 onboarding 缺口。",
            "先补核心概念、制度代价或世界规则解释。",
        ),
        (
            "faction-registry-gap",
            int(summary.get("factionRegistryGapCount", 0) or 0),
            "当前卷累计暴露 {count} 个势力建档薄弱项。",
            "先补势力层级、状态或地盘信息。",
        ),
        (
            "capability-task-risk",
            int(summary.get("capabilityTaskRiskCount", 0) or 0),
            "当前卷累计暴露 {count} 个能力与任务门槛风险。",
            "先补保护条件或例外说明。",
        ),
        (
            "power-progression-conflict",
            int(summary.get("powerProgressionConflictCount", 0) or 0),
            "当前卷累计暴露 {count} 个突破链冲突。",
            "先修正战力推进链。",
        ),
    ]
    signals = []
    for code, count, message_template, suggestion in issue_specs:
        if count <= 0:
            continue
        signals.append(
            {
                "code": code,
                "count": count,
                "message": message_template.format(count=count),
                "suggestion": suggestion,
            }
        )
    return signals


def _build_suggested_repairs(preflight_payload: Dict[str, Any], blocking_signals: list[Dict[str, Any]]) -> list[str]:
    suggestions = [item.get("suggestion", "") for item in blocking_signals if item.get("suggestion")]
    if suggestions:
        return suggestions[:5]
    if preflight_payload.get("chapterCount", 0):
        return [
            "先判断这一卷是否已经形成完整小故事闭环。",
            "再逐项补写最影响人工审查的结构或解释缺口。",
        ]
    return []


def _build_chapter_signals(preflight_payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    result = []
    for item in preflight_payload.get("chapterPreflights", []):
        if not isinstance(item, dict):
            continue
        summary = item.get("summary", {})
        result.append(
            {
                "chapterId": item.get("chapterId", ""),
                "chapterTitle": item.get("chapterTitle", ""),
                "chapterFileExists": bool(item.get("chapterFileExists")),
                "mentionActionCount": summary.get("mentionActionCount", 0),
                "dueForeshadowCount": summary.get("dueForeshadowCount", 0),
                "overdueForeshadowCount": summary.get("overdueForeshadowCount", 0),
                "worldOnboardingGapCount": summary.get("worldOnboardingGapCount", 0),
                "factionRegistryGapCount": summary.get("factionRegistryGapCount", 0),
                "capabilityTaskRiskCount": summary.get("capabilityTaskRiskCount", 0),
                "powerProgressionConflictCount": summary.get("powerProgressionConflictCount", 0),
            }
        )
    return result


def _compact_latest_review(latest_review: Dict[str, Any]) -> Dict[str, Any]:
    if not latest_review:
        return {}
    conclusion = latest_review.get("conclusion", {})
    editor_pass = latest_review.get("editorPass", {})
    editor_assessment = latest_review.get("editorAssessment", {})
    score_summary = latest_review.get("scoreSummary", {})
    return {
        "generatedAt": latest_review.get("generatedAt", ""),
        "closureStatus": conclusion.get("closureStatus", ""),
        "declaredAllowHumanReview": conclusion.get("allowHumanReview"),
        "finalAllowHumanReview": latest_review.get("finalAllowHumanReview"),
        "editorPassCompleted": editor_pass.get("completed"),
        "editorMode": editor_pass.get("mode", ""),
        "editorContextIsolation": editor_pass.get("contextIsolation", ""),
        "editorVerdict": editor_assessment.get("overallVerdict", ""),
        "strongestPoint": conclusion.get("strongestPoint", ""),
        "biggestRisk": conclusion.get("biggestRisk", ""),
        "averageScore": score_summary.get("average"),
        "lowestDimensions": score_summary.get("lowestDimensions", []),
        "topRepairSuggestions": list(latest_review.get("repairSuggestions", []))[:3],
    }


def _normalize_editor_pass(raw_value: Any) -> Dict[str, Any]:
    if raw_value is None:
        return {
            "completed": False,
            "reviewerRole": "editor",
            "mode": "same_agent_fallback",
            "contextIsolation": "same_thread",
            "notes": "未提供独立编辑审查记录。",
        }
    payload = _require_dict(raw_value, "editorPass")
    return {
        "completed": _require_bool(
            payload.get("completed"),
            "editorPass.completed",
        ),
        "reviewerRole": _require_choice(
            payload.get("reviewerRole"),
            "editorPass.reviewerRole",
            ("editor",),
        ),
        "mode": _require_choice(
            payload.get("mode"),
            "editorPass.mode",
            VOLUME_SELF_REVIEW_EDITOR_MODES,
        ),
        "contextIsolation": _require_choice(
            payload.get("contextIsolation"),
            "editorPass.contextIsolation",
            VOLUME_SELF_REVIEW_EDITOR_CONTEXTS,
        ),
        "notes": _normalize_optional_string(
            payload.get("notes"),
            "editorPass.notes",
            default="",
        ),
    }


def _normalize_editor_assessment(raw_value: Any, *, completed: bool) -> Dict[str, Any]:
    if raw_value is None:
        return {
            "overallVerdict": "not_provided",
            "summaryComment": "",
            "topProblems": [],
            "improvementPoints": [],
            "scores": [],
        }
    payload = _require_dict(raw_value, "editorAssessment")
    normalized_scores = payload.get("scores")
    if normalized_scores is None or (not completed and normalized_scores == []):
        normalized_score_entries: list[Dict[str, Any]] = []
    else:
        normalized_score_entries = _normalize_scores(
            normalized_scores,
            field_name="editorAssessment.scores",
        )
    return {
        "overallVerdict": _require_choice(
            payload.get("overallVerdict"),
            "editorAssessment.overallVerdict",
            VOLUME_SELF_REVIEW_EDITOR_VERDICTS,
        ),
        "summaryComment": _normalize_optional_string(
            payload.get("summaryComment"),
            "editorAssessment.summaryComment",
            default="",
        ),
        "topProblems": _normalize_string_list(
            payload.get("topProblems", []),
            "editorAssessment.topProblems",
            allow_empty=not completed,
        ),
        "improvementPoints": _normalize_string_list(
            payload.get("improvementPoints", []),
            "editorAssessment.improvementPoints",
            allow_empty=not completed,
        ),
        "scores": normalized_score_entries,
    }


def _build_repair_coverage(
    normalized_scores: list[Dict[str, Any]],
    *,
    editor_scores: list[Dict[str, Any]] | None = None,
    issues: list[Dict[str, Any]],
    repair_suggestions: list[str],
    extra_coverage_texts: Iterable[str] | None = None,
) -> Dict[str, Any]:
    root_weak_dimensions = [
        item.get("dimensionId", "")
        for item in normalized_scores
        if item.get("score", 0) <= 2
    ]
    editor_weak_dimensions = [
        item.get("dimensionId", "")
        for item in (editor_scores or [])
        if item.get("score", 0) <= 2
    ]
    weak_dimensions = _dedupe_dimension_ids(root_weak_dimensions + editor_weak_dimensions)
    uncovered = _find_uncovered_weak_dimensions(
        weak_dimensions,
        issues=issues,
        repair_suggestions=repair_suggestions,
        extra_coverage_texts=extra_coverage_texts,
    )
    return {
        "weakDimensionIds": weak_dimensions,
        "weakDimensionLabels": [
            VOLUME_SELF_REVIEW_DIMENSION_LABELS[item]
            for item in weak_dimensions
            if item in VOLUME_SELF_REVIEW_DIMENSION_LABELS
        ],
        "rootWeakDimensionIds": root_weak_dimensions,
        "rootWeakDimensionLabels": [
            VOLUME_SELF_REVIEW_DIMENSION_LABELS[item]
            for item in root_weak_dimensions
            if item in VOLUME_SELF_REVIEW_DIMENSION_LABELS
        ],
        "editorWeakDimensionIds": editor_weak_dimensions,
        "editorWeakDimensionLabels": [
            VOLUME_SELF_REVIEW_DIMENSION_LABELS[item]
            for item in editor_weak_dimensions
            if item in VOLUME_SELF_REVIEW_DIMENSION_LABELS
        ],
        "uncoveredWeakDimensionIds": uncovered,
        "uncoveredWeakDimensionLabels": [
            VOLUME_SELF_REVIEW_DIMENSION_LABELS[item]
            for item in uncovered
            if item in VOLUME_SELF_REVIEW_DIMENSION_LABELS
        ],
        "issueCount": len(issues),
        "repairSuggestionCount": len(repair_suggestions),
        "status": "complete" if not uncovered else "incomplete",
    }


def _find_uncovered_weak_dimensions(
    weak_dimensions: list[str],
    *,
    issues: list[Dict[str, Any]],
    repair_suggestions: list[str],
    extra_coverage_texts: Iterable[str] | None = None,
) -> list[str]:
    issue_texts = []
    for item in issues:
        issue_texts.append(str(item.get("issue", "")))
        issue_texts.append(str(item.get("impact", "")))
        issue_texts.append(str(item.get("fixAction", "")))
    issue_texts.extend(repair_suggestions)
    issue_texts.extend(str(item) for item in (extra_coverage_texts or []))
    uncovered = []
    for dimension_id in weak_dimensions:
        if not _dimension_keywords_hit(dimension_id, issue_texts):
            uncovered.append(dimension_id)
    return uncovered


def _dedupe_dimension_ids(dimension_ids: Iterable[str]) -> list[str]:
    deduped: list[str] = []
    for dimension_id in dimension_ids:
        value = str(dimension_id or "").strip()
        if not value or value not in VOLUME_SELF_REVIEW_DIMENSION_LABELS:
            continue
        if value not in deduped:
            deduped.append(value)
    return deduped


def _find_low_score_dimensions_without_refs(
    normalized_scores: list[Dict[str, Any]],
    *,
    issues: list[Dict[str, Any]],
) -> list[str]:
    issue_texts_with_refs: list[str] = []
    for item in issues:
        if not _has_any_refs(item):
            continue
        issue_texts_with_refs.append(str(item.get("issue", "")))
        issue_texts_with_refs.append(str(item.get("impact", "")))
        issue_texts_with_refs.append(str(item.get("fixAction", "")))
    missing: list[str] = []
    for item in normalized_scores:
        dimension_id = str(item.get("dimensionId", ""))
        score = int(item.get("score", 0) or 0)
        if score > 2:
            continue
        if _has_any_refs(item):
            continue
        if _dimension_keywords_hit(dimension_id, issue_texts_with_refs):
            continue
        missing.append(dimension_id)
    return missing


def _has_any_refs(item: Dict[str, Any]) -> bool:
    return bool(item.get("chapterRefs") or item.get("evidenceRefs"))


def _dimension_keywords_hit(dimension_id: str, texts: Iterable[str]) -> bool:
    keywords = VOLUME_SELF_REVIEW_DIMENSION_KEYWORDS.get(dimension_id, ())
    if not keywords:
        return True
    combined = " ".join(str(item) for item in texts if item).lower()
    if not combined:
        return False
    return any(keyword.lower() in combined for keyword in keywords)


def _merge_payload_value(base_value: Any, overlay_value: Any) -> Any:
    if overlay_value is None:
        return deepcopy(base_value)
    if isinstance(base_value, dict) and isinstance(overlay_value, dict):
        merged = deepcopy(base_value)
        for key, value in overlay_value.items():
            merged[key] = _merge_payload_value(merged.get(key), value)
        return merged
    return deepcopy(overlay_value)
