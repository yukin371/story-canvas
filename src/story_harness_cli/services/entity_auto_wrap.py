"""
实体资产自动包裹服务 - Entity Auto-Wrap Service
基于Agent预先构建的资产库自动添加@{}包裹
"""

from typing import Any, Dict, List, Tuple, Set
import re
from pathlib import Path


class Entity:
    """实体资产"""
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.aliases = data.get("aliases", [])
        self.kind = data.get("kind", "")
        self.brief = data.get("brief", "")
        self.pronoun = self._get_pronoun()

    def _get_pronoun(self) -> str:
        """获取代词"""
        if self.kind == "character":
            # 从brief或其他字段推断
            return "他"  # 简化处理
        return ""

    def all_names(self) -> List[str]:
        """获取所有可能的名称"""
        names = [self.name]
        names.extend(self.aliases)
        return list(set(names))


class EntityIndex:
    """实体名称索引"""

    def __init__(self):
        self.canonical_names: Dict[str, Entity] = {}
        self.aliases: Dict[str, Entity] = {}
        self.pronouns: Dict[str, Entity] = {}
        self.context_entities: List[Entity] = []  # 当前活跃实体

    def add_entity(self, entity: Entity) -> None:
        """添加实体到索引"""
        # 添加标准名称
        if entity.name:
            self.canonical_names[entity.name] = entity

        # 添加别名
        for alias in entity.aliases:
            if alias:
                self.aliases[alias] = entity

        # 添加代词（需要上下文）
        if entity.pronoun:
            self.pronouns[entity.pronoun] = entity

    def find_entity(self, name: str) -> Entity | None:
        """查找实体"""
        # 优先查找标准名称
        if name in self.canonical_names:
            return self.canonical_names[name]

        # 查找别名
        if name in self.aliases:
            return self.aliases[name]

        # 查找代词（需要上下文判断）
        if name in self.pronouns and len(self.context_entities) == 1:
            return self.pronouns[name]

        return None

    def set_context_entities(self, entities: List[Entity]) -> None:
        """设置当前上下文中的活跃实体"""
        self.context_entities = entities


def build_entity_index(state: Dict[str, Any]) -> EntityIndex:
    """构建实体名称索引"""
    index = EntityIndex()

    # 加载角色实体
    entities = state.get("entities", {}).get("entities", [])
    for entity_data in entities:
        entity = Entity(entity_data)
        index.add_entity(entity)

    # 加载势力实体
    world = state.get("world", {})
    factions = world.get("factions", [])
    for faction_data in factions:
        entity = Entity(faction_data)
        index.add_entity(entity)

    # 加载地点实体
    locations = world.get("locations", [])
    for location_data in locations:
        entity = Entity(location_data)
        index.add_entity(entity)

    return index


def split_sentences(text: str) -> List[str]:
    """分割句子"""
    # 中文句子分割
    sentences = re.split(r'([。！？；\n])', text)

    # 重组句子（保留标点）
    result = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
            if sentence.strip():
                result.append(sentence.strip())

    return result


def match_entities_in_sentence(
    sentence: str,
    entity_index: EntityIndex,
    max_entities: int = 10
) -> List[Dict[str, Any]]:
    """在句子中匹配实体"""
    matches = []
    matched_names = set()

    # 按长度降序排序实体名称（优先匹配长名称）
    all_entities = []
    for entity in set(entity_index.canonical_names.values()):
        for name in entity.all_names():
            all_entities.append((name, entity))

    all_entities.sort(key=lambda x: len(x[0]), reverse=True)

    # 查找实体
    for name, entity in all_entities:
        if len(matches) >= max_entities:
            break

        if name in matched_names:
            continue

        # 检查是否已经包裹
        wrapped_pattern = f"@{{{name}}}"
        if wrapped_pattern in sentence:
            matched_names.add(name)
            continue

        # 检查是否在文本中
        if name in sentence:
            matches.append({
                "entity": entity,
                "name": name,
                "position": sentence.find(name),
                "wrapped": False
            })
            matched_names.add(name)

    return matches


