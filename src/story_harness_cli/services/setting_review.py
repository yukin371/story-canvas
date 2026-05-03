"""
设定级审查服务 - Setting-Level Review Service
检查设定完善度、一致性和与核心承诺的契合度
"""

from typing import Any, Dict, List


def review_setting(
    state: Dict[str, Any],
    strictness: str = "standard",  # "minimal" | "standard" | "strict"
) -> Dict[str, Any]:
    """
    审查设定完善度
    Review setting completeness
    """
    project = state.get("project", {})
    worldbook = state.get("worldbook", {})
    world = state.get("world", {})
    entities = state.get("entities", {}).get("entities", [])
    story_contract = project.get("storyContract", {})
    story_template = project.get("storyTemplate", {})

    issues = []
    scores = {}

    # 1. 检查世界规则完善度
    world_rules = worldbook.get("worldRules", [])
    world_rules_score = _check_world_rules_completeness(
        world_rules, story_template, strictness
    )
    scores["worldRules"] = world_rules_score

    if world_rules_score["score"] < 10:
        issues.append({
            "level": "error" if strictness == "strict" else "warning",
            "category": "setting-completeness",
            "message": f"世界规则不足（当前{world_rules_score['actual']}条）",
            "suggestion": "运行 `setting expand --target worldbook --focus worldRules` 补充世界规则",
        })

    # 2. 检查设定与核心承诺的一致性
    consistency_score = _check_setting_promise_consistency(
        worldbook, entities, story_contract
    )
    scores["promiseConsistency"] = consistency_score

    if consistency_score["score"] < 12:
        issues.append({
            "level": "warning",
            "category": "setting-consistency",
            "message": "设定与核心承诺可能存在偏差",
            "details": consistency_score.get("mismatches", []),
            "suggestion": "检查设定是否真正支撑了核心承诺",
        })

    # 3. 检查角色设定完善度
    character_score = _check_character_completeness(
        entities, story_template, strictness
    )
    scores["characters"] = character_score

    if character_score["score"] < 10:
        issues.append({
            "level": "warning",
            "category": "character-completeness",
            "message": f"角色设定不够完善（{character_score['complete_count']}/{character_score['total_count']}）",
            "suggestion": "为角色添加详细的背景、性格、动机等设定",
        })

    # 4. 检查势力设定完善度
    factions = worldbook.get("factions", [])
    faction_score = _check_faction_completeness(
        factions, story_template, strictness
    )
    scores["factions"] = faction_score

    # 5. 检查世界设定项
    world_items = world.get("items", [])
    items_score = _check_world_items_completeness(
        world_items, story_template, strictness
    )
    scores["worldItems"] = items_score

    # 计算总分
    total_score = sum(s["score"] for s in scores.values()) / len(scores) if scores else 0

    return {
        "overallScore": total_score,
        "strictness": strictness,
        "scores": scores,
        "issues": issues,
        "ready": total_score >= 12 and len([i for i in issues if i["level"] == "error"]) == 0,
        "summary": _build_review_summary(total_score, len(issues)),
        "recommendations": _build_recommendations(issues),
    }


def _check_world_rules_completeness(
    world_rules: List[Dict[str, Any]],
    story_template: Dict[str, Any],
    strictness: str,
) -> Dict[str, Any]:
    """检查世界规则完善度"""
    module_policy = story_template.get("modulePolicy", {})
    required = module_policy.get("worldRules") == "required"

    if not required:
        return {"score": 15, "required": 0, "actual": len(world_rules)}

    required_count = 3 if strictness == "standard" else (5 if strictness == "strict" else 1)
    actual_count = len(world_rules)

    # 检查规则质量
    quality_score = 0
    for rule in world_rules:
        rule_text = rule.get("rule", "")
        if rule_text and len(rule_text) > 30:
            quality_score += 3
        elif rule_text:
            quality_score += 1

    # 计算分数
    if actual_count >= required_count:
        count_score = 15
    elif actual_count >= required_count * 0.7:
        count_score = 10
    else:
        count_score = 5

    final_score = min(15, count_score + quality_score / 2)

    return {
        "score": final_score,
        "required": required_count,
        "actual": actual_count,
        "quality": quality_score,
    }


