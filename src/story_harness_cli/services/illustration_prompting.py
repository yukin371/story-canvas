from __future__ import annotations

from typing import Any, Dict, List


def build_entity_illustration_payload(
    state: Dict[str, Any],
    *,
    entity: Dict[str, Any],
    use_case: str = "",
    mode: str,
    prompt_pack: Dict[str, Any],
    pack_ref: Dict[str, Any],
    template_id: str = "",
    modifier_refs: List[str] | None = None,
    user_extra_prompt: str = "",
    commercial_mode: str = "",
    default_template_by_use_case: Dict[str, str] | None = None,
    default_modifier_refs: List[str] | None = None,
    input_images: List[str] | None = None,
    mask_path: str = "",
) -> Dict[str, Any]:
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    resolved_use_case = str(use_case or "character").strip() or "character"
    subject = _build_entity_subject(
        project,
        positioning,
        entity=entity,
        mode=mode,
        use_case=resolved_use_case,
    )
    return _build_payload(
        target_type="entity",
        target_id=entity.get("id", ""),
        target_name=entity.get("name", ""),
        use_case=resolved_use_case,
        subject=subject,
        mode=mode,
        prompt_pack=prompt_pack,
        pack_ref=pack_ref,
        template_id=template_id,
        modifier_refs=modifier_refs or [],
        user_extra_prompt=user_extra_prompt,
        commercial_mode=commercial_mode,
        default_template_by_use_case=default_template_by_use_case or {},
        default_modifier_refs=default_modifier_refs or [],
        input_images=input_images or [],
        mask_path=mask_path,
    )


def build_chapter_illustration_payload(
    state: Dict[str, Any],
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_text: str,
    use_case: str = "",
    mode: str,
    prompt_pack: Dict[str, Any],
    pack_ref: Dict[str, Any],
    template_id: str = "",
    modifier_refs: List[str] | None = None,
    user_extra_prompt: str = "",
    commercial_mode: str = "",
    default_template_by_use_case: Dict[str, str] | None = None,
    default_modifier_refs: List[str] | None = None,
    input_images: List[str] | None = None,
    mask_path: str = "",
) -> Dict[str, Any]:
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    resolved_use_case = str(use_case or "chapter-scene").strip() or "chapter-scene"
    subject = _build_chapter_subject(
        project,
        positioning,
        chapter_id=chapter_id,
        chapter_title=chapter_title,
        chapter_text=chapter_text,
        mode=mode,
        use_case=resolved_use_case,
    )
    return _build_payload(
        target_type="chapter",
        target_id=chapter_id,
        target_name=chapter_title,
        use_case=resolved_use_case,
        subject=subject,
        mode=mode,
        prompt_pack=prompt_pack,
        pack_ref=pack_ref,
        template_id=template_id,
        modifier_refs=modifier_refs or [],
        user_extra_prompt=user_extra_prompt,
        commercial_mode=commercial_mode,
        default_template_by_use_case=default_template_by_use_case or {},
        default_modifier_refs=default_modifier_refs or [],
        input_images=input_images or [],
        mask_path=mask_path,
    )


def build_freeform_illustration_payload(
    state: Dict[str, Any],
    *,
    target_label: str,
    use_case: str,
    subject: str,
    mode: str,
    prompt_pack: Dict[str, Any],
    pack_ref: Dict[str, Any],
    template_id: str = "",
    modifier_refs: List[str] | None = None,
    user_extra_prompt: str = "",
    commercial_mode: str = "",
    default_template_by_use_case: Dict[str, str] | None = None,
    default_modifier_refs: List[str] | None = None,
    input_images: List[str] | None = None,
    mask_path: str = "",
) -> Dict[str, Any]:
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    normalized_subject = subject.strip()
    if not normalized_subject:
        genre = str(positioning.get("primaryGenre") or project.get("genre") or "").strip()
        title = str(project.get("title") or "").strip()
        fragments = [item for item in (title, genre, user_extra_prompt.strip()) if item]
        normalized_subject = "；".join(fragments) if fragments else target_label.strip()
    return _build_payload(
        target_type="temporary",
        target_id=target_label,
        target_name=target_label,
        use_case=use_case,
        subject=normalized_subject,
        mode=mode,
        prompt_pack=prompt_pack,
        pack_ref=pack_ref,
        template_id=template_id,
        modifier_refs=modifier_refs or [],
        user_extra_prompt=user_extra_prompt,
        commercial_mode=commercial_mode,
        default_template_by_use_case=default_template_by_use_case or {},
        default_modifier_refs=default_modifier_refs or [],
        input_images=input_images or [],
        mask_path=mask_path,
    )


