"""
大纲级审查服务 - Outline-Level Review Service
检查大纲合理性、设定一致性和剧情连贯性
"""

from typing import Any, Dict, List


def review_outline(
    state: Dict[str, Any],
    check_consistency: bool = True,
    check_foreshadowing: bool = True,
) -> Dict[str, Any]:
    """
    审查大纲合理性和一致性
    Review outline rationality and consistency
    """
    outline = state.get("outline", {})
    worldbook = state.get("worldbook", {})
    world = state.get("world", {})
    entities = state.get("entities", {}).get("entities", [])
    foreshadowing = state.get("foreshadowing", {})

    issues = []
    scores = {}

    # 1. 检查大纲与设定的一致性
    if check_consistency:
        consistency_score = _check_outline_setting_consistency(
            outline, worldbook, world, entities
        )
        scores["settingConsistency"] = consistency_score

        if consistency_score["score"] < 12:
            issues.extend(consistency_score.get("issues", []))

    # 2. 检查大纲与伏笔的一致性
    if check_foreshadowing:
        foreshadow_score = _check_outline_foreshadow_consistency(
            outline, foreshadowing
        )
        scores["foreshadowConsistency"] = foreshadow_score

        if foreshadow_score["score"] < 12:
            issues.extend(foreshadow_score.get("issues", []))

    # 3. 检查剧情走向连贯性
    coherence_score = _check_plot_coherence(outline)
    scores["plotCoherence"] = coherence_score

    if coherence_score["score"] < 12:
        issues.extend(coherence_score.get("issues", []))

    # 4. 检查角色弧线合理性
    arc_score = _check_character_arcs(outline, entities)
    scores["characterArcs"] = arc_score

    if arc_score["score"] < 12:
        issues.extend(arc_score.get("issues", []))

    # 计算总分
    total_score = sum(s["score"] for s in scores.values()) / len(scores) if scores else 0

    return {
        "overallScore": total_score,
        "scores": scores,
        "issues": issues,
        "ready": total_score >= 12 and len([i for i in issues if i["level"] == "error"]) == 0,
        "summary": _build_review_summary(total_score, len(issues)),
        "recommendations": _build_recommendations(issues),
    }


