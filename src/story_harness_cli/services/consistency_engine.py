from __future__ import annotations

import re
from typing import Any, Dict, List

from story_harness_cli.utils.text import paragraphs_from_text


ACTIVE_BEHAVIOR_KEYWORDS = [
    "走", "跑", "说", "笑", "站", "坐", "拿", "看", "握", "挥",
    "推", "拉", "跳", "爬", "骑", "开", "关", "打", "写", "抓",
    "点头", "摇头", "转身", "回头", "弯腰", "抬头", "低头",
    "拥抱", "亲吻", "微笑", "怒吼", "低声", "喊",
]

INTIMATE_KEYWORDS = [
    "亲密", "拥抱", "亲吻", "依偎", "牵手", "抚摸", "温柔",
    "默契", "配合", "并肩", "携手", "守护",
]

NEGATION_PREFIXES = ("不", "没", "无", "未", "非")

INTIMATE_WORDS_NEED_NEGATION_CHECK = {"信任", "爱", "喜欢"}
CJK_RANGE = f"{chr(0x4E00)}-{chr(0x9FFF)}"
SETTING_CUE_PATTERNS = (
    r"被称为",
    r"叫做",
    r"称作",
    r"意味着",
    r"所谓",
    r"规则是",
    r"代价是",
    r"每次.{0,20}都会",
    r"一旦.{0,20}就",
    r"只有.{0,20}才",
    r"无法",
    r"不能",
    r"必须",
)
SETTING_LABEL_PATTERNS = (
    r"[“「『《]([^”」』》]{2,12})[”」』》]",
    f"([{CJK_RANGE}]{{2,10}}(?:效应|法则|定律|理论|模型|体系|术式|仪式|回路|协议|计划|印记|烙印|命格|命途|体质|灵根|血脉|规则))",
)
SETTING_NEGATIONS = ("不", "没", "无", "未", "非", "无法", "不能", "不会", "不得")
SETTING_OPPOSITE_PAIRS = (
    ("可以", "不能"),
    ("必须", "无需"),
    ("会", "不会"),
    ("留下", "不会留下"),
    ("暴露", "不会暴露"),
    ("失去", "不会失去"),
)


