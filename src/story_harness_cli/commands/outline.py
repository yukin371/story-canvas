from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.commands.project_support import build_chapter_start_guide, build_project_advisories
from story_harness_cli.protocol import chapter_path, ensure_project_root, load_project_state, save_state
from story_harness_cli.services import detect_scene_plans, evaluate_project_outline_readiness
from story_harness_cli.utils.text import paragraphs_from_text
from story_harness_cli.utils import now_iso, stable_hash


def command_outline_propose(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    items = []
    for item in args.item or []:
        title, _, summary = item.partition("::")
        title = title.strip()
        summary = summary.strip()
        if not title:
            continue
        items.append({"title": title, "summary": summary})

    proposal_kind = "beat-outline" if items else "chapter-direction"
    proposal_id = f"proposal-{stable_hash(args.title + now_iso())}"
    state["proposals"].setdefault("draftProposals", []).append(
        {
            "id": proposal_id,
            "projectId": state["project"].get("title", "story-project"),
            "chapterId": args.chapter_id or None,
            "source": "structure-assistant",
            "kind": proposal_kind,
            "title": args.title,
            "summary": args.summary,
            "content": {
                "mode": args.mode,
                "prompt": args.prompt or "",
                "items": items,
            },
            "editable": True,
            "status": "draft",
            "createdAt": now_iso(),
            "updatedAt": now_iso(),
        }
    )
    save_state(root, state)
    print(json.dumps({"proposalId": proposal_id, "kind": proposal_kind}, ensure_ascii=False, indent=2))
    return 0


def command_outline_promote(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    proposals = state["proposals"].setdefault("draftProposals", [])
    proposal = next((item for item in proposals if item.get("id") == args.proposal_id), None)
    if proposal is None:
        raise SystemExit(f"未找到 proposal: {args.proposal_id}")

    chapter_id = args.chapter_id or proposal.get("chapterId")
    if not chapter_id:
        raise SystemExit("缺少目标 chapter id")

    outline = state["outline"]
    chapter_entry = next((item for item in outline.get("chapters", []) if item.get("id") == chapter_id), None)
    if chapter_entry is None:
        chapter_entry = {"id": chapter_id, "title": chapter_id, "status": "draft", "beats": [], "scenePlans": []}
        outline.setdefault("chapters", []).append(chapter_entry)

    content = proposal.get("content", {})
    items = content.get("items", [])
    if proposal.get("kind") == "chapter-direction":
        outline.setdefault("chapterDirections", []).append(
            {
                "chapterId": chapter_id,
                "title": proposal.get("title"),
                "summary": proposal.get("summary"),
                "prompt": content.get("prompt", ""),
                "sourceProposalId": proposal.get("id"),
                "updatedAt": now_iso(),
            }
        )
    else:
        beats = chapter_entry.setdefault("beats", [])
        for item in items:
            beats.append(
                {
                    "title": item.get("title"),
                    "summary": item.get("summary", ""),
                    "sourceProposalId": proposal.get("id"),
                }
            )

    proposal["status"] = "applied"
    proposal["adoption"] = {"mode": "full", "appliedAt": now_iso()}
    proposal["projectionStatus"] = "pending"
    proposal["updatedAt"] = now_iso()
    save_state(root, state)
    print(json.dumps({"proposalId": proposal.get("id"), "chapterId": chapter_id, "status": "applied"}, ensure_ascii=False, indent=2))
    return 0


def command_outline_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    result = evaluate_project_outline_readiness(
        state,
        chapter_id=args.chapter_id,
        require_beats=not args.allow_missing_beats,
        require_scene_plans=not args.allow_missing_scene_plans,
        require_project_gate=not args.allow_missing_project_gate,
    )
    result["projectAdvisories"] = build_project_advisories(root, include_prd_content=True)
    if args.chapter_id and result.get("chapters"):
        missing_codes = [item.get("code", "") for item in result["chapters"][0].get("missing", []) if item.get("code")]
        result["startGuide"] = build_chapter_start_guide(root, args.chapter_id, missing_codes=missing_codes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready"] else 1


def _find_chapter(outline: dict, chapter_id: str) -> dict | None:
    """Find chapter entry in either volumes or flat chapters list."""
    for vol in outline.get("volumes", []):
        for ch in vol.get("chapters", []):
            if ch.get("id") == chapter_id:
                return ch
    for ch in outline.get("chapters", []):
        if ch.get("id") == chapter_id:
            return ch
    return None


def command_outline_beat_add(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id
    summary = args.summary

    chapter = _find_chapter(state["outline"], chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {chapter_id}")

    beats = chapter.setdefault("beats", [])
    beat_id = f"beat-{stable_hash(summary + now_iso())[:10]}"
    beat = {
        "id": beat_id,
        "summary": summary,
        "status": "planned",
        "createdAt": now_iso(),
    }
    beats.append(beat)
    save_state(root, state)
    print(json.dumps(beat, ensure_ascii=False, indent=2))
    return 0


def command_outline_beat_complete(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id
    beat_id = args.beat_id

    chapter = _find_chapter(state["outline"], chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {chapter_id}")

    beats = chapter.get("beats", [])
    beat = next((b for b in beats if b.get("id") == beat_id), None)
    if beat is None:
        raise SystemExit(f"找不到 beat: {beat_id}")

    beat["status"] = "completed"
    beat["completedAt"] = now_iso()
    save_state(root, state)
    print(json.dumps(beat, ensure_ascii=False, indent=2))
    return 0


def command_outline_beat_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id

    chapter = _find_chapter(state["outline"], chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {chapter_id}")

    beats = chapter.get("beats", [])
    if args.status:
        beats = [b for b in beats if b.get("status") == args.status]

    print(json.dumps(beats, ensure_ascii=False, indent=2))
    return 0


def command_outline_scene_add(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter = _find_chapter(state["outline"], args.chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {args.chapter_id}")
    if args.start_paragraph < 1 or args.end_paragraph < args.start_paragraph:
        raise SystemExit("scene 段落范围无效")

    scene_id = f"scene-{stable_hash(args.chapter_id + args.title + now_iso())[:10]}"
    scene = {
        "id": scene_id,
        "title": args.title,
        "summary": args.summary or "",
        "startParagraph": args.start_paragraph,
        "endParagraph": args.end_paragraph,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    chapter.setdefault("scenePlans", []).append(scene)
    save_state(root, state)
    print(json.dumps(scene, ensure_ascii=False, indent=2))
    return 0


def command_outline_scene_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter = _find_chapter(state["outline"], args.chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {args.chapter_id}")
    print(json.dumps(chapter.get("scenePlans", []), ensure_ascii=False, indent=2))
    return 0


def command_outline_scene_detect(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter = _find_chapter(state["outline"], args.chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {args.chapter_id}")

    existing_scenes = chapter.get("scenePlans", [])
    if existing_scenes and not args.replace:
        raise SystemExit("该章节已有 scenePlans，如需覆盖请显式传入 --replace")

    target_chapter = chapter_path(root, args.chapter_id)
    if not target_chapter.exists():
        raise SystemExit(f"章节不存在: {target_chapter}")

    chapter_text = target_chapter.read_text(encoding="utf-8")
    if not paragraphs_from_text(chapter_text):
        raise SystemExit("当前章节还没有正文段落；请先在章节文件中按场景写 1 段骨架，再运行 outline scene-detect。")
    detected_scenes = detect_scene_plans(args.chapter_id, chapter_text)
    if not detected_scenes:
        raise SystemExit("未检测到可用场景，请先补充章节正文")

    persisted_scenes = []
    for scene in detected_scenes:
        timestamp = now_iso()
        persisted_scenes.append({**scene, "createdAt": timestamp, "updatedAt": timestamp})

    chapter["scenePlans"] = persisted_scenes
    save_state(root, state)
    print(
        json.dumps(
            {
                "chapterId": args.chapter_id,
                "detected": len(persisted_scenes),
                "replaced": bool(existing_scenes),
                "scenes": persisted_scenes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _find_scene_plan(chapter: dict, scene_id: str) -> dict | None:
    for scene in chapter.get("scenePlans", []):
        if scene.get("id") == scene_id:
            return scene
    return None


def command_outline_scene_update(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter = _find_chapter(state["outline"], args.chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {args.chapter_id}")

    scene = _find_scene_plan(chapter, args.scene_id)
    if scene is None:
        raise SystemExit(f"找不到 scene: {args.scene_id}")

    if args.start_paragraph is not None and args.end_paragraph is not None:
        if args.start_paragraph < 1 or args.end_paragraph < args.start_paragraph:
            raise SystemExit("scene 段落范围无效")
        scene["startParagraph"] = args.start_paragraph
        scene["endParagraph"] = args.end_paragraph
    elif args.start_paragraph is not None or args.end_paragraph is not None:
        raise SystemExit("更新段落范围时必须同时提供 --start-paragraph 和 --end-paragraph")

    if args.title is not None:
        scene["title"] = args.title
    if args.summary is not None:
        scene["summary"] = args.summary
    scene["updatedAt"] = now_iso()
    save_state(root, state)
    print(json.dumps(scene, ensure_ascii=False, indent=2))
    return 0


def command_outline_scene_remove(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter = _find_chapter(state["outline"], args.chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {args.chapter_id}")

    scenes = chapter.get("scenePlans", [])
    remaining = [scene for scene in scenes if scene.get("id") != args.scene_id]
    if len(remaining) == len(scenes):
        raise SystemExit(f"找不到 scene: {args.scene_id}")

    chapter["scenePlans"] = remaining
    save_state(root, state)
    print(json.dumps({"removed": 1, "sceneId": args.scene_id, "chapterId": args.chapter_id}, ensure_ascii=False, indent=2))
    return 0


def _validate_scene_ranges(scene_plans: list[dict], paragraph_count: int) -> list[dict]:
    issues: list[dict] = []
    previous_end = 0
    for index, scene in enumerate(scene_plans, start=1):
        start = scene.get("startParagraph")
        end = scene.get("endParagraph")
        issue = {
            "sceneId": scene.get("id", ""),
            "title": scene.get("title", ""),
            "index": index,
        }
        if not isinstance(start, int) or not isinstance(end, int):
            issues.append({**issue, "issue": "missing-range"})
            continue
        if start < 1 or end < start or end > paragraph_count:
            issues.append(
                {
                    **issue,
                    "issue": "out-of-range",
                    "startParagraph": start,
                    "endParagraph": end,
                    "paragraphCount": paragraph_count,
                }
            )
            continue
        if start <= previous_end:
            issues.append(
                {
                    **issue,
                    "issue": "overlap-or-nonascending",
                    "startParagraph": start,
                    "endParagraph": end,
                    "previousEndParagraph": previous_end,
                }
            )
        previous_end = end
    return issues


def _persisted_detected_scenes(chapter_id: str, chapter_text: str) -> list[dict]:
    scenes = []
    for scene in detect_scene_plans(chapter_id, chapter_text):
        timestamp = now_iso()
        scenes.append({**scene, "createdAt": timestamp, "updatedAt": timestamp})
    return scenes


def _trim_tail_overflow(scene_plans: list[dict], paragraph_count: int) -> tuple[list[dict], str] | tuple[None, str]:
    issues = _validate_scene_ranges(scene_plans, paragraph_count)
    if len(issues) != 1:
        return None, ""
    issue = issues[0]
    if issue.get("issue") != "out-of-range":
        return None, ""
    last_scene = scene_plans[-1] if scene_plans else {}
    if issue.get("sceneId") != last_scene.get("id"):
        return None, ""
    start = last_scene.get("startParagraph")
    end = last_scene.get("endParagraph")
    if not isinstance(start, int) or not isinstance(end, int):
        return None, ""
    if start < 1 or start > paragraph_count or end <= paragraph_count:
        return None, ""

    repaired = []
    for scene in scene_plans:
        updated = dict(scene)
        if scene.get("id") == last_scene.get("id"):
            updated["endParagraph"] = paragraph_count
            updated["updatedAt"] = now_iso()
            updated["syncMethod"] = "trim-tail-overflow"
        repaired.append(updated)
    if _validate_scene_ranges(repaired, paragraph_count):
        return None, ""
    return repaired, "trim-tail-overflow"


def _repartition_scene_ranges(
    scene_plans: list[dict],
    detected_scenes: list[dict],
) -> tuple[list[dict], str] | tuple[None, str]:
    if not scene_plans or not detected_scenes or len(scene_plans) != len(detected_scenes):
        return None, ""

    updated_scenes = []
    changed = False
    for existing, detected in zip(scene_plans, detected_scenes):
        updated = dict(existing)
        for field in ("startParagraph", "endParagraph"):
            if updated.get(field) != detected.get(field):
                changed = True
            updated[field] = detected.get(field)
        if not updated.get("title"):
            updated["title"] = detected.get("title", "")
        if not updated.get("summary"):
            updated["summary"] = detected.get("summary", "")
        updated["updatedAt"] = now_iso()
        updated["syncMethod"] = "heuristic-repartition"
        updated_scenes.append(updated)

    if not changed:
        return None, ""
    return updated_scenes, "heuristic-repartition"


def _scene_sync_suggestion(
    chapter_id: str,
    chapter_text: str,
    scene_plans: list[dict],
    paragraph_count: int,
) -> tuple[list[dict], str, bool]:
    if not scene_plans:
        detected = _persisted_detected_scenes(chapter_id, chapter_text)
        if detected:
            return detected, "heuristic-detect", True
        return [], "", False

    trimmed, trim_method = _trim_tail_overflow(scene_plans, paragraph_count)
    if trimmed:
        return trimmed, trim_method, True

    detected = _persisted_detected_scenes(chapter_id, chapter_text)
    repartitioned, repartition_method = _repartition_scene_ranges(scene_plans, detected)
    if repartitioned:
        return repartitioned, repartition_method, True

    return [], "", False


def command_outline_scene_sync(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter = _find_chapter(state["outline"], args.chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {args.chapter_id}")

    target_chapter = chapter_path(root, args.chapter_id)
    if not target_chapter.exists():
        raise SystemExit(f"章节不存在: {target_chapter}")

    chapter_text = target_chapter.read_text(encoding="utf-8")
    paragraphs = paragraphs_from_text(chapter_text)
    paragraph_count = len(paragraphs)
    if paragraph_count == 0:
        raise SystemExit("章节中没有可用于 scenePlans 同步的正文段落")

    current_scenes = [dict(scene) for scene in chapter.get("scenePlans", [])]
    validation_issues = _validate_scene_ranges(current_scenes, paragraph_count)
    suggested_scenes, suggestion_method, can_apply = _scene_sync_suggestion(
        args.chapter_id,
        chapter_text,
        current_scenes,
        paragraph_count,
    )

    applied = False
    if args.apply:
        if not can_apply or not suggested_scenes:
            raise SystemExit("当前 scenePlans 没有可安全应用的同步建议")
        chapter["scenePlans"] = suggested_scenes
        save_state(root, state)
        applied = True

    payload = {
        "chapterId": args.chapter_id,
        "paragraphCount": paragraph_count,
        "currentScenePlanCount": len(current_scenes),
        "validation": {
            "valid": len(validation_issues) == 0,
            "issues": validation_issues,
        },
        "suggestion": {
            "available": can_apply,
            "method": suggestion_method,
            "scenePlanCount": len(suggested_scenes),
            "scenes": suggested_scenes,
        },
        "applied": applied,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _find_detailed_entry(detailed_outlines: dict, chapter_id: str) -> dict | None:
    for entry in detailed_outlines.get("entries", []):
        if entry.get("chapterId") == chapter_id:
            return entry
    return None


def command_outline_detail_init(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id

    chapter = _find_chapter(state["outline"], chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {chapter_id}")

    detailed = state.setdefault("detailed_outlines", {"entries": []})
    entry = _find_detailed_entry(detailed, chapter_id)
    if entry is None:
        entry = {"chapterId": chapter_id}
        detailed["entries"].append(entry)

    if args.direction:
        entry["direction"] = args.direction
        chapter["direction"] = args.direction

    from story_harness_cli.utils import now_iso
    entry["updatedAt"] = now_iso()

    save_state(root, state)
    print(json.dumps({"chapterId": chapter_id, "status": "initialized"}, ensure_ascii=False, indent=2))
    return 0


def command_outline_detail_show(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id

    chapter = _find_chapter(state["outline"], chapter_id)
    if chapter is None:
        raise SystemExit(f"找不到章节: {chapter_id}")

    result = {
        "chapterId": chapter_id,
        "title": chapter.get("title", ""),
        "direction": chapter.get("direction", ""),
        "beats": chapter.get("beats", []),
        "scenePlans": chapter.get("scenePlans", []),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def register_outline_commands(subparsers) -> None:
    outline_parser = subparsers.add_parser("outline", help="Outline and structure commands")
    outline_subparsers = outline_parser.add_subparsers(dest="outline_command", required=True)

    propose_parser = outline_subparsers.add_parser("propose", help="Persist a structure proposal")
    propose_parser.add_argument("--root", required=True)
    propose_parser.add_argument("--mode", required=True, choices=["volume", "chapter"])
    propose_parser.add_argument("--title", required=True)
    propose_parser.add_argument("--summary", required=True)
    propose_parser.add_argument("--chapter-id")
    propose_parser.add_argument("--prompt")
    propose_parser.add_argument("--item", action="append")
    propose_parser.set_defaults(func=command_outline_propose)

    promote_parser = outline_subparsers.add_parser("promote", help="Promote a draft proposal into outline state")
    promote_parser.add_argument("--root", required=True)
    promote_parser.add_argument("--proposal-id", required=True)
    promote_parser.add_argument("--chapter-id")
    promote_parser.set_defaults(func=command_outline_promote)

    check_parser = outline_subparsers.add_parser(
        "check",
        help="Validate whether chapters are ready for drafting/refinement under the strict project/chapter gate",
    )
    check_parser.add_argument("--root", required=True)
    check_parser.add_argument("--chapter-id")
    check_parser.add_argument(
        "--allow-missing-beats",
        action="store_true",
        help="Relax gate: allow chapters without beats",
    )
    check_parser.add_argument(
        "--allow-missing-scene-plans",
        action="store_true",
        help="Relax gate: allow chapters without explicit scenePlans",
    )
    check_parser.add_argument(
        "--allow-missing-project-gate",
        action="store_true",
        help="Relax gate: ignore project positioning / contract prerequisites",
    )
    check_parser.set_defaults(func=command_outline_check)

    beat_add_parser = outline_subparsers.add_parser("beat-add", help="Add a beat to a chapter")
    beat_add_parser.add_argument("--root", required=True)
    beat_add_parser.add_argument("--chapter-id", required=True)
    beat_add_parser.add_argument("--summary", required=True, help="Beat description")
    beat_add_parser.set_defaults(func=command_outline_beat_add)

    beat_complete_parser = outline_subparsers.add_parser("beat-complete", help="Mark a beat as completed")
    beat_complete_parser.add_argument("--root", required=True)
    beat_complete_parser.add_argument("--chapter-id", required=True)
    beat_complete_parser.add_argument("--beat-id", required=True)
    beat_complete_parser.set_defaults(func=command_outline_beat_complete)

    beat_list_parser = outline_subparsers.add_parser("beat-list", help="List beats for a chapter")
    beat_list_parser.add_argument("--root", required=True)
    beat_list_parser.add_argument("--chapter-id", required=True)
    beat_list_parser.add_argument("--status", choices=["planned", "completed"], help="Filter by status")
    beat_list_parser.set_defaults(func=command_outline_beat_list)

    scene_add_parser = outline_subparsers.add_parser("scene-add", help="Add an explicit scene plan to a chapter")
    scene_add_parser.add_argument("--root", required=True)
    scene_add_parser.add_argument("--chapter-id", required=True)
    scene_add_parser.add_argument("--title", required=True)
    scene_add_parser.add_argument("--summary")
    scene_add_parser.add_argument("--start-paragraph", required=True, type=int)
    scene_add_parser.add_argument("--end-paragraph", required=True, type=int)
    scene_add_parser.set_defaults(func=command_outline_scene_add)

    scene_list_parser = outline_subparsers.add_parser("scene-list", help="List explicit scene plans for a chapter")
    scene_list_parser.add_argument("--root", required=True)
    scene_list_parser.add_argument("--chapter-id", required=True)
    scene_list_parser.set_defaults(func=command_outline_scene_list)

    scene_detect_parser = outline_subparsers.add_parser(
        "scene-detect",
        help="Detect heuristic scene candidates and persist them as explicit scene plans",
    )
    scene_detect_parser.add_argument("--root", required=True)
    scene_detect_parser.add_argument("--chapter-id", required=True)
    scene_detect_parser.add_argument("--replace", action="store_true")
    scene_detect_parser.set_defaults(func=command_outline_scene_detect)

    scene_update_parser = outline_subparsers.add_parser("scene-update", help="Update an explicit scene plan")
    scene_update_parser.add_argument("--root", required=True)
    scene_update_parser.add_argument("--chapter-id", required=True)
    scene_update_parser.add_argument("--scene-id", required=True)
    scene_update_parser.add_argument("--title")
    scene_update_parser.add_argument("--summary")
    scene_update_parser.add_argument("--start-paragraph", type=int)
    scene_update_parser.add_argument("--end-paragraph", type=int)
    scene_update_parser.set_defaults(func=command_outline_scene_update)

    scene_remove_parser = outline_subparsers.add_parser("scene-remove", help="Remove an explicit scene plan")
    scene_remove_parser.add_argument("--root", required=True)
    scene_remove_parser.add_argument("--chapter-id", required=True)
    scene_remove_parser.add_argument("--scene-id", required=True)
    scene_remove_parser.set_defaults(func=command_outline_scene_remove)

    scene_sync_parser = outline_subparsers.add_parser(
        "scene-sync",
        help="Validate explicit scenePlans and suggest or apply safe boundary syncs",
    )
    scene_sync_parser.add_argument("--root", required=True)
    scene_sync_parser.add_argument("--chapter-id", required=True)
    scene_sync_parser.add_argument("--apply", action="store_true")
    scene_sync_parser.set_defaults(func=command_outline_scene_sync)

    detail_init_parser = outline_subparsers.add_parser("detail-init", help="Initialize detailed outline for a chapter")
    detail_init_parser.add_argument("--root", required=True)
    detail_init_parser.add_argument("--chapter-id", required=True)
    detail_init_parser.add_argument("--direction", help="Initial chapter direction")
    detail_init_parser.set_defaults(func=command_outline_detail_init)

    detail_show_parser = outline_subparsers.add_parser("detail-show", help="Show detailed outline for a chapter")
    detail_show_parser.add_argument("--root", required=True)
    detail_show_parser.add_argument("--chapter-id", required=True)
    detail_show_parser.set_defaults(func=command_outline_detail_show)
