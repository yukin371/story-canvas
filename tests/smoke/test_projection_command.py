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


class ProjectionCommandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-projection-"))
        with redirect_stdout(StringIO()):
            exit_code = main(
                [
                    "init",
                    "--root",
                    str(self.temp_dir),
                    "--title",
                    "Projection Harbor",
                    "--genre",
                    "Mystery",
                ]
            )
        self.assertEqual(exit_code, 0)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_projection_apply_ingests_non_conflicting_setting_candidates(self) -> None:
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n"
            "所谓“守夜回响”，就是夜巡人借力后残留在现场的追踪痕迹。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "logs" / "latest-analysis.yaml").write_text(
            json.dumps({"sceneScope": {"activeEntityIds": []}}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["projection", "apply", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["appliedPremiseFacts"], 1)

        worldbook = json.loads((self.temp_dir / "worldbook.yaml").read_text(encoding="utf-8"))
        self.assertEqual(worldbook["premiseFacts"][0]["label"], "守夜回响")
        self.assertIn("追踪痕迹", worldbook["premiseFacts"][0]["fact"])


if __name__ == "__main__":
    unittest.main()
