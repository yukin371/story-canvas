from __future__ import annotations

import json
import sys
from pathlib import Path

from story_harness_cli.commands.project_support import build_project_advisories
from story_harness_cli.commands.review_support import build_review_preflight_payload
from story_harness_cli.protocol import ensure_project_root, load_project_state
from story_harness_cli.services import latest_volume_self_review
from story_harness_cli.services.reference_mentions import build_reference_mention_report
from story_harness_cli.utils.text import count_words, strip_entity_tags, strip_markdown


def command_export(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    fmt = args.format
    chapter_id = getattr(args, "chapter_id", None)
    volume_id = getattr(args, "volume_id", None)
    if chapter_id and volume_id:
        raise SystemExit("`--chapter-id` 与 `--volume-id` 不能同时使用")
    volume = _find_volume(state, volume_id) if volume_id else None

    # Hierarchical format always exports as split files
    if fmt == "spec-outline-hierarchical":
        return _export_hierarchical_split(state, args)

    # Spec formats export structured data, not chapter prose
    if fmt == "spec-outline":
        output = _generate_spec_outline(state)
    elif fmt == "spec-characters":
        output = _generate_spec_characters(state)
    elif fmt == "spec-global-outline":
        output = _generate_spec_global_outline(state)
    elif fmt == "spec-detail":
        output = _generate_spec_detail(state)
    elif fmt == "review-packet":
        output = _generate_review_packet(state, root, chapter_id, volume)
    else:
        output = _export_chapter_prose(state, root, fmt, chapter_id, volume)

    # Output destination
    if args.output:
        out_path = Path(args.output)
        if out_path.is_dir():
            ext = _format_extension(fmt)
            out_path = out_path / f"{_default_export_name(state, fmt, volume)}{ext}"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"已导出到 {out_path}", file=sys.stderr)
    else:
        _write_stdout(output)

    return 0


def write_volume_review_packet(
    root: Path,
    state: dict,
    volume: dict,
    *,
    output_path: Path | None = None,
) -> Path:
    target_path = output_path or _default_volume_review_packet_path(root, volume)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(_generate_volume_review_packet(state, root, volume), encoding="utf-8")
    return target_path.resolve()


def write_volume_review_packet_for_chapter(
    root: Path,
    state: dict,
    chapter_id: str,
) -> Path | None:
    volume = _find_volume_for_chapter(state, chapter_id)
    if volume is None:
        return None
    return write_volume_review_packet(root, state, volume)


def _chapter_title(state: dict, chapter_id: str) -> str:
    for vol in state.get("outline", {}).get("volumes", []):
        for ch in vol.get("chapters", []):
            if ch.get("id") == chapter_id:
                return ch.get("title", chapter_id)
    for ch in state.get("outline", {}).get("chapters", []):
        if ch.get("id") == chapter_id:
            return ch.get("title", chapter_id)
    return chapter_id


def _ordered_chapter_ids(state: dict) -> list[str]:
    chapter_ids = []
    for vol in state.get("outline", {}).get("volumes", []):
        for ch in vol.get("chapters", []):
            cid = ch.get("id")
            if cid:
                chapter_ids.append(cid)
    if not chapter_ids:
        for ch in state.get("outline", {}).get("chapters", []):
            cid = ch.get("id")
            if cid:
                chapter_ids.append(cid)
    return chapter_ids


def _find_volume(state: dict, volume_id: str | None) -> dict | None:
    if not volume_id:
        return None
    for volume in state.get("outline", {}).get("volumes", []):
        if volume.get("id") == volume_id:
            return volume
    raise SystemExit(f"volume 不存在: {volume_id}")


def _resolve_export_scope(
    state: dict,
    *,
    chapter_id: str | None,
    volume: dict | None,
) -> list[str]:
    if chapter_id:
        return [chapter_id]
    if volume is not None:
        chapter_ids = [item.get("id") for item in volume.get("chapters", []) if item.get("id")]
        if not chapter_ids:
            raise SystemExit(f"volume `{volume.get('id', '')}` 下没有可导出的章节")
        return chapter_ids
    return _ordered_chapter_ids(state)


def _default_export_name(state: dict, fmt: str, volume: dict | None) -> str:
    if volume is not None:
        title = str(volume.get("title") or volume.get("id") or "volume").strip()
        if fmt == "review-packet":
            return f"{title}-review-packet"
        return title
    return state["project"].get("title", "manuscript")


def _default_volume_review_packet_path(root: Path, volume: dict) -> Path:
    volume_id = str(volume.get("id") or "").strip()
    filename = f"{volume_id}-review-packet.md" if volume_id else "volume-review-packet.md"
    return root / "reviews" / filename


def _find_volume_for_chapter(state: dict, chapter_id: str | None) -> dict | None:
    if not chapter_id:
        return None
    for volume in state.get("outline", {}).get("volumes", []):
        for chapter in volume.get("chapters", []):
            if chapter.get("id") == chapter_id:
                return volume
    return None


