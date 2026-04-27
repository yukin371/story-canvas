from __future__ import annotations

import json
import sys
import re
from pathlib import Path

from story_harness_cli.commands.review_support import build_foreshadow_check_payload
from story_harness_cli.protocol import ensure_project_root, load_project_state
from story_harness_cli.protocol.files import resolve_state_path


def _load_foreshadows(root: Path) -> list:
    path = resolve_state_path(root, "foreshadowing")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8").strip() or "{}")
    return data.get("foreshadows", [])


def _save_foreshadows(root: Path, foreshadows: list) -> None:
    path = resolve_state_path(root, "foreshadowing")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"foreshadows": foreshadows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _next_id(foreshadows: list) -> str:
    max_num = 0
    for fs in foreshadows:
        fs_id = fs.get("id", "fs-000")
        try:
            num = int(fs_id.split("-")[1])
            max_num = max(max_num, num)
        except (ValueError, IndexError):
            pass
    return f"fs-{max_num + 1:03d}"


def _chapter_number(chapter_ref: str) -> int | None:
    match = re.search(r"(\d+)(?!.*\d)", chapter_ref or "")
    if not match:
        return None
    return int(match.group(1))


def _chapter_in_window(chapter_id: str, window: dict) -> bool:
    if not isinstance(window, dict):
        return False
    target_chapter = window.get("targetChapter")
    if target_chapter:
        return target_chapter == chapter_id

    start = window.get("targetChapterStart")
    end = window.get("targetChapterEnd")
    if not start and not end:
        return False

    current_num = _chapter_number(chapter_id)
    start_num = _chapter_number(start) if start else None
    end_num = _chapter_number(end) if end else None
    if current_num is not None and (start_num is not None or end_num is not None):
        if start_num is not None and current_num < start_num:
            return False
        if end_num is not None and current_num > end_num:
            return False
        return True

    if start and chapter_id < start:
        return False
    if end and chapter_id > end:
        return False
    return True


def _chapter_after(target: str, chapter_id: str) -> bool:
    target_num = _chapter_number(target)
    current_num = _chapter_number(chapter_id)
    if target_num is not None and current_num is not None:
        return current_num > target_num
    return chapter_id > target


def _window_ended_before_chapter(window: dict, chapter_id: str) -> bool:
    if not isinstance(window, dict):
        return False
    target_chapter = window.get("targetChapter")
    if target_chapter:
        return _chapter_after(target_chapter, chapter_id)
    end = window.get("targetChapterEnd")
    if end:
        return _chapter_after(end, chapter_id)
    return False


def _foreshadow_title(item: dict) -> str:
    return str(item.get("title") or item.get("description") or item.get("id") or "").strip()


def _foreshadow_due_in_chapter(item: dict, chapter_id: str) -> bool:
    if item.get("status") == "resolved":
        return False
    if item.get("plannedPayoffChapter") == chapter_id:
        return True
    for payoff_point in item.get("payoffPoints", []):
        if payoff_point.get("chapterId") == chapter_id:
            return True
    payoff_plan = item.get("payoffPlan", {})
    if not isinstance(payoff_plan, dict):
        return False
    return _chapter_in_window(chapter_id, payoff_plan.get("window", {}))


def _foreshadow_overdue_for_chapter(item: dict, chapter_id: str) -> bool:
    if item.get("status") == "resolved":
        return False
    planned_payoff = item.get("plannedPayoffChapter")
    if isinstance(planned_payoff, str) and planned_payoff and _chapter_after(planned_payoff, chapter_id):
        return True
    payoff_plan = item.get("payoffPlan", {})
    if isinstance(payoff_plan, dict) and _window_ended_before_chapter(payoff_plan.get("window", {}), chapter_id):
        return True
    return False


def _foreshadow_schedule_summary(item: dict) -> dict:
    payoff_plan = item.get("payoffPlan", {}) if isinstance(item.get("payoffPlan", {}), dict) else {}
    window = payoff_plan.get("window", {}) if isinstance(payoff_plan, dict) else {}
    return {
        "plannedPayoffChapter": item.get("plannedPayoffChapter"),
        "window": window,
        "payoffPointCount": len(item.get("payoffPoints", [])),
    }


