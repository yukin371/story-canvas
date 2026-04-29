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
    resolve_review_rule_profile,
    load_review_rules,
    resolve_review_rule_profile_name,
    resolve_state_path,
)
from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.services import (
    hydrate_workflow_progress,
    infer_volume_preflight_workflow,
    infer_workflow_status,
    latest_volume_self_review,
)
from story_harness_cli.services.reference_mentions import build_reference_mention_report
from story_harness_cli.utils import stable_hash
from story_harness_cli.utils.text import count_words, paragraphs_from_text, strip_entity_tags, strip_markdown


def _ordered_outline_chapters(state: dict[str, Any]) -> list[dict[str, Any]]:
    outline = state.get("outline", {})
    volumes = outline.get("volumes", [])
    if volumes:
        chapters: list[dict[str, Any]] = []
        for volume in volumes:
            chapters.extend(volume.get("chapters", []))
        return chapters
    return outline.get("chapters", [])


def _chapter_title(state: dict[str, Any], chapter_id: str | None) -> str:
    if not chapter_id:
        return ""
    chapter_entry = _find_outline_chapter(state, chapter_id)
    return str(chapter_entry.get("title") or chapter_id)


def _find_outline_chapter(state: dict[str, Any], chapter_id: str) -> dict[str, Any]:
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return chapter
    for chapter in state.get("outline", {}).get("chapters", []):
        if chapter.get("id") == chapter_id:
            return chapter
    return {}


def _find_detailed_entry(state: dict[str, Any], chapter_id: str) -> dict[str, Any]:
    for entry in state.get("detailed_outlines", {}).get("entries", []):
        if entry.get("chapterId") == chapter_id:
            return entry
    return {}