def _find_outline_chapter(state: dict, chapter_id: str) -> dict:
    for vol in state.get("outline", {}).get("volumes", []):
        for ch in vol.get("chapters", []):
            if ch.get("id") == chapter_id:
                return ch
    for ch in state.get("outline", {}).get("chapters", []):
        if ch.get("id") == chapter_id:
            return ch
    return {}


def _find_detailed_entry(state: dict, chapter_id: str) -> dict:
    for entry in state.get("detailed_outlines", {}).get("entries", []):
        if entry.get("chapterId") == chapter_id:
            return entry
    return {}


def _export_chapter_prose(
    state: dict,
    root: Path,
    fmt: str,
    chapter_id: str | None,
    volume: dict | None,
) -> str:
    """Export chapter prose in txt/json/markdown formats."""
    ordered_chapter_ids = _ordered_chapter_ids(state)
    chapter_ids = _resolve_export_scope(state, chapter_id=chapter_id, volume=volume)

    if not chapter_ids:
        raise SystemExit("没有找到可导出的章节")

    next_title_by_id = {}
    for index, cid in enumerate(ordered_chapter_ids[:-1]):
        next_cid = ordered_chapter_ids[index + 1]
        if next_cid:
            next_title_by_id[cid] = _chapter_title(state, next_cid)

    # Collect chapter data
    chapters_data = []
    for cid in chapter_ids:
        cp = _find_chapter_file(root, cid)
        if not cp:
            continue
        raw = cp.read_text(encoding="utf-8")
        title = _chapter_title(state, cid)
        clean = _strip_export_boundary_headings(
            strip_entity_tags(raw),
            title=title,
            next_title=next_title_by_id.get(cid, ""),
        )
        if fmt == "txt":
            clean = strip_markdown(clean)
        chapters_data.append({"chapterId": cid, "title": title, "content": clean, "wordCount": count_words(clean)})

    if not chapters_data:
        raise SystemExit("没有找到章节文件")

    if fmt == "json":
        return json.dumps(chapters_data, ensure_ascii=False, indent=2)
    elif fmt == "markdown":
        parts = []
        for ch in chapters_data:
            parts.append(f"## {ch['title']}\n\n{ch['content']}")
        return "\n\n".join(parts)
    else:  # txt
        return "\n\n".join(ch["content"] for ch in chapters_data)


