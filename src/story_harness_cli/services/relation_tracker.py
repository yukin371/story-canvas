"""
关系追踪服务 - Relationship Tracker Service
自动检测和追踪角色关系变化
"""

from typing import Any, Dict, List
import re


def track_relation_changes(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    auto_detect: bool = True,
) -> Dict[str, Any]:
    """
    追踪角色关系变化
    Track character relationship changes
    """
    entities = state.get("entities", {}).get("entities", [])
    relation_projections = state.get("projection", {}).get("relationProjections", [])

    # 自动检测关系变化
    detected_changes = []
    if auto_detect:
        detected_changes = _detect_relation_changes(
            entities, relation_projections, chapter_text, chapter_id
        )

    # 生成关系追踪报告
    return {
        "chapterId": chapter_id,
        "detectedChanges": detected_changes,
        "changeCount": len(detected_changes),
        "relationHistory": _build_relation_history(relation_projections),
        "suggestions": _generate_relation_suggestions(detected_changes),
    }


def _detect_relation_changes(
    entities: List[Dict[str, Any]],
    relation_projections: List[Dict[str, Any]],
    chapter_text: str,
    chapter_id: str,
) -> List[Dict[str, Any]]:
    """自动检测关系变化"""
    # 提取章节中出现的角色对
    character_pairs = _extract_character_pairs_from_text(chapter_text, entities)

    changes = []
    for pair in character_pairs:
        from_id = pair["from"]
        to_id = pair["to"]

        # 查找现有关系
        existing = _find_relation(relation_projections, from_id, to_id)

        # 分析当前章节的关系表现
        current_analysis = _analyze_relation_in_chapter(
            chapter_text, pair, entities
        )

        if existing:
            # 检查关系是否变化
            if _is_relation_changed(existing, current_analysis):
                changes.append({
                    "type": "relation-change",
                    "fromId": from_id,
                    "toId": to_id,
                    "fromName": _get_entity_name(entities, from_id),
                    "toName": _get_entity_name(entities, to_id),
                    "previousLabel": existing.get("label", ""),
                    "currentLabel": current_analysis["label"],
                    "changeType": _classify_relation_change(
                        existing.get("label", ""),
                        current_analysis["label"]
                    ),
                    "evidence": current_analysis.get("evidence", []),
                    "confidence": current_analysis.get("confidence", 0.5),
                    "suggestedAction": "update-relation",
                })
        else:
            # 新发现的关系
            if current_analysis.get("confidence", 0) > 0.6:
                changes.append({
                    "type": "new-relation",
                    "fromId": from_id,
                    "toId": to_id,
                    "fromName": _get_entity_name(entities, from_id),
                    "toName": _get_entity_name(entities, to_id),
                    "suggestedLabel": current_analysis["label"],
                    "evidence": current_analysis.get("evidence", []),
                    "confidence": current_analysis.get("confidence", 0.5),
                    "suggestedAction": "add-relation",
                })

    return changes


