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
        pack_ref=pack_ref,
        template=resolved_template,
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
    pack_ref: Dict[str, Any],
    template: Dict[str, Any],
    modifiers: List[Dict[str, Any]],
    user_extra_prompt: str,
    subject: str,
    commercial_prompt: str,
) -> Dict[str, Any]:
    style_fragments = [
        str(item.get("promptFragment") or "").strip()
        for item in modifiers
        if str(item.get("promptFragment") or "").strip()
    ]
    resolved_prompt = _render_prompt_template(
        str(template.get("promptTemplate") or "{subject}\n{styleModifiers}\n{userExtraPrompt}"),
        {
            "subject": subject,
            "styleModifiers": ", ".join(style_fragments),
            "userExtraPrompt": str(user_extra_prompt or "").strip(),
            "commercialPrompt": commercial_prompt,
        },
    )
    return {
        "packRef": pack_ref,
        "templateRef": template.get("id", ""),
        "modifierRefs": [item.get("id", "") for item in modifiers],
        "userExtraPrompt": str(user_extra_prompt or "").strip(),
        "resolvedPrompt": resolved_prompt,
    }


def _render_prompt_template(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    lines = [line.strip() for line in rendered.splitlines()]
    return "\n".join(line for line in lines if line)


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
    project_title = project.get("title", "")
    primary_genre = positioning.get("primaryGenre", "")
    sub_genre = positioning.get("subGenre", "")
    style_tags = ", ".join(positioning.get("styleTags", []))
    appearance_anchor = _build_entity_appearance_anchor(entity)
    lines = [
        f"为小说《{project_title}》生成角色设定图。",
        f"角色：{entity.get('name', '')}。",
    ]
    if appearance_anchor:
        lines.append(f"角色外貌锚点：{appearance_anchor}。")
    if seed.get("archetype"):
        lines.append(f"身份原型：{seed['archetype']}。")
    if profile.get("role"):
        lines.append(f"角色定位：{profile['role']}。")
    if profile.get("summary"):
        lines.append(f"人物简介：{profile['summary']}。")
    physical_state = _extract_current_physical_state(current_state)
    if physical_state:
        lines.append(f"当前外在状态：{physical_state}。")
    genre_bits = [item for item in (primary_genre, sub_genre, style_tags) if item]
    if genre_bits:
        lines.append(f"题材氛围：{' / '.join(genre_bits)}。")
    if mode == "image-to-image":
        lines.append("这是图生图任务：保持角色身份一致，只重绘风格、镜头和细节，不要改人设。")
    else:
        lines.append("这是文生图任务：优先建立稳定的角色视觉锚点，方便后续章节和商业图复用。")
    lines.append("输出应优先服从角色卡外貌、服饰、职业气质和题材一致性，不要擅自扩写剧情正文。")
    return " ".join(lines)


def _build_chapter_subject(
    project: Dict[str, Any],
    positioning: Dict[str, Any],
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_text: str,
    mode: str,
) -> str:
    project_title = project.get("title", "")
    style_tags = ", ".join(positioning.get("styleTags", []))
    genre_bits = [item for item in (positioning.get("primaryGenre", ""), positioning.get("subGenre", ""), style_tags) if item]
    lines = [
        f"为小说《{project_title}》的章节 {chapter_id}《{chapter_title or chapter_id}》生成关键场景插图。",
    ]
    if genre_bits:
        lines.append(f"题材氛围：{' / '.join(genre_bits)}。")
    if mode == "image-to-image":
        lines.append("这是图生图任务：参考输入图保持角色与场景连续性，只强化构图、光影和高潮时刻。")
    else:
        lines.append("这是文生图任务：只建立章节场景基线，不直接复述正文内容。")
    lines.append("角色外貌与服饰以角色卡为准，场景动作、镜头、器物和环境由用户补充提示词决定。")
    lines.append("避免剧透后续未揭示信息，不要把整章文本压进 prompt。")
    return " ".join(lines)


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