def _generate_review_packet(
    state: dict,
    root: Path,
    chapter_id: str | None,
    volume: dict | None,
) -> str:
    if volume is not None:
        return _generate_volume_review_packet(state, root, volume)

    resolved_chapter_id = chapter_id or state.get("project", {}).get("activeChapterId")
    if not resolved_chapter_id:
        ordered = _ordered_chapter_ids(state)
        resolved_chapter_id = ordered[0] if ordered else ""
    if not resolved_chapter_id:
        raise SystemExit("没有找到可导出的章节，无法生成审查包")

    chapter_file = _find_chapter_file(root, resolved_chapter_id)
    if not chapter_file:
        raise SystemExit(f"没有找到章节文件: {resolved_chapter_id}")

    chapter_entry = _find_outline_chapter(state, resolved_chapter_id)
    detailed_entry = _find_detailed_entry(state, resolved_chapter_id)
    title = _chapter_title(state, resolved_chapter_id)
    chapter_text = _strip_export_boundary_headings(
        strip_entity_tags(chapter_file.read_text(encoding="utf-8")),
        title=title,
        next_title="",
    )

    direction = detailed_entry.get("direction") or chapter_entry.get("direction", "")
    beats = detailed_entry.get("beats") or chapter_entry.get("beats", [])
    scenes = detailed_entry.get("scenePlans") or chapter_entry.get("scenePlans", [])

    story_reviews = state.get("story_reviews", {})
    chapter_review = _latest_matching(
        story_reviews.get("chapterReviews", []),
        lambda item: item.get("chapterId") == resolved_chapter_id,
    )
    scene_reviews = _latest_scene_reviews(story_reviews.get("sceneReviews", []), resolved_chapter_id)
    mention_report = build_reference_mention_report(state, chapter_file.read_text(encoding="utf-8"))

    parts = [
        f"# 审查包: {state.get('project', {}).get('title', '未命名')} / {title}",
        "",
        f"- chapterId: `{resolved_chapter_id}`",
    ]
    status = chapter_entry.get("status", "")
    if status:
        parts.append(f"- 状态: `{status}`")
    parts.append(f"- 正文字数: `{count_words(chapter_text)}`")
    parts.append("")

    project_advisories = build_project_advisories(root, include_prd_content=True)
    _append_markdown_list(parts, "## 项目提示", _format_project_advisory_lines(project_advisories))

    parts.append("## 章节目标")
    parts.append("")
    if direction:
        parts.append(f"**方向:** {direction}")
        parts.append("")
    if beats:
        parts.append("**节拍:**")
        for beat in beats:
            if isinstance(beat, dict):
                parts.append(f"- {beat.get('summary', beat.get('description', str(beat)))}")
            else:
                parts.append(f"- {beat}")
        parts.append("")
    if scenes:
        parts.append("**场景计划:**")
        for index, scene in enumerate(scenes, 1):
            title_part = scene.get("title", "")
            summary_part = scene.get("summary", "")
            paragraph_part = ""
            start = scene.get("startParagraph")
            end = scene.get("endParagraph")
            if start and end:
                paragraph_part = f" (`{start}..{end}`)"
            if title_part and summary_part:
                parts.append(f"{index}. {title_part}{paragraph_part}：{summary_part}")
            elif summary_part:
                parts.append(f"{index}. {summary_part}{paragraph_part}")
            elif title_part:
                parts.append(f"{index}. {title_part}{paragraph_part}")
        parts.append("")

    parts.append("## 引用卫生")
    parts.append("")
    parts.append(f"- 已建档未包裹: `{mention_report.get('summary', {}).get('knownUnwrappedCount', 0)}`")
    parts.append(f"- 已包裹未建档: `{mention_report.get('summary', {}).get('taggedMissingCount', 0)}`")
    parts.append(f"- 引号内已知称呼: `{mention_report.get('summary', {}).get('ignoredQuotedKnownMentionCount', 0)}`")
    parts.append("")
    _append_markdown_list(parts, "**待补包裹:**", _format_known_unwrapped_lines(mention_report.get("knownUnwrapped", [])))
    _append_markdown_list(parts, "**待补建档:**", _format_tagged_missing_lines(mention_report.get("taggedMissing", [])))

    parts.append("## 机器审查摘要")
    parts.append("")
    if chapter_review:
        total = chapter_review.get("scores", {}).get("total")
        rating = chapter_review.get("rating", "")
        summary = chapter_review.get("summary", "")
        if total is not None:
            parts.append(f"- chapter review: `{total}/100` ({rating or 'unrated'})")
        elif rating:
            parts.append(f"- chapter review: `{rating}`")
        if summary:
            parts.append(f"- 摘要: {summary}")

        weighted = chapter_review.get("weightedScores", {})
        if weighted.get("total") is not None:
            parts.append(f"- 加权总分: `{weighted.get('total')}`")

        style_summary = chapter_review.get("styleAnalysis", {}).get("styleAnalysis", {}).get("summary", "")
        if style_summary:
            parts.append(f"- 风格检测: {style_summary}")

        parts.append("")
        _append_markdown_list(parts, "**优先动作:**", chapter_review.get("priorityActions", []))
        _append_markdown_list(parts, "**优势:**", chapter_review.get("strengths", []))
        _append_markdown_list(parts, "**契约风险:**", chapter_review.get("contractAlignment", {}).get("risks", []))
        _append_markdown_list(parts, "**商业风险:**", chapter_review.get("commercialAlignment", {}).get("risks", []))
        _append_markdown_list(parts, "**规则命中:**", _format_judgement_lines(chapter_review.get("ruleJudgements", [])))
    else:
        parts.append("当前章节还没有 `review chapter` 结果。")
        parts.append("")

    parts.append("## 场景审查")
    parts.append("")
    if scene_reviews:
        for review in scene_reviews:
            scene_range = review.get("sceneRange", {})
            scene_index = scene_range.get("sceneIndex")
            start = scene_range.get("startParagraph")
            end = scene_range.get("endParagraph")
            header = "### 场景"
            if scene_index is not None:
                header = f"### 场景 {scene_index}"
            if start and end:
                header += f" (`{start}..{end}`)"
            parts.append(header)
            parts.append("")
            total = review.get("scores", {}).get("total")
            rating = review.get("rating", "")
            if total is not None:
                parts.append(f"- scene review: `{total}/100` ({rating or 'unrated'})")
            elif rating:
                parts.append(f"- scene review: `{rating}`")
            if review.get("summary"):
                parts.append(f"- 摘要: {review.get('summary')}")
            parts.append("")
            _append_markdown_list(parts, "**优先动作:**", review.get("priorityActions", []))
            _append_markdown_list(parts, "**优势:**", review.get("strengths", []))
            _append_markdown_list(parts, "**规则命中:**", _format_judgement_lines(review.get("ruleJudgements", [])))
    else:
        parts.append("当前章节还没有 `review scene` 结果。")
        parts.append("")

    parts.append("## 正文")
    parts.append("")
    parts.append(chapter_text or "暂无正文。")
    parts.append("")
    return "\n".join(parts)


