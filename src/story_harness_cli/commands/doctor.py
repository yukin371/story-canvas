from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from story_harness_cli.commands.illustration_support import decorate_generated_entry
from story_harness_cli.protocol import chapter_path, choose_style_profile_name, root_file
from story_harness_cli.protocol.files import resolve_state_path
from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.protocol.schema import default_project_state
from story_harness_cli.protocol.state import merge_defaults
from story_harness_cli.protocol.style_profiles import get_default_style_profiles, merge_with_defaults
from story_harness_cli.services.outline_guard import evaluate_chapter_outline_readiness
from story_harness_cli.services.stats import compute_project_stats
from story_harness_cli.utils.project_meta import (
    is_commercial_serial_project,
    is_machine_label,
    normalize_machine_label,
    normalize_primary_genre,
)


WORKFLOW_FILES = {
    "proposals": "proposals/draft-proposals.yaml",
    "reviews": "reviews/change-requests.yaml",
    "story_reviews": "reviews/story-reviews.yaml",
    "projection": "projections/projection.yaml",
    "context_lens": "projections/context-lens.yaml",
    "projection_log": "logs/projection-log.yaml",
}

WORKFLOW_DIRS = [
    "chapters",
    "proposals",
    "reviews",
    "projections",
    "logs",
]

_TEMPLATE_OPTION_VALUES = {"required", "optional", "off"}


def record_check(checks: List[Dict[str, str]], level: str, code: str, message: str) -> None:
    checks.append({"level": level, "code": code, "message": message})


def validate_json_compatible_file(
    root: Path,
    relative_path: str,
    default_payload: Dict[str, Any],
    checks: List[Dict[str, str]],
) -> Dict[str, Any]:
    path = root_file(root, relative_path)
    if not path.exists():
        record_check(checks, "error", "missing-file", f"缺少必需文件: {relative_path}")
        return json.loads(json.dumps(default_payload))
    try:
        payload = load_json_compatible_yaml(path, default_payload)
    except SystemExit as exc:
        record_check(checks, "error", "invalid-json-compatible-yaml", str(exc))
        return json.loads(json.dumps(default_payload))
    record_check(checks, "info", "parsed-file", f"文件可解析: {relative_path}")
    return payload


