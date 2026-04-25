from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
DEMO_ROOT = REPO_ROOT / "projects" / "demo-urban-occult-long"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main


class DemoUrbanOccultLongSampleSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-demo-urban-occult-long-"))
        self.project_root = self.temp_dir / "demo-urban-occult-long"
        shutil.copytree(DEMO_ROOT, self.project_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_json(self, args: list[str]) -> dict:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(args)
        self.assertEqual(exit_code, 0, msg=f"command failed: {' '.join(args)}")
        return json.loads(buffer.getvalue())

    def _run_text(self, args: list[str]) -> str:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(args)
        self.assertEqual(exit_code, 0, msg=f"command failed: {' '.join(args)}")
        return buffer.getvalue()

    def test_demo_urban_occult_long_sample_supports_commercial_long_form_workflow(self) -> None:
        project = json.loads((self.project_root / "project.yaml").read_text(encoding="utf-8"))
        self.assertEqual(project["commercialPositioning"]["targetPlatform"], "qidian")
        self.assertEqual(project["commercialPositioning"]["chapterWordTarget"], 3000)
        self.assertTrue(project["commercialPositioning"]["hookStack"])

        doctor = self._run_json(["doctor", "--root", str(self.project_root)])
        warning_codes = [item.get("code") for item in doctor["checks"] if item.get("level") == "warning"]
        self.assertTrue(doctor["ok"])
        self.assertEqual(doctor["summary"]["errors"], 0)
        self.assertEqual(doctor["summary"]["warnings"], 0)
        self.assertEqual(warning_codes, [])

        scene_targets = {
            "chapter-001": 1,
            "chapter-002": 2,
            "chapter-003": 2,
            "chapter-004": 3,
            "chapter-005": 3,
            "chapter-006": 3,
            "chapter-007": 3,
            "chapter-008": 3,
        }
        expected_ratings = {
            "chapter-001": "strong",
            "chapter-002": "solid",
            "chapter-003": "strong",
            "chapter-004": "strong",
            "chapter-005": "solid",
            "chapter-006": "solid",
            "chapter-007": "strong",
            "chapter-008": "solid",
        }

        for chapter_id, scene_index in scene_targets.items():
            analysis = self._run_json(
                ["chapter", "analyze", "--root", str(self.project_root), "--chapter-id", chapter_id]
            )
            self.assertTrue(analysis["activeEntities"])

            review = self._run_json(
                ["review", "chapter", "--root", str(self.project_root), "--chapter-id", chapter_id]
            )
            self.assertEqual(review["chapterId"], chapter_id)
            self.assertEqual(review["weightedScores"]["profile"]["primaryGenre"], "fantasy")
            self.assertEqual(review["weightedScores"]["profile"]["subGenre"], "urban-occult")
            self.assertIn("web-serial", review["weightedScores"]["profile"]["styleTags"])
            self.assertIn("folk-occult", review["weightedScores"]["profile"]["styleTags"])
            self.assertEqual(review["weightedScores"]["profile"]["targetPlatform"], "qidian")
            adjustment_sources = {item["source"] for item in review["weightedScores"]["adjustments"]}
            self.assertIn("targetPlatform:qidian", adjustment_sources)
            self.assertEqual(review["rating"], expected_ratings[chapter_id])
            self.assertIn("contractAlignment", review)
            self.assertIn("commercialAlignment", review)
            self.assertNotEqual(review["commercialAlignment"]["status"], "not-applicable")

            context = self._run_json(
                ["context", "refresh", "--root", str(self.project_root), "--chapter-id", chapter_id]
            )
            self.assertEqual(context["chapterId"], chapter_id)
            self.assertTrue(context["activeCharacters"])

            scene_review = self._run_json(
                [
                    "review",
                    "scene",
                    "--root",
                    str(self.project_root),
                    "--chapter-id",
                    chapter_id,
                    "--scene-index",
                    str(scene_index),
                ]
            )
            self.assertEqual(scene_review["chapterId"], chapter_id)
            self.assertEqual(scene_review["sceneRange"]["sceneIndex"], scene_index)
            self.assertEqual(scene_review["sceneRange"]["source"], "explicit")
            self.assertIn(scene_review["rating"], {"solid", "strong"})
            self.assertIn("scenePlanId", scene_review["sceneRange"])
            self.assertIn("contractAlignment", scene_review)
            self.assertIn("commercialAlignment", scene_review)
            self.assertNotEqual(scene_review["commercialAlignment"]["status"], "not-applicable")

        chapter_011_analysis = self._run_json(
            ["chapter", "analyze", "--root", str(self.project_root), "--chapter-id", "chapter-011"]
        )
        self.assertTrue(chapter_011_analysis["activeEntities"])

        chapter_011_review = self._run_json(
            ["review", "chapter", "--root", str(self.project_root), "--chapter-id", "chapter-011"]
        )
        self.assertEqual(chapter_011_review["chapterId"], "chapter-011")
        self.assertEqual(chapter_011_review["rating"], "solid")
        self.assertGreaterEqual(chapter_011_review["textMetrics"]["wordCount"], 3000)
        self.assertEqual(chapter_011_review["weightedScores"]["profile"]["targetPlatform"], "qidian")
        self.assertNotEqual(chapter_011_review["commercialAlignment"]["status"], "not-applicable")

        chapter_011_scene = self._run_json(
            [
                "review",
                "scene",
                "--root",
                str(self.project_root),
                "--chapter-id",
                "chapter-011",
                "--scene-index",
                "3",
            ]
        )
        self.assertEqual(chapter_011_scene["sceneRange"]["sceneIndex"], 3)
        self.assertEqual(chapter_011_scene["sceneRange"]["source"], "explicit")
        self.assertIn(chapter_011_scene["rating"], {"solid", "strong"})
        self.assertNotEqual(chapter_011_scene["commercialAlignment"]["status"], "not-applicable")

        chapter_012_review = self._run_json(
            ["review", "chapter", "--root", str(self.project_root), "--chapter-id", "chapter-012"]
        )
        self.assertEqual(chapter_012_review["chapterId"], "chapter-012")
        self.assertEqual(chapter_012_review["rating"], "strong")
        self.assertGreaterEqual(chapter_012_review["textMetrics"]["wordCount"], 3000)
        self.assertEqual(chapter_012_review["commercialAlignment"]["status"], "aligned")

        chapter_012_scene = self._run_json(
            [
                "review",
                "scene",
                "--root",
                str(self.project_root),
                "--chapter-id",
                "chapter-012",
                "--scene-index",
                "2",
            ]
        )
        self.assertEqual(chapter_012_scene["sceneRange"]["sceneIndex"], 2)
        self.assertEqual(chapter_012_scene["sceneRange"]["source"], "explicit")
        self.assertIn(chapter_012_scene["rating"], {"solid", "strong"})

        suggest_payload = self._run_json(
            ["chapter", "suggest", "--root", str(self.project_root), "--chapter-id", "chapter-001"]
        )
        self.assertIn("created", suggest_payload)

        apply_payload = self._run_json(
            [
                "review",
                "apply",
                "--root",
                str(self.project_root),
                "--chapter-id",
                "chapter-001",
                "--all-pending",
                "--decision",
                "accepted",
            ]
        )
        self.assertIn("updated", apply_payload)

        projection_payload = self._run_json(
            ["projection", "apply", "--root", str(self.project_root), "--chapter-id", "chapter-001"]
        )
        self.assertIn("appliedChangeRequests", projection_payload)

        export_path = self.project_root / "manuscript-smoke.md"
        self._run_text(
            [
                "export",
                "--root",
                str(self.project_root),
                "--format",
                "markdown",
                "--output",
                str(export_path),
            ]
        )
        self.assertTrue(export_path.exists())
        exported_text = export_path.read_text(encoding="utf-8")
        self.assertIn("## 夜班接尸", exported_text)
        self.assertIn("## 执牌上任", exported_text)


if __name__ == "__main__":
    unittest.main()
