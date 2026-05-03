"""
综合审查服务 - Comprehensive Review Service
审查AI作为严格编辑，全面检查小说质量
"""

from typing import Any, Dict, List, Tuple
import re
from collections import Counter


def comprehensive_review(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    focus_areas: List[str] | None = None,
    strictness: str = "standard"
) -> Dict[str, Any]:
    """
    综合审查 - 全面检查小说质量
    Comprehensive review covering all editing aspects
    """
    focus_areas = focus_areas or ["entities", "logic", "satisfaction", "structure"]

    review_result = {
        "reviewId": f"comprehensive-review-{chapter_id}",
        "chapterId": chapter_id,
        "generatedAt": _now_iso(),
        "strictness": strictness,
        "focusAreas": focus_areas,
    }

    # 1. 实体审查
    if "entities" in focus_areas:
        entity_review = review_entities(state, chapter_id, chapter_text)
        review_result["entityReview"] = entity_review

    # 2. 逻辑一致性检查
    if "logic" in focus_areas:
        logic_review = review_logical_consistency(state, chapter_id, chapter_text)
        review_result["logicalConsistency"] = logic_review

    # 3. 爽点分析
    if "satisfaction" in focus_areas:
        satisfaction_review = review_satisfaction_points(state, chapter_id, chapter_text)
        review_result["satisfactionAnalysis"] = satisfaction_review

    # 4. 结构分析
    if "structure" in focus_areas:
        structure_review = review_structure(state, chapter_id, chapter_text)
        review_result["structureAnalysis"] = structure_review

    # 5. 生成总体评估
    review_result["overallAssessment"] = generate_overall_assessment(review_result)

    return review_result


def review_entities(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str
) -> Dict[str, Any]:
    """实体审查"""
    from .entity_missing_detection import detect_unknown_entities_comprehensive

    # 检查未知实体
    entity_detection = detect_unknown_entities_comprehensive(state, chapter_text, chapter_id)

    return entity_detection.get("entityReview", {})


def review_logical_consistency(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str
) -> Dict[str, Any]:
    """逻辑一致性检查"""
    issues = []

    # 1. 加载前面章节的内容
    previous_chapters = _load_previous_chapters(state, chapter_id, count=2)

    # 2. 提取当前章节的实体和状态
    current_entities = _extract_entities(chapter_text)
    current_states = _extract_states(chapter_text)

    # 3. 检查实体状态矛盾
    for entity_name, current_state in current_states.items():
        previous_state = _get_entity_state_from_previous(
            entity_name, previous_chapters
        )

        if previous_state and _has_contradiction(previous_state, current_state):
            issues.append({
                "severity": "major",
                "type": "entity-state-contradiction",
                "entity": entity_name,
                "previous": previous_state,
                "current": current_state,
                "location": _find_contradiction_location(chapter_text, entity_name),
                "suggestion": f"修正{entity_name}的状态描述，或补充过渡说明"
            })

    # 4. 检查因果关系合理性
    events = _extract_events(chapter_text)
    for event in events:
        causality_issues = _check_causality(event, chapter_text, state)
        issues.extend(causality_issues)

    # 5. 检查设定遵循
    world_rules = state.get("worldbook", {}).get("worldRules", [])
    for rule in world_rules:
        violations = _check_rule_violation(chapter_text, rule)
        if violations:
            issues.append({
                "severity": "moderate",
                "type": "world-rule-violation",
                "rule": rule.get("rule", ""),
                "violations": violations,
                "suggestion": "调整内容或更新设定"
            })

    # 计算分数
    error_count = len([i for i in issues if i["severity"] == "major"])
    warning_count = len([i for i in issues if i["severity"] == "moderate"])

    score = 15 - error_count * 3 - warning_count * 1
    score = max(0, score)

    return {
        "overallScore": score,
        "issues": issues,
        "errorCount": error_count,
        "warningCount": warning_count,
        "summary": _generate_logic_summary(score, issues)
    }


