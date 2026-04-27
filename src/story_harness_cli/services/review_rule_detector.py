from __future__ import annotations

import re
from typing import Any, Dict, List


META_LEAKAGE_PATTERNS = (
    r"第[0-9零一二两三四五六七八九十百千]+章",
    r"第[0-9零一二两三四五六七八九十百千]+卷",
    r"(?:上一章|下一章|本章|这一章|该章)",
    r"(?:上一卷|下一卷|本卷|这一卷)",
)
POV_BLIND_SPOT_LOCATORS = (
    "身后",
    "背后",
    "后方",
    "右后方",
    "左后方",
    "背后右侧",
    "背后左侧",
)
POV_ALLOWANCE_CUES = (
    "回头",
    "转身",
    "扭头",
    "侧头",
    "偏头",
    "余光",
    "余角",
    "镜中",
    "镜里",
    "倒影",
    "反光",
    "映出",
    "神识",
    "灵识",
    "感知",
    "察觉",
    "觉察",
    "听见",
    "听到",
)
POV_VISUAL_DETAIL_CUES = (
    "落下",
    "落在",
    "站着",
    "有人",
    "出现",
    "掠过",
    "闪过",
    "边沿",
    "木梁",
    "排灰沟",
    "人影",
    "身影",
    "灰",
    "目光",
    "神情",
    "表情",
)
QUOTE_PAIRS = (
    ("“", "”"),
    ("「", "」"),
    ("『", "』"),
    ("‘", "’"),
)