def _check_setting_promise_consistency(
    worldbook: Dict[str, Any],
    entities: List[Dict[str, Any]],
    story_contract: Dict[str, Any],
) -> Dict[str, Any]:
    """检查设定与核心承诺的一致性"""
    core_promises = story_contract.get("corePromises", [])
    world_rules = worldbook.get("worldRules", [])

    mismatches = []

    if not core_promises:
        return {"score": 15, "mismatches": []}

    if not world_rules:
        return {
            "score": 5,
            "mismatches": [{"promise": p, "issue": "缺少世界规则"} for p in core_promises],
        }

    # 检查每个承诺是否有对应规则支撑
    for promise in core_promises:
        supported = False
        for rule in world_rules:
            if _rule_supports_promise(rule, promise):
                supported = True
                break

        if not supported:
            mismatches.append({
                "promise": promise,
                "issue": "缺少对应的世界规则支撑",
            })

    # 计算分数
    if not mismatches:
        score = 15
    elif len(mismatches) < len(core_promises) * 0.5:
        score = 10
    else:
        score = 6

    return {"score": score, "mismatches": mismatches}


def _rule_supports_promise(rule: Dict[str, Any], promise: str) -> bool:
    """检查规则是否支撑承诺"""
    rule_text = rule.get("rule", "").lower()
    promise_lower = promise.lower()

    # 简单的关键词匹配
    promise_keywords = [k for k in promise_lower.split() if len(k) > 2]
    for keyword in promise_keywords:
        if keyword in rule_text:
            return True

    return False


def _check_character_completeness(
    entities: List[Dict[str, Any]],
    story_template: Dict[str, Any],
    strictness: str,
) -> Dict[str, Any]:
    """检查角色设定完善度"""
    characters = [e for e in entities if e.get("kind") == "character"]

    if not characters:
        return {"score": 0, "complete_count": 0, "total_count": 0}

    complete_count = 0
    for char in characters:
        brief = char.get("brief", "")
        if brief and len(brief) >= 20:
            complete_count += 1

    # 计算分数
    completeness_ratio = complete_count / len(characters) if characters else 0
    base_score = int(completeness_ratio * 15)

    # 根据严格度调整
    required_ratio = 0.5 if strictness == "standard" else (0.8 if strictness == "strict" else 0.3)
    if completeness_ratio >= required_ratio:
        score = base_score
    else:
        score = max(5, base_score - 3)

    return {
        "score": score,
        "complete_count": complete_count,
        "total_count": len(characters),
    }


def _check_faction_completeness(
    factions: List[Dict[str, Any]],
    story_template: Dict[str, Any],
    strictness: str,
) -> Dict[str, Any]:
    """检查势力设定完善度"""
    if not factions:
        return {"score": 15, "count": 0}  # 势力是可选的

    # 检查势力设定质量
    complete_count = 0
    for faction in factions:
        if faction.get("name") and faction.get("brief"):
            complete_count += 1

    completeness_ratio = complete_count / len(factions) if factions else 0
    score = int(completeness_ratio * 15)

    return {
        "score": score,
        "count": len(factions),
        "complete_count": complete_count,
    }


def _check_world_items_completeness(
    world_items: List[Dict[str, Any]],
    story_template: Dict[str, Any],
    strictness: str,
) -> Dict[str, Any]:
    """检查世界设定项完善度"""
    required_count = 3 if strictness == "standard" else (5 if strictness == "strict" else 1)
    actual_count = len(world_items)

    if actual_count >= required_count:
        score = 15
    elif actual_count >= required_count * 0.6:
        score = 10
    else:
        score = 6

    return {
        "score": score,
        "required": required_count,
        "actual": actual_count,
    }


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
        return f"设定审查通过，质量{quality}"
    else:
        return f"设定审查发现{issue_count}个问题，质量{quality}"


def _build_recommendations(issues: List[Dict[str, Any]]) -> List[str]:
    """构建改进建议"""
    recommendations = []

    for issue in issues:
        suggestion = issue.get("suggestion")
        if suggestion and suggestion not in recommendations:
            recommendations.append(suggestion)

    # 如果没有具体建议，添加通用建议
    if not recommendations:
        recommendations.append("设定审查通过，可以继续写作")

    return recommendations
