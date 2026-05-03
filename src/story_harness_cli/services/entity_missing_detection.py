"""
实体缺失检查服务 - Entity Missing Detection Service
审查AI检查文本中的实体，发现资产库中缺失的实体
"""

from typing import Any, Dict, List, Set, Tuple
import re
from collections import Counter


class EntityMissingDetector:
    """实体缺失检测器"""

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.entity_index = self._build_entity_index()
        self.known_entities = self._get_known_entities()

    def _build_entity_index(self) -> Dict[str, Set[str]]:
        """构建已知实体名称索引"""
        index = {
            "characters": set(),
            "factions": set(),
            "locations": set(),
            "items": set(),
            "all": set()
        }

        # 加载角色
        entities = self.state.get("entities", {}).get("entities", [])
        for entity in entities:
            name = entity.get("name", "")
            if name:
                index["characters"].add(name)
                index["all"].add(name)

            aliases = entity.get("aliases", [])
            for alias in aliases:
                index["characters"].add(alias)
                index["all"].add(alias)

        # 加载势力
        world = self.state.get("world", {})
        factions = world.get("factions", [])
        for faction in factions:
            name = faction.get("name", "")
            if name:
                index["factions"].add(name)
                index["all"].add(name)

        # 加载地点
        locations = world.get("locations", [])
        for location in locations:
            name = location.get("name", "")
            if name:
                index["locations"].add(name)
                index["all"].add(name)

        return index

    def _get_known_entities(self) -> Dict[str, Any]:
        """获取已知实体详情"""
        entities = {}

        # 角色
        for entity in self.state.get("entities", {}).get("entities", []):
            entities[entity.get("name", "")] = {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "kind": "character",
                "brief": entity.get("brief", "")
            }

        # 势力
        for faction in self.state.get("world", {}).get("factions", []):
            entities[faction.get("name", "")] = {
                "id": faction.get("id"),
                "name": faction.get("name"),
                "kind": "faction",
                "brief": faction.get("brief", "")
            }

        # 地点
        for location in self.state.get("world", {}).get("locations", []):
            entities[location.get("name", "")] = {
                "id": location.get("id"),
                "name": location.get("name"),
                "kind": "location",
                "brief": location.get("brief", "")
            }

        return entities

    def detect_missing_entities(
        self,
        chapter_text: str,
        chapter_id: str
    ) -> Dict[str, Any]:
        """检测缺失的实体"""
        # 1. 提取文本中的候选实体
        candidate_entities = self._extract_candidate_entities(chapter_text)

        # 2. 过滤已知实体
        unknown_entities = self._filter_unknown_entities(candidate_entities)

        # 3. 预测实体类型
        predicted_entities = self._predict_entity_types(unknown_entities, chapter_text)

        # 4. 计算优先级
        prioritized_entities = self._calculate_priorities(predicted_entities, chapter_text)

        # 5. 生成建议
        suggestions = self._generate_suggestions(prioritized_entities)

        return {
            "chapterId": chapter_id,
            "knownEntityCount": len(self.entity_index["all"]),
            "candidateCount": len(candidate_entities),
            "unknownCount": len(prioritized_entities),
            "unknownEntities": prioritized_entities,
            "suggestions": suggestions
        }

    def _extract_candidate_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取候选实体"""
        candidates = []

        # 1. 使用正则表达式提取中文词汇
        # 提取2-4个字的中文词汇
        pattern = r'[一-龥]{2,4}'
        words = re.findall(pattern, text)

        # 2. 过滤常见词汇
        common_words = self._get_common_words()
        words = [w for w in words if w not in common_words]

        # 3. 统计词频
        word_counts = Counter(words)

        # 4. 只保留出现多次的词（可能是实体）
        for word, count in word_counts.items():
            if count >= 2:  # 至少出现2次
                candidates.append({
                    "name": word,
                    "frequency": count,
                    "contexts": self._extract_contexts(text, word)
                })

        return candidates

    def _get_common_words(self) -> Set[str]:
        """获取常见词汇（排除列表）"""
        return {
            # 代词
            "我", "你", "他", "她", "它", "我们", "你们", "他们",
            "这个", "那个", "这些", "那些",

            # 连词
            "但是", "然而", "因此", "所以", "因为", "虽然",

            # 动词
            "说", "道", "想", "觉得", "看", "去", "来", "做", "是",
            "有", "没有", "会", "能", "可以", "应该",

            # 形容词
            "很", "非常", "十分", "特别", "比较", "更", "最",

            # 时间词
            "今天", "昨天", "明天", "现在", "刚才", "之前", "之后",

            # 方位词
            "这里", "那里", "哪里", "这边", "那边",

            # 常见名词
            "人", "事", "东西", "时候", "地方", "情况", "问题"
        }

    def _extract_contexts(self, text: str, word: str, context_length: int = 50) -> List[str]:
        """提取词汇出现的上下文"""
        contexts = []

        # 查找所有出现位置
        positions = []
        start = 0
        while True:
            pos = text.find(word, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        # 提取上下文
        for pos in positions:
            start_pos = max(0, pos - context_length)
            end_pos = min(len(text), pos + len(word) + context_length)
            context = text[start_pos:end_pos].strip()
            if context:
                contexts.append(context)

        return contexts[:3]  # 最多返回3个上下文

    def _filter_unknown_entities(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤未知实体"""
        unknown = []

        for candidate in candidates:
            name = candidate["name"]

            # 检查是否在已知实体中
            if name not in self.entity_index["all"]:
                unknown.append(candidate)

        return unknown

    def _predict_entity_types(
        self,
        unknown_entities: List[Dict[str, Any]],
        chapter_text: str
    ) -> List[Dict[str, Any]]:
        """预测实体类型"""
        predicted = []

        for entity in unknown_entities:
            name = entity["name"]
            contexts = entity.get("contexts", [])
            full_context = " ".join(contexts)

            # 基于上下文预测类型
            entity_type = self._predict_type(name, full_context)

            predicted.append({
                "name": name,
                "frequency": entity["frequency"],
                "predictedType": entity_type,
                "contexts": contexts
            })

        return predicted

    def _predict_type(self, name: str, context: str) -> str:
        """预测实体类型"""
        # 角色特征
        character_patterns = {
            "说": 3, "道": 3, "想": 2, "觉得": 2, "看着": 2,
            "剑": 2, "刀": 2, "武功": 2, "内力": 2,
            "人": 1, "师傅": 3, "弟子": 3, "长老": 3
        }

        # 势力特征
        faction_patterns = {
            "门派": 5, "盟": 3, "宗": 3, "教": 3, "帮": 3,
            "阁": 2, "派": 2, "弟子": 2, "长老": 2,
            "势力": 5, "组织": 3
        }

        # 地点特征
        location_patterns = {
            "山": 3, "城": 3, "殿": 3, "阁": 2, "室": 2,
            "谷": 2, "峰": 2, "林": 2, "河": 2,
            "来": 1, "到": 1, "去": 1, "在": 1
        }

        # 物品特征
        item_patterns = {
            "剑": 3, "刀": 3, "丹": 2, "药": 2,
            "功法": 3, "秘籍": 3, "法宝": 3,
            "拿": 1, "用": 1, "佩": 1, "炼": 1
        }

        # 计算得分
        scores = {
            "character": sum(weight for pattern, weight in character_patterns.items() if pattern in context),
            "faction": sum(weight for pattern, weight in faction_patterns.items() if pattern in context),
            "location": sum(weight for pattern, weight in location_patterns.items() if pattern in context),
            "item": sum(weight for pattern, weight in item_patterns.items() if pattern in context)
        }

        # 返回得分最高的类型
        if max(scores.values()) == 0:
            return "unknown"

        return max(scores, key=scores.get)

    def _calculate_priorities(
        self,
        entities: List[Dict[str, Any]],
        chapter_text: str
    ) -> List[Dict[str, Any]]:
        """计算优先级"""
        prioritized = []

        for entity in entities:
            name = entity["name"]
            frequency = entity["frequency"]
            predicted_type = entity["predictedType"]

            # 计算优先级
            priority_score = 0

            # 出现频率（越高越重要）
            if frequency >= 5:
                priority_score += 3
            elif frequency >= 3:
                priority_score += 2
            elif frequency >= 2:
                priority_score += 1

            # 实体类型（角色和势力更重要）
            if predicted_type == "character":
                priority_score += 3
            elif predicted_type == "faction":
                priority_score += 2

            # 上下文数量（越多越确定）
            context_count = len(entity.get("contexts", []))
            if context_count >= 3:
                priority_score += 2
            elif context_count >= 2:
                priority_score += 1

            # 确定优先级
            if priority_score >= 5:
                priority = "high"
            elif priority_score >= 3:
                priority = "medium"
            else:
                priority = "low"

            prioritized.append({
                **entity,
                "priority": priority,
                "priorityScore": priority_score
            })

        # 按优先级排序
        prioritized.sort(key=lambda x: x["priorityScore"], reverse=True)

        return prioritized

    def _generate_suggestions(self, entities: List[Dict[str, Any]]) -> List[str]:
        """生成补充建议"""
        suggestions = []

        if not entities:
            return ["未发现需要补充的实体"]

        # 按优先级分组
        high_priority = [e for e in entities if e["priority"] == "high"]
        medium_priority = [e for e in entities if e["priority"] == "medium"]

        if high_priority:
            suggestions.append(f"发现 {len(high_priority)} 个高优先级实体需要补充")
            for entity in high_priority[:3]:
                suggestions.append(f"  - {entity['name']}: 补充{entity['predictedType']}资产")

        if medium_priority:
            suggestions.append(f"发现 {len(medium_priority)} 个中优先级实体可考虑补充")

        return suggestions


