"""
设定扩展服务 - 支持渐进式设定扩展
Setting Expansion Service - Support progressive setting expansion
"""

import json
from copy import deepcopy
from typing import Any, Dict, List, Optional

from story_harness_cli.data.genre_templates import GENRE_TEMPLATES


def default_genre_templates() -> Dict[str, Any]:
    """Return builtin genre templates without exposing mutable module state."""
    return deepcopy(GENRE_TEMPLATES)


def get_genre_template(genre: str, templates: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """获取特定类型的模板"""
    genres = (templates or GENRE_TEMPLATES).get("genres", {})
    return genres.get(genre)


def list_available_genres(templates: Optional[Dict[str, Any]] = None) -> List[str]:
    """列出所有可用的类型"""
    return list((templates or GENRE_TEMPLATES).get("genres", {}).keys())


def get_expansion_stage(
    genre: str,
    stage: int,
    templates: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """获取特定扩展阶段的指导"""
    template = get_genre_template(genre, templates)
    if not template:
        return None

    stages = template.get("expansion_stages", [])
    for stage_data in stages:
        if stage_data.get("stage") == stage:
            return stage_data
    return None


def assess_setting_readiness(
    state: Dict[str, Any],
    templates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    评估设定完备性
    Assess setting completeness
    """
    project = state.get("project", {})
    outline = state.get("outline", {})
    world = state.get("worldbook", {}) or state.get("world", {})
    entity_state = state.get("entities", {})

    issues = []
    warnings = []
    score = 0
    max_score = 0

    # 检查基础设定 (权重: 30%)
    max_score += 30
    world_items = _collect_world_items(world)
    if len(world_items) == 0:
        issues.append("缺少任何世界设定项")
    elif len(world_items) < 3:
        warnings.append("世界设定项较少，建议至少包含3个核心设定")
        score += 10
    else:
        score += 20

    # 检查角色设定 (权重: 25%)
    max_score += 25
    entities = entity_state.get("entities", [])
    characters = [
        entity
        for entity in entities
        if isinstance(entity, dict) and entity.get("type", "character") == "character"
    ]
    if len(characters) == 0:
        issues.append("缺少角色设定")
    elif len(characters) < 2:
        warnings.append("角色较少，故事可能缺乏冲突")
        score += 10
    else:
        score += 20

    # 检查大纲完备性 (权重: 25%)
    max_score += 25
    volumes = outline.get("volumes", [])
    if len(volumes) == 0:
        issues.append("缺少卷级结构")
    else:
        has_chapters = any(
            len(vol.get("chapters", [])) > 0
            for vol in volumes
        )
        if not has_chapters:
            warnings.append("卷内缺少章节规划")
            score += 10
        else:
            score += 20

    # 检查核心承诺 (权重: 20%)
    max_score += 20
    story_contract = project.get("storyContract", {})
    core_promises = project.get("corePromises") or story_contract.get("corePromises", [])
    if not core_promises:
        warnings.append("未明确故事的核心承诺")
        score += 5
    else:
        score += 15

    # 计算准备度百分比
    readiness_percent = int((score / max_score) * 100) if max_score > 0 else 0

    # 确定准备度等级
    if readiness_percent >= 80:
        level = "ready"
        level_label = "准备充分"
    elif readiness_percent >= 60:
        level = "adequate"
        level_label = "基本准备"
    elif readiness_percent >= 40:
        level = "needs_work"
        level_label = "需要完善"
    else:
        level = "inadequate"
        level_label = "准备不足"

    return {
        "readinessPercent": readiness_percent,
        "readinessLevel": level,
        "readinessLabel": level_label,
        "score": score,
        "maxScore": max_score,
        "issues": issues,
        "warnings": warnings,
        "recommendations": _generate_recommendations(state, issues, warnings, templates),
    }


def _generate_recommendations(
    state: Dict[str, Any],
    issues: List[str],
    warnings: List[str],
    templates: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """基于问题生成改进建议"""
    recommendations = []
    # 基于问题生成建议
    if "缺少任何世界设定项" in issues:
        recommendations.append("使用 `world add` 命令添加核心世界设定")

    if "缺少角色设定" in issues:
        recommendations.append("使用 `entity create --kind character` 创建主要角色")

    if "缺少卷级结构" in issues:
        recommendations.append("使用 `outline propose` 生成初始大纲结构")

    # 基于警告生成建议
    if "世界设定项较少" in warnings:
        project = state.get("project", {})
        positioning = project.get("positioning", {})
        genre = project.get("genre") or positioning.get("primaryGenre", "")
        if genre:
            template = get_genre_template(genre, templates)
            if template:
                elements = template.get("setting_elements", [])
                recommendations.append(
                    f"根据{template['name']}类型，建议添加设定：{', '.join(elements[:3])}"
                )

    if "角色较少" in warnings:
        recommendations.append("考虑添加反派角色、配角或导师角色")

    if "未明确故事的核心承诺" in warnings:
        recommendations.append("使用 `project edit` 明确故事的核心承诺")

    return recommendations


def build_setting_expansion_prompt(
    state: Dict[str, Any],
    mode: str = "progressive",
    focus_area: Optional[str] = None,
    current_stage: Optional[int] = None,
    templates: Optional[Dict[str, Any]] = None,
) -> str:
    """
    构建设定扩展的AI提示
    Build AI prompt for setting expansion
    """
    project = state.get("project", {})
    world = state.get("worldbook", {}) or state.get("world", {})
    entity_state = state.get("entities", {})
    outline = state.get("outline", {})

    positioning = project.get("positioning", {})
    genre = project.get("genre") or positioning.get("primaryGenre", "")
    title = project.get("title", "未命名项目")
    story_contract = project.get("storyContract", {})
    core_promises = project.get("corePromises") or story_contract.get("corePromises", [])

    # 获取类型模板
    genre_template = None
    if genre:
        genre_template = get_genre_template(genre, templates)

    prompt_parts = []

    # 基础信息
    prompt_parts.append(f"# 项目：{title}")
    if genre:
        prompt_parts.append(f"类型：{genre}")
    if core_promises:
        prompt_parts.append(f"核心承诺：{'；'.join(core_promises)}")

    # 当前设定摘要
    prompt_parts.append("\n## 当前设定")

    world_items = _collect_world_items(world)
    if world_items:
        prompt_parts.append(f"世界设定（{len(world_items)}项）：")
        for item in world_items[:5]:  # 只显示前5项
            prompt_parts.append(f"- {item.get('name', '')}：{item.get('brief', '')[:50]}...")
    else:
        prompt_parts.append("（暂无世界设定）")

    entities = entity_state.get("entities", [])
    characters = [
        entity
        for entity in entities
        if isinstance(entity, dict) and entity.get("type", "character") == "character"
    ]
    if characters:
        prompt_parts.append(f"\n角色（{len(characters)}个）：")
        for char in characters[:5]:
            prompt_parts.append(f"- {char.get('name', '')}：{char.get('brief', '')[:50]}...")
    else:
        prompt_parts.append("\n（暂无角色设定）")

    # 扩展模式
    prompt_parts.append(f"\n## 扩展模式：{mode}")

    if mode == "progressive" and genre_template:
        # 渐进式扩展 - 使用类型模板的阶段
        stage = current_stage or 1
        stage_data = get_expansion_stage(genre, stage, templates)

        if stage_data:
            prompt_parts.append(f"\n### 扩展阶段 {stage}：{stage_data.get('name', '')}")
            prompt_parts.append(f"重点：{stage_data.get('focus', '')}")

            questions = stage_data.get("questions", [])
            if questions:
                prompt_parts.append("\n指导问题：")
                for q in questions:
                    prompt_parts.append(f"- {q}")

            examples = stage_data.get("examples", [])
            if examples:
                prompt_parts.append("\n参考示例：")
                for ex in examples:
                    prompt_parts.append(f"- {ex}")
        else:
            prompt_parts.append(f"\n### 扩展阶段 {stage}")
            prompt_parts.append("（未找到该阶段的模板，请根据类型特性自由扩展）")

    elif mode == "targeted" and focus_area:
        # 目标式扩展 - 针对特定领域
        prompt_parts.append(f"\n### 目标领域：{focus_area}")
        prompt_parts.append(f"请针对'{focus_area}'方面进行深入扩展")

        if genre_template:
            elements = genre_template.get("setting_elements", [])
            relevant_elements = [e for e in elements if focus_area in e]
            if relevant_elements:
                prompt_parts.append("\n相关要素：")
                for elem in relevant_elements:
                    prompt_parts.append(f"- {elem}")

    elif mode == "brainstorm":
        # 头脑风暴模式
        prompt_parts.append("\n### 头脑风暴")
        prompt_parts.append("请基于当前设定，提出创意性的扩展建议")
        prompt_parts.append("可以包括：")
        prompt_parts.append("- 新的设定要素")
        prompt_parts.append("- 现有设定的深化方向")
        prompt_parts.append("- 可能的冲突来源")
        prompt_parts.append("- 有趣的组合或对比")

    # 输出要求
    prompt_parts.append("\n## 输出要求")
    prompt_parts.append("请提供：")
    prompt_parts.append("1. 新设定的名称和简要说明")
    prompt_parts.append("2. 设定在故事中的作用")
    prompt_parts.append("3. 与现有设定的关联")
    prompt_parts.append("4. 可能引发的剧情冲突")
    prompt_parts.append("\n输出格式为JSON，包含以下字段：")
    prompt_parts.append("- suggestions: 数组，每个包含 name, description, purpose, connections, conflicts")

    return "\n".join(prompt_parts)


def parse_setting_expansion_response(response_text: str) -> List[Dict[str, Any]]:
    """
    解析AI返回的设定扩展建议
    Parse AI response for setting expansion suggestions
    """
    import json
    import re

    # 尝试提取JSON
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return data.get("suggestions", [])
        except json.JSONDecodeError:
            pass

    # 如果无法解析JSON，返回空列表
    return []


def suggest_setting_expansions(
    state: Dict[str, Any],
    mode: str = "progressive",
    focus_area: Optional[str] = None,
    current_stage: Optional[int] = None,
    templates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    建议设定扩展
    Suggest setting expansions
    """
    readiness = assess_setting_readiness(state, templates)

    # 如果准备度不足，优先解决基础问题
    if readiness["readinessLevel"] in ["inadequate", "needs_work"]:
        return {
            "status": "low_readiness",
            "readiness": readiness,
            "recommendations": readiness["recommendations"],
            "message": f"设定准备度{readiness['readinessLabel']}，建议先完善基础设定",
        }

    # 构建提示
    prompt = build_setting_expansion_prompt(
        state=state,
        mode=mode,
        focus_area=focus_area,
        current_stage=current_stage,
        templates=templates,
    )

    return {
        "status": "ready",
        "readiness": readiness,
        "prompt": prompt,
        "mode": mode,
        "focusArea": focus_area,
        "currentStage": current_stage,
        "message": f"设定准备度{readiness['readinessLabel']}，可以进行扩展",
    }


def get_next_expansion_stage(
    state: Dict[str, Any],
    templates: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    获取建议的下一个扩展阶段
    Get recommended next expansion stage
    """
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    genre = project.get("genre") or positioning.get("primaryGenre", "")
    if not genre:
        return None

    readiness = assess_setting_readiness(state, templates)

    # 基于准备度建议阶段
    if readiness["readinessLevel"] == "inadequate":
        return 1  # 从基础开始
    elif readiness["readinessLevel"] == "needs_work":
        return 2  # 核心架构
    elif readiness["readinessLevel"] == "adequate":
        return 3  # 深化细节
    else:
        # 检查是否有更多阶段
        template = get_genre_template(genre, templates)
        if template:
            max_stage = len(template.get("expansion_stages", []))
            if max_stage > 3:
                return 4
        return None  # 已完成所有阶段


def validate_setting_for_writing(state: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
    """
    验证设定是否足够支持特定章节的写作
    Validate if setting is sufficient for writing a specific chapter
    """
    outline = state.get("outline", {})
    world = state.get("worldbook", {}) or state.get("world", {})

    # 查找章节
    chapter = None
    for volume in outline.get("volumes", []):
        for ch in volume.get("chapters", []):
            if ch.get("id") == chapter_id:
                chapter = ch
                break
        if chapter:
            break

    if not chapter:
        return {
            "valid": False,
            "error": f"章节 {chapter_id} 不存在",
        }

    issues = []
    warnings = []

    # 检查章节中提到的实体是否已注册
    chapter_title = chapter.get("title", "")
    chapter_brief = chapter.get("brief", "")

    entities = world.get("entities", {})
    entity_names = set(entities.keys())

    # 简单的实体提及检查（实际应用中可能需要更复杂的NLP）
    missing_entities = []
    for entity_name in entity_names:
        # 这里只是示例，实际需要更好的实体识别
        pass

    if missing_entities:
        warnings.append(f"章节中可能引用了未注册的实体：{', '.join(missing_entities)}")

    # 检查设定覆盖度
    world_items = _collect_world_items(world)
    if len(world_items) < 3:
        issues.append("世界设定较少，可能影响写作丰富度")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "recommendations": issues + warnings,
    }


def _collect_world_items(world: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for key in (
        "items",
        "worldRules",
        "factions",
        "locations",
        "artifacts",
        "mysteries",
        "premiseFacts",
        "powerProgressions",
    ):
        values = world.get(key, [])
        if isinstance(values, list):
            items.extend(item for item in values if isinstance(item, dict))
    return items
