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
        self.assertIn("ruleJudgements", payload)
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

    def test_review_chapter_exposes_term_repetition_and_setting_conflict(self) -> None:
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
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "林舟第一次听见蝴蝶效应这个词，仍没意识到它会改变判断。\n\n"
            "沈昭又提起蝴蝶效应，像是在提醒他每个选择都会反噬。\n\n"
            "所谓守夜代价，就是每次借力都不会留下痕迹。可下一段里，蝴蝶效应再次被说出口，像成了口头禅。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["consistencySignals"]["specialTermRepetition"]["detected"])
        self.assertTrue(payload["consistencySignals"]["settingConflicts"])
        self.assertIn("守夜代价", payload["consistencySignals"]["settingConflicts"][0]["issue"])
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("高频特殊术语复用" in item for item in alignment_text))
        self.assertTrue(any("设定冲突" in item or "守夜代价" in item for item in alignment_text))
        self.assertTrue(any("蝴蝶效应" in item for item in payload["consistencySignals"]["specialTermRepetition"]["evidence"]))

    def test_review_chapter_flags_genre_register_drift_for_xuanhuan(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["genre"] = "玄幻"
        project["positioning"]["primaryGenre"] = "fantasy"
        project["positioning"]["subGenre"] = "xuanhuan"
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "沈玄将所有信息整合成一个时间框架，把接下来一年里最危险的变数都压进脑海深处，像在给自己列一张不合时宜的清单。\n\n"
            "第一优先级是压制归墟体气息，第二优先级是在苍梧域站稳脚跟，第三优先级则是摸清顾长渊的动向。这样的优先级口吻与整段玄幻叙事格格不入，连他自己都隐约觉得生硬。\n\n"
            "前世的记忆催他立刻动手，前世的经验又提醒他必须忍耐，前世的判断更让他反复回到同一套解释框架里。",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["styleAnalysis"]["profile"], "xuanhuan-zh")
        self.assertTrue(
            any(item["id"] == "registerDrift" and item["detected"] for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"])
        )
        self.assertTrue(
            any(item["id"] == "narrativeFrameRepetition" and item["detected"] for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"])
        )
        self.assertTrue(any("优先级" in item or "框架" in item for item in payload["priorityActions"]))
        self.assertTrue(any("前世的" in item or "叙事支架" in item for item in payload["priorityActions"]))
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("题材语域失真" in item or "现代项目管理口吻" in item for item in alignment_text))

    def test_review_chapter_exposes_wrapped_entity_registry_gaps(self) -> None:
        (self.temp_dir / "entities.yaml").write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "id": "char-shenxuan",
                            "name": "沈玄",
                            "type": "character",
                            "aliases": [],
                        }
                    ],
                    "enrichmentProposals": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{沈玄}抬头望向山门尽头的 @{青云宗}，又低头看了一眼掌中的 @{镇海印}。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["wrappedEntitySignals"]["count"], 3)
        self.assertTrue(any(item["name"] == "沈玄" and item["source"] == "entities" for item in payload["wrappedEntitySignals"]["covered"]))
        self.assertTrue(any(item["name"] == "青云宗" for item in payload["wrappedEntitySignals"]["missing"]))
        self.assertTrue(any(item["name"] == "镇海印" for item in payload["wrappedEntitySignals"]["missing"]))
        self.assertGreaterEqual(payload["analysisSignals"]["wrappedEntityMissingCount"], 2)
        self.assertTrue(any("青云宗" in item or "镇海印" in item for item in payload["priorityActions"]))
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("未建档" in item or "真相源" in item for item in alignment_text))

    def test_review_chapter_flags_unintroduced_name_reveal(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-005.md"
        chapter_path.write_text(
            "# 第五章\n\n"
            "人家是散修，想走哪条路走哪条路。不过青云宗的试炼她也报了名，说是要在试炼中找一条线索。\n\n"
            "女散修。黑鞘剑。冰寒的剑意。\n\n"
            "叶清漪。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-005"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["analysisSignals"]["unintroducedNameRevealCount"], 1)
        self.assertTrue(payload["consistencySignals"]["unintroducedNameReveals"])
        self.assertEqual(payload["consistencySignals"]["unintroducedNameReveals"][0]["name"], "叶清漪")
        self.assertTrue(any("叶清漪" in item for item in payload["priorityActions"]))
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("无来源提前揭露" in item or "旁白越界" in item for item in alignment_text))

    def test_review_chapter_flags_capability_task_mismatch(self) -> None:
        (self.temp_dir / "entities.yaml").write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "id": "char-shenxuan",
                            "name": "沈玄",
                            "type": "character",
                            "state": {
                                "powerLevel": {"publicLevel": "练气一层"},
                            },
                        }
                    ],
                    "enrichmentProposals": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        chapter_path = self.temp_dir / "chapters" / "chapter-006.md"
        chapter_path.write_text(
            "# 第六章\n\n"
            "沈玄入门之后还未真正站稳脚跟，眼下也只在练气一层。\n\n"
            "可执事仍让沈玄参加宗门试炼，最终环节不是比武，而是进入秘境探索。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-006"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["analysisSignals"]["capabilityTaskRiskCount"], 1)
        self.assertTrue(payload["consistencySignals"]["capabilityTaskRisks"])
        self.assertEqual(payload["consistencySignals"]["capabilityTaskRisks"][0]["entityName"], "沈玄")
        self.assertTrue(any(item["ruleId"] == "capabilityTaskMismatch" for item in payload["ruleJudgements"]))
        self.assertTrue(any("沈玄" in item for item in payload["priorityActions"]))
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("任务门槛" in item or "保护条件" in item for item in alignment_text))


if __name__ == "__main__":
    unittest.main()
