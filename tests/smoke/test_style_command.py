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
        self.assertIn("judgements", payload)
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

    def test_style_constraints_auto_choose_xuanhuan_profile_and_emit_register_constraints(self) -> None:
        xuanhuan_dir = Path(tempfile.mkdtemp(prefix="story-harness-style-xuanhuan-"))
        try:
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "init",
                        "--root",
                        str(xuanhuan_dir),
                        "--title",
                        "归墟残卷",
                        "--genre",
                        "玄幻",
                        "--core-promise",
                        "命格真相推进",
                        "--pace-contract",
                        "中快节奏",
                    ]
                )
            self.assertEqual(exit_code, 0)

            (xuanhuan_dir / "chapters" / "chapter-001.md").write_text(
                "# 第一章\n\n"
                "沈玄将所有线索整合成一个时间框架，又把近一年的风险与机会逐条排开，像在心里排演一场不该出现在修真世界里的推演。\n\n"
                "第一优先级是压住归墟体气息，第二优先级是尽快在苍梧域站稳脚跟，第三优先级则是盯紧顾长渊的动向。这种过于清晰的优先级口吻，连他自己都觉得生硬。\n\n"
                "前世的记忆告诉他不要迟疑，前世的经验又提醒他不能轻信任何人，前世的判断却让他在同一瞬间生出截然不同的迟疑。\n",
                encoding="utf-8",
            )

            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = main(["style", "constraints", "--root", str(xuanhuan_dir), "--chapter-id", "chapter-001"])
            payload = json.loads(buffer.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["profile"], "xuanhuan-zh")
            self.assertTrue(any("优先级" in item or "框架" in item for item in payload["constraints"]))
            self.assertTrue(any("叙事支架" in item or "前世的" in item for item in payload["constraints"]))
        finally:
            shutil.rmtree(xuanhuan_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
