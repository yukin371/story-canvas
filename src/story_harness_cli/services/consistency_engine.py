from __future__ import annotations

import re
from typing import Any, Dict, List

from story_harness_cli.utils.text import paragraphs_from_text
from .rule_semantics import build_rule_judgement, chapter_scope_ref


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
IDENTITY_INTRO_PATTERNS = (
    r"自称",
    r"报上名号",
    r"报出姓名",
    r"说自己叫",
    r"说她叫",
    r"说他叫",
    r"名叫",
    r"名为",
    r"唤作",
    r"唤做",
    r"被称作",
    r"有人叫(?:她|他)?",
    r"听见(?:有人)?叫(?:她|他)?",
    r"听到(?:有人)?喊(?:她|他)?",
    r"有人喊出了?她的名字",
)
ANONYMOUS_ROLE_CUES = (
    "散修", "剑修", "修士", "女修", "男修", "少女", "女子", "女人", "少年", "青年",
    "来人", "那人", "对方", "她", "他",
)
ANONYMOUS_DESCRIPTOR_CUES = (
    "剑", "鞘", "剑意", "气息", "寒意", "杀意", "灵压", "目光", "眼神", "嗓音",
    "声音", "步伐", "背影", "衣", "袍", "发", "眸", "面容",
)
NON_PERSON_NAME_SUFFIXES = ("宗", "门", "阁", "城", "域", "印", "诀", "术", "丹", "符", "珠", "塔", "阵", "殿", "宫", "盟", "谷", "山", "海")
LOW_POWER_TERMS = (
    "凡人", "未入练气", "未入炼气", "未入道", "练气", "炼气", "练气初期", "炼气初期",
    "练气一层", "炼气一层", "练气二层", "炼气二层", "练气三层", "炼气三层",
)
HIGH_POWER_TERMS = (
    "筑基", "结丹", "金丹", "元婴", "化神", "洞虚", "洞天", "通玄", "先天", "圣阶",
)
HIGH_RISK_TASK_PATTERNS = (
    ("秘境探索", (r"秘境", r"探索|探路|深入")),
    ("宗门试炼", (r"试炼", r"秘境|险地|禁地|猎杀|历练")),
    ("险地任务", (r"禁地|险地|绝地", r"前往|进入|深入|探索")),
)
BREAKTHROUGH_TARGET_CUES = (
    "突破", "冲击", "晋入", "晋升", "迈入", "踏入", "直入",
)
TASK_PARTICIPATION_CUES = (
    "参加", "报名", "被派", "派去", "前往", "进入", "去往", "赴", "安排", "最终环节",
)
TASK_SAFEGUARD_CUES = (
    "外围", "外层", "边缘", "低阶弟子", "只限练气", "只许练气", "练气弟子试炼",
    "长老带队", "随行长老", "护道", "护符", "保命符", "传送符", "接应", "安全区域",
    "不得深入", "不许深入", "禁制压制", "风险可控", "不会致命", "演练",
)
PROGRESSION_EXCEPTION_CUES = (
    "传承灌顶", "灌顶", "秘法", "禁术", "外力", "奇遇", "重修", "转世", "夺舍", "破格",
)
BREAKTHROUGH_NEGATION_PREFIXES = (
    "未能", "不能", "不敢", "不会", "难以", "无法", "尚未", "还未", "没能", "未曾",
)
BREAKTHROUGH_FAILURE_SUFFIXES = (
    "失败", "未成", "未果", "受阻", "夭折", "中断",
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
    unintroduced_name_reveals = _detect_unintroduced_name_reveals(chapter_text, chapter_id)
    capability_task_risks = _detect_capability_task_risks(state, chapter_text, chapter_id)
    power_progression_conflicts = _detect_power_progression_conflicts(state, chapter_text, chapter_id)

    context_for_ai = _build_ai_context(state, chapter_text, chapter_id)
    judgements = _build_consistency_judgements(
        hard=hard,
        soft=soft,
        setting_conflicts=setting_conflicts,
        unintroduced_name_reveals=unintroduced_name_reveals,
        capability_task_risks=capability_task_risks,
        power_progression_conflicts=power_progression_conflicts,
        chapter_id=chapter_id,
    )

    return {
        "hardChecks": hard,
        "softChecks": soft,
        "settingCandidates": setting_candidates,
        "settingConflicts": setting_conflicts,
        "unintroducedNameReveals": unintroduced_name_reveals,
        "capabilityTaskRisks": capability_task_risks,
        "powerProgressionConflicts": power_progression_conflicts,
        "judgements": judgements,
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
    direct_patterns = (
        r"所谓([^\s，。；：]{2,10})",
        r"([^\s，。；：]{2,10})被称为",
        r"([^\s，。；：]{2,10})叫做",
        r"([^\s，。；：]{2,10})称作",
    )
    for pattern in direct_patterns:
        match = re.search(pattern, text)
        if match:
            label = match.group(1).strip("“”「」『』《》")
            if 2 <= len(label) <= 12:
                return label
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


def _detect_unintroduced_name_reveals(
    chapter_text: str,
    chapter_id: str,
) -> List[Dict[str, Any]]:
    paragraphs = paragraphs_from_text(chapter_text)
    results: List[Dict[str, Any]] = []
    for paragraph_index, paragraph in enumerate(paragraphs, start=1):
        candidate_name = _extract_isolated_name_candidate(paragraph)
        if not candidate_name:
            continue
        previous_text = "\n".join(paragraphs[: paragraph_index - 1])
        if candidate_name and candidate_name in previous_text:
            continue
        window_start = max(0, paragraph_index - 3)
        nearby_text = "\n".join(paragraphs[window_start:paragraph_index])
        if _has_identity_intro_cue(nearby_text, candidate_name):
            continue
        anonymous_context = paragraphs[window_start: paragraph_index - 1]
        context_score = _score_anonymous_character_context(anonymous_context)
        if context_score < 2:
            continue
        before_excerpt = " / ".join(item.strip() for item in anonymous_context[-2:] if item.strip())
        current_excerpt = paragraph.strip()
        results.append(
            {
                "name": candidate_name,
                "issue": f"角色“{candidate_name}”首次出现时缺少明确来源，像是旁白直接得知了姓名",
                "chapterId": chapter_id,
                "paragraphIndex": paragraph_index,
                "severity": "warning",
                "evidence": [
                    f"前置匿名描写: {before_excerpt[:80]}",
                    f"直接命名段落: {current_excerpt[:40]}",
                ],
                "suggestion": f"在揭示“{candidate_name}”前补一处来源，例如自报名号、他人称呼，或 POV 明确听见/得知其姓名。",
            }
        )
    return results


def _extract_isolated_name_candidate(paragraph: str) -> str:
    text = paragraph.strip()
    if not text or text.startswith("#"):
        return ""
    normalized = re.sub(r"[。！？；：、\s]", "", text)
    normalized = normalized.strip("“”「」『』《》()（）[]【】")
    if not re.fullmatch(f"[{CJK_RANGE}]{{2,4}}", normalized):
        return ""
    if normalized.endswith(NON_PERSON_NAME_SUFFIXES):
        return ""
    return normalized


def _has_identity_intro_cue(text: str, name: str) -> bool:
    if not text:
        return False
    for pattern in IDENTITY_INTRO_PATTERNS:
        if re.search(pattern, text):
            return True
    if name and re.search(rf"[“\"「『]?{re.escape(name)}[”\"」』]?[，,:：]?", text):
        intro_near_name = (
            rf"(?:叫|名叫|名为|唤作|唤做|自称|报上名号|报出姓名).{{0,6}}{re.escape(name)}"
            rf"|{re.escape(name)}.{{0,6}}(?:这个名字|三个字|之名)"
        )
        if re.search(intro_near_name, text):
            return True
    return False


def _score_anonymous_character_context(paragraphs: List[str]) -> int:
    if not paragraphs:
        return 0
    joined = "\n".join(paragraphs)
    score = 0
    if any(cue in joined for cue in ANONYMOUS_ROLE_CUES):
        score += 1
    if any(cue in joined for cue in ANONYMOUS_DESCRIPTOR_CUES):
        score += 1
    short_fragments = 0
    for paragraph in paragraphs:
        for fragment in re.split(r"[。！？；]", paragraph):
            unit = fragment.strip()
            if 2 <= len(unit) <= 8:
                short_fragments += 1
    if short_fragments >= 2:
        score += 1
    if any(re.search(pattern, joined) for pattern in IDENTITY_INTRO_PATTERNS):
        score -= 2
    return score


def _detect_capability_task_risks(
    state: Dict[str, Dict[str, Any]],
    chapter_text: str,
    chapter_id: str,
) -> List[Dict[str, Any]]:
    paragraphs = paragraphs_from_text(chapter_text)
    if not paragraphs:
        return []
    low_power_entities = _collect_low_power_entities(state)
    results: List[Dict[str, Any]] = []
    for entity in low_power_entities:
        name = entity.get("name", "")
        if not name:
            continue
        for paragraph_index, _paragraph in enumerate(paragraphs, start=1):
            window_text = _paragraph_window_text(paragraphs, paragraph_index)
            if name not in window_text:
                continue
            task_label = _detect_high_risk_task_label(window_text)
            if not task_label:
                continue
            if not any(cue in window_text for cue in TASK_PARTICIPATION_CUES):
                continue
            if any(cue in window_text for cue in TASK_SAFEGUARD_CUES):
                continue
            power_label = entity.get("powerLabel", "")
            results.append(
                {
                    "entityId": entity.get("id", ""),
                    "entityName": name,
                    "powerLevel": power_label,
                    "taskLabel": task_label,
                    "issue": f"{name} 当前实力“{power_label}”却被卷入“{task_label}”，正文缺少安全边界或世界规则例外说明",
                    "chapterId": chapter_id,
                    "paragraphIndex": paragraph_index,
                    "severity": "warning",
                    "evidence": [window_text.strip()[:120]],
                    "suggestion": (
                        f"补足 {task_label} 的合理性依据，例如低阶试炼限定、外围活动、长老带队、护符保护，"
                        f"或明确 {name} 此时已具备足以应对的术法/手段。"
                    ),
                }
            )
            break
    return results


def _collect_low_power_entities(state: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    entities = state.get("entities", {}).get("entities", [])
    results: List[Dict[str, str]] = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        power_label = _extract_power_label(entity)
        if not power_label:
            continue
        if any(term in power_label for term in HIGH_POWER_TERMS):
            continue
        if not any(term in power_label for term in LOW_POWER_TERMS):
            continue
        results.append(
            {
                "id": str(entity.get("id", "")),
                "name": str(entity.get("name", "")),
                "powerLabel": power_label,
            }
        )
    return results


def _extract_power_label(entity: Dict[str, Any]) -> str:
    state_info = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
    power_level = state_info.get("powerLevel", {}) if isinstance(state_info.get("powerLevel"), dict) else {}
    labels = []
    for key in ("publicLevel", "trueLevel"):
        value = power_level.get(key)
        if isinstance(value, str) and value:
            labels.append(value)
    if labels:
        return "/".join(labels)
    current_state = entity.get("currentState")
    if isinstance(current_state, dict):
        value = current_state.get("powerLevel")
        if isinstance(value, str) and value:
            return value
    return ""


def _paragraph_window_text(paragraphs: List[str], paragraph_index: int) -> str:
    start = max(0, paragraph_index - 2)
    end = min(len(paragraphs), paragraph_index + 1)
    return "\n".join(paragraphs[start:end])


def _detect_high_risk_task_label(text: str) -> str:
    for label, patterns in HIGH_RISK_TASK_PATTERNS:
        if all(re.search(pattern, text) for pattern in patterns):
            return label
    return ""


def _detect_power_progression_conflicts(
    state: Dict[str, Dict[str, Any]],
    chapter_text: str,
    chapter_id: str,
) -> List[Dict[str, Any]]:
    paragraphs = paragraphs_from_text(chapter_text)
    if not paragraphs:
        return []
    stage_lookup = _build_power_progression_lookup(state.get("worldbook", {}))
    if not stage_lookup:
        return []

    results: List[Dict[str, Any]] = []
    for entity in state.get("entities", {}).get("entities", []):
        if not isinstance(entity, dict):
            continue
        name = str(entity.get("name", "")).strip()
        current_stage = _extract_entity_progression_stage(entity)
        current_stage_info = stage_lookup.get(_normalize_progression_stage(current_stage))
        if not name or not current_stage_info:
            continue
        expected_next_stage = current_stage_info.get("nextStage", "")
        if not isinstance(expected_next_stage, str) or not expected_next_stage:
            continue

        for paragraph_index, _paragraph in enumerate(paragraphs, start=1):
            window_text = _paragraph_window_text(paragraphs, paragraph_index)
            if name not in window_text:
                continue
            target_stage_info = None
            target_stage = ""
            for clause in _progression_clauses(window_text):
                if name not in clause:
                    continue
                if any(cue in clause for cue in PROGRESSION_EXCEPTION_CUES):
                    continue
                target_stage_info = _detect_breakthrough_target_stage(clause, stage_lookup)
                if not target_stage_info:
                    continue
                if target_stage_info.get("progressionId") != current_stage_info.get("progressionId"):
                    target_stage_info = None
                    continue
                target_stage = str(target_stage_info.get("name", ""))
                if target_stage in {current_stage_info.get("name", ""), expected_next_stage}:
                    target_stage_info = None
                    continue
                break
            if not target_stage_info:
                continue

            bottleneck = str(current_stage_info.get("bottleneck", ""))
            requirements = [
                item for item in current_stage_info.get("breakthroughRequirements", [])
                if isinstance(item, str) and item
            ]
            requirement_hint = ""
            if bottleneck:
                requirement_hint = f"当前瓶颈是“{bottleneck}”"
            elif requirements:
                requirement_hint = f"当前突破条件包括“{requirements[0]}”"
            suggestion_suffix = f"，并把 {requirement_hint} 写进正文" if requirement_hint else ""
            results.append(
                {
                    "entityId": str(entity.get("id", "")),
                    "entityName": name,
                    "currentStage": current_stage_info.get("name", ""),
                    "targetStage": target_stage,
                    "expectedNextStage": expected_next_stage,
                    "progressionLabel": current_stage_info.get("progressionLabel", ""),
                    "issue": (
                        f"{name} 当前境界“{current_stage_info.get('name', '')}”按世界规则应先突破到“{expected_next_stage}”，"
                        f"但正文却直接指向“{target_stage}”"
                    ),
                    "chapterId": chapter_id,
                    "paragraphIndex": paragraph_index,
                    "severity": "warning",
                    "evidence": [window_text.strip()[:120]],
                    "suggestion": (
                        f"确认 {name} 本章的突破目标是否应改为“{expected_next_stage}”，"
                        f"或补足能越阶冲击“{target_stage}”的明确例外规则{suggestion_suffix}。"
                    ),
                }
            )
            break
    return results


def _build_power_progression_lookup(worldbook: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for index, progression in enumerate(worldbook.get("powerProgressions", []), start=1):
        if not isinstance(progression, dict):
            continue
        progression_id = str(progression.get("id") or progression.get("label") or f"progression-{index}")
        progression_label = str(progression.get("label") or progression_id)
        for stage in progression.get("stages", []):
            if not isinstance(stage, dict):
                continue
            name = str(stage.get("name", "")).strip()
            next_stage = str(stage.get("nextStage", "")).strip()
            if not name:
                continue
            stage_info = {
                "progressionId": progression_id,
                "progressionLabel": progression_label,
                "name": name,
                "nextStage": next_stage,
                "bottleneck": str(stage.get("bottleneck", "")).strip(),
                "breakthroughRequirements": [
                    item for item in stage.get("breakthroughRequirements", [])
                    if isinstance(item, str) and item
                ],
            }
            aliases = [name]
            aliases.extend(
                item for item in stage.get("aliases", [])
                if isinstance(item, str) and item
            )
            for alias in aliases:
                lookup[_normalize_progression_stage(alias)] = stage_info
    return lookup


def _normalize_progression_stage(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _extract_entity_progression_stage(entity: Dict[str, Any]) -> str:
    state_info = entity.get("state", {}) if isinstance(entity.get("state"), dict) else {}
    power_level = state_info.get("powerLevel", {}) if isinstance(state_info.get("powerLevel"), dict) else {}
    for key in ("publicLevel", "trueLevel"):
        value = power_level.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    current_state = entity.get("currentState")
    if isinstance(current_state, dict):
        value = current_state.get("powerLevel")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _progression_clauses(text: str) -> List[str]:
    return [item.strip() for item in re.split(r"[。！？；\n]", text) if item.strip()]


def _detect_breakthrough_target_stage(
    text: str,
    stage_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any] | None:
    normalized_text = _normalize_progression_stage(text)
    sorted_stages = sorted(
        stage_lookup.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for normalized_stage, stage_info in sorted_stages:
        stage_name = normalized_stage
        if not stage_name:
            continue
        for cue in BREAKTHROUGH_TARGET_CUES:
            if re.search(rf"{re.escape(cue)}[^。！？；，,\n]{{0,8}}{re.escape(stage_name)}", normalized_text):
                if _is_negated_breakthrough_target(normalized_text, cue, stage_name):
                    continue
                return stage_info
    return None


def _is_negated_breakthrough_target(text: str, cue: str, stage_name: str) -> bool:
    for prefix in BREAKTHROUGH_NEGATION_PREFIXES:
        if re.search(rf"{re.escape(prefix)}[^。\n]{{0,4}}{re.escape(cue)}[^。\n]{{0,8}}{re.escape(stage_name)}", text):
            return True
    for suffix in BREAKTHROUGH_FAILURE_SUFFIXES:
        if re.search(rf"{re.escape(cue)}[^。\n]{{0,8}}{re.escape(stage_name)}[^。\n]{{0,4}}{re.escape(suffix)}", text):
            return True
    return False


def _build_consistency_judgements(
    *,
    hard: Dict[str, List[Any]],
    soft: Dict[str, List[Any]],
    setting_conflicts: List[Dict[str, Any]],
    unintroduced_name_reveals: List[Dict[str, Any]],
    capability_task_risks: List[Dict[str, Any]],
    power_progression_conflicts: List[Dict[str, Any]],
    chapter_id: str,
) -> List[Dict[str, Any]]:
    judgements: List[Dict[str, Any]] = []
    judgements.extend(_judgements_from_items(hard.get("stateContradictions", []), "stateContradiction", "error", chapter_id))
    judgements.extend(_judgements_from_items(hard.get("relationContradictions", []), "relationContradiction", "error", chapter_id))
    judgements.extend(_judgements_from_items(hard.get("timelineConflicts", []), "timelineConflict", "error", chapter_id))
    judgements.extend(_judgements_from_items(soft.get("outlineDeviations", []), "outlineDeviation", "warning", chapter_id))
    judgements.extend(_judgements_from_items(setting_conflicts, "settingConflict", "warning", chapter_id))
    judgements.extend(_judgements_from_items(unintroduced_name_reveals, "unintroducedNameReveal", "warning", chapter_id))
    judgements.extend(_judgements_from_items(capability_task_risks, "capabilityTaskMismatch", "warning", chapter_id))
    judgements.extend(_judgements_from_items(power_progression_conflicts, "powerProgressionConflict", "warning", chapter_id))
    return judgements


def _judgements_from_items(
    items: List[Dict[str, Any]],
    rule_id: str,
    default_severity: str,
    chapter_id: str,
) -> List[Dict[str, Any]]:
    judgements: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        paragraph_index = item.get("paragraphIndex")
        scope_ref = chapter_scope_ref(chapter_id, paragraph_index if isinstance(paragraph_index, int) else None)
        message = _consistency_item_message(item)
        suggestion = str(item.get("suggestion", ""))
        evidence = _consistency_item_evidence(item)
        judgements.append(
            build_rule_judgement(
                rule_id=rule_id,
                severity=_normalize_consistency_severity(str(item.get("severity", default_severity)), default_severity),
                message=message,
                suggestion=suggestion,
                evidence=evidence,
                scope_ref=scope_ref,
                payload=item,
            )
        )
    return judgements


def _normalize_consistency_severity(severity: str, default_severity: str) -> str:
    if severity in {"error", "warning", "info"}:
        return severity
    mapping = {
        "strict": "error",
        "advisory": "warning",
        "high-risk": "warning",
    }
    return mapping.get(severity, default_severity)


def _consistency_item_message(item: Dict[str, Any]) -> str:
    for key in ("issue", "note", "summary"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return "检测到一致性风险。"


def _consistency_item_evidence(item: Dict[str, Any]) -> List[str]:
    evidence = item.get("evidence")
    if isinstance(evidence, list):
        return [str(value) for value in evidence if value]
    current = item.get("currentEvidence")
    if isinstance(current, str) and current:
        return [current]
    existing = item.get("existingText")
    candidate = item.get("candidateText")
    merged = []
    if isinstance(existing, str) and existing:
        merged.append(existing)
    if isinstance(candidate, str) and candidate:
        merged.append(candidate)
    return merged
