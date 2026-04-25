from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.protocol import (
    chapter_path,
    choose_style_profile_name,
    ensure_project_root,
    load_project_state,
    resolve_style_profile,
    save_state,
)
from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services import (
    analyze_style_text,
    build_chapter_review,
    build_scene_review,
    resolve_scene_candidates,
    review_change_requests,
)


def command_review_apply(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    result = review_change_requests(
        state,
        decision=args.decision,
        chapter_id=args.chapter_id,
        request_ids=args.request_id or [],
        all_pending=args.all_pending,
        reason=args.reason or "",
    )
    save_state(root, state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_review_chapter(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    analysis = load_json_compatible_yaml(root / "logs" / f"analysis-{chapter_id}.yaml", {})
    if not analysis:
        analysis = load_json_compatible_yaml(root / "logs" / "latest-analysis.yaml", {})
    if analysis.get("chapterId") not in {None, chapter_id}:
        analysis = {}

    chapter_text = chapter_file.read_text(encoding="utf-8")
    scorer, source = load_style_similarity_scorer()
    profile_name = choose_style_profile_name(state.get("project", {}))
    profile_config, profile_source = resolve_style_profile(root, profile_name)
    review = build_chapter_review(
        state,
        chapter_id=chapter_id,
        chapter_text=chapter_text,
        analysis=analysis,
        style_report=analyze_style_text(
            chapter_text,
            opener_similarity_scorer=scorer,
            repetition_source=source,
            profile_name=profile_name,
            profile_config=profile_config,
        ),
    )
    review["styleAnalysis"]["profileSource"] = profile_source

    story_reviews = state["story_reviews"].setdefault("chapterReviews", [])
    state["story_reviews"]["rubricVersion"] = review["rubricVersion"]
    for index, existing in enumerate(story_reviews):
        if existing.get("fingerprint") == review["fingerprint"]:
            story_reviews[index] = review
            break
    else:
        story_reviews.append(review)

    save_state(root, state)
    print(json.dumps(review, ensure_ascii=False, indent=2))
    return 0


def command_review_scene(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    analysis = load_json_compatible_yaml(root / "logs" / f"analysis-{chapter_id}.yaml", {})
    if not analysis:
        analysis = load_json_compatible_yaml(root / "logs" / "latest-analysis.yaml", {})
    if analysis.get("chapterId") not in {None, chapter_id}:
        analysis = {}

    chapter_text = chapter_file.read_text(encoding="utf-8")
    chapter_entry = next((item for item in state["outline"].get("chapters", []) if item.get("id") == chapter_id), {})
    scene_candidates = resolve_scene_candidates(chapter_entry, chapter_text)
    if args.list_scenes:
        print(json.dumps({"chapterId": chapter_id, "scenes": scene_candidates}, ensure_ascii=False, indent=2))
        return 0

    start_paragraph = args.start_paragraph
    end_paragraph = args.end_paragraph
    selected_scene_index = None
    if args.scene_index is not None:
        if args.scene_index < 1 or args.scene_index > len(scene_candidates):
            raise SystemExit(f"scene-index 超出范围，可用范围为 1..{len(scene_candidates)}")
        selected = scene_candidates[args.scene_index - 1]
        start_paragraph = selected["startParagraph"]
        end_paragraph = selected["endParagraph"]
        selected_scene_index = args.scene_index

    if start_paragraph is None:
        raise SystemExit("缺少段落范围，请提供 --scene-index 或 --start-paragraph")

    try:
        review = build_scene_review(
            state,
            chapter_id=chapter_id,
            chapter_text=chapter_text,
            start_paragraph=start_paragraph,
            end_paragraph=end_paragraph or start_paragraph,
            analysis=analysis,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if selected_scene_index is not None:
        review["sceneRange"]["sceneIndex"] = selected_scene_index
        review["sceneRange"]["source"] = scene_candidates[selected_scene_index - 1].get("source", "heuristic")
        if scene_candidates[selected_scene_index - 1].get("scenePlanId"):
            review["sceneRange"]["scenePlanId"] = scene_candidates[selected_scene_index - 1]["scenePlanId"]

    story_reviews = state["story_reviews"].setdefault("sceneReviews", [])
    state["story_reviews"]["sceneRubricVersion"] = review["rubricVersion"]
    for index, existing in enumerate(story_reviews):
        if existing.get("fingerprint") == review["fingerprint"]:
            story_reviews[index] = review
            break
    else:
        story_reviews.append(review)

    save_state(root, state)
    print(json.dumps(review, ensure_ascii=False, indent=2))
    return 0


def register_review_commands(subparsers) -> None:
    review_parser = subparsers.add_parser("review", help="Review workflow items and chapter quality")
    review_subparsers = review_parser.add_subparsers(dest="review_command", required=True)

    apply_parser = review_subparsers.add_parser("apply", help="Apply decisions to change requests")
    apply_parser.add_argument("--root", required=True)
    apply_parser.add_argument("--decision", required=True, choices=["accepted", "ignored", "deferred"])
    apply_parser.add_argument("--request-id", action="append")
    apply_parser.add_argument("--all-pending", action="store_true")
    apply_parser.add_argument("--chapter-id")
    apply_parser.add_argument("--reason")
    apply_parser.set_defaults(func=command_review_apply)

    chapter_parser = review_subparsers.add_parser("chapter", help="Review one chapter with rubric scores")
    chapter_parser.add_argument("--root", required=True)
    chapter_parser.add_argument("--chapter-id")
    chapter_parser.set_defaults(func=command_review_chapter)

    scene_parser = review_subparsers.add_parser("scene", help="Review one scene fragment by paragraph range or scene index")
    scene_parser.add_argument("--root", required=True)
    scene_parser.add_argument("--chapter-id")
    scene_parser.add_argument("--list-scenes", action="store_true")
    scene_parser.add_argument("--scene-index", type=int)
    scene_parser.add_argument("--start-paragraph", type=int)
    scene_parser.add_argument("--end-paragraph", type=int)
    scene_parser.set_defaults(func=command_review_scene)
