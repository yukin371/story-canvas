"""Tests for outline hierarchy (detailed outlines) feature."""
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

from story_harness_cli.cli import main
from story_harness_cli.protocol.files import resolve_state_path
from story_harness_cli.protocol.schema import default_project_state
from story_harness_cli.protocol.state import STATE_KEY_MAP, load_project_state, save_state


def _write_json_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_project(root: Path, *, layered: bool = False, outline: dict | None = None) -> None:
    if layered:
        (root / "spec").mkdir(parents=True, exist_ok=True)
    (root / "chapters").mkdir(parents=True, exist_ok=True)
    (root / "proposals").mkdir(parents=True, exist_ok=True)
    (root / "reviews").mkdir(parents=True, exist_ok=True)
    (root / "projections").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)

    sample_data = default_project_state()
    sample_data["project"].update({"title": "detail-test", "genre": "fantasy"})
    sample_data["outline"] = outline or {"chapters": [], "chapterDirections": [], "volumes": []}
    for state_key, internal_key in STATE_KEY_MAP.items():
        fpath = resolve_state_path(root, state_key)
        _write_json_yaml(fpath, sample_data[internal_key])


class ExtractMergeRoundtripTest(unittest.TestCase):
    """Save extracts detailed fields, reload merges them back."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-detail-roundtrip-"))
        self.root = self.tmp / "project"
        outline = {
            "chapters": [
                {
                    "id": "chapter-001",
                    "title": "Test Chapter",
                    "status": "planned",
                    "direction": "Go north",
                    "beats": [{"id": "beat-1", "summary": "Beat one", "status": "planned"}],
                    "scenePlans": [{"id": "scene-1", "title": "Scene one", "summary": "Test"}],
                }
            ],
            "chapterDirections": [],
            "volumes": [],
        }
        _build_project(self.root, outline=outline)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_extract_merge_roundtrip(self):
        state = load_project_state(self.root)
        ch = state["outline"]["chapters"][0]
        self.assertEqual(ch["direction"], "Go north")
        self.assertEqual(len(ch["beats"]), 1)
        self.assertEqual(len(ch["scenePlans"]), 1)

        save_state(self.root, state)

        # Verify detailed_outlines.yaml was created
        detailed_path = self.root / "detailed_outlines.yaml"
        self.assertTrue(detailed_path.exists())
        detailed = json.loads(detailed_path.read_text(encoding="utf-8"))
        self.assertEqual(len(detailed["entries"]), 1)
        self.assertEqual(detailed["entries"][0]["chapterId"], "chapter-001")
        self.assertEqual(detailed["entries"][0]["direction"], "Go north")

        # Reload and verify merge
        reloaded = load_project_state(self.root)
        ch_reloaded = reloaded["outline"]["chapters"][0]
        self.assertEqual(ch_reloaded["direction"], "Go north")
        self.assertEqual(len(ch_reloaded["beats"]), 1)
        self.assertEqual(ch_reloaded["beats"][0]["summary"], "Beat one")
        self.assertEqual(len(ch_reloaded["scenePlans"]), 1)


class BackwardCompatNoDetailedFileTest(unittest.TestCase):
    """Projects without detailed_outlines.yaml still work."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-detail-backcompat-"))
        self.root = self.tmp / "project"
        _build_project(self.root)
        # Delete detailed_outlines.yaml to simulate old project
        detailed_path = self.root / "detailed_outlines.yaml"
        if detailed_path.exists():
            detailed_path.unlink()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_backward_compat_no_detailed_file(self):
        state = load_project_state(self.root)
        self.assertIn("detailed_outlines", state)
        self.assertEqual(state["detailed_outlines"]["entries"], [])