def _generate_volume_review_packet(state: dict, root: Path, volume: dict) -> str:
    chapter_ids = _resolve_export_scope(state, chapter_id=None, volume=volume)
    story_reviews = state.get("story_reviews", {})
    chapter_reviews = story_reviews.get("chapterReviews", [])
    scene_reviews = story_reviews.get("sceneReviews", [])
    volume_self_review = latest_volume_self_review(story_reviews, volume.get("id", ""))
    preflight_payload = build_review_preflight_payload(root, state, volume_id=volume.get("id", ""))
    volume_structure_check = preflight_payload.get("volumeStructureCheck", {})
    project_title = state.get("project", {}).get("title", "未命名")
    volume_title = volume.get("title", volume.get("id", "未命名卷"))
    volume_theme = volume.get("theme", "")

    parts = [
        f"# 卷级审查包: {project_title} / {volume_title}",
        "",
        f"- volumeId: `{volume.get('id', '')}`",
        f"- 章节数: `{len(chapter_ids)}`",
    ]
    if volume_theme:
        parts.append(f"- 卷主题: {volume_theme}")
    parts.append("")

    project_advisories = build_project_advisories(root, include_prd_content=True)
    _append_markdown_list(parts, "## 项目提示", _format_project_advisory_lines(project_advisories))

    parts.append("## 卷级 AI 自审")
    parts.append("")
    if volume_self_review:
        conclusion = volume_self_review.get("conclusion", {})
        closure_assessment = volume_self_review.get("closureAssessment", {})
        parts.append(f"- 生成时间: `{volume_self_review.get('generatedAt', '')}`")
        parts.append(f"- 闭环状态: `{conclusion.get('closureStatus', '')}`")
        parts.append(
            f"- 人工审查许可: 声明 `{_yes_no(conclusion.get('allowHumanReview'))}` / "
            f"工具判定 `{_yes_no(volume_self_review.get('finalAllowHumanReview'))}`"
        )
        if conclusion.get("strongestPoint"):
            parts.append(f"- 最强项: {conclusion.get('strongestPoint')}")
        if conclusion.get("biggestRisk"):
            parts.append(f"- 最大风险: {conclusion.get('biggestRisk')}")
        score_summary = volume_self_review.get("scoreSummary", {})
        if score_summary.get("average") is not None:
            parts.append(f"- 平均分: `{score_summary.get('average')}/5`")
        if score_summary.get("lowestDimensions"):
            parts.append(
                f"- 最弱维度: {' / '.join(score_summary.get('lowestDimensions', []))} "
                f"(`{score_summary.get('lowestScore', '')}/5`)"
            )
        repair_coverage = volume_self_review.get("repairCoverage", {})
        if repair_coverage:
            parts.append(f"- 修复覆盖状态: `{repair_coverage.get('status', '')}`")
            weak_labels = repair_coverage.get("weakDimensionLabels", [])
            if weak_labels:
                parts.append(f"- 待覆盖弱项: {' / '.join(weak_labels)}")
            uncovered_labels = repair_coverage.get("uncoveredWeakDimensionLabels", [])
            parts.append(
                "- 未覆盖弱项: "
                + (" / ".join(uncovered_labels) if uncovered_labels else "无")
            )
        if closure_assessment.get("mainProblem"):
            parts.append(f"- 本卷主问题: {closure_assessment.get('mainProblem')}")
        parts.append("")
        parts.append("**评分:**")
        for item in volume_self_review.get("scores", []):
            parts.append(
                f"- {item.get('label', item.get('dimensionId', ''))}: "
                f"`{item.get('score', '')}/5` - {item.get('conclusion', '')}"
            )
        parts.append("")
        _append_markdown_list(
            parts,
            "**主要问题:**",
            [
                f"{item.get('issue', '')}（{item.get('primaryCause', '')}）；修正：{item.get('fixAction', '')}"
                for item in volume_self_review.get("issues", [])
                if item.get("issue")
            ],
        )
        _append_markdown_list(parts, "**修后建议:**", volume_self_review.get("repairSuggestions", []))
        _append_markdown_list(parts, "**接受风险:**", volume_self_review.get("acceptedRisks", []))
        _append_markdown_list(
            parts,
            "**人工审查阻塞:**",
            [item.get("message", "") for item in volume_self_review.get("gateFailures", []) if item.get("message")],
        )
    else:
        parts.append("当前卷还没有 `review volume-self` 结果。")
        parts.append("")

    parts.append("## 卷级结构检查")
    parts.append("")
    if volume_structure_check:
        parts.append(f"- 结构角色: `{volume_structure_check.get('role', '')}`")
        structure_summary = volume_structure_check.get("summary", {})
        parts.append(
            f"- 检查摘要: pass `{structure_summary.get('passCount', 0)}` / "
            f"risk `{structure_summary.get('riskCount', 0)}` / "
            f"missing `{structure_summary.get('missingCount', 0)}` / "
            f"n/a `{structure_summary.get('notApplicableCount', 0)}`"
        )
        parts.append("")
        _append_markdown_list(
            parts,
            "**阶段映射:**",
            [
                f"{item.get('chapterTitle', item.get('chapterId', ''))}: `{item.get('phase', '')}`"
                for item in volume_structure_check.get("phaseAssignments", [])
            ],
        )
        _append_markdown_list(
            parts,
            "**结构检查项:**",
            [
                (
                    f"{item.get('label', item.get('id', ''))} [{item.get('status', '')}] "
                    f"{item.get('message', '')}"
                )
                for item in volume_structure_check.get("checklist", [])
            ],
        )
    else:
        parts.append("当前卷还没有可用的结构检查信号。")
        parts.append("")

    parts.append("## 章节目录")
    parts.append("")

    aggregated_actions: list[str] = []
    aggregated_strengths: list[str] = []
    aggregated_risks: list[str] = []
    aggregated_known_unwrapped: list[str] = []
    aggregated_tagged_missing: list[str] = []

    for chapter_id in chapter_ids:
        chapter_entry = _find_outline_chapter(state, chapter_id)
        title = _chapter_title(state, chapter_id)
        chapter_file = _find_chapter_file(root, chapter_id)
        chapter_text = ""
        mention_report = None
        if chapter_file:
            raw_text = chapter_file.read_text(encoding="utf-8")
            mention_report = build_reference_mention_report(state, raw_text)
            chapter_text = _strip_export_boundary_headings(
                strip_entity_tags(raw_text),
                title=title,
                next_title="",
            )
        word_count = count_words(chapter_text) if chapter_text else 0
        status = chapter_entry.get("status", "")
        status_suffix = f" [{status}]" if status else ""
        parts.append(f"### {title}{status_suffix}")
        parts.append("")
        parts.append(f"- chapterId: `{chapter_id}`")
        parts.append(f"- 正文字数: `{word_count}`")

        chapter_review = _latest_matching(
            chapter_reviews,
            lambda item, cid=chapter_id: item.get("chapterId") == cid,
        )
        if chapter_review:
            score = chapter_review.get("scores", {}).get("total")
            rating = chapter_review.get("rating", "")
            if score is not None:
                parts.append(f"- chapter review: `{score}/100` ({rating or 'unrated'})")
            elif rating:
                parts.append(f"- chapter review: `{rating}`")
            if chapter_review.get("summary"):
                parts.append(f"- 摘要: {chapter_review.get('summary')}")
            aggregated_actions.extend(chapter_review.get("priorityActions", []))
            aggregated_strengths.extend(chapter_review.get("strengths", []))
            aggregated_risks.extend(chapter_review.get("contractAlignment", {}).get("risks", []))
            aggregated_risks.extend(chapter_review.get("commercialAlignment", {}).get("risks", []))
        else:
            parts.append("- chapter review: `missing`")

        scene_review_count = len(_latest_scene_reviews(scene_reviews, chapter_id))
        parts.append(f"- scene review 数: `{scene_review_count}`")
        if mention_report:
            parts.append(
                f"- mention hygiene: 已建档未包裹 `{mention_report.get('summary', {}).get('knownUnwrappedCount', 0)}` / "
                f"已包裹未建档 `{mention_report.get('summary', {}).get('taggedMissingCount', 0)}`"
            )
            aggregated_known_unwrapped.extend(
                f"{title}: {line}" for line in _format_known_unwrapped_lines(mention_report.get("knownUnwrapped", []))
            )
            aggregated_tagged_missing.extend(
                f"{title}: {line}" for line in _format_tagged_missing_lines(mention_report.get("taggedMissing", []))
            )
        parts.append("")

    parts.append("## 聚合机器审查摘要")
    parts.append("")
    _append_markdown_list(parts, "**优先动作:**", _dedupe_preserve_order(aggregated_actions))
    _append_markdown_list(parts, "**优势:**", _dedupe_preserve_order(aggregated_strengths))
    _append_markdown_list(parts, "**风险:**", _dedupe_preserve_order(aggregated_risks))
    _append_markdown_list(parts, "**待补包裹:**", _dedupe_preserve_order(aggregated_known_unwrapped))
    _append_markdown_list(parts, "**待补建档:**", _dedupe_preserve_order(aggregated_tagged_missing))
    if len(parts) >= 2 and parts[-1] != "":
        parts.append("")

    parts.append("## 正文")
    parts.append("")
    for chapter_id in chapter_ids:
        chapter_file = _find_chapter_file(root, chapter_id)
        if not chapter_file:
            continue
        title = _chapter_title(state, chapter_id)
        chapter_text = _strip_export_boundary_headings(
            strip_entity_tags(chapter_file.read_text(encoding="utf-8")),
            title=title,
            next_title="",
        )
        parts.append(f"### {title}")
        parts.append("")
        parts.append(chapter_text or "暂无正文。")
        parts.append("")

    return "\n".join(parts)