def _compact_foreshadow(item: dict) -> dict:
    return {
        "id": item.get("id", ""),
        "title": _foreshadow_title(item),
        "status": item.get("status", ""),
        "plantedChapter": item.get("plantedChapter") or (
            item.get("plantPoints", [{}])[0].get("chapterId") if item.get("plantPoints") else ""
        ),
        "schedule": _foreshadow_schedule_summary(item),
    }


def run_plant(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    foreshadows = _load_foreshadows(root)
    entry = {
        "id": _next_id(foreshadows),
        "description": args.description,
        "plantedChapter": args.chapter_id,
        "plantedScene": getattr(args, "scene_index", None),
        "plannedPayoffChapter": getattr(args, "planned_payoff", None),
        "actualPayoffChapter": None,
        "status": "planted",
        "notes": getattr(args, "notes", ""),
    }
    foreshadows.append(entry)
    _save_foreshadows(root, foreshadows)
    print(f"Planted foreshadow {entry['id']}: {entry['description']}")
    return 0


def run_resolve(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    foreshadows = _load_foreshadows(root)
    found = False
    for fs in foreshadows:
        if fs.get("id") == args.foreshadow_id:
            fs["status"] = "resolved"
            fs["actualPayoffChapter"] = getattr(args, "payoff_chapter", None)
            found = True
            break
    if not found:
        print(f"Foreshadow {args.foreshadow_id} not found.", file=sys.stderr)
        return 1
    _save_foreshadows(root, foreshadows)
    print(f"Resolved foreshadow {args.foreshadow_id}")
    return 0


def run_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    foreshadows = _load_foreshadows(root)
    status_filter = getattr(args, "status", None)
    if status_filter:
        foreshadows = [fs for fs in foreshadows if fs.get("status") == status_filter]
    if not foreshadows:
        print("No foreshadows found.")
        return 0
    for fs in foreshadows:
        status_mark = "Y" if fs.get("status") == "resolved" else "o"
        payoff = fs.get("actualPayoffChapter") or fs.get("plannedPayoffChapter") or "?"
        print(
            f"  {status_mark} {fs['id']}: {fs.get('description', '')} "
            f"(planted: {fs.get('plantedChapter', '?')}, payoff: {payoff})"
        )
    return 0


def run_check(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    chapter_id = args.chapter_id or state.get("project", {}).get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    payload = build_foreshadow_check_payload(state, chapter_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def register_foreshadow_commands(subparsers) -> None:
    foreshadow_parser = subparsers.add_parser("foreshadow", help="Foreshadow tracking")
    foreshadow_sub = foreshadow_parser.add_subparsers(dest="foreshadow_action")

    plant = foreshadow_sub.add_parser("plant", help="Plant a foreshadow")
    plant.add_argument("--root", required=True)
    plant.add_argument("--description", required=True)
    plant.add_argument("--chapter-id", required=True)
    plant.add_argument("--scene-index", type=int, default=None)
    plant.add_argument("--planned-payoff", default=None)
    plant.add_argument("--notes", default="")
    plant.set_defaults(func=run_plant)

    resolve = foreshadow_sub.add_parser("resolve", help="Resolve a foreshadow")
    resolve.add_argument("--root", required=True)
    resolve.add_argument("--foreshadow-id", required=True)
    resolve.add_argument("--payoff-chapter", default=None)
    resolve.set_defaults(func=run_resolve)

    list_cmd = foreshadow_sub.add_parser("list", help="List foreshadows")
    list_cmd.add_argument("--root", required=True)
    list_cmd.add_argument("--status", choices=["planted", "resolved"], default=None)
    list_cmd.set_defaults(func=run_list)

    check_cmd = foreshadow_sub.add_parser(
        "check",
        help="Check due, overdue, and unscheduled unresolved foreshadows for a chapter",
    )
    check_cmd.add_argument("--root", required=True)
    check_cmd.add_argument("--chapter-id")
    check_cmd.set_defaults(func=run_check)
