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


class ReviewChapterSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-review-"))
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "init",
                    "--root",
                    str(self.temp_dir),
                    "--title",
                    "Fog Harbor",
                    "--genre",
                    "Mystery",
                    "--core-promise",
                    "悬疑反转稳定",
                    "--pace-contract",
                    "快节奏",
                ]
            )
        self.assertEqual(exit_code, 0)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_review_chapter_generates_scores_and_persists_report(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}拖着受伤的手臂冲进仓库，却发现@{周墨}已经在里面等他。\n\n"
            "周墨压低声音说：“你如果现在还不交出账本，我们今晚都走不出去。”林舟一边流血一边怀疑她是不是已经背叛。\n",
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()):
            analyze_exit = main(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(analyze_exit, 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertEqual(payload["rubricVersion"], "chapter-review-v1")
        self.assertEqual(payload["scores"]["maxScore"], 100)
        self.assertEqual(len(payload["scores"]["dimensions"]), 5)
        self.assertEqual(payload["weightedScores"]["profile"]["primaryGenre"], "mystery")
        self.assertEqual(payload["weightedScores"]["profile"]["targetPlatform"], "")
        self.assertEqual(payload["weightedScores"]["maxScore"], 100)
        self.assertEqual(len(payload["weightedScores"]["breakdown"]), 5)
        self.assertTrue(payload["analysisSignals"]["analysisBacked"])
        self.assertIn("styleAnalysis", payload)
        self.assertIn("styleAnalysis", payload["styleAnalysis"])
        self.assertIn("profileSource", payload["styleAnalysis"])
        self.assertTrue(payload["priorityActions"])
        self.assertEqual(payload["projectContext"]["positioning"]["primaryGenre"], "mystery")
        self.assertEqual(payload["projectContext"]["commercialPositioning"]["targetPlatform"], "")
        self.assertIn("status", payload["contractAlignment"])
        self.assertTrue(payload["contractAlignment"]["matched"] or payload["contractAlignment"]["risks"])
        self.assertEqual(payload["commercialAlignment"]["status"], "not-applicable")

        saved = json.loads((self.temp_dir / "reviews" / "story-reviews.yaml").read_text(encoding="utf-8"))
        self.assertEqual(saved["rubricVersion"], "chapter-review-v1")
        self.assertEqual(len(saved["chapterReviews"]), 1)
        self.assertEqual(saved["chapterReviews"][0]["reviewId"], payload["reviewId"])

    def test_review_chapter_can_run_without_analysis_log(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里站在码头，迟迟没有拨出那个电话。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["analysisSignals"]["analysisBacked"])
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertIn("styleAnalysis", payload)
        self.assertIn("summary", payload)
        self.assertIn("contractAlignment", payload)
        self.assertIn("commercialAlignment", payload)
        self.assertIn("weightedScores", payload)
        self.assertEqual(payload["projectContext"]["commercialPositioning"]["targetPlatform"], "")


if __name__ == "__main__":
    unittest.main()
