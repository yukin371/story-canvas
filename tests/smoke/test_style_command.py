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
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main


class StyleCommandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-style-"))
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "init",
                    "--root",
                    str(self.temp_dir),
                    "--title",
                    "Style Harbor",
                    "--genre",
                    "Mystery",
                    "--core-promise",
                    "悬疑反转稳定",
                    "--pace-contract",
                    "快节奏",
                ]
            )
        self.assertEqual(exit_code, 0)

        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "他慢慢走进仓库，仿佛空气都在耳边发冷。\n\n"
            "他慢慢停在铁桌边，仿佛桌角也在等他出错。\n\n"
            "他慢慢抬起头，仿佛黑暗里有人先一步认出了他。\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_style_check_outputs_analysis(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertEqual(payload["profile"], "default")
        self.assertEqual(payload["profileSource"], "builtin")
        self.assertIn("styleAnalysis", payload)
        self.assertIn("constraints", payload)
        self.assertIn("textMetrics", payload)

    def test_style_check_uses_project_profile_override(self) -> None:
        (self.temp_dir / "style-profiles.yaml").write_text(
            json.dumps(
                {
                    "profiles": {
                        "web-serial-zh": {
                            "patternThresholds": {"formulaicTransition": 4.0}
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "style",
                    "check",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--profile",
                    "web-serial-zh",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["profile"], "web-serial-zh")
        self.assertEqual(payload["profileSource"], "project")

    def test_style_report_aggregates_chapters(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "report", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterCount"], 1)
        self.assertEqual(payload["aggregate"]["chapterCount"], 1)
        self.assertTrue(payload["chapters"])
        self.assertIn("patternCounts", payload["aggregate"])

    def test_style_repair_outputs_prompt(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                ["style", "repair", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--format", "prompt"]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertIn("repairPrompt", payload)
        self.assertIn("style constraints", payload["repairPrompt"])

    def test_style_repair_outputs_change_request_drafts(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "style",
                    "repair",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--format",
                    "change-requests",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertTrue(payload["changeRequests"])
        self.assertEqual(payload["changeRequests"][0]["kind"], "style")


if __name__ == "__main__":
    unittest.main()
