from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

from .files import LAYOUT_FLAT, LAYOUT_LAYERED, ROOT_FILES, detect_layout, resolve_state_path, root_file
from .io import dump_json_compatible_yaml, load_json_compatible_yaml
from .schema import default_project_state

STATE_FILE_NAMES = (
    "project.yaml",
    "outline.yaml",
    "entities.yaml",
    "timeline.yaml",
    "branches.yaml",
    "proposals/draft-proposals.yaml",
    "reviews/change-requests.yaml",
    "reviews/story-reviews.yaml",
    "projections/projection.yaml",
    "projections/context-lens.yaml",
    "logs/projection-log.yaml",
    "workflow.yaml",
    "illustrations.yaml",
    "threads.yaml",
    "structures.yaml",
    "worldbook.yaml",
    "foreshadowing.yaml",
    "detailed_outlines.yaml",
)

# Ordered mapping from state_key (used with resolve_state_path) to the
# internal dict key inside the state dict returned by load_project_state().
STATE_KEY_MAP = {
    "project": "project",
    "outline": "outline",
    "entities": "entities",
    "timeline": "timeline",
    "branches": "branches",
    "proposals": "proposals",
    "reviews": "reviews",
    "story_reviews": "story_reviews",
    "projection": "projection",
    "context_lens": "context_lens",
    "projection_log": "projection_log",
    "workflow_progress": "workflow_progress",
    "illustrations": "illustrations",
    "threads": "threads",
    "structures": "structures",
    "worldbook": "worldbook",
    "foreshadowing": "foreshadowing",
    "detailed_outlines": "detailed_outlines",
}
STATE_META_KEY = "_stateMeta"
STATE_LOCK_FILENAME = ".story-harness.lock"
STATE_LOCK_TIMEOUT_SECONDS = 10.0
STATE_LOCK_POLL_INTERVAL_SECONDS = 0.05


def load_project_state(root: Path) -> Dict[str, Any]:
    defaults = default_project_state()
    state: Dict[str, Any] = {}
    for state_key, internal_key in STATE_KEY_MAP.items():
        fpath = resolve_state_path(root, state_key)
        raw = load_json_compatible_yaml(fpath, defaults[internal_key])
        if state_key in ("project", "story_reviews", "workflow_progress", "illustrations", "worldbook"):
            state[internal_key] = merge_defaults(raw, defaults[internal_key])
        else:
            state[internal_key] = raw

    # In layered layout, volumes may be stored in per-volume files.
    layout = detect_layout(root)
    if layout == LAYOUT_LAYERED:
        outline = state["outline"]
        volumes = outline.get("volumes")
        if volumes and not any(v.get("chapters") for v in volumes):
            state["outline"] = _load_outline_layered(root, outline)

    # Merge detailed outlines into outline chapters for transparent access.
    _merge_detailed_into_outline(state["outline"], state.get("detailed_outlines", {"entries": []}))

    state[STATE_META_KEY] = _build_state_meta(root)
    return state


def _merge_detailed_into_outline(outline: Dict[str, Any], detailed_outlines: Dict[str, Any]) -> None:
    entries = detailed_outlines.get("entries", [])
    if not entries:
        return
    lookup: Dict[str, dict] = {e.get("chapterId"): e for e in entries if e.get("chapterId")}

    for ch in outline.get("chapters", []):
        _apply_detailed_entry(ch, lookup.get(ch.get("id")))
    for vol in outline.get("volumes", []):
        for ch in vol.get("chapters", []):
            _apply_detailed_entry(ch, lookup.get(ch.get("id")))


def _apply_detailed_entry(chapter: Dict[str, Any], entry: dict | None) -> None:
    if entry is None:
        return
    for field in ("direction", "beats", "scenePlans"):
        val = entry.get(field)
        if val is not None:
            chapter[field] = val


