from __future__ import annotations

import json
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
from story_harness_cli.utils.text import strip_entity_tags


class StripTagsTest(unittest.TestCase):
    def test_strip_curly_brace_tags(self):
        self.assertEqual(strip_entity_tags("@{林舟}走进了仓库"), "林舟走进了仓库")

    def test_strip_simple_tags(self):
        self.assertEqual(strip_entity_tags("@林舟 走进了仓库"), "林舟 走进了仓库")

    def test_no_tags(self):
        self.assertEqual(strip_entity_tags("天空飘着小雨"), "天空飘着小雨")

    def test_multiple_tags(self):
        text = "@{林舟}看着@{沈昭}，低声说自己从未@背叛任何人"
        # @背叛任何人 matches simple tag pattern, @ is stripped
        self.assertEqual(strip_entity_tags(text), "林舟看着沈昭，低声说自己从未背叛任何人")


class ExportCommandTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-export-"))
        fixture = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
        shutil.copytree(fixture, self.temp_dir, dirs_exist_ok=True)
        for d in ["proposals", "reviews", "projections", "logs"]:
            (self.temp_dir / d).mkdir(exist_ok=True)
        for name, content in [
            ("entities.yaml", '{"entities":[],"enrichmentProposals":[]}'),
            ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
            ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
            ("projections/projection.yaml", '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}'),
            ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
            ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
        ]:
            (self.temp_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (self.temp_dir / name).write_text(content + "\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_to_file(self):
        out_file = self.temp_dir / "output" / "novel.txt"
        result = main([
            "export", "--root", str(self.temp_dir),
            "--output", str(out_file),
        ])
        self.assertEqual(result, 0)
        self.assertTrue(out_file.exists())
        content = out_file.read_text(encoding="utf-8")
        self.assertNotIn("@{", content)
        self.assertIn("林舟", content)
        self.assertIn("沈昭", content)

    def test_export_single_chapter(self):
        out_file = self.temp_dir / "single.txt"
        result = main([
            "export", "--root", str(self.temp_dir),
            "--chapter-id", "chapter-001",
            "--output", str(out_file),
        ])
        self.assertEqual(result, 0)
        content = out_file.read_text(encoding="utf-8")
        self.assertNotIn("@{", content)

    def test_export_json_format(self):
        out_file = self.temp_dir / "output.json"
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "json",
            "--output", str(out_file),
        ])
        self.assertEqual(result, 0)
        data = json.loads(out_file.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        ch = data[0]
        self.assertEqual(ch["chapterId"], "chapter-001")
        self.assertIn("title", ch)
        self.assertIn("wordCount", ch)
        self.assertIn("content", ch)
        self.assertGreater(ch["wordCount"], 0)

    def test_export_markdown_format(self):
        out_file = self.temp_dir / "output.md"
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "markdown",
            "--output", str(out_file),
        ])
        self.assertEqual(result, 0)
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("## ", content)
        self.assertNotIn("@{", content)

    def test_export_txt_default(self):
        out_file = self.temp_dir / "output.txt"
        result = main([
            "export", "--root", str(self.temp_dir),
            "--output", str(out_file),
        ])
        self.assertEqual(result, 0)
        content = out_file.read_text(encoding="utf-8")
        self.assertNotIn("## ", content)
        self.assertNotIn("@{", content)

    def test_export_strips_source_chapter_heading_from_body(self):
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章 停电夜\n\n"
            "但脑海中反复浮现的，始终是那道银色的剑光。\n",
            encoding="utf-8",
        )
        outline = json.loads((self.temp_dir / "outline.yaml").read_text(encoding="utf-8"))
        outline["chapters"][0]["title"] = "第一章 停电夜"
        (self.temp_dir / "outline.yaml").write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")

        out_file = self.temp_dir / "output.txt"
        result = main([
            "export", "--root", str(self.temp_dir),
            "--output", str(out_file),
        ])
        self.assertEqual(result, 0)
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("但脑海中反复浮现的，始终是那道银色的剑光。", content)
        self.assertNotIn("第一章 停电夜", content)


if __name__ == "__main__":
    unittest.main()