def _build_payload(
    *,
    target_type: str,
    target_id: str,
    target_name: str,
    use_case: str,
    subject: str,
    mode: str,
    prompt_pack: Dict[str, Any],
    pack_ref: Dict[str, Any],
    template_id: str,
    modifier_refs: List[str],
    user_extra_prompt: str,
    commercial_mode: str,
    default_template_by_use_case: Dict[str, str],
    default_modifier_refs: List[str],
    input_images: List[str],
    mask_path: str,
) -> Dict[str, Any]:
    resolved_template = _resolve_template(
        prompt_pack,
        use_case=use_case,
        mode=mode,
        template_id=template_id,
        default_template_id=str(default_template_by_use_case.get(use_case) or ""),
    )
    resolved_modifier_refs = _normalize_modifier_refs(modifier_refs, default_modifier_refs)
    resolved_modifiers = _resolve_modifiers(prompt_pack, resolved_modifier_refs)
    resolved_commercial_mode = commercial_mode or "personal"
    policy_snapshot = _resolve_policy_snapshot(
        prompt_pack,
        template=resolved_template,
        modifiers=resolved_modifiers,
        commercial_mode=resolved_commercial_mode,
    )
    prompt_snapshot = _build_prompt_snapshot(
        prompt_pack=prompt_pack,
        pack_ref=pack_ref,
        template=resolved_template,
        use_case=use_case,
        mode=mode,
        commercial_mode=resolved_commercial_mode,
        modifiers=resolved_modifiers,
        user_extra_prompt=user_extra_prompt,
        subject=subject,
        commercial_prompt=policy_snapshot.get("commercialPrompt", ""),
    )

    prompt_pack_name = str(pack_ref.get("packId", "")).rsplit("/", 1)[-1] if pack_ref.get("packId") else "default"
    return {
        "targetType": target_type,
        "targetId": target_id,
        "targetName": target_name,
        "useCase": use_case,
        "mode": mode,
        "promptPack": prompt_pack_name,
        "promptPackRef": pack_ref,
        "templateId": resolved_template.get("id", ""),
        "modifierRefs": [item.get("id", "") for item in resolved_modifiers],
        "commercialMode": resolved_commercial_mode,
        "promptText": prompt_snapshot["resolvedPrompt"],
        "promptSnapshot": prompt_snapshot,
        "policySnapshot": policy_snapshot,
        "inputImages": list(input_images),
        "maskPath": mask_path,
        "providerRequest": {
            "prompt": prompt_snapshot["resolvedPrompt"],
            "negativePrompt": policy_snapshot.get("negativePrompt", ""),
            "inputImages": list(input_images),
            "maskPath": mask_path,
            "metadata": {
                "targetType": target_type,
                "targetId": target_id,
                "targetName": target_name,
                "useCase": use_case,
                "mode": mode,
                "promptPack": prompt_pack_name,
                "promptPackRef": pack_ref,
                "templateRef": resolved_template.get("id", ""),
                "modifierRefs": [item.get("id", "") for item in resolved_modifiers],
                "commercialMode": resolved_commercial_mode,
            },
        },
    }


