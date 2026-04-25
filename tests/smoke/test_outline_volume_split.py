"""Tests for volume-level outline splitting in layered layout.

Task 3: In layered layout, each volume's chapter details are saved to
``spec/outlines/vol-NNN.yaml`` and ``spec/outline.yaml`` is kept as a thin
index.  On load, the chapters are re-assembled from the per-volume files.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.protocol.files import resolve_state_path
from story_harness_cli.protocol.schema import default_project_state
from story_harness_cli.protocol.state import STATE_KEY_MAP, load_project_state, save_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def _make_volume(vol_id: str, ch_count: int) -> dict:
    """Generate a volume dict with *ch_count* simple chapters."""
    chapters = [
        {"id": f"ch-{vol_id}-{i:03d}", "title": f"Chapter {i}", "status": "planned"}
        for i in range(1, ch_count + 1)
    ]
    return {"id": vol_id, "title": f"Volume {vol_id}", "chapters": chapters}


def _setup_layered_with_volumes(root: Path, volumes: list[dict]) -> None:
    """Create a full layered project directory with the given outline volumes."""
    (root / "spec" / "outlines").mkdir(parents=True, exist_ok=True)
    (root / "proposals").mkdir(parents=True, exist_ok=True)
    (root / "reviews").mkdir(parents=True, exist_ok=True)
    (root / "projections").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)

    sample_data = default_project_state()
    sample_data["project"].update({"title": "vol-split-test"})
    sample_data["outline"] = {"chapters": [], "chapterDirections": [], "volumes": volumes}

    for state_key, internal_key in STATE_KEY_MAP.items():
        fpath = resolve_state_path(root, state_key)
        _write_json_yaml(fpath, sample_data[internal_key])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class SaveWritesVolumeFilesTest(unittest.TestCase):
    """Saving a layered project with volumes writes per-volume files."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-volsplit-save-"))
        self.root = self.tmp / "project"
        volumes = [
            _make_volume("vol-001", 3),
            _make_volume("vol-002", 2),
        ]
        _setup_layered_with_volumes(self.root, volumes)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_writes_volume_files_in_layered(self):
        state = load_project_state(self.root)
        save_state(self.root, state)

        vol1_path = self.root / "spec" / "outlines" / "vol-001.yaml"
        vol2_path = self.root / "spec" / "outlines" / "vol-002.yaml"
        self.assertTrue(vol1_path.exists(), "vol-001.yaml should exist")
        self.assertTrue(vol2_path.exists(), "vol-002.yaml should exist")

        vol1_data = json.loads(vol1_path.read_text(encoding="utf-8"))
        vol2_data = json.loads(vol2_path.read_text(encoding="utf-8"))

        self.assertEqual(len(vol1_data["chapters"]), 3)
        self.assertEqual(len(vol2_data["chapters"]), 2)

        # Thin index: volumes have id + title but NO chapters
        idx_path = self.root / "spec" / "outline.yaml"
        idx_data = json.loads(idx_path.read_text(encoding="utf-8"))
        for vol in idx_data["volumes"]:
            self.assertIn("id", vol)
            self.assertIn("title", vol)
            self.assertNotIn("chapters", vol)


class LoadReadsVolumeFilesTest(unittest.TestCase):
    """Loading a layered project reads per-volume files and re-assembles."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-volsplit-load-"))
        self.root = self.tmp / "project"

        # Write thin index (no chapters in volumes)
        volumes = [
            {"id": "vol-001", "title": "Volume vol-001"},
            {"id": "vol-002", "title": "Volume vol-002"},
        ]
        _setup_layered_with_volumes(self.root, volumes)

        # Write per-volume files
        vol1_chapters = [
            {"id": "ch-vol-001-001", "title": "Chapter 1", "status": "planned"},
            {"id": "ch-vol-001-002", "title": "Chapter 2", "status": "planned"},
            {"id": "ch-vol-001-003", "title": "Chapter 3", "status": "planned"},
        ]
        vol2_chapters = [
            {"id": "ch-vol-002-001", "title": "Chapter 1", "status": "planned"},
            {"id": "ch-vol-002-002", "title": "Chapter 2", "status": "planned"},
        ]

        vol1_path = self.root / "spec" / "outlines" / "vol-001.yaml"
        vol2_path = self.root / "spec" / "outlines" / "vol-002.yaml"
        _write_json_yaml(vol1_path, {"chapters": vol1_chapters})
        _write_json_yaml(vol2_path, {"chapters": vol2_chapters})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_reads_volume_files_in_layered(self):
        state = load_project_state(self.root)

        # _sync_outline is called on save, not load. But the load should
        # have re-assembled the volume chapters so they are available.
        outline = state["outline"]
        volumes = outline.get("volumes", [])
        total_ch = sum(len(v.get("chapters", [])) for v in volumes)
        self.assertEqual(total_ch, 5, "Should have 5 chapters total across volumes")

    def test_load_then_save_flattens_correctly(self):
        state = load_project_state(self.root)
        save_state(self.root, state)

        # After save, _sync_outline should have flattened volumes → chapters
        reloaded = load_project_state(self.root)
        flat_chapters = reloaded["outline"].get("chapters", [])
        self.assertEqual(len(flat_chapters), 5, "Flat chapters array should have 5 entries")


class FlatLayoutNoVolumeFilesTest(unittest.TestCase):
    """Flat projects should NOT create spec/ or per-volume files."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-volsplit-flat-"))
        self.root = self.tmp / "project"
        # Flat layout: no spec/ dir
        self.root.mkdir(parents=True, exist_ok=True)

        volumes = [
            _make_volume("vol-001", 2),
            _make_volume("vol-002", 1),
        ]
        sample_data = default_project_state()
        sample_data["project"].update({"title": "flat-volsplit-test"})
        sample_data["outline"] = {"chapters": [], "chapterDirections": [], "volumes": volumes}
        for state_key, internal_key in STATE_KEY_MAP.items():
            fpath = resolve_state_path(self.root, state_key)
            _write_json_yaml(fpath, sample_data[internal_key])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_flat_layout_no_volume_files(self):
        state = load_project_state(self.root)
        save_state(self.root, state)

        # No spec/ directory should exist
        self.assertFalse(
            (self.root / "spec").exists(),
            "Flat layout should not create spec/ directory",
        )

        # No per-volume outline files
        self.assertFalse(
            (self.root / "spec" / "outlines").exists(),
            "Flat layout should not create spec/outlines/",
        )


if __name__ == "__main__":
    unittest.main()