def _extract_to_detailed(outline: Dict[str, Any], detailed_outlines: Dict[str, Any]) -> None:
    """Copy direction/beats/scenePlans from outline chapters into detailed_outlines entries."""
    entries = detailed_outlines.setdefault("entries", [])
    existing: Dict[str, dict] = {e.get("chapterId"): e for e in entries if e.get("chapterId")}

    all_chapters = list(outline.get("chapters", []))
    for vol in outline.get("volumes", []):
        all_chapters.extend(vol.get("chapters", []))

    for ch in all_chapters:
        cid = ch.get("id")
        if not cid:
            continue
        has_detail = any(ch.get(f) for f in ("direction", "beats", "scenePlans"))
        if not has_detail:
            continue
        entry = existing.get(cid)
        if entry is None:
            entry = {"chapterId": cid}
            entries.append(entry)
            existing[cid] = entry
        for field in ("direction", "beats", "scenePlans"):
            val = ch.get(field)
            if val is not None:
                entry[field] = val
        entry["updatedAt"] = _now_iso_compat()


def _now_iso_compat() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def save_state(root: Path, state: Dict[str, Any], *, timeout_seconds: float = STATE_LOCK_TIMEOUT_SECONDS) -> None:
    with _project_write_lock(root, timeout_seconds=timeout_seconds):
        _ensure_state_not_stale(root, state)
        # Sync volumes → flat chapters/chapterDirections before saving
        _sync_outline(state["outline"])

        # Extract detailed fields into detailed_outlines storage (keeps outline.yaml backward-compatible).
        _extract_to_detailed(state["outline"], state.setdefault("detailed_outlines", {"entries": []}))

        for state_key, internal_key in STATE_KEY_MAP.items():
            fpath = resolve_state_path(root, state_key)
            dump_json_compatible_yaml(fpath, state[internal_key])

        # In layered layout, split volume chapters into per-volume files.
        layout = detect_layout(root)
        if layout == LAYOUT_LAYERED:
            volumes = state["outline"].get("volumes")
            if volumes and any(v.get("chapters") for v in volumes):
                _save_outline_layered(root, state["outline"])

        state[STATE_META_KEY] = _build_state_meta(root)


def ensure_project_root(root: Path) -> None:
    # project.yaml and branches.yaml always at root; spec-eligible keys use resolve_state_path
    always_root = ["project.yaml", "branches.yaml"]
    missing = [name for name in always_root if not (root / name).exists()]
    spec_keys = ["outline", "entities", "timeline", "threads", "structures"]
    for key in spec_keys:
        if not resolve_state_path(root, key).exists():
            missing.append(f"{key}.yaml")
    if missing:
        raise SystemExit(f"{root} 不是已初始化的 story harness 项目，缺少: {', '.join(missing)}")


def load_outline_for_chapter(root: Path, chapter_id: str) -> dict:
    """Load only the outline volume containing the given chapter.

    In flat layout, returns the full outline.
    In layered layout, returns only the relevant volume's chapters.
    """
    layout = detect_layout(root)
    if layout == LAYOUT_FLAT:
        state = load_project_state(root)
        return state["outline"]

    # Layered: read index, find volume containing chapter, load only that volume
    index_path = resolve_state_path(root, "outline", layout=LAYOUT_LAYERED)
    if not index_path.exists():
        return {"chapters": [], "chapterDirections": [], "volumes": []}

    index = _load_yaml(index_path)
    for vol in index.get("volumes", []):
        vol_id = vol.get("id")
        if not vol_id:
            continue
        vol_path = resolve_state_path(
            root, "outline_volume", volume_id=vol_id, layout=LAYOUT_LAYERED
        )
        if not vol_path.exists():
            continue
        vol_data = _load_yaml(vol_path)
        for ch in vol_data.get("chapters", []):
            if ch.get("id") == chapter_id:
                return {
                    "chapters": vol_data.get("chapters", []),
                    "chapterDirections": [
                        {"chapterId": c["id"], "title": c.get("title", ""),
                         "summary": c.get("direction", "")}
                        for c in vol_data.get("chapters", [])
                        if c.get("direction")
                    ],
                    "volumes": [vol],
                    "activeVolumeId": vol_id,
                }

    # Fallback: chapter not found in any volume, return full outline
    state = load_project_state(root)
    return state["outline"]