def _extract_character_pairs_from_text(
    chapter_text: str,
    entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """从文本中提取角色对"""
    characters = [e for e in entities if e.get("kind") == "character"]

    # 找出文本中出现的角色
    mentioned_characters = []
    for char in characters:
        name = char.get("name", "")
        if name and name in chapter_text:
            mentioned_characters.append(char)

    # 生成所有可能的角色对
    pairs = []
    for i, char1 in enumerate(mentioned_characters):
        for char2 in mentioned_characters[i + 1:]:
            pairs.append({
                "from": char1.get("id"),
                "to": char2.get("id"),
                "fromName": char1.get("name"),
                "toName": char2.get("name"),
            })

    return pairs


def _find_relation(
    relation_projections: List[Dict[str, Any]],
    from_id: str,
    to_id: str,
) -> Dict[str, Any] | None:
    """查找现有关系"""
    for relation in relation_projections:
        if (relation.get("fromId") == from_id and relation.get("toId") == to_id) or \
           (relation.get("fromId") == to_id and relation.get("toId") == from_id):
            return relation
    return None


def _analyze_relation_in_chapter(
    chapter_text: str,
    pair: Dict[str, Any],
    entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """分析章节中的关系表现"""
    from_name = pair["fromName"]
    to_name = pair["toName"]

    # 查找两个角色共同出现的句子
    sentences = _split_sentences(chapter_text)
    co_occurrence_sentences = [
        s for s in sentences
        if from_name in s and to_name in s
    ]

    if not co_occurrence_sentences:
        return {"label": "", "confidence": 0, "evidence": []}

    # 分析关系类型
    relation_keywords = {
        "friend": ["朋友", "好友", "伙伴", "盟友", "友谊"],
        "enemy": ["敌人", "敌对", "仇人", "对手", "敌意"],
        "love": ["爱", "喜欢", "恋人", "情侣", "心动"],
        "family": ["家人", "父子", "母女", "兄弟", "姐妹", "亲情"],
        "master": ["师父", "老师", "师傅", "导师", "徒弟"],
        "betrayal": ["背叛", "欺骗", "出卖", "背信"],
    }

    # 统计关键词出现次数
    keyword_counts = {}
    for relation_type, keywords in relation_keywords.items():
        count = 0
        for sentence in co_occurrence_sentences:
            for keyword in keywords:
                if keyword in sentence:
                    count += 1
        if count > 0:
            keyword_counts[relation_type] = count

    # 确定关系类型
    if keyword_counts:
        max_type = max(keyword_counts, key=keyword_counts.get)
        label = _get_relation_label(max_type)
        confidence = min(1.0, keyword_counts[max_type] / len(co_occurrence_sentences))
    else:
        # 基于上下文推断
        label = _infer_relation_from_context(co_occurrence_sentences)
        confidence = 0.4

    # 提取证据
    evidence = co_occurrence_sentences[:3]  # 最多3条证据

    return {
        "label": label,
        "confidence": confidence,
        "evidence": evidence,
    }


def _split_sentences(text: str) -> List[str]:
    """分割句子"""
    # 简单的句子分割
    sentences = re.split(r'[。！？；]', text)
    return [s.strip() for s in sentences if s.strip()]


def _get_relation_label(relation_type: str) -> str:
    """获取关系标签"""
    labels = {
        "friend": "朋友",
        "enemy": "敌对",
        "love": "恋人",
        "family": "家人",
        "master": "师徒",
        "betrayal": "背叛",
    }
    return labels.get(relation_type, "其他")


def _infer_relation_from_context(sentences: List[str]) -> str:
    """从上下文推断关系"""
    # 简单的推断：如果共同出现且有动作，可能是互动关系
    action_keywords = ["打", "杀", "救", "帮", "攻击", "保护", "说话", "对话"]

    for sentence in sentences:
        for keyword in action_keywords:
            if keyword in sentence:
                return "互动"

    return "其他"


def _is_relation_changed(
    existing: Dict[str, Any],
    current_analysis: Dict[str, Any],
) -> bool:
    """检查关系是否变化"""
    existing_label = existing.get("label", "")
    current_label = current_analysis.get("label", "")

    # 如果当前分析置信度太低，认为没有变化
    if current_analysis.get("confidence", 0) < 0.5:
        return False

    # 检查标签是否不同
    return existing_label != current_label and current_label != ""


def _classify_relation_change(previous_label: str, current_label: str) -> str:
    """分类关系变化类型"""
    if not previous_label or not current_label:
        return "unknown"

    # 敌对关系变化
    if "敌" in previous_label or "对" in previous_label:
        if "友" in current_label or "盟" in current_label:
            return "enemy-to-friend"
        elif "合" in current_label:
            return "enemy-to-cooperation"

    # 友好关系变化
    if "友" in previous_label or "盟" in previous_label:
        if "敌" in current_label or "对" in current_label:
            return "friend-to-enemy"
        elif "背叛" in current_label:
            return "friend-to-betrayal"

    return "other-change"


def _get_entity_name(entities: List[Dict[str, Any]], entity_id: str) -> str:
    """获取实体名称"""
    for entity in entities:
        if entity.get("id") == entity_id:
            return entity.get("name", entity_id)
    return entity_id


def _build_relation_history(relation_projections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """构建关系历史"""
    history = []

    for relation in relation_projections:
        history.append({
            "fromId": relation.get("fromId"),
            "toId": relation.get("toId"),
            "label": relation.get("label"),
            "category": relation.get("category"),
        })

    return history


def _generate_relation_suggestions(changes: List[Dict[str, Any]]) -> List[str]:
    """生成关系建议"""
    suggestions = []

    for change in changes:
        if change["type"] == "new-relation":
            suggestions.append(
                f"发现新关系：{change['fromName']} -> {change['toName']} ({change['suggestedLabel']})"
            )
        elif change["type"] == "relation-change":
            suggestions.append(
                f"关系变化：{change['fromName']} -> {change['toName']} "
                f"从 '{change['previousLabel']}' 变为 '{change['currentLabel']}'"
            )

    if not suggestions:
        suggestions.append("未检测到明显的关系变化")

    return suggestions