def _latest_matching(items: list[dict], predicate) -> dict:
    latest = {}
    for item in items:
        if predicate(item):
            latest = item
    return latest


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _append_markdown_list(parts: list[str], label: str, items: list[str]) -> None:
    if not items:
        return
    parts.append(label)
    for item in items:
        parts.append(f"- {item}")
    parts.append("")


def _format_known_unwrapped_lines(items: list[dict]) -> list[str]:
    lines: list[str] = []
    for item in items:
        name = item.get("name", "")
        count = item.get("plainCount", 0)
        source = item.get("source", "")
        if not name:
            continue
        lines.append(f"{name} (`{count}` 次，来源 `{source}`)")
    return lines


def _format_tagged_missing_lines(items: list[dict]) -> list[str]:
    lines: list[str] = []
    for item in items:
        name = item.get("name", "")
        count = item.get("occurrenceCount", 0)
        if not name:
            continue
        lines.append(f"{name} (`{count}` 次)")
    return lines


def _format_judgement_lines(judgements: list[dict]) -> list[str]:
    lines = []
    for judgement in judgements:
        message = judgement.get("message", "")
        severity = judgement.get("severity", "")
        suggestion = judgement.get("suggestion", "")
        line = message
        if severity:
            line = f"[{severity}] {line}"
        if suggestion:
            line = f"{line}；建议：{suggestion}"
        if line:
            lines.append(line)
    return lines


