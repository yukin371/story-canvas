from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


STATE_KEYWORDS = {
    "受伤": "受伤",
    "流血": "流血",
    "虚弱": "虚弱",
    "疲惫": "疲惫",
    "愤怒": "愤怒",
    "震惊": "震惊",
    "恐惧": "恐惧",
    "悲伤": "悲伤",
    "开心": "开心",
    "紧张": "紧张",
    "冷静": "冷静",
    "怀疑": "怀疑",
    "信任": "信任",
    "背叛": "背叛",
    "离开": "离开",
    "决裂": "决裂",
}


RELATION_KEYWORDS = {
    "背叛": ("裂痕", "high-risk"),
    "决裂": ("裂痕", "high-risk"),
    "对立": ("对立", "high-risk"),
    "冲突": ("冲突", "suggestion"),
    "争吵": ("冲突", "suggestion"),
    "怀疑": ("信任下降", "high-risk"),
    "信任": ("信任上升", "suggestion"),
    "联手": ("合作", "suggestion"),
    "合作": ("合作", "suggestion"),
    "并肩": ("盟友", "suggestion"),
    "喜欢": ("亲近", "suggestion"),
    "心动": ("亲近", "suggestion"),
}


def paragraphs_from_text(text: str) -> List[str]:
    raw_parts = re.split(r"\n\s*\n", text)
    parts: List[str] = []
    for item in raw_parts:
        normalized = item.strip().lstrip("\ufeff").strip()
        if not normalized:
            continue
        if normalized.startswith("#"):
            continue
        parts.append(normalized)
    return parts


def extract_tag_mentions(text: str) -> List[str]:
    mentions: List[str] = []
    seen = set()

    for name in re.findall(r"@\{([^{}\n]+)\}", text):
        normalized = name.strip()
        if normalized and normalized not in seen:
            mentions.append(normalized)
            seen.add(normalized)

    simple_pattern = re.compile(
        r"@("
        r"[A-Za-z][A-Za-z0-9_-]{0,31}"
        r"|"
        r"[\u4e00-\u9fff·-]{1,12}(?=[\s，。！？、；：“”‘’（）()《》〈〉【】\[\],.!?:;]|$)"
        r")"
    )
    for name in simple_pattern.findall(text):
        normalized = name.strip()
        if normalized and normalized not in seen:
            mentions.append(normalized)
            seen.add(normalized)

    return mentions


def find_malformed_entity_tags(text: str) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    valid_wrapped_name = re.compile(
        r"(?:"
        r"[A-Za-z][A-Za-z0-9_-]{0,31}"
        r"|"
        r"[\u4e00-\u9fff·-]{1,24}"
        r")$"
    )
    cursor = 0
    while True:
        start = text.find("@{", cursor)
        if start < 0:
            break
        end = text.find("}", start + 2)
        newline = text.find("\n", start + 2)
        if end < 0 or (newline >= 0 and newline < end):
            snippet_end = newline if newline >= 0 else min(len(text), start + 40)
            issues.append(
                {
                    "code": "unclosed-wrapped-entity-tag",
                    "snippet": text[start:snippet_end].strip(),
                }
            )
            cursor = start + 2
            continue

        name = text[start + 2 : end].strip()
        if not name:
            issues.append({"code": "empty-wrapped-entity-tag", "snippet": "@{}"})
        elif not valid_wrapped_name.fullmatch(name):
            issues.append(
                {
                    "code": "invalid-wrapped-entity-tag",
                    "snippet": f"@{{{name[:40]}}}",
                    "name": name,
                }
            )
        cursor = end + 1
    return issues


def state_tags_for_paragraph(paragraph: str) -> List[str]:
    kw = _kw_override.get("state", STATE_KEYWORDS) if _kw_override else STATE_KEYWORDS
    labels: List[str] = []
    for keyword, label in kw.items():
        for match in re.finditer(re.escape(keyword), paragraph):
            if not _keyword_is_negated(paragraph, match.start()):
                labels.append(label)
                break
    return labels


def _keyword_is_negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 4) : start]
    return any(prefix.endswith(marker) for marker in ("没有", "未", "并未", "不是", "不再", "无法", "不会", "无"))


def relation_for_paragraph(paragraph: str) -> Tuple[str | None, str]:
    raw = _kw_override.get("relation", RELATION_KEYWORDS) if _kw_override else RELATION_KEYWORDS
    # Normalize: both {k: (label, sev)} and {k: [label, sev]} forms
    for keyword, val in raw.items():
        if keyword in paragraph:
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return val[0], val[1]
            return None, "suggestion"
    return None, "suggestion"