def _resolve_template(
    prompt_pack: Dict[str, Any],
    *,
    use_case: str,
    mode: str,
    template_id: str,
    default_template_id: str,
) -> Dict[str, Any]:
    templates = [item for item in prompt_pack.get("templates", []) if isinstance(item, dict)]
    for candidate_id in (template_id, default_template_id):
        normalized = str(candidate_id or "").strip()
        if not normalized:
            continue
        for template in templates:
            if template.get("id") == normalized:
                return template

    for candidate_use_case in _template_use_case_candidates(use_case):
        exact_mode_match = [
            template
            for template in templates
            if template.get("useCase") == candidate_use_case and template.get("mode") == mode
        ]
        if exact_mode_match:
            return exact_mode_match[0]

    for candidate_use_case in _template_use_case_candidates(use_case):
        use_case_match = [template for template in templates if template.get("useCase") == candidate_use_case]
        if use_case_match:
            return use_case_match[0]

    if templates:
        return templates[0]
    raise ValueError("prompt pack 不包含可用模板")


def _normalize_modifier_refs(modifier_refs: List[str], default_modifier_refs: List[str]) -> List[str]:
    source = modifier_refs or default_modifier_refs
    result: List[str] = []
    for item in source:
        normalized = str(item or "").strip()
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _resolve_modifiers(prompt_pack: Dict[str, Any], modifier_refs: List[str]) -> List[Dict[str, Any]]:
    modifiers = [item for item in prompt_pack.get("modifierGroups", []) if isinstance(item, dict)]
    resolved: List[Dict[str, Any]] = []
    for ref in modifier_refs:
        for item in modifiers:
            if item.get("id") == ref:
                resolved.append(item)
                break
    return resolved


def _resolve_policy_snapshot(
    prompt_pack: Dict[str, Any],
    *,
    template: Dict[str, Any],
    modifiers: List[Dict[str, Any]],
    commercial_mode: str,
) -> Dict[str, Any]:
    policies = prompt_pack.get("policies", {}) if isinstance(prompt_pack.get("policies"), dict) else {}
    negative_policies = [item for item in policies.get("negativePolicies", []) if isinstance(item, dict)]
    commercial_policies = [item for item in policies.get("commercialPolicies", []) if isinstance(item, dict)]

    negative_ref = str(template.get("defaultNegativePolicyRef") or "")
    commercial_ref = str(template.get("defaultCommercialPolicyRef") or "")
    negative = next((item for item in negative_policies if item.get("id") == negative_ref), {})
    commercial = next((item for item in commercial_policies if item.get("id") == commercial_ref), {})
    if not commercial and commercial_mode:
        commercial = next((item for item in commercial_policies if item.get("mode") == commercial_mode), {})

    negative_parts = [str(negative.get("negativePrompt") or "").strip()]
    negative_parts.extend(
        str(item.get("negativeFragment") or "").strip()
        for item in modifiers
        if str(item.get("negativeFragment") or "").strip()
    )
    negative_prompt = ", ".join(part for part in negative_parts if part)
    commercial_prompt = str(commercial.get("extraPrompt") or "").strip()

    return {
        "negativePolicyRef": negative_ref,
        "commercialPolicyRef": str(commercial.get("id") or commercial_ref),
        "commercialMode": commercial_mode or str(commercial.get("mode") or "personal"),
        "negativePrompt": negative_prompt,
        "commercialPrompt": commercial_prompt,
        "restrictions": list(commercial.get("restrictions", [])) if isinstance(commercial.get("restrictions"), list) else [],
    }