def apply_wraps(sentence: str, matches: List[Dict[str, Any]]) -> str:
    """应用@{}包裹"""
    if not matches:
        return sentence

    # 按位置排序（从后往前替换，避免位置偏移）
    sorted_matches = sorted(matches, key=lambda x: x["position"], reverse=True)

    result = sentence
    for match in sorted_matches:
        name = match["name"]
        entity = match["entity"]

        # 使用标准名称包裹
        canonical_name = entity.name
        old_text = name
        new_text = f"@{{{canonical_name}}}"

        result = result[:match["position"]] + new_text + result[match["position"] + len(name):]

    return result


def auto_wrap_entities(
    chapter_text: str,
    entity_index: EntityIndex,
    context: Dict[str, Any] | None = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """自动包裹实体"""
    context = context or {}

    # 1. 分割句子
    sentences = split_sentences(chapter_text)

    # 2. 设置当前活跃实体
    active_entities = context.get("activeEntities", [])
    entity_index.set_context_entities([Entity(e) for e in active_entities])

    # 3. 为每个句子进行实体匹配
    wrapped_sentences = []
    all_matches = []

    for sentence in sentences:
        # 跳过对话和特殊格式
        if should_skip_sentence(sentence):
            wrapped_sentences.append(sentence)
            continue

        # 匹配实体
        matches = match_entities_in_sentence(sentence, entity_index)

        # 应用包裹
        if matches:
            wrapped_sentence = apply_wraps(sentence, matches)
            wrapped_sentences.append(wrapped_sentence)
            all_matches.extend(matches)
        else:
            wrapped_sentences.append(sentence)

    wrapped_text = "\n".join(wrapped_sentences)

    # 4. 生成包裹报告
    wrap_report = generate_wrap_report(all_matches, chapter_text, wrapped_text)

    return wrapped_text, wrap_report


def should_skip_sentence(sentence: str) -> bool:
    """判断是否应该跳过该句子"""
    # 跳过对话
    if sentence.startswith('"') or sentence.startswith('"'):
        return True

    # 跳过诗词
    if len(sentence) < 5 or sentence.count('，') == 0:
        # 可能是诗词
        if any(c in sentence for c in '，。？！'):
            return False
        # 短句可能需要检查
        return False

    return False


def generate_wrap_report(
    matches: List[Dict[str, Any]],
    original_text: str,
    wrapped_text: str
) -> List[Dict[str, Any]]:
    """生成包裹报告"""
    report = []

    # 统计每种类型的实体
    entity_types = {}
    for match in matches:
        entity = match["entity"]
        kind = entity.kind
        if kind not in entity_types:
            entity_types[kind] = []
        entity_types[kind].append({
            "name": entity.name,
            "matchedAs": match["name"]
        })

    # 生成报告
    for kind, entities in entity_types.items():
        report.append({
            "type": kind,
            "count": len(entities),
            "entities": entities
        })

    return report


def detect_already_wrapped(text: str, entity_index: EntityIndex) -> List[str]:
    """检测已经包裹的实体"""
    already_wrapped = set()

    # 查找所有@{}包裹
    pattern = r'@\{([^}]+)\}'
    matches = re.findall(pattern, text)

    for match in matches:
        entity = entity_index.find_entity(match)
        if entity:
            already_wrapped.add(match)

    return list(already_wrapped)


def count_unwrapped_entities(
    text: str,
    entity_index: EntityIndex
) -> Dict[str, int]:
    """统计未包裹的实体"""
    # 移除所有已包裹的实体
    text_without_wrapped = re.sub(r'@\{[^}]+\}', '', text)

    # 统计未包裹的出现次数
    unwrapped_counts = {}

    for entity in set(entity_index.canonical_names.values()):
        for name in entity.all_names():
            if name in text_without_wrapped:
                count = text_without_wrapped.count(name)
                if count > 0:
                    unwrapped_counts[entity.name] = unwrapped_counts.get(entity.name, 0) + count

    return unwrapped_counts
