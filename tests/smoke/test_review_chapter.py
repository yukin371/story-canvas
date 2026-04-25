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

    def test_review_chapter_consumes_story_constraints(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["emotionalContract"] = {
            "coreEmotions": ["压迫下反制", "真相落地时的原来如此"],
            "chapterEmotionFloor": ["每章至少有一个明确情绪推进点"],
            "forbiddenEmotions": ["空转讲设定"],
            "revealPreference": {
                "defaultMode": "partial-inference",
                "allowDirectExplainAtClimax": True,
            },
        }
        project["storyTemplate"] = {
            "id": "xianxia-revenge-serial",
            "label": "仙侠复仇长篇",
            "modulePolicy": {
                "worldRules": "required",
                "foreshadowLedger": "required",
                "characterStateTracking": "required",
            },
            "reviewFocus": ["世界规则兑现", "伏笔长回收"],
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        (self.temp_dir / "entities.yaml").write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "id": "char-linzhou",
                            "name": "林舟",
                            "type": "character",
                            "state": {
                                "statusTags": ["受伤", "暴露风险上升"],
                                "powerLevel": {"publicLevel": "凡人", "trueLevel": "半觉醒"},
                            },
                            "changeLog": [
                                {
                                    "id": "chg-001",
                                    "chapterId": "chapter-001",
                                    "field": "state.statusTags",
                                    "reason": "仓库冲突后确认自己被盯上",
                                }
                            ],
                        }
                    ],
                    "enrichmentProposals": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [],
                    "worldRules": [
                        {
                            "id": "rule-001",
                            "label": "守夜代价",
                            "rule": "每次借力都会留下追踪痕迹",
                            "scope": "global",
                            "status": "active",
                        }
                    ],
                    "factions": [],
                    "locations": [],
                    "artifacts": [],
                    "mysteries": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.temp_dir / "foreshadowing.yaml").write_text(
            json.dumps(
                {
                    "foreshadows": [
                        {
                            "id": "fs-001",
                            "title": "账本的缺页",
                            "payoffPlan": {
                                "window": {
                                    "type": "short",
                                    "targetChapterStart": "chapter-001",
                                    "targetChapterEnd": "chapter-001",
                                },
                                "style": "partial-reveal",
                                "readerRealizationMode": "infer-before-confirm",
                            },
                            "payoffPoints": [],
                            "status": "planted",
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}拖着受伤的手臂冲进仓库，他知道自己一旦继续追查就会暴露，却还是决定反查账本缺页的来源。\n\n"
            "账本里的缺页果然对应三年前那起旧案，林舟这才意识到真正的幕后人还没有现身。\n",
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
        self.assertEqual(payload["projectContext"]["emotionalContract"]["coreEmotions"], ["压迫下反制", "真相落地时的原来如此"])
        self.assertEqual(payload["projectContext"]["storyTemplate"]["id"], "xianxia-revenge-serial")
        self.assertEqual(payload["storyConstraintSignals"]["worldRules"][0]["id"], "rule-001")
        self.assertEqual(payload["storyConstraintSignals"]["dueForeshadows"][0]["id"], "fs-001")
        self.assertEqual(payload["storyConstraintSignals"]["trackedEntities"][0]["name"], "林舟")
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(
            any("情绪契约" in item for item in alignment_text)
        )
        self.assertTrue(any("推断" in item for item in alignment_text))
        self.assertTrue(any("守夜代价" in item for item in alignment_text))
        self.assertTrue(any("账本的缺页" in item for item in alignment_text))
        self.assertTrue(any("仓库冲突后确认自己被盯上" in item for item in alignment_text))


if __name__ == "__main__":
    unittest.main()