APPEARANCE_KEYWORDS = {
    "长发": "长发",
    "短发": "短发",
    "光头": "光头",
    "马尾": "马尾",
    "白发": "白发",
    "黑发": "黑发",
    "金发": "金发",
    "红发": "红发",
    "灰发": "灰发",
    "银发": "银发",
    "蓝眼睛": "蓝眼睛",
    "琥珀色": "琥珀色眼睛",
    "琥珀色眼睛": "琥珀色眼睛",
    "黑眼睛": "黑眼睛",
    "绿眼睛": "绿眼睛",
    "高个子": "高个子",
    "矮个子": "矮个子",
    "瘦削": "瘦削",
    "魁梧": "魁梧",
    "疤痕": "有疤痕",
    "伤疤": "有疤痕",
    "纹身": "有纹身",
    "胎记": "有胎记",
    "戴眼镜": "戴眼镜",
    "胡子": "有胡子",
    "胡须": "有胡子",
    "络腮胡": "络腮胡",
    "独眼": "独眼",
    "拐杖": "拄拐杖",
    "轮椅": "坐轮椅",
}

ABILITY_KEYWORDS = {
    "格斗": "格斗",
    "拳击": "格斗",
    "刀法": "刀术",
    "剑术": "剑术",
    "枪法": "枪法",
    "射击": "射击",
    "暗器": "暗器",
    "轻功": "轻功",
    "身法": "身法",
    "内力": "内力",
    "法术": "法术",
    "魔法": "魔法",
    "咒语": "咒语",
    "医术": "医术",
    "毒术": "毒术",
    "易容": "易容",
    "潜行": "潜行",
    "破解": "破解",
    "黑客": "黑客",
    "驾驶": "驾驶",
    "骑术": "骑术",
    "游泳": "游泳",
    "追踪": "追踪",
    "推理": "推理",
    "分析": "分析",
    "领导": "领导",
    "口才": "口才",
    "谈判": "谈判",
}


# Module-level keyword override — set once per CLI invocation via set_keywords()
_kw_override: dict | None = None


def set_keywords(kw: dict) -> None:
    """Inject custom keyword tables, replacing built-in defaults.

    Expected keys: state, relation, appearance, ability.
    - state: dict {keyword: label}
    - relation: dict {keyword: [label, severity]}
    - appearance: dict {keyword: label}
    - ability: dict {keyword: label}
    """
    global _kw_override
    _kw_override = kw


def appearance_tags_for_paragraph(paragraph: str) -> List[str]:
    kw = _kw_override.get("appearance", APPEARANCE_KEYWORDS) if _kw_override else APPEARANCE_KEYWORDS
    return [label for keyword, label in kw.items() if keyword in paragraph]


def ability_tags_for_paragraph(paragraph: str) -> List[str]:
    kw = _kw_override.get("ability", ABILITY_KEYWORDS) if _kw_override else ABILITY_KEYWORDS
    return [label for keyword, label in kw.items() if keyword in paragraph]


def strip_markdown(text: str) -> str:
    """Remove markdown formatting for plain-text export.

    Strips: *italic*, **bold**, ***bold-italic***, # headings, --- rules,
    > blockquotes, [link](url), ![alt](img), `inline code`.
    """
    # Bold+italic ***...*** → text
    text = re.sub(r"\*{3}(.+?)\*{3}", r"\1", text)
    # Bold **...** → text
    text = re.sub(r"\*{2}(.+?)\*{2}", r"\1", text)
    # Italic *...* → text
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Headings: # ... → strip the leading #s
    text = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]+(.*)$", r"\1", text, flags=re.MULTILINE)
    # Horizontal rules --- or *** or ___ (3+ chars on own line)
    text = re.sub(r"^[ \t]{0,3}[-*_]{3,}[ \t]*$", "", text, flags=re.MULTILINE)
    # Blockquotes > ...
    text = re.sub(r"^[ \t]{0,3}>[ \t]?", "", text, flags=re.MULTILINE)
    # Links [text](url) → text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Images ![alt](url) → alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Inline code `...` → ...
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_entity_tags(text: str) -> str:
    """Remove all @{实体} and @entity markup tags, keeping the entity name."""
    text = re.sub(r"@\{([^{}\n]+)\}", r"\1", text)
    text = re.sub(
        r"@([A-Za-z][A-Za-z0-9_-]{0,31}|[\u4e00-\u9fff·-]{1,12})(?=[\s，。！？、；：""''（）()《》〈〉【】\[\],.!?:;]|$)",
        r"\1",
        text,
    )
    return text


def count_words(text: str) -> int:
    """Count Chinese characters + English words in text."""
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    en_words = len(re.findall(r'[A-Za-z]+', text))
    return cn_chars + en_words

