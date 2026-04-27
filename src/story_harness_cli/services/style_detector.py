"""AI style pattern detection for Chinese prose.

Detects 7 categories of AI-typical writing patterns and produces
actionable suggestions for reducing them. Pure functions, no side effects.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Callable, Dict, List, Tuple

from story_harness_cli.utils import now_iso, stable_hash

from story_harness_cli.utils.text import count_words, paragraphs_from_text, strip_entity_tags
from .review_rule_detector import detect_review_rule_signals
from .rule_semantics import build_rule_judgement, chapter_scope_ref


SimilarityScorer = Callable[[str, str], float]
CJK_RANGE = f"{chr(0x4E00)}-{chr(0x9FFF)}"
ABSTRACT_FRAME_TAILS = {
    "记忆", "经验", "情报", "判断", "认知", "印象", "念头", "念想",
    "直觉", "意识", "本能", "认定", "结论", "推断", "推演", "理解",
    "认知", "知识", "筹算", "计划", "谋划",
}
CONCRETE_FRAME_PREFIXES = {
    "黑色的", "白色的", "漆黑的", "明亮的", "昏暗的", "冰冷的", "滚烫的",
    "锋利的", "柔软的", "巨大的", "沉重的", "苍白的", "熟悉的", "陌生的",
    "手中的", "眼前的", "身后的", "脚下的", "耳边的", "掌中的", "心里的",
}
PLAN_BLOCK_LABELS = (
    "目标",
    "风险",
    "约束",
    "时间窗口",
    "优先级",
)


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

AI_STYLE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "simile_density": {
        "id": "simileDensity",
        "label": "比喻密度",
        "description": "过多使用'像……一样'式比喻",
        "patterns": [
            r"像[^。，？！\n]{2,20}一样",
            r"宛如[^。，？！\n]{2,15}",
            r"仿佛[^。，？！\n]{2,15}",
            r"如同[^。，？！\n]{2,15}一般",
        ],
        "threshold_per_1000": 3.0,
    },
    "hedge_adverbs": {
        "id": "hedgeAdverbs",
        "label": "模糊副词",
        "description": "过度使用'微微'、'缓缓'、'不禁'等AI倾向副词",
        "patterns": [
            r"微微", r"缓缓", r"不禁", r"默默", r"淡淡",
            r"轻轻", r"静静", r"悄悄", r"渐渐", r"逐渐", r"慢慢",
        ],
        "threshold_per_1000": 5.0,
    },
    "telling_emotion": {
        "id": "tellingEmotion",
        "label": "叙述性情感",
        "description": "直接告诉读者情绪而非通过行动展示",
        "patterns": [
            r"感到[^。，？！\n]{1,10}(?:悲伤|愤怒|恐惧|震惊|欣慰|失落|绝望|不安|焦虑|一阵)",
            r"心中(?:涌起|升起|泛起|充满|满是)[^。，？！\n]{2,15}",
            r"(?:一种|一股|一阵)[^。，？！\n]{1,8}(?:涌上|涌起|升起|袭来|弥漫)",
            r"内心(?:深处的|深处的)?[^。，？！\n]{0,5}(?:震动|波澜|悸动|颤抖)",
        ],
        "threshold_per_1000": 2.0,
    },
    "formulaic_transition": {
        "id": "formulaicTransition",
        "label": "程式化过渡",
        "description": "使用AI倾向的过渡短语",
        "patterns": [
            r"然而[,，]",
            r"与此同时",
            r"不仅如此",
            r"就在这时",
            r"就在此时",
            r"不知不觉中",
            r"时间(?:一分一秒地)?流逝",
            r"此刻",
        ],
        "threshold_per_1000": 2.0,
    },
    "contrast_flip_pattern": {
        "id": "contrastFlipPattern",
        "label": "翻转句式",
        "description": "高频使用'不是……是……'类解释式翻转",
        "patterns": [
            r"不是[^。！？\n]{1,18}[，,；;]\s*是[^。！？\n]{1,18}",
            r"不是[^。！？\n]{1,18}。\s*是[^。！？\n]{1,18}",
            r"不是[^。！？\n]{1,18}[，,；;]\s*不是[^。！？\n]{1,18}[，,；;]\s*是[^。！？\n]{1,18}",
            r"不是[^。！？\n]{1,18}。\s*不是[^。！？\n]{1,18}。\s*是[^。！？\n]{1,18}",
        ],
        "threshold_per_1000": 1.2,
    },
    "analogical_pivot_pattern": {
        "id": "analogicalPivotPattern",
        "label": "类比翻转句",
        "description": "高频使用'不像……更像……'或'不是……更像……'类抽象转折",
        "patterns": [
            r"不像[^。！？\n]{1,18}[，,；;]\s*更像[^。！？\n]{1,18}",
            r"不像[^。！？\n]{1,18}。\s*更像[^。！？\n]{1,18}",
            r"不是[^。！？\n]{1,18}[，,；;]\s*更像[^。！？\n]{1,18}",
            r"不是[^。！？\n]{1,18}。\s*更像[^。！？\n]{1,18}",
            r"不像[^。！？\n]{1,18}[，,；;]\s*倒像[^。！？\n]{1,18}",
            r"不是[^。！？\n]{1,18}[，,；;]\s*倒像[^。！？\n]{1,18}",
        ],
        "threshold_per_1000": 0.8,
    },
    "template_catchphrase_pattern": {
        "id": "templateCatchphrasePattern",
        "label": "模板化口癖",
        "description": "高频出现故作深沉或追问式模板短句",
        "patterns": [
            r"真正[^。！？\n]{1,20}(?:从来都是|才是)",
            r"还有什么[？?]",
            r"从来都不是[^。！？\n]{1,18}",
        ],
        "threshold_per_1000": 0.8,
    },
}

SENSORY_CATEGORIES: Dict[str, str] = {
    "visual": r"(?:看|望|瞧|瞥|颜色|光(?:芒|线|影)|亮|暗|色彩|闪烁|照耀)",
    "auditory": r"(?:听|声|响|音|鸣|呼|叫|咆哮|呢喃|低语|嘶吼|回响)",
    "tactile": r"(?:摸|触|碰|握|抓|冷|热|冰|烫|柔软|坚硬|粗糙|刺痛|颤抖)",
    "olfactory": r"(?:闻|嗅|香|臭|气味|味道|芬芳|腥|腐)",
    "gustatory": r"(?:尝|舔|咸|甜|苦|酸|辣|鲜|涩)",
}


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_ai_style(
    paragraphs: List[str],
    clean_text: str,
    *,
    opener_similarity_scorer: SimilarityScorer | None = None,
    repetition_source: str = "builtin",
    profile_config: Dict[str, Any] | None = None,
    review_rule_config: Dict[str, Any] | None = None,
    review_rule_scope: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Run all AI style detection patterns against chapter text.

    Returns a dict with patternResults, sensoryDistribution,
    paragraphUniformity, sentenceRepetition, and scoring info.
    """
    word_count = _count_cjk(clean_text)
    review_rule_config = review_rule_config or {}
    review_rule_scope = review_rule_scope or {}
    results: List[Dict[str, Any]] = []
    total_deduction = 0

    review_rule_signals = detect_review_rule_signals(
        clean_text,
        word_count=word_count,
        review_rule_config=review_rule_config,
        review_rule_scope=review_rule_scope,
    )
    results.extend(review_rule_signals.get("patternResults", []))
    meta_leakage = review_rule_signals.get("signals", {}).get("metaLeakage", {})
    for item in review_rule_signals.get("patternResults", []):
        total_deduction += _deduction_for_severity(item.get("severity", "none"))

    if word_count < 50:
        total_deduction = min(total_deduction, 6)
        return _build_short_text_result(
            results,
            total_deduction,
            meta_leakage=meta_leakage,
            review_rule_config=review_rule_config,
        )

    for key, spec in AI_STYLE_PATTERNS.items():
        threshold, patterns = _resolve_pattern_profile(spec, profile_config or {})
        count, evidence = _count_pattern_matches(clean_text, patterns)
        per_thousand = (count / word_count) * 1000
        severity = _severity(per_thousand, threshold)
        detected = severity != "none"

        deduction = 0
        if severity == "low":
            deduction = 1
        elif severity == "medium":
            deduction = 2
        elif severity == "high":
            deduction = 3

        total_deduction += deduction

        results.append({
            "id": spec["id"],
            "label": spec["label"],
            "detected": detected,
            "count": count,
            "perThousand": round(per_thousand, 1),
            "threshold": threshold,
            "severity": severity,
            "evidence": evidence[:5],
            "suggestion": _pattern_suggestion(spec["id"], severity, per_thousand, threshold),
        })

    # Sensory variety
    sensory = _detect_sensory_variety(clean_text)
    if len(sensory["missingSenses"]) >= 2:
        total_deduction += 1
    results.append(_sensory_result(sensory))

    # Paragraph uniformity
    uniformity = _detect_paragraph_uniformity(paragraphs)
    if uniformity["isUniform"]:
        total_deduction += 1
    results.append(_uniformity_result(uniformity))

    # Paragraph readability
    readability = _detect_paragraph_readability(paragraphs)
    if readability["detected"]:
        total_deduction += _deduction_for_severity(readability["severity"])
    results.append(_paragraph_readability_result(readability))

    # Sentence repetition
    repetition = _detect_sentence_repetition(
        paragraphs,
        similarity_scorer=opener_similarity_scorer,
        source_label=repetition_source,
    )
    if repetition["hasRepetition"]:
        total_deduction += 1
    results.append(_repetition_result(repetition))

    # Special term repetition
    special_terms = _detect_special_term_repetition(clean_text, profile_config or {})
    if special_terms["detected"]:
        total_deduction += 1 if special_terms["severity"] == "low" else 2
    results.append(_special_term_result(special_terms))

    # Narrative frame repetition
    narrative_frames = _detect_narrative_frame_repetition(clean_text, profile_config or {})
    if narrative_frames["detected"]:
        total_deduction += 1 if narrative_frames["severity"] == "low" else 2
    results.append(_narrative_frame_result(narrative_frames))

    # Genre/register drift
    register_drift = _detect_register_drift(clean_text, profile_config or {})
    if register_drift["detected"]:
        total_deduction += 1 if register_drift["severity"] == "low" else 2
    results.append(_register_drift_result(register_drift))

    # Structured planning/checklist prose
    structured_plan_block = _detect_structured_plan_block(paragraphs, profile_config or {})
    if structured_plan_block["detected"]:
        total_deduction += 3 if structured_plan_block["severity"] == "high" else 2
    results.append(_structured_plan_block_result(structured_plan_block))

    # Cap total deduction at 6
    total_deduction = min(total_deduction, 6)

    suggestions = []
    for r in results:
        if r.get("detected") and r.get("suggestion"):
            suggestions.append(r["suggestion"])

    return {
        "overallScore": max(0, 20 - total_deduction),
        "totalDeduction": total_deduction,
        "patternResults": results,
        "sensoryDistribution": sensory,
        "paragraphUniformity": uniformity,
        "paragraphReadability": readability,
        "sentenceRepetition": repetition,
        "specialTermRepetition": special_terms,
        "narrativeFrameRepetition": narrative_frames,
        "registerDrift": register_drift,
        "structuredPlanBlock": structured_plan_block,
        "metaLeakage": meta_leakage,
        "sources": {
            "sentenceRepetition": repetition["source"],
        },
        "judgements": _build_style_judgements(results, profile_config or {}, review_rule_config),
        "summary": _generate_summary(results, total_deduction),
        "suggestions": suggestions[:5],
    }


