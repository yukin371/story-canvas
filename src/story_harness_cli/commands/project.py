from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from story_harness_cli.commands.project_support import build_chapter_start_guide
from story_harness_cli.protocol import chapter_path, load_project_state, save_state
from story_harness_cli.protocol.files import LAYOUT_FLAT, LAYOUT_LAYERED, resolve_state_path
from story_harness_cli.protocol.io import dump_json_compatible_yaml
from story_harness_cli.protocol.schema import default_project_state
from story_harness_cli.utils import now_iso
from story_harness_cli.utils.project_meta import normalize_machine_label, normalize_primary_genre


_TEMPLATE_OPTION_VALUES = {"off", "optional", "required"}


def _parse_module_policy(items: list[str] | None) -> Dict[str, str]:
    policy: Dict[str, str] = {}
    for raw_item in items or []:
        item = raw_item.strip()
        if not item:
            continue
        if "=" not in item:
            raise SystemExit("`--module-policy` 必须使用 key=value 形式")
        key, value = item.split("=", 1)
        normalized_key = normalize_machine_label(key)
        normalized_value = normalize_machine_label(value)
        if not normalized_key or not normalized_value:
            raise SystemExit("`--module-policy` 不能包含空 key 或空 value")
        if normalized_value not in _TEMPLATE_OPTION_VALUES:
            raise SystemExit("`--module-policy` 的 value 只能是 off / optional / required")
        policy[normalized_key] = normalized_value
    return policy


def _markdown_bullets(items: list[str]) -> list[str]:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    return [f"- {item}" for item in cleaned] if cleaned else ["- TBD"]


def _seed_or_tbd(value: object, *, fallback: str = "TBD") -> str:
    text = str(value or "").strip()
    return text or fallback


def _build_prd_markdown(
    project: Dict[str, object],
    *,
    chapter_id: str,
    chapter_title: str,
    volume_goal: str = "",
    reader_hook: str = "",
    suppression_source: str = "",
    onboarding_focus: str = "",
    chapter_handoff: str = "",
    chapter_delivery: str = "",
) -> str:
    positioning = project.get("positioning", {}) if isinstance(project.get("positioning"), dict) else {}
    story_contract = project.get("storyContract", {}) if isinstance(project.get("storyContract"), dict) else {}
    emotional_contract = (
        project.get("emotionalContract", {}) if isinstance(project.get("emotionalContract"), dict) else {}
    )
    story_template = project.get("storyTemplate", {}) if isinstance(project.get("storyTemplate"), dict) else {}
    commercial = (
        project.get("commercialPositioning", {})
        if isinstance(project.get("commercialPositioning"), dict)
        else {}
    )
    title = str(project.get("title", "")).strip() or "未命名项目"
    genre = str(project.get("genre", "")).strip() or "TBD"
    primary_genre = str(positioning.get("primaryGenre", "")).strip() or "TBD"
    sub_genre = str(positioning.get("subGenre", "")).strip() or "TBD"
    style_tags = [str(item).strip() for item in positioning.get("styleTags", []) if str(item).strip()]
    target_audience = [str(item).strip() for item in positioning.get("targetAudience", []) if str(item).strip()]
    core_promises = [str(item).strip() for item in story_contract.get("corePromises", []) if str(item).strip()]
    avoidances = [str(item).strip() for item in story_contract.get("avoidances", []) if str(item).strip()]
    core_emotions = [str(item).strip() for item in emotional_contract.get("coreEmotions", []) if str(item).strip()]
    review_focus = [str(item).strip() for item in story_template.get("reviewFocus", []) if str(item).strip()]
    hook_stack = [str(item).strip() for item in commercial.get("hookStack", []) if str(item).strip()]
    reader_hook_text = reader_hook.strip() or str(commercial.get("hookLine", "")).strip()

    lines = [
        f"# PRD: {title}",
        "",
        "> 状态: draft",
        "> 说明: 用于明确项目定位、卷级职责与当前启动焦点；不是协议真相源。",
        "",
        "## 1. 项目定义",
        "",
        f"- 书名: {title}",
        f"- genre: `{genre}`",
        f"- primaryGenre: `{primary_genre}`",
        f"- subGenre: `{sub_genre}`",
        f"- styleTags: {', '.join(style_tags) if style_tags else 'TBD'}",
        "",
        "## 2. 目标读者",
        "",
        *_markdown_bullets(target_audience),
        "",
        "## 3. 核心承诺",
        "",
        *_markdown_bullets(core_promises),
        "",
        "## 4. 明确避免",
        "",
        *_markdown_bullets(avoidances),
        "",
        "## 5. 情绪与体验",
        "",
        *_markdown_bullets(core_emotions),
        "",
        "## 6. 商业与连载钩子",
        "",
        f"- premise: {str(commercial.get('premise', '')).strip() or 'TBD'}",
        f"- hookLine: {str(commercial.get('hookLine', '')).strip() or 'TBD'}",
        f"- targetPlatform: {str(commercial.get('targetPlatform', '')).strip() or 'TBD'}",
        f"- chapterWordFloor: {commercial.get('chapterWordFloor', 0) or 'TBD'}",
        f"- chapterWordTarget: {commercial.get('chapterWordTarget', 0) or 'TBD'}",
        f"- hookStack: {', '.join(hook_stack) if hook_stack else 'TBD'}",
        "",
        "## 7. 题材与审查重点",
        "",
        f"- storyTemplate: {str(story_template.get('id', '')).strip() or 'TBD'}",
        f"- reviewFocus: {', '.join(review_focus) if review_focus else 'TBD'}",
        "",
        "## 8. 第一卷 / 当前启动焦点",
        "",
        f"- 卷目标: {_seed_or_tbd(volume_goal)}",
        f"- 读者钩子: {_seed_or_tbd(reader_hook_text)}",
        f"- 压制源与预期爆发点: {_seed_or_tbd(suppression_source)}",
        f"- 关键设定 onboarding: {_seed_or_tbd(onboarding_focus)}",
        "",
        "## 9. 当前起始章节",
        "",
        f"- activeChapterId: `{chapter_id}`",
        f"- chapterTitle: {chapter_title}",
        f"- 本章承接点: {_seed_or_tbd(chapter_handoff)}",
        f"- 本章交付点: {_seed_or_tbd(chapter_delivery)}",
        "",
        "## 10. 待补清单",
        "",
        "- 明确第一卷的小闭环交付",
        "- 明确核心世界规则/制度代价",
        "- 明确主角阶段性目标、主要阻力与短线爽点",
        "",
    ]
    return "\n".join(lines)