def review_satisfaction_points(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str
) -> Dict[str, Any]:
    """爽点分析"""
    satisfaction_points = []

    # 1. 识别各种爽点类型
    paragraphs = _split_paragraphs(chapter_text)

    for i, para in enumerate(paragraphs):
        point_type = _identify_satisfaction_point(para)
        if point_type:
            strength = _calculate_satisfaction_strength(para, point_type, state)
            satisfaction_points.append({
                "type": point_type,
                "paragraph": i + 1,
                "strength": strength,
                "content": para[:100],
                "emotionImpact": _analyze_emotion_impact(para)
            })

    # 2. 分析分布
    distribution = Counter(p["type"] for p in satisfaction_points)

    # 3. 检查密度
    density = _analyze_satisfaction_density(satisfaction_points, len(paragraphs))

    # 4. 检查商业契约履行
    contract_alignment = _check_contract_alignment(satisfaction_points, state)

    # 5. 生成建议
    suggestions = _generate_satisfaction_suggestions(
        satisfaction_points, density, contract_alignment
    )

    # 计算分数
    point_count = len(satisfaction_points)
    if point_count >= 5:
        score = 15
    elif point_count >= 3:
        score = 12
    elif point_count >= 1:
        score = 9
    else:
        score = 6

    return {
        "overallScore": score,
        "pointCount": point_count,
        "points": satisfaction_points,
        "distribution": dict(distribution),
        "density": density,
        "contractAlignment": contract_alignment,
        "suggestions": suggestions,
        "summary": _generate_satisfaction_summary(score, satisfaction_points)
    }


def review_structure(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str
) -> Dict[str, Any]:
    """结构分析"""
    outline = state.get("outline", {})
    volume = _find_volume_for_chapter(outline, chapter_id)

    if not volume:
        return {
            "overallScore": 0,
            "error": "无法找到章节所属的卷",
            "issues": []
        }

    # 1. 检查3幕结构
    three_act = _analyze_three_act_structure(volume, outline)

    # 2. 检查卷级闭环
    closure = _check_volume_closure(state, volume)

    # 3. 检查剧情节奏
    rhythm = _analyze_plot_rhythm(chapter_id, chapter_text, outline)

    # 4. 汇总问题
    all_issues = (
        three_act.get("issues", []) +
        closure.get("issues", []) +
        rhythm.get("issues", [])
    )

    # 计算分数
    major_count = len([i for i in all_issues if i.get("severity") == "major"])
    score = 15 - major_count * 2

    return {
        "overallScore": score,
        "threeActStructure": three_act,
        "volumeClosure": closure,
        "plotRhythm": rhythm,
        "issues": all_issues,
        "summary": _generate_structure_summary(score, all_issues)
    }


# ===== 辅助函数 =====

def _identify_satisfaction_point(text: str) -> str | None:
    """识别爽点类型"""
    # 打脸特征
    face_slap_patterns = [
        r"不是.*吗.*",  # 反问打脸
        r"你以为.*",    # 误解纠正
        r"其实.*",       # 真相揭露
        r"原来.*",       # 发现真相
    ]

    # 装逼特征
    show_off_patterns = [
        "展现实力", "震惊全场", "众人瞩目",
        "出手", "露一手", "展示"
    ]

    # 反转特征
    reversal_patterns = [
        "然而", "没想到", "竟然",
        "真相", "事实是", "原来"
    ]

    # 获得特征
    gain_patterns = [
        "获得", "得到", "突破", "提升",
        "炼制", "学会", "领悟"
    ]

    # 检查是否匹配
    for pattern in face_slap_patterns:
        if re.search(pattern, text):
            return "face_slap"

    for keyword in show_off_patterns:
        if keyword in text:
            return "show_off"

    for keyword in reversal_patterns:
        if keyword in text:
            return "reversal"

    for keyword in gain_patterns:
        if keyword in text:
            return "gain"

    return None


def _calculate_satisfaction_strength(text: str, point_type: str, state: Dict[str, Any]) -> int:
    """计算爽点强度"""
    base_strength = 5

    # 根据类型调整
    type_modifiers = {
        "face_slap": 3,
        "show_off": 2,
        "reversal": 4,
        "gain": 2
    }

    # 检查描述丰富度
    description_length = len(text)
    if description_length > 200:
        base_strength += 2
    elif description_length > 100:
        base_strength += 1

    # 检查是否有对话（对话增强爽感）
    if '"' in text or '"' in text:
        base_strength += 1

    # 检查是否有感叹号（情绪强烈）
    if text.count('！') >= 2:
        base_strength += 1

    return min(15, base_strength + type_modifiers.get(point_type, 0))


