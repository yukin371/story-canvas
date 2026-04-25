from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
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


def _build_state_files(root: Path) -> None:
    """Write minimal valid state files for every key in STATE_KEY_MAP."""
    sample_data = default_project_state()
    sample_data["project"].update({"title": "layered-test"})
    sample_data["outline"] = {"chapters": [], "chapterDirections": [], "volumes": []}
    for state_key, internal_key in STATE_KEY_MAP.items():
        fpath = resolve_state_path(root, state_key)
        _write_json_yaml(fpath, sample_data[internal_key])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class LoadLayeredProjectTest(unittest.TestCase):
    """Loading a layered project reads files from spec/ where appropriate."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-layered-load-"))
        self.root = self.tmp / "project"
        # Create layered layout: spec/ dir present
        (self.root / "spec").mkdir(parents=True)
        _build_state_files(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_layered_project(self):
        state = load_project_state(self.root)
        self.assertEqual(state["project"]["title"], "layered-test")
        self.assertEqual(state["outline"]["chapters"], [])
        self.assertEqual(state["entities"]["entities"], [])
        self.assertIn("_stateMeta", state)
        # Verify spec-eligible keys were read from spec/ paths
        outline_path = resolve_state_path(self.root, "outline")
        self.assertTrue(str(outline_path).startswith(str(self.root / "spec")))


class SaveLayeredProjectTest(unittest.TestCase):
    """Saving a layered project writes files to spec/ where appropriate."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-layered-save-"))
        self.root = self.tmp / "project"
        (self.root / "spec").mkdir(parents=True)
        _build_state_files(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_layered_project(self):
        state = load_project_state(self.root)
        state["project"]["title"] = "modified-layered"
        state["outline"]["chapters"] = [{"id": "ch01", "title": "first"}]
        save_state(self.root, state)

        # Reload and verify
        reloaded = load_project_state(self.root)
        self.assertEqual(reloaded["project"]["title"], "modified-layered")
        self.assertEqual(reloaded["outline"]["chapters"][0]["id"], "ch01")

        # Verify spec-eligible files are under spec/
        self.assertTrue((self.root / "spec" / "outline.yaml").exists())
        self.assertTrue((self.root / "spec" / "entities.yaml").exists())
        self.assertTrue((self.root / "spec" / "timeline.yaml").exists())
        self.assertTrue((self.root / "spec" / "threads.yaml").exists())
        self.assertTrue((self.root / "spec" / "structures.yaml").exists())

        # Verify always-at-root files are NOT in spec/
        self.assertTrue((self.root / "project.yaml").exists())
        self.assertFalse((self.root / "spec" / "project.yaml").exists())

        # Verify subdir-resident files are at expected locations
        self.assertTrue((self.root / "proposals" / "draft-proposals.yaml").exists())
        self.assertTrue((self.root / "reviews" / "change-requests.yaml").exists())


class FlatProjectUnchangedTest(unittest.TestCase):
    """Flat projects continue to work exactly as before (no spec/ created)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sh-flat-state-"))
        self.root = self.tmp / "project"
        shutil.copytree(FIXTURE_ROOT, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_flat_project_unchanged(self):
        # spec/ should NOT exist initially
        self.assertFalse((self.root / "spec").exists())

        # Load and modify
        state = load_project_state(self.root)
        state["project"]["title"] = "flat-modified"
        save_state(self.root, state)

        # spec/ should NOT have been created by save
        self.assertFalse((self.root / "spec").exists())

        # Verify files are at root (flat layout)
        self.assertTrue((self.root / "outline.yaml").exists())
        self.assertTrue((self.root / "entities.yaml").exists())
        self.assertTrue((self.root / "threads.yaml").exists())
        self.assertTrue((self.root / "structures.yaml").exists())

        # Reload and verify data integrity
        reloaded = load_project_state(self.root)
        self.assertEqual(reloaded["project"]["title"], "flat-modified")


if __name__ == "__main__":
    unittest.main()
