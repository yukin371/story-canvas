"""
架构审查服务 - Architecture Review Service
用于预防方向性问题的架构级审查
"""

from typing import Any, Dict, List


def review_architecture(
    state: Dict[str, Any],
    scope: str = "full",  # "setting" | "outline" | "characters" | "plot" | "full"
) -> Dict[str, Any]:
    """
    架构级审查，预防方向性问题
    Architecture-level review to prevent directional issues
    """
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    story_contract = project.get("storyContract", {})
    story_template = project.get("storyTemplate", {})
    worldbook = state.get("worldbook", {})
    entities = state.get("entities", {}).get("entities", [])
    outline = state.get("outline", {})

    issues = []
    risks = []

    # 1. 设定架构审查
    if scope in ["setting", "full"]:
        setting_review = _review_setting_architecture(
            worldbook, story_contract, story_template
        )
        issues.extend(setting_review["issues"])
        risks.extend(setting_review["risks"])

    # 2. 大纲架构审查
    if scope in ["outline", "full"]:
        outline_review = _review_outline_architecture(
            outline, story_contract, worldbook
        )
        issues.extend(outline_review["issues"])
        risks.extend(outline_review["risks"])

    # 3. 角色架构审查
    if scope in ["characters", "full"]:
        character_review = _review_character_architecture(
            entities, story_contract, outline
        )
        issues.extend(character_review["issues"])
        risks.extend(character_review["risks"])

    # 4. 剧情架构审查
    if scope in ["plot", "full"]:
        foreshadowing = state.get("foreshadowing", {})
        plot_review = _review_plot_architecture(
            outline, story_contract, foreshadowing
        )
        issues.extend(plot_review["issues"])
        risks.extend(plot_review["risks"])

    # 评估架构风险等级
    risk_level = _assess_risk_level(issues, risks)

    return {
        "riskLevel": risk_level,
        "riskLabel": _get_risk_label(risk_level),
        "scope": scope,
        "issues": issues,
        "risks": risks,
        "recommendations": _generate_recommendations(issues, risks),
        "readyToWrite": risk_level != "high",
        "summary": _build_summary(issues, risks, risk_level),
    }


def _review_setting_architecture(
    worldbook: Dict[str, Any],
    story_contract: Dict[str, Any],
    story_template: Dict[str, Any],
) -> Dict[str, Any]:
    """审查设定架构"""
    issues = []
    risks = []

    # 检查设定是否支撑核心承诺
    core_promises = story_contract.get("corePromises", [])
    world_rules = worldbook.get("worldRules", [])

    if core_promises and world_rules:
        for promise in core_promises:
            supported = False
            for rule in world_rules:
                if _rule_supports_promise(rule, promise):
                    supported = True
                    break

            if not supported:
                issues.append({
                    "level": "warning",
                    "category": "setting-promise-alignment",
                    "message": f"设定可能不支撑核心承诺: {promise}",
                    "suggestion": "检查世界规则是否真正支撑了核心承诺",
                })
    elif core_promises and not world_rules:
        issues.append({
            "level": "error",
            "category": "setting-missing",
            "message": "缺少世界规则设定",
            "suggestion": "使用 `setting expand --target worldbook` 添加世界规则",
        })

    # 检查设定是否过于复杂
    complexity_risk = _assess_setting_complexity(worldbook)
    if complexity_risk > 0.8:
        risks.append({
            "level": "warning",
            "category": "setting-complexity",
            "message": "设定过于复杂，可能增加维护难度",
            "suggestion": "考虑简化部分设定或延迟引入",
        })

    return {"issues": issues, "risks": risks}