def _analyze_emotion_impact(text: str) -> str:
    """分析情绪冲击"""
    if '！' in text or text.count('!') >= 2:
        return "strong"
    elif '？' in text or '?' in text:
        return "curious"
    elif '...' in text or '…' in text:
        return "contemplative"
    else:
        return "neutral"


def _analyze_satisfaction_density(points: List[Dict], paragraph_count: int) -> str:
    """分析爽点密度"""
    if paragraph_count == 0:
        return "unknown"

    density = len(points) / paragraph_count

    if density >= 0.4:  # 每2.5段一个爽点
        return "dense"
    elif density >= 0.2:  # 每5段一个爽点
        return "adequate"
    else:
        return "sparse"


def _check_contract_alignment(points: List[Dict], state: Dict[str, Any]) -> Dict[str, Any]:
    """检查商业契约履行"""
    contract = state.get("project", {}).get("storyContract", {})
    core_promises = contract.get("corePromises", [])

    alignment = {
        "corePromises": core_promises,
        "fulfilled": True,
        "hookQuality": "unknown"
    }

    # 检查结尾钩子
    last_point = points[-1] if points else None
    if last_point:
        if last_point["type"] in ["reversal", "face_slap"]:
            alignment["hookQuality"] = "high"
        elif last_point["type"] == "gain":
            alignment["hookQuality"] = "medium"
        else:
            alignment["hookQuality"] = "low"

    # 检查核心承诺
    for promise in core_promises:
        if "追读钩子" in promise and alignment["hookQuality"] == "low":
            alignment["fulfilled"] = False

    return alignment


def _generate_satisfaction_suggestions(
    points: List[Dict],
    density: str,
    contract_alignment: Dict[str, Any]
) -> List[str]:
    """生成爽点改进建议"""
    suggestions = []

    if density == "sparse":
        suggestions.append("爽点密度较低，建议增加主角展示实力或剧情反转的情节")

    if density == "dense":
        suggestions.append("爽点密度较高，注意避免审美疲劳")

    if contract_alignment["hookQuality"] == "low":
        suggestions.append("结尾钩子质量不高，建议增加悬念或反转")

    if not points:
        suggestions.append("未检测到明显爽点，考虑添加主角高光时刻")

    return suggestions


def _extract_entities(text: str) -> Dict[str, Dict]:
    """提取实体"""
    # 简化实现：查找@{}包裹的实体
    entities = {}
    pattern = r'@\{([^}]+)\}'
    matches = re.findall(pattern, text)

    for match in matches:
        entities[match] = {"name": match, "wrapped": True}

    return entities


def _extract_states(text: str) -> Dict[str, Dict]:
    """提取实体状态"""
    # 简化实现：查找状态描述
    states = {}

    # 这里需要更复杂的NLP分析
    # 暂时返回空字典
    return states


def _extract_events(text: str) -> List[Dict]:
    """提取事件"""
    # 简化实现：按句子分割事件
    sentences = re.split(r'[。！？]', text)
    events = []

    for i, sentence in enumerate(sentences):
        if sentence.strip():
            events.append({
                "id": f"event-{i}",
                "description": sentence.strip(),
                "position": i
            })

    return events


def _load_previous_chapters(state: Dict[str, Any], chapter_id: str, count: int = 2) -> List[str]:
    """加载前面章节的内容"""
    # 简化实现
    return []


def _get_entity_state_from_previous(entity_name: str, previous_chapters: List[str]) -> Dict | None:
    """从前面章节获取实体状态"""
    # 简化实现
    return None


def _has_contradiction(previous: Dict, current: Dict) -> bool:
    """检查是否有矛盾"""
    # 简化实现
    return False


def _find_contradiction_location(text: str, entity_name: str) -> str:
    """查找矛盾位置"""
    # 简化实现：返回实体第一次出现的位置
    pos = text.find(entity_name)
    if pos != -1:
        return f"位置 {pos} 附近"
    return "未知位置"


def _check_causality(event: Dict, text: str, state: Dict[str, Any]) -> List[Dict]:
    """检查因果关系"""
    # 简化实现
    return []


def _check_rule_violation(text: str, rule: Dict) -> List[str]:
    """检查设定违规"""
    violations = []
    rule_text = rule.get("rule", "")

    # 简化检查：如果规则中有"禁止"关键词
    if "禁止" in rule_text or "不能" in rule_text:
        # 提取禁止的内容
        # 这里需要更复杂的解析
        pass

    return violations


