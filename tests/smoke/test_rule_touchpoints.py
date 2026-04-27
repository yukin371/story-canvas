from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_rule_touchpoints import analyze_staged_files


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_rule_touchpoints.py"


class RuleTouchpointAnalysisTests(unittest.TestCase):
    def test_reports_service_rule_hint(self) -> None:
        hints, warnings = analyze_staged_files(
            [
                "src/story_harness_cli/services/story_review.py",
                "tests/smoke/test_review_chapter.py",
            ]
        )
        self.assertTrue(any("services 层" in item for item in hints))
        self.assertTrue(any("services/MODULE.md" in item for item in warnings))

    def test_suppresses_doc_sync_warning_when_docs_are_staged(self) -> None:
        hints, warnings = analyze_staged_files(
            [
                "src/story_harness_cli/protocol/schema.py",
                "docs/PROJECT_PROFILE.md",
            ]
        )
        self.assertTrue(any("protocol 层" in item for item in hints))
        self.assertFalse(warnings)


class RuleTouchpointScriptTests(unittest.TestCase):
    def test_script_prints_touchpoint_summary(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
            handle.write("src/story_harness_cli/commands/export.py\n")
            temp_path = Path(handle.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--staged-file-list", str(temp_path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[rule-touchpoints]", result.stdout)
        self.assertIn("commands 层", result.stdout)
