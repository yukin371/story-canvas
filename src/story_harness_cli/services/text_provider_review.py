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
