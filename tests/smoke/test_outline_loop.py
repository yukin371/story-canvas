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


class OutlineLoopSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-outline-"))
        main(
            [
                "init",
                "--root",
                str(self.temp_dir),
                "--title",
                "雾港疑案",
                "--genre",
                "悬疑",
                "--target-audience",
                "mystery-reader",
                "--core-promise",
                "每章推进账本谜团",
                "--pace-contract",
                "中快节奏",
                "--chapter-id",
                "chapter-001",
                "--chapter-title",
                "裂痕之夜",
            ]
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_incomplete_prd(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 关键设定 onboarding: TBD\n- 本章交付点: TBD\n",
            encoding="utf-8",
        )

    def test_outline_loop(self) -> None:
        args_root = str(self.temp_dir)
        self.assertEqual(
            main(
                [
                    "outline",
                    "propose",
                    "--root",
                    args_root,
                    "--mode",
                    "chapter",
                    "--title",
                    "第二章方向草案",
                    "--summary",
                    "让林舟继续追查账本。",
                    "--chapter-id",
                    "chapter-002",
                    "--item",
                    "港区追踪::林舟沿着血迹和传闻追查账本。",
                ]
            ),
            0,
        )

        proposals = json.loads((self.temp_dir / "proposals" / "draft-proposals.yaml").read_text(encoding="utf-8"))
        proposal_id = proposals["draftProposals"][0]["id"]

        self.assertEqual(
            main(
                [
                    "outline",
                    "promote",
                    "--root",
                    args_root,
                    "--proposal-id",
                    proposal_id,
                    "--chapter-id",
                    "chapter-002",
                ]
            ),
            0,
        )
        self.assertEqual(main(["projection", "apply", "--root", args_root, "--chapter-id", "chapter-002"]), 0)

        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        projection_log = json.loads((self.temp_dir / "logs" / "projection-log.yaml").read_text(encoding="utf-8"))

        chapter_002 = next(item for item in outline["chapters"] if item["id"] == "chapter-002")
        self.assertTrue(chapter_002["beats"])
        self.assertTrue(projection_log["projectionChanges"])

    def test_outline_scene_add_and_list(self) -> None:
        args_root = str(self.temp_dir)
        self.assertEqual(
            main(
                [
                    "outline",
                    "scene-add",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--title",
                    "仓库对峙",
                    "--summary",
                    "林舟与沈昭在仓库爆发冲突",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "3",
                ]
            ),
            0,
        )

        scene_payload = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in scene_payload["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(len(chapter["scenePlans"]), 1)
        self.assertEqual(chapter["scenePlans"][0]["title"], "仓库对峙")

    def test_outline_scene_update_and_remove(self) -> None:
        args_root = str(self.temp_dir)
        self.assertEqual(
            main(
                [
                    "outline",
                    "scene-add",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--title",
                    "仓库对峙",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "3",
                ]
            ),
            0,
        )
        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        scene_id = chapter["scenePlans"][0]["id"]

        self.assertEqual(
            main(
                [
                    "outline",
                    "scene-update",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--scene-id",
                    scene_id,
                    "--title",
                    "仓库裂痕",
                    "--summary",
                    "林舟与沈昭关系恶化",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "2",
                ]
            ),
            0,
        )
        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(chapter["scenePlans"][0]["title"], "仓库裂痕")
        self.assertEqual(chapter["scenePlans"][0]["endParagraph"], 2)

        self.assertEqual(
            main(
                [
                    "outline",
                    "scene-remove",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--scene-id",
                    scene_id,
                ]
            ),
            0,
        )
        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(chapter["scenePlans"], [])

    def test_outline_scene_detect_generates_scene_plans(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n\n"
            "他开始怀疑自己是不是漏掉了什么。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "scene-detect", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertEqual(payload["detected"], 2)
        self.assertFalse(payload["replaced"])
        self.assertEqual(payload["scenes"][0]["source"], "heuristic-detect")
        self.assertEqual(payload["scenes"][0]["detectionMethod"], "scene-candidate-v1")

        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(len(chapter["scenePlans"]), 2)
        self.assertTrue(chapter["scenePlans"][0]["title"].startswith("场景01"))

    def test_outline_scene_detect_requires_replace_for_existing_scene_plans(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n",
            encoding="utf-8",
        )
        with redirect_stdout(StringIO()):
            main(
                [
                    "outline",
                    "scene-add",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--title",
                    "手工场景",
                    "--start-paragraph",
                    "1",
                    "--end-paragraph",
                    "1",
                ]
            )

        with self.assertRaises(SystemExit):
            main(["outline", "scene-detect", "--root", args_root, "--chapter-id", "chapter-001"])

        with redirect_stdout(StringIO()):
            exit_code = main(["outline", "scene-detect", "--root", args_root, "--chapter-id", "chapter-001", "--replace"])
        self.assertEqual(exit_code, 0)

    def test_outline_scene_sync_reports_and_repairs_tail_overflow(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "第一段。\n\n"
            "第二段。\n",
            encoding="utf-8",
        )
        with redirect_stdout(StringIO()):
            self.assertEqual(
                main(
                    [
                        "outline",
                        "scene-add",
                        "--root",
                        args_root,
                        "--chapter-id",
                        "chapter-001",
                        "--title",
                        "尾段越界",
                        "--start-paragraph",
                        "1",
                        "--end-paragraph",
                        "3",
                    ]
                ),
                0,
            )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "scene-sync", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["validation"]["valid"])
        self.assertEqual(payload["suggestion"]["method"], "trim-tail-overflow")
        self.assertTrue(payload["suggestion"]["available"])
        self.assertEqual(payload["suggestion"]["scenes"][0]["endParagraph"], 2)
        self.assertFalse(payload["applied"])

        with redirect_stdout(StringIO()):
            exit_code = main(["outline", "scene-sync", "--root", args_root, "--chapter-id", "chapter-001", "--apply"])
        self.assertEqual(exit_code, 0)

        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(chapter["scenePlans"][0]["endParagraph"], 2)
        self.assertEqual(chapter["scenePlans"][0]["syncMethod"], "trim-tail-overflow")

    def test_outline_scene_sync_repartitions_ranges_when_scene_count_matches(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "@{林舟}在雨夜里冲进仓库。\n\n"
            "@{周墨}已经在里面等他。\n\n"
            "三天后，@{林舟}再次回到码头。\n\n"
            "他开始怀疑自己是不是漏掉了什么。\n",
            encoding="utf-8",
        )
        with redirect_stdout(StringIO()):
            self.assertEqual(
                main(
                    [
                        "outline",
                        "scene-add",
                        "--root",
                        args_root,
                        "--chapter-id",
                        "chapter-001",
                        "--title",
                        "仓库对峙",
                        "--summary",
                        "旧边界一",
                        "--start-paragraph",
                        "1",
                        "--end-paragraph",
                        "1",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "outline",
                        "scene-add",
                        "--root",
                        args_root,
                        "--chapter-id",
                        "chapter-001",
                        "--title",
                        "码头回返",
                        "--summary",
                        "旧边界二",
                        "--start-paragraph",
                        "2",
                        "--end-paragraph",
                        "4",
                    ]
                ),
                0,
            )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "scene-sync", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["suggestion"]["method"], "heuristic-repartition")
        self.assertTrue(payload["suggestion"]["available"])
        self.assertEqual(payload["suggestion"]["scenes"][0]["title"], "仓库对峙")
        self.assertEqual(payload["suggestion"]["scenes"][0]["startParagraph"], 1)
        self.assertEqual(payload["suggestion"]["scenes"][0]["endParagraph"], 2)
        self.assertEqual(payload["suggestion"]["scenes"][1]["title"], "码头回返")
        self.assertEqual(payload["suggestion"]["scenes"][1]["startParagraph"], 3)
        self.assertEqual(payload["suggestion"]["scenes"][1]["endParagraph"], 4)

        with redirect_stdout(StringIO()):
            exit_code = main(["outline", "scene-sync", "--root", args_root, "--chapter-id", "chapter-001", "--apply"])
        self.assertEqual(exit_code, 0)

        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(chapter["scenePlans"][0]["title"], "仓库对峙")
        self.assertEqual(chapter["scenePlans"][0]["endParagraph"], 2)
        self.assertEqual(chapter["scenePlans"][1]["title"], "码头回返")
        self.assertEqual(chapter["scenePlans"][1]["startParagraph"], 3)
        self.assertEqual(chapter["scenePlans"][1]["syncMethod"], "heuristic-repartition")

        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        chapter = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        self.assertEqual(len(chapter["scenePlans"]), 2)
        self.assertNotEqual(chapter["scenePlans"][0]["title"], "手工场景")

    def test_structure_scaffold_populates_outline_guidance(self) -> None:
        args_root = str(self.temp_dir)
        outline_path = self.temp_dir / "outline.yaml"
        outline_path.write_text(
            json.dumps(
                {
                    "chapters": [
                        {"id": "chapter-001", "title": "第一章", "status": "draft", "beats": [], "scenePlans": []},
                        {
                            "id": "chapter-002",
                            "title": "第二章",
                            "status": "planned",
                            "beats": [],
                            "scenePlans": [],
                            "direction": "手工方向：保持林舟调查账本。",
                        },
                        {"id": "chapter-003", "title": "第三章", "status": "planned", "beats": [], "scenePlans": []},
                        {"id": "chapter-004", "title": "第四章", "status": "planned", "beats": [], "scenePlans": []},
                    ],
                    "chapterDirections": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["structure", "apply", "--root", args_root, "--template", "three-act"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["structure", "map", "--root", args_root, "--beat", "中点", "--chapter-id", "chapter-002"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["structure", "scaffold", "--root", args_root])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["beatsGenerated"], 7)
        self.assertEqual(payload["directionsUpdated"], 2)
        self.assertEqual(payload["directionsPreserved"], 1)
        self.assertEqual(len(payload["chaptersUpdated"]), 3)

        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        chapter_001 = next(item for item in outline["chapters"] if item["id"] == "chapter-001")
        chapter_002 = next(item for item in outline["chapters"] if item["id"] == "chapter-002")
        chapter_004 = next(item for item in outline["chapters"] if item["id"] == "chapter-004")

        self.assertTrue(any(item.get("source") == "structure-scaffold" for item in chapter_001["beats"]))
        self.assertTrue(any(item.get("structureBeatName") == "中点" for item in chapter_002["beats"]))
        self.assertEqual(chapter_002["direction"], "手工方向：保持林舟调查账本。")
        self.assertTrue(chapter_001["direction"].startswith("结构指引："))
        self.assertTrue(any(item.get("structureBeatName") == "结局" for item in chapter_004["beats"]))

        with redirect_stdout(StringIO()):
            exit_code = main(["structure", "scaffold", "--root", args_root, "--replace-directions"])
        self.assertEqual(exit_code, 0)

        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        chapter_002 = next(item for item in outline["chapters"] if item["id"] == "chapter-002")
        self.assertTrue(chapter_002["direction"].startswith("结构指引："))

    def test_structure_check_exposes_missing_project_prd_advisory(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "PRD.md").unlink()

        with redirect_stdout(StringIO()):
            self.assertEqual(main(["structure", "apply", "--root", args_root, "--template", "three-act"]), 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["structure", "check", "--root", args_root])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["projectAdvisories"][0]["path"], "PRD.md")

    def test_outline_check_requires_direction_and_breakdown(self) -> None:
        args_root = str(self.temp_dir)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "check", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["summary"]["notReadyChapters"], 1)
        self.assertEqual(payload["chapters"][0]["status"], "missing-direction")

        with redirect_stdout(StringIO()):
            self.assertEqual(
                main(
                    [
                        "outline",
                        "propose",
                        "--root",
                        args_root,
                        "--mode",
                        "chapter",
                        "--title",
                        "第一章方向",
                        "--summary",
                        "林舟必须在仓库线索失效前锁定账本去向。",
                        "--chapter-id",
                        "chapter-001",
                    ]
                ),
                0,
            )
        proposals = json.loads((self.temp_dir / "proposals" / "draft-proposals.yaml").read_text(encoding="utf-8"))
        proposal_id = proposals["draftProposals"][0]["id"]
        with redirect_stdout(StringIO()):
            self.assertEqual(
                main(
                    [
                        "outline",
                        "promote",
                        "--root",
                        args_root,
                        "--proposal-id",
                        proposal_id,
                        "--chapter-id",
                        "chapter-001",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "outline",
                        "beat-add",
                        "--root",
                        args_root,
                        "--chapter-id",
                        "chapter-001",
                        "--summary",
                        "仓库对峙必须暴露账本已经易手。",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "outline",
                        "scene-add",
                        "--root",
                        args_root,
                        "--chapter-id",
                        "chapter-001",
                        "--title",
                        "仓库正面交锋",
                        "--summary",
                        "林舟和沈昭必须在这一幕里摊开彼此的怀疑。",
                        "--start-paragraph",
                        "1",
                        "--end-paragraph",
                        "2",
                    ]
                ),
                0,
            )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "check", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertTrue(payload["chapters"][0]["hasDirection"])
        self.assertTrue(payload["chapters"][0]["hasBeats"])
        self.assertTrue(payload["chapters"][0]["hasScenePlans"])

    def test_outline_check_exposes_missing_project_prd_advisory(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "PRD.md").unlink()

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "check", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["projectAdvisories"][0]["path"], "PRD.md")

    def test_outline_check_exposes_incomplete_project_prd_advisory(self) -> None:
        args_root = str(self.temp_dir)
        self._write_incomplete_prd()

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["outline", "check", "--root", args_root, "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertIn("关键设定 onboarding", payload["projectAdvisories"][0]["message"])

    def test_chapter_suggest_requires_outline_before_refine(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "@{林舟}在仓库门口停住了脚步。\n\n"
            "@{沈昭}从黑暗里开口，逼他交出账本。\n",
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()):
            self.assertEqual(main(["chapter", "analyze", "--root", args_root, "--chapter-id", "chapter-001"]), 0)

        with self.assertRaises(SystemExit):
            main(["chapter", "suggest", "--root", args_root, "--chapter-id", "chapter-001"])

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "chapter",
                    "suggest",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--allow-without-outline",
                ]
            )
        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

    def test_chapter_suggest_exposes_missing_project_prd_advisory(self) -> None:
        args_root = str(self.temp_dir)
        (self.temp_dir / "PRD.md").unlink()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "@{林舟}在仓库门口停住了脚步。\n\n"
            "@{沈昭}从黑暗里开口，逼他交出账本。\n",
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()):
            self.assertEqual(main(["chapter", "analyze", "--root", args_root, "--chapter-id", "chapter-001"]), 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "chapter",
                    "suggest",
                    "--root",
                    args_root,
                    "--chapter-id",
                    "chapter-001",
                    "--allow-without-outline",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["projectAdvisories"][0]["path"], "PRD.md")


if __name__ == "__main__":
    unittest.main()
