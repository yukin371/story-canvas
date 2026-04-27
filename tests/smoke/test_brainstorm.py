from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main


class BrainstormCommandTest(unittest.TestCase):
    def _write_incomplete_prd(self, root: Path) -> None:
        (root / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 读者钩子: TBD\n- 本章承接点: TBD\n",
            encoding="utf-8",
        )

    def test_brainstorm_character_random(self):
        result = main(["brainstorm", "character", "--random"])
        self.assertEqual(result, 0)

    def test_brainstorm_world_random(self):
        result = main(["brainstorm", "world", "--random"])
        self.assertEqual(result, 0)

    def test_brainstorm_outline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for d in ["chapters", "proposals", "reviews", "projections", "logs"]:
                (root / d).mkdir()
            for name, content in [
                ("project.yaml", '{"title":"test"}'),
                ("outline.yaml", '{"volumes":[],"chapters":[],"chapterDirections":[]}'),
                ("entities.yaml", '{"entities":[],"enrichmentProposals":[]}'),
                ("timeline.yaml", '{"events":[]}'),
                ("branches.yaml", '{"branches":[]}'),
                ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
                ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
                ("projections/projection.yaml", '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}'),
                ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
                ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
            ]:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(content + "\n", encoding="utf-8")

            buffer = StringIO()
            with redirect_stdout(buffer):
                result = main([
                    "brainstorm", "outline",
                    "--root", str(root),
                    "--volumes", "2",
                    "--chapters-per-volume", "3",
                ])
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
            self.assertEqual(payload["projectAdvisories"][0]["path"], "PRD.md")
            outline = json.loads((root / "outline.yaml").read_text(encoding="utf-8"))
            self.assertTrue(len(outline.get("volumes", [])) > 0)

    def test_brainstorm_outline_reports_incomplete_prd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for d in ["chapters", "proposals", "reviews", "projections", "logs"]:
                (root / d).mkdir()
            for name, content in [
                ("project.yaml", '{"title":"test"}'),
                ("outline.yaml", '{"volumes":[],"chapters":[],"chapterDirections":[]}'),
                ("entities.yaml", '{"entities":[],"enrichmentProposals":[]}'),
                ("timeline.yaml", '{"events":[]}'),
                ("branches.yaml", '{"branches":[]}'),
                ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
                ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
                ("projections/projection.yaml", '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}'),
                ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
                ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
            ]:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(content + "\n", encoding="utf-8")
            self._write_incomplete_prd(root)

            buffer = StringIO()
            with redirect_stdout(buffer):
                result = main([
                    "brainstorm", "outline",
                    "--root", str(root),
                    "--volumes", "1",
                    "--chapters-per-volume", "2",
                ])
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
            self.assertIn("卷目标", payload["projectAdvisories"][0]["message"])


if __name__ == "__main__":
    unittest.main()
