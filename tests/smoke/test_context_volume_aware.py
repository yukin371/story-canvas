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
from story_harness_cli.protocol.state import STATE_KEY_MAP, load_outline_for_chapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_minimal_state_files(root: Path) -> None:
    """Write minimal valid state files for every key in STATE_KEY_MAP."""
    sample_data = default_project_state()
    sample_data["project"].update({"title": "volume-aware-test"})
    sample_data["outline"] = {"chapters": [], "chapterDirections": [], "volumes": []}
    for state_key, internal_key in STATE_KEY_MAP.items():
        fpath = resolve_state_path(root, state_key)
        _write_json_yaml(fpath, sample_data[internal_key])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class LoadOutlineForChapterTest(unittest.TestCase):
    """load_outline_for_chapter returns only the relevant volume's chapters."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-volume-aware-"))
        self.root = self.tmp / "project"
        # Create layered layout: spec/ dir present
        (self.root / "spec").mkdir(parents=True)
        _build_minimal_state_files(self.root)

        # Write outline index with 2 thin volumes
        outline_index = {
            "chapters": [],
            "chapterDirections": [],
            "volumes": [
                {"id": "vol-001", "title": "Volume 1"},
                {"id": "vol-002", "title": "Volume 2"},
            ],
        }
        index_path = resolve_state_path(self.root, "outline")
        _write_json_yaml(index_path, outline_index)

        # Write per-volume files
        vol_001_path = resolve_state_path(
            self.root, "outline_volume", volume_id="vol-001", layout="layered"
        )
        _write_json_yaml(vol_001_path, {
            "chapters": [
                {"id": "chapter-001", "title": "Chapter 1", "status": "completed"},
                {"id": "chapter-002", "title": "Chapter 2", "status": "in_progress",
                 "direction": "The hero enters the forest"},
            ],
        })

        vol_002_path = resolve_state_path(
            self.root, "outline_volume", volume_id="vol-002", layout="layered"
        )
        _write_json_yaml(vol_002_path, {
            "chapters": [
                {"id": "chapter-003", "title": "Chapter 3", "status": "planned"},
            ],
        })

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_outline_for_chapter_returns_only_relevant_volume(self):
        result = load_outline_for_chapter(self.root, "chapter-002")

        # Should return only the 2 chapters from vol-001, not the 3 total
        self.assertEqual(len(result["chapters"]), 2)
        self.assertEqual(result["chapters"][0]["id"], "chapter-001")
        self.assertEqual(result["chapters"][1]["id"], "chapter-002")

        # Should include chapterDirections for chapters with direction
        self.assertEqual(len(result["chapterDirections"]), 1)
        self.assertEqual(result["chapterDirections"][0]["chapterId"], "chapter-002")

        # Should identify the active volume
        self.assertEqual(result["activeVolumeId"], "vol-001")

        # Should include only the one volume in volumes list
        self.assertEqual(len(result["volumes"]), 1)
        self.assertEqual(result["volumes"][0]["id"], "vol-001")


if __name__ == "__main__":
    unittest.main()
