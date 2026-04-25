from __future__ import annotations

from pathlib import Path


ROOT_FILES = [
    "project.yaml",
    "outline.yaml",
    "entities.yaml",
    "timeline.yaml",
    "branches.yaml",
    "threads.yaml",
    "structures.yaml",
]


def root_file(root: Path, relative: str) -> Path:
    return root / relative


def chapter_path(root: Path, chapter_id: str) -> Path:
    direct = root / "chapters" / f"{chapter_id}.md"
    if direct.exists():
        return direct
    for item in (root / "chapters").glob("*.md"):
        if item.stem == chapter_id:
            return item
    return direct


# ---------------------------------------------------------------------------
# Layout detection & layered path resolution
# ---------------------------------------------------------------------------

LAYOUT_FLAT = "flat"
LAYOUT_LAYERED = "layered"

_SPEC_KEYS = {"outline", "entities", "timeline", "threads", "structures", "foreshadowing", "detailed_outlines"}

_SUBDIR_KEYS = {
    "proposals": "proposals/draft-proposals.yaml",
    "reviews": "reviews/change-requests.yaml",
    "story_reviews": "reviews/story-reviews.yaml",
    "projection": "projections/projection.yaml",
    "context_lens": "projections/context-lens.yaml",
    "projection_log": "logs/projection-log.yaml",
}


def detect_layout(root: Path) -> str:
    """Return ``LAYOUT_LAYERED`` if *root*/spec is a directory, else ``LAYOUT_FLAT``."""
    return LAYOUT_LAYERED if (root / "spec").is_dir() else LAYOUT_FLAT


def resolve_state_path(
    root: Path,
    state_key: str,
    *,
    layout: str | None = None,
    volume_id: str | None = None,
    entity_slug: str | None = None,
) -> Path:
    """Resolve the filesystem path for *state_key* honouring the project layout.

    Parameters
    ----------
    root:
        Project root directory.
    state_key:
        Logical key identifying the state file (e.g. ``"outline"``, ``"entities"``).
    layout:
        ``LAYOUT_FLAT`` or ``LAYOUT_LAYERED``.  When *None*, auto-detected via
        :func:`detect_layout`.
    volume_id:
        Volume identifier used only when *state_key* is ``"outline_volume"``.
    entity_slug:
        Entity slug used only when *state_key* is ``"entity_detail"``.
    """
    if layout is None:
        layout = detect_layout(root)

    # -- always-at-root keys --------------------------------------------------
    if state_key == "project":
        return root / "project.yaml"

    if state_key == "workflow_progress":
        return root / "workflow.yaml"

    if state_key == "illustrations":
        return root / "illustrations.yaml"

    if state_key == "chapters":
        return root / "chapters"

    # -- subdir-resident keys (identical for both layouts) --------------------
    if state_key in _SUBDIR_KEYS:
        return root / _SUBDIR_KEYS[state_key]

    # -- outline_volume (layered only) ---------------------------------------
    if state_key == "outline_volume":
        if layout == LAYOUT_LAYERED and volume_id is not None:
            return root / "spec" / "outlines" / f"{volume_id}.yaml"
        return resolve_state_path(root, "outline", layout=layout)

    # -- entity_detail (layered only) ----------------------------------------
    if state_key == "entity_detail":
        if layout == LAYOUT_LAYERED and entity_slug is not None:
            return root / "spec" / "entities" / f"{entity_slug}.yaml"
        return resolve_state_path(root, "entities", layout=layout)

    # -- spec-eligible keys ---------------------------------------------------
    if state_key in _SPEC_KEYS:
        if layout == LAYOUT_LAYERED:
            return root / "spec" / f"{state_key}.yaml"
        return root / f"{state_key}.yaml"

    # -- fallback -------------------------------------------------------------
    return root / f"{state_key}.yaml"
