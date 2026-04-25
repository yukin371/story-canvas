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


class ReviewSceneSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-scene-review-"))
        with redirect_stdout(StringIO()):
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

    def test_review_scene_generates_scores_and_persists_report(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库，手臂还在流血。\n\n"
            "@{周墨}已经站在货架旁等他，她低声问账本是不是已经落到别人手里。林舟因为怀疑她，决定继续试探。\n\n"
            "周墨忽然说出只有内鬼才知道的细节，林舟这才意识到账本背后还有更大的秘密？\n\n"
            "门外响起脚步声，两人同时停下争执。\n",
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()):
            analyze_exit = main(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(analyze_exit, 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "review",
                    "scene",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--start-paragraph",
                    "2",
                    "--end-paragraph",
                    "3",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["rubricVersion"], "scene-review-v1")
        self.assertEqual(payload["sceneRange"]["startParagraph"], 2)
        self.assertEqual(payload["sceneRange"]["endParagraph"], 3)
        self.assertEqual(payload["scores"]["maxScore"], 100)
        self.assertEqual(len(payload["scores"]["dimensions"]), 5)
        self.assertIn("summary", payload)
        self.assertTrue(payload["analysisSignals"]["analysisBacked"])
        self.assertTrue(payload["priorityActions"])
        self.assertIn("projectContext", payload)
        self.assertEqual(payload["projectContext"]["commercialPositioning"]["targetPlatform"], "")
        self.assertIn("contractAlignment", payload)
        self.assertEqual(payload["commercialAlignment"]["status"], "not-applicable")

        saved = json.loads((self.temp_dir / "reviews" / "story-reviews.yaml").read_text(encoding="utf-8"))
        self.assertEqual(saved["sceneRubricVersion"], "scene-review-v1")
        self.assertEqual(len(saved["sceneReviews"]), 1)
        self.assertEqual(saved["sceneReviews"][0]["reviewId"], payload["reviewId"])

    def test_review_scene_can_list_candidates(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n\n"
            "他开始怀疑自己是不是漏掉了什么。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--list-scenes"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertGreaterEqual(len(payload["scenes"]), 2)
        self.assertEqual(payload["scenes"][0]["sceneIndex"], 1)

    def test_review_scene_can_use_scene_index(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n\n"
            "他开始怀疑自己是不是漏掉了什么。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                ["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--scene-index", "2"]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["sceneRange"]["sceneIndex"], 2)
        self.assertEqual(payload["sceneRange"]["startParagraph"], 3)

    def test_review_scene_prefers_explicit_scene_plans(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n\n"
            "他开始怀疑自己是不是漏掉了什么。\n",
            encoding="utf-8",
        )
        with redirect_stdout(StringIO()):
            main(
                [
                    "outline",
                    "scene-add",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--title",
                    "仓库",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "2",
                ]
            )
            main(
                [
                    "outline",
                    "scene-add",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--title",
                    "码头",
                    "--start-paragraph",
                    "3",
                    "--end-paragraph",
                    "4",
                ]
            )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--scene-index", "2"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["sceneRange"]["sceneIndex"], 2)
        self.assertEqual(payload["sceneRange"]["startParagraph"], 3)
        self.assertEqual(payload["sceneRange"]["source"], "explicit")
        self.assertIn("scenePlanId", payload["sceneRange"])

    def test_review_scene_uses_detected_scene_plans_as_explicit_source(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n\n"
            "他开始怀疑自己是不是漏掉了什么。\n",
            encoding="utf-8",
        )
        with redirect_stdout(StringIO()):
            main(["outline", "scene-detect", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--scene-index", "2"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["sceneRange"]["sceneIndex"], 2)
        self.assertEqual(payload["sceneRange"]["startParagraph"], 3)
        self.assertEqual(payload["sceneRange"]["source"], "explicit")
        self.assertIn("scenePlanId", payload["sceneRange"])

    def test_review_scene_outputs_contract_alignment(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里追问账本的去向。\n\n"
            "@{周墨}忽然说出只有内鬼才知道的细节，林舟这才意识到真正的真相还没揭开？\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "review",
                    "scene",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "2",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertIn("status", payload["contractAlignment"])
        self.assertTrue(payload["contractAlignment"]["matched"] or payload["contractAlignment"]["risks"])
        self.assertIn("commercialAlignment", payload)
        self.assertEqual(payload["commercialAlignment"]["status"], "not-applicable")

    def test_review_scene_rejects_invalid_paragraph_range(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里站在码头。\n\n"
            "@{周墨}没有出现。\n",
            encoding="utf-8",
        )

        with self.assertRaises(SystemExit):
            main(
                [
                    "review",
                    "scene",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--start-paragraph",
                    "3",
                ]
            )

    def test_review_scene_consumes_story_constraints(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["emotionalContract"] = {
            "coreEmotions": ["未知感", "原来如此"],
            "chapterEmotionFloor": ["每章至少有一个明确情绪推进点"],
            "forbiddenEmotions": ["空转讲设定"],
            "revealPreference": {
                "defaultMode": "partial-inference",
                "allowDirectExplainAtClimax": True,
            },
        }
        project["storyTemplate"] = {
            "id": "mystery-web-serial",
            "label": "悬疑连载",
            "modulePolicy": {
                "worldRules": "required",
                "foreshadowLedger": "required",
                "characterStateTracking": "required",
            },
            "reviewFocus": ["世界规则兑现", "伏笔回收", "角色状态演化"],
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
                            "state": {"statusTags": ["受伤", "怀疑同伴"]},
                            "changeLog": [
                                {
                                    "id": "chg-001",
                                    "chapterId": "chapter-001",
                                    "field": "state.statusTags",
                                    "reason": "得知账本缺页与旧案吻合",
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
                            "label": "旧案印章会暴露借阅者身份",
                            "rule": "翻阅卷宗会留下可追溯痕迹",
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
                            "title": "账本缺页",
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
            "@{林舟}追问账本缺页的来源，明知道继续查下去会让自己暴露，还是决定把这条线索追到底。\n\n"
            "他忽然想起三年前卷宗上的印章，原来账本缺页真的对应那起旧案？\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "review",
                    "scene",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "2",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectContext"]["emotionalContract"]["coreEmotions"], ["未知感", "原来如此"])
        self.assertEqual(payload["projectContext"]["storyTemplate"]["id"], "mystery-web-serial")
        self.assertEqual(payload["storyConstraintSignals"]["worldRules"][0]["id"], "rule-001")
        self.assertEqual(payload["storyConstraintSignals"]["dueForeshadows"][0]["id"], "fs-001")
        self.assertEqual(payload["storyConstraintSignals"]["trackedEntities"][0]["name"], "林舟")
        self.assertEqual(
            payload["storyConstraintSignals"]["trackedEntities"][0]["recentChange"]["reason"],
            "得知账本缺页与旧案吻合",
        )
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(
            any("情绪契约" in item for item in alignment_text)
        )
        self.assertTrue(any("推断" in item for item in alignment_text))
        self.assertTrue(any("旧案印章会暴露借阅者身份" in item for item in alignment_text))
        self.assertTrue(any("账本缺页" in item for item in alignment_text))


if __name__ == "__main__":
    unittest.main()