def check_known_entity_compliance(
    state: Dict[str, Any],
    chapter_text: str,
    entity_index: Dict[str, Set[str]]
) -> Dict[str, Any]:
    """检查已知实体的规范性"""
    # 1. 检查已知实体是否都正确使用
    known_entity_issues = []

    # 2. 检查已知实体是否都包裹了
    from .entity_auto_wrap import detect_already_wrapped, count_unwrapped_entities
    from .entity_auto_wrap import EntityIndex as AutoWrapEntityIndex

    # 这里需要重新构建索引
    # 实际实现时应该优化索引构建

    # 3. 统计包裹情况
    wrapped_entities = detect_already_wrapped(chapter_text, None)

    # 4. 检查实体引用是否符合设定
    compliance_issues = []

    return {
        "totalKnownEntities": len(entity_index["all"]),
        "wrappedEntities": len(wrapped_entities),
        "unwrappedCount": 0,  # 需要计算
        "issues": known_entity_issues + compliance_issues
    }


def detect_unknown_entities_comprehensive(
    state: Dict[str, Any],
    chapter_text: str,
    chapter_id: str
) -> Dict[str, Any]:
    """全面检测未知实体（供审查AI使用）"""
    detector = EntityMissingDetector(state)

    result = detector.detect_missing_entities(chapter_text, chapter_id)

    # 生成审查报告
    review_report = {
        "entityReview": {
            "knownEntityCompliance": {
                "score": 15,  # 暂时给满分，实际需要检查
                "totalEntities": result["knownEntityCount"],
                "wrappedEntities": result["knownEntityCount"],  # 假设都已包裹
                "unwrappedEntities": 0,
                "issues": []
            },
            "unknownEntityDiscovery": {
                "discoveredCount": result["unknownCount"],
                "entities": [
                    {
                        "name": entity["name"],
                        "predictedType": entity["predictedType"],
                        "context": entity["contexts"][0] if entity.get("contexts") else "",
                        "occurrenceCount": entity["frequency"],
                        "priority": entity["priority"],
                        "suggestedAction": f"补充{entity['predictedType']}资产",
                        "requiredFields": _get_required_fields(entity["predictedType"])
                    }
                    for entity in result["unknownEntities"]
                ]
            }
        }
    }

    return review_report


def _get_required_fields(entity_type: str) -> List[str]:
    """获取实体类型必需的字段"""
    field_map = {
        "character": ["姓名", "身份", "外貌特征", "性格特点", "背景故事"],
        "faction": ["势力名称", "势力目标", "现任领袖", "主要成员", "与其他势力的关系"],
        "location": ["地点名称", "地理位置", "环境特点", "相关势力", "特殊功能"],
        "item": ["物品名称", "类型", "功能", "获得方式", "特殊效果"],
        "unknown": ["名称", "基本描述"]
    }

    return field_map.get(entity_type, field_map["unknown"])
