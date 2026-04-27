from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main
from story_harness_cli.protocol import load_project_state
from story_harness_cli.protocol.files import LAYOUT_LAYERED, resolve_state_path
from story_harness_cli.protocol.io import dump_json_compatible_yaml


class TestChapterCreateFlat(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh-chapter-create-flat-"))
        exit_code = main(
            [
                "init",
                "--root",
                str(self.temp_dir),
                "--title",
                "测试书",
                "--genre",
                "玄幻",
                "--chapter-id",
                "chapter-001",
                "--chapter-title",
                "第一章",
            ]
        )
        self.assertEqual(exit_code, 0)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_inserts_after_existing_chapter_and_sets_active(self):
        exit_code = main(
            [
                "chapter",
                "create",
                "--root",
                str(self.temp_dir),
                "--chapter-id",
                "chapter-002",
                "--title",
                "第二章 灯下有灰",
                "--after-chapter-id",
                "chapter-001",
                "--direction",
                "承接上一章余波，并把新的交易条件抛出来。",
                "--beat",
                "压价::岳怀川开出更苛刻条件",
                "--beat",
                "沈照决定先赌一把",
                "--scene",
                "后屋::两人试探底线",
                "--scene",
                "残灰落地",
            ]
        )
        self.assertEqual(exit_code, 0)

        state = load_project_state(self.temp_dir)
        chapter_ids = [item["id"] for item in state["outline"]["chapters"]]
        self.assertEqual(chapter_ids, ["chapter-001", "chapter-002"])
        created = next(item for item in state["outline"]["chapters"] if item["id"] == "chapter-002")
        self.assertEqual(created["title"], "第二章 灯下有灰")
        self.assertEqual(created["direction"], "承接上一章余波，并把新的交易条件抛出来。")
        self.assertEqual(len(created["beats"]), 2)
        self.assertEqual(created["beats"][0]["title"], "压价")
        self.assertEqual(created["beats"][0]["summary"], "岳怀川开出更苛刻条件")
        self.assertEqual(created["scenePlans"][0]["title"], "后屋")
        self.assertEqual(created["scenePlans"][0]["summary"], "两人试探底线")
        self.assertEqual(created["scenePlans"][1]["summary"], "残灰落地")
        self.assertEqual(state["project"]["activeChapterId"], "chapter-002")

        detailed = next(item for item in state["detailed_outlines"]["entries"] if item["chapterId"] == "chapter-002")
        self.assertEqual(detailed["direction"], "承接上一章余波，并把新的交易条件抛出来。")
        self.assertEqual(len(detailed["scenePlans"]), 2)

        chapter_file = self.temp_dir / "chapters" / "chapter-002.md"
        self.assertTrue(chapter_file.exists())
        self.assertEqual(chapter_file.read_text(encoding="utf-8"), "# 第二章 灯下有灰\n\n")


class TestChapterCreateLayered(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh-chapter-create-layered-"))
        exit_code = main(
            [
                "init",
                "--root",
                str(self.temp_dir),
                "--title",
                "分卷测试书",
                "--genre",
                "玄幻",
                "--layout",
                "layered",
                "--chapter-id",
                "chapter-001",
                "--chapter-title",
                "第一章",
            ]
        )
        self.assertEqual(exit_code, 0)

        outline_index = {
            "chapters": [],
            "chapterDirections": [],
            "volumes": [
                {"id": "vol-001", "title": "第一卷"},
                {"id": "vol-002", "title": "第二卷"},
            ],
        }
        dump_json_compatible_yaml(resolve_state_path(self.temp_dir, "outline", layout=LAYOUT_LAYERED), outline_index)
        dump_json_compatible_yaml(
            resolve_state_path(self.temp_dir, "outline_volume", volume_id="vol-001", layout=LAYOUT_LAYERED),
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "第一章",
                        "status": "completed",
                        "beats": [],
                        "scenePlans": [],
                    }
                ]
            },
        )
        dump_json_compatible_yaml(
            resolve_state_path(self.temp_dir, "outline_volume", volume_id="vol-002", layout=LAYOUT_LAYERED),
            {"chapters": []},
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_targets_explicit_volume_without_changing_active(self):
        exit_code = main(
            [
                "chapter",
                "create",
                "--root",
                str(self.temp_dir),
                "--chapter-id",
                "chapter-010",
                "--title",
                "第十章 新卷起手",
                "--volume-id",
                "vol-002",
                "--direction",
                "切入第二卷新舞台。",
                "--no-set-active",
            ]
        )
        self.assertEqual(exit_code, 0)

        reloaded = load_project_state(self.temp_dir)
        self.assertEqual(reloaded["project"]["activeChapterId"], "chapter-001")
        vol_2 = next(item for item in reloaded["outline"]["volumes"] if item["id"] == "vol-002")
        self.assertEqual([item["id"] for item in vol_2["chapters"]], ["chapter-010"])
        self.assertEqual(vol_2["chapters"][0]["direction"], "切入第二卷新舞台。")

        persisted_path = resolve_state_path(self.temp_dir, "outline_volume", volume_id="vol-002", layout=LAYOUT_LAYERED)
        persisted = persisted_path.read_text(encoding="utf-8")
        self.assertIn('"chapter-010"', persisted)
        self.assertIn('"第十章 新卷起手"', persisted)

        chapter_file = self.temp_dir / "chapters" / "chapter-010.md"
        self.assertTrue(chapter_file.exists())


if __name__ == "__main__":
    unittest.main()
