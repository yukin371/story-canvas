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
DEMO_ROOT = REPO_ROOT / "projects" / "demo-light-novel-short"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main


class DemoLightNovelShortSampleSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-demo-light-novel-short-"))
        self.project_root = self.temp_dir / "demo-light-novel-short"
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

    def test_demo_light_novel_short_sample_supports_style_aware_review_workflow(self) -> None:
        doctor = self._run_json(["doctor", "--root", str(self.project_root)])
        self.assertTrue(doctor["ok"])
        self.assertEqual(doctor["summary"]["errors"], 0)

        scene_counts = {
            "chapter-001": 2,
            "chapter-002": 2,
            "chapter-003": 2,
        }

        for chapter_id, scene_count in scene_counts.items():
            analysis = self._run_json(
                ["chapter", "analyze", "--root", str(self.project_root), "--chapter-id", chapter_id]
            )
            self.assertTrue(analysis["activeEntities"])

            review = self._run_json(
                ["review", "chapter", "--root", str(self.project_root), "--chapter-id", chapter_id]
            )
            self.assertEqual(review["chapterId"], chapter_id)
            self.assertEqual(review["weightedScores"]["profile"]["primaryGenre"], "fantasy")
            self.assertEqual(review["weightedScores"]["profile"]["subGenre"], "western-fantasy")
            self.assertIn("light-novel", review["weightedScores"]["profile"]["styleTags"])
            self.assertIn("projectContext", review)
            self.assertIn("contractAlignment", review)

            context = self._run_json(
                ["context", "refresh", "--root", str(self.project_root), "--chapter-id", chapter_id]
            )
            self.assertEqual(context["chapterId"], chapter_id)
            self.assertTrue(context["activeCharacters"])

            for scene_index in range(1, scene_count + 1):
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
                self.assertIn("scenePlanId", scene_review["sceneRange"])
                self.assertIn("contractAlignment", scene_review)

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
        self.assertIn("## 会打喷嚏的包裹", exported_text)
        self.assertIn("晨钟前的试飞", exported_text)


if __name__ == "__main__":
    unittest.main()