def _review_outline_architecture(
    outline: Dict[str, Any],
    story_contract: Dict[str, Any],
    worldbook: Dict[str, Any],
) -> Dict[str, Any]:
    """审查大纲架构"""
    issues = []
    risks = []

    volumes = outline.get("volumes", [])

    if not volumes:
        issues.append({
            "level": "error",
            "category": "outline-missing",
            "message": "缺少卷结构",
            "suggestion": "使用 `outline propose` 创建初始大纲结构",
        })
        return {"issues": issues, "risks": risks}

    # 检查每卷是否有明确主题
    for vol in volumes:
        vol_theme = vol.get("theme", "")
        if not vol_theme:
            risks.append({
                "level": "info",
                "category": "volume-theme-missing",
                "volumeId": vol.get("id"),
                "message": f"卷 '{vol.get('title', vol.get('id'))}' 缺少明确主题",
                "suggestion": "为每卷定义明确的主题和目标",
            })

    # 检查章节数量是否合理
    total_chapters = sum(len(vol.get("chapters", [])) for vol in volumes)
    if total_chapters < 10:
        risks.append({
            "level": "info",
            "category": "chapter-count-low",
            "message": f"总章数较少（{total_chapters}章）",
            "suggestion": "确认是否能充分展开故事",
        })

    # 检查章节衔接
    all_chapters = []
    for vol in volumes:
        all_chapters.extend(vol.get("chapters", []))

    continuity_issues = _check_chapter_continuity(all_chapters)
    issues.extend(continuity_issues)

    return {"issues": issues, "risks": risks}


def _review_character_architecture(
    entities: List[Dict[str, Any]],
    story_contract: Dict[str, Any],
    outline: Dict[str, Any],
) -> Dict[str, Any]:
    """审查角色架构"""
    issues = []
    risks = []

    if not entities:
        issues.append({
            "level": "error",
            "category": "entities-missing",
            "message": "缺少角色设定",
            "suggestion": "使用 `entity create --kind character` 创建主要角色",
        })
        return {"issues": issues, "risks": risks}

    # 检查是否有明确的主角
    protagonists = [e for e in entities if e.get("kind") == "character"]
    if not protagonists:
        issues.append({
            "level": "warning",
            "category": "protagonist-missing",
            "message": "缺少主角角色",
            "suggestion": "至少创建一个主角角色",
        })
    elif len(protagonists) < 2:
        risks.append({
            "level": "info",
            "category": "character-count-low",
            "message": "角色较少，可能缺乏冲突",
            "suggestion": "考虑添加反派、配角或导师角色",
        })

    # 检查角色设定完善度
    incomplete_characters = []
    for char in protagonists:
        brief = char.get("brief", "")
        if not brief or len(brief) < 20:
            incomplete_characters.append(char.get("name", char.get("id")))

    if incomplete_characters:
        risks.append({
            "level": "info",
            "category": "character-incomplete",
            "message": f"以下角色设定不够完善: {', '.join(incomplete_characters)}",
            "suggestion": "为角色添加详细的背景、性格、动机等设定",
        })

    return {"issues": issues, "risks": risks}


def _review_plot_architecture(
    outline: Dict[str, Any],
    story_contract: Dict[str, Any],
    foreshadowing: Dict[str, Any],
) -> Dict[str, Any]:
    """审查剧情架构"""
    issues = []
    risks = []

    foreshadows = foreshadowing.get("foreshadows", [])

    # 检查伏笔数量
    if len(foreshadows) < 3:
        risks.append({
            "level": "info",
            "category": "foreshadow-insufficient",
            "message": f"伏笔数量较少（{len(foreshadows)}条）",
            "suggestion": "考虑增加长期伏笔以支撑主线",
        })

    # 检查伏笔回收计划
    unresolved_without_schedule = [
        f for f in foreshadows
        if f.get("status") != "resolved" and not f.get("payoffPlan", {}).get("window")
    ]

    if unresolved_without_schedule:
        if len(unresolved_without_schedule) > len(foreshadows) * 0.5:
            issues.append({
                "level": "warning",
                "category": "foreshadow-unscheduled",
                "message": f"{len(unresolved_without_schedule)}条伏笔缺少回收计划",
                "suggestion": "为伏笔添加明确的回收窗口",
            })

    # 检查剧情连贯性
    volumes = outline.get("volumes", [])
    all_chapters = []
    for vol in volumes:
        all_chapters.extend(vol.get("chapters", []))

    coherence_issues = _check_plot_coherence(all_chapters)
    issues.extend(coherence_issues)

    return {"issues": issues, "risks": risks}


def _rule_supports_promise(rule: Dict[str, Any], promise: str) -> bool:
    """检查规则是否支撑承诺"""
    rule_text = rule.get("rule", "").lower()
    promise_lower = promise.lower()

    # 简单的关键词匹配
    promise_keywords = promise_lower.split()
    for keyword in promise_keywords:
        if len(keyword) > 2 and keyword in rule_text:
            return True

    return False