def analyze_style_text(
    chapter_text: str,
    *,
    opener_similarity_scorer: SimilarityScorer | None = None,
    repetition_source: str = "builtin",
    profile_name: str = "default",
    profile_config: Dict[str, Any] | None = None,
    review_rule_profile_name: str = "default",
    review_rule_config: Dict[str, Any] | None = None,
    review_rule_scope: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Analyze style for one chapter-like text block."""
    clean_text = strip_entity_tags(chapter_text)
    paragraphs = paragraphs_from_text(clean_text)
    style_analysis = detect_ai_style(
        paragraphs,
        clean_text,
        opener_similarity_scorer=opener_similarity_scorer,
        repetition_source=repetition_source,
        profile_config=profile_config,
        review_rule_config=review_rule_config,
        review_rule_scope=review_rule_scope,
    )
    constraints = generate_style_constraints(style_analysis)
    return {
        "profile": profile_name,
        "reviewRuleProfile": review_rule_profile_name,
        "reviewRuleEnabledRules": list((review_rule_config or {}).get("enabledRules", [])),
        "styleAnalysis": style_analysis,
        "judgements": _attach_style_scope(style_analysis.get("judgements", []), chapter_id=""),
        "constraints": constraints,
        "textMetrics": {
            "wordCount": count_words(clean_text),
            "paragraphCount": len(paragraphs),
            "averageParagraphLength": _average_length(paragraphs),
        },
    }


def build_style_report(
    chapter_reports: List[Dict[str, Any]],
    *,
    volume_id: str = "",
    profile_name: str = "default",
) -> Dict[str, Any]:
    """Aggregate multiple chapter style reports into one report payload."""
    if not chapter_reports:
        return {
            "profile": profile_name,
            "volumeId": volume_id,
            "chapterCount": 0,
            "averageOverallScore": 0.0,
            "averageDeduction": 0.0,
            "flaggedChapters": [],
            "patternCounts": [],
        }

    total_score = 0
    total_deduction = 0
    pattern_counts: Dict[str, int] = {}
    flagged: List[Dict[str, Any]] = []
    for item in chapter_reports:
        analysis = item["styleAnalysis"]
        total_score += analysis["overallScore"]
        total_deduction += analysis["totalDeduction"]
        detected_labels = []
        for pattern in analysis.get("patternResults", []):
            if not pattern.get("detected"):
                continue
            label = pattern.get("label", pattern.get("id", "unknown"))
            pattern_counts[label] = pattern_counts.get(label, 0) + 1
            detected_labels.append(label)
        if analysis["totalDeduction"] > 0:
            flagged.append(
                {
                    "chapterId": item["chapterId"],
                    "overallScore": analysis["overallScore"],
                    "totalDeduction": analysis["totalDeduction"],
                    "detectedPatterns": detected_labels,
                }
            )

    pattern_summary = [
        {"label": label, "chapterHits": count}
        for label, count in sorted(pattern_counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]

    return {
        "profile": profile_name,
        "volumeId": volume_id,
        "chapterCount": len(chapter_reports),
        "averageOverallScore": round(total_score / len(chapter_reports), 1),
        "averageDeduction": round(total_deduction / len(chapter_reports), 1),
        "flaggedChapters": sorted(flagged, key=lambda item: (-item["totalDeduction"], item["chapterId"])),
        "patternCounts": pattern_summary,
    }


def _build_style_judgements(
    pattern_results: List[Dict[str, Any]],
    profile_config: Dict[str, Any],
    review_rule_config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    judgements: List[Dict[str, Any]] = []
    for item in pattern_results:
        if not item.get("detected"):
            continue
        severity = item.get("severity", "none")
        if severity == "none":
            continue
        rule_id = str(item.get("id", "style-pattern"))
        source = _style_rule_source(rule_id, profile_config, review_rule_config)
        judgements.append(
            build_rule_judgement(
                rule_id=rule_id,
                source=source,
                severity=severity,
                message=_style_rule_message(item),
                suggestion=str(item.get("suggestion", "")),
                evidence=list(item.get("evidence", [])),
            )
        )
    return judgements


def _style_rule_source(
    rule_id: str,
    profile_config: Dict[str, Any],
    review_rule_config: Dict[str, Any],
) -> str:
    enabled_rules = review_rule_config.get("enabledRules", []) if isinstance(review_rule_config, dict) else []
    if rule_id in {"metaLeakage", "povOverreach"} and rule_id in enabled_rules:
        return "review-rule-profile"
    if rule_id == "registerDrift":
        register_policy = profile_config.get("registerPolicy", {}) if isinstance(profile_config, dict) else {}
        if register_policy.get("disallowedCategories"):
            return "genre-pack"
    return "core"


def _style_rule_message(item: Dict[str, Any]) -> str:
    label = str(item.get("label", item.get("id", "风格信号")))
    evidence = list(item.get("evidence", []))
    evidence_suffix = f"，例如 {evidence[0]}" if evidence else ""
    return f"检测到{label}问题{evidence_suffix}。"


def _attach_style_scope(judgements: List[Dict[str, Any]], chapter_id: str) -> List[Dict[str, Any]]:
    if not chapter_id:
        return [dict(item) for item in judgements]
    scoped: List[Dict[str, Any]] = []
    for item in judgements:
        enriched = dict(item)
        scope_ref = dict(item.get("scopeRef", {}))
        if "chapterId" not in scope_ref:
            scope_ref.update(chapter_scope_ref(chapter_id))
        enriched["scopeRef"] = scope_ref
        scoped.append(enriched)
    return scoped


# ---------------------------------------------------------------------------
# Sub-detectors
# ---------------------------------------------------------------------------

def _count_pattern_matches(text: str, patterns: List[str]) -> Tuple[int, List[str]]:
    """Count regex pattern matches and collect evidence."""
    total = 0
    evidence: List[str] = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            total += 1
            snippet = m.group(0)
            if len(snippet) > 30:
                snippet = snippet[:30] + "..."
            if snippet not in evidence:
                evidence.append(snippet)
    return total, evidence


def _resolve_pattern_profile(spec: Dict[str, Any], profile_config: Dict[str, Any]) -> Tuple[float, List[str]]:
    threshold_map = profile_config.get("patternThresholds", {}) if isinstance(profile_config, dict) else {}
    extra_patterns = profile_config.get("extraPatterns", {}) if isinstance(profile_config, dict) else {}
    threshold = float(threshold_map.get(spec["id"], spec["threshold_per_1000"]))
    patterns = list(spec["patterns"])
    for pattern in extra_patterns.get(spec["id"], []):
        if pattern not in patterns:
            patterns.append(pattern)
    return threshold, patterns


def _detect_sensory_variety(text: str) -> Dict[str, Any]:
    """Categorize sensory descriptions and check for dominance."""
    counts: Dict[str, int] = {}
    for category, pattern in SENSORY_CATEGORIES.items():
        counts[category] = len(re.findall(pattern, text))

    total = sum(counts.values()) or 1
    dominant = max(counts, key=lambda k: counts[k])
    missing = [k for k in counts if counts[k] == 0]

    return {
        "visual": counts.get("visual", 0),
        "auditory": counts.get("auditory", 0),
        "tactile": counts.get("tactile", 0),
        "olfactory": counts.get("olfactory", 0),
        "gustatory": counts.get("gustatory", 0),
        "dominantSense": dominant,
        "missingSenses": missing,
    }


def _detect_paragraph_uniformity(paragraphs: List[str]) -> Dict[str, Any]:
    """Check if paragraph lengths are too uniform."""
    if len(paragraphs) < 3:
        return {"lengthStdDev": 0, "avgLength": 0, "isUniform": False, "score": 3}

    lengths = [len(p) for p in paragraphs]
    avg = sum(lengths) / len(lengths)
    if avg == 0:
        return {"lengthStdDev": 0, "avgLength": 0, "isUniform": False, "score": 3}

    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    cv = std_dev / avg  # coefficient of variation

    return {
        "lengthStdDev": round(std_dev, 1),
        "avgLength": round(avg, 1),
        "isUniform": cv < 0.3,
        "score": 1 if cv < 0.2 else (2 if cv < 0.3 else 3),
    }


def _detect_paragraph_readability(paragraphs: List[str]) -> Dict[str, Any]:
    long_threshold = 90
    very_long_threshold = 150
    overlong: List[Dict[str, Any]] = []
    max_length = 0
    for index, paragraph in enumerate(paragraphs, start=1):
        length = _count_cjk(paragraph)
        max_length = max(max_length, length)
        if length < long_threshold:
            continue
        snippet = paragraph.strip().replace("\n", " ")
        if len(snippet) > 32:
            snippet = snippet[:32] + "..."
        overlong.append(
            {
                "paragraphIndex": index,
                "length": length,
                "snippet": snippet,
            }
        )

    very_long_count = sum(1 for item in overlong if item["length"] >= very_long_threshold)
    if very_long_count > 0:
        severity = "high"
    elif len(overlong) >= 2:
        severity = "medium"
    elif len(overlong) == 1:
        severity = "low"
    else:
        severity = "none"

    return {
        "detected": bool(overlong),
        "severity": severity,
        "count": len(overlong),
        "threshold": long_threshold,
        "veryLongThreshold": very_long_threshold,
        "maxLength": max_length,
        "evidence": [f"第{item['paragraphIndex']}段约{item['length']}字：{item['snippet']}" for item in overlong[:3]],
        "overlongParagraphs": overlong[:5],
    }


def _detect_sentence_repetition(
    paragraphs: List[str],
    *,
    similarity_scorer: SimilarityScorer | None = None,
    source_label: str = "builtin",
    threshold: float = 90.0,
) -> Dict[str, Any]:
    """Detect consecutive paragraphs with similar opening structure."""
    if len(paragraphs) < 3:
        return {
            "repeatedStructures": [],
            "hasRepetition": False,
            "score": 3,
            "source": source_label if similarity_scorer is not None else "builtin",
        }

    # Extract sentence openers: first 3 chars after sentence-starting position.
    openers: List[str] = []
    for p in paragraphs:
        text = p.strip()
        if len(text) >= 3:
            openers.append(text[:3])
        else:
            openers.append(text)

    if similarity_scorer is None:
        similarity_scorer = _exact_similarity
        source = "builtin"
    else:
        source = source_label

    # Check for 3+ consecutive similar openers.
    repeated: List[Dict[str, Any]] = []
    streak_start = 0
    for i in range(1, len(openers)):
        if similarity_scorer(openers[i], openers[streak_start]) >= threshold:
            continue
        streak_len = i - streak_start
        if streak_len >= 3:
            repeated.append({
                "pattern": openers[streak_start],
                "count": streak_len,
                "paragraphs": list(range(streak_start, i)),
            })
        streak_start = i

    # Final streak
    final_len = len(openers) - streak_start
    if final_len >= 3:
        repeated.append({
            "pattern": openers[streak_start],
            "count": final_len,
            "paragraphs": list(range(streak_start, len(openers))),
        })

    return {
        "repeatedStructures": repeated,
        "hasRepetition": len(repeated) > 0,
        "score": 1 if len(repeated) >= 2 else (2 if len(repeated) == 1 else 3),
        "source": source,
    }


def _detect_special_term_repetition(text: str, profile_config: Dict[str, Any]) -> Dict[str, Any]:
    term_policy = profile_config.get("termPolicy", {}) if isinstance(profile_config, dict) else {}
    allow_repeated = {
        item for item in term_policy.get("allowRepeated", [])
        if isinstance(item, str) and item
    }
    watch_terms = [
        item for item in term_policy.get("watchTerms", [])
        if isinstance(item, str) and item
    ]
    suffixes = [
        item for item in term_policy.get("specialTermSuffixes", [])
        if isinstance(item, str) and item
    ]
    per_term_thresholds = {
        key: int(value)
        for key, value in term_policy.get("perTermThresholds", {}).items()
        if isinstance(key, str) and key and isinstance(value, int) and value >= 1
    }
    candidates: List[str] = []
    quoted_terms = re.findall(r"[“「『《]([^”」』》]{2,10})[”」』》]", text)
    suffix_pattern = "|".join(
        re.escape(item)
        for item in [
            "效应", "法则", "定律", "理论", "模型", "体系", "术式", "仪式", "回路", "协议",
            "计划", "印记", "烙印", "命格", "命途", "体质", "灵根", "血脉", "规则",
            *suffixes,
        ]
    )
    suffix_matches = re.findall(
        f"([{CJK_RANGE}]{{2,10}}(?:{suffix_pattern}))",
        text,
    ) if suffix_pattern else []
    candidates.extend(term for term in quoted_terms if _is_special_term_candidate(term))
    for raw_term in suffix_matches:
        candidates.extend(_normalize_suffix_term_candidates(raw_term))
    for term in watch_terms:
        candidates.extend([term] * text.count(term))

    counts = Counter(candidates)
    repeated = [
        {"term": term, "count": count}
        for term, count in counts.items()
        if not _term_is_allowlisted(term, allow_repeated) and count >= per_term_thresholds.get(term, 3)
    ]
    repeated.sort(key=lambda item: (-item["count"], item["term"]))
    if not repeated:
        return {
            "detected": False,
            "severity": "none",
            "count": 0,
            "evidence": [],
            "topTerms": [],
        }

    top_count = repeated[0]["count"]
    if top_count >= 6:
        severity = "high"
    elif top_count >= 4:
        severity = "medium"
    else:
        severity = "low"
    return {
        "detected": True,
        "severity": severity,
        "count": sum(item["count"] for item in repeated),
        "evidence": [f"{item['term']} ×{item['count']}" for item in repeated[:3]],
        "topTerms": repeated[:5],
    }


def _detect_register_drift(text: str, profile_config: Dict[str, Any]) -> Dict[str, Any]:
    register_policy = profile_config.get("registerPolicy", {}) if isinstance(profile_config, dict) else {}
    allow_terms = {
        item for item in register_policy.get("allowTerms", [])
        if isinstance(item, str) and item
    }
    categories = [
        item for item in register_policy.get("disallowedCategories", [])
        if isinstance(item, dict)
    ]
    matched_categories: List[Dict[str, Any]] = []
    evidence: List[str] = []
    total_hits = 0

    for category in categories:
        terms = [
            item for item in category.get("terms", [])
            if isinstance(item, str) and item and not _term_is_allowlisted(item, allow_terms)
        ]
        matches = []
        for term in terms:
            count = text.count(term)
            if count <= 0:
                continue
            matches.append({"term": term, "count": count})
            total_hits += count
        if not matches:
            continue
        matches.sort(key=lambda item: (-item["count"], item["term"]))
        matched_categories.append(
            {
                "id": category.get("id", ""),
                "label": category.get("label", ""),
                "matches": matches,
                "suggestion": category.get("suggestion", ""),
            }
        )
        top_terms = "、".join(f"{item['term']}×{item['count']}" for item in matches[:3])
        label = category.get("label", "题材语域失真")
        evidence.append(f"{label}：{top_terms}")

    if not matched_categories:
        return {
            "detected": False,
            "severity": "none",
            "count": 0,
            "evidence": [],
            "matchedCategories": [],
            "suggestion": "",
        }

    distinct_terms = sum(len(item.get("matches", [])) for item in matched_categories)
    if total_hits >= 4 or distinct_terms >= 3:
        severity = "high"
    elif total_hits >= 2 or distinct_terms >= 2:
        severity = "medium"
    else:
        severity = "low"

    suggestion = matched_categories[0].get("suggestion", "")
    return {
        "detected": True,
        "severity": severity,
        "count": total_hits,
        "evidence": evidence[:3],
        "matchedCategories": matched_categories[:5],
        "suggestion": suggestion,
    }


def _detect_structured_plan_block(paragraphs: List[str], profile_config: Dict[str, Any]) -> Dict[str, Any]:
    plan_block_policy = profile_config.get("planBlockPolicy", {}) if isinstance(profile_config, dict) else {}
    allow_labels = {
        item for item in plan_block_policy.get("allowLabels", [])
        if isinstance(item, str) and item
    }
    min_labels = plan_block_policy.get("minLabels", 3)
    min_distinct_labels = plan_block_policy.get("minDistinctLabels", 2)
    if not isinstance(min_labels, int) or min_labels < 2:
        min_labels = 3
    if not isinstance(min_distinct_labels, int) or min_distinct_labels < 2:
        min_distinct_labels = 2

    blocks: List[Dict[str, Any]] = []
    current_lines: List[str] = []
    current_labels: List[str] = []

    def flush_current() -> None:
        if not current_labels:
            return
        distinct_labels = sorted(set(current_labels))
        blocks.append(
            {
                "labels": list(current_labels),
                "distinctLabels": distinct_labels,
                "evidence": list(current_lines[:3]),
            }
        )

    for paragraph in paragraphs:
        paragraph_hits = _plan_block_hits_for_paragraph(paragraph, allow_labels)
        if not paragraph_hits:
            flush_current()
            current_lines = []
            current_labels = []
            continue
        current_lines.extend(item["line"] for item in paragraph_hits)
        current_labels.extend(item["label"] for item in paragraph_hits)

    flush_current()
    if not blocks:
        return {
            "detected": False,
            "severity": "none",
            "count": 0,
            "evidence": [],
            "matchedLabels": [],
            "suggestion": "",
        }

    blocks = [
        item for item in blocks
        if len(item["labels"]) >= min_labels and len(item["distinctLabels"]) >= min_distinct_labels
    ]
    if not blocks:
        return {
            "detected": False,
            "severity": "none",
            "count": 0,
            "evidence": [],
            "matchedLabels": [],
            "suggestion": "",
        }

    blocks.sort(
        key=lambda item: (
            len(item["labels"]),
            len(item["distinctLabels"]),
        ),
        reverse=True,
    )
    best_block = blocks[0]
    label_count = len(best_block["labels"])
    distinct_count = len(best_block["distinctLabels"])
    severity = "high" if label_count >= 4 or distinct_count >= 3 else "medium"
    return {
        "detected": True,
        "severity": severity,
        "count": label_count,
        "evidence": best_block["evidence"],
        "matchedLabels": best_block["distinctLabels"],
        "suggestion": "将“目标/风险/约束”式清单改写成角色行动、顾虑、代价与抉择，避免正文像方案说明。",
    }


def _plan_block_hits_for_paragraph(paragraph: str, allow_labels: set[str]) -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    for raw_line in paragraph.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for label in PLAN_BLOCK_LABELS:
            if label in allow_labels:
                continue
            if re.match(rf"^{re.escape(label)}[：:]", line):
                hits.append({"label": label, "line": line})
                break
    return hits


def _detect_narrative_frame_repetition(text: str, profile_config: Dict[str, Any]) -> Dict[str, Any]:
    frame_policy = profile_config.get("framePolicy", {}) if isinstance(profile_config, dict) else {}
    allow_prefixes = {
        item for item in frame_policy.get("allowPrefixes", [])
        if isinstance(item, str) and item
    }
    per_prefix_thresholds = {
        key: int(value)
        for key, value in frame_policy.get("perPrefixThresholds", {}).items()
        if isinstance(key, str) and key and isinstance(value, int) and value >= 1
    }
    prefix_counts: Counter[str] = Counter()
    prefix_tails: Dict[str, set[str]] = {}

    tail_pattern = "|".join(sorted((re.escape(item) for item in ABSTRACT_FRAME_TAILS), key=len, reverse=True))
    if not tail_pattern:
        return {
            "detected": False,
            "severity": "none",
            "count": 0,
            "evidence": [],
            "topFrames": [],
        }

    pattern = re.compile(f"([{CJK_RANGE}]{{2,6}}的)({tail_pattern})")
    for prefix, tail in pattern.findall(text):
        if prefix in allow_prefixes:
            continue
        if prefix in CONCRETE_FRAME_PREFIXES:
            continue
        prefix_counts[prefix] += 1
        prefix_tails.setdefault(prefix, set()).add(tail)

    repeated = []
    for prefix, count in prefix_counts.items():
        threshold = per_prefix_thresholds.get(prefix, 3)
        tails = sorted(prefix_tails.get(prefix, set()))
        if count < threshold or len(tails) < 2:
            continue
        repeated.append(
            {
                "prefix": prefix,
                "count": count,
                "tails": tails[:5],
            }
        )
    repeated.sort(key=lambda item: (-item["count"], item["prefix"]))

    if not repeated:
        return {
            "detected": False,
            "severity": "none",
            "count": 0,
            "evidence": [],
            "topFrames": [],
        }

    top_count = repeated[0]["count"]
    if top_count >= 4:
        severity = "high"
    elif top_count >= 3:
        severity = "medium"
    else:
        severity = "low"
    return {
        "detected": True,
        "severity": severity,
        "count": sum(item["count"] for item in repeated),
        "evidence": [f"{item['prefix']}×{item['count']}（{ '、'.join(item['tails'][:3]) }）" for item in repeated[:3]],
        "topFrames": repeated[:5],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deduction_for_severity(severity: str) -> int:
    if severity == "low":
        return 1
    if severity == "medium":
        return 2
    if severity == "high":
        return 3
    return 0

def _severity(per_thousand: float, threshold: float) -> str:
    if per_thousand <= threshold:
        return "none"
    ratio = per_thousand / threshold
    if ratio < 1.5:
        return "low"
    if ratio < 2.5:
        return "medium"
    return "high"


def _pattern_suggestion(pattern_id: str, severity: str, value: float, threshold: float) -> str:
    if severity == "none":
        return ""
    msgs = {
        "simileDensity": f"比喻密度偏高（每千字{value:.1f}次，建议<{threshold:.0f}），尝试用具体动作或白描替代部分比喻",
        "hedgeAdverbs": f"模糊副词偏多（每千字{value:.1f}次），尝试用具体感官描写替代'微微'、'不禁'等",
        "tellingEmotion": f"叙述性情感偏多（每千字{value:.1f}次），尝试通过动作、表情、生理反应展示情绪",
        "formulaicTransition": f"程式化过渡偏多（每千字{value:.1f}次），尝试用情节推进自然过渡",
        "contrastFlipPattern": f"“不是……是……”类翻转句偏多（每千字{value:.1f}次），优先改成直接动作、结果或判断，不要反复先否后立",
        "analogicalPivotPattern": f"“不像……更像……”类翻转句偏多（每千字{value:.1f}次），优先写清人物实际观察到的事实，不要总靠抽象换挡",
        "templateCatchphrasePattern": f"模板化口癖偏多（每千字{value:.1f}次），应减少故作深沉的套话或追问式短句，拉开人物口吻差异",
    }
    return msgs.get(pattern_id, "")


def _sensory_result(sensory: Dict[str, Any]) -> Dict[str, Any]:
    missing = sensory["missingSenses"]
    detected = len(missing) >= 2
    return {
        "id": "sensoryVariety",
        "label": "感官单一",
        "detected": detected,
        "count": sum(1 for k in ["visual", "auditory", "tactile", "olfactory", "gustatory"] if sensory.get(k, 0) > 0),
        "perThousand": 0,
        "threshold": 3,
        "severity": "medium" if detected else "none",
        "evidence": [],
        "suggestion": f"感官描写单一，缺少{'和'.join(missing)}描写" if detected else "",
    }


def _uniformity_result(uniformity: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": "paragraphUniformity",
        "label": "段落均质",
        "detected": uniformity["isUniform"],
        "count": 0,
        "perThousand": 0,
        "threshold": 0,
        "severity": "medium" if uniformity["isUniform"] else "none",
        "evidence": [],
        "suggestion": "段落长度过于均匀，可调整长短交替制造节奏感" if uniformity["isUniform"] else "",
    }


def _paragraph_readability_result(readability: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": "paragraphReadability",
        "label": "段落可读性",
        "detected": readability.get("detected", False),
        "count": readability.get("count", 0),
        "perThousand": 0,
        "threshold": readability.get("threshold", 110),
        "severity": readability.get("severity", "none"),
        "evidence": readability.get("evidence", []),
        "suggestion": (
            "存在过长段落，移动端阅读压力偏大；可按动作、反应、信息点拆段，让每段只承载一个主要推进单位"
            if readability.get("detected", False)
            else ""
        ),
    }


def _repetition_result(repetition: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": "sentenceRepetition",
        "label": "句式重复",
        "detected": repetition["hasRepetition"],
        "count": len(repetition["repeatedStructures"]),
        "perThousand": 0,
        "threshold": 0,
        "severity": "medium" if repetition["hasRepetition"] else "none",
        "evidence": [r["pattern"] + "..." for r in repetition["repeatedStructures"][:3]],
        "source": repetition["source"],
        "suggestion": "连续段落开头句式重复，可变化句首结构" if repetition["hasRepetition"] else "",
    }


def _special_term_result(special_terms: Dict[str, Any]) -> Dict[str, Any]:
    top_terms = special_terms.get("topTerms", [])
    top_label = "、".join(item["term"] for item in top_terms[:2])
    suggestion = ""
    if special_terms.get("detected"):
        suggestion = f"特殊术语复用偏多（如 {top_label}），可减少直呼其名的次数，改用动作结果、人物理解或上下文代称分散表达"
    return {
        "id": "specialTermRepetition",
        "label": "特殊术语复用",
        "detected": special_terms.get("detected", False),
        "count": special_terms.get("count", 0),
        "perThousand": 0,
        "threshold": 3,
        "severity": special_terms.get("severity", "none"),
        "evidence": special_terms.get("evidence", []),
        "suggestion": suggestion,
    }


def _register_drift_result(register_drift: Dict[str, Any]) -> Dict[str, Any]:
    suggestion = register_drift.get("suggestion", "") if register_drift.get("detected") else ""
    return {
        "id": "registerDrift",
        "label": "题材语域失真",
        "detected": register_drift.get("detected", False),
        "count": register_drift.get("count", 0),
        "perThousand": 0,
        "threshold": 0,
        "severity": register_drift.get("severity", "none"),
        "evidence": register_drift.get("evidence", []),
        "suggestion": suggestion,
    }


def _structured_plan_block_result(structured_plan_block: Dict[str, Any]) -> Dict[str, Any]:
    suggestion = structured_plan_block.get("suggestion", "") if structured_plan_block.get("detected") else ""
    return {
        "id": "structuredPlanBlock",
        "label": "方案文档腔",
        "detected": structured_plan_block.get("detected", False),
        "count": structured_plan_block.get("count", 0),
        "perThousand": 0,
        "threshold": 0,
        "severity": structured_plan_block.get("severity", "none"),
        "evidence": structured_plan_block.get("evidence", []),
        "suggestion": suggestion,
    }


def _narrative_frame_result(narrative_frames: Dict[str, Any]) -> Dict[str, Any]:
    suggestion = ""
    top_frames = narrative_frames.get("topFrames", [])
    if narrative_frames.get("detected") and top_frames:
        sample = top_frames[0]["prefix"]
        suggestion = f"叙事支架短语复用偏多（如 {sample}××），可改用当下动作、代价反馈或新的认知落点承接，不要反复用同一解释框架起句"
    return {
        "id": "narrativeFrameRepetition",
        "label": "叙事支架复用",
        "detected": narrative_frames.get("detected", False),
        "count": narrative_frames.get("count", 0),
        "perThousand": 0,
        "threshold": 3,
        "severity": narrative_frames.get("severity", "none"),
        "evidence": narrative_frames.get("evidence", []),
        "suggestion": suggestion,
    }


def _exact_similarity(left: str, right: str) -> float:
    return 100.0 if left == right else 0.0


def _average_length(paragraphs: List[str]) -> int:
    if not paragraphs:
        return 0
    return round(sum(len(item) for item in paragraphs) / len(paragraphs))


def _count_cjk(text: str) -> int:
    return len(re.findall(f"[{CJK_RANGE}]", text))


def _empty_result() -> Dict[str, Any]:
    return {
        "overallScore": 20,
        "totalDeduction": 0,
        "patternResults": [],
        "sensoryDistribution": {},
        "paragraphUniformity": {},
        "paragraphReadability": {},
        "sentenceRepetition": {},
        "specialTermRepetition": {},
        "narrativeFrameRepetition": {},
        "registerDrift": {},
        "structuredPlanBlock": {},
        "metaLeakage": {},
        "judgements": [],
        "summary": "文本过短，跳过风格检测",
        "suggestions": [],
    }


def _build_short_text_result(
    pattern_results: List[Dict[str, Any]],
    total_deduction: int,
    *,
    meta_leakage: Dict[str, Any],
    review_rule_config: Dict[str, Any],
) -> Dict[str, Any]:
    if not pattern_results:
        return _empty_result()

    detected = [item for item in pattern_results if item.get("detected")]
    if detected:
        summary = f"文本较短，仅执行规则型检测；{_generate_summary(pattern_results, total_deduction)}"
    else:
        summary = "文本较短，仅执行规则型检测，未发现未豁免的问题。"
    suggestions = [
        item["suggestion"]
        for item in pattern_results
        if item.get("detected") and item.get("suggestion")
    ]
    return {
        "overallScore": max(0, 20 - total_deduction),
        "totalDeduction": total_deduction,
        "patternResults": pattern_results,
        "sensoryDistribution": {},
        "paragraphUniformity": {},
        "paragraphReadability": {},
        "sentenceRepetition": {},
        "specialTermRepetition": {},
        "narrativeFrameRepetition": {},
        "registerDrift": {},
        "structuredPlanBlock": {},
        "metaLeakage": meta_leakage,
        "judgements": _build_style_judgements(pattern_results, {}, review_rule_config),
        "summary": summary,
        "suggestions": suggestions[:5],
    }


def _generate_summary(results: List[Dict[str, Any]], deduction: int) -> str:
    detected = [r for r in results if r.get("detected")]
    if not detected:
        return "未检测到明显AI风格特征。"
    labels = "、".join(r["label"] for r in detected)
    return f"检测到{len(detected)}项AI风格特征：{labels}。扣{deduction}分。"


def _is_special_term_candidate(term: str) -> bool:
    if len(term) < 2 or len(term) > 10:
        return False
    if re.search(r"(今天|现在|自己|事情|时候|地方|东西|问题|声音|目光|空气)$", term):
        return False
    return True


def _normalize_suffix_term_candidates(raw_term: str) -> List[str]:
    if len(raw_term) <= 4:
        return [raw_term] if _is_special_term_candidate(raw_term) else []
    variants: List[str] = []
    for prefix_len in range(2, min(6, len(raw_term) - 1) + 1):
        candidate = raw_term[-(prefix_len + 2):]
        if _is_special_term_candidate(candidate):
            variants.append(candidate)
    if _is_special_term_candidate(raw_term):
        variants.append(raw_term)
    deduped: List[str] = []
    for item in variants:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _term_is_allowlisted(term: str, allow_repeated: set[str]) -> bool:
    return any(allowed in term or term in allowed for allowed in allow_repeated)


# ---------------------------------------------------------------------------
# Constraint generation
# ---------------------------------------------------------------------------

def generate_style_constraints(style_result: Dict[str, Any]) -> List[str]:
    """Generate writing constraint rules from detection results."""
    constraints: List[str] = []
    for r in style_result.get("patternResults", []):
        if r.get("severity") in ("medium", "high") and r.get("suggestion"):
            constraints.append(r["suggestion"])
    return constraints


def build_style_repair_prompt(
    chapter_text: str,
    style_report: Dict[str, Any],
    *,
    chapter_id: str,
) -> str:
    """Build a prompt that asks a model to repair AI-typical style issues."""
    style_analysis = style_report.get("styleAnalysis", {})
    constraints = style_report.get("constraints", [])
    detected_patterns = [
        item["label"]
        for item in style_analysis.get("patternResults", [])
        if item.get("detected")
    ]
    summary = style_analysis.get("summary", "")
    lines = [
        f"请对章节 {chapter_id} 做风格精修。",
        "目标：保留剧情事实、角色关系、顺序和信息量，只降低 AI 风格痕迹。",
        f"当前检测摘要：{summary}",
    ]
    if detected_patterns:
        lines.append(f"重点问题：{'、'.join(detected_patterns)}。")
    if constraints:
        lines.append("必须遵守的 style constraints：")
        lines.extend(f"- {item}" for item in constraints)
    lines.extend(
        [
            "输出要求：",
            "- 不得改动剧情结论、人物姓名、设定事实和关键线索。",
            "- 优先重写重复句式、模糊副词和程式化过渡句。",
            "- 优先把直接情绪陈述改成动作、对话或感官细节。",
            "- 输出修订后的完整章节正文，不要附解释。",
            "",
            "原文如下：",
            chapter_text,
        ]
    )
    return "\n".join(lines)


def build_style_change_request_drafts(
    chapter_id: str,
    style_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build change-request-like drafts from style analysis results."""
    drafts: List[Dict[str, Any]] = []
    for item in style_report.get("styleAnalysis", {}).get("patternResults", []):
        if item.get("severity") not in ("medium", "high"):
            continue
        label = item.get("label", item.get("id", "style"))
        evidence = "；".join(item.get("evidence", [])[:3]) or item.get("suggestion", "")
        fingerprint = f"style::{chapter_id}::{item.get('id', label)}::{item.get('severity', '')}"
        drafts.append(
            {
                "id": f"cr-{stable_hash(fingerprint + now_iso())}",
                "chapterId": chapter_id,
                "kind": "style",
                "severity": "suggestion" if item.get("severity") == "medium" else "important",
                "title": f"修复章节风格问题：{label}",
                "summary": item.get("suggestion", ""),
                "evidence": evidence,
                "targetIds": [],
                "confidence": 0.7 if item.get("severity") == "medium" else 0.85,
                "suggestedPayload": {
                    "patternId": item.get("id", ""),
                    "label": label,
                    "severity": item.get("severity", ""),
                    "suggestion": item.get("suggestion", ""),
                },
                "status": "draft",
                "projectionStatus": "n/a",
                "fingerprint": fingerprint,
                "createdAt": now_iso(),
                "updatedAt": now_iso(),
            }
        )
    return drafts