def _analyze_three_act_structure(volume: Dict, outline: Dict) -> Dict[str, Any]:
    """分析3幕结构"""
    chapters = volume.get("chapters", [])
    total_chapters = len(chapters)

    if total_chapters == 0:
        return {
            "error": "卷中没有章节",
            "issues": []
        }

    # 3幕划分
    act1_end = int(total_chapters * 0.25)
    act2_end = int(total_chapters * 0.75)

    act1_chapters = chapters[:act1_end]
    act2_chapters = chapters[act1_end:act2_end]
    act3_chapters = chapters[act2_end:]

    return {
        "act1": {
            "name": "铺垫",
            "chapterRange": f"1-{act1_end}",
            "chapterCount": len(act1_chapters),
            "purpose": "介绍主角、建立目标、引入冲突"
        },
        "act2": {
            "name": "冲突",
            "chapterRange": f"{act1_end + 1}-{act2_end}",
            "chapterCount": len(act2_chapters),
            "purpose": "发展冲突、升级压力、推进剧情"
        },
        "act3": {
            "name": "结局",
            "chapterRange": f"{act2_end + 1}-{total_chapters}",
            "chapterCount": len(act3_chapters),
            "purpose": "解决冲突、达成目标、为下一卷铺垫"
        },
        "issues": []
    }


def _check_volume_closure(state: Dict[str, Any], volume: Dict[str, Any]) -> Dict[str, Any]:
    """检查卷级闭环"""
    issues = []

    # 检查主线目标
    goal = volume.get("goal")
    if not goal:
        issues.append({
            "severity": "major",
            "type": "missing-volume-goal",
            "description": "卷缺少明确的主线目标"
        })

    return {
        "canClose": len([i for i in issues if i["severity"] == "major"]) == 0,
        "goalAchieved": bool(goal),
        "issues": issues
    }


def _analyze_plot_rhythm(chapter_id: str, chapter_text: str, outline: Dict) -> Dict[str, Any]:
    """分析剧情节奏"""
    # 简化实现：基于段落长度分析节奏
    paragraphs = _split_paragraphs(chapter_text)

    if not paragraphs:
        return {
            "rhythm": "unknown",
            "issues": []
        }

    # 计算平均段落长度
    avg_length = sum(len(p) for p in paragraphs) / len(paragraphs)

    # 分析节奏
    long_paragraphs = len([p for p in paragraphs if len(p) > avg_length * 1.5])
    short_paragraphs = len([p for p in paragraphs if len(p) < avg_length * 0.5])

    if long_paragraphs > len(paragraphs) * 0.3:
        rhythm = "slow"
        issues = [{
            "severity": "minor",
            "type": "rhythm-slow",
            "description": "长段落较多，节奏可能偏慢"
        }]
    elif short_paragraphs > len(paragraphs) * 0.7:
        rhythm = "fast"
        issues = [{
            "severity": "minor",
            "type": "rhythm-fast",
            "description": "短段落较多，节奏可能偏快"
        }]
    else:
        rhythm = "balanced"
        issues = []

    return {
        "rhythm": rhythm,
        "avgParagraphLength": avg_length,
        "longParagraphs": long_paragraphs,
        "shortParagraphs": short_paragraphs,
        "issues": issues
    }


def _find_volume_for_chapter(outline: Dict, chapter_id: str) -> Dict | None:
    """查找章节所属的卷"""
    for volume in outline.get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return None


def _split_paragraphs(text: str) -> List[str]:
    """分割段落"""
    paragraphs = text.split('\n\n')
    return [p.strip() for p in paragraphs if p.strip()]


