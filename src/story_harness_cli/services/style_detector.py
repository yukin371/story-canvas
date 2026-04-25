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


SimilarityScorer = Callable[[str, str], float]
CJK_RANGE = f"{chr(0x4E00)}-{chr(0x9FFF)}"


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
) -> Dict[str, Any]:
    """Run all AI style detection patterns against chapter text.

    Returns a dict with patternResults, sensoryDistribution,
    paragraphUniformity, sentenceRepetition, and scoring info.
    """
    word_count = _count_cjk(clean_text)
    if word_count < 50:
        return _empty_result()

    results: List[Dict[str, Any]] = []
    total_deduction = 0

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
        "sentenceRepetition": repetition,
        "specialTermRepetition": special_terms,
        "sources": {
            "sentenceRepetition": repetition["source"],
        },
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
    )
    constraints = generate_style_constraints(style_analysis)
    return {
        "profile": profile_name,
        "styleAnalysis": style_analysis,
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        "sentenceRepetition": {},
        "specialTermRepetition": {},
        "summary": "文本过短，跳过风格检测",
        "suggestions": [],
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
