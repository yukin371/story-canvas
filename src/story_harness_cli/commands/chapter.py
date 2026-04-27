from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_harness_cli.protocol import ensure_project_root, load_project_state, save_state
from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.protocol.keywords import load_keywords
from story_harness_cli.commands.project_support import build_project_advisories
from story_harness_cli.services import analyze_chapter, evaluate_chapter_outline_readiness, generate_change_requests
from story_harness_cli.utils import now_iso, stable_hash
from story_harness_cli.utils.text import set_keywords


def _iter_outline_chapters(outline: dict[str, Any]):
    for volume in outline.get("volumes", []):
        for chapter in volume.get("chapters", []):
            yield volume, chapter
    for chapter in outline.get("chapters", []):
        yield None, chapter


def _find_chapter_entry(outline: dict[str, Any], chapter_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    for volume, chapter in _iter_outline_chapters(outline):
        if chapter.get("id") == chapter_id:
            return volume, chapter
    return None, None


def _chapter_exists(outline: dict[str, Any], chapter_id: str) -> bool:
    _, chapter = _find_chapter_entry(outline, chapter_id)
    return chapter is not None


def _parse_seed_items(raw_items: list[str] | None, *, item_kind: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw in raw_items or []:
        text = raw.strip()
        if not text:
            continue
        title, sep, summary = text.partition("::")
        title = title.strip()
        summary = summary.strip()
        if not sep:
            title = ""
            summary = text
        if not title and not summary:
            raise SystemExit(f"{item_kind} 不能为空")
        items.append({"title": title, "summary": summary})
    return items


def _build_seed_beats(chapter_id: str, seeds: list[dict[str, str]], created_at: str) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    for index, item in enumerate(seeds, 1):
        summary = item.get("summary") or item.get("title") or ""
        beats.append(
            {
                "id": f"beat-{stable_hash(f'{chapter_id}:beat:{index}:{summary}:{created_at}')[:10]}",
                "title": item.get("title") or "",
                "summary": summary,
                "status": "planned",
                "createdAt": created_at,
            }
        )
    return beats


def _build_seed_scenes(chapter_id: str, seeds: list[dict[str, str]], created_at: str) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    for index, item in enumerate(seeds, 1):
        scene_title = item.get("title") or ""
        scene_summary = item.get("summary") or scene_title
        scenes.append(
            {
                "id": f"scene-{stable_hash(f'{chapter_id}:scene:{index}:{scene_title}:{scene_summary}:{created_at}')[:10]}",
                "title": scene_title,
                "summary": scene_summary,
                "createdAt": created_at,
                "updatedAt": created_at,
            }
        )
    return scenes


def _resolve_target_chapter_list(
    state: dict[str, Any],
    *,
    volume_id: str,
    after_chapter_id: str,
) -> tuple[list[dict[str, Any]], str]:
    outline = state["outline"]
    volumes = outline.get("volumes", [])
    has_volumes = bool(volumes)

    if after_chapter_id:
        volume, chapter = _find_chapter_entry(outline, after_chapter_id)
        if chapter is None:
            raise SystemExit(f"找不到 after chapter: {after_chapter_id}")
        if volume_id:
            resolved_volume_id = volume.get("id", "") if volume else ""
            if resolved_volume_id != volume_id:
                raise SystemExit(f"after chapter `{after_chapter_id}` 不在 volume `{volume_id}` 中")
        if volume is not None:
            return volume.setdefault("chapters", []), volume.get("id", "")
        if has_volumes:
            raise SystemExit("当前项目按卷管理；插入章节时请指定 volume 或使用卷内章节作为锚点")
        return outline.setdefault("chapters", []), ""

    if volume_id:
        for volume in volumes:
            if volume.get("id") == volume_id:
                return volume.setdefault("chapters", []), volume_id
        raise SystemExit(f"找不到 volume: {volume_id}")

    if has_volumes:
        active_chapter_id = state.get("project", {}).get("activeChapterId", "")
        if active_chapter_id:
            active_volume, _ = _find_chapter_entry(outline, active_chapter_id)
            if active_volume is not None:
                return active_volume.setdefault("chapters", []), active_volume.get("id", "")
        last_volume = volumes[-1]
        return last_volume.setdefault("chapters", []), last_volume.get("id", "")

    return outline.setdefault("chapters", []), ""


def _insert_chapter(target_list: list[dict[str, Any]], chapter_entry: dict[str, Any], *, after_chapter_id: str) -> None:
    if not after_chapter_id:
        target_list.append(chapter_entry)
        return
    for index, chapter in enumerate(target_list):
        if chapter.get("id") == after_chapter_id:
            target_list.insert(index + 1, chapter_entry)
            return
    raise SystemExit(f"找不到 after chapter: {after_chapter_id}")


def _write_chapter_stub(chapter_file: Path, title: str) -> None:
    chapter_file.parent.mkdir(parents=True, exist_ok=True)
    chapter_file.write_text(f"# {title}\n\n", encoding="utf-8")


def command_chapter_create(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    outline = state["outline"]
    chapter_id = args.chapter_id

    if _chapter_exists(outline, chapter_id):
        raise SystemExit(f"章节已存在: {chapter_id}")

    chapter_file = root / "chapters" / f"{chapter_id}.md"
    if chapter_file.exists():
        raise SystemExit(f"章节文件已存在: {chapter_file}")

    created_at = now_iso()
    beat_seeds = _parse_seed_items(args.beat, item_kind="beat")
    scene_seeds = _parse_seed_items(args.scene, item_kind="scene")
    beats = _build_seed_beats(chapter_id, beat_seeds, created_at)
    scenes = _build_seed_scenes(chapter_id, scene_seeds, created_at)
    chapter_entry: dict[str, Any] = {
        "id": chapter_id,
        "title": args.title,
        "status": args.status,
        "beats": beats,
        "scenePlans": scenes,
    }
    if args.direction:
        chapter_entry["direction"] = args.direction

    target_list, resolved_volume_id = _resolve_target_chapter_list(
        state,
        volume_id=args.volume_id or "",
        after_chapter_id=args.after_chapter_id or "",
    )
    _insert_chapter(target_list, chapter_entry, after_chapter_id=args.after_chapter_id or "")

    if not args.no_set_active:
        state["project"]["activeChapterId"] = chapter_id
    state["project"]["updatedAt"] = created_at
    _write_chapter_stub(chapter_file, args.title)
    save_state(root, state)

    print(
        json.dumps(
            {
                "chapterId": chapter_id,
                "title": args.title,
                "status": args.status,
                "direction": args.direction or "",
                "beatCount": len(beats),
                "sceneCount": len(scenes),
                "activeChapterId": state["project"].get("activeChapterId"),
                "setActive": not args.no_set_active,
                "volumeId": resolved_volume_id,
                "afterChapterId": args.after_chapter_id or "",
                "chapterFile": str(chapter_file),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_chapter_analyze(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    set_keywords(load_keywords(root))
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")

    analysis = analyze_chapter(root, state, chapter_id)

    # Auto-register inferred entities that are not yet in entities.yaml
    entities_list = state["entities"].setdefault("entities", [])
    existing_ids = {e.get("id") for e in entities_list}
    for active in analysis.get("activeEntities", []):
        if active.get("source") == "inferred" and active["id"] not in existing_ids:
            entities_list.append(
                {
                    "id": active["id"],
                    "name": active["name"],
                    "type": "character",
                    "aliases": [],
                    "summary": "",
                    "currentState": "",
                    "source": "inferred",
                    "registeredAt": now_iso(),
                }
            )
            existing_ids.add(active["id"])

    # Auto-update chapter status in outline volumes
    for vol in state["outline"].get("volumes", []):
        for ch in vol.get("chapters", []):
            if ch.get("id") == chapter_id:
                ch["status"] = "completed"
                break

    state["project"]["activeChapterId"] = chapter_id
    state["project"]["updatedAt"] = now_iso()
    save_state(root, state)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    return 0


def command_chapter_suggest(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    analysis_path = root / "logs" / (f"analysis-{chapter_id}.yaml" if chapter_id else "latest-analysis.yaml")
    if not analysis_path.exists():
        analysis_path = root / "logs" / "latest-analysis.yaml"
    if not analysis_path.exists():
        raise SystemExit("还没有分析结果，请先运行 chapter analyze")

    readiness = evaluate_chapter_outline_readiness(state, chapter_id)
    if not readiness["ready"] and not args.allow_without_outline:
        missing = "、".join(item["message"] for item in readiness["missing"]) or "缺少前置大纲"
        raise SystemExit(
            (
                f"章节 {chapter_id} 尚未通过大纲前置检查：{missing}。"
                f"请先运行 outline check --root {root} --chapter-id {chapter_id} 并补齐大纲；"
                "如需跳过该门禁，请显式传入 --allow-without-outline"
            )
        )

    analysis = load_json_compatible_yaml(analysis_path, {})
    result = generate_change_requests(state, analysis)
    result["projectAdvisories"] = build_project_advisories(root, include_prd_content=True)
    save_state(root, state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def register_chapter_commands(subparsers) -> None:
    chapter_parser = subparsers.add_parser("chapter", help="Chapter-oriented commands")
    chapter_subparsers = chapter_parser.add_subparsers(dest="chapter_command", required=True)

    create_parser = chapter_subparsers.add_parser("create", help="Create a new chapter stub and register it in outline state")
    create_parser.add_argument("--root", required=True)
    create_parser.add_argument("--chapter-id", required=True)
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--volume-id", help="Target volume id for layered or volume-based projects")
    create_parser.add_argument("--after-chapter-id", help="Insert new chapter after the given chapter id")
    create_parser.add_argument("--direction", help="Initial chapter direction")
    create_parser.add_argument("--beat", action="append", help="Initial beat seed; use `title::summary` or plain summary")
    create_parser.add_argument("--scene", action="append", help="Initial scene seed; use `title::summary` or plain summary")
    create_parser.add_argument("--status", default="draft", choices=["planned", "draft", "completed"])
    create_parser.add_argument("--no-set-active", action="store_true", help="Do not move project.activeChapterId to the new chapter")
    create_parser.set_defaults(func=command_chapter_create)

    analyze_parser = chapter_subparsers.add_parser("analyze", help="Analyze one chapter")
    analyze_parser.add_argument("--root", required=True)
    analyze_parser.add_argument("--chapter-id")
    analyze_parser.set_defaults(func=command_chapter_analyze)

    suggest_parser = chapter_subparsers.add_parser("suggest", help="Generate change requests from latest analysis")
    suggest_parser.add_argument("--root", required=True)
    suggest_parser.add_argument("--chapter-id")
    suggest_parser.add_argument(
        "--allow-without-outline",
        action="store_true",
        help="Skip outline-first guard for legacy or imported drafts",
    )
    suggest_parser.set_defaults(func=command_chapter_suggest)