def _assess_setting_complexity(worldbook: Dict[str, Any]) -> float:
    """评估设定复杂度"""
    world_rules = worldbook.get("worldRules", [])
    premise_facts = worldbook.get("premiseFacts", [])

    # 规则数量和长度的复杂度
    rule_complexity = len(world_rules) * 0.3
    for rule in world_rules:
        rule_complexity += len(rule.get("rule", "")) * 0.01

    # 前提事实的复杂度
    fact_complexity = len(premise_facts) * 0.2

    total_complexity = rule_complexity + fact_complexity

    # 归一化到0-1
    return min(1.0, total_complexity / 20.0)


def _check_chapter_continuity(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """检查章节衔接"""
    issues = []

    for i in range(len(chapters) - 1):
        current = chapters[i]
        next_ch = chapters[i + 1]

        current_direction = current.get("direction", "")
        next_direction = next_ch.get("direction", "")

        # 如果两个章节都没有方向信息，跳过检查
        if not current_direction and not next_direction:
            continue

        # 检查是否有明确的承接关系
        if current_direction and next_direction:
            # 简单的承接检查：看是否有共同关键词
            current_words = set(current_direction.split())
            next_words = set(next_direction.split())

            overlap = current_words & next_words
            if len(overlap) == 0:
                issues.append({
                    "level": "info",
                    "category": "chapter-continuity",
                    "fromChapter": current.get("id"),
                    "toChapter": next_ch.get("id"),
                    "message": f"章节 {current.get('title', current.get('id'))} 到 {next_ch.get('title', next_ch.get('id'))} 的承接关系可能不够明确",
                    "suggestion": "补充章节间的承接点或钩子",
                })

    return issues


def _check_plot_coherence(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """检查剧情连贯性"""
    issues = []

    # 检查是否有空洞章节（没有direction或brief）
    empty_chapters = [
        ch for ch in chapters
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

    return issues


def _assess_risk_level(issues: List[Dict[str, Any]], risks: List[Dict[str, Any]]) -> str:
    """评估风险等级"""
    error_count = len([i for i in issues if i.get("level") == "error"])
    warning_count = len([i for i in issues if i.get("level") == "warning"])

    if error_count > 0:
        return "high"
    elif warning_count >= 3:
        return "medium"
    elif warning_count > 0 or len(risks) > 0:
        return "low"
    else:
        return "minimal"


def _get_risk_label(risk_level: str) -> str:
    """获取风险等级标签"""
    labels = {
        "minimal": "风险极低",
        "low": "风险较低",
        "medium": "风险中等",
        "high": "风险较高",
    }
    return labels.get(risk_level, risk_level)


def _generate_recommendations(
    issues: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
) -> List[str]:
    """生成改进建议"""
    recommendations = []

    # 从issues和risks中提取建议
    all_items = issues + risks
    suggestion_set = set()

    for item in all_items:
        suggestion = item.get("suggestion")
        if suggestion and suggestion not in suggestion_set:
            suggestion_set.add(suggestion)
            recommendations.append(suggestion)

    # 如果没有具体建议，添加通用建议
    if not recommendations:
        if not issues and not risks:
            recommendations.append("架构审查通过，可以开始写作")
        else:
            recommendations.append("建议根据上述问题进行相应调整")

    return recommendations


def _build_summary(
    issues: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    risk_level: str,
) -> str:
    """构建审查摘要"""
    error_count = len([i for i in issues if i.get("level") == "error"])
    warning_count = len([i for i in issues if i.get("level") == "warning"])
    info_count = len([i for i in issues if i.get("level") == "info"]) + len(risks)

    parts = []
    if error_count > 0:
        parts.append(f"{error_count}个错误")
    if warning_count > 0:
        parts.append(f"{warning_count}个警告")
    if info_count > 0:
        parts.append(f"{info_count}条提示")

    if parts:
        issue_summary = "、".join(parts)
        return f"架构审查发现 {issue_summary}，风险等级：{_get_risk_label(risk_level)}"
    else:
        return "架构审查通过，未发现问题"