def command_init(args) -> int:
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)

    layout_name = getattr(args, "layout", "flat")
    layout = LAYOUT_LAYERED if layout_name == "layered" else LAYOUT_FLAT
    core_emotions = getattr(args, "core_emotion", None) or []
    chapter_emotion_floor = getattr(args, "chapter_emotion_floor", None) or []
    forbidden_emotions = getattr(args, "forbidden_emotion", None) or []
    default_reveal_mode = getattr(args, "default_reveal_mode", "") or ""
    allow_direct_explain_at_climax = bool(getattr(args, "allow_direct_explain_at_climax", False))
    story_template_id = getattr(args, "story_template_id", "") or ""
    story_template_label = getattr(args, "story_template_label", "") or ""
    module_policy = getattr(args, "module_policy", None)
    review_focus = getattr(args, "review_focus", None) or []

    # In layered layout, create spec/ and spec/outlines/ directories
    if layout == LAYOUT_LAYERED:
        (root / "spec").mkdir(exist_ok=True)
        (root / "spec" / "outlines").mkdir(exist_ok=True)

    (root / "chapters").mkdir(exist_ok=True)
    (root / "proposals").mkdir(exist_ok=True)
    (root / "reviews").mkdir(exist_ok=True)
    (root / "projections").mkdir(exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)

    defaults = default_project_state()
    project = defaults["project"] | {
        "title": args.title,
        "genre": args.genre,
        "defaultMode": args.default_mode,
        "activeChapterId": args.chapter_id,
        "positioning": {
            "primaryGenre": normalize_primary_genre(args.primary_genre or args.genre),
            "subGenre": normalize_machine_label(args.sub_genre or ""),
            "styleTags": [normalize_machine_label(item) for item in (args.style_tag or []) if item.strip()],
            "targetAudience": [normalize_machine_label(item) for item in (args.target_audience or []) if item.strip()],
        },
        "storyContract": {
            "corePromises": args.core_promise or [],
            "avoidances": args.avoidance or [],
            "endingContract": args.ending_contract or "",
            "paceContract": args.pace_contract or "",
        },
        "emotionalContract": {
            "coreEmotions": [item.strip() for item in core_emotions if item.strip()],
            "chapterEmotionFloor": [item.strip() for item in chapter_emotion_floor if item.strip()],
            "forbiddenEmotions": [item.strip() for item in forbidden_emotions if item.strip()],
            "revealPreference": {
                "defaultMode": normalize_machine_label(default_reveal_mode),
                "allowDirectExplainAtClimax": allow_direct_explain_at_climax,
            },
        },
        "storyTemplate": {
            "id": normalize_machine_label(story_template_id),
            "label": story_template_label or "",
            "modulePolicy": _parse_module_policy(module_policy),
            "reviewFocus": [item.strip() for item in review_focus if item.strip()],
        },
        "commercialPositioning": {
            "premise": args.premise or "",
            "hookLine": args.hook_line or "",
            "hookStack": [normalize_machine_label(item) for item in (args.hook_stack or []) if item.strip()],
            "benchmarkWorks": [item.strip() for item in (args.benchmark_work or []) if item.strip()],
            "targetPlatform": normalize_machine_label(args.target_platform or ""),
            "serializationModel": args.serialization_model or "",
            "releaseCadence": args.release_cadence or "",
            "chapterWordFloor": args.chapter_word_floor or 0,
            "chapterWordTarget": args.chapter_word_target or 0,
        },
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    initial_chapter = {
        "id": args.chapter_id,
        "title": args.chapter_title,
        "status": "draft",
        "beats": [],
        "scenePlans": [],
    }
    volume_id = getattr(args, "volume_id", "") or ""
    volume_title = getattr(args, "volume_title", "") or ""
    volume_theme = getattr(args, "volume_theme", "") or ""
    outline = {
        "chapters": [],
        "chapterDirections": [],
    }
    if volume_id or volume_title or volume_theme:
        outline["volumes"] = [
            {
                "id": volume_id or "volume-001",
                "title": volume_title or "第一卷",
                "theme": volume_theme,
                "chapters": [initial_chapter],
            }
        ]
    else:
        outline["chapters"] = [initial_chapter]

    # project.yaml always at root
    dump_json_compatible_yaml(resolve_state_path(root, "project", layout=layout), project)

    # spec-eligible files routed through resolve_state_path
    dump_json_compatible_yaml(resolve_state_path(root, "outline", layout=layout), outline)
    dump_json_compatible_yaml(resolve_state_path(root, "entities", layout=layout), defaults["entities"])
    dump_json_compatible_yaml(resolve_state_path(root, "timeline", layout=layout), defaults["timeline"])
    dump_json_compatible_yaml(resolve_state_path(root, "threads", layout=layout), defaults["threads"])
    dump_json_compatible_yaml(resolve_state_path(root, "structures", layout=layout), defaults["structures"])
    dump_json_compatible_yaml(resolve_state_path(root, "worldbook", layout=layout), defaults["worldbook"])
    dump_json_compatible_yaml(resolve_state_path(root, "foreshadowing", layout=layout), defaults["foreshadowing"])

    # branches is not in _SPEC_KEYS, stays at root via resolve_state_path fallback
    dump_json_compatible_yaml(root / "branches.yaml", defaults["branches"])

    # subdir-resident files (same path in both layouts)
    dump_json_compatible_yaml(resolve_state_path(root, "proposals", layout=layout), defaults["proposals"])
    dump_json_compatible_yaml(resolve_state_path(root, "reviews", layout=layout), defaults["reviews"])
    dump_json_compatible_yaml(resolve_state_path(root, "story_reviews", layout=layout), defaults["story_reviews"])
    dump_json_compatible_yaml(resolve_state_path(root, "projection", layout=layout), defaults["projection"])
    dump_json_compatible_yaml(resolve_state_path(root, "context_lens", layout=layout), {"currentChapterId": args.chapter_id, "lenses": []})
    dump_json_compatible_yaml(resolve_state_path(root, "projection_log", layout=layout), defaults["projection_log"])

    chapter_file = chapter_path(root, args.chapter_id)
    if not chapter_file.exists() or args.force:
        chapter_file.write_text(f"# {args.chapter_title}\n", encoding="utf-8")

    prd_file = root / "PRD.md"
    if not prd_file.exists() or args.force:
        prd_file.write_text(
            _build_prd_markdown(
                project,
                chapter_id=args.chapter_id,
                chapter_title=args.chapter_title,
                volume_goal=getattr(args, "volume_goal", "") or "",
                reader_hook=getattr(args, "reader_hook", "") or "",
                suppression_source=getattr(args, "suppression_source", "") or "",
                onboarding_focus=getattr(args, "onboarding_focus", "") or "",
                chapter_handoff=getattr(args, "chapter_handoff", "") or "",
                chapter_delivery=getattr(args, "chapter_delivery", "") or "",
            ),
            encoding="utf-8",
        )

    start_guide = build_chapter_start_guide(
        root,
        args.chapter_id,
        missing_codes=["missing-direction", "missing-beats", "missing-scene-plans"],
    )

    print(
        json.dumps(
            {
                "root": str(root),
                "title": args.title,
                "genre": args.genre,
                "positioning": project["positioning"],
                "storyContract": project["storyContract"],
                "emotionalContract": project["emotionalContract"],
                "storyTemplate": project["storyTemplate"],
                "commercialPositioning": project["commercialPositioning"],
                "chapterId": args.chapter_id,
                "volumeId": outline.get("volumes", [{}])[0].get("id", "") if outline.get("volumes") else "",
                "volumeTitle": outline.get("volumes", [{}])[0].get("title", "") if outline.get("volumes") else "",
                "chapterFile": str(chapter_file),
                "prdFile": str(prd_file),
                "nextActions": start_guide["notes"],
                "suggestedCommands": start_guide["suggestedCommands"],
                "startGuide": start_guide,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def register_project_commands(subparsers) -> None:
    init_parser = subparsers.add_parser("init", help="Initialize a Story Canvas project")
    init_parser.add_argument("--root", required=True)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--genre", required=True)
    init_parser.add_argument("--default-mode", default="driving")
    init_parser.add_argument("--primary-genre")
    init_parser.add_argument("--sub-genre")
    init_parser.add_argument("--style-tag", action="append")
    init_parser.add_argument("--target-audience", action="append")
    init_parser.add_argument("--core-promise", action="append")
    init_parser.add_argument("--avoidance", action="append")
    init_parser.add_argument("--ending-contract")
    init_parser.add_argument("--pace-contract")
    init_parser.add_argument("--core-emotion", action="append")
    init_parser.add_argument("--chapter-emotion-floor", action="append")
    init_parser.add_argument("--forbidden-emotion", action="append")
    init_parser.add_argument("--default-reveal-mode")
    init_parser.add_argument("--allow-direct-explain-at-climax", action="store_true")
    init_parser.add_argument("--story-template-id")
    init_parser.add_argument("--story-template-label")
    init_parser.add_argument("--module-policy", action="append")
    init_parser.add_argument("--review-focus", action="append")
    init_parser.add_argument("--premise")
    init_parser.add_argument("--hook-line")
    init_parser.add_argument("--hook-stack", action="append")
    init_parser.add_argument("--benchmark-work", action="append")
    init_parser.add_argument("--target-platform")
    init_parser.add_argument("--serialization-model")
    init_parser.add_argument("--release-cadence")
    init_parser.add_argument("--chapter-word-floor", type=int)
    init_parser.add_argument("--chapter-word-target", type=int)
    init_parser.add_argument("--chapter-id", default="chapter-001")
    init_parser.add_argument("--chapter-title", default="第一章")
    init_parser.add_argument("--volume-id")
    init_parser.add_argument("--volume-title")
    init_parser.add_argument("--volume-theme")
    init_parser.add_argument("--volume-goal")
    init_parser.add_argument("--reader-hook")
    init_parser.add_argument("--suppression-source")
    init_parser.add_argument("--onboarding-focus")
    init_parser.add_argument("--chapter-handoff")
    init_parser.add_argument("--chapter-delivery")
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument(
        "--layout", choices=["flat", "layered"], default="flat",
        help="Project file layout mode (default: flat)",
    )
    init_parser.set_defaults(func=command_init)