def _build_prompt_snapshot(
    *,
    prompt_pack: Dict[str, Any],
    pack_ref: Dict[str, Any],
    template: Dict[str, Any],
    use_case: str,
    mode: str,
    commercial_mode: str,
    modifiers: List[Dict[str, Any]],
    user_extra_prompt: str,
    subject: str,
    commercial_prompt: str,
) -> Dict[str, Any]:
    lexicon_snapshot = _resolve_lexicon_snapshot(
        prompt_pack,
        use_case=use_case,
        mode=mode,
        commercial_mode=commercial_mode,
    )
    style_fragments = [
        str(item.get("promptFragment") or "").strip()
        for item in modifiers
        if str(item.get("promptFragment") or "").strip()
    ]
    resolved_prompt = _render_prompt_template(
        str(template.get("promptTemplate") or _default_prompt_template(use_case)),
        {
            "subject": subject,
            "styleModifiers": ", ".join(style_fragments),
            "subjectPhrases": _join_prompt_phrases(lexicon_snapshot.get("subjectPhrases", [])),
            "detailPhrases": _join_prompt_phrases(lexicon_snapshot.get("detailPhrases", [])),
            "modeHint": _join_prompt_sentences(lexicon_snapshot.get("modePhrases", [])),
            "stylePrompt": _build_prompt_hint_line("风格上可以带一点", style_fragments),
            "userExtraPrompt": str(user_extra_prompt or "").strip(),
            "userDirection": _join_prompt_sentences([str(user_extra_prompt or "").strip()]),
            "commercialPrompt": commercial_prompt,
            "commercialDirection": _join_prompt_sentences(
                list(lexicon_snapshot.get("commercialPhrases", [])) + [commercial_prompt]
            ),
        },
    )
    return {
        "packRef": pack_ref,
        "templateRef": template.get("id", ""),
        "modifierRefs": [item.get("id", "") for item in modifiers],
        "userExtraPrompt": str(user_extra_prompt or "").strip(),
        "lexiconSnapshot": lexicon_snapshot,
        "resolvedPrompt": resolved_prompt,
    }


def _default_prompt_template(use_case: str) -> str:
    templates = {
        "character": "{subject}\n先把{subjectPhrases}立住，再把{detailPhrases}交代清楚。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "character-sheet": "{subject}\n把人物当成长线设定图处理，先稳住{subjectPhrases}，再把{detailPhrases}交代成可反复复用的视觉记忆。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "chapter-scene": "{subject}\n重点抓住{subjectPhrases}，把{detailPhrases}处理得清楚、可信、能直接落图。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "cover-concept": "{subject}\n先用{subjectPhrases}立住整张海报的叙事轮廓，再让{detailPhrases}在留白和层次里慢慢长出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "cover-poster": "{subject}\n先用{subjectPhrases}立住整张海报的叙事轮廓，再让{detailPhrases}在留白和层次里慢慢长出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "ensemble-key-visual": "{subject}\n先把{subjectPhrases}理清，再让{detailPhrases}服务群像关系、主次层级和版面呼吸。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "duel-scene": "{subject}\n抓住{subjectPhrases}，让{detailPhrases}服务受力、距离和胜负未分的张力。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "chase-escape": "{subject}\n先把{subjectPhrases}推出来，再用{detailPhrases}交代速度、危险和空间方向。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "comic-relief": "{subject}\n先把{subjectPhrases}打准，再用{detailPhrases}把节奏、夸张点和表情读感做出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "promo": "{subject}\n先把{subjectPhrases}打出来，再把{detailPhrases}和画面节奏收干净。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "product": "{subject}\n把{subjectPhrases}当成主角，再把{detailPhrases}交代出材质、年代和象征意味。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "prop-relic": "{subject}\n把{subjectPhrases}当成主角，再把{detailPhrases}交代出材质、年代和象征意味。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "creature-sheet": "{subject}\n先立住{subjectPhrases}，再把{detailPhrases}交代成可信的生物设定。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "manga-panel": "{subject}\n按单格分镜处理，先把{subjectPhrases}立住，再让{detailPhrases}服务阅读方向和黑白节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "manga-page": "{subject}\n按整页漫画分镜处理，先把{subjectPhrases}排清楚，再让{detailPhrases}服务镜头衔接、留白和页内节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
    }
    return templates.get(
        use_case,
        "{subject}\n先把{subjectPhrases}和{detailPhrases}交代清楚。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
    )