def _find_volume_for_chapter(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    if not chapter_id:
        return {}
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return {}


def _find_volume_by_id(state: dict[str, Any], volume_id: str | None) -> dict[str, Any]:
    if not volume_id:
        return {}
    for volume in state.get("outline", {}).get("volumes", []):
        if volume.get("id") == volume_id:
            return volume
    return {}


def _resolve_target_chapter_id(state: dict[str, Any], explicit_chapter_id: str | None) -> str | None:
    if explicit_chapter_id:
        return explicit_chapter_id
    active_chapter_id = state.get("project", {}).get("activeChapterId")
    if active_chapter_id:
        return active_chapter_id
    context_chapter_id = state.get("context_lens", {}).get("currentChapterId")
    if context_chapter_id:
        return context_chapter_id
    for chapter in _ordered_outline_chapters(state):
        chapter_id = chapter.get("id")
        if chapter_id:
            return chapter_id
    return None


def _collect_chapter_files(root: Path, state: dict[str, Any], explicit_chapter_id: str | None) -> dict[str, bool]:
    chapter_ids = {
        item.get("id")
        for item in _ordered_outline_chapters(state)
        if item.get("id")
    }
    if explicit_chapter_id:
        chapter_ids.add(explicit_chapter_id)
    return {chapter_id: chapter_path(root, chapter_id).exists() for chapter_id in chapter_ids if chapter_id}


def _collect_chapter_file_signatures(root: Path, state: dict[str, Any], explicit_chapter_id: str | None) -> dict[str, str]:
    chapter_ids = {
        item.get("id")
        for item in _ordered_outline_chapters(state)
        if item.get("id")
    }
    if explicit_chapter_id:
        chapter_ids.add(explicit_chapter_id)
    signatures: dict[str, str] = {}
    for chapter_id in chapter_ids:
        if not chapter_id:
            continue
        path = chapter_path(root, chapter_id)
        signatures[chapter_id] = stable_hash(path.read_text(encoding="utf-8")) if path.exists() else ""
    return signatures


def _latest_matching(items: list[dict[str, Any]], predicate) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for item in items:
        if predicate(item):
            latest = item
    return latest


def _latest_scene_reviews(scene_reviews: list[dict[str, Any]], chapter_id: str | None) -> list[dict[str, Any]]:
    if not chapter_id:
        return []
    latest_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    order: list[tuple[Any, ...]] = []
    for review in scene_reviews:
        if review.get("chapterId") != chapter_id:
            continue
        scene_range = review.get("sceneRange", {})
        if scene_range.get("scenePlanId"):
            key = ("scenePlanId", scene_range.get("scenePlanId"))
        elif scene_range.get("sceneIndex") is not None:
            key = ("sceneIndex", scene_range.get("sceneIndex"))
        else:
            key = (
                "paragraphRange",
                scene_range.get("startParagraph"),
                scene_range.get("endParagraph"),
            )
        if key not in latest_by_key:
            order.append(key)
        latest_by_key[key] = review

    result = [latest_by_key[key] for key in order]
    result.sort(
        key=lambda item: (
            item.get("sceneRange", {}).get("sceneIndex", 999999),
            item.get("sceneRange", {}).get("startParagraph", 999999),
        )
    )
    return result


def _count_by_status(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _build_project_summary(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    project = state.get("project", {})
    chapters = _ordered_outline_chapters(state)
    active_chapter_id = project.get("activeChapterId")
    review_rule_config = _build_review_rule_config_summary(root)
    return {
        "root": str(root),
        "title": project.get("title", ""),
        "genre": project.get("genre", ""),
        "defaultMode": project.get("defaultMode", ""),
        "activeChapterId": active_chapter_id,
        "activeChapterTitle": _chapter_title(state, active_chapter_id),
        "chapterCount": len(chapters),
        "volumeCount": len(state.get("outline", {}).get("volumes", [])),
        "chapterStatusCounts": _count_by_status(chapters),
        "reviewRuleConfig": review_rule_config,
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
        "createdAt": project.get("createdAt", ""),
        "updatedAt": project.get("updatedAt", ""),
    }


def _build_review_rule_config_summary(root: Path) -> dict[str, Any]:
    config_path = root / "review-rules.yaml"
    if not config_path.exists():
        return {
            "exists": False,
            "configPath": str(config_path),
            "requestedProfile": "default",
            "resolvedProfile": "default",
            "profileSource": "builtin",
            "enabledRuleCount": 0,
            "exemptionCount": 0,
        }

    config = load_review_rules(root)
    requested_profile, resolved_profile = resolve_review_rule_profile_name(config)
    profile, _, source = resolve_review_rule_profile(root, resolved_profile)
    return {
        "exists": True,
        "configPath": str(config_path),
        "requestedProfile": requested_profile,
        "resolvedProfile": resolved_profile,
        "profileSource": source,
        "enabledRuleCount": len(profile.get("enabledRules", [])),
        "exemptionCount": len(profile.get("exemptions", [])),
    }


def _build_target_volume_summary(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    volume = _find_volume_for_chapter(state, chapter_id)
    if not volume:
        return {
            "exists": False,
            "volumeId": "",
            "title": "",
            "theme": "",
            "chapterCount": 0,
            "completedChapterCount": 0,
            "currentChapterIndex": None,
        }
    chapters = volume.get("chapters", [])
    current_index = None
    for index, chapter in enumerate(chapters, start=1):
        if chapter.get("id") == chapter_id:
            current_index = index
            break
    return {
        "exists": True,
        "volumeId": volume.get("id", ""),
        "title": volume.get("title", ""),
        "theme": volume.get("theme", ""),
        "chapterCount": len(chapters),
        "completedChapterCount": sum(1 for item in chapters if item.get("status") == "completed"),
        "currentChapterIndex": current_index,
    }


def _build_target_volume_summary_by_id(state: dict[str, Any], volume_id: str | None) -> dict[str, Any]:
    volume = _find_volume_by_id(state, volume_id)
    if not volume:
        return {
            "exists": False,
            "volumeId": volume_id or "",
            "title": "",
            "theme": "",
            "chapterCount": 0,
            "completedChapterCount": 0,
            "currentChapterIndex": None,
        }
    chapters = volume.get("chapters", [])
    return {
        "exists": True,
        "volumeId": volume.get("id", ""),
        "title": volume.get("title", ""),
        "theme": volume.get("theme", ""),
        "chapterCount": len(chapters),
        "completedChapterCount": sum(1 for item in chapters if item.get("status") == "completed"),
        "currentChapterIndex": None,
    }


def _scene_plan_status(scene_plans: list[dict[str, Any]], paragraph_count: int | None) -> dict[str, Any]:
    if paragraph_count is None:
        return {
            "scenePlanCount": len(scene_plans),
            "valid": None,
            "invalidScenePlans": [],
        }

    invalid_items: list[dict[str, Any]] = []
    for index, scene in enumerate(scene_plans, start=1):
        start = scene.get("startParagraph")
        end = scene.get("endParagraph")
        if not isinstance(start, int) or not isinstance(end, int):
            invalid_items.append(
                {
                    "scenePlanId": scene.get("id", ""),
                    "title": scene.get("title", ""),
                    "index": index,
                    "issue": "missing-range",
                }
            )
            continue
        if start < 1 or end < start or end > paragraph_count:
            invalid_items.append(
                {
                    "scenePlanId": scene.get("id", ""),
                    "title": scene.get("title", ""),
                    "index": index,
                    "startParagraph": start,
                    "endParagraph": end,
                    "issue": "out-of-range",
                }
            )

    return {
        "scenePlanCount": len(scene_plans),
        "valid": len(invalid_items) == 0,
        "invalidScenePlans": invalid_items,
    }


def _build_mention_hygiene_summary(state: dict[str, Any], chapter_text: str | None) -> dict[str, Any]:
    if not chapter_text:
        return {
            "exists": False,
            "knownUnwrappedCount": 0,
            "taggedMissingCount": 0,
            "ignoredQuotedKnownMentionCount": 0,
            "topKnownUnwrapped": [],
            "topTaggedMissing": [],
        }

    report = build_reference_mention_report(state, chapter_text)
    known_unwrapped = sorted(
        report.get("knownUnwrapped", []),
        key=lambda item: (-int(item.get("plainCount", 0) or 0), item.get("name", "")),
    )
    tagged_missing = sorted(
        report.get("taggedMissing", []),
        key=lambda item: (-int(item.get("occurrenceCount", 0) or 0), item.get("name", "")),
    )
    ignored_quoted = sorted(
        report.get("ignoredQuotedKnownMentions", []),
        key=lambda item: (-int(item.get("quotedCount", 0) or 0), item.get("name", "")),
    )
    return {
        "exists": True,
        "knownUnwrappedCount": report.get("summary", {}).get("knownUnwrappedCount", 0),
        "taggedMissingCount": report.get("summary", {}).get("taggedMissingCount", 0),
        "ignoredQuotedKnownMentionCount": report.get("summary", {}).get("ignoredQuotedKnownMentionCount", 0),
        "topKnownUnwrapped": known_unwrapped[:3],
        "topTaggedMissing": tagged_missing[:3],
        "topIgnoredQuotedKnownMentions": ignored_quoted[:3],
    }


def _build_target_chapter_summary(root: Path, state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    if not chapter_id:
        return {
            "exists": False,
            "chapterId": "",
            "title": "",
            "status": "",
            "chapterFileExists": False,
            "chapterFile": "",
            "wordCount": 0,
            "paragraphCount": 0,
            "directionReady": False,
            "beatCount": 0,
            "completedBeatCount": 0,
            "scenePlanStatus": _scene_plan_status([], None),
            "mentionHygiene": _build_mention_hygiene_summary(state, None),
        }

    chapter_entry = _find_outline_chapter(state, chapter_id)
    detailed_entry = _find_detailed_entry(state, chapter_id)
    chapter_file = chapter_path(root, chapter_id)
    chapter_text = chapter_file.read_text(encoding="utf-8") if chapter_file.exists() else ""
    paragraphs = paragraphs_from_text(chapter_text) if chapter_text else []
    clean_text = strip_markdown(strip_entity_tags(chapter_text)) if chapter_text else ""

    direction = detailed_entry.get("direction") or chapter_entry.get("direction", "")
    beats = detailed_entry.get("beats") or chapter_entry.get("beats", [])
    scene_plans = detailed_entry.get("scenePlans") or chapter_entry.get("scenePlans", [])
    missing_codes: list[str] = []
    if not direction:
        missing_codes.append("missing-direction")
    if not beats:
        missing_codes.append("missing-beats")
    if not scene_plans:
        missing_codes.append("missing-scene-plans")

    return {
        "exists": bool(chapter_entry),
        "chapterId": chapter_id,
        "title": chapter_entry.get("title", chapter_id),
        "status": chapter_entry.get("status", ""),
        "chapterFileExists": chapter_file.exists(),
        "chapterFile": str(chapter_file),
        "wordCount": count_words(clean_text) if clean_text else 0,
        "paragraphCount": len(paragraphs),
        "directionReady": bool(direction),
        "direction": direction,
        "beatCount": len(beats),
        "completedBeatCount": sum(1 for item in beats if item.get("status") == "completed"),
        "scenePlanStatus": _scene_plan_status(scene_plans, len(paragraphs) if chapter_file.exists() else None),
        "mentionHygiene": _build_mention_hygiene_summary(state, chapter_text if chapter_file.exists() else None),
        "startGuide": build_chapter_start_guide(root, chapter_id, missing_codes=missing_codes),
    }


def _build_context_summary(state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    context_lens = state.get("context_lens", {})
    lens = _latest_matching(
        context_lens.get("lenses", []),
        lambda item: item.get("chapterId") == chapter_id,
    )
    if not lens:
        return {
            "exists": False,
            "currentChapterId": context_lens.get("currentChapterId"),
            "chapterId": chapter_id,
            "activeCharacterCount": 0,
            "activeRelationCount": 0,
            "dueForeshadowCount": 0,
            "pendingChangeRequestCount": 0,
            "hasChapterHandoff": False,
            "updatedAt": "",
        }
    return {
        "exists": True,
        "currentChapterId": context_lens.get("currentChapterId"),
        "chapterId": chapter_id,
        "activeCharacterCount": len(lens.get("activeCharacters", [])),
        "activeRelationCount": len(lens.get("activeRelations", [])),
        "dueForeshadowCount": len(lens.get("dueForeshadows", [])),
        "pendingChangeRequestCount": lens.get("pendingChangeRequestCount", 0),
        "hasChapterHandoff": bool(lens.get("chapterHandoff")),
        "updatedAt": lens.get("updatedAt", ""),
    }


def _build_change_request_summary(state: dict[str, Any]) -> dict[str, Any]:
    requests = state.get("reviews", {}).get("changeRequests", [])
    return {
        "total": len(requests),
        "statusCounts": _count_by_status(requests),
        "pendingCount": sum(1 for item in requests if item.get("status") == "pending"),
    }


def _build_chapter_review_summary(chapter_review: dict[str, Any]) -> dict[str, Any]:
    if not chapter_review:
        return {
            "exists": False,
            "reviewId": "",
            "generatedAt": "",
            "rating": "",
            "totalScore": None,
            "weightedTotalScore": None,
            "summary": "",
            "priorityActions": [],
            "ruleJudgementCount": 0,
        }
    weighted_scores = chapter_review.get("weightedScores", {})
    return {
        "exists": True,
        "reviewId": chapter_review.get("reviewId", ""),
        "generatedAt": chapter_review.get("generatedAt", ""),
        "rating": chapter_review.get("rating", ""),
        "totalScore": chapter_review.get("scores", {}).get("total"),
        "weightedTotalScore": weighted_scores.get("total"),
        "summary": chapter_review.get("summary", ""),
        "priorityActions": list(chapter_review.get("priorityActions", []))[:3],
        "ruleJudgementCount": len(chapter_review.get("ruleJudgements", [])),
    }


def _build_scene_review_summary(scene_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    latest = scene_reviews[-1] if scene_reviews else {}
    if not latest:
        return {
            "count": 0,
            "latest": {
                "exists": False,
                "reviewId": "",
                "generatedAt": "",
                "rating": "",
                "totalScore": None,
                "summary": "",
                "sceneRange": {},
            },
        }
    return {
        "count": len(scene_reviews),
        "latest": {
            "exists": True,
            "reviewId": latest.get("reviewId", ""),
            "generatedAt": latest.get("generatedAt", ""),
            "rating": latest.get("rating", ""),
            "totalScore": latest.get("scores", {}).get("total"),
            "summary": latest.get("summary", ""),
            "sceneRange": latest.get("sceneRange", {}),
        },
    }


def _build_volume_self_review_summary(state: dict[str, Any], volume_id: str | None) -> dict[str, Any]:
    if not volume_id:
        return {
            "exists": False,
            "volumeId": "",
            "generatedAt": "",
            "closureStatus": "",
            "declaredAllowHumanReview": None,
            "finalAllowHumanReview": None,
            "editorPassCompleted": None,
            "editorMode": "",
            "editorContextIsolation": "",
            "editorVerdict": "",
            "strongestPoint": "",
            "biggestRisk": "",
            "averageScore": None,
            "lowestDimensions": [],
            "gateFailureCount": 0,
            "repairCoverageStatus": "",
            "weakDimensionLabels": [],
            "uncoveredWeakDimensionLabels": [],
            "topRepairSuggestions": [],
        }
    review = latest_volume_self_review(state.get("story_reviews", {}), volume_id)
    if not review:
        return {
            "exists": False,
            "volumeId": volume_id,
            "generatedAt": "",
            "closureStatus": "",
            "declaredAllowHumanReview": None,
            "finalAllowHumanReview": None,
            "editorPassCompleted": None,
            "editorMode": "",
            "editorContextIsolation": "",
            "editorVerdict": "",
            "strongestPoint": "",
            "biggestRisk": "",
            "averageScore": None,
            "lowestDimensions": [],
            "gateFailureCount": 0,
            "repairCoverageStatus": "",
            "weakDimensionLabels": [],
            "uncoveredWeakDimensionLabels": [],
            "topRepairSuggestions": [],
        }
    conclusion = review.get("conclusion", {})
    editor_pass = review.get("editorPass", {})
    editor_assessment = review.get("editorAssessment", {})
    score_summary = review.get("scoreSummary", {})
    repair_coverage = review.get("repairCoverage", {})
    return {
        "exists": True,
        "volumeId": review.get("volumeId", volume_id),
        "generatedAt": review.get("generatedAt", ""),
        "closureStatus": conclusion.get("closureStatus", ""),
        "declaredAllowHumanReview": conclusion.get("allowHumanReview"),
        "finalAllowHumanReview": review.get("finalAllowHumanReview"),
        "editorPassCompleted": editor_pass.get("completed"),
        "editorMode": editor_pass.get("mode", ""),
        "editorContextIsolation": editor_pass.get("contextIsolation", ""),
        "editorVerdict": editor_assessment.get("overallVerdict", ""),
        "strongestPoint": conclusion.get("strongestPoint", ""),
        "biggestRisk": conclusion.get("biggestRisk", ""),
        "averageScore": score_summary.get("average"),
        "lowestDimensions": score_summary.get("lowestDimensions", []),
        "gateFailureCount": len(review.get("gateFailures", [])),
        "repairCoverageStatus": repair_coverage.get("status", ""),
        "weakDimensionLabels": repair_coverage.get("weakDimensionLabels", []),
        "uncoveredWeakDimensionLabels": repair_coverage.get("uncoveredWeakDimensionLabels", []),
        "topRepairSuggestions": list(review.get("repairSuggestions", []))[:3],
    }


def _build_style_summary(chapter_review: dict[str, Any]) -> dict[str, Any]:
    style_report = chapter_review.get("styleAnalysis", {}) if chapter_review else {}
    style_analysis = style_report.get("styleAnalysis", {}) if isinstance(style_report, dict) else {}
    pattern_results = style_analysis.get("patternResults", []) if isinstance(style_analysis, dict) else []
    detected_patterns = [
        item.get("label") or item.get("id")
        for item in pattern_results
        if item.get("detected")
    ]
    return {
        "exists": bool(style_report),
        "source": "chapter-review" if style_report else "none",
        "profile": style_report.get("profile", ""),
        "profileSource": style_report.get("profileSource", ""),
        "overallScore": style_analysis.get("overallScore"),
        "totalDeduction": style_analysis.get("totalDeduction"),
        "summary": style_analysis.get("summary", ""),
        "detectedPatterns": detected_patterns[:5],
    }


def _sum_nested_list_values(payload: dict[str, Any]) -> int:
    total = 0
    for value in payload.values():
        if isinstance(value, list):
            total += len(value)
    return total


def _build_consistency_summary(root: Path, chapter_id: str | None, chapter_review: dict[str, Any]) -> dict[str, Any]:
    if not chapter_id:
        return {
            "exists": False,
            "source": "none",
            "checkedAt": "",
            "hardConflictCount": 0,
            "softWarningCount": 0,
            "settingCandidateCount": 0,
            "settingConflictCount": 0,
            "unintroducedNameRevealCount": 0,
            "capabilityTaskRiskCount": 0,
            "powerProgressionConflictCount": 0,
        }

    check_path = root / "projections" / f"consistency-check-{chapter_id}.yaml"
    if check_path.exists():
        payload = load_json_compatible_yaml(check_path, {})
        return {
            "exists": True,
            "source": "check-file",
            "checkFile": str(check_path),
            "checkedAt": payload.get("checkedAt", ""),
            "hardConflictCount": _sum_nested_list_values(payload.get("hardChecks", {})),
            "softWarningCount": _sum_nested_list_values(payload.get("softChecks", {})),
            "settingCandidateCount": len(payload.get("settingCandidates", [])),
            "settingConflictCount": len(payload.get("settingConflicts", [])),
            "unintroducedNameRevealCount": len(payload.get("unintroducedNameReveals", [])),
            "capabilityTaskRiskCount": len(payload.get("capabilityTaskRisks", [])),
            "powerProgressionConflictCount": len(payload.get("powerProgressionConflicts", [])),
        }

    signals = chapter_review.get("consistencySignals", {}) if chapter_review else {}
    return {
        "exists": bool(signals),
        "source": "chapter-review" if signals else "none",
        "checkFile": str(check_path),
        "checkedAt": chapter_review.get("generatedAt", "") if signals else "",
        "hardConflictCount": 0,
        "softWarningCount": 0,
        "settingCandidateCount": len(signals.get("settingCandidates", [])),
        "settingConflictCount": len(signals.get("settingConflicts", [])),
        "unintroducedNameRevealCount": len(signals.get("unintroducedNameReveals", [])),
        "capabilityTaskRiskCount": len(signals.get("capabilityTaskRisks", [])),
        "powerProgressionConflictCount": len(signals.get("powerProgressionConflicts", [])),
    }


def _build_review_summary(root: Path, state: dict[str, Any], chapter_id: str | None, volume_id: str | None) -> dict[str, Any]:
    story_reviews = state.get("story_reviews", {})
    chapter_review = _latest_matching(
        story_reviews.get("chapterReviews", []),
        lambda item: item.get("chapterId") == chapter_id,
    )
    scene_reviews = _latest_scene_reviews(
        story_reviews.get("sceneReviews", []),
        chapter_id,
    )
    return {
        "changeRequests": _build_change_request_summary(state),
        "chapterReview": _build_chapter_review_summary(chapter_review),
        "sceneReviews": _build_scene_review_summary(scene_reviews),
        "style": _build_style_summary(chapter_review),
        "consistency": _build_consistency_summary(root, chapter_id, chapter_review),
        "volumeSelfReview": _build_volume_self_review_summary(state, volume_id),
    }


def _build_workflow_summary(root: Path, state: dict[str, Any], chapter_id: str | None) -> dict[str, Any]:
    workflow_file = resolve_state_path(root, "workflow_progress")
    inferred = infer_workflow_status(
        state,
        chapter_id=chapter_id,
        chapter_files=_collect_chapter_files(root, state, chapter_id),
        chapter_file_signatures=_collect_chapter_file_signatures(root, state, chapter_id),
    )
    workflow_progress = hydrate_workflow_progress(state.get("workflow_progress", {}), inferred)
    current_stage = workflow_progress["currentStage"]
    current_stage_payload = workflow_progress["stageResults"][current_stage]
    return {
        "workflowFile": str(workflow_file),
        "workflowFileExists": workflow_file.exists(),
        "stateSource": "persisted" if workflow_file.exists() else "inferred",
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
        "currentStage": current_stage,
        "workflowStatus": workflow_progress["workflowStatus"],
        "inferredCurrentStage": inferred["currentStage"],
        "inferredWorkflowStatus": inferred["workflowStatus"],
        "targetChapterId": workflow_progress.get("targetChapterId"),
        "targetChapterTitle": inferred.get("targetChapterTitle", ""),
        "currentGateDecision": current_stage_payload.get("gateDecision", {}),
        "nextActions": list(current_stage_payload.get("nextActions", []))[:3],
        "startGuide": (
            build_chapter_start_guide(
                root,
                workflow_progress.get("targetChapterId") or chapter_id or "",
                missing_codes=list(
                    workflow_progress["stageResults"].get("outline_ready", {}).get("gateDecision", {}).get(
                        "blockingRules", []
                    )
                ),
            )
            if (workflow_progress.get("targetChapterId") or chapter_id)
            else {}
        ),
    }


def _build_volume_workflow_summary(root: Path, state: dict[str, Any], volume_id: str) -> dict[str, Any]:
    preflight_payload = build_review_preflight_payload(root, state, volume_id=volume_id)
    volume_self_review = latest_volume_self_review(state.get("story_reviews", {}), volume_id)
    workflow = infer_volume_preflight_workflow(preflight_payload, volume_self_review)
    return {
        "scope": "volume",
        "projectAdvisories": build_project_advisories(root, include_prd_content=True),
        "currentStage": workflow["currentStage"],
        "workflowStatus": workflow["workflowStatus"],
        "stageOrder": workflow["stageOrder"],
        "currentGateDecision": workflow["currentGateDecision"],
        "nextActions": list(workflow.get("nextActions", []))[:3],
        "preflightSummary": workflow.get("preflightSummary", {}),
        "volumeSelfReview": workflow.get("volumeSelfReview", {}),
    }


def command_status(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    if args.chapter_id and args.volume_id:
        raise SystemExit("`--chapter-id` 与 `--volume-id` 不能同时使用")
    if args.volume_id:
        volume = _find_volume_by_id(state, args.volume_id)
        if not volume:
            raise SystemExit(f"volume 不存在: {args.volume_id}")
        payload = {
            "scope": "volume",
            "project": _build_project_summary(root, state),
            "targetVolume": _build_target_volume_summary_by_id(state, args.volume_id),
            "targetChapter": _build_target_chapter_summary(root, state, None),
            "context": _build_context_summary(state, None),
            "reviewStatus": _build_review_summary(root, state, None, args.volume_id),
            "workflow": _build_volume_workflow_summary(root, state, args.volume_id),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    chapter_id = _resolve_target_chapter_id(state, args.chapter_id)
    volume_id = _find_volume_for_chapter(state, chapter_id).get("id", "")

    payload = {
        "scope": "chapter",
        "project": _build_project_summary(root, state),
        "targetVolume": _build_target_volume_summary(state, chapter_id),
        "targetChapter": _build_target_chapter_summary(root, state, chapter_id),
        "context": _build_context_summary(state, chapter_id),
        "reviewStatus": _build_review_summary(root, state, chapter_id, volume_id),
        "workflow": _build_workflow_summary(root, state, chapter_id),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def register_status_commands(subparsers) -> None:
    status_parser = subparsers.add_parser("status", help="Show aggregated project, chapter, review, and workflow status")
    status_parser.add_argument("--root", required=True)
    status_parser.add_argument("--chapter-id")
    status_parser.add_argument("--volume-id")
    status_parser.set_defaults(func=command_status)
