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
        self.assertIn("ruleJudgements", payload)
        self.assertIn("contractAlignment", payload)
        self.assertEqual(payload["commercialAlignment"]["status"], "not-applicable")

        saved = json.loads((self.temp_dir / "reviews" / "story-reviews.yaml").read_text(encoding="utf-8"))
        self.assertEqual(saved["sceneRubricVersion"], "scene-review-v1")
        self.assertEqual(len(saved["sceneReviews"]), 1)
        self.assertEqual(saved["sceneReviews"][0]["reviewId"], payload["reviewId"])

    def test_review_scene_counts_mystery_hook_without_question_mark(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["commercialPositioning"] = {
            "hookLine": "她发现日志异常来自被截断的接管链路。",
            "serializationModel": "短卷测试",
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "@{许澄}把原始雨量日志和调度签章并排放大，发现二十三点三十七分那一格有半个灰色光标残影，像被人截断过一次输入。\n\n"
            "陌生号码跳进一行字：别追二十三点四十分，追二十三点三十七分。有人在接管前先动了日志。\n",
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
                    "1",
                    "--end-paragraph",
                    "2",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        dimensions = {item["id"]: item for item in payload["scores"]["dimensions"]}
        self.assertGreaterEqual(dimensions["foreshadowing"]["score"], 15)
        self.assertTrue(any("悬念物证/异常信号" in item for item in dimensions["foreshadowing"]["signals"]))
        self.assertFalse(any("未解答的问题" in item for item in dimensions["foreshadowing"]["suggestions"]))
        self.assertEqual(payload["commercialAlignment"]["status"], "aligned")
        self.assertTrue(any("追读钩子" in item for item in payload["commercialAlignment"]["matched"]))

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

    def test_review_scene_limits_outline_deviation_to_current_scene(self) -> None:
        (self.temp_dir / "outline.yaml").write_text(
            json.dumps(
                {
                    "volumes": [
                        {
                            "id": "volume-001",
                            "title": "第一卷",
                            "theme": "",
                            "chapters": [
                                {
                                    "id": "chapter-001",
                                    "title": "第一章",
                                    "status": "completed",
                                    "direction": "两场冲突依次升级。",
                                    "beats": [
                                        {"id": "beat-1", "summary": "林舟在仓库门口先确认接头暗号。", "status": "planned"},
                                        {"id": "beat-2", "summary": "林舟和沈昭在仓库深处把怀疑摊开。", "status": "planned"},
                                    ],
                                    "scenePlans": [
                                        {
                                            "id": "scene-001",
                                            "title": "门口接头",
                                            "summary": "林舟先在仓库门口确认接头暗号。",
                                            "startParagraph": 1,
                                            "endParagraph": 1,
                                        },
                                        {
                                            "id": "scene-002",
                                            "title": "仓库对峙",
                                            "summary": "林舟和沈昭在仓库深处摊开彼此怀疑。",
                                            "startParagraph": 2,
                                            "endParagraph": 3,
                                        },
                                    ],
                                }
                            ],
                        }
                    ],
                    "chapters": [],
                    "chapterDirections": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "林舟直接从侧墙翻了进去，连原定流程都懒得走。\n\n"
            "沈昭已经站在货架尽头等他。\n\n"
            "两人很快把彼此的怀疑摊开，对峙不再留余地。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            scene_one_exit = main(["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--scene-index", "1"])
        scene_one_payload = json.loads(buffer.getvalue())

        buffer = StringIO()
        with redirect_stdout(buffer):
            scene_two_exit = main(["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--scene-index", "2"])
        scene_two_payload = json.loads(buffer.getvalue())

        self.assertEqual(scene_one_exit, 0)
        self.assertEqual(scene_two_exit, 0)
        scene_one_outline = [item for item in scene_one_payload["ruleJudgements"] if item["ruleId"] == "outlineDeviation"]
        scene_two_outline = [item for item in scene_two_payload["ruleJudgements"] if item["ruleId"] == "outlineDeviation"]
        self.assertEqual(len(scene_one_outline), 1)
        self.assertEqual(scene_one_outline[0]["payload"]["beatId"], "beat-1")
        self.assertEqual(scene_two_outline, [])

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

    def test_review_scene_exposes_term_repetition_and_setting_conflict(self) -> None:
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
            "@{林舟}第一次听见蝴蝶效应这个词时，还以为那只是沈昭故作高深的比喻。\n\n"
            "可沈昭再次提起蝴蝶效应，说每一个选择都会沿着暗线反噬回来，让林舟根本无法把这个词从脑子里赶走。\n\n"
            "所谓守夜代价，就是每次借力都不会留下痕迹。可就在这句解释之后，蝴蝶效应又一次被挂在嘴边，像一枚被反复敲响的铃。\n",
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
                    "3",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["styleAnalysis"]["profileSource"], "builtin")
        self.assertTrue(payload["consistencySignals"]["specialTermRepetition"]["detected"])
        self.assertTrue(payload["consistencySignals"]["settingConflicts"])
        self.assertIn("守夜代价", payload["consistencySignals"]["settingConflicts"][0]["issue"])
        self.assertGreaterEqual(payload["analysisSignals"]["settingConflictCount"], 1)
        alignment_text = payload["contractAlignment"]["matched"] + payload["contractAlignment"]["risks"] + payload["contractAlignment"]["notes"]
        self.assertTrue(any("高频特殊术语复用" in item for item in alignment_text))
        self.assertTrue(any("设定冲突" in item or "守夜代价" in item for item in alignment_text))
        self.assertTrue(any("蝴蝶效应" in item for item in payload["consistencySignals"]["specialTermRepetition"]["evidence"]))

    def test_review_scene_emits_meta_leakage_rule_judgement(self) -> None:
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
            "沈照沿着断墙往前摸，指尖一遍遍擦过潮湿的砖缝，耳边只有风从洞口灌进来的呜咽声。\n\n"
            "他忽然意识到这一卷里最早埋下的那点异样正在回头追他，可这种想法本不该以作品结构的口吻闯进当下。\n\n"
            "更糟的是，他甚至像在提醒读者，上一章那盏旧灯并没有真正熄灭，而是把新的危险悄悄送到了眼前。\n\n"
            "意识到不对之后，他立刻压下杂念，继续顺着灰痕向前找人，不让自己再偏离现场。\n",
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
                    "2",
                    "--end-paragraph",
                    "3",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["styleAnalysis"]["reviewRuleProfile"], "default")
        self.assertEqual(payload["styleAnalysis"]["reviewRuleProfileSource"], "project")
        meta = next(item for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"] if item["id"] == "metaLeakage")
        self.assertTrue(meta["detected"])
        self.assertTrue(any(item["ruleId"] == "metaLeakage" for item in payload["ruleJudgements"]))

    def test_review_scene_emits_pov_overreach_rule_judgement(self) -> None:
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
            "沈照贴着断墙往前挪，连脚下碎瓦都不敢踩实，生怕再惊动黑暗里的东西。\n\n"
            "就在这时，背后高处忽然落下一点灰，正落在他右后方那条废弃排灰沟的边沿。\n\n"
            "他没有回头，也没有任何余光、镜面或感知来源，可叙述却直接把盲区里的细节摆到了读者眼前。\n\n"
            "下一瞬，他才真正听见身后传来更轻的一声脆响。\n",
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
                    "2",
                    "--end-paragraph",
                    "3",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        pov = next(item for item in payload["styleAnalysis"]["styleAnalysis"]["patternResults"] if item["id"] == "povOverreach")
        self.assertTrue(pov["detected"])
        self.assertTrue(any(item["ruleId"] == "povOverreach" for item in payload["ruleJudgements"]))

    def test_review_scene_emits_new_ai_phrase_rule_judgement(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "前置段落只用来保证场景编号稳定。\n\n"
            "那不是犹豫，是多年压下去的旧火重新顶了上来。这不是侥幸，不是误打误撞，是他早就留在袖里的后手。\n\n"
            "那不像试探，更像有人故意把门缝留给他。这不是风声。更像旧灯室深处有人轻轻拨了一下灯芯。真正值钱的，从来都是这盏灯现在指着的地方。岳怀川压低声音问了一句：“还有什么？”\n\n"
            "收束段落放在场景之外。\n",
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
                    "2",
                    "--end-paragraph",
                    "3",
                ]
            )
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
        self.assertTrue(any(item["ruleId"] == "analogicalPivotPattern" for item in payload["ruleJudgements"]))


if __name__ == "__main__":
    unittest.main()
