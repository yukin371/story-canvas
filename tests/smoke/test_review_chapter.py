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

    def test_review_chapter_surfaces_structured_plan_block_actions(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "目标：先压住体内失控的潮息。\n风险：顾长渊可能提前察觉异样。\n\n"
            "约束：不能在宗门长老面前暴露归墟体。\n时间窗口：只剩今夜到天明前这段空档。\n\n"
            "沈玄意识到自己又把念头排成了清单，像是在给一场逃亡写执行方案。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            any(item["id"] == "structuredPlanBlock" and item["detected"] for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"])
        )
        self.assertTrue(any("目标/风险/约束" in item or "方案说明" in item for item in payload["priorityActions"]))
        self.assertTrue(any("方案文档腔" in item for item in payload["contractAlignment"]["risks"]))

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
        wrapped_entity_rule = next(
            item for item in payload["ruleJudgements"] if item.get("ruleId") == "wrappedEntityMissingRegistry"
        )
        self.assertEqual(wrapped_entity_rule["source"], "core")
        self.assertEqual(wrapped_entity_rule["scope"], "chapter")
        self.assertEqual(wrapped_entity_rule["kind"], "hard")
        self.assertEqual(wrapped_entity_rule["severity"], "warning")
        self.assertIn("registry-coverage", wrapped_entity_rule["tags"])
        self.assertIn("wrapped-entity", wrapped_entity_rule["tags"])
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

    def test_review_chapter_surfaces_power_progression_conflict_signal(self) -> None:
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
        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [],
                    "worldRules": [],
                    "powerProgressions": [
                        {
                            "id": "immortal-path",
                            "label": "仙道境界",
                            "stages": [
                                {"name": "练气一层", "nextStage": "练气二层", "breakthroughRequirements": ["凝气入脉"]},
                                {"name": "练气二层", "nextStage": "练气三层"},
                                {"name": "练气三层", "nextStage": "筑基"},
                                {"name": "筑基", "nextStage": "金丹"},
                            ],
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

        chapter_path = self.temp_dir / "chapters" / "chapter-007.md"
        chapter_path.write_text(
            "# 第七章\n\n"
            "沈玄如今仍停在练气一层，可他偏要借这一夜直接突破筑基，连护法与药引都还没备齐。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-007"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["analysisSignals"]["powerProgressionConflictCount"], 1)
        self.assertTrue(payload["consistencySignals"]["powerProgressionConflicts"])
        self.assertEqual(payload["consistencySignals"]["powerProgressionConflicts"][0]["expectedNextStage"], "练气二层")
        self.assertTrue(any(item["ruleId"] == "powerProgressionConflict" for item in payload["ruleJudgements"]))
        self.assertTrue(any("练气二层" in item or "突破链" in item for item in payload["priorityActions"]))
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("越阶" in item or "世界规则" in item for item in alignment_text))

    def test_review_chapter_flags_weak_chapter_handoff(self) -> None:
        (self.temp_dir / "outline.yaml").write_text(
            json.dumps(
                {
                    "chapters": [
                        {
                            "id": "chapter-001",
                            "title": "仓库惊变",
                            "status": "draft",
                            "direction": "林舟在仓库冲突后确认自己被盯上。",
                            "beats": [{"summary": "确认风险来源"}],
                            "scenePlans": [{"title": "仓库对峙", "goal": "暴露追踪风险"}],
                        },
                        {
                            "id": "chapter-002",
                            "title": "追踪余波",
                            "status": "draft",
                            "direction": "承接仓库冲突后的追踪风险，决定是否继续深查守夜人。",
                            "beats": [{"summary": "接住余波"}, {"summary": "做出选择"}],
                            "scenePlans": [{"title": "回到住处", "goal": "处理伤势并判断下一步"}],
                        },
                    ],
                    "chapterDirections": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.temp_dir / "entities.yaml").write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "id": "char-linzhou",
                            "name": "林舟",
                            "type": "character",
                            "state": {"statusTags": ["受伤", "暴露风险上升"]},
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
        (self.temp_dir / "threads.yaml").write_text(
            json.dumps(
                {
                    "threads": [
                        {
                            "id": "thread-night-watch",
                            "label": "守夜人暗线",
                            "status": "active",
                            "relatedEntities": ["char-linzhou"],
                            "relatedChapters": ["chapter-001", "chapter-002"],
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        chapter_path = self.temp_dir / "chapters" / "chapter-002.md"
        chapter_path.write_text(
            "# 第二章\n\n"
            "清晨的集市已经热闹起来，卖药的、卖鱼的、吆喝的声音混在一起，像一锅翻滚的水。\n\n"
            "他只是随意买了份热汤，便去城南打听旧案，整段开场都没有回到前夜留下的伤势、追踪或守夜人压力。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-002"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["analysisSignals"]["chapterHandoffRiskCount"], 1)
        self.assertTrue(payload["chapterHandoffSignals"]["detected"])
        self.assertEqual(payload["storyConstraintSignals"]["chapterHandoff"]["previousChapter"]["id"], "chapter-001")
        self.assertTrue(any("上一章" in item or "细纲" in item for item in payload["priorityActions"]))
        self.assertTrue(any(item["ruleId"] == "chapterHandoffWeak" for item in payload["ruleJudgements"]))
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("自然续写" in item or "切场" in item for item in alignment_text))

    def test_review_chapter_emits_meta_leakage_rule_judgement(self) -> None:
        (self.temp_dir / "review-rules.yaml").write_text(
            json.dumps(
                {
                    "profiles": {
                        "default": {
                            "enabledRules": ["metaLeakage"],
                            "exemptions": [],
                        }
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "沈照推开旧库房的门，扑面而来的灰味让他下意识屏住呼吸，可脑子里忽然冒出上一章没有的确定判断。\n\n"
            "这种判断与眼前场景并不相连，反而像作者在正文里提醒读者，第三章里某个伏笔已经提前动了一下。\n\n"
            "他很快把心思拉回地上的灰痕，却已经让叙述露出一丝不属于故事世界的裂口。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["styleAnalysis"]["reviewRuleProfile"], "default")
        self.assertEqual(payload["styleAnalysis"]["reviewRuleProfileSource"], "project")
        meta = next(item for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"] if item["id"] == "metaLeakage")
        self.assertTrue(meta["detected"])
        self.assertTrue(any(item["ruleId"] == "metaLeakage" for item in payload["ruleJudgements"]))

    def test_review_chapter_emits_pov_overreach_rule_judgement(self) -> None:
        (self.temp_dir / "review-rules.yaml").write_text(
            json.dumps(
                {
                    "profiles": {
                        "default": {
                            "enabledRules": ["povOverreach"],
                            "exemptions": [],
                        }
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "沈照站在废灯棚前，肩背绷得很紧，连呼吸都像在等下一声裂响。\n\n"
            "就在这片诡异的静里，西侧木梁上忽然落下一点灰，正落在沈照右后方那条废弃排灰沟的边沿。\n\n"
            "他没有回头，也没有任何镜面或感知来源，可旁白却替他看见了那块盲区里的细节。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        pov = next(item for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"] if item["id"] == "povOverreach")
        self.assertTrue(pov["detected"])
        self.assertTrue(any(item["ruleId"] == "povOverreach" for item in payload["ruleJudgements"]))

    def test_review_chapter_emits_new_ai_phrase_rule_judgement(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "那不是犹豫，是多年压下去的旧火重新顶了上来。这不是侥幸，不是误打误撞，是他早就留在袖里的后手。\n\n"
            "那不像试探，更像有人故意把门缝留给他。这不是风声。更像旧灯室深处有人轻轻拨了一下灯芯。真正值钱的，从来都是这盏灯现在指着的地方。\n\n"
            "岳怀川压低声音问了一句：“还有什么？”沈照沿着废灯棚外那条狭窄的灰沟慢慢往前挪，脚下每一块松动的砖都像会突然塌下去，他一边盯着风里晃动的残灯，一边还得分神去记那些被夜色吞没的脚印、火痕和断裂木梁的位置，整个人绷得像一根被拉到快断的旧弦。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        pattern_ids = {
            item["id"]
            for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"]
            if item.get("detected")
        }
        self.assertIn("contrastFlipPattern", pattern_ids)
        self.assertIn("analogicalPivotPattern", pattern_ids)
        self.assertIn("templateCatchphrasePattern", pattern_ids)
        self.assertIn("paragraphReadability", pattern_ids)
        self.assertTrue(any(item["ruleId"] == "contrastFlipPattern" for item in payload["ruleJudgements"]))
        self.assertTrue(any(item["ruleId"] == "paragraphReadability" for item in payload["ruleJudgements"]))


if __name__ == "__main__":
    unittest.main()