def _render_prompt_template(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    lines = [line.strip() for line in rendered.splitlines()]
    return "\n".join(line for line in lines if line)


def _resolve_lexicon_snapshot(
    prompt_pack: Dict[str, Any],
    *,
    use_case: str,
    mode: str,
    commercial_mode: str,
) -> Dict[str, List[str]]:
    lexicon = prompt_pack.get("lexicon", {}) if isinstance(prompt_pack.get("lexicon"), dict) else {}
    use_case_keys = ["common"] + _template_use_case_candidates(use_case)
    subject_phrases = _resolve_lexicon_phrases(lexicon, "subjectPhrases", *use_case_keys)
    detail_phrases = _resolve_lexicon_phrases(lexicon, "detailPhrases", *use_case_keys)
    mode_phrases = _resolve_lexicon_phrases(lexicon, "modePhrases", "common", mode)
    commercial_phrases = _resolve_lexicon_phrases(lexicon, "commercialPhrases", "common", commercial_mode)
    negative_phrases = _resolve_lexicon_phrases(lexicon, "negativePhrases", "common", *use_case_keys, mode)
    return {
        "subjectPhrases": subject_phrases or _default_subject_phrases(use_case),
        "detailPhrases": detail_phrases or _default_detail_phrases(use_case),
        "modePhrases": mode_phrases,
        "commercialPhrases": commercial_phrases,
        "negativePhrases": negative_phrases,
    }


def _resolve_lexicon_phrases(lexicon: Dict[str, Any], group_name: str, *keys: str) -> List[str]:
    group = lexicon.get(group_name, {}) if isinstance(lexicon.get(group_name), dict) else {}
    phrases: List[str] = []
    for key in keys:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        values = group.get(normalized_key)
        phrases.extend(_collect_text_fragments(values))
    return _dedupe_fragments(phrases)


def _default_subject_phrases(use_case: str) -> List[str]:
    defaults = {
        "character": ["人物辨识度", "稳定的人设锚点"],
        "character-sheet": ["完整人设立绘", "可长期复用的外轮廓", "服装与体态记忆点"],
        "chapter-scene": ["人物关系和动作焦点", "场景重心"],
        "cover-poster": ["巨大轮廓主视觉", "一眼识别的世界观符号", "收藏版海报气场"],
        "ensemble-key-visual": ["主角群关系站位", "谁和谁是一伙", "整体势能"],
        "duel-scene": ["对峙双方的力量差", "出手瞬间", "胜负未分的压迫"],
        "chase-escape": ["追逃双方的距离关系", "速度方向", "险些被抓住的一刻"],
        "comic-relief": ["反差感", "表情包级读感", "轻松节奏"],
        "promo": ["第一眼视觉钩子", "主卖点"],
        "prop-relic": ["器物轮廓", "辨识度极强的象征符号", "传说感"],
        "creature-sheet": ["生物体态", "种族辨识度", "威胁或神性"],
        "manga-panel": ["单格焦点", "黑白对比中心", "一眼能懂的动作关系"],
        "manga-page": ["页内主次镜头", "阅读顺序", "整页节奏起伏"],
    }
    for candidate in _template_use_case_candidates(use_case):
        if candidate in defaults:
            return list(defaults[candidate])
    return ["画面重点", "主体识别度"]


def _default_detail_phrases(use_case: str) -> List[str]:
    defaults = {
        "character": ["面部、服饰和气质层次"],
        "character-sheet": ["正面信息、配饰、材质和层次", "人物气质与身份痕迹"],
        "chapter-scene": ["光影、空间层次和关键道具"],
        "cover-poster": ["留白、版式和内轮廓叙事层次", "关键建筑、角色关系与象征物"],
        "ensemble-key-visual": ["前后排层次、主副角色分配和标题留白"],
        "duel-scene": ["武器轨迹、受力姿态、空间切割和特效残响"],
        "chase-escape": ["动线、障碍物、环境压迫和镜头前冲感"],
        "comic-relief": ["夸张动作、道具包袱和人物表情"],
        "promo": ["远近节奏和留白关系"],
        "prop-relic": ["材质磨损、铭文、能量痕迹和陈列气场"],
        "creature-sheet": ["骨骼结构、皮毛鳞片、器官和生态痕迹"],
        "manga-panel": ["分镜取景、对白留白和明暗块面"],
        "manga-page": ["格与格之间的留白、转场和关键特写"],
    }
    for candidate in _template_use_case_candidates(use_case):
        if candidate in defaults:
            return list(defaults[candidate])
    return ["细节层次", "画面完成度"]


def _join_prompt_phrases(values: List[str]) -> str:
    normalized = _dedupe_fragments(values)
    return "、".join(normalized)


def _join_prompt_sentences(values: List[str]) -> str:
    sentences = [_ensure_sentence(value) for value in values if str(value or "").strip()]
    return " ".join(sentence for sentence in sentences if sentence)


def _build_prompt_hint_line(prefix: str, values: List[str]) -> str:
    joined = _join_prompt_phrases(values)
    if not joined:
        return ""
    return _ensure_sentence(f"{prefix}{joined}")


def _ensure_sentence(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    if normalized[-1] in "。！？!?.":
        return normalized
    return normalized + "。"


def _build_entity_subject(
    project: Dict[str, Any],
    positioning: Dict[str, Any],
    *,
    entity: Dict[str, Any],
    mode: str,
    use_case: str,
) -> str:
    seed = entity.get("seed", {})
    profile = entity.get("profile", {})
    current_state = entity.get("currentState", {})
    project_title = str(project.get("title") or "").strip()
    entity_name = str(entity.get("name") or "").strip()
    primary_genre = positioning.get("primaryGenre", "")
    sub_genre = positioning.get("subGenre", "")
    style_tags = ", ".join(positioning.get("styleTags", []))
    appearance_anchor = _build_entity_appearance_anchor(entity)
    head = _entity_subject_head(project_title, entity_name=entity_name, use_case=use_case)
    lines = [head]
    if appearance_anchor:
        lines.append(f"请把{appearance_anchor}当作稳定的视觉锚点。")
    identity_bits = _dedupe_fragments(
        _collect_text_fragments(profile.get("role"), seed.get("archetype"))
    )
    if identity_bits:
        lines.append(f"身份与角色基调偏向{_join_prompt_phrases(identity_bits)}。")
    if profile.get("summary"):
        lines.append(_ensure_sentence(f"人物气质接近{profile['summary']}"))
    physical_state = _extract_current_physical_state(current_state)
    if physical_state:
        lines.append(f"当前外在状态偏{physical_state}。")
    genre_bits = [item for item in (primary_genre, sub_genre, style_tags) if item]
    if genre_bits:
        lines.append(f"整体语境落在{' / '.join(genre_bits)}里。")
    if mode == "image-to-image":
        lines.append("请沿用输入图的人设基础，只微调镜头、质感和局部细节。")
    else:
        lines.append(_entity_use_case_direction(use_case))
    lines.append(_entity_use_case_guardrail(use_case))
    return " ".join(_ensure_sentence(line) for line in lines if line)


def _build_chapter_subject(
    project: Dict[str, Any],
    positioning: Dict[str, Any],
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_text: str,
    mode: str,
    use_case: str,
) -> str:
    project_title = str(project.get("title") or "").strip()
    style_tags = ", ".join(positioning.get("styleTags", []))
    genre_bits = [item for item in (positioning.get("primaryGenre", ""), positioning.get("subGenre", ""), style_tags) if item]
    chapter_label = chapter_title or chapter_id
    lines = [_chapter_subject_head(project_title, chapter_id=chapter_id, chapter_label=chapter_label, use_case=use_case)]
    if genre_bits:
        lines.append(f"整体语境落在{' / '.join(genre_bits)}里。")
    if mode == "image-to-image":
        lines.append("请沿用输入图的角色与场景连续性，把构图、光影和高潮时刻再推清楚。")
    else:
        lines.append(_chapter_use_case_direction(use_case))
    lines.append(_chapter_use_case_guardrail(use_case))
    lines.append("避免提前泄露后续信息，也不要把正文原文整段塞进图像提示词。")
    return " ".join(_ensure_sentence(line) for line in lines if line)


def _template_use_case_candidates(use_case: str) -> List[str]:
    normalized = str(use_case or "").strip() or "chapter-scene"
    fallbacks = {
        "cover-concept": ["cover-poster", "promo"],
        "character-sheet": ["character"],
        "creature-sheet": ["character"],
        "cover-poster": ["promo"],
        "ensemble-key-visual": ["cover-poster", "promo", "chapter-scene"],
        "duel-scene": ["chapter-scene"],
        "chase-escape": ["chapter-scene"],
        "comic-relief": ["chapter-scene", "character"],
        "product": ["prop-relic", "promo", "character"],
        "prop-relic": ["promo", "character"],
        "manga-panel": ["chapter-scene"],
        "manga-page": ["manga-panel", "chapter-scene", "promo"],
    }
    candidates = [normalized]
    candidates.extend(fallbacks.get(normalized, []))
    deduped: List[str] = []
    for item in candidates:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def _entity_subject_head(project_title: str, *, entity_name: str, use_case: str) -> str:
    if use_case == "character-sheet":
        return f"《{project_title}》人物设定图，主体是{entity_name}。" if project_title else f"人物设定图，主体是{entity_name}。"
    if use_case == "cover-poster":
        return f"《{project_title}》收藏版人物海报，主视觉核心是{entity_name}。" if project_title else f"收藏版人物海报，主视觉核心是{entity_name}。"
    if use_case == "comic-relief":
        return f"《{project_title}》角色趣味图，主角是{entity_name}。" if project_title else f"角色趣味图，主角是{entity_name}。"
    if use_case == "creature-sheet":
        return f"《{project_title}》生物设定图，主体是{entity_name}。" if project_title else f"生物设定图，主体是{entity_name}。"
    return f"《{project_title}》角色设定图，主角是{entity_name}。" if project_title else f"角色设定图，主角是{entity_name}。"


def _entity_use_case_direction(use_case: str) -> str:
    if use_case == "character-sheet":
        return "优先给出完整人设、服装结构和稳定立绘读感，不需要额外编造剧情。"
    if use_case == "cover-poster":
        return "把人物当成整张海报的外轮廓核心，让人设气质自己带出世界观。"
    if use_case == "comic-relief":
        return "先把角色识别度立住，再把轻松、反差和夸张节奏做出来。"
    if use_case == "creature-sheet":
        return "先把物种辨识度和生物结构立住，再让设定感而不是廉价奇观说话。"
    return "先把角色形象立稳，不需要额外编造剧情，只让人物像已经活在这个故事里。"


def _entity_use_case_guardrail(use_case: str) -> str:
    if use_case == "cover-poster":
        return "轮廓、服饰、职业气质和题材一致性优先，不要把人物海报画成泛用模板主角。"
    if use_case == "character-sheet":
        return "服饰、职业气质和题材一致性优先，不要把设定图画成泛用模板人。"
    if use_case == "comic-relief":
        return "搞笑可以夸张，但角色脸和核心服装不能崩，也不要变成无关 meme。"
    if use_case == "creature-sheet":
        return "生物结构和材质要可信，不要堆廉价奇幻素材。"
    return "服饰、职业气质和题材一致性优先，不要把设定图画成泛用模板人。"


def _chapter_subject_head(project_title: str, *, chapter_id: str, chapter_label: str, use_case: str) -> str:
    if use_case == "cover-poster":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的收藏版史诗叙事海报。" if project_title else f"{chapter_id}《{chapter_label}》的收藏版史诗叙事海报。"
    if use_case == "ensemble-key-visual":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的群像主视觉。" if project_title else f"{chapter_id}《{chapter_label}》的群像主视觉。"
    if use_case == "duel-scene":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的关键对决插图。" if project_title else f"{chapter_id}《{chapter_label}》的关键对决插图。"
    if use_case == "chase-escape":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的追逐逃脱场景插图。" if project_title else f"{chapter_id}《{chapter_label}》的追逐逃脱场景插图。"
    if use_case == "comic-relief":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的轻松搞笑场景图。" if project_title else f"{chapter_id}《{chapter_label}》的轻松搞笑场景图。"
    if use_case == "manga-panel":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的漫画单格分镜。" if project_title else f"{chapter_id}《{chapter_label}》的漫画单格分镜。"
    if use_case == "manga-page":
        return f"《{project_title}》{chapter_id}《{chapter_label}》的漫画分镜页。" if project_title else f"{chapter_id}《{chapter_label}》的漫画分镜页。"
    return f"《{project_title}》{chapter_id}《{chapter_label}》的关键场景插图。" if project_title else f"{chapter_id}《{chapter_label}》的关键场景插图。"


def _chapter_use_case_direction(use_case: str) -> str:
    if use_case == "cover-poster":
        return "不要复述整章，而是把最能代表这一章世界观、关系和象征物的那一下做成海报叙事。"
    if use_case == "ensemble-key-visual":
        return "重点是群像关系和谁压谁的气场，不要平均分配存在感。"
    if use_case == "duel-scene":
        return "只抓住胜负最紧的一刻，让力量差、距离和招式意图自己说话。"
    if use_case == "chase-escape":
        return "优先交代速度、动线和险象环生的压迫感，不复述前因后果。"
    if use_case == "comic-relief":
        return "只抓住最有包袱的一刻，让反差、表情和肢体节奏先落地。"
    if use_case == "manga-panel":
        return "按漫画单格处理，只抓最值得停住的一刻，不要把一整章塞成一张图。"
    if use_case == "manga-page":
        return "按整页分镜处理，优先交代镜头顺序和页内节奏，而不是单张插画式平均铺开。"
    return "只抓住最值得落图的一刻，不复述整章内容。"


def _chapter_use_case_guardrail(use_case: str) -> str:
    if use_case in {"manga-panel", "manga-page"}:
        return "角色外貌与服饰仍以角色卡为准，分镜关系、黑白块面和阅读方向优先，不要把漫画模板画成普通彩图拼贴。"
    if use_case == "cover-poster":
        return "角色外貌与服饰仍以角色卡为准，世界观符号和版式留白要服务海报识别，不要做成杂乱拼贴。"
    if use_case == "comic-relief":
        return "角色外貌与服饰仍以角色卡为准，搞笑感来自情境和表情，不要脱离主题乱玩梗。"
    return "角色外貌与服饰仍以角色卡为准，场景动作、镜头和环境重点由画面自己说话。"


def _chapter_excerpt(chapter_text: str, limit: int = 180) -> str:
    body = chapter_text.replace("#", " ").replace("\r", " ").replace("\n", " ").strip()
    compact = " ".join(body.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _build_entity_appearance_anchor(entity: Dict[str, Any]) -> str:
    profile = entity.get("profile", {}) if isinstance(entity.get("profile"), dict) else {}
    seed = entity.get("seed", {}) if isinstance(entity.get("seed"), dict) else {}
    current_state = entity.get("currentState", {})
    fragments = _collect_text_fragments(
        entity.get("appearance"),
        profile.get("appearance"),
        profile.get("visual"),
        profile.get("look"),
        seed.get("appearance"),
        seed.get("visual"),
    )
    physical_state = _extract_current_physical_state(current_state)
    if physical_state:
        fragments.append(physical_state)
    if not fragments:
        fallback = _collect_text_fragments(entity.get("summary"), profile.get("summary"))
        fragments.extend(fallback[:1])
    return "；".join(_dedupe_fragments(fragments)[:4])


def _extract_current_physical_state(current_state: Any) -> str:
    if isinstance(current_state, dict):
        return str(current_state.get("physicalState") or current_state.get("physical") or "").strip()
    return str(current_state or "").strip()


def _collect_text_fragments(*values: Any) -> List[str]:
    result: List[str] = []
    for value in values:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                result.append(normalized)
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    normalized = item.strip()
                    if normalized:
                        result.append(normalized)
    return result


def _dedupe_fragments(values: List[str]) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
