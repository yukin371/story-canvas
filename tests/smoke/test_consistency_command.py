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


class ConsistencyCommandTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-consistency-"))
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

    def test_consistency_check_runs(self):
        result = main([
            "consistency", "check",
            "--root", str(self.temp_dir),
            "--chapter-id", "chapter-001",
        ])
        self.assertEqual(result, 0)
        check_file = self.temp_dir / "projections" / "consistency-check-chapter-001.yaml"
        self.assertTrue(check_file.exists())
        data = json.loads(check_file.read_text(encoding="utf-8"))
        self.assertIn("hardChecks", data)
        self.assertIn("softChecks", data)
        self.assertIn("settingCandidates", data)
        self.assertIn("settingConflicts", data)
        self.assertIn("judgements", data)
        self.assertIn("contextForAI", data)


if __name__ == "__main__":
    unittest.main()