def _check_outline_setting_consistency(
    outline: Dict[str, Any],
    worldbook: Dict[str, Any],
    world: Dict[str, Any],
    entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """检查大纲与设定的一致性"""
    issues = []

    volumes = outline.get("volumes", [])
    world_rules = worldbook.get("worldRules", [])
    world_items = world.get("items", [])

    # 检查大纲是否使用了设定的元素
    all_chapters = []
    for vol in volumes:
        all_chapters.extend(vol.get("chapters", []))

    # 提取章节中提到的实体
    mentioned_entities = set()
    for ch in all_chapters:
        brief = ch.get("brief", "")
        direction = ch.get("direction", "")
        text = f"{brief} {direction}"

        # 简单的实体名提取
        for entity in entities:
            name = entity.get("name", "")
            if name and name in text:
                mentioned_entities.add(name)

    # 检查是否有已注册实体未被使用
    unused_entities = []
    for entity in entities:
        name = entity.get("name", "")
        if name and name not in mentioned_entities:
            unused_entities.append(name)

    if unused_entities and len(unused_entities) > len(entities) * 0.3:
        issues.append({
            "level": "info",
            "category": "entity-usage",
            "message": f"部分设定实体可能未在大纲中使用: {', '.join(unused_entities[:5])}",
            "suggestion": "考虑在相应章节中引入这些实体，或确认它们是否为后期角色",
        })

    # 检查是否使用了世界规则
    if world_rules:
        rule_usage = False
        for ch in all_chapters:
            direction = ch.get("direction", "")
            if any(rule.get("rule", "") in direction for rule in world_rules):
                rule_usage = True
                break

        if not rule_usage:
            issues.append({
                "level": "info",
                "category": "rule-usage",
                "message": "大纲中可能未充分利用世界规则",
                "suggestion": "考虑在章节direction中体现世界规则的作用",
            })

    # 计算分数
    if not issues:
        score = 15
    elif len([i for i in issues if i["level"] == "warning"]) > 0:
        score = 10
    else:
        score = 12

    return {"score": score, "issues": issues}


def _check_outline_foreshadow_consistency(
    outline: Dict[str, Any],
    foreshadowing: Dict[str, Any],
) -> Dict[str, Any]:
    """检查大纲与伏笔的一致性"""
    issues = []

    foreshadows = foreshadowing.get("foreshadows", [])
    volumes = outline.get("volumes", [])

    # 收集所有章节ID
    all_chapter_ids = set()
    for vol in volumes:
        for ch in vol.get("chapters", []):
            all_chapter_ids.add(ch.get("id"))

    # 检查伏笔的埋点章节是否存在
    invalid_plants = []
    for foreshadow in foreshadows:
        for plant in foreshadow.get("plantPoints", []):
            chapter_id = plant.get("chapterId")
            if chapter_id and chapter_id not in all_chapter_ids:
                invalid_plants.append({
                    "foreshadowId": foreshadow.get("id"),
                    "chapterId": chapter_id,
                })

    if invalid_plants:
        issues.append({
            "level": "warning",
            "category": "foreshadow-plant-invalid",
            "message": f"{len(invalid_plants)}个伏笔埋点引用了不存在的章节",
            "details": invalid_plants[:5],
            "suggestion": "检查伏笔的plantPoints是否引用了正确的章节ID",
        })

    # 检查伏笔回收窗口是否合理
    invalid_payoffs = []
    for foreshadow in foreshadows:
        payoff_plan = foreshadow.get("payoffPlan", {})
        window = payoff_plan.get("window", "")

        if window:
            # 检查窗口格式是否合理
            if not _is_valid_chapter_window(window, all_chapter_ids):
                invalid_payoffs.append({
                    "foreshadowId": foreshadow.get("id"),
                    "window": window,
                })

    if invalid_payoffs:
        issues.append({
            "level": "warning",
            "category": "foreshadow-payoff-invalid",
            "message": f"{len(invalid_payoffs)}个伏笔回收窗口格式不正确",
            "details": invalid_payoffs[:5],
            "suggestion": "回收窗口应为章节ID范围，如 'chapter-001:chapter-010'",
        })

    # 计算分数
    if not issues:
        score = 15
    elif len(invalid_plants) > 0 or len(invalid_payoffs) > 0:
        score = 8
    else:
        score = 12

    return {"score": score, "issues": issues}


def _check_plot_coherence(outline: Dict[str, Any]) -> Dict[str, Any]:
    """检查剧情走向连贯性"""
    issues = []

    volumes = outline.get("volumes", [])
    all_chapters = []
    for vol in volumes:
        all_chapters.extend(vol.get("chapters", []))

    # 检查章节之间的衔接
    for i in range(len(all_chapters) - 1):
        current = all_chapters[i]
        next_ch = all_chapters[i + 1]

        current_direction = current.get("direction", "")
        next_direction = next_ch.get("direction", "")

        # 检查是否有明确的承接关系
        if current_direction and next_direction:
            # 检查是否有明显的承接信号
            if not _has_clear_continuation(current_direction, next_direction):
                issues.append({
                    "level": "info",
                    "category": "plot-coherence",
                    "fromChapter": current.get("id"),
                    "toChapter": next_ch.get("id"),
                    "message": f"章节 {current.get('title', current.get('id'))} 到 {next_ch.get('title', next_ch.get('id'))} 的承接关系可能不够明确",
                    "suggestion": "补充章节间的承接点或钩子",
                })

    # 检查是否有空洞章节
    empty_chapters = [
        ch for ch in all_chapters
        if not ch.get("direction") and not ch.get("brief")
    ]

    for ch in empty_chapters:
        issues.append({
            "level": "warning",
            "category": "plot-coherence",
            "chapterId": ch.get("id"),
            "message": f"章节 '{ch.get('title', ch.get('id'))}' 缺少方向说明",
            "suggestion": "为章节添加direction或brief",
        })

    # 计算分数
    total_chapters = len(all_chapters)
    if total_chapters == 0:
        score = 0
    else:
        coherence_ratio = 1 - len(issues) / max(total_chapters, 1)
        score = int(coherence_ratio * 15)

    return {
        "score": score,
        "totalChapters": total_chapters,
        "continuityIssues": len([i for i in issues if i["category"] == "plot-coherence"]),
        "issues": issues,
    }


def _check_character_arcs(
    outline: Dict[str, Any],
    entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """检查角色弧线合理性"""
    issues = []

    volumes = outline.get("volumes", [])
    all_chapters = []
    for vol in volumes:
        all_chapters.extend(vol.get("chapters", []))

    characters = [e for e in entities if e.get("kind") == "character"]

    # 检查主角是否在章节中有足够的出场
    protagonist_appearances = {}
    for ch in all_chapters:
        brief = ch.get("brief", "") or ""
        direction = ch.get("direction", "") or ""
        text = f"{brief} {direction}"

        for char in characters:
            name = char.get("name", "")
            if name and name in text:
                protagonist_appearances[name] = protagonist_appearances.get(name, 0) + 1

    # 检查主角出场是否合理
    for char in characters:
        if char.get("role") == "protagonist":
            name = char.get("name")
            appearances = protagonist_appearances.get(name, 0)

            # 主角应该在至少30%的章节中出现
            min_appearances = len(all_chapters) * 0.3
            if appearances < min_appearances and len(all_chapters) > 5:
                issues.append({
                    "level": "info",
                    "category": "character-appearance",
                    "entityName": name,
                    "message": f"主角 '{name}' 出现场次较少（{appearances}次）",
                    "suggestion": "考虑在更多章节中引入主角，或确认这是否为群像剧",
                })

    # 计算分数
    if not issues:
        score = 15
    elif len([i for i in issues if i["level"] == "warning"]) > 0:
        score = 10
    else:
        score = 12

    return {"score": score, "issues": issues}


def _has_clear_continuation(current_direction: str, next_direction: str) -> bool:
    """检查是否有明确的承接关系"""
    # 简单的承接检查：看是否有共同关键词
    current_words = set(current_direction.split())
    next_words = set(next_direction.split())

    overlap = current_words & next_words

    # 如果有共同关键词，认为有承接
    if len(overlap) > 0:
        return True

    # 检查是否有承接词
    continuation_keywords = ["接着", "随后", "同时", "与此同时", "另一方面", "而"]
    for keyword in continuation_keywords:
        if keyword in next_direction:
            return True

    return False


def _is_valid_chapter_window(window: str, chapter_ids: set) -> bool:
    """检查章节窗口是否有效"""
    if not window:
        return True

    # 检查是否为范围格式
    if ":" in window:
        parts = window.split(":")
        if len(parts) != 2:
            return False

        start, end = parts
        return start in chapter_ids and end in chapter_ids

    # 检查是否为单个章节ID
    return window in chapter_ids


def _build_review_summary(score: float, issue_count: int) -> str:
    """构建审查摘要"""
    if score >= 14:
        quality = "优秀"
    elif score >= 12:
        quality = "良好"
    elif score >= 9:
        quality = "一般"
    else:
        quality = "需要改进"

    if issue_count == 0:
        return f"大纲审查通过，质量{quality}"
    else:
        return f"大纲审查发现{issue_count}个问题，质量{quality}"


def _build_recommendations(issues: List[Dict[str, Any]]) -> List[str]:
    """构建改进建议"""
    recommendations = []

    for issue in issues:
        suggestion = issue.get("suggestion")
        if suggestion and suggestion not in recommendations:
            recommendations.append(suggestion)

    # 如果没有具体建议，添加通用建议
    if not recommendations:
        recommendations.append("大纲审查通过，可以继续写作")

    return recommendations
