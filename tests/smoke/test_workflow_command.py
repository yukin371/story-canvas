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

    def _write_incomplete_prd(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 读者钩子: TBD\n- 本章承接点: TBD\n",
            encoding="utf-8",
        )

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

    def _prepare_volume_gate_project(self) -> None:
        self._init_project(ready_project_gate=True)
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["chapters"] = []
        outline["chapterDirections"] = []
        outline["volumes"] = [
            {
                "id": "volume-001",
                "title": "第一卷",
                "theme": "命火初现",
                "chapters": [
                    {"id": "chapter-001", "title": "入山", "status": "draft"},
                    {"id": "chapter-002", "title": "压火", "status": "draft"},
                ],
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        entities_path = self.temp_dir / "entities.yaml"
        entities = json.loads(entities_path.read_text(encoding="utf-8"))
        entities["entities"] = [
            {
                "id": "char-linzhou",
                "name": "林舟",
                "type": "character",
                "aliases": [],
                "state": {
                    "powerLevel": {
                        "publicLevel": "灵动境",
                    }
                },
            }
        ]
        entities_path.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [],
                    "worldRules": [],
                    "powerProgressions": [],
                    "factions": [
                        {
                            "id": "faction-qingyun",
                            "name": "青云宗",
                            "summary": "本地中型宗门",
                        }
                    ],
                    "locations": [],
                    "artifacts": [],
                    "mysteries": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.temp_dir / "foreshadowing.yaml").write_text(
            json.dumps(
                {
                    "foreshadows": [
                        {
                            "id": "fs-001",
                            "title": "山门旧印",
                            "plannedPayoffChapter": "chapter-001",
                            "status": "planted",
                            "payoffPoints": [],
                        },
                        {
                            "id": "fs-002",
                            "title": "压火真相",
                            "payoffPlan": {
                                "window": {
                                    "type": "short",
                                    "targetChapterStart": "chapter-001",
                                    "targetChapterEnd": "chapter-002",
                                }
                            },
                            "status": "planted",
                            "payoffPoints": [],
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 第二章\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )

    def _prepare_clean_volume_project(self) -> None:
        self._init_project(ready_project_gate=True)
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["chapters"] = []
        outline["chapterDirections"] = []
        outline["volumes"] = [
            {
                "id": "volume-001",
                "title": "第一卷",
                "theme": "残灯初鸣",
                "chapters": [
                    {"id": "chapter-001", "title": "灯尽人未绝", "status": "completed"},
                    {"id": "chapter-002", "title": "灰里递名", "status": "completed"},
                ],
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "foreshadowing.yaml").write_text('{"foreshadows":[]}\n', encoding="utf-8")
        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [],
                    "worldRules": [],
                    "powerProgressions": [],
                    "factions": [],
                    "locations": [],
                    "artifacts": [],
                    "mysteries": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n他在废棚里熬过第一夜。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 第二章\n\n第二天一早，他决定先稳住局面。\n",
            encoding="utf-8",
        )

    def _write_volume_self_review(self, *, allow_human_review: bool, closure_status: str = "closed", chapter_handoff_score: int = 4) -> None:
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T10:00:00+08:00",
                    "conclusion": {
                        "closureStatus": closure_status,
                        "allowHumanReview": allow_human_review,
                        "strongestPoint": "承接稳定",
                        "biggestRisk": "世界解释仍可继续补强",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 4, "conclusion": "小闭环已成立"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "基本可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "底层逻辑可接受"},
                        {"dimensionId": "chapterHandoff", "score": chapter_handoff_score, "conclusion": "章间承接稳定"},
                        {"dimensionId": "characterContinuity", "score": 4, "conclusion": "角色连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手基本成立"},
                        {"dimensionId": "conflictEscalation", "score": 4, "conclusion": "冲突抬升正常"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "兑现成立"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔节奏可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "风格可读"},
                    ],
                    "issues": [
                        {
                            "issue": "世界解释仍偏少",
                            "evidence": ["底层规则解释还可以更早交付"],
                            "impact": "读者理解成本略高",
                            "primaryCause": "self_review_miss",
                            "fixAction": "补一段制度代价解释",
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "主角能否从死局中拿到第一层主动",
                        "delivered": ["主角活下来", "拿到一条主动线索"],
                        "missing": [],
                        "reasoning": "本卷已形成可交付的小闭环。",
                    },
                    "repairSuggestions": ["补一处底层规则解释"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        exit_code, _ = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
            ]
        )
        self.assertEqual(exit_code, 0)

    def test_workflow_status_infers_project_contract_without_workflow_file(self) -> None:
        self._init_project(ready_project_gate=False)

        exit_code, payload = self._run_json(["workflow", "status", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["workflowFileExists"])
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["currentStage"], "project_contract")
        self.assertEqual(payload["inferredCurrentStage"], "project_contract")
        self.assertEqual(payload["workflowStatus"], "in_progress")
        self.assertFalse(payload["stageResults"]["project_contract"]["completed"])
        self.assertEqual(payload["currentGateDecision"]["gateId"], "project_contract")
        self.assertIn("missing-target-audience", payload["currentGateDecision"]["blockingRules"])
        self.assertTrue(payload["currentRuleJudgements"])
        target_audience_rule = next(
            item for item in payload["currentRuleJudgements"] if item.get("ruleId") == "missing-target-audience"
        )
        self.assertEqual(target_audience_rule["source"], "core")
        self.assertEqual(target_audience_rule["scope"], "project")
        self.assertEqual(target_audience_rule["kind"], "gate")
        self.assertIn("project-gate", target_audience_rule["tags"])
        self.assertIn("project_contract", target_audience_rule["tags"])
        outline_rule = next(
            item
            for item in payload["stageResults"]["outline_ready"]["ruleJudgements"]
            if item.get("ruleId") == "project-missing-target-audience"
        )
        self.assertEqual(outline_rule["source"], "core")
        self.assertEqual(outline_rule["scope"], "chapter")
        self.assertEqual(outline_rule["kind"], "gate")
        self.assertIn("project-gate", outline_rule["tags"])
        self.assertIn("outline_ready", outline_rule["tags"])

    def test_workflow_status_reports_missing_project_prd_as_advisory(self) -> None:
        self._init_project(ready_project_gate=True)
        (self.temp_dir / "PRD.md").unlink()

        exit_code, payload = self._run_json(["workflow", "status", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(payload["projectAdvisories"]), 1)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["projectAdvisories"][0]["severity"], "warning")
        self.assertEqual(payload["projectAdvisories"][0]["path"], "PRD.md")
        self.assertIn("立项/卷职责文档入口", payload["projectAdvisories"][0]["message"])

    def test_workflow_status_reports_incomplete_project_prd_as_advisory(self) -> None:
        self._init_project(ready_project_gate=True)
        self._write_incomplete_prd()

        exit_code, payload = self._run_json(["workflow", "status", "--root", str(self.temp_dir)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["projectAdvisories"][0]["severity"], "warning")
        self.assertIn("卷目标", payload["projectAdvisories"][0]["message"])

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
        self.assertEqual(saved["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

    def test_workflow_export_reports_missing_project_prd_as_advisory(self) -> None:
        self._init_project(ready_project_gate=True)
        (self.temp_dir / "PRD.md").unlink()

        output_path = self.temp_dir / "workflow-export.json"
        exit_code, payload = self._run_json(
            ["workflow", "export", "--root", str(self.temp_dir), "--output", str(output_path)]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        saved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["projectAdvisories"][0]["ruleId"], "missing-project-prd")

    def test_workflow_status_supports_volume_scope(self) -> None:
        self._prepare_volume_gate_project()

        exit_code, payload = self._run_json(
            ["workflow", "status", "--root", str(self.temp_dir), "--volume-id", "volume-001"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["scope"], "volume")
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["workflowKind"], "volume_preflight_gate")
        self.assertEqual(payload["volumeId"], "volume-001")
        self.assertEqual(payload["currentStage"], "volume_tooling_gate")
        self.assertEqual(payload["workflowStatus"], "in_progress")
        self.assertFalse(payload["workflowFileExists"])
        self.assertEqual(payload["volumeStructureCheck"]["role"], "intro-volume")
        self.assertEqual(payload["volumeStructureCheck"]["summary"]["missingCount"], 1)
        self.assertEqual(payload["preflightSummary"]["mentionActionCount"], 5)
        self.assertIn("volume-mention-hygiene-pending", payload["currentGateDecision"]["blockingRules"])
        self.assertTrue(payload["currentRuleJudgements"])
        self.assertTrue(payload["changeRequestDrafts"])
        self.assertEqual(payload["changeRequestDrafts"][0]["kind"], "volume_workflow")
        self.assertIn("volume-mention-hygiene-pending", payload["changeRequestDrafts"][0]["title"])
        self.assertEqual(payload["changeRequestDrafts"][0]["targetIds"], ["chapter-001", "chapter-002"])
        self.assertTrue(any("岳池" in item or "青云宗" in item for item in payload["changeRequestDrafts"][0]["evidence"]))
        self.assertTrue(
            any(
                item["suggestedPayload"].get("checkId") == "outline-coverage"
                and item["targetIds"] == ["chapter-001", "chapter-002"]
                for item in payload["changeRequestDrafts"]
            )
        )

    def test_workflow_volume_scope_reports_missing_project_prd_as_advisory(self) -> None:
        self._prepare_volume_gate_project()
        (self.temp_dir / "PRD.md").unlink()

        exit_code, payload = self._run_json(
            ["workflow", "status", "--root", str(self.temp_dir), "--volume-id", "volume-001"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["projectAdvisories"][0]["path"], "PRD.md")

    def test_workflow_export_supports_volume_scope(self) -> None:
        self._prepare_volume_gate_project()

        output_path = self.temp_dir / "workflow-volume-export.json"
        exit_code, payload = self._run_json(
            [
                "workflow",
                "export",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--output",
                str(output_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(output_path.exists())
        saved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["scope"], "volume")
        self.assertEqual(saved["currentStage"], payload["currentStage"])
        self.assertIn("preflight", saved)
        self.assertEqual(saved["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

    def test_workflow_volume_scope_requires_self_review_after_tooling_gate(self) -> None:
        self._prepare_clean_volume_project()

        exit_code, payload = self._run_json(
            ["workflow", "status", "--root", str(self.temp_dir), "--volume-id", "volume-001"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["currentStage"], "human_review_ready")
        self.assertEqual(payload["workflowStatus"], "in_progress")
        self.assertFalse(payload["latestVolumeSelfReview"])
        self.assertEqual(payload["volumeStructureCheck"]["summary"]["missingCount"], 1)
        self.assertEqual(payload["preflightSummary"]["mentionActionCount"], 0)
        self.assertIn("missing-volume-self-review", payload["currentGateDecision"]["blockingRules"])
        self.assertEqual(payload["volumeSelfReview"]["repairCoverageStatus"], "")
        self.assertEqual(payload["volumeSelfReview"]["weakDimensionLabels"], [])
        self.assertEqual(payload["volumeSelfReview"]["uncoveredWeakDimensionLabels"], [])
        self.assertTrue(payload["changeRequestDrafts"])
        self.assertTrue(
            any(
                item["suggestedPayload"].get("checkId") == "outline-coverage"
                and item["summary"].startswith("当前卷仅")
                for item in payload["changeRequestDrafts"]
            )
        )

    def test_workflow_volume_scope_completes_after_passing_self_review(self) -> None:
        self._prepare_clean_volume_project()
        self._write_volume_self_review(allow_human_review=True)

        exit_code, payload = self._run_json(
            ["workflow", "status", "--root", str(self.temp_dir), "--volume-id", "volume-001"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["currentStage"], "human_review_ready")
        self.assertEqual(payload["workflowStatus"], "completed")
        self.assertTrue(payload["volumeSelfReview"]["present"])
        self.assertTrue(payload["volumeSelfReview"]["finalAllowHumanReview"])
        self.assertEqual(payload["volumeSelfReview"]["repairCoverageStatus"], "complete")
        self.assertEqual(payload["volumeSelfReview"]["weakDimensionLabels"], [])
        self.assertEqual(payload["volumeSelfReview"]["uncoveredWeakDimensionLabels"], [])
        self.assertEqual(payload["currentGateDecision"]["status"], "ready")
        self.assertEqual(payload["changeRequestDrafts"], [])

    def test_workflow_volume_scope_blocks_incomplete_repair_coverage(self) -> None:
        self._prepare_clean_volume_project()
        (self.temp_dir / "reviews" / "story-reviews.yaml").write_text(
            json.dumps(
                {
                    "rubricVersion": "chapter-review-v1",
                    "sceneRubricVersion": "scene-review-v1",
                    "volumeSelfReviewRubricVersion": "volume-self-review-v1",
                    "chapterReviews": [],
                    "sceneReviews": [],
                    "volumeSelfReviews": [
                        {
                            "rubricVersion": "volume-self-review-v1",
                            "volumeId": "volume-001",
                            "volumeTitle": "第一卷",
                            "generatedAt": "2026-04-27T10:00:00+08:00",
                            "conclusion": {
                                "closureStatus": "closed",
                                "allowHumanReview": False,
                                "strongestPoint": "卷级闭环成立",
                                "biggestRisk": "章间承接仍有断裂风险",
                            },
                            "scores": [],
                            "closureAssessment": {
                                "mainProblem": "章间承接仍需补强",
                                "delivered": ["主线小闭环已成立"],
                                "missing": [],
                                "reasoning": "可以继续修，但当前版本不宜进入人工审查。",
                            },
                            "repairSuggestions": ["补一段 12-13 章之间的过渡承接"],
                            "acceptedRisks": [],
                            "gateFailures": [],
                            "finalAllowHumanReview": False,
                            "scoreSummary": {
                                "average": 3.0,
                                "lowestScore": 2,
                                "lowestDimensions": ["章间承接"],
                                "strongestDimension": {"dimensionId": "volumeClosure", "label": "卷级闭环", "score": 4},
                            },
                            "repairCoverage": {
                                "weakDimensionIds": ["chapterHandoff"],
                                "weakDimensionLabels": ["章间承接"],
                                "uncoveredWeakDimensionIds": ["chapterHandoff"],
                                "uncoveredWeakDimensionLabels": ["章间承接"],
                                "issueCount": 1,
                                "repairSuggestionCount": 1,
                                "status": "incomplete",
                            },
                            "issues": [
                                {
                                    "issue": "第 12 章到第 13 章之间缺少过渡承接",
                                    "evidence": ["主角上一章做出的选择没有在下一章开头形成直接后果"],
                                    "impact": "读者会感到剧情断裂",
                                    "primaryCause": "generation_miss",
                                    "fixAction": "补一段承接段，明确上一章余波如何落到下一章",
                                    "chapterRefs": [],
                                    "evidenceRefs": ["chapter-002#paragraph-4"],
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            ["workflow", "status", "--root", str(self.temp_dir), "--volume-id", "volume-001"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["currentStage"], "human_review_ready")
        self.assertEqual(payload["workflowStatus"], "in_progress")
        self.assertEqual(payload["volumeSelfReview"]["repairCoverageStatus"], "incomplete")
        self.assertEqual(payload["volumeSelfReview"]["weakDimensionLabels"], ["章间承接"])
        self.assertEqual(payload["volumeSelfReview"]["uncoveredWeakDimensionLabels"], ["章间承接"])
        self.assertIn(
            "volume-self-review-repair-coverage-incomplete",
            payload["currentGateDecision"]["blockingRules"],
        )
        self.assertIn("章间承接", payload["currentGateDecision"]["notes"][0])
        self.assertIn("章间承接", payload["currentRuleJudgements"][0]["message"])
        self.assertTrue(payload["changeRequestDrafts"])
        self.assertEqual(payload["changeRequestDrafts"][0]["kind"], "volume_workflow")
        self.assertIn("章间承接", payload["changeRequestDrafts"][0]["summary"])
        self.assertTrue(any(item["summary"] == "补一段 12-13 章之间的过渡承接" for item in payload["changeRequestDrafts"]))
        self.assertTrue(payload["changeRequestDrafts"][0]["evidence"])
        self.assertEqual(payload["changeRequestDrafts"][0]["targetIds"], ["chapter-002"])
        self.assertIn("chapter-002#paragraph-4", payload["changeRequestDrafts"][0]["evidence"][0])

    def test_workflow_run_rejects_volume_scope_for_now(self) -> None:
        self._prepare_volume_gate_project()

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit):
                main(
                    [
                        "workflow",
                        "run",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                    ]
                )

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
