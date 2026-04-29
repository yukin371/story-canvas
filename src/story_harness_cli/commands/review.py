from __future__ import annotations

import json
from pathlib import Path

from story_harness_cli.commands.export import write_volume_review_packet
from story_harness_cli.commands.review_support import (
    build_review_preflight_payload,
    build_world_check_payload,
)
from story_harness_cli.protocol import (
    chapter_path,
    choose_style_profile_name,
    ensure_project_root,
    load_project_state,
    resolve_review_rule_profile,
    resolve_state_path,
    resolve_style_profile,
    save_state,
)
from story_harness_cli.protocol.io import load_json_compatible_yaml
from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services import (
    analyze_style_text,
    build_volume_self_review_template,
    build_chapter_review,
    build_scene_review,
    check_consistency,
    latest_volume_self_review,
    merge_volume_self_review_payload,
    normalize_volume_self_review,
    resolve_scene_candidates,
    review_change_requests,
    validate_volume_self_review_refs,
)
from story_harness_cli.utils import now_iso
from story_harness_cli.utils.text import paragraphs_from_text


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
    review_rule_config, review_rule_profile_name, review_rule_source = resolve_review_rule_profile(root)
    volume = _find_volume_for_chapter(state, chapter_id)
    consistency_result = check_consistency(state, chapter_text, chapter_id)
    previous_chapter_ending_text = _previous_chapter_ending_text(root, state, chapter_id)
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
            review_rule_profile_name=review_rule_profile_name,
            review_rule_config=review_rule_config,
            review_rule_scope={
                "chapterId": chapter_id,
                "volumeId": str(volume.get("id", "")),
                "scenePlanId": "",
            },
        ),
        consistency_result=consistency_result,
        previous_chapter_ending_text=previous_chapter_ending_text,
    )
    review["styleAnalysis"]["profileSource"] = profile_source
    review["styleAnalysis"]["reviewRuleProfileSource"] = review_rule_source

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

    scene_paragraphs = paragraphs_from_text(chapter_text)
    if start_paragraph < 1 or (end_paragraph or start_paragraph) < start_paragraph or (end_paragraph or start_paragraph) > len(scene_paragraphs):
        raise SystemExit(f"段落范围无效，可用范围为 1..{len(scene_paragraphs)}")

    selected_scene_text = "\n\n".join(scene_paragraphs[start_paragraph - 1 : (end_paragraph or start_paragraph)])
    scorer, source = load_style_similarity_scorer()
    profile_name = choose_style_profile_name(state.get("project", {}))
    profile_config, profile_source = resolve_style_profile(root, profile_name)
    review_rule_config, review_rule_profile_name, review_rule_source = resolve_review_rule_profile(root)
    volume = _find_volume_for_chapter(state, chapter_id)
    selected_scene_plan_id = ""
    if selected_scene_index is not None:
        selected_scene_plan_id = str(scene_candidates[selected_scene_index - 1].get("scenePlanId", ""))

    try:
        review = build_scene_review(
            state,
            chapter_id=chapter_id,
            chapter_text=chapter_text,
            start_paragraph=start_paragraph,
            end_paragraph=end_paragraph or start_paragraph,
            analysis=analysis,
            style_report=analyze_style_text(
                selected_scene_text,
                opener_similarity_scorer=scorer,
                repetition_source=source,
                profile_name=profile_name,
                profile_config=profile_config,
                review_rule_profile_name=review_rule_profile_name,
                review_rule_config=review_rule_config,
                review_rule_scope={
                    "chapterId": chapter_id,
                    "volumeId": str(volume.get("id", "")),
                    "scenePlanId": selected_scene_plan_id,
                },
            ),
            consistency_result=check_consistency(state, selected_scene_text, chapter_id),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    review["styleAnalysis"]["profileSource"] = profile_source
    review["styleAnalysis"]["reviewRuleProfileSource"] = review_rule_source
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


def command_review_preflight(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = build_review_preflight_payload(
        root,
        state,
        chapter_id=args.chapter_id,
        volume_id=args.volume_id,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_review_volume_self(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    volume = _find_volume(state, args.volume_id)
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"卷级自审输入文件不存在: {input_path}")

    raw_payload = load_json_compatible_yaml(input_path, {})
    merged_inputs: list[str] = []
    for overlay_path in _resolve_overlay_paths(args.merge_input):
        raw_payload = merge_volume_self_review_payload(
            raw_payload,
            _load_volume_self_overlay(overlay_path),
        )
        merged_inputs.append(str(overlay_path))
    editor_input_path = _resolve_optional_overlay_path(args.editor_input)
    if editor_input_path is not None:
        editor_overlay = _load_volume_self_overlay(editor_input_path)
        if "editorPass" not in editor_overlay and "editorAssessment" not in editor_overlay:
            raise SystemExit("editor-input 必须至少包含 editorPass 或 editorAssessment。")
        raw_payload = merge_volume_self_review_payload(
            raw_payload,
            editor_overlay,
            sections=("editorPass", "editorAssessment"),
        )
    generated_at = raw_payload.get("generatedAt") or now_iso()
    try:
        review = normalize_volume_self_review(
            raw_payload,
            volume_id=volume.get("id", ""),
            volume_title=volume.get("title", volume.get("id", "")),
            generated_at=generated_at,
        )
        validate_volume_self_review_refs(
            review,
            chapter_anchor_index=_build_volume_chapter_anchor_index(root, state, volume),
            volume_id=volume.get("id", ""),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    story_reviews = state["story_reviews"].setdefault("volumeSelfReviews", [])
    state["story_reviews"]["volumeSelfReviewRubricVersion"] = review["rubricVersion"]
    for index, existing in enumerate(story_reviews):
        if (
            existing.get("volumeId") == review["volumeId"]
            and existing.get("generatedAt") == review["generatedAt"]
        ):
            story_reviews[index] = review
            break
    else:
        story_reviews.append(review)

    save_state(root, state)
    review_packet_file = ""
    review_packet_refreshed = False
    review_packet_refresh_error = ""
    try:
        review_packet_file = str(write_volume_review_packet(root, state, volume))
        review_packet_refreshed = True
    except OSError as exc:
        review_packet_refresh_error = str(exc)
    print(
        json.dumps(
            {
                "saved": True,
                "reviewFile": str(resolve_state_path(root, "story_reviews")),
                "reviewPacketFile": review_packet_file,
                "reviewPacketRefreshed": review_packet_refreshed,
                "reviewPacketRefreshError": review_packet_refresh_error,
                "inputFile": str(input_path),
                "mergedInputs": merged_inputs,
                "editorInput": str(editor_input_path) if editor_input_path else "",
                "volumeId": review["volumeId"],
                "volumeTitle": review["volumeTitle"],
                "finalAllowHumanReview": review["finalAllowHumanReview"],
                "gateFailures": review["gateFailures"],
                "review": review,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_review_volume_self_template(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    volume = _find_volume(state, args.volume_id)
    preflight_payload = build_review_preflight_payload(root, state, volume_id=args.volume_id)
    latest_review = latest_volume_self_review(state.get("story_reviews", {}), args.volume_id)
    try:
        payload = build_volume_self_review_template(
            preflight_payload,
            generated_at=now_iso(),
            latest_review=latest_review,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    merged_inputs: list[str] = []
    for overlay_path in _resolve_overlay_paths(args.merge_input):
        payload = merge_volume_self_review_payload(
            payload,
            _load_volume_self_overlay(overlay_path),
        )
        merged_inputs.append(str(overlay_path))
    editor_input_path = _resolve_optional_overlay_path(args.editor_input)
    if editor_input_path is not None:
        editor_overlay = _load_volume_self_overlay(editor_input_path)
        if "editorPass" not in editor_overlay and "editorAssessment" not in editor_overlay:
            raise SystemExit("editor-input 必须至少包含 editorPass 或 editorAssessment。")
        payload = merge_volume_self_review_payload(
            payload,
            editor_overlay,
            sections=("editorPass", "editorAssessment"),
        )
    mode = "draft" if merged_inputs or editor_input_path else "template"

    if args.output:
        output_path = Path(args.output)
        if output_path.exists() and output_path.is_dir():
            suffix = "draft.yaml" if mode == "draft" else "template.yaml"
            output_path = output_path / f"{args.volume_id}-volume-self-review.{suffix}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = {
            "saved": True,
            "outputFile": str(output_path.resolve()),
            "volumeId": args.volume_id,
            "mode": mode,
            "mergedInputs": merged_inputs,
            "editorInput": str(editor_input_path) if editor_input_path else "",
            "template": payload,
        }
    else:
        result = {
            "saved": False,
            "outputFile": "",
            "volumeId": args.volume_id,
            "mode": mode,
            "mergedInputs": merged_inputs,
            "editorInput": str(editor_input_path) if editor_input_path else "",
            "template": payload,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _find_volume(state: dict, volume_id: str) -> dict:
    for volume in state.get("outline", {}).get("volumes", []):
        if volume.get("id") == volume_id:
            return volume
    raise SystemExit(f"volume 不存在: {volume_id}")


def _find_volume_for_chapter(state: dict, chapter_id: str) -> dict:
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return {}


def _find_outline_chapter(state: dict, chapter_id: str) -> dict:
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return chapter
    for chapter in state.get("outline", {}).get("chapters", []):
        if chapter.get("id") == chapter_id:
            return chapter
    return {}


def _find_previous_outline_chapter(state: dict, chapter_id: str) -> dict:
    previous: dict = {}
    for volume in state.get("outline", {}).get("volumes", []):
        previous = {}
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return previous
            previous = chapter if isinstance(chapter, dict) else {}
    previous = {}
    for chapter in state.get("outline", {}).get("chapters", []):
        if chapter.get("id") == chapter_id:
            return previous
        previous = chapter if isinstance(chapter, dict) else {}
    return {}


def _previous_chapter_ending_text(root: Path, state: dict, chapter_id: str, paragraph_limit: int = 16) -> str:
    previous_chapter = _find_previous_outline_chapter(state, chapter_id)
    previous_chapter_id = str(previous_chapter.get("id", "")).strip()
    if not previous_chapter_id:
        return ""
    previous_file = chapter_path(root, previous_chapter_id)
    if not previous_file.exists():
        return ""
    paragraphs = paragraphs_from_text(previous_file.read_text(encoding="utf-8"))
    if not paragraphs:
        return ""
    return "\n\n".join(paragraphs[-paragraph_limit:])


def _build_volume_chapter_anchor_index(root: Path, state: dict, volume: dict) -> dict:
    chapters: dict[str, dict] = {}
    scene_reviews = state.get("story_reviews", {}).get("sceneReviews", [])
    chapter_reviews = state.get("story_reviews", {}).get("chapterReviews", [])
    for chapter_ref in volume.get("chapters", []):
        chapter_id = str(chapter_ref.get("id", "")).strip()
        if not chapter_id:
            continue
        chapter_entry = _find_outline_chapter(state, chapter_id)
        chapter_file = chapter_path(root, chapter_id)
        chapter_file_exists = chapter_file.exists()
        paragraph_count = 0
        if chapter_file_exists:
            paragraph_count = len(paragraphs_from_text(chapter_file.read_text(encoding="utf-8")))
        scene_numbers: list[int] = []
        scene_plan_ids: dict[str, int] = {}
        for index, scene in enumerate(chapter_entry.get("scenePlans", []), start=1):
            if not isinstance(scene, dict):
                continue
            scene_numbers.append(index)
            scene_id = str(scene.get("id", "")).strip()
            if scene_id:
                scene_plan_ids[scene_id] = index
        reviewed_scene_numbers = _collect_reviewed_scene_numbers(
            scene_reviews,
            chapter_id=chapter_id,
            scene_plan_ids=scene_plan_ids,
        )
        semantic_anchors = set()
        if chapter_file_exists:
            world_check = build_world_check_payload(root, state, chapter_id)
            if world_check.get("onboardingGaps"):
                semantic_anchors.add("world-rule-onboarding")
        if _chapter_has_handoff_gap(chapter_reviews, chapter_id):
            semantic_anchors.add("handoff-gap")
        chapters[chapter_id] = {
            "chapterId": chapter_id,
            "paragraphCount": paragraph_count,
            "sceneNumbers": scene_numbers,
            "reviewedSceneNumbers": reviewed_scene_numbers,
            "semanticAnchors": sorted(semantic_anchors),
            "chapterFileExists": chapter_file_exists,
        }
    return {
        "volumeId": volume.get("id", ""),
        "chapters": chapters,
    }


def _collect_reviewed_scene_numbers(
    scene_reviews: list[dict],
    *,
    chapter_id: str,
    scene_plan_ids: dict[str, int],
) -> list[int]:
    reviewed: list[int] = []
    for review in scene_reviews:
        if review.get("chapterId") != chapter_id:
            continue
        scene_range = review.get("sceneRange", {})
        scene_index = scene_range.get("sceneIndex")
        if isinstance(scene_index, int) and scene_index > 0 and scene_index not in reviewed:
            reviewed.append(scene_index)
            continue
        scene_plan_id = str(scene_range.get("scenePlanId", "")).strip()
        mapped_index = scene_plan_ids.get(scene_plan_id)
        if mapped_index and mapped_index not in reviewed:
            reviewed.append(mapped_index)
    reviewed.sort()
    return reviewed


def _chapter_has_handoff_gap(chapter_reviews: list[dict], chapter_id: str) -> bool:
    normalized_chapter_id = chapter_id.lower()
    for item in chapter_reviews:
        if str(item.get("chapterId", "")).strip().lower() != normalized_chapter_id:
            continue
        chapter_handoff_signals = item.get("chapterHandoffSignals", {})
        if isinstance(chapter_handoff_signals, dict) and chapter_handoff_signals.get("detected"):
            return True
        for judgement in item.get("ruleJudgements", []):
            if not isinstance(judgement, dict):
                continue
            rule_id = str(judgement.get("ruleId", "")).strip().lower()
            if rule_id in {"chapterhandoffweak", "chapter-handoff-weak"}:
                return True
    return False


def _resolve_overlay_paths(raw_paths: list[str] | None) -> list[Path]:
    return [Path(item).resolve() for item in (raw_paths or [])]


def _resolve_optional_overlay_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    return Path(raw_path).resolve()


def _load_volume_self_overlay(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"卷级自审覆盖输入文件不存在: {path}")
    payload = load_json_compatible_yaml(path, {})
    if not isinstance(payload, dict):
        raise SystemExit(f"卷级自审覆盖输入必须是对象: {path}")
    return payload


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

    preflight_parser = review_subparsers.add_parser(
        "preflight",
        help="Aggregate mention, foreshadow, and world-scale checks for one chapter or one volume",
    )
    preflight_parser.add_argument("--root", required=True)
    preflight_parser.add_argument("--chapter-id")
    preflight_parser.add_argument("--volume-id")
    preflight_parser.set_defaults(func=command_review_preflight)

    volume_self_parser = review_subparsers.add_parser(
        "volume-self",
        help="Persist one structured volume AI self-review result",
    )
    volume_self_parser.add_argument("--root", required=True)
    volume_self_parser.add_argument("--volume-id", required=True)
    volume_self_parser.add_argument("--input", required=True)
    volume_self_parser.add_argument("--merge-input", action="append")
    volume_self_parser.add_argument("--editor-input")
    volume_self_parser.set_defaults(func=command_review_volume_self)

    volume_self_template_parser = review_subparsers.add_parser(
        "volume-self-template",
        help="Generate a structured template file for one volume AI self-review",
    )
    volume_self_template_parser.add_argument("--root", required=True)
    volume_self_template_parser.add_argument("--volume-id", required=True)
    volume_self_template_parser.add_argument("-o", "--output")
    volume_self_template_parser.add_argument("--merge-input", action="append")
    volume_self_template_parser.add_argument("--editor-input")
    volume_self_template_parser.set_defaults(func=command_review_volume_self_template)

    scene_parser = review_subparsers.add_parser("scene", help="Review one scene fragment by paragraph range or scene index")
    scene_parser.add_argument("--root", required=True)
    scene_parser.add_argument("--chapter-id")
    scene_parser.add_argument("--list-scenes", action="store_true")
    scene_parser.add_argument("--scene-index", type=int)
    scene_parser.add_argument("--start-paragraph", type=int)
    scene_parser.add_argument("--end-paragraph", type=int)
    scene_parser.set_defaults(func=command_review_scene)
