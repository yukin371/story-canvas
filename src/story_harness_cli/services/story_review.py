from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from story_harness_cli.utils import now_iso, stable_hash
from story_harness_cli.utils.project_meta import normalize_machine_label, normalize_primary_genre
from story_harness_cli.utils.text import count_words, extract_tag_mentions, paragraphs_from_text, strip_entity_tags

from .analyzer import chapter_title
from .style_detector import analyze_style_text


RUBRIC_VERSION = "chapter-review-v1"
SCENE_RUBRIC_VERSION = "scene-review-v1"
MAX_DIMENSION_SCORE = 20
PLOT_CONNECTORS = ("但是", "却", "然而", "于是", "随后", "突然", "结果", "直到", "终于", "这才")
PRESSURE_KEYWORDS = ("害怕", "恐惧", "怀疑", "犹豫", "挣扎", "后悔", "愤怒", "紧张", "秘密", "代价")
TENSION_KEYWORDS = ("冲突", "争吵", "危险", "威胁", "追逐", "背叛", "裂痕", "秘密", "失控", "崩溃", "追杀")
SETTING_KEYWORDS = (
    "清晨",
    "午后",
    "傍晚",
    "深夜",
    "雨",
    "雪",
    "风",
    "街",
    "巷",
    "屋",
    "房间",
    "仓库",
    "酒馆",
    "学校",
    "医院",
    "车站",
    "天台",
)
SCENE_BREAK_KEYWORDS = (
    "三天后",
    "一天后",
    "第二天",
    "第三天",
    "几天后",
    "几分钟后",
    "十五分钟后",
    "一个月后",
    "三个月后",
    "当晚",
    "当天晚上",
    "第二天早上",
    "与此同时",
    "另一边",
    "就在这时",
    "就在此时",
    "此时",
    "这时",
    "现在",
    "新的一天",
)
SCENE_CONTINUITY_KEYWORDS = (
    "随后",
    "这时",
    "仍然",
    "继续",
    "再次",
    "已经",
    "回到",
    "同时",
    "与此同时",
    "另一边",
    "现在",
    "想起",
    "曾经",
    "这意味着",
)
SCENE_CHANGE_KEYWORDS = ("发现", "决定", "答应", "拒绝", "交出", "离开", "开始", "终于", "确认", "暴露", "质问")
CAUSALITY_KEYWORDS = ("因为", "所以", "因此", "于是", "为了", "导致", "结果", "如果", "既然", "不得不", "只能", "意味着")
MOTIVATION_KEYWORDS = ("想", "决定", "打算", "必须", "为了", "害怕", "怀疑", "相信", "不敢", "希望")
FORESHADOWING_SETUP_KEYWORDS = ("秘密", "线索", "异样", "不对劲", "预感", "似乎", "隐约", "传言", "迹象", "账本")
FORESHADOWING_PAYOFF_KEYWORDS = (
    "原来",
    "果然",
    "应验",
    "揭开",
    "真相",
    "兑现",
    "回想",
    "想起",
    "曾经说过",
    "终于明白",
    "证实",
    "这意味着",
)
HOOK_KEYWORDS = ("秘密", "真相", "代价", "危险", "账本", "背叛", "是谁", "为什么")

CHAPTER_REVIEW_RUBRIC = [
    {"id": "plotMomentum", "label": "情节推进", "maxScore": MAX_DIMENSION_SCORE, "focus": "这一章是否产生了明确推进或落点"},
    {"id": "characterPressure", "label": "人物压力", "maxScore": MAX_DIMENSION_SCORE, "focus": "人物是否承受了新的压力、状态变化或选择"},
    {"id": "conflictTension", "label": "冲突张力", "maxScore": MAX_DIMENSION_SCORE, "focus": "文本里是否存在阻力、风险、悬念或对抗"},
    {"id": "sceneClarity", "label": "场景清晰度", "maxScore": MAX_DIMENSION_SCORE, "focus": "读者能否快速抓到场景、角色和叙事焦点"},
    {"id": "proseControl", "label": "表达控制", "maxScore": MAX_DIMENSION_SCORE, "focus": "段落节奏、句式负担和强调是否受控"},
]
SCENE_REVIEW_RUBRIC = [
    {"id": "sceneFunction", "label": "场景功能", "maxScore": MAX_DIMENSION_SCORE, "focus": "这一幕是否承担推进、转折、铺垫或兑现任务"},
    {"id": "continuity", "label": "连续性", "maxScore": MAX_DIMENSION_SCORE, "focus": "这一幕是否与前后文形成承接，而不是孤立切片"},
    {"id": "logic", "label": "逻辑性", "maxScore": MAX_DIMENSION_SCORE, "focus": "人物行动、因果链和信息流是否说得通"},
    {"id": "foreshadowing", "label": "伏笔与回收", "maxScore": MAX_DIMENSION_SCORE, "focus": "这一幕是否种下信息、维持悬念或完成局部兑现"},
    {"id": "sceneClarity", "label": "场景清晰度", "maxScore": MAX_DIMENSION_SCORE, "focus": "读者能否迅速抓到时间、地点、角色和冲突焦点"},
]

BASE_GENRE_WEIGHTS = {
    "default": {
        "plotMomentum": 20,
        "characterPressure": 20,
        "conflictTension": 20,
        "sceneClarity": 20,
        "proseControl": 20,
    },
    "literary": {
        "plotMomentum": 15,
        "characterPressure": 25,
        "conflictTension": 10,
        "sceneClarity": 20,
        "proseControl": 30,
    },
    "romance": {
        "plotMomentum": 20,
        "characterPressure": 30,
        "conflictTension": 15,
        "sceneClarity": 10,
        "proseControl": 25,
    },
    "mystery": {
        "plotMomentum": 20,
        "characterPressure": 15,
        "conflictTension": 35,
        "sceneClarity": 15,
        "proseControl": 15,
    },
    "thriller": {
        "plotMomentum": 20,
        "characterPressure": 15,
        "conflictTension": 35,
        "sceneClarity": 15,
        "proseControl": 15,
    },
    "fantasy": {
        "plotMomentum": 20,
        "characterPressure": 15,
        "conflictTension": 20,
        "sceneClarity": 30,
        "proseControl": 15,
    },
    "science-fiction": {
        "plotMomentum": 20,
        "characterPressure": 15,
        "conflictTension": 20,
        "sceneClarity": 30,
        "proseControl": 15,
    },
    "historical": {
        "plotMomentum": 15,
        "characterPressure": 20,
        "conflictTension": 15,
        "sceneClarity": 30,
        "proseControl": 20,
    },
    "ya": {
        "plotMomentum": 20,
        "characterPressure": 30,
        "conflictTension": 15,
        "sceneClarity": 10,
        "proseControl": 25,
    },
}

SUBGENRE_WEIGHT_DELTAS = {
    "western-fantasy": {"sceneClarity": 10, "plotMomentum": -5, "proseControl": -5},
    "xuanhuan": {"plotMomentum": 10, "conflictTension": 5, "sceneClarity": 5, "characterPressure": -10, "proseControl": -10},
}

STYLE_WEIGHT_DELTAS = {
    "light-novel": {"plotMomentum": 10, "characterPressure": 5, "proseControl": 5, "sceneClarity": -5, "conflictTension": -5},
    "web-serial": {"plotMomentum": 5, "conflictTension": 5, "proseControl": -5, "sceneClarity": -5},
}

PLATFORM_WEIGHT_DELTAS = {
    "qidian": {"plotMomentum": 5, "conflictTension": 5, "proseControl": -5, "sceneClarity": -5},
    "jjwxc": {"characterPressure": 5, "proseControl": 5, "plotMomentum": -5, "sceneClarity": -5},
}


