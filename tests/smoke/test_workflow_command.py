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


class WorkflowCommandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-workflow-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_json(self, args: list[str]) -> tuple[int, dict]:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(args)
        return exit_code, json.loads(buffer.getvalue())

    def _init_project(self, *, ready_project_gate: bool = False) -> None:
        args = [
            "init",
            "--root",
            str(self.temp_dir),
            "--title",
            "雾港",
            "--genre",
            "mystery",
        ]
        if ready_project_gate:
            args += [
                "--primary-genre",
                "mystery",
                "--target-audience",
                "suspense-reader",
                "--core-promise",
                "案件持续反转",
                "--pace-contract",
                "中快节奏",
            ]
        exit_code, _ = self._run_json(args)
        self.assertEqual(exit_code, 0)

    def _make_outline_ready(self) -> None:
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["chapters"][0]["direction"] = "主角在雨夜仓库发现关键证物"
        outline["chapters"][0]["beats"] = [
            {"id": "beat-001", "summary": "进入仓库", "status": "planned"}
        ]
        outline["chapters"][0]["scenePlans"] = [
            {
                "id": "scene-001",
                "title": "仓库追查",
                "summary": "雨夜仓库中的第一次发现",
                "startParagraph": 1,
                "endParagraph": 2,
            }
        ]
        outline["chapterDirections"] = [
            {
                "chapterId": "chapter-001",
                "title": "第一章方向",
                "summary": "主角在雨夜仓库发现关键证物",
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_chapter(self) -> None:
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "林舟推开仓库铁门，雨水顺着衣角往下淌。墙角的木箱被人撬开，露出半截烧焦的账册。\n\n"
            "他刚弯腰去捡，门外就传来急促脚步声。有人停在门口，没有进来，只把手电光压在他的肩背上。\n",
            encoding="utf-8",
        )

    def _prepare_review_ready_project(self) -> None:
        self._init_project(ready_project_gate=True)
        self._make_outline_ready()
        self._write_chapter()

    def test_workflow_status_infers_project_contract_without_workflow_file(self) -> None:
        self._init_project(ready_project_gate=False)

        exit_code, payload = self._run_json(["workflow", "status", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["workflowFileExists"])
        self.assertEqual(payload["currentStage"], "project_contract")
        self.assertEqual(payload["inferredCurrentStage"], "project_contract")
        self.assertEqual(payload["workflowStatus"], "in_progress")
        self.assertFalse(payload["stageResults"]["project_contract"]["completed"])
        self.assertEqual(payload["currentGateDecision"]["gateId"], "project_contract")
        self.assertIn("missing-target-audience", payload["currentGateDecision"]["blockingRules"])
        self.assertTrue(payload["currentRuleJudgements"])

    def test_workflow_run_persists_workflow_yaml(self) -> None:
        self._init_project(ready_project_gate=True)

        exit_code, payload = self._run_json(
            ["workflow", "run", "--root", str(self.temp_dir), "--non-interactive"]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["saved"])
        self.assertEqual(payload["mode"], "non-interactive")
        self.assertEqual(payload["workflow"]["currentStage"], "outline_ready")

        workflow_path = self.temp_dir / "workflow.yaml"
        self.assertTrue(workflow_path.exists())
        saved = json.loads(workflow_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["currentStage"], "outline_ready")
        self.assertEqual(saved["workflowStatus"], "in_progress")
        self.assertEqual(saved["lastRunMode"], "non-interactive")

    def test_workflow_advance_accepts_gates_in_order(self) -> None:
        self._prepare_review_ready_project()

        exit_code, payload = self._run_json(["workflow", "run", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["workflow"]["currentStage"], "chapter_review_ready")

        exit_code, _ = self._run_json(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(exit_code, 0)
        exit_code, _ = self._run_json(["review", "chapter", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(exit_code, 0)

        exit_code, payload = self._run_json(
            ["workflow", "advance", "--root", str(self.temp_dir), "--gate", "chapter_review_ready", "--decision", "accept"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["currentStage"], "scene_review_ready")

        exit_code, _ = self._run_json(
            ["review", "scene", "--root", str(self.temp_dir), "--chapter-id", "chapter-001", "--scene-index", "1"]
        )
        self.assertEqual(exit_code, 0)

        exit_code, payload = self._run_json(
            ["workflow", "advance", "--root", str(self.temp_dir), "--gate", "scene_review_ready", "--decision", "accept"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["currentStage"], "export_ready")

        exit_code, payload = self._run_json(
            ["workflow", "advance", "--root", str(self.temp_dir), "--gate", "export_ready", "--decision", "accept"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["workflowStatus"], "completed")
        self.assertEqual(payload["workflow"]["workflowStatus"], "completed")
        self.assertEqual(len(payload["workflow"]["gateHistory"]), 3)

    def test_workflow_advance_modify_and_reset(self) -> None:
        self._prepare_review_ready_project()

        exit_code, _ = self._run_json(
            ["workflow", "run", "--root", str(self.temp_dir), "--resume-from", "outline_ready"]
        )
        self.assertEqual(exit_code, 0)

        exit_code, payload = self._run_json(
            [
                "workflow",
                "advance",
                "--root",
                str(self.temp_dir),
                "--gate",
                "outline_ready",
                "--decision",
                "modify",
                "--feedback",
                "补一层场景张力",
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["workflowStatus"], "needs_changes")
        self.assertEqual(payload["currentStage"], "outline_ready")
        self.assertEqual(payload["workflow"]["stageResults"]["outline_ready"]["feedback"], "补一层场景张力")

        exit_code, payload = self._run_json(
            ["workflow", "reset", "--root", str(self.temp_dir), "--from-gate", "outline_ready"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["currentStage"], "outline_ready")
        self.assertEqual(payload["workflowStatus"], "in_progress")
        self.assertFalse("lastDecision" in payload["workflow"]["stageResults"]["outline_ready"])
        self.assertEqual(payload["workflow"]["gateHistory"], [])

    def test_workflow_run_resume_from_rewinds_current_stage(self) -> None:
        self._prepare_review_ready_project()

        exit_code, payload = self._run_json(
            ["workflow", "run", "--root", str(self.temp_dir), "--resume-from", "outline_ready"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["workflow"]["currentStage"], "outline_ready")
        self.assertEqual(payload["workflow"]["workflowStatus"], "in_progress")

    def test_workflow_export_writes_snapshot(self) -> None:
        self._init_project(ready_project_gate=True)
        exit_code, _ = self._run_json(["workflow", "run", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)

        output_path = self.temp_dir / "workflow-export.json"
        exit_code, payload = self._run_json(
            ["workflow", "export", "--root", str(self.temp_dir), "--output", str(output_path)]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(output_path.exists())
        saved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["currentStage"], payload["currentStage"])
        self.assertIn("stageResults", saved)
        self.assertIn("currentGateDecision", saved)

    def test_workflow_advance_rejects_incomplete_gate(self) -> None:
        self._init_project(ready_project_gate=True)
        exit_code, _ = self._run_json(["workflow", "run", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit):
                main(
                    [
                        "workflow",
                        "advance",
                        "--root",
                        str(self.temp_dir),
                        "--gate",
                        "outline_ready",
                        "--decision",
                        "accept",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
