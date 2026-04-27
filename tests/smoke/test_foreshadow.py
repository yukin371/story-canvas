from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.protocol.files import resolve_state_path, detect_layout, LAYOUT_LAYERED, LAYOUT_FLAT
from story_harness_cli.cli import main


def _write_json_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _setup_flat_project(root: Path) -> None:
    """Create a minimal flat-layout project."""
    _write_json_yaml(root / "project.yaml", {
        "title": "Test",
        "genre": "test",
        "defaultMode": "driving",
        "activeChapterId": "ch-001",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    })
    _write_json_yaml(root / "outline.yaml", {"chapters": [], "chapterDirections": [], "volumes": []})
    _write_json_yaml(root / "entities.yaml", {"entities": [], "enrichmentProposals": []})
    _write_json_yaml(root / "timeline.yaml", {"events": []})
    _write_json_yaml(root / "branches.yaml", {"branches": []})
    _write_json_yaml(root / "threads.yaml", {"threads": []})
    _write_json_yaml(root / "structures.yaml", {"activeStructure": None, "mappings": []})
    _write_json_yaml(root / "proposals" / "draft-proposals.yaml", {"draftProposals": []})
    _write_json_yaml(root / "reviews" / "change-requests.yaml", {"changeRequests": []})
    _write_json_yaml(root / "reviews" / "story-reviews.yaml", {
        "rubricVersion": "chapter-review-v1",
        "sceneRubricVersion": "scene-review-v1",
        "chapterReviews": [],
        "sceneReviews": [],
    })
    _write_json_yaml(root / "projections" / "projection.yaml", {
        "snapshotProjections": [], "relationProjections": [],
        "sceneScopeProjections": [], "timelineProjections": [],
        "causalityProjections": [],
    })
    _write_json_yaml(root / "projections" / "context-lens.yaml", {"currentChapterId": None, "lenses": []})
    _write_json_yaml(root / "logs" / "projection-log.yaml", {"projectionChanges": []})
    (root / "chapters").mkdir(exist_ok=True)


def _setup_layered_project(root: Path) -> None:
    """Create a minimal layered-layout project."""
    _setup_flat_project(root)
    # Move spec-eligible files into spec/
    spec = root / "spec"
    spec.mkdir(exist_ok=True)
    for name in ("outline.yaml", "entities.yaml", "timeline.yaml", "threads.yaml", "structures.yaml"):
        src = root / name
        if src.exists():
            src.rename(spec / name)


class ForeshadowPathTest(unittest.TestCase):
    """Test that foreshadowing.yaml resolves correctly for both layouts."""

    def test_foreshadow_path_layered(self) -> None:
        with tempfile.TemporaryDirectory(prefix="story-harness-foreshadow-") as td:
            root = Path(td)
            _setup_layered_project(root)
            layout = detect_layout(root)
            self.assertEqual(layout, LAYOUT_LAYERED)
            path = resolve_state_path(root, "foreshadowing")
            self.assertEqual(path, root / "spec" / "foreshadowing.yaml")

    def test_foreshadow_path_flat(self) -> None:
        with tempfile.TemporaryDirectory(prefix="story-harness-foreshadow-") as td:
            root = Path(td)
            _setup_flat_project(root)
            layout = detect_layout(root)
            self.assertEqual(layout, LAYOUT_FLAT)
            path = resolve_state_path(root, "foreshadowing")
            self.assertEqual(path, root / "foreshadowing.yaml")


class ForeshadowCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-foreshadow-"))
        _setup_flat_project(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plant_foreshadow(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main([
                "foreshadow", "plant",
                "--root", str(self.temp_dir),
                "--description", "Mysterious locket found in attic",
                "--chapter-id", "ch-001",
                "--planned-payoff", "ch-010",
                "--notes", "Key to family secret",
            ])
        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Planted foreshadow fs-001", output)

        # Verify the file was written correctly
        fs_path = self.temp_dir / "foreshadowing.yaml"
        self.assertTrue(fs_path.exists())
        data = json.loads(fs_path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["foreshadows"]), 1)
        entry = data["foreshadows"][0]
        self.assertEqual(entry["id"], "fs-001")
        self.assertEqual(entry["description"], "Mysterious locket found in attic")
        self.assertEqual(entry["plantedChapter"], "ch-001")
        self.assertEqual(entry["plannedPayoffChapter"], "ch-010")
        self.assertEqual(entry["actualPayoffChapter"], None)
        self.assertEqual(entry["status"], "planted")
        self.assertEqual(entry["notes"], "Key to family secret")

    def test_resolve_foreshadow(self) -> None:
        # Plant first
        main([
            "foreshadow", "plant",
            "--root", str(self.temp_dir),
            "--description", "Mysterious locket",
            "--chapter-id", "ch-001",
        ])

        # Now resolve
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main([
                "foreshadow", "resolve",
                "--root", str(self.temp_dir),
                "--foreshadow-id", "fs-001",
                "--payoff-chapter", "ch-012",
            ])
        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Resolved foreshadow fs-001", output)

        # Verify the file was updated correctly
        fs_path = self.temp_dir / "foreshadowing.yaml"
        data = json.loads(fs_path.read_text(encoding="utf-8"))
        entry = data["foreshadows"][0]
        self.assertEqual(entry["status"], "resolved")
        self.assertEqual(entry["actualPayoffChapter"], "ch-012")

    def test_list_foreshadow(self) -> None:
        # Plant two foreshadows
        main([
            "foreshadow", "plant",
            "--root", str(self.temp_dir),
            "--description", "First foreshadow",
            "--chapter-id", "ch-001",
        ])
        main([
            "foreshadow", "plant",
            "--root", str(self.temp_dir),
            "--description", "Second foreshadow",
            "--chapter-id", "ch-003",
        ])
        # Resolve the first
        main([
            "foreshadow", "resolve",
            "--root", str(self.temp_dir),
            "--foreshadow-id", "fs-001",
            "--payoff-chapter", "ch-010",
        ])

        # List all
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main([
                "foreshadow", "list",
                "--root", str(self.temp_dir),
            ])
        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("fs-001", output)
        self.assertIn("fs-002", output)

        # List only planted
        buffer2 = StringIO()
        with redirect_stdout(buffer2):
            exit_code = main([
                "foreshadow", "list",
                "--root", str(self.temp_dir),
                "--status", "planted",
            ])
        self.assertEqual(exit_code, 0)
        output2 = buffer2.getvalue()
        self.assertNotIn("fs-001", output2)
        self.assertIn("fs-002", output2)

    def test_resolve_nonexistent_foreshadow(self) -> None:
        err_buffer = StringIO()
        with redirect_stderr(err_buffer):
            exit_code = main([
                "foreshadow", "resolve",
                "--root", str(self.temp_dir),
                "--foreshadow-id", "fs-999",
            ])
        self.assertEqual(exit_code, 1)
        self.assertIn("not found", err_buffer.getvalue())

    def test_check_foreshadow_reports_due_overdue_and_unscheduled(self) -> None:
        (self.temp_dir / "foreshadowing.yaml").write_text(
            json.dumps(
                {
                    "foreshadows": [
                        {
                            "id": "fs-001",
                            "description": "旧版单章回收",
                            "plantedChapter": "ch-001",
                            "plannedPayoffChapter": "ch-005",
                            "actualPayoffChapter": None,
                            "status": "planted",
                            "notes": "",
                        },
                        {
                            "id": "fs-002",
                            "title": "新版窗口回收",
                            "plantPoints": [{"chapterId": "ch-002"}],
                            "payoffPlan": {
                                "window": {
                                    "type": "short",
                                    "targetChapterStart": "ch-004",
                                    "targetChapterEnd": "ch-005",
                                }
                            },
                            "status": "planted",
                            "payoffPoints": [],
                        },
                        {
                            "id": "fs-003",
                            "title": "已经拖过回收窗",
                            "plantPoints": [{"chapterId": "ch-001"}],
                            "payoffPlan": {
                                "window": {
                                    "type": "short",
                                    "targetChapterStart": "ch-002",
                                    "targetChapterEnd": "ch-003",
                                }
                            },
                            "status": "planted",
                            "payoffPoints": [],
                        },
                        {
                            "id": "fs-004",
                            "description": "没有计划回收",
                            "plantedChapter": "ch-001",
                            "plannedPayoffChapter": None,
                            "actualPayoffChapter": None,
                            "status": "planted",
                            "notes": "",
                        },
                        {
                            "id": "fs-005",
                            "description": "已经回收",
                            "plantedChapter": "ch-001",
                            "plannedPayoffChapter": "ch-004",
                            "actualPayoffChapter": "ch-004",
                            "status": "resolved",
                            "notes": "",
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["foreshadow", "check", "--root", str(self.temp_dir), "--chapter-id", "ch-005"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())

        self.assertEqual(payload["chapterId"], "ch-005")
        self.assertEqual(payload["summary"]["dueCount"], 2)
        self.assertEqual(payload["summary"]["overdueCount"], 1)
        self.assertEqual(payload["summary"]["unresolvedWithoutScheduleCount"], 1)
        self.assertTrue(any(item["id"] == "fs-001" for item in payload["dueForeshadows"]))
        self.assertTrue(any(item["id"] == "fs-002" for item in payload["dueForeshadows"]))
        self.assertTrue(any(item["id"] == "fs-003" for item in payload["overdueForeshadows"]))
        self.assertTrue(any(item["id"] == "fs-004" for item in payload["unresolvedWithoutSchedule"]))

    def test_check_foreshadow_defaults_to_active_chapter(self) -> None:
        (self.temp_dir / "foreshadowing.yaml").write_text(
            json.dumps(
                {
                    "foreshadows": [
                        {
                            "id": "fs-010",
                            "description": "活跃章节回收",
                            "plantedChapter": "ch-001",
                            "plannedPayoffChapter": "ch-001",
                            "actualPayoffChapter": None,
                            "status": "planted",
                            "notes": "",
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["foreshadow", "check", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["chapterId"], "ch-001")
        self.assertEqual(payload["summary"]["dueCount"], 1)


if __name__ == "__main__":
    unittest.main()