def build_chapter_review(
    state: Dict[str, Dict[str, Any]],
    chapter_id: str,
    chapter_text: str,
    analysis: Dict[str, Any] | None = None,
    style_report: Dict[str, Any] | None = None,
    consistency_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    analysis = analysis or {}
    clean_text = strip_entity_tags(chapter_text)
    paragraphs = paragraphs_from_text(clean_text)
    style_report = style_report or analyze_style_text(chapter_text)
    word_count = count_words(clean_text)
    mention_names = sorted({name for name in extract_tag_mentions(chapter_text) if name})
    active_entities = list(analysis.get("activeEntities", []))
    snapshot_candidates = list(analysis.get("snapshotCandidates", []))
    relation_candidates = list(analysis.get("relationCandidates", []))
    scene_entities = analysis.get("sceneScope", {}).get("activeEntityNames", []) or mention_names[:6]
    story_constraint_signals = _build_story_constraint_signals(state, chapter_id, scene_entities or mention_names)
    consistency_result = consistency_result or {}
    consistency_signals = _build_consistency_signals(style_report, consistency_result)

    text_metrics = {
        "wordCount": word_count,
        "paragraphCount": len(paragraphs),
        "averageParagraphLength": _average_length(paragraphs),
        "dialogueParagraphs": _dialogue_paragraphs(paragraphs),
        "tagMentions": mention_names,
    }
    analysis_signals = {
        "analysisBacked": bool(analysis),
        "activeEntityCount": len(active_entities) if active_entities else len(mention_names),
        "snapshotCandidateCount": len(snapshot_candidates),
        "relationCandidateCount": len(relation_candidates),
        "sceneEntityNames": scene_entities,
        "settingCandidateCount": len(consistency_signals["settingCandidates"]),
        "settingConflictCount": len(consistency_signals["settingConflicts"]),
    }

    dimensions = [
        _score_plot_momentum(word_count, paragraphs, snapshot_candidates, relation_candidates, clean_text),
        _score_character_pressure(active_entities, mention_names, snapshot_candidates, clean_text),
        _score_conflict_tension(relation_candidates, clean_text),
        _score_scene_clarity(paragraphs, scene_entities, clean_text),
        _score_prose_control(paragraphs, clean_text, style_report),
    ]
    dimension_map = {item["id"]: item for item in dimensions}
    total_score = sum(item["score"] for item in dimensions)
    weighted_scores = _build_weighted_scores(state.get("project", {}), dimension_map)
    best = max(dimensions, key=lambda item: item["score"])
    weakest = min(dimensions, key=lambda item: item["score"])

    strengths = [f"{item['label']}：{item['comment']}" for item in dimensions if item["score"] >= 16]
    if not strengths:
        strengths = [f"{best['label']}：{best['comment']}"]

    priority_actions: List[str] = []
    for item in sorted(dimensions, key=lambda current: current["score"]):
        for suggestion in item["suggestions"]:
            if suggestion not in priority_actions:
                priority_actions.append(suggestion)
            if len(priority_actions) >= 4:
                break
        if len(priority_actions) >= 4:
            break
    for suggestion in _consistency_priority_actions(consistency_signals):
        if suggestion not in priority_actions:
            priority_actions.insert(0, suggestion)
        if len(priority_actions) > 4:
            priority_actions = priority_actions[:4]

    fingerprint = f"{RUBRIC_VERSION}:{chapter_id}:{stable_hash(clean_text, size=16)}"
    contract_alignment = _evaluate_contract_alignment(
        state.get("project", {}),
        dimension_map,
        text_metrics,
        clean_text,
        story_constraint_signals,
    )
    _apply_consistency_signals_to_alignment(contract_alignment, consistency_signals)
    return {
        "reviewId": f"chapter-review-{stable_hash(fingerprint)}",
        "fingerprint": fingerprint,
        "rubricVersion": RUBRIC_VERSION,
        "generatedAt": now_iso(),
        "chapterId": chapter_id,
        "chapterTitle": chapter_title(state["outline"], chapter_id),
        "summary": _build_summary(total_score, best["label"], weakest["label"], bool(analysis)),
        "rating": _rating_label(total_score),
        "scores": {
            "total": total_score,
            "maxScore": MAX_DIMENSION_SCORE * len(dimensions),
            "dimensions": dimensions,
        },
        "weightedScores": weighted_scores,
        "strengths": strengths,
        "priorityActions": priority_actions,
        "textMetrics": text_metrics,
        "analysisSignals": analysis_signals,
        "styleAnalysis": style_report,
        "projectContext": {
            "genre": state.get("project", {}).get("genre", ""),
            "positioning": state.get("project", {}).get("positioning", {}),
            "storyContract": state.get("project", {}).get("storyContract", {}),
            "emotionalContract": state.get("project", {}).get("emotionalContract", {}),
            "storyTemplate": state.get("project", {}).get("storyTemplate", {}),
            "commercialPositioning": state.get("project", {}).get("commercialPositioning", {}),
        },
        "storyConstraintSignals": story_constraint_signals,
        "consistencySignals": consistency_signals,
        "contractAlignment": contract_alignment,
        "commercialAlignment": _evaluate_commercial_chapter_alignment(
            state.get("project", {}),
            dimension_map,
            text_metrics,
            clean_text,
            paragraphs,
        ),
        "rubric": CHAPTER_REVIEW_RUBRIC,
    }


def build_scene_review(
    state: Dict[str, Dict[str, Any]],
    chapter_id: str,
    chapter_text: str,
    start_paragraph: int,
    end_paragraph: int,
    analysis: Dict[str, Any] | None = None,
    style_report: Dict[str, Any] | None = None,
    consistency_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    analysis = analysis or {}
    raw_paragraphs = paragraphs_from_text(chapter_text)
    clean_paragraphs = [strip_entity_tags(item) for item in raw_paragraphs]
    total_paragraphs = len(clean_paragraphs)
    if total_paragraphs == 0:
        raise ValueError("章节中没有可评审的正文段落")
    if start_paragraph < 1 or end_paragraph < start_paragraph or end_paragraph > total_paragraphs:
        raise ValueError(f"段落范围无效，可用范围为 1..{total_paragraphs}")

    start_index = start_paragraph - 1
    end_index = end_paragraph
    selected_raw = raw_paragraphs[start_index:end_index]
    selected_clean = clean_paragraphs[start_index:end_index]
    previous_raw = raw_paragraphs[start_index - 1] if start_index > 0 else ""
    next_raw = raw_paragraphs[end_index] if end_index < total_paragraphs else ""
    previous_clean = clean_paragraphs[start_index - 1] if start_index > 0 else ""
    next_clean = clean_paragraphs[end_index] if end_index < total_paragraphs else ""

    scene_text = "\n\n".join(selected_clean)
    raw_scene_text = "\n\n".join(selected_raw)
    style_report = style_report or analyze_style_text(raw_scene_text)
    mention_names = sorted({name for name in extract_tag_mentions(raw_scene_text) if name})
    scene_analysis = _filter_analysis_for_scene(analysis, selected_clean, mention_names)
    story_constraint_signals = _build_story_constraint_signals(
        state,
        chapter_id,
        [item.get("name") for item in scene_analysis["activeEntities"] if item.get("name")] or mention_names,
    )
    consistency_result = consistency_result or {}
    consistency_signals = _build_consistency_signals(style_report, consistency_result)

    text_metrics = {
        "wordCount": count_words(scene_text),
        "paragraphCount": len(selected_clean),
        "averageParagraphLength": _average_length(selected_clean),
        "tagMentions": mention_names,
        "totalChapterParagraphs": total_paragraphs,
    }
    analysis_signals = {
        "analysisBacked": bool(analysis),
        "activeEntityCount": len(scene_analysis["activeEntities"]) if scene_analysis["activeEntities"] else len(mention_names),
        "snapshotCandidateCount": len(scene_analysis["snapshotCandidates"]),
        "relationCandidateCount": len(scene_analysis["relationCandidates"]),
        "settingCandidateCount": len(consistency_signals["settingCandidates"]),
        "settingConflictCount": len(consistency_signals["settingConflicts"]),
    }

    dimensions = [
        _score_scene_function(selected_clean, scene_analysis["snapshotCandidates"], scene_analysis["relationCandidates"], scene_text),
        _score_scene_continuity(selected_raw, previous_raw, next_raw, previous_clean, next_clean),
        _score_scene_logic(scene_analysis["snapshotCandidates"], scene_analysis["relationCandidates"], scene_text),
        _score_scene_foreshadowing(scene_analysis["relationCandidates"], scene_text),
        _score_scene_clarity(selected_clean, mention_names, scene_text),
    ]
    dimension_map = {item["id"]: item for item in dimensions}
    total_score = sum(item["score"] for item in dimensions)
    best = max(dimensions, key=lambda item: item["score"])
    weakest = min(dimensions, key=lambda item: item["score"])

    strengths = [f"{item['label']}：{item['comment']}" for item in dimensions if item["score"] >= 16]
    if not strengths:
        strengths = [f"{best['label']}：{best['comment']}"]

    priority_actions: List[str] = []
    for item in sorted(dimensions, key=lambda current: current["score"]):
        for suggestion in item["suggestions"]:
            if suggestion not in priority_actions:
                priority_actions.append(suggestion)
            if len(priority_actions) >= 4:
                break
        if len(priority_actions) >= 4:
            break
    for suggestion in _consistency_priority_actions(consistency_signals):
        if suggestion not in priority_actions:
            priority_actions.insert(0, suggestion)
        if len(priority_actions) > 4:
            priority_actions = priority_actions[:4]

    fingerprint = (
        f"{SCENE_RUBRIC_VERSION}:{chapter_id}:{start_paragraph}:{end_paragraph}:{stable_hash(scene_text, size=16)}"
    )
    contract_alignment = _evaluate_scene_contract_alignment(
        state.get("project", {}),
        dimension_map,
        text_metrics,
        scene_text,
        story_constraint_signals,
    )
    _apply_consistency_signals_to_alignment(contract_alignment, consistency_signals)
    return {
        "reviewId": f"scene-review-{stable_hash(fingerprint)}",
        "fingerprint": fingerprint,
        "rubricVersion": SCENE_RUBRIC_VERSION,
        "generatedAt": now_iso(),
        "chapterId": chapter_id,
        "chapterTitle": chapter_title(state["outline"], chapter_id),
        "sceneRange": {
            "startParagraph": start_paragraph,
            "endParagraph": end_paragraph,
            "paragraphCount": len(selected_clean),
            "totalChapterParagraphs": total_paragraphs,
        },
        "summary": _build_scene_summary(total_score, best["label"], weakest["label"]),
        "rating": _rating_label(total_score),
        "scores": {
            "total": total_score,
            "maxScore": MAX_DIMENSION_SCORE * len(dimensions),
            "dimensions": dimensions,
        },
        "strengths": strengths,
        "priorityActions": priority_actions,
        "textMetrics": text_metrics,
        "analysisSignals": analysis_signals,
        "styleAnalysis": style_report,
        "projectContext": {
            "genre": state.get("project", {}).get("genre", ""),
            "positioning": state.get("project", {}).get("positioning", {}),
            "storyContract": state.get("project", {}).get("storyContract", {}),
            "emotionalContract": state.get("project", {}).get("emotionalContract", {}),
            "storyTemplate": state.get("project", {}).get("storyTemplate", {}),
            "commercialPositioning": state.get("project", {}).get("commercialPositioning", {}),
        },
        "storyConstraintSignals": story_constraint_signals,
        "consistencySignals": consistency_signals,
        "contractAlignment": contract_alignment,
        "commercialAlignment": _evaluate_commercial_scene_alignment(
            state.get("project", {}),
            dimension_map,
            text_metrics,
            scene_text,
            selected_clean,
            end_paragraph == total_paragraphs,
        ),
        "rubric": SCENE_REVIEW_RUBRIC,
    }


def list_scene_candidates(chapter_text: str) -> List[Dict[str, Any]]:
    paragraphs = paragraphs_from_text(chapter_text)
    if not paragraphs:
        return []

    ranges: List[tuple[int, int, str]] = []
    start = 1
    previous_reason = "chapter-start"
    for index in range(2, len(paragraphs) + 1):
        paragraph = strip_entity_tags(paragraphs[index - 1])
        current_length = index - start
        break_reason = _scene_break_reason(paragraph, current_length)
        if break_reason:
            ranges.append((start, index - 1, previous_reason))
            start = index
            previous_reason = break_reason
    ranges.append((start, len(paragraphs), previous_reason))

    candidates: List[Dict[str, Any]] = []
    for scene_index, (scene_start, scene_end, reason) in enumerate(ranges, start=1):
        selected = [strip_entity_tags(item) for item in paragraphs[scene_start - 1 : scene_end]]
        preview = selected[0][:60] if selected else ""
        candidates.append(
            {
                "sceneIndex": scene_index,
                "startParagraph": scene_start,
                "endParagraph": scene_end,
                "paragraphCount": scene_end - scene_start + 1,
                "breakReason": reason,
                "preview": preview,
            }
        )
    return candidates


def resolve_scene_candidates(chapter_entry: Dict[str, Any], chapter_text: str) -> List[Dict[str, Any]]:
    explicit_plans = chapter_entry.get("scenePlans", []) if isinstance(chapter_entry, dict) else []
    if explicit_plans:
        candidates: List[Dict[str, Any]] = []
        for scene_index, plan in enumerate(explicit_plans, start=1):
            start_paragraph = plan.get("startParagraph")
            end_paragraph = plan.get("endParagraph")
            if not isinstance(start_paragraph, int) or not isinstance(end_paragraph, int):
                continue
            candidates.append(
                {
                    "sceneIndex": scene_index,
                    "startParagraph": start_paragraph,
                    "endParagraph": end_paragraph,
                    "paragraphCount": end_paragraph - start_paragraph + 1,
                    "breakReason": "explicit-scene-plan",
                    "preview": plan.get("title") or plan.get("summary", ""),
                    "title": plan.get("title", ""),
                    "summary": plan.get("summary", ""),
                    "scenePlanId": plan.get("id", ""),
                    "source": "explicit",
                }
            )
        if candidates:
            return candidates

    heuristic = list_scene_candidates(chapter_text)
    for item in heuristic:
        item["source"] = "heuristic"
    return heuristic


def detect_scene_plans(chapter_id: str, chapter_text: str) -> List[Dict[str, Any]]:
    scene_plans: List[Dict[str, Any]] = []
    for scene_index, candidate in enumerate(list_scene_candidates(chapter_text), start=1):
        start_paragraph = candidate["startParagraph"]
        end_paragraph = candidate["endParagraph"]
        preview = candidate.get("preview", "").strip()
        scene_plans.append(
            {
                "id": f"scene-{stable_hash(f'{chapter_id}:{start_paragraph}:{end_paragraph}', size=10)}",
                "title": _detected_scene_title(scene_index, preview),
                "summary": preview,
                "startParagraph": start_paragraph,
                "endParagraph": end_paragraph,
                "source": "heuristic-detect",
                "detectionMethod": "scene-candidate-v1",
                "breakReason": candidate.get("breakReason", ""),
            }
        )
    return scene_plans


def _detected_scene_title(scene_index: int, preview: str) -> str:
    normalized = re.sub(r"\s+", " ", preview).strip().strip("，。！？,.?、；;:：")
    if len(normalized) > 18:
        normalized = normalized[:18].rstrip("，。！？,.?、；;:：")
    if normalized:
        return f"场景{scene_index:02d} {normalized}"
    return f"场景{scene_index:02d}"


def _score_plot_momentum(
    word_count: int,
    paragraphs: List[str],
    snapshot_candidates: List[Dict[str, Any]],
    relation_candidates: List[Dict[str, Any]],
    clean_text: str,
) -> Dict[str, Any]:
    connector_hits = _count_keyword_hits(clean_text, PLOT_CONNECTORS)
    progression_signals = len(snapshot_candidates) + len(relation_candidates)
    score = 4
    if word_count >= 220:
        score += 4
    elif word_count >= 120:
        score += 3
    elif word_count >= 60:
        score += 2

    if len(paragraphs) >= 3:
        score += 3
    elif len(paragraphs) >= 2:
        score += 2

    if progression_signals >= 3:
        score += 7
    elif progression_signals >= 1:
        score += 5

    if connector_hits >= 3:
        score += 2
    elif connector_hits >= 1:
        score += 1

    suggestions: List[str] = []
    if progression_signals == 0:
        suggestions.append("补一个明确的状态变化、关系变化或决定性动作，让章节前后产生落差。")
    if word_count < 120:
        suggestions.append("当前章节偏短，建议补足转折或收束段，避免只像一个切片。")
    if len(paragraphs) < 2:
        suggestions.append("把起势、推进、落点拆成至少两段，读者会更容易感到推进。")

    comment = "这一章能看到明确推进。" if progression_signals else "这一章更像铺垫，推进信号偏弱。"
    signals = [
        f"状态/关系推进信号 {progression_signals} 处",
        f"段落 {len(paragraphs)} 段",
        f"转折连接词 {connector_hits} 处",
    ]
    return _dimension_result("plotMomentum", "情节推进", score, comment, signals, suggestions)


def _score_character_pressure(
    active_entities: List[Dict[str, Any]],
    mention_names: List[str],
    snapshot_candidates: List[Dict[str, Any]],
    clean_text: str,
) -> Dict[str, Any]:
    active_count = len(active_entities) if active_entities else len(mention_names)
    dominant_mentions = max((item.get("mentionCount", 0) for item in active_entities), default=0)
    pressure_hits = _count_keyword_hits(clean_text, PRESSURE_KEYWORDS)
    score = 4

    if active_count >= 3:
        score += 5
    elif active_count >= 1:
        score += 3

    if dominant_mentions >= 3:
        score += 3
    elif dominant_mentions >= 1:
        score += 2

    if len(snapshot_candidates) >= 2:
        score += 6
    elif len(snapshot_candidates) >= 1:
        score += 4

    if pressure_hits >= 3:
        score += 2
    elif pressure_hits >= 1:
        score += 1

    suggestions: List[str] = []
    if not snapshot_candidates:
        suggestions.append("补一处人物状态变化或代价反馈，让角色不是只在场而是真的被事件推动。")
    if active_count <= 1:
        suggestions.append("给核心角色一个更具体的选择、犹豫或立场变化，增强人物存在感。")

    comment = "人物承压和状态变化可感知。" if snapshot_candidates else "人物出场了，但被逼到变化的力度还不够。"
    signals = [
        f"活跃角色 {active_count} 个",
        f"状态候选 {len(snapshot_candidates)} 个",
        f"心理/压力词 {pressure_hits} 个",
    ]
    return _dimension_result("characterPressure", "人物压力", score, comment, signals, suggestions)


def _score_conflict_tension(relation_candidates: List[Dict[str, Any]], clean_text: str) -> Dict[str, Any]:
    high_risk_count = sum(1 for item in relation_candidates if item.get("severity") == "high-risk")
    tension_hits = _count_keyword_hits(clean_text, TENSION_KEYWORDS)
    punctuation_hits = len(re.findall(r"[？！?!]", clean_text))
    score = 3

    if high_risk_count >= 1:
        score += 6
    elif relation_candidates:
        score += 4

    if tension_hits >= 3:
        score += 6
    elif tension_hits >= 1:
        score += 4

    if punctuation_hits >= 3:
        score += 3
    elif punctuation_hits >= 1:
        score += 2

    if relation_candidates or tension_hits:
        score += 2

    suggestions: List[str] = []
    if not relation_candidates and tension_hits == 0:
        suggestions.append("补一个明确阻力：对手、风险、时间压力或信息缺口，避免章节太平。")
    if punctuation_hits == 0:
        suggestions.append("考虑留下一个未解答的问题或悬念钩子，提高章末牵引力。")

    comment = "文本有明确阻力和悬念。" if (relation_candidates or tension_hits) else "冲突张力偏平，读者的追读理由还不够强。"
    signals = [
        f"高风险关系变化 {high_risk_count} 处",
        f"张力关键词 {tension_hits} 个",
        f"疑问/感叹标记 {punctuation_hits} 个",
    ]
    return _dimension_result("conflictTension", "冲突张力", score, comment, signals, suggestions)


def _score_scene_clarity(paragraphs: List[str], scene_entities: List[str], clean_text: str) -> Dict[str, Any]:
    setting_hits = _count_keyword_hits(clean_text, SETTING_KEYWORDS)
    opening = paragraphs[0] if paragraphs else clean_text[:80]
    opening_has_anchor = _count_keyword_hits(opening, SETTING_KEYWORDS) > 0
    score = 5

    if setting_hits >= 3:
        score += 6
    elif setting_hits >= 1:
        score += 4

    if len(scene_entities) >= 2:
        score += 4
    elif len(scene_entities) >= 1:
        score += 2

    if len(paragraphs) >= 2:
        score += 3

    if opening_has_anchor:
        score += 2

    suggestions: List[str] = []
    if setting_hits == 0:
        suggestions.append("在开头补一个时间、地点或环境锚点，减少读者找镜头的成本。")
    if len(scene_entities) <= 1:
        suggestions.append("明确场景里的关键角色和关系焦点，避免读者只看到动作没看到局面。")

    comment = "场景锚点比较清楚。" if (setting_hits or opening_has_anchor) else "场景信息偏轻，读者需要自己补镜头。"
    signals = [
        f"环境锚点 {setting_hits} 个",
        f"场景焦点角色 {len(scene_entities)} 个",
        f"开头是否带锚点 {'是' if opening_has_anchor else '否'}",
    ]
    return _dimension_result("sceneClarity", "场景清晰度", score, comment, signals, suggestions)


def _score_prose_control(paragraphs: List[str], clean_text: str, style_report: Dict[str, Any]) -> Dict[str, Any]:
    average_length = _average_length(paragraphs)
    long_paragraphs = sum(1 for item in paragraphs if len(item) > 180)
    short_paragraphs = sum(1 for item in paragraphs if len(item) < 20)
    dialogue_paragraphs = _dialogue_paragraphs(paragraphs)
    repeated_punctuation = len(re.findall(r"([!！?？。])\1{2,}", clean_text))
    style_analysis = style_report.get("styleAnalysis", {})
    style_deduction = min(6, int(style_analysis.get("totalDeduction", 0)))
    score = 11

    if 35 <= average_length <= 150:
        score += 4
    elif 20 <= average_length <= 200:
        score += 2

    if long_paragraphs == 0:
        score += 2
    elif long_paragraphs == 1:
        score += 1
    else:
        score -= 2

    if repeated_punctuation == 0:
        score += 2
    else:
        score -= 2

    if dialogue_paragraphs > 0:
        score += 1
    if short_paragraphs <= max(1, len(paragraphs) // 3):
        score += 1
    score -= style_deduction

    suggestions: List[str] = []
    if long_paragraphs >= 2:
        suggestions.append("拆分过长段落，把动作、信息和情绪分开承载，节奏会更稳。")
    if repeated_punctuation > 0:
        suggestions.append("减少连续感叹或问号，尽量用动作和细节替代强调符号。")
    if average_length < 20:
        suggestions.append("段落普遍太短，建议增加承接句，避免阅读节奏过碎。")
    for suggestion in style_report.get("constraints", [])[:2]:
        if suggestion not in suggestions:
            suggestions.append(suggestion)

    if style_deduction > 0:
        comment = f"基础节奏可读，但 AI 风格信号额外扣了 {style_deduction} 分。"
    else:
        comment = "段落和强调基本受控。" if repeated_punctuation == 0 and long_paragraphs <= 1 else "表达有亮点，但节奏和强调还可以再收。"
    signals = [
        f"平均段长 {average_length}",
        f"长段落 {long_paragraphs} 段",
        f"对话段 {dialogue_paragraphs} 段",
        f"风格额外扣分 {style_deduction}",
    ]
    return _dimension_result("proseControl", "表达控制", score, comment, signals, suggestions)


def _dimension_result(
    dimension_id: str,
    label: str,
    score: int,
    comment: str,
    signals: List[str],
    suggestions: List[str],
) -> Dict[str, Any]:
    return {
        "id": dimension_id,
        "label": label,
        "score": _clamp(score),
        "maxScore": MAX_DIMENSION_SCORE,
        "comment": comment,
        "signals": signals,
        "suggestions": suggestions[:3],
    }


def _evaluate_contract_alignment(
    project: Dict[str, Any],
    dimension_map: Dict[str, Dict[str, Any]],
    text_metrics: Dict[str, Any],
    chapter_text: str = "",
    story_constraint_signals: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    positioning = project.get("positioning", {})
    story_contract = project.get("storyContract", {})
    emotional_contract = project.get("emotionalContract", {})
    story_template = project.get("storyTemplate", {})
    primary_genre = normalize_primary_genre(positioning.get("primaryGenre", ""))
    pace_contract = story_contract.get("paceContract", "")
    core_promises = [item for item in story_contract.get("corePromises", []) if item]
    story_constraint_signals = story_constraint_signals or {}

    matched: List[str] = []
    risks: List[str] = []
    notes: List[str] = []

    plot_score = dimension_map["plotMomentum"]["score"]
    character_score = dimension_map["characterPressure"]["score"]
    conflict_score = dimension_map["conflictTension"]["score"]
    scene_score = dimension_map["sceneClarity"]["score"]
    emotional_floor = [item for item in emotional_contract.get("chapterEmotionFloor", []) if item]
    core_emotions = [item for item in emotional_contract.get("coreEmotions", []) if item]
    forbidden_emotions = [item for item in emotional_contract.get("forbiddenEmotions", []) if item]
    reveal_preference = emotional_contract.get("revealPreference", {})
    reveal_mode = reveal_preference.get("defaultMode", "")
    allow_direct_explain_at_climax = bool(reveal_preference.get("allowDirectExplainAtClimax", False))
    review_focus = [item for item in story_template.get("reviewFocus", []) if item]
    due_foreshadows = story_constraint_signals.get("dueForeshadows", [])
    tracked_entities = story_constraint_signals.get("trackedEntities", [])
    world_rules = story_constraint_signals.get("worldRules", [])
    payoff_hits = _count_keyword_hits(chapter_text, FORESHADOWING_PAYOFF_KEYWORDS)
    world_rule_labels = _signal_values(world_rules, "label")
    due_foreshadow_titles = _signal_values(due_foreshadows, "title")
    due_reader_modes = _signal_values(due_foreshadows, "readerRealizationMode")
    tracked_names = _signal_values(tracked_entities, "name")
    tracked_change_example = _tracked_change_example(tracked_entities)

    if primary_genre in {"mystery", "thriller"}:
        if conflict_score >= 16:
            matched.append("主类型要求的悬念/张力信号已建立。")
        else:
            risks.append("当前主类型偏悬疑/惊悚，但章节张力还不够稳定。")
    elif primary_genre == "romance":
        if character_score >= 16:
            matched.append("主类型偏言情，当前人物压力与关系牵引是成立的。")
        else:
            risks.append("当前主类型偏言情，但人物关系拉扯还不够突出。")
    elif primary_genre in {"fantasy", "science-fiction"}:
        if scene_score >= 16:
            matched.append("主类型偏设定型，场景与世界锚点基本清楚。")
        else:
            risks.append("当前主类型偏设定型，但场景/设定锚点偏弱。")
    elif primary_genre == "literary":
        if dimension_map["proseControl"]["score"] >= 17:
            matched.append("主类型偏文学向，当前表达控制已形成支撑。")
        else:
            risks.append("当前主类型偏文学向，但表达控制尚未明显高于通用水位。")

    if pace_contract == "快节奏":
        if plot_score >= 16 and conflict_score >= 14:
            matched.append("节奏承诺为快节奏，本章推进和牵引基本对位。")
        else:
            risks.append("声明为快节奏，但本章推进或牵引还不够强。")
    elif pace_contract == "慢热":
        if character_score >= 14 and scene_score >= 14 and text_metrics.get("wordCount", 0) >= 120:
            matched.append("节奏承诺为慢热，本章的人物/氛围积累基本成立。")
        else:
            risks.append("声明为慢热，但当前章节的人物或场景积累仍偏薄。")
    elif pace_contract:
        notes.append(f"已记录节奏承诺：{pace_contract}。")

    for promise in core_promises[:3]:
        if any(keyword in promise for keyword in ("升级", "成长", "逆袭", "修炼", "进阶")):
            _append_alignment(
                promise,
                plot_score >= 16 or character_score >= 16,
                matched,
                risks,
                "成长/升级信号已被章节推进支撑。",
                "成长/升级承诺在本章里的兑现信号偏弱。",
            )
        elif any(keyword in promise for keyword in ("悬疑", "谜题", "真相", "反转", "诡计")):
            _append_alignment(
                promise,
                conflict_score >= 16,
                matched,
                risks,
                "悬疑/反转承诺已得到张力支撑。",
                "悬疑/反转承诺在本章里的张力兑现偏弱。",
            )
        elif any(keyword in promise for keyword in ("爱情", "恋爱", "情感", "关系", "拉扯", "CP")):
            _append_alignment(
                promise,
                character_score >= 16,
                matched,
                risks,
                "情感/关系承诺已得到人物压力支撑。",
                "情感/关系承诺在本章里的人物拉扯偏弱。",
            )
        elif any(keyword in promise for keyword in ("世界观", "设定", "探索", "地图", "冒险")):
            _append_alignment(
                promise,
                scene_score >= 16,
                matched,
                risks,
                "设定/探索承诺已得到场景锚点支撑。",
                "设定/探索承诺在本章里的场景锚点偏弱。",
            )
        elif any(keyword in promise for keyword in ("爽", "反击", "打脸", "兑现")):
            _append_alignment(
                promise,
                plot_score >= 16 and conflict_score >= 16,
                matched,
                risks,
                "兑现/爽点承诺已得到推进和张力共同支撑。",
                "兑现/爽点承诺在本章里的爆点还不够明显。",
            )
        else:
            notes.append(f"核心承诺“{promise}”目前仅记录，尚未接入自动判定。")

    if core_emotions:
        if character_score >= 15 or conflict_score >= 15 or plot_score >= 15:
            matched.append(f"情绪契约已被章节压力/推进承接，核心目标包括：{', '.join(core_emotions[:2])}。")
        else:
            risks.append("项目已声明情绪契约的核心情绪体验，但本章的压力、冲突或推进还不足以稳定承接。")

    if emotional_floor:
        if max(plot_score, character_score, conflict_score) >= 14:
            matched.append("情绪契约中的章节情绪底线基本成立，本章不只是信息搬运。")
        else:
            risks.append("已声明情绪契约的章节情绪底线，但本章仍偏信息说明，情绪推进不足。")

    if any("空转" in item or "设定" in item for item in forbidden_emotions):
        if plot_score < 14 and character_score < 14 and conflict_score < 14 and scene_score >= 15:
            risks.append("情绪契约禁止“空转讲设定”，但本章更像说明而不是情绪/情节推进。")
        else:
            notes.append("已检查“避免空转讲设定”约束。")

    if reveal_mode in {"partial-inference", "infer-before-confirm"}:
        if due_foreshadows and (payoff_hits >= 1 or conflict_score >= 15 or scene_score >= 15):
            matched.append("揭露偏好强调“让读者自行推断”，当前章已经留下可供拼合的回收信号。")
        elif due_foreshadows:
            risks.append("揭露偏好强调“让读者自行推断”，但当前章仍缺少足够清晰的拼图信号。")
        else:
            notes.append("已记录揭露偏好为“让读者自行推断”。")
    elif reveal_mode:
        notes.append(f"已记录揭露偏好：{reveal_mode}。")
    if allow_direct_explain_at_climax:
        notes.append("已记录“高潮点允许直接解释”的揭露例外。")

    if due_foreshadows:
        if payoff_hits >= 1 or plot_score >= 15 or conflict_score >= 15:
            focus_suffix = f"，例如“{due_foreshadow_titles[0]}”" if due_foreshadow_titles else ""
            matched.append(f"当前章有 {len(due_foreshadows)} 条伏笔进入回收窗口{focus_suffix}，文本已出现一定兑现信号。")
        else:
            focus_suffix = f"，例如“{due_foreshadow_titles[0]}”" if due_foreshadow_titles else ""
            risks.append(f"当前章有 {len(due_foreshadows)} 条伏笔进入回收窗口{focus_suffix}，但兑现/推进信号仍偏弱。")

    if tracked_entities:
        if character_score >= 14 or len(tracked_entities) >= 2:
            example_suffix = f"，例如 {tracked_change_example}" if tracked_change_example else ""
            matched.append(f"当前章已承接 {len(tracked_entities)} 个受追踪角色的状态或变化压力{example_suffix}。")
        else:
            example_suffix = f"，例如 {tracked_change_example}" if tracked_change_example else ""
            risks.append(f"项目存在动态角色状态追踪，但本章对这些状态变化的承接还不够明显{example_suffix}。")

    if world_rules:
        label_suffix = f"，例如“{world_rule_labels[0]}”" if world_rule_labels else ""
        notes.append(f"项目当前存在 {len(world_rules)} 条世界规则约束{label_suffix}，chapter review 已纳入提示。")

    if _focus_enabled(review_focus, ("世界规则", "规则兑现")):
        if world_rules and (scene_score >= 15 or conflict_score >= 15 or plot_score >= 15):
            matched.append(f"模板关注点要求世界规则兑现，当前章已开始承接“{_join_signal_values(world_rule_labels)}”。")
        elif world_rules:
            risks.append("模板关注点要求世界规则兑现，但本章对规则代价/边界的承接仍偏弱。")
        else:
            notes.append("模板关注点要求世界规则兑现，但当前项目未提供可消费的 worldRules。")

    if _focus_enabled(review_focus, ("伏笔", "回收", "暗线", "揭晓")):
        if due_foreshadows and (payoff_hits >= 1 or plot_score >= 15 or conflict_score >= 15):
            matched.append(f"模板关注点要求伏笔回收，当前章已对“{_join_signal_values(due_foreshadow_titles)}”给出拼图或兑现信号。")
        elif due_foreshadows:
            risks.append("模板关注点要求伏笔回收，但当前章对临近窗口伏笔的承接仍偏弱。")
        else:
            notes.append("模板关注点包含伏笔/暗线回收，但当前章没有进入窗口的伏笔。")

    if _focus_enabled(review_focus, ("角色状态", "状态演化", "成长余波", "角色变化")):
        if tracked_entities and (character_score >= 14 or conflict_score >= 14):
            matched.append(f"模板关注点要求角色状态演化，当前章已承接“{_join_signal_values(tracked_names)}”的变化余波。")
        elif tracked_entities:
            risks.append("模板关注点要求角色状态演化，但当前章对角色变化余波的承接仍偏弱。")
        else:
            notes.append("模板关注点包含角色状态演化，但当前项目没有可消费的角色状态追踪。")

    if due_reader_modes and any(mode in {"infer-before-confirm", "partial-inference"} for mode in due_reader_modes):
        notes.append(f"临近窗口伏笔的读者认知模式偏向“先推断后确认”，例如“{due_foreshadow_titles[0]}”。")

    if not primary_genre and not pace_contract and not core_promises:
        status = "missing-contract"
    elif risks and matched:
        status = "mixed"
    elif risks:
        status = "at-risk"
    else:
        status = "aligned"

    return {
        "status": status,
        "matched": matched[:5],
        "risks": risks[:5],
        "notes": notes[:5],
    }


def _evaluate_scene_contract_alignment(
    project: Dict[str, Any],
    dimension_map: Dict[str, Dict[str, Any]],
    text_metrics: Dict[str, Any],
    scene_text: str = "",
    story_constraint_signals: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    positioning = project.get("positioning", {})
    story_contract = project.get("storyContract", {})
    emotional_contract = project.get("emotionalContract", {})
    story_template = project.get("storyTemplate", {})
    primary_genre = normalize_primary_genre(positioning.get("primaryGenre", ""))
    pace_contract = story_contract.get("paceContract", "")
    core_promises = [item for item in story_contract.get("corePromises", []) if item]
    story_constraint_signals = story_constraint_signals or {}

    matched: List[str] = []
    risks: List[str] = []
    notes: List[str] = []

    scene_function = dimension_map["sceneFunction"]["score"]
    continuity = dimension_map["continuity"]["score"]
    logic_score = dimension_map["logic"]["score"]
    foreshadowing = dimension_map["foreshadowing"]["score"]
    scene_clarity = dimension_map["sceneClarity"]["score"]
    core_emotions = [item for item in emotional_contract.get("coreEmotions", []) if item]
    emotional_floor = [item for item in emotional_contract.get("chapterEmotionFloor", []) if item]
    forbidden_emotions = [item for item in emotional_contract.get("forbiddenEmotions", []) if item]
    reveal_preference = emotional_contract.get("revealPreference", {})
    reveal_mode = reveal_preference.get("defaultMode", "")
    allow_direct_explain_at_climax = bool(reveal_preference.get("allowDirectExplainAtClimax", False))
    review_focus = [item for item in story_template.get("reviewFocus", []) if item]
    due_foreshadows = story_constraint_signals.get("dueForeshadows", [])
    tracked_entities = story_constraint_signals.get("trackedEntities", [])
    world_rules = story_constraint_signals.get("worldRules", [])
    payoff_hits = _count_keyword_hits(scene_text, FORESHADOWING_PAYOFF_KEYWORDS)
    pressure_hits = _count_keyword_hits(scene_text, PRESSURE_KEYWORDS)
    world_rule_labels = _signal_values(world_rules, "label")
    due_foreshadow_titles = _signal_values(due_foreshadows, "title")
    due_reader_modes = _signal_values(due_foreshadows, "readerRealizationMode")
    tracked_names = _signal_values(tracked_entities, "name")
    tracked_change_example = _tracked_change_example(tracked_entities)

    if primary_genre in {"mystery", "thriller"}:
        if foreshadowing >= 15:
            matched.append("主类型偏悬疑/惊悚，这一幕已维持住悬念或后续钩子。")
        else:
            risks.append("主类型偏悬疑/惊悚，但这一幕的悬念维持还不够强。")
    elif primary_genre == "romance":
        if continuity >= 14 and logic_score >= 14:
            matched.append("主类型偏言情，这一幕的关系承接和人物反应基本成立。")
        else:
            risks.append("主类型偏言情，但这一幕的人物关系承接还不够显性。")
    elif primary_genre in {"fantasy", "science-fiction"}:
        if scene_clarity >= 15:
            matched.append("主类型偏设定型，这一幕的镜头和设定锚点基本清楚。")
        else:
            risks.append("主类型偏设定型，但这一幕的场景/设定锚点偏弱。")
    elif primary_genre == "literary":
        if logic_score >= 15 and continuity >= 14:
            matched.append("主类型偏文学向，这一幕的内在线索和承接基本稳住了。")
        else:
            risks.append("主类型偏文学向，但这一幕的内在线索还不够凝练。")

    if pace_contract == "快节奏":
        if scene_function >= 14 and foreshadowing >= 14:
            matched.append("节奏承诺为快节奏，这一幕的推进和钩子基本对位。")
        else:
            risks.append("声明为快节奏，但这一幕的推进或钩子还不够强。")
    elif pace_contract == "慢热":
        if continuity >= 14 and scene_clarity >= 14 and text_metrics.get("wordCount", 0) >= 80:
            matched.append("节奏承诺为慢热，这一幕的承接和铺垫基本成立。")
        else:
            risks.append("声明为慢热，但这一幕的承接或铺垫仍偏薄。")
    elif pace_contract:
        notes.append(f"已记录节奏承诺：{pace_contract}。")

    for promise in core_promises[:3]:
        if any(keyword in promise for keyword in ("升级", "成长", "逆袭", "修炼", "进阶")):
            _append_alignment(
                promise,
                scene_function >= 14 or logic_score >= 14,
                matched,
                risks,
                "成长/升级信号已被这一幕的推进支撑。",
                "成长/升级承诺在这一幕里的推进信号偏弱。",
            )
        elif any(keyword in promise for keyword in ("悬疑", "谜题", "真相", "反转", "诡计")):
            _append_alignment(
                promise,
                foreshadowing >= 15,
                matched,
                risks,
                "悬疑/反转承诺已被这一幕的伏笔与回收支撑。",
                "悬疑/反转承诺在这一幕里的钩子偏弱。",
            )
        elif any(keyword in promise for keyword in ("爱情", "恋爱", "情感", "关系", "拉扯", "CP")):
            _append_alignment(
                promise,
                continuity >= 14 or logic_score >= 14,
                matched,
                risks,
                "情感/关系承诺已被这一幕的承接与反应支撑。",
                "情感/关系承诺在这一幕里的承接还不够强。",
            )
        elif any(keyword in promise for keyword in ("世界观", "设定", "探索", "地图", "冒险")):
            _append_alignment(
                promise,
                scene_clarity >= 15,
                matched,
                risks,
                "设定/探索承诺已被这一幕的场景锚点支撑。",
                "设定/探索承诺在这一幕里的场景锚点偏弱。",
            )
        elif any(keyword in promise for keyword in ("爽", "反击", "打脸", "兑现")):
            _append_alignment(
                promise,
                scene_function >= 15 and foreshadowing >= 14,
                matched,
                risks,
                "兑现/爽点承诺已被这一幕的推进和钩子支撑。",
                "兑现/爽点承诺在这一幕里的爆点还不够明显。",
            )
        else:
            notes.append(f"核心承诺“{promise}”目前仅记录，尚未接入一幕级自动判定。")

    if core_emotions:
        if pressure_hits >= 1 or scene_function >= 14 or foreshadowing >= 14:
            matched.append(f"这一幕已承接情绪契约的核心情绪方向：{', '.join(core_emotions[:2])}。")
        else:
            risks.append("项目已声明情绪契约的核心情绪体验，但这一幕的情绪推进仍不够明确。")

    if emotional_floor:
        if max(scene_function, foreshadowing, logic_score) >= 14:
            matched.append("这一幕满足情绪契约的章节情绪底线，没有完全滑向纯说明。")
        else:
            risks.append("已声明情绪契约的章节情绪底线，但这一幕更像信息补丁，情绪推进偏弱。")

    if any("空转" in item or "设定" in item for item in forbidden_emotions):
        if scene_function < 13 and foreshadowing < 13 and scene_clarity >= 15:
            risks.append("情绪契约禁止“空转讲设定”，但这一幕偏说明性场景。")

    if reveal_mode in {"partial-inference", "infer-before-confirm"}:
        if due_foreshadows and (payoff_hits >= 1 or foreshadowing >= 14 or logic_score >= 14):
            matched.append("揭露偏好强调“让读者自行推断”，这一幕已留下可供读者拼合的信号。")
        elif due_foreshadows:
            risks.append("揭露偏好强调“让读者自行推断”，但这一幕的拼图信号还不够清楚。")
        else:
            notes.append("已记录揭露偏好为“让读者自行推断”。")
    elif reveal_mode:
        notes.append(f"已记录揭露偏好：{reveal_mode}。")
    if allow_direct_explain_at_climax:
        notes.append("已记录“高潮点允许直接解释”的揭露例外。")

    if due_foreshadows:
        if foreshadowing >= 14 or payoff_hits >= 1:
            focus_suffix = f"，例如“{due_foreshadow_titles[0]}”" if due_foreshadow_titles else ""
            matched.append(f"这一幕对应了 {len(due_foreshadows)} 条临近回收的伏笔{focus_suffix}。")
        else:
            focus_suffix = f"，例如“{due_foreshadow_titles[0]}”" if due_foreshadow_titles else ""
            risks.append(f"这一幕所在章节已有 {len(due_foreshadows)} 条伏笔进入窗口{focus_suffix}，但片段里的回收信号偏弱。")

    if tracked_entities:
        if logic_score >= 14 or continuity >= 14:
            example_suffix = f"，例如 {tracked_change_example}" if tracked_change_example else ""
            matched.append(f"这一幕对受追踪角色状态的承接基本成立{example_suffix}。")
        else:
            example_suffix = f"，例如 {tracked_change_example}" if tracked_change_example else ""
            risks.append(f"项目存在角色状态追踪，但这一幕对状态余波的承接还不够清楚{example_suffix}。")

    if world_rules:
        label_suffix = f"，例如“{world_rule_labels[0]}”" if world_rule_labels else ""
        notes.append(f"项目当前存在 {len(world_rules)} 条世界规则约束{label_suffix}，scene review 已纳入提示。")

    if _focus_enabled(review_focus, ("世界规则", "规则兑现")):
        if world_rules and (scene_clarity >= 15 or logic_score >= 14 or foreshadowing >= 14):
            matched.append(f"模板关注点要求世界规则兑现，这一幕已开始承接“{_join_signal_values(world_rule_labels)}”。")
        elif world_rules:
            risks.append("模板关注点要求世界规则兑现，但这一幕对规则代价/边界的承接仍偏弱。")
        else:
            notes.append("模板关注点要求世界规则兑现，但当前项目未提供可消费的 worldRules。")

    if _focus_enabled(review_focus, ("伏笔", "回收", "暗线", "揭晓")):
        if due_foreshadows and (foreshadowing >= 14 or payoff_hits >= 1):
            matched.append(f"模板关注点要求伏笔回收，这一幕已对“{_join_signal_values(due_foreshadow_titles)}”给出拼图或兑现信号。")
        elif due_foreshadows:
            risks.append("模板关注点要求伏笔回收，但这一幕对临近窗口伏笔的承接仍偏弱。")
        else:
            notes.append("模板关注点包含伏笔/暗线回收，但这一幕所在章节没有进入窗口的伏笔。")

    if _focus_enabled(review_focus, ("角色状态", "状态演化", "成长余波", "角色变化")):
        if tracked_entities and (logic_score >= 14 or continuity >= 14 or scene_function >= 14):
            matched.append(f"模板关注点要求角色状态演化，这一幕已承接“{_join_signal_values(tracked_names)}”的变化余波。")
        elif tracked_entities:
            risks.append("模板关注点要求角色状态演化，但这一幕对角色变化余波的承接仍偏弱。")
        else:
            notes.append("模板关注点包含角色状态演化，但当前项目没有可消费的角色状态追踪。")

    if due_reader_modes and any(mode in {"infer-before-confirm", "partial-inference"} for mode in due_reader_modes):
        notes.append(f"临近窗口伏笔的读者认知模式偏向“先推断后确认”，例如“{due_foreshadow_titles[0]}”。")

    if not primary_genre and not pace_contract and not core_promises:
        status = "missing-contract"
    elif risks and matched:
        status = "mixed"
    elif risks:
        status = "at-risk"
    else:
        status = "aligned"

    return {
        "status": status,
        "matched": matched[:5],
        "risks": risks[:5],
        "notes": notes[:5],
    }


def _evaluate_commercial_chapter_alignment(
    project: Dict[str, Any],
    dimension_map: Dict[str, Dict[str, Any]],
    text_metrics: Dict[str, Any],
    chapter_text: str,
    paragraphs: List[str],
) -> Dict[str, Any]:
    commercial = project.get("commercialPositioning", {})
    target_platform = normalize_machine_label(commercial.get("targetPlatform", ""))
    hook_line = commercial.get("hookLine", "")
    hook_stack = [normalize_machine_label(item) for item in commercial.get("hookStack", []) if item]
    serialization_model = commercial.get("serializationModel", "")
    release_cadence = commercial.get("releaseCadence", "")
    chapter_word_floor = commercial.get("chapterWordFloor", 0) or 0
    chapter_word_target = commercial.get("chapterWordTarget", 0) or 0

    if not any(commercial.values()):
        return {
            "status": "not-applicable",
            "matched": [],
            "risks": [],
            "notes": [],
        }

    matched: List[str] = []
    risks: List[str] = []
    notes: List[str] = []
    word_count = text_metrics.get("wordCount", 0)
    plot_score = dimension_map["plotMomentum"]["score"]
    character_score = dimension_map["characterPressure"]["score"]
    conflict_score = dimension_map["conflictTension"]["score"]
    scene_score = dimension_map["sceneClarity"]["score"]
    hook_hits = _count_keyword_hits(chapter_text, HOOK_KEYWORDS)
    final_paragraph = paragraphs[-1] if paragraphs else ""
    final_hook_hits = _count_keyword_hits(final_paragraph, HOOK_KEYWORDS)
    cliffhanger_like = final_hook_hits > 0 or "？" in final_paragraph or "?" in final_paragraph

    if chapter_word_floor:
        if word_count >= chapter_word_floor:
            matched.append(f"章节字数达到最低交付线 {chapter_word_floor} 字。")
        else:
            risks.append(f"章节字数仅 {word_count}，低于商业交付底线 {chapter_word_floor} 字。")
    if chapter_word_target:
        if word_count >= chapter_word_target:
            matched.append(f"章节字数达到建议目标 {chapter_word_target} 字。")
        else:
            notes.append(f"章节字数 {word_count}，距建议目标 {chapter_word_target} 字仍有差距。")

    if hook_line:
        if plot_score >= 15 and (conflict_score >= 14 or cliffhanger_like):
            matched.append("商业 hook line 对应的开章承诺和章末追读牵引基本成立。")
        else:
            risks.append("已声明商业 hook line，但本章的推进或章末追读牵引还不够强。")

    for hook in hook_stack[:4]:
        if hook == "cliffhanger-end":
            _append_alignment(
                hook,
                cliffhanger_like and conflict_score >= 14,
                matched,
                risks,
                "章末追读钩子成立。",
                "章末追读钩子还不够强。",
            )
        elif hook == "unit-case-payoff":
            _append_alignment(
                hook,
                plot_score >= 16 and conflict_score >= 15,
                matched,
                risks,
                "单元案推进/兑现感已建立。",
                "单元案推进或兑现感偏弱。",
            )
        elif hook == "mainline-escalation":
            _append_alignment(
                hook,
                plot_score >= 16 and hook_hits >= 1,
                matched,
                risks,
                "主线认知抬升信号已建立。",
                "主线抬升信号不够明显。",
            )
        elif hook == "upgrade-payoff":
            _append_alignment(
                hook,
                plot_score >= 16 and character_score >= 15,
                matched,
                risks,
                "升级/兑现感已在本章落地。",
                "升级/兑现感仍偏弱。",
            )
        elif hook == "suppression-reversal":
            _append_alignment(
                hook,
                plot_score >= 15 and conflict_score >= 16,
                matched,
                risks,
                "压制到反压制的反弹感已建立。",
                "压制/反转的爆点不够明显。",
            )
        elif hook == "career-entry-hook":
            _append_alignment(
                hook,
                scene_score >= 15 and plot_score >= 14,
                matched,
                risks,
                "职业入口与世界规则的钩子成立。",
                "职业入口钩子还不够清晰。",
            )
        else:
            notes.append(f"商业 hook 栈“{hook}”目前仅记录，尚未接入自动判定。")

    if target_platform:
        notes.append(f"已记录目标平台：{target_platform}。")
    if serialization_model:
        notes.append(f"已记录连载模型：{serialization_model}。")
    if release_cadence:
        notes.append(f"已记录更新节奏：{release_cadence}。")

    if risks and matched:
        status = "mixed"
    elif risks:
        status = "at-risk"
    else:
        status = "aligned"

    return {
        "status": status,
        "matched": matched[:6],
        "risks": risks[:6],
        "notes": notes[:6],
    }


def _evaluate_commercial_scene_alignment(
    project: Dict[str, Any],
    dimension_map: Dict[str, Dict[str, Any]],
    text_metrics: Dict[str, Any],
    scene_text: str,
    paragraphs: List[str],
    is_terminal_scene: bool,
) -> Dict[str, Any]:
    commercial = project.get("commercialPositioning", {})
    hook_line = commercial.get("hookLine", "")
    hook_stack = [normalize_machine_label(item) for item in commercial.get("hookStack", []) if item]
    serialization_model = commercial.get("serializationModel", "")

    if not any(commercial.values()):
        return {
            "status": "not-applicable",
            "matched": [],
            "risks": [],
            "notes": [],
        }

    matched: List[str] = []
    risks: List[str] = []
    notes: List[str] = []
    scene_function = dimension_map["sceneFunction"]["score"]
    logic_score = dimension_map["logic"]["score"]
    foreshadowing = dimension_map["foreshadowing"]["score"]
    scene_clarity = dimension_map["sceneClarity"]["score"]
    last_paragraph = paragraphs[-1] if paragraphs else ""
    hook_hits = _count_keyword_hits(scene_text, HOOK_KEYWORDS)
    final_hook_hits = _count_keyword_hits(last_paragraph, HOOK_KEYWORDS)
    cliffhanger_like = final_hook_hits > 0 or "？" in last_paragraph or "?" in last_paragraph

    if hook_line and is_terminal_scene:
        if foreshadowing >= 14 and cliffhanger_like:
            matched.append("这一幕作为章末场景，已形成较明确的追读钩子。")
        else:
            risks.append("这一幕处于章末，但追读钩子还不够强。")
    elif hook_line:
        notes.append("项目已声明商业 hook line；当前片段不是章末场景，优先检查局部推进。")

    for hook in hook_stack[:4]:
        if hook == "cliffhanger-end":
            if is_terminal_scene:
                _append_alignment(
                    hook,
                    foreshadowing >= 14 and cliffhanger_like,
                    matched,
                    risks,
                    "章末钩子成立。",
                    "章末钩子偏弱。",
                )
            else:
                notes.append("当前片段不是章末场景，未强行判定 cliffhanger-end。")
        elif hook in {"unit-case-payoff", "mainline-escalation"}:
            _append_alignment(
                hook,
                scene_function >= 15 and (foreshadowing >= 14 or logic_score >= 14),
                matched,
                risks,
                "这一幕的功能性推进符合连载要求。",
                "这一幕的功能性推进偏弱。",
            )
        elif hook in {"upgrade-payoff", "suppression-reversal"}:
            _append_alignment(
                hook,
                scene_function >= 15 and logic_score >= 14,
                matched,
                risks,
                "这一幕具备明确的兑现/反转作用。",
                "这一幕的兑现/反转作用还不够明显。",
            )
        elif hook == "career-entry-hook":
            _append_alignment(
                hook,
                scene_clarity >= 15 and scene_function >= 14,
                matched,
                risks,
                "这一幕维持住了职业/规则入口的可读性。",
                "这一幕的职业/规则入口锚点偏弱。",
            )
        else:
            notes.append(f"商业 hook 栈“{hook}”目前仅记录，尚未接入一幕级自动判定。")

    if hook_hits == 0 and foreshadowing < 12:
        notes.append("这一幕的商业钩子信号较弱，如用作章节关键场景可考虑补一层追读问题。")
    if serialization_model:
        notes.append(f"已记录连载模型：{serialization_model}。")

    if risks and matched:
        status = "mixed"
    elif risks:
        status = "at-risk"
    else:
        status = "aligned"

    return {
        "status": status,
        "matched": matched[:6],
        "risks": risks[:6],
        "notes": notes[:6],
    }


def _filter_analysis_for_scene(
    analysis: Dict[str, Any],
    scene_paragraphs: List[str],
    mention_names: List[str],
) -> Dict[str, Any]:
    snapshot_candidates = [
        item
        for item in analysis.get("snapshotCandidates", [])
        if _evidence_matches_scene(item.get("evidence", ""), scene_paragraphs)
    ]
    relation_candidates = [
        item
        for item in analysis.get("relationCandidates", [])
        if _evidence_matches_scene(item.get("evidence", ""), scene_paragraphs)
    ]
    active_entities = [
        item for item in analysis.get("activeEntities", []) if item.get("name") in mention_names
    ]
    return {
        "activeEntities": active_entities,
        "snapshotCandidates": snapshot_candidates,
        "relationCandidates": relation_candidates,
    }


def _build_story_constraint_signals(
    state: Dict[str, Dict[str, Any]],
    chapter_id: str,
    entity_names: List[str],
) -> Dict[str, Any]:
    project = state.get("project", {})
    worldbook = state.get("worldbook", {})
    entities = state.get("entities", {}).get("entities", [])
    foreshadowing = state.get("foreshadowing", {}).get("foreshadows", [])
    tracked_name_set = {name for name in entity_names if name}

    world_rules = [
        {
            "id": item.get("id"),
            "label": item.get("label"),
            "scope": item.get("scope", ""),
        }
        for item in worldbook.get("worldRules", [])
        if isinstance(item, dict) and item.get("status") != "inactive"
    ][:5]

    due_foreshadows = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "payoffStyle": (item.get("payoffPlan", {}) or {}).get("style", ""),
            "readerRealizationMode": (item.get("payoffPlan", {}) or {}).get("readerRealizationMode", ""),
        }
        for item in foreshadowing
        if isinstance(item, dict) and _foreshadow_due_in_chapter(item, chapter_id)
    ][:5]

    tracked_entities = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        if tracked_name_set and entity.get("name") not in tracked_name_set:
            continue
        entity_state = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
        change_log = entity.get("changeLog", []) if isinstance(entity.get("changeLog"), list) else []
        if not entity_state and not change_log:
            continue
        recent_change = None
        for change in reversed(change_log):
            if change.get("chapterId") == chapter_id:
                recent_change = change
                break
        if recent_change is None and change_log:
            recent_change = change_log[-1]
        tracked_entities.append(
            {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "currentState": entity.get("currentState", ""),
                "stateTags": entity_state.get("statusTags", [])[:4] if isinstance(entity_state.get("statusTags", []), list) else [],
                "recentChange": (
                    {
                        "chapterId": recent_change.get("chapterId"),
                        "field": recent_change.get("field"),
                        "reason": recent_change.get("reason"),
                    }
                    if isinstance(recent_change, dict)
                    else None
                ),
            }
        )

    return {
        "emotionalContract": {
            "coreEmotions": [item for item in project.get("emotionalContract", {}).get("coreEmotions", []) if item][:4],
            "chapterEmotionFloor": [item for item in project.get("emotionalContract", {}).get("chapterEmotionFloor", []) if item][:3],
            "forbiddenEmotions": [item for item in project.get("emotionalContract", {}).get("forbiddenEmotions", []) if item][:3],
        },
        "worldRules": world_rules,
        "dueForeshadows": due_foreshadows,
        "trackedEntities": tracked_entities[:5],
    }


def _chapter_number(chapter_ref: str) -> int | None:
    match = re.search(r"(\d+)(?!.*\d)", chapter_ref or "")
    if not match:
        return None
    return int(match.group(1))


def _chapter_in_window(chapter_id: str, window: Dict[str, Any]) -> bool:
    if not isinstance(window, dict):
        return False
    target_chapter = window.get("targetChapter")
    if target_chapter:
        return target_chapter == chapter_id
    start = window.get("targetChapterStart")
    end = window.get("targetChapterEnd")
    if not start and not end:
        return False

    current_num = _chapter_number(chapter_id)
    start_num = _chapter_number(start) if start else None
    end_num = _chapter_number(end) if end else None
    if current_num is not None and (start_num is not None or end_num is not None):
        if start_num is not None and current_num < start_num:
            return False
        if end_num is not None and current_num > end_num:
            return False
        return True

    if start and chapter_id < start:
        return False
    if end and chapter_id > end:
        return False
    return True


def _foreshadow_due_in_chapter(item: Dict[str, Any], chapter_id: str) -> bool:
    if item.get("plannedPayoffChapter") == chapter_id:
        return True
    for payoff_point in item.get("payoffPoints", []):
        if isinstance(payoff_point, dict) and payoff_point.get("chapterId") == chapter_id:
            return True
    payoff_plan = item.get("payoffPlan", {})
    if not isinstance(payoff_plan, dict):
        return False
    return _chapter_in_window(chapter_id, payoff_plan.get("window", {}))


def _build_consistency_signals(
    style_report: Dict[str, Any],
    consistency_result: Dict[str, Any],
) -> Dict[str, Any]:
    style_analysis = style_report.get("styleAnalysis", {}) if isinstance(style_report, dict) else {}
    special_terms = style_analysis.get("specialTermRepetition", {})
    return {
        "specialTermRepetition": {
            "detected": bool(special_terms.get("detected", False)),
            "severity": special_terms.get("severity", "none"),
            "evidence": list(special_terms.get("evidence", []))[:3],
            "suggestion": special_terms.get("suggestion", ""),
        },
        "settingCandidates": list(consistency_result.get("settingCandidates", []))[:5],
        "settingConflicts": list(consistency_result.get("settingConflicts", []))[:5],
    }


def _consistency_priority_actions(consistency_signals: Dict[str, Any]) -> List[str]:
    actions: List[str] = []
    term_signal = consistency_signals.get("specialTermRepetition", {})
    if term_signal.get("detected") and term_signal.get("suggestion"):
        actions.append(term_signal["suggestion"])
    conflicts = consistency_signals.get("settingConflicts", [])
    if conflicts:
        actions.append(f"处理新设定与旧设定的冲突：{conflicts[0].get('label', '未知设定')}")
    elif consistency_signals.get("settingCandidates"):
        actions.append("确认本章产生的新设定候选是否应写入世界真相层。")
    return actions


def _apply_consistency_signals_to_alignment(
    contract_alignment: Dict[str, Any],
    consistency_signals: Dict[str, Any],
) -> None:
    matched = contract_alignment.setdefault("matched", [])
    risks = contract_alignment.setdefault("risks", [])
    notes = contract_alignment.setdefault("notes", [])

    term_signal = consistency_signals.get("specialTermRepetition", {})
    if term_signal.get("detected"):
        evidence = term_signal.get("evidence", [])
        evidence_suffix = f"，例如 {evidence[0]}" if evidence else ""
        risks.append(f"检测到高频特殊术语复用{evidence_suffix}，容易形成 AI 痕迹或阅读突兀感。")

    setting_conflicts = consistency_signals.get("settingConflicts", [])
    if setting_conflicts:
        first = setting_conflicts[0]
        risks.append(f"当前章引入的新设定可能与既有设定冲突：{first.get('issue', '设定冲突待核查')}。")

    setting_candidates = consistency_signals.get("settingCandidates", [])
    if setting_candidates and not setting_conflicts:
        labels = [item.get("label") for item in setting_candidates if item.get("label")]
        if labels:
            notes.append(f"当前章产出 {len(setting_candidates)} 条新设定候选，如“{labels[0]}”，可纳入后续世界真相层比对。")

    if not setting_conflicts and not term_signal.get("detected") and setting_candidates:
        matched.append("章节产生了可追踪的新设定候选，系统已开始承担设定入账与后续比对。")

    if risks and matched:
        contract_alignment["status"] = "mixed"
    elif risks:
        contract_alignment["status"] = "at-risk"

    contract_alignment["matched"] = matched[:5]
    contract_alignment["risks"] = risks[:5]
    contract_alignment["notes"] = notes[:5]


def _signal_values(items: List[Dict[str, Any]], key: str, limit: int = 2) -> List[str]:
    values = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    return values[:limit]


def _join_signal_values(values: List[str]) -> str:
    if not values:
        return "相关约束"
    return "、".join(values[:2])


def _tracked_change_example(tracked_entities: List[Dict[str, Any]]) -> str:
    for entity in tracked_entities:
        if not isinstance(entity, dict):
            continue
        recent_change = entity.get("recentChange")
        if not isinstance(recent_change, dict):
            continue
        reason = recent_change.get("reason")
        name = entity.get("name")
        if isinstance(reason, str) and reason and isinstance(name, str) and name:
            return f"{name}：{reason}"
    return ""


def _focus_enabled(review_focus: List[str], keywords: tuple[str, ...]) -> bool:
    return any(any(keyword in focus for keyword in keywords) for focus in review_focus)


def _scene_break_reason(paragraph: str, current_scene_length: int) -> str:
    if current_scene_length < 2:
        return ""
    opening = paragraph[:20]
    for keyword in SCENE_BREAK_KEYWORDS:
        if opening.startswith(keyword):
            return f"transition:{keyword}"
    if re.match(r"^第[一二三四五六七八九十0-9]+天", paragraph):
        return "transition:day-shift"
    return ""


def _evidence_matches_scene(evidence: str, scene_paragraphs: List[str]) -> bool:
    normalized_evidence = strip_entity_tags(evidence or "").strip()
    if not normalized_evidence:
        return False
    for paragraph in scene_paragraphs:
        normalized_paragraph = paragraph.strip()
        if not normalized_paragraph:
            continue
        if normalized_paragraph in normalized_evidence or normalized_evidence in normalized_paragraph:
            return True
    return False


def _score_scene_function(
    paragraphs: List[str],
    snapshot_candidates: List[Dict[str, Any]],
    relation_candidates: List[Dict[str, Any]],
    scene_text: str,
) -> Dict[str, Any]:
    progression_signals = (
        len(snapshot_candidates)
        + len(relation_candidates)
        + _count_keyword_hits(scene_text, SCENE_CHANGE_KEYWORDS)
    )
    score = 4
    if count_words(scene_text) >= 120:
        score += 3
    elif count_words(scene_text) >= 60:
        score += 2

    if progression_signals >= 5:
        score += 8
    elif progression_signals >= 2:
        score += 6
    elif progression_signals >= 1:
        score += 4

    if len(paragraphs) >= 2:
        score += 3

    suggestions: List[str] = []
    if progression_signals == 0:
        suggestions.append("补一个明确变化：决定、冲突升级、信息揭示或关系转向，让这一幕承担任务。")
    if len(paragraphs) == 1:
        suggestions.append("如果这一幕承担转折，建议拆成至少两段，让起势和落点更清楚。")

    comment = "这一幕承担了清楚的推进或转折功能。" if progression_signals else "这一幕更像气氛切片，功能性还不够明确。"
    signals = [
        f"推进/变化信号 {progression_signals} 处",
        f"状态候选 {len(snapshot_candidates)} 个",
        f"关系候选 {len(relation_candidates)} 个",
    ]
    return _dimension_result("sceneFunction", "场景功能", score, comment, signals, suggestions)


def _score_scene_continuity(
    raw_paragraphs: List[str],
    previous_raw: str,
    next_raw: str,
    previous_clean: str,
    next_clean: str,
) -> Dict[str, Any]:
    current_mentions = set(extract_tag_mentions("\n\n".join(raw_paragraphs)))
    previous_mentions = set(extract_tag_mentions(previous_raw))
    next_mentions = set(extract_tag_mentions(next_raw))
    continuity_hits = _count_keyword_hits(strip_entity_tags("\n\n".join(raw_paragraphs)), SCENE_CONTINUITY_KEYWORDS)
    handoff_hits = len(re.findall(r"[？?!！]", strip_entity_tags(raw_paragraphs[-1] if raw_paragraphs else "")))
    score = 5

    if not previous_raw:
        score += 4
    elif current_mentions & previous_mentions or continuity_hits >= 1:
        score += 6
    elif previous_clean:
        score += 3

    if not next_raw:
        score += 3
    elif current_mentions & next_mentions or handoff_hits >= 1:
        score += 5
    elif next_clean:
        score += 2

    if len(raw_paragraphs) >= 2:
        score += 2

    suggestions: List[str] = []
    if previous_raw and not (current_mentions & previous_mentions) and continuity_hits == 0:
        suggestions.append("开场可以补一笔承接前文的动作、关系或状态，减少片段感。")
    if next_raw and not (current_mentions & next_mentions) and handoff_hits == 0:
        suggestions.append("结尾补一个钩子、未完成动作或状态余波，让下一幕更自然接上。")

    comment = "这一幕与前后文的接缝基本顺。" if score >= 15 else "这一幕单独可读，但与前后文的承接还可以更明显。"
    signals = [
        f"承接角色重合 {len(current_mentions & previous_mentions)} 个",
        f"后续角色重合 {len(current_mentions & next_mentions)} 个",
        f"承接/过渡词 {continuity_hits} 个",
    ]
    return _dimension_result("continuity", "连续性", score, comment, signals, suggestions)


def _score_scene_logic(
    snapshot_candidates: List[Dict[str, Any]],
    relation_candidates: List[Dict[str, Any]],
    scene_text: str,
) -> Dict[str, Any]:
    causal_hits = _count_keyword_hits(scene_text, CAUSALITY_KEYWORDS)
    motivation_hits = _count_keyword_hits(scene_text, MOTIVATION_KEYWORDS)
    decision_hits = _count_keyword_hits(scene_text, SCENE_CHANGE_KEYWORDS)
    score = 5

    if causal_hits >= 2:
        score += 6
    elif causal_hits >= 1:
        score += 4

    if motivation_hits >= 2:
        score += 4
    elif motivation_hits >= 1:
        score += 2

    if decision_hits >= 1:
        score += 3

    if snapshot_candidates or relation_candidates:
        score += 2

    suggestions: List[str] = []
    if causal_hits == 0 and decision_hits == 0:
        suggestions.append("补清楚“为什么现在发生这件事”，避免角色像被作者硬推着走。")
    if motivation_hits == 0:
        suggestions.append("给角色一个更直白的动机或顾虑提示，读者更容易跟上行动逻辑。")

    comment = "人物行动和因果链基本说得通。" if score >= 15 else "事件能看懂，但因果或动机还可以再明示一点。"
    signals = [
        f"因果词 {causal_hits} 个",
        f"动机词 {motivation_hits} 个",
        f"决定/变化词 {decision_hits} 个",
    ]
    return _dimension_result("logic", "逻辑性", score, comment, signals, suggestions)


def _score_scene_foreshadowing(relation_candidates: List[Dict[str, Any]], scene_text: str) -> Dict[str, Any]:
    setup_hits = _count_keyword_hits(scene_text, FORESHADOWING_SETUP_KEYWORDS)
    payoff_hits = _count_keyword_hits(scene_text, FORESHADOWING_PAYOFF_KEYWORDS)
    question_hits = len(re.findall(r"[？?]", scene_text))
    score = 4

    if setup_hits >= 2:
        score += 6
    elif setup_hits >= 1:
        score += 4

    if payoff_hits >= 1:
        score += 6

    if question_hits >= 1 or relation_candidates:
        score += 3

    suggestions: List[str] = []
    if setup_hits == 0 and payoff_hits == 0:
        suggestions.append("考虑种下一个后续要兑现的信息点，或让当前冲突形成更明确的回收钩子。")
    if question_hits == 0 and not relation_candidates:
        suggestions.append("结尾可以留下一个未解答的问题，增强这一幕的牵引力。")

    comment = "这一幕兼顾了悬念维持或局部兑现。" if score >= 15 else "这一幕完成了当前动作，但伏笔/回收信号还偏弱。"
    signals = [
        f"伏笔信号 {setup_hits} 个",
        f"回收信号 {payoff_hits} 个",
        f"疑问钩子 {question_hits} 个",
    ]
    return _dimension_result("foreshadowing", "伏笔与回收", score, comment, signals, suggestions)


def _score_scene_clarity(paragraphs: List[str], mention_names: List[str], scene_text: str) -> Dict[str, Any]:
    setting_hits = _count_keyword_hits(scene_text, SETTING_KEYWORDS)
    opening = paragraphs[0] if paragraphs else ""
    opening_has_anchor = _count_keyword_hits(opening, SETTING_KEYWORDS) > 0
    score = 5

    if setting_hits >= 2:
        score += 6
    elif setting_hits >= 1:
        score += 4

    if len(mention_names) >= 2:
        score += 4
    elif len(mention_names) >= 1:
        score += 2

    if opening_has_anchor:
        score += 3

    if len(paragraphs) >= 2:
        score += 2

    suggestions: List[str] = []
    if setting_hits == 0:
        suggestions.append("开头补一个时间、地点或环境锚点，帮助读者快速抓到镜头。")
    if len(mention_names) <= 1:
        suggestions.append("把这一幕里最关键的角色关系点得更明确，减少“有人在说话但局面不清”的感觉。")

    comment = "这一幕的镜头和焦点比较清楚。" if score >= 15 else "读者能跟上大意，但场景锚点还可以更稳。"
    signals = [
        f"环境锚点 {setting_hits} 个",
        f"出场角色 {len(mention_names)} 个",
        f"开头带锚点 {'是' if opening_has_anchor else '否'}",
    ]
    return _dimension_result("sceneClarity", "场景清晰度", score, comment, signals, suggestions)


def _append_alignment(
    promise: str,
    condition: bool,
    matched: List[str],
    risks: List[str],
    matched_message: str,
    risk_message: str,
) -> None:
    if condition:
        matched.append(f"核心承诺“{promise}”：{matched_message}")
    else:
        risks.append(f"核心承诺“{promise}”：{risk_message}")


def _build_weighted_scores(project: Dict[str, Any], dimension_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    positioning = project.get("positioning", {})
    commercial = project.get("commercialPositioning", {})
    primary_genre = normalize_primary_genre(positioning.get("primaryGenre", ""))
    sub_genre = normalize_machine_label(positioning.get("subGenre", ""))
    style_tags = [normalize_machine_label(item) for item in positioning.get("styleTags", []) if item]
    target_platform = normalize_machine_label(commercial.get("targetPlatform", ""))

    applied_profile = BASE_GENRE_WEIGHTS.get(primary_genre, BASE_GENRE_WEIGHTS["default"]).copy()
    adjustments: List[Dict[str, str | int]] = []

    _apply_weight_delta(applied_profile, SUBGENRE_WEIGHT_DELTAS.get(sub_genre, {}), f"subGenre:{sub_genre}", adjustments)
    for style_tag in style_tags:
        _apply_weight_delta(applied_profile, STYLE_WEIGHT_DELTAS.get(style_tag, {}), f"styleTag:{style_tag}", adjustments)
    _apply_weight_delta(
        applied_profile,
        PLATFORM_WEIGHT_DELTAS.get(target_platform, {}),
        f"targetPlatform:{target_platform}",
        adjustments,
    )

    normalized_profile = _normalize_weight_profile(applied_profile)
    breakdown: List[Dict[str, Any]] = []
    total = 0.0
    for dimension in CHAPTER_REVIEW_RUBRIC:
        dimension_id = dimension["id"]
        raw_score = dimension_map[dimension_id]["score"]
        weight = normalized_profile[dimension_id]
        contribution = round((raw_score / MAX_DIMENSION_SCORE) * weight, 2)
        breakdown.append(
            {
                "id": dimension_id,
                "label": dimension["label"],
                "rawScore": raw_score,
                "weight": weight,
                "contribution": contribution,
            }
        )
        total += contribution

    return {
        "profile": {
            "primaryGenre": primary_genre or "default",
            "subGenre": sub_genre,
            "styleTags": style_tags,
            "targetPlatform": target_platform,
        },
        "appliedWeights": normalized_profile,
        "adjustments": adjustments,
        "total": round(total, 2),
        "maxScore": 100,
        "rating": _rating_label(round(total)),
        "breakdown": breakdown,
    }


def _apply_weight_delta(
    profile: Dict[str, int],
    delta: Dict[str, int],
    source: str,
    adjustments: List[Dict[str, str | int]],
) -> None:
    if not delta:
        return
    for key, value in delta.items():
        if key in profile:
            profile[key] += value
            adjustments.append({"source": source, "dimension": key, "delta": value})


def _normalize_weight_profile(profile: Dict[str, int]) -> Dict[str, int]:
    clamped = {key: max(5, value) for key, value in profile.items()}
    total = sum(clamped.values()) or 1
    normalized = {key: round(value * 100 / total) for key, value in clamped.items()}
    diff = 100 - sum(normalized.values())
    if diff != 0:
        anchor = max(normalized, key=normalized.get)
        normalized[anchor] += diff
    return normalized


def _build_summary(total_score: int, best_label: str, weakest_label: str, analysis_backed: bool) -> str:
    basis = "结合分析结果和正文信号" if analysis_backed else "仅基于正文启发式信号"
    return f"{basis}，本章总分 {total_score}/100。当前强项在{best_label}，最需要补强的是{weakest_label}。"


def _build_scene_summary(total_score: int, best_label: str, weakest_label: str) -> str:
    return f"基于选定片段的正文与分析信号，这一幕总分 {total_score}/100。当前最稳的是{best_label}，最需要补强的是{weakest_label}。"


def _rating_label(total_score: int) -> str:
    if total_score >= 85:
        return "strong"
    if total_score >= 70:
        return "solid"
    if total_score >= 55:
        return "workable"
    return "needs-revision"


def _count_keyword_hits(text: str, keywords: Iterable[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _dialogue_paragraphs(paragraphs: Iterable[str]) -> int:
    return sum(1 for item in paragraphs if any(mark in item for mark in ("“", "”", "\"", "「", "」")))


def _average_length(paragraphs: List[str]) -> int:
    if not paragraphs:
        return 0
    return round(sum(len(item) for item in paragraphs) / len(paragraphs))


def _clamp(value: int, low: int = 0, high: int = MAX_DIMENSION_SCORE) -> int:
    return max(low, min(high, value))