def check_consistency(
    state: Dict[str, Dict[str, Any]],
    chapter_text: str,
    chapter_id: str,
    keywords: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    hard: Dict[str, List] = {
        "stateContradictions": [],
        "relationContradictions": [],
        "timelineConflicts": [],
    }
    soft: Dict[str, List] = {
        "outlineDeviations": [],
    }

    active_kw = (keywords or {}).get("activeBehavior", ACTIVE_BEHAVIOR_KEYWORDS)
    intimate_kw = (keywords or {}).get("intimate", INTIMATE_KEYWORDS)
    negation_kw = tuple((keywords or {}).get("negationPrefixes", NEGATION_PREFIXES))

    _check_state_contradictions(state, chapter_text, chapter_id, hard["stateContradictions"], active_kw)
    _check_relation_contradictions(
        state, chapter_text, chapter_id, hard["relationContradictions"], intimate_kw, negation_kw,
    )
    _check_outline_deviations(state, chapter_id, soft["outlineDeviations"])
    _check_thread_status(state, chapter_id, soft["outlineDeviations"])
    _check_arc_alignment(state, chapter_text, chapter_id, soft["outlineDeviations"])
    setting_candidates = _extract_setting_candidates(chapter_text, chapter_id)
    setting_conflicts = _check_setting_conflicts(state, setting_candidates)

    context_for_ai = _build_ai_context(state, chapter_text, chapter_id)

    return {
        "hardChecks": hard,
        "softChecks": soft,
        "settingCandidates": setting_candidates,
        "settingConflicts": setting_conflicts,
        "contextForAI": context_for_ai,
    }


def _check_state_contradictions(
    state: Dict, chapter_text: str, chapter_id: str, results: List, active_kw: List[str]
) -> None:
    entities = state.get("entities", {}).get("entities", [])
    paragraphs = paragraphs_from_text(chapter_text)

    for entity in entities:
        current = entity.get("currentState", {})
        if not isinstance(current, dict):
            continue
        if current.get("status") != "deceased":
            continue
        name = entity.get("name", "")
        for para in paragraphs:
            if name not in para:
                continue
            has_active = any(kw in para for kw in active_kw)
            if has_active:
                last_chapter = current.get("lastUpdatedChapter", "unknown")
                results.append({
                    "entity": entity.get("id"),
                    "entityName": name,
                    "issue": f"projection 标记为 deceased，但正文中 {name} 有活跃描写",
                    "evidence": [
                        f"projection: status=deceased (chapter-{last_chapter})",
                        f"chapter: {chapter_id} 段落: '{para[:80]}...'",
                    ],
                    "severity": "strict",
                })
                break


def _check_relation_contradictions(
    state: Dict, chapter_text: str, chapter_id: str, results: List,
    intimate_kw: List[str], negation_kw: tuple,
) -> None:
    relations = state.get("projection", {}).get("relationProjections", [])
    paragraphs = paragraphs_from_text(chapter_text)

    broken_labels = {"裂痕", "对立", "决裂"}
    for rel in relations:
        label = rel.get("label", "")
        if label not in broken_labels:
            continue
        from_name = rel.get("fromName", "")
        to_name = rel.get("toName", "")
        scope_ref = rel.get("scopeRef", "")

        for para in paragraphs:
            if from_name not in para or to_name not in para:
                continue
            has_intimate = False
            for kw in intimate_kw:
                if kw not in para:
                    continue
                if kw in INTIMATE_WORDS_NEED_NEGATION_CHECK:
                    idx = para.index(kw)
                    if idx > 0 and para[idx - 1] in negation_kw:
                        continue
                has_intimate = True
                break
            if has_intimate:
                results.append({
                    "from": rel.get("fromId"),
                    "fromName": from_name,
                    "to": rel.get("toId"),
                    "toName": to_name,
                    "issue": f"projection 标记关系为'{label}'(chapter-{scope_ref})，但正文表现亲密",
                    "previousLabel": label,
                    "currentEvidence": f"{chapter_id} 段落: '{para[:80]}...'",
                    "severity": "strict",
                })
                break


def _check_outline_deviations(
    state: Dict, chapter_id: str, results: List
) -> None:
    outline = state.get("outline", {})
    volumes = outline.get("volumes", [])

    for vol in volumes:
        for ch in vol.get("chapters", []):
            if ch.get("id") != chapter_id:
                continue
            if ch.get("status") != "completed":
                continue
            for beat in ch.get("beats", []):
                if beat.get("status") == "planned":
                    results.append({
                        "beatId": beat.get("id"),
                        "summary": beat.get("summary", ""),
                        "status": "planned",
                        "note": "细纲中规划的场景在正文中未出现，可能是故意跳过",
                        "severity": "advisory",
                    })


def _build_ai_context(
    state: Dict, chapter_text: str, chapter_id: str
) -> Dict[str, Any]:
    entities = state.get("entities", {}).get("entities", [])
    projection = state.get("projection", {})
    outline = state.get("outline", {})

    entity_cards = []
    for e in entities:
        entity_cards.append({
            "id": e.get("id"),
            "name": e.get("name"),
            "seed": e.get("seed", {}),
            "profile": e.get("profile", {}),
            "currentState": e.get("currentState", {}),
        })

    relevant_snapshots = [
        s for s in projection.get("snapshotProjections", [])
        if s.get("scopeRef") == chapter_id
    ]
    relevant_relations = [
        r for r in projection.get("relationProjections", [])
        if r.get("scopeRef") == chapter_id
    ]

    outline_expectation = ""
    for vol in outline.get("volumes", []):
        for ch in vol.get("chapters", []):
            if ch.get("id") == chapter_id:
                outline_expectation = ch.get("direction", "")
                break

    return {
        "entityCards": entity_cards,
        "relevantProjections": {
            "snapshots": relevant_snapshots,
            "relations": relevant_relations,
        },
        "chapterContent": chapter_text,
        "outlineExpectation": outline_expectation,
    }


def _check_thread_status(
    state: Dict, chapter_id: str, results: List
) -> None:
    """Check if any suspense threads are overdue at this chapter."""
    import re
    threads = state.get("threads", {}).get("threads", [])
    if not threads:
        return

    def _ch_num(cid: str) -> int:
        m = re.search(r"\d+", cid)
        return int(m.group()) if m else 0

    current_num = _ch_num(chapter_id)
    for t in threads:
        if t.get("status") == "resolved":
            continue
        expected = t.get("expectedResolveBy")
        if expected and _ch_num(expected) < current_num:
            results.append({
                "threadId": t.get("id"),
                "summary": t.get("name", ""),
                "status": "overdue",
                "note": f"悬念线索 '{t.get('name')}' 已逾期 (预期 chapter-{_ch_num(expected)} 解决)",
                "severity": "advisory",
            })


def _check_arc_alignment(
    state: Dict, chapter_text: str, chapter_id: str, results: List
) -> None:
    """Check if characters appearing in this chapter have arc milestones here."""
    entities = state.get("entities", {}).get("entities", [])
    for entity in entities:
        arc = entity.get("arc")
        if not arc:
            continue
        name = entity.get("name", "")
        if name not in chapter_text:
            continue
        milestones = arc.get("milestones", [])
        has_milestone = any(m.get("chapterId") == chapter_id for m in milestones)
        if not has_milestone and milestones:
            results.append({
                "entityId": entity.get("id"),
                "summary": f"{name} 在 {chapter_id} 出现但无弧线里程碑",
                "status": "info",
                "note": "角色出现但弧线未发展，可能遗漏弧线推进机会",
                "severity": "advisory",
            })


def _extract_setting_candidates(chapter_text: str, chapter_id: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen = set()
    for paragraph_index, paragraph in enumerate(paragraphs_from_text(chapter_text), start=1):
        text = paragraph.strip()
        if len(text) < 10:
            continue
        if not any(re.search(pattern, text) for pattern in SETTING_CUE_PATTERNS):
            continue
        label = _extract_setting_label(text)
        if not label:
            continue
        normalized_fact = _normalize_setting_text(text)
        dedupe_key = (label, normalized_fact)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        confidence = 0.72
        if "所谓" in text or re.search(r"[“「『《][^”」』》]{2,12}[”」』》]", text):
            confidence += 0.08
        if re.search(r"每次.{0,20}都会|一旦.{0,20}就|只有.{0,20}才", text):
            confidence += 0.08
        candidates.append(
            {
                "label": label,
                "fact": text,
                "chapterId": chapter_id,
                "paragraphIndex": paragraph_index,
                "confidence": round(min(confidence, 0.92), 2),
                "kind": "premise-fact",
            }
        )
    return candidates


def _check_setting_conflicts(
    state: Dict[str, Dict[str, Any]],
    setting_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    worldbook = state.get("worldbook", {})
    existing_by_label: Dict[str, List[Dict[str, str]]] = {}
    for item in worldbook.get("premiseFacts", []):
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        fact = item.get("fact")
        if isinstance(label, str) and label and isinstance(fact, str) and fact:
            existing_by_label.setdefault(label, []).append({"source": "premiseFacts", "text": fact})
    for item in worldbook.get("worldRules", []):
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        rule = item.get("rule")
        if isinstance(label, str) and label and isinstance(rule, str) and rule:
            existing_by_label.setdefault(label, []).append({"source": "worldRules", "text": rule})

    conflicts: List[Dict[str, Any]] = []
    for candidate in setting_candidates:
        label = candidate.get("label", "")
        fact = candidate.get("fact", "")
        if not label or not fact:
            continue
        for existing in existing_by_label.get(label, []):
            if _normalize_setting_text(existing["text"]) == _normalize_setting_text(fact):
                continue
            if not _setting_texts_conflict(existing["text"], fact):
                continue
            conflicts.append(
                {
                    "label": label,
                    "issue": f"新设定“{label}”与既有设定可能冲突",
                    "existingSource": existing["source"],
                    "existingText": existing["text"],
                    "candidateText": fact,
                    "chapterId": candidate.get("chapterId", ""),
                    "severity": "warning",
                }
            )
            break
    return conflicts


def _extract_setting_label(text: str) -> str:
    for pattern in SETTING_LABEL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            label = match.group(1).strip()
            if 2 <= len(label) <= 12:
                return label
    if text.startswith("所谓"):
        trimmed = text[2:14]
        match = re.match(f"([{CJK_RANGE}]{{2,10}})", trimmed)
        if match:
            return match.group(1)
    return ""


def _normalize_setting_text(text: str) -> str:
    return re.sub(r"[，。？！、“”‘’：；\s]", "", text)


def _setting_texts_conflict(left: str, right: str) -> bool:
    left_norm = _normalize_setting_text(left)
    right_norm = _normalize_setting_text(right)
    if left_norm == right_norm:
        return False

    left_has_negation = any(token in left for token in SETTING_NEGATIONS)
    right_has_negation = any(token in right for token in SETTING_NEGATIONS)
    if left_has_negation != right_has_negation:
        return True

    left_numbers = re.findall(r"\d+", left)
    right_numbers = re.findall(r"\d+", right)
    if left_numbers and right_numbers and left_numbers != right_numbers:
        return True

    for positive, negative in SETTING_OPPOSITE_PAIRS:
        if (positive in left and negative in right) or (positive in right and negative in left):
            return True
    return False