def _format_project_advisory_lines(advisories: list[dict]) -> list[str]:
    lines: list[str] = []
    for item in advisories:
        message = str(item.get("message", "")).strip()
        next_action = str(item.get("nextAction", "")).strip()
        line = message
        if next_action:
            line = f"{line}；下一步：{next_action}" if line else next_action
        if line:
            lines.append(line)
    return lines


def _yes_no(value: object) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def _latest_scene_reviews(scene_reviews: list[dict], chapter_id: str) -> list[dict]:
    latest_by_key: dict[tuple, dict] = {}
    order: list[tuple] = []
    for review in scene_reviews:
        if review.get("chapterId") != chapter_id:
            continue
        scene_range = review.get("sceneRange", {})
        if scene_range.get("scenePlanId"):
            key = ("scenePlanId", scene_range.get("scenePlanId"))
        elif scene_range.get("sceneIndex") is not None:
            key = ("sceneIndex", scene_range.get("sceneIndex"))
        else:
            key = (
                "paragraphRange",
                scene_range.get("startParagraph"),
                scene_range.get("endParagraph"),
            )
        if key not in latest_by_key:
            order.append(key)
        latest_by_key[key] = review

    result = [latest_by_key[key] for key in order]
    result.sort(
        key=lambda item: (
            item.get("sceneRange", {}).get("sceneIndex", 999999),
            item.get("sceneRange", {}).get("startParagraph", 999999),
        )
    )
    return result


def _generate_spec_outline(state: dict) -> str:
    """Generate a human-readable Markdown outline spec."""
    title = state["project"].get("title", "未命名")
    parts = [f"# 大纲: {title}", ""]

    outline = state.get("outline", {})
    volumes = outline.get("volumes", [])

    if volumes:
        for vol in volumes:
            vol_title = vol.get("title", "未命名卷")
            parts.append(f"## 卷: {vol_title}")
            parts.append("")
            for ch in vol.get("chapters", []):
                _append_chapter_spec(parts, ch)
    else:
        # Flat chapters list (no volumes)
        for ch in outline.get("chapters", []):
            _append_chapter_spec(parts, ch)

    return "\n".join(parts)


def _append_chapter_spec(parts: list, ch: dict) -> None:
    """Append a single chapter's spec-block to parts list."""
    ch_id = ch.get("id", "unknown")
    ch_title = ch.get("title", "未命名")
    status = ch.get("status", "")
    status_label = f" [{status}]" if status else ""
    parts.append(f"### {ch_id}: {ch_title}{status_label}")

    direction = ch.get("direction")
    if direction:
        parts.append(f"**方向:** {direction}")
        parts.append("")

    beats = ch.get("beats", [])
    if beats:
        parts.append("**细纲:**")
        for beat in beats:
            if isinstance(beat, dict):
                parts.append(f"- {beat.get('description', beat.get('detail', str(beat)))}")
            else:
                parts.append(f"- {beat}")
        parts.append("")

    scenes = ch.get("scenePlans", [])
    if scenes:
        parts.append("**场景:**")
        for i, scene in enumerate(scenes, 1):
            summary = scene.get("summary", scene.get("title", ""))
            parts.append(f"{i}. {summary}")
        parts.append("")

    parts.append("---")
    parts.append("")


def _generate_spec_characters(state: dict) -> str:
    """Generate human-readable Markdown character cards."""
    title = state["project"].get("title", "未命名")
    parts = [f"# 角色卡: {title}", "", "---"]

    entities = state.get("entities", {}).get("entities", [])
    if not entities:
        parts.append("")
        parts.append("暂无角色数据。")
        return "\n".join(parts)

    # Build name lookup for resolving relation targets
    id_to_name = {}
    for ent in entities:
        eid = ent.get("id", "")
        ename = ent.get("name", "")
        if eid and ename:
            id_to_name[eid] = ename

    for ent in entities:
        name = ent.get("name", "未命名")
        etype = ent.get("type", "unknown")
        profile = ent.get("profile", {})
        is_inferred = ent.get("source") == "inferred" and not profile

        parts.append("")
        parts.append(f"## {name} ({etype})")

        if is_inferred:
            registered = ent.get("registeredAt", "")
            if registered:
                parts.append(f"> 推断实体，首次出现于 {registered}")
            parts.append("> 待补全角色信息")
            parts.append("")
            parts.append("---")
            continue

        registered = ent.get("registeredAt", "")
        if registered:
            parts.append(f"> 首次出场: {registered}")

        if isinstance(profile, dict):
            # Traits
            traits = profile.get("traits", [])
            if traits:
                parts.append(f"**特质:** {', '.join(traits)}")

            # Appearance
            appearance = profile.get("appearance", [])
            if appearance:
                app_strs = []
                for item in appearance:
                    if isinstance(item, dict):
                        app_strs.append(item.get("detail", str(item)))
                    else:
                        app_strs.append(str(item))
                parts.append(f"**外貌:** {', '.join(app_strs)}")

            # Abilities
            abilities = profile.get("abilities", [])
            if abilities:
                ab_strs = []
                for item in abilities:
                    if isinstance(item, dict):
                        ab_strs.append(item.get("detail", str(item)))
                    else:
                        ab_strs.append(str(item))
                parts.append(f"**能力:** {', '.join(ab_strs)}")

            # Background
            background = profile.get("background", "")
            if background:
                parts.append(f"**背景:** {background}")

            # Motivation
            motivation = profile.get("motivation", "")
            if motivation:
                parts.append(f"**动机:** {motivation}")

            # Arc
            arc = profile.get("arc", "")
            if arc:
                parts.append(f"**弧线:** {arc}")

        # Relations
        relations = ent.get("relations", [])
        if relations:
            parts.append("")
            parts.append("**关系:**")
            for rel in relations:
                target_id = rel.get("target", "")
                target_name = id_to_name.get(target_id, target_id)
                rel_type = rel.get("type", "")
                rel_detail = rel.get("detail", "")
                label = f"{rel_type}" if rel_type else "未知"
                if rel_detail:
                    parts.append(f"- {target_name}: {label} — {rel_detail}")
                else:
                    parts.append(f"- {target_name}: {label}")

        parts.append("")
        parts.append("---")

    return "\n".join(parts)