def validate_layout_aware_file(
    root: Path,
    state_key: str,
    default_payload: Dict[str, Any],
    checks: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Validate a state file whose location depends on the project layout.

    Uses :func:`resolve_state_path` to find the correct path for *state_key*
    (e.g. ``outline`` may live at ``root/outline.yaml`` or ``root/spec/outline.yaml``).
    """
    path = resolve_state_path(root, state_key)
    display = path.relative_to(root) if path.is_relative_to(root) else str(path)
    if not path.exists():
        record_check(checks, "error", "missing-file", f"缺少必需文件: {display}")
        return json.loads(json.dumps(default_payload))
    try:
        payload = load_json_compatible_yaml(path, default_payload)
    except SystemExit as exc:
        record_check(checks, "error", "invalid-json-compatible-yaml", str(exc))
        return json.loads(json.dumps(default_payload))
    record_check(checks, "info", "parsed-file", f"文件可解析: {display}")
    return payload


def validate_optional_layout_aware_file(
    root: Path,
    state_key: str,
    default_payload: Dict[str, Any],
    checks: List[Dict[str, str]],
) -> Dict[str, Any]:
    path = resolve_state_path(root, state_key)
    display = path.relative_to(root) if path.is_relative_to(root) else str(path)
    if not path.exists():
        return json.loads(json.dumps(default_payload))
    try:
        payload = load_json_compatible_yaml(path, default_payload)
    except SystemExit as exc:
        record_check(checks, "error", "invalid-json-compatible-yaml", str(exc))
        return json.loads(json.dumps(default_payload))
    record_check(checks, "info", "parsed-file", f"文件可解析: {display}")
    return payload


def validate_project_shape(root: Path, checks: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    defaults = default_project_state()
    project_payload = validate_json_compatible_file(root, "project.yaml", defaults["project"], checks)
    illustrations_path = resolve_state_path(root, "illustrations")
    illustrations_payload = defaults["illustrations"]
    if illustrations_path.exists():
        display = illustrations_path.relative_to(root) if illustrations_path.is_relative_to(root) else str(illustrations_path)
        try:
            illustrations_payload = load_json_compatible_yaml(illustrations_path, defaults["illustrations"])
        except SystemExit as exc:
            record_check(checks, "error", "invalid-illustrations", str(exc))
            illustrations_payload = json.loads(json.dumps(defaults["illustrations"]))
        else:
            record_check(checks, "info", "parsed-file", f"文件可解析: {display}")
    state = {
        "project": merge_defaults(project_payload, defaults["project"]),
        "outline": validate_layout_aware_file(root, "outline", defaults["outline"], checks),
        "entities": validate_layout_aware_file(root, "entities", defaults["entities"], checks),
        "timeline": validate_layout_aware_file(root, "timeline", defaults["timeline"], checks),
        "branches": validate_json_compatible_file(root, "branches.yaml", defaults["branches"], checks),
        "threads": validate_layout_aware_file(root, "threads", defaults["threads"], checks),
        "structures": validate_layout_aware_file(root, "structures", defaults["structures"], checks),
        "worldbook": merge_defaults(
            validate_optional_layout_aware_file(root, "worldbook", defaults["worldbook"], checks),
            defaults["worldbook"],
        ),
        "foreshadowing": validate_optional_layout_aware_file(root, "foreshadowing", defaults["foreshadowing"], checks),
        "illustrations": merge_defaults(illustrations_payload, defaults["illustrations"]),
    }
    for key, relative_path in WORKFLOW_FILES.items():
        state[key] = validate_json_compatible_file(root, relative_path, defaults[key], checks)
    return state


def validate_project_links(root: Path, state: Dict[str, Dict[str, Any]], checks: List[Dict[str, str]]) -> None:
    chapters = state["outline"].get("chapters", [])
    outline_ids = set()
    for item in chapters:
        chapter_id = item.get("id")
        if not chapter_id:
            record_check(checks, "warning", "missing-chapter-id", "outline.chapters 中存在缺少 id 的条目")
            continue
        outline_ids.add(chapter_id)
        chapter_file = chapter_path(root, chapter_id)
        if chapter_file.exists():
            record_check(checks, "info", "chapter-file", f"已找到章节文件: chapters/{chapter_file.name}")
        else:
            record_check(checks, "error", "missing-chapter-file", f"outline 中声明了 {chapter_id}，但缺少对应章节文件")

    chapters_dir = root / "chapters"
    if chapters_dir.exists():
        orphan_files = sorted(item.stem for item in chapters_dir.glob("*.md") if item.stem not in outline_ids)
        for chapter_id in orphan_files:
            record_check(checks, "warning", "orphan-chapter-file", f"章节文件 {chapter_id}.md 未在 outline.chapters 中声明")

    active_chapter_id = state["project"].get("activeChapterId")
    if active_chapter_id:
        if chapter_path(root, active_chapter_id).exists():
            record_check(checks, "info", "active-chapter", f"activeChapterId 指向现有章节: {active_chapter_id}")
        else:
            record_check(checks, "error", "missing-active-chapter", f"activeChapterId 指向不存在的章节: {active_chapter_id}")
        if active_chapter_id not in outline_ids:
            record_check(checks, "warning", "active-chapter-not-in-outline", f"activeChapterId 未出现在 outline.chapters 中: {active_chapter_id}")

    context_chapter_id = state["context_lens"].get("currentChapterId")
    if context_chapter_id:
        if chapter_path(root, context_chapter_id).exists():
            record_check(checks, "info", "context-chapter", f"context-lens 指向现有章节: {context_chapter_id}")
        else:
            record_check(checks, "warning", "missing-context-chapter", f"context-lens 指向不存在的章节: {context_chapter_id}")


def _check_outline_volumes(root: Path, issues: list) -> None:
    """Validate outline.yaml has volumes structure."""
    outline_path = resolve_state_path(root, "outline")
    if not outline_path.exists():
        return
    outline = load_json_compatible_yaml(outline_path, {})
    volumes = outline.get("volumes")
    if volumes is None:
        issues.append({"level": "warning", "message": "outline.yaml 缺少 volumes 字段，建议运行 brainstorm outline 初始化"})
    else:
        for vol in volumes:
            for ch in vol.get("chapters", []):
                for beat in ch.get("beats", []):
                    if beat.get("status") == "planned" and ch.get("status") == "completed":
                        issues.append({
                            "level": "info",
                            "message": f"卷 '{vol.get('title')}' 章 '{ch.get('title')}' 的 beat '{beat.get('summary')}' 状态仍为 planned，但章节已标记 completed",
                        })


def _check_entity_profiles(root: Path, issues: list) -> None:
    """Validate entities have profile structure."""
    entities_path = resolve_state_path(root, "entities")
    if not entities_path.exists():
        return
    entities_data = load_json_compatible_yaml(entities_path, {})
    for entity in entities_data.get("entities", []):
        if "profile" not in entity:
            issues.append({
                "level": "warning",
                "message": f"实体 '{entity.get('name')}' 缺少 profile 字段，建议重新初始化或运行 entity enrich",
            })
        if "seed" not in entity:
            issues.append({
                "level": "info",
                "message": f"实体 '{entity.get('name')}' 缺少 seed 字段，建议通过 brainstorm character 创建种子",
            })
        if entity.get("source") == "inferred" and not entity.get("profile"):
            issues.append({
                "level": "info",
                "message": f"推断实体 '{entity.get('name')}' 缺少 profile，建议运行 entity enrich 补充",
            })


def _check_threads(root: Path, state: Dict, issues: list) -> None:
    """Check thread (suspense) health."""
    from story_harness_cli.services.thread import check_threads as thread_check

    threads_data = state.get("threads", {})
    if not threads_data.get("threads"):
        return
    outline = state.get("outline", {})
    chapters = outline.get("chapters", [])
    last_ch_id = chapters[-1].get("id") if chapters else None
    result = thread_check(state, current_chapter_id=last_ch_id)
    for w in result.get("warnings", []):
        issues.append({"level": "warning", "message": w.get("message", "")})
    stats = result.get("stats", {})
    if stats.get("overdue", 0) > 0:
        issues.append({"level": "warning", "message": f"有 {stats['overdue']} 条悬念线索已逾期未回收"})
    open_count = stats.get("majorOpen", 0) + stats.get("minorOpen", 0)
    if open_count > 0:
        issues.append({"level": "info", "message": f"有 {open_count} 条悬念线索待回收"})


def _check_arcs(root: Path, state: Dict, issues: list) -> None:
    """Check character arc completeness."""
    from story_harness_cli.services.arc import check_arcs as arc_check

    result = arc_check(state)
    for w in result.get("warnings", []):
        issues.append({"level": "warning", "message": w.get("message", "")})
    for a in result.get("advisory", []):
        issues.append({"level": "info", "message": a.get("message", "")})


def _check_structure_coverage(root: Path, state: Dict, issues: list) -> None:
    """Check narrative structure coverage."""
    from story_harness_cli.services.structure import check_structure as struct_check

    structures = state.get("structures", {})
    if not structures.get("activeStructure"):
        return
    result = struct_check(state)
    for w in result.get("warnings", []):
        level = "warning" if w.get("type") == "missing_critical_beat" else "info"
        issues.append({"level": level, "message": w.get("message", "")})
    coverage = result.get("coverage", 0)
    if coverage < 1.0:
        issues.append({"level": "info", "message": f"叙事结构覆盖率: {int(coverage * 100)}%"})


def _check_chapter_word_counts(
    root: Path,
    state: Dict[str, Dict[str, Any]],
    checks: List[Dict[str, str]],
    *,
    min_chapter_words: int,
    target_chapter_words: int,
) -> None:
    commercial = state.get("project", {}).get("commercialPositioning", {})
    configured_floor = commercial.get("chapterWordFloor", 0) or 0
    configured_target = commercial.get("chapterWordTarget", 0) or 0
    effective_min = max(min_chapter_words, configured_floor)
    effective_target = max(target_chapter_words, configured_target, effective_min)
    stats = compute_project_stats(
        state,
        root,
        min_chapter_words=effective_min,
        target_chapter_words=effective_target,
    )
    for chapter in stats.get("wordCount", {}).get("byChapter", []):
        chapter_id = chapter.get("chapterId") or "unknown-chapter"
        title = chapter.get("title") or chapter_id
        words = chapter.get("words", 0)
        status = chapter.get("status")
        if status == "below-minimum":
            missing = chapter.get("missingToMinimum", 0)
            record_check(
                checks,
                "warning",
                "chapter-below-minimum",
                (
                    f"章节 {chapter_id}《{title}》当前约 {words} 字，"
                    f"低于最低 {effective_min} 字，还差 {missing} 字"
                ),
            )
        elif status == "meets-minimum":
            missing = chapter.get("missingToTarget", 0)
            record_check(
                checks,
                "info",
                "chapter-below-target",
                (
                    f"章节 {chapter_id}《{title}》当前约 {words} 字，"
                    f"已达到最低 {effective_min} 字，但距建议 {effective_target} 字还差 {missing} 字"
                ),
            )


def _check_outline_readiness(root: Path, state: Dict[str, Dict[str, Any]], checks: List[Dict[str, str]]) -> None:
    chapters = state.get("outline", {}).get("chapters", [])
    for chapter in chapters:
        chapter_id = chapter.get("id")
        if not chapter_id:
            continue
        if not chapter_path(root, chapter_id).exists():
            continue
        readiness = evaluate_chapter_outline_readiness(
            state,
            chapter_id,
            require_project_gate=False,
        )
        if readiness["ready"]:
            continue
        missing = "、".join(item["message"] for item in readiness["missing"]) or "缺少前置大纲"
        record_check(
            checks,
            "warning",
            "chapter-outline-not-ready",
            f"章节 {chapter_id}《{readiness['title']}》已有正文文件，但仍未完成大纲前置约束：{missing}",
        )


def _check_project_positioning(state: Dict, checks: List[Dict[str, str]]) -> None:
    project = state.get("project", {})
    positioning = project.get("positioning", {})
    story_contract = project.get("storyContract", {})
    emotional_contract = project.get("emotionalContract", {})
    story_template = project.get("storyTemplate", {})

    primary_genre = positioning.get("primaryGenre", "")
    target_audience = positioning.get("targetAudience", [])
    core_promises = story_contract.get("corePromises", [])
    pace_contract = story_contract.get("paceContract", "")
    core_emotions = emotional_contract.get("coreEmotions", [])
    chapter_emotion_floor = emotional_contract.get("chapterEmotionFloor", [])
    genre = project.get("genre", "")
    template_id = story_template.get("id", "")
    module_policy = story_template.get("modulePolicy", {})

    if not primary_genre:
        record_check(checks, "warning", "missing-primary-genre", "project.positioning.primaryGenre 为空，后续类型化 review 无法稳定切换权重")
    elif not is_machine_label(primary_genre):
        record_check(checks, "warning", "non-normalized-primary-genre", f"primaryGenre 建议使用稳定 slug，当前值为: {primary_genre}")

    normalized_genre = normalize_primary_genre(genre)
    normalized_primary = normalize_primary_genre(primary_genre)
    if genre and primary_genre and normalized_genre and normalized_primary != normalized_genre:
        record_check(checks, "warning", "genre-primary-mismatch", f"genre={genre} 与 primaryGenre={primary_genre} 可能漂移，建议统一")

    if not target_audience:
        record_check(checks, "warning", "missing-target-audience", "project.positioning.targetAudience 为空，读者定位尚未显式声明")
    if not core_promises:
        record_check(checks, "warning", "missing-core-promises", "project.storyContract.corePromises 为空，作品卖点承诺尚未声明")
    if not pace_contract:
        record_check(checks, "info", "missing-pace-contract", "project.storyContract.paceContract 为空，节奏承诺尚未声明")
    if not core_emotions:
        record_check(checks, "info", "missing-core-emotions", "project.emotionalContract.coreEmotions 为空，读者情绪体验尚未显式声明")
    if not chapter_emotion_floor:
        record_check(checks, "info", "missing-chapter-emotion-floor", "project.emotionalContract.chapterEmotionFloor 为空，章节情绪底线尚未显式声明")
    if template_id and not is_machine_label(template_id):
        record_check(checks, "warning", "non-normalized-story-template-id", f"storyTemplate.id 建议使用稳定 slug，当前值为: {template_id}")
    if module_policy and not isinstance(module_policy, dict):
        record_check(checks, "warning", "invalid-story-template-module-policy", "project.storyTemplate.modulePolicy 必须是对象")
    elif isinstance(module_policy, dict):
        for module_name, mode in module_policy.items():
            if mode not in _TEMPLATE_OPTION_VALUES:
                record_check(
                    checks,
                    "warning",
                    "invalid-story-template-module-mode",
                    f"storyTemplate.modulePolicy.{module_name} 取值无效: {mode}",
                )


def _check_story_constraint_modules(root: Path, state: Dict, checks: List[Dict[str, str]]) -> None:
    project = state.get("project", {})
    story_template = project.get("storyTemplate", {})
    module_policy = story_template.get("modulePolicy", {})
    if not isinstance(module_policy, dict) or not module_policy:
        return

    worldbook = state.get("worldbook", {})
    foreshadowing = state.get("foreshadowing", {})
    entities = state.get("entities", {}).get("entities", [])
    worldbook_path = resolve_state_path(root, "worldbook")
    foreshadow_path = resolve_state_path(root, "foreshadowing")

    def _is_required(module_name: str) -> bool:
        return module_policy.get(module_name) == "required"

    if _is_required("worldbook") and not worldbook_path.exists():
        record_check(checks, "warning", "missing-required-worldbook", "storyTemplate 要求 worldbook，但项目中尚未创建 worldbook.yaml")
    if _is_required("worldRules") and not worldbook.get("worldRules", []):
        record_check(checks, "warning", "missing-required-world-rules", "storyTemplate 要求 worldRules，但 worldbook.worldRules 为空")
    if _is_required("factions") and not worldbook.get("factions", []):
        record_check(checks, "warning", "missing-required-factions", "storyTemplate 要求 factions，但 worldbook.factions 为空")
    if _is_required("foreshadowLedger"):
        foreshadows = foreshadowing.get("foreshadows", [])
        if not foreshadow_path.exists():
            record_check(checks, "warning", "missing-required-foreshadow-ledger", "storyTemplate 要求 foreshadow ledger，但项目中尚未创建 foreshadowing.yaml")
        elif not foreshadows:
            record_check(checks, "warning", "empty-required-foreshadow-ledger", "storyTemplate 要求 foreshadow ledger，但 foreshadowing.foreshadows 为空")
    if _is_required("characterStateTracking"):
        tracked_entities = [
            entity for entity in entities
            if isinstance(entity, dict) and (entity.get("state") or entity.get("changeLog"))
        ]
        if not tracked_entities:
            record_check(checks, "warning", "missing-character-state-tracking", "storyTemplate 要求 character state tracking，但 entities 中尚无 state/changeLog 数据")


def _check_commercial_positioning(state: Dict, checks: List[Dict[str, str]]) -> None:
    project = state.get("project", {})
    commercial = project.get("commercialPositioning", {})
    if not is_commercial_serial_project(project) and not any(commercial.values()):
        return

    premise = commercial.get("premise", "")
    hook_line = commercial.get("hookLine", "")
    hook_stack = commercial.get("hookStack", [])
    benchmark_works = commercial.get("benchmarkWorks", [])
    target_platform = commercial.get("targetPlatform", "")
    serialization_model = commercial.get("serializationModel", "")
    release_cadence = commercial.get("releaseCadence", "")
    chapter_word_floor = commercial.get("chapterWordFloor", 0)
    chapter_word_target = commercial.get("chapterWordTarget", 0)

    if not premise:
        record_check(checks, "warning", "missing-commercial-premise", "commercialPositioning.premise 为空，连载作品的商业主张尚未明确")
    if not hook_line:
        record_check(checks, "warning", "missing-commercial-hook-line", "commercialPositioning.hookLine 为空，缺少可复用的一句话钩子")
    if not hook_stack:
        record_check(checks, "warning", "missing-commercial-hook-stack", "commercialPositioning.hookStack 为空，缺少稳定的追读钩子结构")
    if not benchmark_works:
        record_check(checks, "info", "missing-commercial-benchmarks", "commercialPositioning.benchmarkWorks 为空，建议补充对标作品/参考样板")
    if not target_platform:
        record_check(checks, "warning", "missing-commercial-target-platform", "commercialPositioning.targetPlatform 为空，平台感与投放口径尚未声明")
    if not serialization_model:
        record_check(checks, "warning", "missing-commercial-serialization-model", "commercialPositioning.serializationModel 为空，连载模型尚未明确")
    if not release_cadence:
        record_check(checks, "info", "missing-commercial-release-cadence", "commercialPositioning.releaseCadence 为空，更新节奏尚未明确")
    if chapter_word_floor and chapter_word_target and chapter_word_target < chapter_word_floor:
        record_check(
            checks,
            "warning",
            "commercial-word-target-order",
            "commercialPositioning.chapterWordTarget 不应小于 chapterWordFloor",
        )


def _check_style_profiles(root: Path, state: Dict[str, Dict[str, Any]], checks: List[Dict[str, str]]) -> None:
    profile_path = root / "style-profiles.yaml"
    active_profile = choose_style_profile_name(state.get("project", {}))
    record_check(checks, "info", "active-style-profile", f"当前自动 style profile: {active_profile}")

    if not profile_path.exists():
        return

    try:
        raw_payload = load_json_compatible_yaml(profile_path, {})
    except SystemExit as exc:
        record_check(checks, "error", "invalid-style-profiles", str(exc))
        return

    record_check(checks, "info", "parsed-style-profiles", "文件可解析: style-profiles.yaml")

    profiles = raw_payload.get("profiles")
    if profiles is None:
        record_check(checks, "warning", "missing-style-profiles", "style-profiles.yaml 缺少 profiles 字段")
        return
    if not isinstance(profiles, dict):
        record_check(checks, "warning", "invalid-style-profiles-shape", "style-profiles.yaml 的 profiles 必须是对象")
        return

    merged_profiles = merge_with_defaults(raw_payload)
    defaults = get_default_style_profiles()
    if active_profile not in merged_profiles:
        record_check(checks, "warning", "missing-active-style-profile", f"自动选中的 style profile 不存在: {active_profile}")

    for profile_name, payload in profiles.items():
        if not isinstance(payload, dict):
            record_check(checks, "warning", "invalid-style-profile-payload", f"profile '{profile_name}' 必须是对象")
            continue

        threshold_map = payload.get("patternThresholds", {})
        if not isinstance(threshold_map, dict):
            record_check(checks, "warning", "invalid-style-thresholds", f"profile '{profile_name}' 的 patternThresholds 必须是对象")
        else:
            for pattern_id, value in threshold_map.items():
                if not isinstance(value, (int, float)) or value <= 0:
                    record_check(
                        checks,
                        "warning",
                        "invalid-style-threshold-value",
                        f"profile '{profile_name}' 的阈值 {pattern_id} 必须是大于 0 的数字",
                    )

        extra_patterns = payload.get("extraPatterns", {})
        if not isinstance(extra_patterns, dict):
            record_check(checks, "warning", "invalid-style-extra-patterns", f"profile '{profile_name}' 的 extraPatterns 必须是对象")
        else:
            for pattern_id, pattern_list in extra_patterns.items():
                if not isinstance(pattern_list, list) or not all(isinstance(item, str) for item in pattern_list):
                    record_check(
                        checks,
                        "warning",
                        "invalid-style-pattern-list",
                        f"profile '{profile_name}' 的 extraPatterns.{pattern_id} 必须是字符串列表",
                    )

        if profile_name in defaults:
            record_check(checks, "info", "style-profile-override", f"profile '{profile_name}' 覆盖了 builtin style profile")
        else:
            record_check(checks, "info", "style-profile-custom", f"profile '{profile_name}' 是项目自定义 style profile")


def _check_illustration_assets(root: Path, state: Dict[str, Dict[str, Any]], checks: List[Dict[str, str]]) -> None:
    generated = state.get("illustrations", {}).get("generated", [])

    asset_root = root / "assets" / "illustrations"
    referenced_paths: set[Path] = set()
    for entry in generated:
        decorated = decorate_generated_entry(root, state, entry)
        illustration_id = (
            decorated.get("id")
            or decorated.get("chapterId")
            or decorated.get("entityId")
            or decorated.get("type")
            or "unknown-illustration"
        )
        assets = decorated.get("artifacts", [])
        target_ref = decorated.get("targetRef", {})
        input_refs = decorated.get("inputImageRefs", [])
        mask_ref = decorated.get("maskRef", {})

        if not target_ref.get("targetId"):
            record_check(
                checks,
                "warning",
                "illustration-target-missing",
                f"插图记录 {illustration_id} 缺少 chapterId/entityId，无法确认引用目标",
            )
        elif not target_ref.get("declaredInState"):
            record_check(
                checks,
                "warning",
                "illustration-target-not-found",
                f"插图记录 {illustration_id} 引用了不存在的 {target_ref.get('type')} 目标: {target_ref.get('targetId')}",
            )
        elif target_ref.get("type") == "chapter" and not target_ref.get("contentFileExists"):
            record_check(
                checks,
                "warning",
                "illustration-target-chapter-file-missing",
                f"插图记录 {illustration_id} 引用的章节正文不存在: {target_ref.get('targetId')}",
            )

        if decorated.get("mode") == "image-to-image" and not input_refs:
            record_check(
                checks,
                "warning",
                "illustration-input-missing",
                f"图生图记录 {illustration_id} 缺少 inputImages 引用",
            )
        for input_ref in input_refs:
            if not input_ref.get("exists"):
                record_check(
                    checks,
                    "warning",
                    "illustration-input-not-found",
                    f"插图记录 {illustration_id} 缺少输入参考图: {input_ref.get('filePath')}",
                )
        if mask_ref.get("filePath") and not mask_ref.get("exists"):
            record_check(
                checks,
                "warning",
                "illustration-mask-not-found",
                f"插图记录 {illustration_id} 的 mask 文件不存在: {mask_ref.get('filePath')}",
            )

        if not assets:
            record_check(
                checks,
                "warning",
                "illustration-missing-assets",
                f"插图记录 {illustration_id} 缺少 filePath/artifacts，无法校验资产落盘状态",
            )
            continue

        metadata_asset_count = decorated.get("metadata", {}).get("assetCount", 0)
        if metadata_asset_count and metadata_asset_count != len(assets):
            record_check(
                checks,
                "warning",
                "illustration-asset-count-mismatch",
                f"插图记录 {illustration_id} 的 metadata.assetCount={metadata_asset_count} 与 artifacts 数量 {len(assets)} 不一致",
            )

        primary_assets = [asset for asset in assets if asset.get("isPrimary")]
        if len(primary_assets) != 1:
            record_check(
                checks,
                "warning",
                "illustration-primary-asset-invalid",
                f"插图记录 {illustration_id} 的主图标记异常，当前 primary 数量为 {len(primary_assets)}",
            )
        elif decorated.get("filePath") and decorated.get("filePath") != primary_assets[0].get("filePath"):
            record_check(
                checks,
                "warning",
                "illustration-primary-path-mismatch",
                f"插图记录 {illustration_id} 的 filePath 与主图 artifacts[isPrimary] 不一致",
            )

        for asset in assets:
            file_path = asset.get("filePath", "")
            if not file_path:
                record_check(
                    checks,
                    "warning",
                    "illustration-asset-path-missing",
                    f"插图记录 {illustration_id} 存在缺少 filePath 的资产条目",
                )
                continue

            path = Path(file_path)
            resolved_path = path.resolve()
            referenced_paths.add(resolved_path)
            try:
                relative_display = resolved_path.relative_to(root)
            except ValueError:
                record_check(
                    checks,
                    "warning",
                    "illustration-asset-outside-root",
                    f"插图记录 {illustration_id} 的资产位于项目外部: {file_path}",
                )
                continue

            if not asset.get("exists"):
                record_check(
                    checks,
                    "warning",
                    "missing-illustration-asset",
                    f"插图记录 {illustration_id} 缺少资产文件: {relative_display}",
                )
                continue

            if asset.get("bytes", 0) and resolved_path.stat().st_size != asset.get("bytes", 0):
                record_check(
                    checks,
                    "warning",
                    "illustration-asset-bytes-mismatch",
                    f"插图记录 {illustration_id} 的资产字节数与记录不一致: {relative_display}",
                )

    if asset_root.exists():
        orphan_files = []
        for path in asset_root.rglob("*"):
            if not path.is_file():
                continue
            if path.resolve() not in referenced_paths:
                orphan_files.append(path.relative_to(root))
        for relative_path in sorted(orphan_files):
            record_check(
                checks,
                "info",
                "orphan-illustration-asset",
                f"发现未被 illustrations.yaml 引用的插图资产: {relative_path}",
            )


def command_doctor(args) -> int:
    root = Path(args.root).resolve()
    checks: List[Dict[str, str]] = []

    if not root.exists():
        raise SystemExit(f"{root} 不存在")
    if args.min_chapter_words <= 0:
        raise SystemExit("--min-chapter-words 必须大于 0")
    if args.target_chapter_words < args.min_chapter_words:
        raise SystemExit("--target-chapter-words 不能小于 --min-chapter-words")

    # -- Always-at-root files (project.yaml, branches.yaml) ----------------------
    _ROOT_ONLY_FILES = ["project.yaml", "branches.yaml"]
    for relative_path in _ROOT_ONLY_FILES:
        if root_file(root, relative_path).exists():
            record_check(checks, "info", "root-file", f"已找到根文件: {relative_path}")
        else:
            record_check(checks, "error", "missing-root-file", f"缺少根文件: {relative_path}")

    # -- Layout-aware spec files -------------------------------------------------
    _SPEC_CHECK_KEYS = ["outline", "entities", "timeline", "threads", "structures"]
    for key in _SPEC_CHECK_KEYS:
        resolved = resolve_state_path(root, key)
        display = resolved.relative_to(root) if resolved.is_relative_to(root) else str(resolved)
        if resolved.exists():
            record_check(checks, "info", "root-file", f"已找到规范文件: {display}")
        else:
            record_check(checks, "error", "missing-root-file", f"缺少规范文件: {display}")

    for directory in WORKFLOW_DIRS:
        path = root / directory
        if path.exists() and path.is_dir():
            record_check(checks, "info", "workflow-dir", f"已找到目录: {directory}")
        else:
            record_check(checks, "error", "missing-workflow-dir", f"缺少必需目录: {directory}")

    state = validate_project_shape(root, checks)
    validate_project_links(root, state, checks)
    _check_project_positioning(state, checks)
    _check_commercial_positioning(state, checks)
    _check_story_constraint_modules(root, state, checks)
    _check_style_profiles(root, state, checks)
    _check_illustration_assets(root, state, checks)
    _check_outline_volumes(root, checks)
    _check_outline_readiness(root, state, checks)
    _check_entity_profiles(root, checks)
    _check_threads(root, state, checks)
    _check_arcs(root, state, checks)
    _check_structure_coverage(root, state, checks)
    _check_chapter_word_counts(
        root,
        state,
        checks,
        min_chapter_words=args.min_chapter_words,
        target_chapter_words=args.target_chapter_words,
    )

    error_count = sum(1 for item in checks if item["level"] == "error")
    warning_count = sum(1 for item in checks if item["level"] == "warning")
    ok = error_count == 0 and (warning_count == 0 or not args.strict)
    payload = {
        "root": str(root),
        "ok": ok,
        "strict": args.strict,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "infos": sum(1 for item in checks if item["level"] == "info"),
        },
        "checks": checks,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def register_doctor_commands(subparsers) -> None:
    doctor_parser = subparsers.add_parser("doctor", help="Validate story project structure and workflow files")
    doctor_parser.add_argument("--root", required=True)
    doctor_parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    doctor_parser.add_argument("--min-chapter-words", type=int, default=2000, help="Minimum acceptable words per chapter")
    doctor_parser.add_argument("--target-chapter-words", type=int, default=3000, help="Recommended words per chapter")
    doctor_parser.set_defaults(func=command_doctor)