class AutoExtractOnSaveTest(unittest.TestCase):
    """First save of an old project auto-extracts detailed fields."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-detail-autoextract-"))
        self.root = self.tmp / "project"
        outline = {
            "chapters": [
                {
                    "id": "chapter-001",
                    "title": "Auto",
                    "status": "planned",
                    "direction": "Auto direction",
                    "beats": [{"id": "beat-1", "summary": "Auto beat"}],
                    "scenePlans": [],
                }
            ],
            "chapterDirections": [],
            "volumes": [],
        }
        _build_project(self.root, outline=outline)
        # Remove detailed_outlines.yaml to simulate old project
        detailed_path = self.root / "detailed_outlines.yaml"
        if detailed_path.exists():
            detailed_path.unlink()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_auto_extract_on_save(self):
        state = load_project_state(self.root)
        # Beats should be accessible through merged outline
        self.assertEqual(state["outline"]["chapters"][0]["direction"], "Auto direction")

        save_state(self.root, state)

        # Verify detailed_outlines.yaml was created
        detailed_path = self.root / "detailed_outlines.yaml"
        self.assertTrue(detailed_path.exists())
        detailed = json.loads(detailed_path.read_text(encoding="utf-8"))
        self.assertEqual(len(detailed["entries"]), 1)
        self.assertEqual(detailed["entries"][0]["direction"], "Auto direction")
        self.assertEqual(len(detailed["entries"][0]["beats"]), 1)


class DetailInitShowTest(unittest.TestCase):
    """outline detail-init and detail-show CLI commands."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-detail-cli-"))
        self.root = self.tmp / "project"
        outline = {
            "chapters": [
                {"id": "chapter-001", "title": "CLI Test", "status": "planned"},
            ],
            "chapterDirections": [],
            "volumes": [],
        }
        _build_project(self.root, outline=outline)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_detail_init_and_show(self):
        root_str = str(self.root)
        # Initialize detailed outline with direction
        self.assertEqual(
            main(["outline", "detail-init", "--root", root_str, "--chapter-id", "chapter-001", "--direction", "Go west"]), 0
        )

        # Show detailed outline
        self.assertEqual(main(["outline", "detail-show", "--root", root_str, "--chapter-id", "chapter-001"]), 0)

        # Verify in state
        state = load_project_state(self.root)
        ch = state["outline"]["chapters"][0]
        self.assertEqual(ch["direction"], "Go west")

        # Verify in detailed_outlines
        self.assertEqual(len(state["detailed_outlines"]["entries"]), 1)
        self.assertEqual(state["detailed_outlines"]["entries"][0]["direction"], "Go west")


class BeatSceneWorkWithSplitTest(unittest.TestCase):
    """beat-add and scene-add still work correctly with the split storage."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-detail-beatscene-"))
        self.root = self.tmp / "project"
        outline = {
            "chapters": [
                {"id": "chapter-001", "title": "Beat Test", "status": "planned"},
            ],
            "chapterDirections": [],
            "volumes": [],
        }
        _build_project(self.root, outline=outline)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_beat_and_scene_commands_work(self):
        root_str = str(self.root)
        # Add a beat
        self.assertEqual(
            main(["outline", "beat-add", "--root", root_str, "--chapter-id", "chapter-001", "--summary", "Test beat"]), 0
        )

        # Verify beat is in merged outline
        state = load_project_state(self.root)
        self.assertEqual(len(state["outline"]["chapters"][0]["beats"]), 1)

        # Verify beat was extracted to detailed_outlines
        self.assertEqual(len(state["detailed_outlines"]["entries"]), 1)
        self.assertEqual(len(state["detailed_outlines"]["entries"][0]["beats"]), 1)

        # List beats still works
        self.assertEqual(
            main(["outline", "beat-list", "--root", root_str, "--chapter-id", "chapter-001"]), 0
        )


class LayeredDetailedOutlinesTest(unittest.TestCase):
    """Detailed outlines work in layered layout."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-detail-layered-"))
        self.root = self.tmp / "project"
        outline = {
            "chapters": [],
            "chapterDirections": [],
            "volumes": [
                {
                    "id": "vol-001",
                    "title": "Volume 1",
                    "chapters": [
                        {
                            "id": "chapter-001",
                            "title": "Layered Test",
                            "status": "planned",
                            "direction": "Layered direction",
                            "beats": [{"id": "beat-1", "summary": "Layered beat"}],
                            "scenePlans": [],
                        }
                    ],
                }
            ],
        }
        _build_project(self.root, layered=True, outline=outline)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_layered_detailed_outlines(self):
        state = load_project_state(self.root)
        # Access chapter through volumes (flat chapters not yet synced on load)
        vol_ch = state["outline"]["volumes"][0]["chapters"][0]
        self.assertEqual(vol_ch["direction"], "Layered direction")
        self.assertEqual(len(vol_ch["beats"]), 1)

        save_state(self.root, state)

        # Verify detailed_outlines.yaml is in spec/
        detailed_path = self.root / "spec" / "detailed_outlines.yaml"
        self.assertTrue(detailed_path.exists())
        detailed = json.loads(detailed_path.read_text(encoding="utf-8"))
        self.assertEqual(len(detailed["entries"]), 1)
        self.assertEqual(detailed["entries"][0]["direction"], "Layered direction")

        # Reload and verify (after save, _sync_outline populates flat chapters)
        reloaded = load_project_state(self.root)
        # Check via volumes
        vol_ch_reloaded = reloaded["outline"]["volumes"][0]["chapters"][0]
        self.assertEqual(vol_ch_reloaded["direction"], "Layered direction")
        self.assertEqual(len(vol_ch_reloaded["beats"]), 1)


if __name__ == "__main__":
    unittest.main()
