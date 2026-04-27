from __future__ import annotations

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
        issues=issues,
        repair_suggestions=repair_suggestions,
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
    latest_review = latest_review or {}

    template = {
        "generatedAt": generated_at,
        "conclusion": {
            "closureStatus": "not_closed",
            "allowHumanReview": False,
            "strongestPoint": "待填写",
            "biggestRisk": blocking_signals[0]["message"] if blocking_signals else "待填写",
        },
        "scores": [
            {
                "dimensionId": dimension_id,
                "score": 0,
                "conclusion": "待填写",
            }
            for dimension_id, _ in VOLUME_SELF_REVIEW_DIMENSIONS
        ],
        "issues": [],
        "closureAssessment": {
            "mainProblem": "待填写",
            "delivered": [],
            "missing": [],
            "reasoning": "待填写",
        },
        "repairSuggestions": suggested_repairs,
        "acceptedRisks": [],
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
            "latestPersistedReview": _compact_latest_review(latest_review),
            "evidenceRefExamples": [
                "chapter-001#scene-1",
                "chapter-001#paragraph-4",
                "chapter-001#world-rule-onboarding",
                "chapter-002#handoff-gap",
                f"review-packet:{preflight_payload.get('volumeId', '')}:chapter-001",
            ],
            "recommendedCommands": [
                f"review preflight --root <root> --volume-id {preflight_payload.get('volumeId', '')}",
                f"workflow status --root <root> --volume-id {preflight_payload.get('volumeId', '')}",
                f"export --root <root> --format review-packet --volume-id {preflight_payload.get('volumeId', '')}",
            ],
        },
    }
    return template


def _normalize_scores(raw_scores: Any) -> list[Dict[str, Any]]:
    if not isinstance(raw_scores, list):
        raise ValueError("scores 必须是数组。")
    normalized_by_id: Dict[str, Dict[str, Any]] = {}
    for index, item in enumerate(raw_scores, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"scores[{index}] 必须是对象。")
        dimension_id = _require_choice(
            item.get("dimensionId"),
            f"scores[{index}].dimensionId",
            tuple(VOLUME_SELF_REVIEW_DIMENSION_LABELS.keys()),
        )
        if dimension_id in normalized_by_id:
            raise ValueError(f"scores 中存在重复维度: {dimension_id}")
        score = item.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > 5:
            raise ValueError(f"scores[{index}].score 必须是 0..5 的整数。")
        normalized_by_id[dimension_id] = {
            "dimensionId": dimension_id,
            "label": VOLUME_SELF_REVIEW_DIMENSION_LABELS[dimension_id],
            "score": score,
            "conclusion": _require_non_empty_string(
                item.get("conclusion"),
                f"scores[{index}].conclusion",
            ),
        }
    missing_dimension_ids = [
        dimension_id
        for dimension_id, _ in VOLUME_SELF_REVIEW_DIMENSIONS
        if dimension_id not in normalized_by_id
    ]
    if missing_dimension_ids:
        raise ValueError(
            "scores 缺少必填维度: " + ", ".join(missing_dimension_ids)
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
                "fixAction": _require_non_empty_string(
                    item.get("fixAction"),
                    f"issues[{index}].fixAction",
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
    score_summary = latest_review.get("scoreSummary", {})
    return {
        "generatedAt": latest_review.get("generatedAt", ""),
        "closureStatus": conclusion.get("closureStatus", ""),
        "declaredAllowHumanReview": conclusion.get("allowHumanReview"),
        "finalAllowHumanReview": latest_review.get("finalAllowHumanReview"),
        "strongestPoint": conclusion.get("strongestPoint", ""),
        "biggestRisk": conclusion.get("biggestRisk", ""),
        "averageScore": score_summary.get("average"),
        "lowestDimensions": score_summary.get("lowestDimensions", []),
        "topRepairSuggestions": list(latest_review.get("repairSuggestions", []))[:3],
    }


def _build_repair_coverage(
    normalized_scores: list[Dict[str, Any]],
    *,
    issues: list[Dict[str, Any]],
    repair_suggestions: list[str],
) -> Dict[str, Any]:
    weak_dimensions = [
        item.get("dimensionId", "")
        for item in normalized_scores
        if item.get("score", 0) <= 2
    ]
    uncovered = _find_uncovered_weak_dimensions(
        weak_dimensions,
        issues=issues,
        repair_suggestions=repair_suggestions,
    )
    return {
        "weakDimensionIds": weak_dimensions,
        "weakDimensionLabels": [
            VOLUME_SELF_REVIEW_DIMENSION_LABELS[item]
            for item in weak_dimensions
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
) -> list[str]:
    issue_texts = []
    for item in issues:
        issue_texts.append(str(item.get("issue", "")))
        issue_texts.append(str(item.get("impact", "")))
        issue_texts.append(str(item.get("fixAction", "")))
    issue_texts.extend(repair_suggestions)
    uncovered = []
    for dimension_id in weak_dimensions:
        if not _dimension_keywords_hit(dimension_id, issue_texts):
            uncovered.append(dimension_id)
    return uncovered


def _dimension_keywords_hit(dimension_id: str, texts: Iterable[str]) -> bool:
    keywords = VOLUME_SELF_REVIEW_DIMENSION_KEYWORDS.get(dimension_id, ())
    if not keywords:
        return True
    combined = " ".join(str(item) for item in texts if item).lower()
    if not combined:
        return False
    return any(keyword.lower() in combined for keyword in keywords)