def merge_defaults(payload: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for key, default_value in defaults.items():
        current_value = payload.get(key)
        if isinstance(default_value, dict):
            merged[key] = merge_defaults(current_value if isinstance(current_value, dict) else {}, default_value)
        elif current_value is None:
            merged[key] = default_value
        else:
            merged[key] = current_value
    for key, value in payload.items():
        if key not in merged:
            merged[key] = value
    return merged


# ---------------------------------------------------------------------------
# Volume-level outline splitting (layered layout)
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    """Read a JSON-compatible YAML file and return its contents as a dict."""
    raw = path.read_text(encoding="utf-8").strip()
    return json.loads(raw) if raw else {}


def _save_outline_layered(root: Path, outline: Dict[str, Any]) -> None:
    """Split volume chapters into per-volume files under spec/outlines/."""
    volumes = outline.get("volumes")
    if not volumes:
        return

    for vol in volumes:
        vol_id = vol.get("id")
        if not vol_id:
            continue
        chapters = vol.get("chapters", [])
        vol_path = resolve_state_path(
            root, "outline_volume", volume_id=vol_id, layout=LAYOUT_LAYERED,
        )
        vol_path.parent.mkdir(parents=True, exist_ok=True)
        dump_json_compatible_yaml(vol_path, {"chapters": chapters})

    # Overwrite the index with thin volumes (id + title only, no chapters).
    thin_volumes = [
        {"id": v.get("id"), "title": v.get("title", "")}
        for v in volumes
    ]
    thin_outline = {k: v for k, v in outline.items() if k != "volumes"}
    thin_outline["volumes"] = thin_volumes
    idx_path = resolve_state_path(root, "outline", layout=LAYOUT_LAYERED)
    dump_json_compatible_yaml(idx_path, thin_outline)


def _load_outline_layered(root: Path, outline: Dict[str, Any]) -> Dict[str, Any]:
    """Re-assemble outline by merging per-volume chapter files into the index."""
    volumes = outline.get("volumes")
    if not volumes:
        return outline

    for vol in volumes:
        vol_id = vol.get("id")
        if not vol_id:
            continue
        vol_path = resolve_state_path(
            root, "outline_volume", volume_id=vol_id, layout=LAYOUT_LAYERED,
        )
        if vol_path.exists():
            vol_data = _load_yaml(vol_path)
            vol["chapters"] = vol_data.get("chapters", [])

    return outline


def _sync_outline(outline: Dict[str, Any]) -> None:
    volumes = outline.get("volumes")
    if not volumes:
        return
    flat_chapters = []
    flat_directions = []
    for vol in volumes:
        for ch in vol.get("chapters", []):
            flat_entry = {
                "id": ch.get("id"),
                "title": ch.get("title"),
                "status": ch.get("status", "planned"),
                "beats": ch.get("beats", []),
                "scenePlans": ch.get("scenePlans", []),
            }
            flat_chapters.append(flat_entry)
            if ch.get("direction"):
                flat_directions.append({
                    "chapterId": ch.get("id"),
                    "title": ch.get("title"),
                    "summary": ch.get("direction", ""),
                })
    outline["chapters"] = flat_chapters
    outline["chapterDirections"] = flat_directions


def _build_state_meta(root: Path) -> Dict[str, str]:
    return {
        state_key: _fingerprint_path(resolve_state_path(root, state_key))
        for state_key in STATE_KEY_MAP
    }


def _fingerprint_path(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha1(path.read_bytes()).hexdigest()


def _ensure_state_not_stale(root: Path, state: Dict[str, Any]) -> None:
    expected_meta = state.get(STATE_META_KEY)
    if not isinstance(expected_meta, dict) or not expected_meta:
        return
    current_meta = _build_state_meta(root)
    changed_files = [
        state_key for state_key in STATE_KEY_MAP
        if current_meta.get(state_key) != expected_meta.get(state_key)
    ]
    if changed_files:
        changed = "，".join(changed_files)
        raise SystemExit(f"项目状态已被其他命令更新，请重新执行当前命令以避免覆盖：{changed}")


@contextmanager
def _project_write_lock(root: Path, *, timeout_seconds: float = STATE_LOCK_TIMEOUT_SECONDS):
    lock_path = root / STATE_LOCK_FILENAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    try:
        if lock_path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + max(timeout_seconds, 0.0)
        while True:
            try:
                _try_acquire_file_lock(handle)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise SystemExit(f"项目状态正被其他命令写入，请稍后重试：{root}")
                time.sleep(STATE_LOCK_POLL_INTERVAL_SECONDS)
        yield
    finally:
        try:
            _release_file_lock(handle)
        except OSError:
            pass
        handle.close()


def _try_acquire_file_lock(handle) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise BlockingIOError from exc
        return

    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        raise BlockingIOError from exc


def _release_file_lock(handle) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
