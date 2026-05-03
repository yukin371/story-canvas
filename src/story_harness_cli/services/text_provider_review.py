from __future__ import annotations

import json
import re
from typing import Any

from .volume_self_review import VOLUME_SELF_REVIEW_DIMENSIONS


EDITOR_OUTPUT_SCHEMA = {
    "editorPass": {
        "completed": True,
        "reviewerRole": "editor",
        "mode": "independent_agent",
        "contextIsolation": "no_context_proxy",
        "notes": "Brief source and scope note.",
    },
    "editorAssessment": {
        "overallVerdict": "pass|revise|block",
        "summaryComment": "One concise paragraph.",
        "topProblems": ["Problem 1"],
        "improvementPoints": ["Action 1"],
        "scores": [
            {"dimensionId": dimension_id, "score": 3, "conclusion": label}
            for dimension_id, label in VOLUME_SELF_REVIEW_DIMENSIONS
        ],
    },
}



# Enhanced review provider functions for clean-room reviews with issue-diagnosis-suggestion pattern
ENHANCED_REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reviewId": {"type": "string"},
        "generatedAt": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["critical", "major", "moderate", "minor"]},
                    "category": {"type": "string", "enum": ["plot", "character", "style", "consistency", "foreshadowing", "handoff"]},
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "suggestion": {"type": "string"},
                                "example": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["severity", "category", "description", "suggestions"],
            },
        },
        "issueSummary": {
            "type": "object",
            "properties": {
                "critical": {"type": "integer"},
                "major": {"type": "integer"},
                "moderate": {"type": "integer"},
                "minor": {"type": "integer"},
                "total": {"type": "integer"},
            },
        },
        "overallVerdict": {"type": "string", "enum": ["pass", "revise", "block"]},
        "summary": {"type": "string"},
    },
    "required": ["issues", "issueSummary", "overallVerdict", "summary"],
}