def _generate_overall_assessment(review_result: Dict) -> Dict[str, Any]:
    """生成总体评估"""
    scores = []

    if "entityReview" in review_result:
        entity_review = review_result["entityReview"]
        if entity_review.get("unknownEntityDiscovery", {}).get("discoveredCount", 0) > 0:
            scores.append({
                "area": "实体完整性",
                "score": 10,
                "issue": f"发现{entity_review['unknownEntityDiscovery']['discoveredCount']}个未知实体"
            })

    if "logicalConsistency" in review_result:
        logic_review = review_result["logicalConsistency"]
        scores.append({
            "area": "逻辑一致性",
            "score": logic_review.get("overallScore", 0),
            "issue": logic_review.get("summary", "")
        })

    if "satisfactionAnalysis" in review_result:
        satisfaction_review = review_result["satisfactionAnalysis"]
        scores.append({
            "area": "爽点设计",
            "score": satisfaction_review.get("overallScore", 0),
            "issue": satisfaction_review.get("summary", "")
        })

    if "structureAnalysis" in review_result:
        structure_review = review_result["structureAnalysis"]
        scores.append({
            "area": "结构完整性",
            "score": structure_review.get("overallScore", 0),
            "issue": structure_review.get("summary", "")
        })

    # 计算总分
    if scores:
        total_score = sum(s["score"] for s in scores) / len(scores)
    else:
        total_score = 10

    # 汇总问题
    all_issues = []
    for area_review in review_result.values():
        if isinstance(area_review, dict) and "issues" in area_review:
            all_issues.extend(area_review["issues"])

    critical_count = len([i for i in all_issues if i.get("severity") == "critical"])
    major_count = len([i for i in all_issues if i.get("severity") == "major"])

    return {
        "totalScore": round(total_score, 1),
        "readyForNext": critical_count == 0 and major_count < 3,
        "criticalIssues": critical_count,
        "majorIssues": major_count,
        "moderateIssues": len([i for i in all_issues if i.get("severity") == "moderate"]),
        "minorIssues": len([i for i in all_issues if i.get("severity") == "minor"]),
        "areaScores": scores,
        "summary": _generate_overall_summary(total_score, all_issues),
        "priorities": _generate_priorities(all_issues)
    }


def _generate_overall_summary(score: float, issues: List) -> str:
    """生成总体摘要"""
    if score >= 14:
        quality = "优秀"
    elif score >= 12:
        quality = "良好"
    elif score >= 9:
        quality = "一般"
    else:
        quality = "需要改进"

    critical_count = len([i for i in issues if i.get("severity") == "critical"])
    major_count = len([i for i in issues if i.get("severity") == "major"])

    if critical_count > 0:
        return f"章节质量{quality}，存在{critical_count}个严重问题需要修正"
    elif major_count > 0:
        return f"章节质量{quality}，存在{major_count}个重要问题建议修正"
    elif len(issues) > 0:
        return f"章节质量{quality}，存在{len(issues)}个可优化项"
    else:
        return f"章节质量{quality}，未发现明显问题"


def _generate_priorities(issues: List) -> List[str]:
    """生成改进优先级"""
    priorities = []

    # 按严重程度分组
    critical_issues = [i for i in issues if i.get("severity") == "critical"]
    major_issues = [i for i in issues if i.get("severity") == "major"]

    if critical_issues:
        priorities.append("【P0-紧急】修正严重问题：")
        for issue in critical_issues[:3]:
            priorities.append(f"  - {issue.get('description', issue.get('type', ''))}")

    if major_issues:
        priorities.append("【P1-重要】修正重要问题：")
        for issue in major_issues[:3]:
            priorities.append(f"  - {issue.get('description', issue.get('type', ''))}")

    return priorities


def _generate_logic_summary(score: int, issues: List) -> str:
    """生成逻辑审查摘要"""
    if score >= 14:
        return "逻辑审查通过，未发现明显矛盾"
    elif score >= 10:
        return f"逻辑审查基本通过，发现{len(issues)}个可优化项"
    else:
        return f"逻辑审查发现问题，建议修正后再继续"


def _generate_satisfaction_summary(score: int, points: List) -> str:
    """生成爽点分析摘要"""
    if score >= 12:
        return f"爽点设计良好，共{len(points)}个爽点"
    elif score >= 8:
        return f"爽点设计尚可，共{len(points)}个爽点"
    else:
        return f"爽点设计需要加强，仅{len(points)}个爽点"


def _generate_structure_summary(score: int, issues: List) -> str:
    """生成结构分析摘要"""
    if score >= 14:
        return "结构完整，符合预期"
    elif score >= 10:
        return f"结构基本完整，发现{len(issues)}个可优化项"
    else:
        return f"结构存在问题，需要调整"


def _now_iso() -> str:
    """获取当前ISO时间"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
