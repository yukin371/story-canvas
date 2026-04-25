from __future__ import annotations

from typing import Any, Dict, List


def build_entity_illustration_payload(
    state: Dict[str, Any],
    *,
    entity: Dict[str, Any],
    mode: str,
    input_images: List[str] | None = None,
    mask_path: str = "",
    prompt_pack_name: str = "default",
) -> Dict[str, Any]:
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    prompt = _build_entity_prompt(project, positioning, entity, mode=mode)
    return {
        "targetType": "entity",
        "targetId": entity.get("id", ""),
        "targetName": entity.get("name", ""),
        "mode": mode,
        "promptPack": prompt_pack_name,
        "promptText": prompt,
        "inputImages": list(input_images or []),
        "maskPath": mask_path,
        "providerRequest": {
            "prompt": prompt,
            "inputImages": list(input_images or []),
            "maskPath": mask_path,
            "metadata": {
                "targetType": "entity",
                "targetId": entity.get("id", ""),
                "targetName": entity.get("name", ""),
                "mode": mode,
                "promptPack": prompt_pack_name,
            },
        },
    }


def build_chapter_illustration_payload(
    state: Dict[str, Any],
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_text: str,
    mode: str,
    input_images: List[str] | None = None,
    mask_path: str = "",
    prompt_pack_name: str = "default",
) -> Dict[str, Any]:
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    prompt = _build_chapter_prompt(
        project,
        positioning,
        chapter_id=chapter_id,
        chapter_title=chapter_title,
        chapter_text=chapter_text,
        mode=mode,
    )
    return {
        "targetType": "chapter",
        "targetId": chapter_id,
        "targetName": chapter_title,
        "mode": mode,
        "promptPack": prompt_pack_name,
        "promptText": prompt,
        "inputImages": list(input_images or []),
        "maskPath": mask_path,
        "providerRequest": {
            "prompt": prompt,
            "inputImages": list(input_images or []),
            "maskPath": mask_path,
            "metadata": {
                "targetType": "chapter",
                "targetId": chapter_id,
                "targetName": chapter_title,
                "mode": mode,
                "promptPack": prompt_pack_name,
            },
        },
    }


def _build_entity_prompt(
    project: Dict[str, Any],
    positioning: Dict[str, Any],
    entity: Dict[str, Any],
    *,
    mode: str,
) -> str:
    seed = entity.get("seed", {})
    profile = entity.get("profile", {})
    current_state = entity.get("currentState", {})
    project_title = project.get("title", "")
    primary_genre = positioning.get("primaryGenre", "")
    sub_genre = positioning.get("subGenre", "")
    style_tags = ", ".join(positioning.get("styleTags", []))
    lines = [
        f"为小说《{project_title}》生成角色设定图。",
        f"角色：{entity.get('name', '')}。",
    ]
    if seed.get("archetype"):
        lines.append(f"身份原型：{seed['archetype']}。")
    if profile.get("role"):
        lines.append(f"角色定位：{profile['role']}。")
    if profile.get("summary"):
        lines.append(f"人物简介：{profile['summary']}。")
    if current_state.get("physicalState"):
        lines.append(f"当前外在状态：{current_state['physicalState']}。")
    genre_bits = [item for item in (primary_genre, sub_genre, style_tags) if item]
    if genre_bits:
        lines.append(f"题材氛围：{' / '.join(genre_bits)}。")
    if mode == "image-to-image":
        lines.append("这是图生图任务：保持角色身份一致，只重绘风格、镜头和细节，不要改人设。")
    else:
        lines.append("这是文生图任务：先建立稳定的角色视觉锚点，方便后续复用。")
    lines.append("输出应强调人物服饰、职业气质、年代与题材一致性。")
    return " ".join(lines)


def _build_chapter_prompt(
    project: Dict[str, Any],
    positioning: Dict[str, Any],
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_text: str,
    mode: str,
) -> str:
    excerpt = _chapter_excerpt(chapter_text)
    project_title = project.get("title", "")
    style_tags = ", ".join(positioning.get("styleTags", []))
    genre_bits = [item for item in (positioning.get("primaryGenre", ""), positioning.get("subGenre", ""), style_tags) if item]
    lines = [
        f"为小说《{project_title}》的章节 {chapter_id}《{chapter_title or chapter_id}》生成关键场景插图。",
    ]
    if genre_bits:
        lines.append(f"题材氛围：{' / '.join(genre_bits)}。")
    if excerpt:
        lines.append(f"场景摘要：{excerpt}。")
    if mode == "image-to-image":
        lines.append("这是图生图任务：参考输入图保持角色与场景连续性，只强化构图、光影和高潮时刻。")
    else:
        lines.append("这是文生图任务：聚焦章节中的高潮瞬间，突出冲突、动作和视觉焦点。")
    lines.append("避免剧透后续未揭示信息，优先表现当前章已经明确出现的角色、器物和环境。")
    return " ".join(lines)


def _chapter_excerpt(chapter_text: str, limit: int = 180) -> str:
    body = chapter_text.replace("#", " ").replace("\r", " ").replace("\n", " ").strip()
    compact = " ".join(body.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."