def build_enhanced_review_provider_prompt(
    state: dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    review_type: str = "chapter",  # "chapter" or "scene"
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    构建增强审查的provider提示
    Build enhanced review provider prompt with issue-diagnosis-suggestion pattern
    """
    context = context or {}
    project = state.get("project", {})
    outline = state.get("outline", {})

    # 获取章节信息
    chapter = None
    for volume in outline.get("volumes", []):
        for ch in volume.get("chapters", []):
            if ch.get("id") == chapter_id:
                chapter = ch
                break
        if chapter:
            break

    chapter_title_val = chapter.get("title", "") if chapter else chapter_id
    genre = project.get("genre", "")
    core_promises = project.get("corePromises", [])

    # 构建系统提示 - 强调clean-room审查
    system_prompt = (
        "You are an independent story editor for Story Canvas. "
        "You must provide objective analysis based only on the provided text. "
        "Do not make assumptions about prior context or authorial intent. "
        "Focus on identifying concrete issues with specific evidence and actionable suggestions. "
        "Return only one strict JSON object. Do not wrap it in Markdown."
    )

    # 构建用户载荷
    user_payload = {
        "task": f"Provide enhanced {review_type} review with issue-diagnosis-suggestion pattern",
        "project": {
            "genre": genre,
            "corePromises": core_promises,
        },
        "chapter": {
            "chapterId": chapter_id,
            "chapterTitle": chapter_title_val,
        },
        "text": {
            "wordCount": len(chapter_text.split()),
            "preview": chapter_text[:500] + "..." if len(chapter_text) > 500 else chapter_text,
        },
        "reviewFocus": [
            "Plot momentum and progression",
            "Character pressure and agency",
            "Conflict and tension",
            "Scene clarity and transitions",
            "Prose control and style",
        ],
        "outputFormat": {
            "issues": "Array of structured issues with severity, category, location, description, evidence, and suggestions",
            "issueSummary": "Count of issues by severity level",
            "overallVerdict": "One of: pass, revise, block",
            "summary": "Brief overall assessment",
        },
        "guidelines": {
            "severity": {
                "critical": "Fundamental problems that prevent the story from working",
                "major": "Significant issues that affect reader experience",
                "moderate": "Areas that could be improved",
                "minor": "Small suggestions and polish opportunities",
            },
            "categories": {
                "plot": "Story progression, momentum, causality",
                "character": "Character agency, pressure, consistency",
                "style": "Prose, dialogue, pacing",
                "consistency": "Internal logic, entity references",
                "foreshadowing": "Setup and payoff effectiveness",
                "handoff": "Chapter transitions and continuity",
            },
            "evidence": "Quote specific text passages that support your analysis",
            "suggestions": "Provide concrete, actionable improvements with examples",
        },
        "outputContract": ENHANCED_REVIEW_OUTPUT_SCHEMA,
    }

    # 添加上下文信息
    if context.get("previous_chapter_ending"):
        user_payload["context"] = {
            "previousChapterEnding": context["previous_chapter_ending"][:200],
        }

    user_prompt = json.dumps(user_payload, ensure_ascii=False, indent=2)

    return {
        "systemPrompt": system_prompt,
        "userPrompt": user_prompt,
        "expectedOutput": ENHANCED_REVIEW_OUTPUT_SCHEMA,
        "chapterId": chapter_id,
        "reviewType": review_type,
    }


def parse_enhanced_review_response(response_text: str) -> dict[str, Any]:
    """
    解析增强审查响应
    Parse enhanced review response from provider
    """
    # 尝试提取JSON
    cleaned = _strip_fenced_json(response_text)
    try:
        data = json.loads(cleaned)

        # 验证基本结构
        if "issues" not in data:
            data["issues"] = []
        if "issueSummary" not in data:
            # 自动计算issueSummary
            issues = data.get("issues", [])
            data["issueSummary"] = {
                "critical": len([i for i in issues if i.get("severity") == "critical"]),
                "major": len([i for i in issues if i.get("severity") == "major"]),
                "moderate": len([i for i in issues if i.get("severity") == "moderate"]),
                "minor": len([i for i in issues if i.get("severity") == "minor"]),
                "total": len(issues),
            }

        return data
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse JSON: {e}",
            "rawResponse": response_text[:500],
            "issues": [],
            "issueSummary": {"critical": 0, "major": 0, "moderate": 0, "minor": 0, "total": 0},
        }


def build_setting_review_provider_prompt(
    state: dict[str, Any],
    focus_area: str | None = None,
) -> dict[str, Any]:
    """
    构建设定审查的provider提示
    Build setting review provider prompt
    """
    project = state.get("project", {})
    world = state.get("world", {})

    genre = project.get("genre", "")
    core_promises = project.get("corePromises", [])

    world_items = world.get("items", [])
    entities = world.get("entities", {})
    characters = [e for e in entities.values() if e.get("kind") == "character"]

    system_prompt = (
        "You are an independent story setting analyst for Story Canvas. "
        "Evaluate the completeness and consistency of story settings based on the provided information. "
        "Return only one strict JSON object. Do not wrap it in Markdown."
    )

    user_payload = {
        "task": "Analyze story setting completeness and provide expansion recommendations",
        "project": {
            "genre": genre,
            "corePromises": core_promises,
        },
        "currentSetting": {
            "worldItemCount": len(world_items),
            "characterCount": len(characters),
            "items": world_items[:10],  # 只发送前10个以控制token
            "characters": [
                {"name": c.get("name"), "brief": c.get("brief")}
                for c in characters[:10]
            ],
        },
        "reviewCriteria": {
            "completeness": "Adequate coverage of setting elements for the genre",
            "consistency": "Internal logic and coherence",
            "depth": "Richness of detail and development",
            "relevance": "Alignment with core promises and genre expectations",
        },
        "outputFormat": {
            "readinessPercent": "0-100 score",
            "readinessLevel": "ready/adequate/needs_work/inadequate",
            "issues": "Array of identified gaps or problems",
            "recommendations": "Array of specific, actionable suggestions",
            "expansionSuggestions": "Array of new setting ideas to explore",
        },
    }

    if focus_area:
        user_payload["focusArea"] = focus_area

    user_prompt = json.dumps(user_payload, ensure_ascii=False, indent=2)

    return {
        "systemPrompt": system_prompt,
        "userPrompt": user_prompt,
        "genre": genre,
        "focusArea": focus_area,
    }


def parse_setting_review_response(response_text: str) -> dict[str, Any]:
    """
    解析设定审查响应
    Parse setting review response from provider
    """
    cleaned = _strip_fenced_json(response_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse JSON: {e}",
            "rawResponse": response_text[:500],
            "readinessPercent": 0,
            "readinessLevel": "inadequate",
            "issues": [],
            "recommendations": [],
        }

def build_volume_editor_provider_prompt(
    preflight_payload: dict[str, Any],
    review_packet_text: str,
    *,
    generated_at: str,
) -> dict[str, Any]:
    volume_id = str(preflight_payload.get("volumeId", "")).strip()
    volume_title = str(preflight_payload.get("volumeTitle", volume_id)).strip() or volume_id
    system_prompt = (
        "You are an independent Story Canvas volume editor. "
        "You must review only the supplied review packet and rubric. "
        "Do not inherit the author's self-defense, prior chat context, or host coding-agent defaults. "
        "Return only one strict JSON object. Do not wrap it in Markdown."
    )
    user_payload = {
        "task": "Produce a clean-room independent editor fragment for Story Canvas volume self-review.",
        "volume": {
            "volumeId": volume_id,
            "volumeTitle": volume_title,
            "generatedAt": generated_at,
        },
        "rubric": {
            "scoreRange": "0-5 integer",
            "dimensions": [
                {"dimensionId": dimension_id, "label": label}
                for dimension_id, label in VOLUME_SELF_REVIEW_DIMENSIONS
            ],
            "overallVerdict": {
                "pass": "The volume can proceed to human review.",
                "revise": "The volume needs revision before human review.",
                "block": "The volume is structurally not ready.",
            },
        },
        "preflightSummary": _compact_preflight(preflight_payload),
        "outputContract": EDITOR_OUTPUT_SCHEMA,
        "reviewPacketMarkdown": review_packet_text,
    }
    user_prompt = json.dumps(user_payload, ensure_ascii=False, indent=2)
    return {
        "systemPrompt": system_prompt,
        "userPrompt": user_prompt,
        "expectedOutput": EDITOR_OUTPUT_SCHEMA,
        "volumeId": volume_id,
        "volumeTitle": volume_title,
        "reviewPacketChars": len(review_packet_text),
    }


def parse_text_provider_json_object(text: str) -> dict[str, Any]:
    raw_text = text.strip()
    if raw_text.startswith("```"):
        raw_text = _strip_fenced_json(raw_text)
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"文本 provider 未返回合法 JSON 对象: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("文本 provider 输出必须是 JSON 对象。")
    return payload


def normalize_editor_provider_fragment(
    raw_payload: dict[str, Any],
    *,
    provider_name: str,
    model: str,
    generated_at: str,
) -> dict[str, Any]:
    if "editorFragment" in raw_payload and isinstance(raw_payload["editorFragment"], dict):
        raw_payload = raw_payload["editorFragment"]

    editor_assessment = raw_payload.get("editorAssessment")
    if editor_assessment is None and "overallVerdict" in raw_payload:
        editor_assessment = {
            "overallVerdict": raw_payload.get("overallVerdict"),
            "summaryComment": raw_payload.get("summaryComment", ""),
            "topProblems": raw_payload.get("topProblems", []),
            "improvementPoints": raw_payload.get("improvementPoints", []),
            "scores": raw_payload.get("scores", []),
        }
    if not isinstance(editor_assessment, dict):
        raise ValueError("文本 provider 输出缺少 editorAssessment 对象。")

    editor_pass = raw_payload.get("editorPass")
    if not isinstance(editor_pass, dict):
        editor_pass = {}
    notes = str(editor_pass.get("notes", "")).strip()
    provider_note = f"由文本 provider {provider_name} / {model} 在 {generated_at} 生成。"
    if notes:
        notes = f"{notes} {provider_note}"
    else:
        notes = provider_note

    return {
        "editorPass": {
            "completed": True,
            "reviewerRole": "editor",
            "mode": editor_pass.get("mode") or "independent_agent",
            "contextIsolation": editor_pass.get("contextIsolation") or "no_context_proxy",
            "notes": notes,
        },
        "editorAssessment": editor_assessment,
    }


def _compact_preflight(preflight_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "volumeId": preflight_payload.get("volumeId", ""),
        "volumeTitle": preflight_payload.get("volumeTitle", ""),
        "chapterCount": preflight_payload.get("chapterCount", 0),
        "blockingRules": preflight_payload.get("blockingRules", []),
        "projectAdvisories": preflight_payload.get("projectAdvisories", []),
        "volumeStructureCheck": preflight_payload.get("volumeStructureCheck", {}),
        "volumeClosureContract": preflight_payload.get("volumeClosureContract", {}),
        "reviewEvidence": preflight_payload.get("reviewEvidence", {}),
    }


def _strip_fenced_json(text: str) -> str:
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text