def _export_hierarchical_split(state: dict, args) -> int:
    """Export global outline, detail, and characters as separate files."""
    title = state["project"].get("title", "manuscript")

    if args.output:
        out_dir = Path(args.output)
    else:
        # Default to <project-root>/exports/
        out_dir = Path(args.root).resolve() / "exports"

    if out_dir.is_file():
        out_dir = out_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    files_written = []

    # 1. Global outline
    global_content = _generate_spec_global_outline(state)
    global_path = out_dir / f"{title}-global-outline.md"
    global_path.write_text(global_content, encoding="utf-8")
    files_written.append(global_path.name)

    # 2. Detailed outline
    detail_content = _generate_spec_detail(state)
    detail_path = out_dir / f"{title}-detail.md"
    detail_path.write_text(detail_content, encoding="utf-8")
    files_written.append(detail_path.name)

    # 3. Character cards
    chars_content = _generate_spec_characters(state)
    chars_path = out_dir / f"{title}-characters.md"
    chars_path.write_text(chars_content, encoding="utf-8")
    files_written.append(chars_path.name)

    for name in files_written:
        print(f"已导出: {out_dir / name}", file=sys.stderr)
    return 0


def _generate_spec_global_outline(state: dict) -> str:
    """Generate global outline only (volumes + chapter index, no details)."""
    title = state["project"].get("title", "未命名")
    parts = [f"# 全局大纲: {title}", ""]

    # Load direction from detailed_outlines if available
    direction_map = {}
    detailed = state.get("detailed_outlines", {})
    for entry in detailed.get("entries", []):
        cid = entry.get("chapterId", "")
        d = entry.get("direction", "")
        if cid and d:
            direction_map[cid] = d

    outline = state.get("outline", {})
    volumes = outline.get("volumes", [])

    if volumes:
        for vol in volumes:
            vol_title = vol.get("title", "未命名卷")
            vol_theme = vol.get("theme", "")
            parts.append(f"## 卷: {vol_title}")
            if vol_theme:
                parts.append(f"**主题:** {vol_theme}")
            parts.append("")
            for ch in vol.get("chapters", []):
                ch_id = ch.get("id", "unknown")
                ch_title = ch.get("title", "未命名")
                status = ch.get("status", "")
                status_label = f" [{status}]" if status else ""
                direction = direction_map.get(ch_id) or ch.get("direction", "")
                if direction:
                    # Truncate to first sentence or 80 chars for overview
                    short = direction.split("。")[0]
                    if len(short) > 80:
                        short = short[:77] + "..."
                    parts.append(f"- {ch_title}{status_label}: {short}")
                else:
                    parts.append(f"- {ch_title}{status_label}")
            parts.append("")
    else:
        for ch in outline.get("chapters", []):
            ch_id = ch.get("id", "unknown")
            ch_title = ch.get("title", "未命名")
            status = ch.get("status", "")
            status_label = f" [{status}]" if status else ""
            direction = direction_map.get(ch_id) or ch.get("direction", "")
            if direction:
                short = direction.split("。")[0]
                if len(short) > 80:
                    short = short[:77] + "..."
                parts.append(f"- {ch_title}{status_label}: {short}")
            else:
                parts.append(f"- {ch_title}{status_label}")
        parts.append("")

    return "\n".join(parts)


