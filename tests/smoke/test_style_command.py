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

    def test_style_check_detects_meta_leakage_from_review_rules(self) -> None:
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
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "沈照一路追到废灯棚外，脑子里还在回想着前面的线索，可他忽然冒出一句第三章里不该出现的判断。\n\n"
            "这种念头并不来自眼前，而像是作者在正文里硬塞进来的提示，让整段叙述一下子跳出故事本身。\n\n"
            "他立刻压下那股违和感，继续盯住风里晃动的残灯，不让注意力再次飘向章节结构。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["reviewRuleProfile"], "default")
        self.assertEqual(payload["reviewRuleProfileSource"], "project")
        meta = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "metaLeakage")
        self.assertTrue(meta["detected"])
        self.assertEqual(meta["count"], 1)
        self.assertFalse(meta["exempted"])
        self.assertTrue(any(item["ruleId"] == "metaLeakage" for item in payload["judgements"]))

    def test_style_check_allows_quoted_meta_leakage_exemption(self) -> None:
        (self.temp_dir / "review-rules.yaml").write_text(
            json.dumps(
                {
                    "profiles": {
                        "default": {
                            "enabledRules": ["metaLeakage"],
                            "exemptions": [
                                {
                                    "ruleId": "metaLeakage",
                                    "allowWhen": {
                                        "quotedOnly": True,
                                        "matchPatterns": ["写|草稿|小说"],
                                    },
                                    "reason": "书中书对白豁免",
                                }
                            ],
                        }
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "沈照伏在案前改稿，耳边只剩灯火轻爆的细响，整个人都埋在纸页和旧伤带来的闷痛里。\n\n"
            "他对同伴低声说：“第十二章这一段还得重写，不然这本小说的伏笔会散。”说完又把纸压平，继续逐句斟酌。\n\n"
            "屋里没人把这句话当成现实叙事的裂口，因为此刻讨论的本来就是他手上的书稿，而不是他们所在的世界。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        meta = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "metaLeakage")
        self.assertFalse(meta["detected"])
        self.assertTrue(meta["rawDetected"])
        self.assertTrue(meta["exempted"])
        self.assertEqual(meta["exemptionReason"], "书中书对白豁免")
        self.assertFalse(any(item["ruleId"] == "metaLeakage" for item in payload["judgements"]))

    def test_style_check_detects_pov_overreach(self) -> None:
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
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "晒场上的灰还没有完全落定，沈照站在旧灯下不敢再往前半步，连呼吸都压得很轻。\n\n"
            "就在这片诡异的静里，晒场西侧的木梁上，忽然又轻轻落下一点灰，正落在沈照右后方一条废弃排灰沟的边沿。\n\n"
            "他没有回头，也没有任何额外感知来源，可叙述却把那处本不该被他看见的细节写得清清楚楚。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        pov = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "povOverreach")
        self.assertTrue(pov["detected"])
        self.assertTrue(any(item["ruleId"] == "povOverreach" for item in payload["judgements"]))

    def test_style_check_does_not_flag_pov_when_character_turns_back(self) -> None:
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
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "晒场上的风刮得人耳膜发紧，沈照忽然停步，意识到身后的动静和先前完全不同。\n\n"
            "他猛地回头，正看见晒场西侧的木梁上落下一点灰，灰点滚到排灰沟边沿才停住。\n\n"
            "既然人物已经明确回头，这一处观察就不该被算作 POV 越界。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        pov = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "povOverreach")
        self.assertFalse(pov["detected"])
        self.assertFalse(any(item["ruleId"] == "povOverreach" for item in payload["judgements"]))

    def test_style_check_detects_new_ai_phrase_clusters_and_readability(self) -> None:
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "那不是犹豫，是多年压下去的旧火重新顶了上来。这不是侥幸，不是误打误撞，是他早就留在袖里的后手。\n\n"
            "那不像试探，更像有人故意把门缝留给他。这不是风声。更像旧灯室深处有人轻轻拨了一下灯芯。真正值钱的，从来都是这盏灯现在指着的地方。岳怀川压低声音问了一句：“还有什么？”\n\n"
            "沈照沿着废灯棚外那条狭窄的灰沟慢慢往前挪，脚下每一块松动的砖都像会突然塌下去，他一边盯着风里晃动的残灯，一边还得分神去记那些被夜色吞没的脚印、火痕和断裂木梁的位置，整个人绷得像一根被拉到快断的旧弦。\n\n"
            "岳怀川跟在后面，同样没有开口，只是把呼吸压得更轻，可他眼角的余光始终在扫四周那些被烟熏黑的墙角、塌陷的梁柱和半埋在灰里的旧灯座，像是生怕下一瞬又有什么被人从黑暗里轻轻拨动，让他们前面所有的判断都变成了更深一层的误导。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["style", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        contrast = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "contrastFlipPattern")
        analogical = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "analogicalPivotPattern")
        catchphrase = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "templateCatchphrasePattern")
        readability = next(item for item in payload["styleAnalysis"]["patternResults"] if item["id"] == "paragraphReadability")

        self.assertTrue(contrast["detected"])
        self.assertTrue(analogical["detected"])
        self.assertTrue(catchphrase["detected"])
        self.assertTrue(readability["detected"])
        self.assertTrue(any(item["ruleId"] == "contrastFlipPattern" for item in payload["judgements"]))
        self.assertTrue(any(item["ruleId"] == "analogicalPivotPattern" for item in payload["judgements"]))
        self.assertTrue(any(item["ruleId"] == "templateCatchphrasePattern" for item in payload["judgements"]))
        self.assertTrue(any(item["ruleId"] == "paragraphReadability" for item in payload["judgements"]))


if __name__ == "__main__":
    unittest.main()
