from __future__ import annotations

from typing import Any, Dict, List


def build_entity_illustration_payload(
    state: Dict[str, Any],
    *,
    entity: Dict[str, Any],
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
    subject = _build_entity_subject(project, positioning, entity=entity, mode=mode)
    return _build_payload(
        target_type="entity",
        target_id=entity.get("id", ""),
        target_name=entity.get("name", ""),
        use_case="character",
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
    subject = _build_chapter_subject(
        project,
        positioning,
        chapter_id=chapter_id,
        chapter_title=chapter_title,
        chapter_text=chapter_text,
        mode=mode,
    )
    return _build_payload(
        target_type="chapter",
        target_id=chapter_id,
        target_name=chapter_title,
        use_case="chapter-scene",
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

    exact_mode_match = [
        template
        for template in templates
        if template.get("useCase") == use_case and template.get("mode") == mode
    ]
    if exact_mode_match:
        return exact_mode_match[0]

    use_case_match = [template for template in templates if template.get("useCase") == use_case]
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
        "chapter-scene": "{subject}\n重点抓住{subjectPhrases}，把{detailPhrases}处理得清楚、可信、能直接落图。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "promo": "{subject}\n先把{subjectPhrases}打出来，再把{detailPhrases}和画面节奏收干净。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
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
    subject_phrases = _resolve_lexicon_phrases(lexicon, "subjectPhrases", "common", use_case)
    detail_phrases = _resolve_lexicon_phrases(lexicon, "detailPhrases", "common", use_case)
    mode_phrases = _resolve_lexicon_phrases(lexicon, "modePhrases", "common", mode)
    commercial_phrases = _resolve_lexicon_phrases(lexicon, "commercialPhrases", "common", commercial_mode)
    negative_phrases = _resolve_lexicon_phrases(lexicon, "negativePhrases", "common", use_case, mode)
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
        "chapter-scene": ["人物关系和动作焦点", "场景重心"],
        "promo": ["第一眼视觉钩子", "主卖点"],
    }
    return list(defaults.get(use_case, ["画面重点", "主体识别度"]))


def _default_detail_phrases(use_case: str) -> List[str]:
    defaults = {
        "character": ["面部、服饰和气质层次"],
        "chapter-scene": ["光影、空间层次和关键道具"],
        "promo": ["远近节奏和留白关系"],
    }
    return list(defaults.get(use_case, ["细节层次", "画面完成度"]))


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
    head = f"《{project_title}》角色设定图，主角是{entity_name}。" if project_title else f"角色设定图，主角是{entity_name}。"
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
        lines.append("先把角色形象立稳，不需要额外编造剧情，只让人物像已经活在这个故事里。")
    lines.append("服饰、职业气质和题材一致性优先，不要把设定图画成泛用模板人。")
    return " ".join(_ensure_sentence(line) for line in lines if line)


def _build_chapter_subject(
    project: Dict[str, Any],
    positioning: Dict[str, Any],
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_text: str,
    mode: str,
) -> str:
    project_title = str(project.get("title") or "").strip()
    style_tags = ", ".join(positioning.get("styleTags", []))
    genre_bits = [item for item in (positioning.get("primaryGenre", ""), positioning.get("subGenre", ""), style_tags) if item]
    chapter_label = chapter_title or chapter_id
    if project_title:
        lines = [f"《{project_title}》{chapter_id}《{chapter_label}》的关键场景插图。"]
    else:
        lines = [f"{chapter_id}《{chapter_label}》的关键场景插图。"]
    if genre_bits:
        lines.append(f"整体语境落在{' / '.join(genre_bits)}里。")
    if mode == "image-to-image":
        lines.append("请沿用输入图的角色与场景连续性，把构图、光影和高潮时刻再推清楚。")
    else:
        lines.append("只抓住最值得落图的一刻，不复述整章内容。")
    lines.append("角色外貌与服饰仍以角色卡为准，场景动作、镜头和环境重点由画面自己说话。")
    lines.append("避免提前泄露后续信息，也不要把正文原文整段塞进图像提示词。")
    return " ".join(_ensure_sentence(line) for line in lines if line)


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