def _generate_spec_detail(state: dict) -> str:
    """Generate per-chapter detailed plans (direction + beats + scenePlans)."""
    title = state["project"].get("title", "未命名")
    parts = [f"# 细纲: {title}", ""]

    detailed = state.get("detailed_outlines", {})
    entry_map = {e.get("chapterId"): e for e in detailed.get("entries", [])}

    outline = state.get("outline", {})
    chapters = list(outline.get("chapters", []))
    for vol in outline.get("volumes", []):
        chapters.extend(vol.get("chapters", []))

    seen = set()
    has_any = False
    for ch in chapters:
        cid = ch.get("id")
        if not cid or cid in seen:
            continue
        seen.add(cid)

        entry = entry_map.get(cid)
        direction = (entry or {}).get("direction") or ch.get("direction", "")
        beats = (entry or {}).get("beats") or ch.get("beats", [])
        scenes = (entry or {}).get("scenePlans") or ch.get("scenePlans", [])

        if not direction and not beats and not scenes:
            continue

        has_any = True

        ch_title = ch.get("title", cid)
        parts.append(f"## {cid}: {ch_title}")
        parts.append("")

        if direction:
            parts.append(f"**方向:** {direction}")
            parts.append("")

        if beats:
            parts.append("**节拍:**")
            for beat in beats:
                summary = beat.get("summary", beat.get("description", str(beat)))
                beat_status = beat.get("status", "")
                label = f" [{beat_status}]" if beat_status else ""
                parts.append(f"- {summary}{label}")
            parts.append("")

        if scenes:
            parts.append("**场景:**")
            for i, scene in enumerate(scenes, 1):
                s_title = scene.get("title", "")
                s_summary = scene.get("summary", "")
                label = f"{s_title}: {s_summary}" if s_title else s_summary
                parts.append(f"{i}. {label}")
            parts.append("")

        parts.append("---")
        parts.append("")

    if not has_any:
        parts.append("暂无细纲数据。")

    return "\n".join(parts)


def _generate_spec_outline_hierarchical(state: dict) -> str:
    """Generate combined view: global outline then detailed plans."""
    parts = [_generate_spec_global_outline(state)]
    parts.append("")
    parts.append("")
    detail = _generate_spec_detail(state)
    # Replace the title to make it a section header
    detail_lines = detail.split("\n")
    if detail_lines and detail_lines[0].startswith("# "):
        detail_lines[0] = detail_lines[0].replace("# ", "## ", 1)
    parts.extend(detail_lines)
    return "\n".join(parts)


def _format_extension(fmt: str) -> str:
    """Return file extension for a given format."""
    return {
        "json": ".json",
        "markdown": ".md",
        "txt": ".txt",
        "spec-outline": ".md",
        "spec-characters": ".md",
        "spec-global-outline": ".md",
        "spec-detail": ".md",
        "spec-outline-hierarchical": ".md",
        "review-packet": ".md",
    }.get(fmt, ".txt")


def _write_stdout(output: str) -> None:
    """Write output string to stdout with UTF-8 encoding."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print(output)


def _find_chapter_file(root: Path, chapter_id: str) -> Path | None:
    direct = root / "chapters" / f"{chapter_id}.md"
    if direct.exists():
        return direct
    for item in (root / "chapters").glob("*.md"):
        if item.stem == chapter_id:
            return item
    return None


def _strip_chapter_heading(text: str, title: str) -> str:
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return ""

    first = lines[0].strip()
    heading_match = None
    if first.startswith("#"):
        heading_match = first.lstrip("#").strip()
    elif _looks_like_chapter_heading(first):
        heading_match = first

    if heading_match and _heading_matches_title(heading_match, title):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def _strip_export_boundary_headings(text: str, *, title: str, next_title: str) -> str:
    cleaned = _strip_chapter_heading(text, title)
    if not next_title:
        return cleaned

    lines = cleaned.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""

    last = lines[-1].strip()
    heading_match = None
    if last.startswith("#"):
        heading_match = last.lstrip("#").strip()
    elif _looks_like_chapter_heading(last):
        heading_match = last

    if heading_match and _heading_matches_title(heading_match, next_title):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    return "\n".join(lines).strip()


def _heading_matches_title(heading: str, title: str) -> bool:
    heading_norm = _normalize_heading_text(heading)
    title_norm = _normalize_heading_text(title)
    if heading_norm and title_norm and heading_norm == title_norm:
        return True
    if heading_norm and _looks_like_chapter_heading(heading):
        return True
    return False


def _normalize_heading_text(text: str) -> str:
    return "".join(text.strip().split())


def _looks_like_chapter_heading(text: str) -> bool:
    normalized = text.strip()
    return len(normalized) <= 40 and normalized.startswith("第") and "章" in normalized[:12]


def register_export_commands(subparsers) -> None:
    export_parser = subparsers.add_parser("export", help="Export clean manuscript text")
    export_parser.add_argument("--root", required=True)
    export_parser.add_argument("--chapter-id", help="Export single chapter (default: all)")
    export_parser.add_argument("--volume-id", help="Export only one volume")
    export_parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    export_parser.add_argument("--format", choices=["txt", "json", "markdown", "spec-outline", "spec-characters", "spec-global-outline", "spec-detail", "spec-outline-hierarchical", "review-packet"], default="txt", help="Output format")
    export_parser.set_defaults(func=command_export)