def detect_review_rule_signals(
    text: str,
    *,
    word_count: int,
    review_rule_config: Dict[str, Any] | None = None,
    review_rule_scope: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    review_rule_config = review_rule_config or {}
    review_rule_scope = review_rule_scope or {}

    pattern_results: List[Dict[str, Any]] = []
    signals: Dict[str, Any] = {}

    meta_leakage = _detect_meta_leakage(
        text,
        word_count=word_count,
        review_rule_config=review_rule_config,
        review_rule_scope=review_rule_scope,
    )
    if meta_leakage.get("enabled"):
        signals["metaLeakage"] = meta_leakage
        pattern_results.append(_meta_leakage_result(meta_leakage))

    pov_overreach = _detect_pov_overreach(
        text,
        word_count=word_count,
        review_rule_config=review_rule_config,
        review_rule_scope=review_rule_scope,
    )
    if pov_overreach.get("enabled"):
        signals["povOverreach"] = pov_overreach
        pattern_results.append(_pov_overreach_result(pov_overreach))

    return {
        "patternResults": pattern_results,
        "signals": signals,
    }


def _detect_meta_leakage(
    text: str,
    *,
    word_count: int,
    review_rule_config: Dict[str, Any],
    review_rule_scope: Dict[str, str],
) -> Dict[str, Any]:
    if not _review_rule_enabled(review_rule_config, "metaLeakage"):
        return {}

    raw_evidence: List[str] = []
    effective_evidence: List[str] = []
    exempted_evidence: List[Dict[str, str]] = []
    raw_count = 0
    effective_count = 0
    exempted_count = 0

    for pattern in META_LEAKAGE_PATTERNS:
        for match in re.finditer(pattern, text):
            if _match_in_markdown_heading(text, match.start()):
                continue
            raw_count += 1
            snippet = _truncate_match(match.group(0))
            if snippet not in raw_evidence:
                raw_evidence.append(snippet)
            context_snippet = _match_context(text, match.start(), match.end())
            exemption_reason = _resolve_review_rule_exemption(
                text,
                rule_id="metaLeakage",
                match_start=match.start(),
                match_end=match.end(),
                context_snippet=context_snippet,
                review_rule_config=review_rule_config,
                review_rule_scope=review_rule_scope,
            )
            if exemption_reason:
                exempted_count += 1
                exempted_evidence.append(
                    {
                        "snippet": snippet,
                        "reason": exemption_reason,
                    }
                )
                continue
            effective_count += 1
            if snippet not in effective_evidence:
                effective_evidence.append(snippet)

    per_thousand = round((effective_count / max(word_count, 1)) * 1000, 1) if word_count else 0.0
    if effective_count == 0:
        severity = "none"
    elif effective_count == 1:
        severity = "medium"
    else:
        severity = "high"

    return {
        "enabled": True,
        "count": raw_count,
        "effectiveCount": effective_count,
        "perThousand": per_thousand,
        "threshold": 1,
        "detected": effective_count > 0,
        "rawDetected": raw_count > 0,
        "severity": severity,
        "rawEvidence": raw_evidence[:5],
        "evidence": effective_evidence[:5],
        "exempted": bool(exempted_evidence),
        "exemptedCount": exempted_count,
        "exemptedEvidence": exempted_evidence[:5],
        "exemptionReason": exempted_evidence[0]["reason"] if exempted_evidence else "",
        "suggestion": (
            "正文不应直接引用“第xx章 / 上一章 / 这一卷”等作品元信息；除非是书中书、角色讨论作品结构等已显式豁免场景。"
            if effective_count > 0
            else ""
        ),
    }


def _detect_pov_overreach(
    text: str,
    *,
    word_count: int,
    review_rule_config: Dict[str, Any],
    review_rule_scope: Dict[str, str],
) -> Dict[str, Any]:
    if not _review_rule_enabled(review_rule_config, "povOverreach"):
        return {}

    raw_evidence: List[str] = []
    effective_evidence: List[str] = []
    exempted_evidence: List[Dict[str, str]] = []
    raw_count = 0
    effective_count = 0
    exempted_count = 0

    for sentence in _split_sentences(text):
        sentence_text = sentence["text"]
        if not _sentence_has_any(sentence_text, POV_BLIND_SPOT_LOCATORS):
            continue
        if _sentence_has_any(sentence_text, POV_ALLOWANCE_CUES):
            continue
        if not _sentence_has_any(sentence_text, POV_VISUAL_DETAIL_CUES):
            continue

        raw_count += 1
        snippet = _truncate_match(sentence_text.strip())
        if snippet not in raw_evidence:
            raw_evidence.append(snippet)
        exemption_reason = _resolve_review_rule_exemption(
            text,
            rule_id="povOverreach",
            match_start=sentence["start"],
            match_end=sentence["end"],
            context_snippet=sentence_text,
            review_rule_config=review_rule_config,
            review_rule_scope=review_rule_scope,
        )
        if exemption_reason:
            exempted_count += 1
            exempted_evidence.append(
                {
                    "snippet": snippet,
                    "reason": exemption_reason,
                }
            )
            continue
        effective_count += 1
        if snippet not in effective_evidence:
            effective_evidence.append(snippet)

    per_thousand = round((effective_count / max(word_count, 1)) * 1000, 1) if word_count else 0.0
    if effective_count == 0:
        severity = "none"
    elif effective_count == 1:
        severity = "medium"
    else:
        severity = "high"

    return {
        "enabled": True,
        "count": raw_count,
        "effectiveCount": effective_count,
        "perThousand": per_thousand,
        "threshold": 1,
        "detected": effective_count > 0,
        "rawDetected": raw_count > 0,
        "severity": severity,
        "rawEvidence": raw_evidence[:5],
        "evidence": effective_evidence[:5],
        "exempted": bool(exempted_evidence),
        "exemptedCount": exempted_count,
        "exemptedEvidence": exempted_evidence[:5],
        "exemptionReason": exempted_evidence[0]["reason"] if exempted_evidence else "",
        "suggestion": (
            "有限视角下不要直接断言角色看不到的身后/背后细节；若确实可知，需要补回头、余光、镜面、神识或其他感知来源。"
            if effective_count > 0
            else ""
        ),
    }


def _meta_leakage_result(meta_leakage: Dict[str, Any]) -> Dict[str, Any]:
    suggestion = meta_leakage.get("suggestion", "") if meta_leakage.get("detected") else ""
    return {
        "id": "metaLeakage",
        "label": "正文元信息泄漏",
        "detected": meta_leakage.get("detected", False),
        "rawDetected": meta_leakage.get("rawDetected", False),
        "count": meta_leakage.get("count", 0),
        "effectiveCount": meta_leakage.get("effectiveCount", 0),
        "perThousand": meta_leakage.get("perThousand", 0),
        "threshold": meta_leakage.get("threshold", 1),
        "severity": meta_leakage.get("severity", "none"),
        "evidence": meta_leakage.get("evidence", []),
        "rawEvidence": meta_leakage.get("rawEvidence", []),
        "exempted": meta_leakage.get("exempted", False),
        "exemptedCount": meta_leakage.get("exemptedCount", 0),
        "exemptedEvidence": meta_leakage.get("exemptedEvidence", []),
        "exemptionReason": meta_leakage.get("exemptionReason", ""),
        "suggestion": suggestion,
    }


def _pov_overreach_result(pov_overreach: Dict[str, Any]) -> Dict[str, Any]:
    suggestion = pov_overreach.get("suggestion", "") if pov_overreach.get("detected") else ""
    return {
        "id": "povOverreach",
        "label": "POV 越界",
        "detected": pov_overreach.get("detected", False),
        "rawDetected": pov_overreach.get("rawDetected", False),
        "count": pov_overreach.get("count", 0),
        "effectiveCount": pov_overreach.get("effectiveCount", 0),
        "perThousand": pov_overreach.get("perThousand", 0),
        "threshold": pov_overreach.get("threshold", 1),
        "severity": pov_overreach.get("severity", "none"),
        "evidence": pov_overreach.get("evidence", []),
        "rawEvidence": pov_overreach.get("rawEvidence", []),
        "exempted": pov_overreach.get("exempted", False),
        "exemptedCount": pov_overreach.get("exemptedCount", 0),
        "exemptedEvidence": pov_overreach.get("exemptedEvidence", []),
        "exemptionReason": pov_overreach.get("exemptionReason", ""),
        "suggestion": suggestion,
    }


def _review_rule_enabled(review_rule_config: Dict[str, Any], rule_id: str) -> bool:
    enabled_rules = review_rule_config.get("enabledRules", []) if isinstance(review_rule_config, dict) else []
    return rule_id in enabled_rules


def _resolve_review_rule_exemption(
    text: str,
    *,
    rule_id: str,
    match_start: int,
    match_end: int,
    context_snippet: str,
    review_rule_config: Dict[str, Any],
    review_rule_scope: Dict[str, str],
) -> str:
    exemptions = review_rule_config.get("exemptions", []) if isinstance(review_rule_config, dict) else []
    for item in exemptions:
        if not isinstance(item, dict) or item.get("ruleId") != rule_id:
            continue
        if not _review_rule_scope_matches(item.get("scope", {}), review_rule_scope):
            continue
        allow_when = item.get("allowWhen", {})
        if allow_when.get("quotedOnly") and not _match_inside_quotes(text, match_start, match_end):
            continue
        match_patterns = allow_when.get("matchPatterns", [])
        if match_patterns and not _match_any_pattern(match_patterns, context_snippet):
            continue
        return str(item.get("reason", "")).strip() or "review-rules exemption"
    return ""


def _review_rule_scope_matches(scope: Dict[str, Any], review_rule_scope: Dict[str, str]) -> bool:
    scope = scope if isinstance(scope, dict) else {}
    chapter_ids = scope.get("chapterIds", [])
    volume_ids = scope.get("volumeIds", [])
    scene_plan_ids = scope.get("scenePlanIds", [])
    if chapter_ids and review_rule_scope.get("chapterId", "") not in chapter_ids:
        return False
    if volume_ids and review_rule_scope.get("volumeId", "") not in volume_ids:
        return False
    if scene_plan_ids and review_rule_scope.get("scenePlanId", "") not in scene_plan_ids:
        return False
    return True


def _match_inside_quotes(text: str, start: int, end: int) -> bool:
    for opening, closing in QUOTE_PAIRS:
        left = text.rfind(opening, 0, start)
        if left < 0:
            continue
        previous_close = text.rfind(closing, 0, start)
        if previous_close > left:
            continue
        right = text.find(closing, end)
        if right >= 0:
            return True
    return False


def _match_any_pattern(patterns: List[str], context_snippet: str) -> bool:
    for pattern in patterns:
        try:
            if re.search(pattern, context_snippet):
                return True
        except re.error:
            continue
    return False


def _sentence_has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _split_sentences(text: str) -> List[Dict[str, Any]]:
    sentences: List[Dict[str, Any]] = []
    start = 0
    for match in re.finditer(r"[。！？!?]\s*|\n+", text):
        end = match.end()
        snippet = text[start:end].strip()
        if snippet:
            sentences.append({"text": snippet, "start": start, "end": end})
        start = end
    tail = text[start:].strip()
    if tail:
        sentences.append({"text": tail, "start": start, "end": len(text)})
    return sentences


def _match_in_markdown_heading(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end].lstrip()
    return line.startswith("#")


def _match_context(text: str, start: int, end: int, radius: int = 18) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return text[left:right]


def _truncate_match(snippet: str, limit: int = 30) -> str:
    if len(snippet) <= limit:
        return snippet
    return snippet[:limit] + "..."
