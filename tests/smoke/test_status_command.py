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


class StatusCommandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-status-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_incomplete_prd(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 压制源与预期爆发点: TBD\n- 本章交付点: TBD\n",
            encoding="utf-8",
        )

    def _run_json(self, args: list[str]) -> tuple[int, dict]:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(args)
        return exit_code, json.loads(buffer.getvalue())

    def _write_json(self, relative_path: str, payload: dict) -> None:
        target = self.temp_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _init_project(self) -> None:
        exit_code, _ = self._run_json(
            [
                "init",
                "--root",
                str(self.temp_dir),
                "--title",
                "命灯照骨",
                "--genre",
                "xuanhuan",
                "--primary-genre",
                "xuanhuan",
                "--target-audience",
                "web-serial-reader",
                "--core-promise",
                "死局求生",
                "--pace-contract",
                "中快节奏",
                "--chapter-id",
                "chapter-001",
                "--chapter-title",
                "灯尽人未绝",
            ]
        )
        self.assertEqual(exit_code, 0)

    def _init_project_with_completed_prd(self) -> None:
        exit_code, _ = self._run_json(
            [
                "init",
                "--root",
                str(self.temp_dir),
                "--title",
                "命灯照骨",
                "--genre",
                "xuanhuan",
                "--primary-genre",
                "xuanhuan",
                "--target-audience",
                "web-serial-reader",
                "--core-promise",
                "死局求生",
                "--pace-contract",
                "中快节奏",
                "--chapter-id",
                "chapter-001",
                "--chapter-title",
                "灯尽人未绝",
                "--hook-line",
                "看主角如何把必死工位撬成第一层主动资格",
                "--volume-goal",
                "第一卷完成主角脱离旧势力控制，并建立第一层主动权。",
                "--suppression-source",
                "青云宗以压火制度榨取底层弟子，主角必须先活下来再找反制机会。",
                "--onboarding-focus",
                "命灯、压火制度、宗门层级与主角为何不能轻易脱离。",
                "--chapter-handoff",
                "从主角即将被送去压火的处境切入。",
                "--chapter-delivery",
                "让读者理解命灯危险，并留下主角第一次反抗的钩子。",
            ]
        )
        self.assertEqual(exit_code, 0)

    def test_status_aggregates_project_chapter_review_and_workflow_state(self) -> None:
        self._init_project()
        self._write_json(
            "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "残灯初鸣",
                        "chapters": [
                            {
                                "id": "chapter-001",
                                "title": "灯尽人未绝",
                                "status": "draft",
                                "direction": "立住死局，并抛出残灯代价。",
                                "beats": [
                                    {"id": "beat-001", "summary": "死局开场", "status": "completed"},
                                    {"id": "beat-002", "summary": "残灯异动", "status": "planned"},
                                ],
                                "scenePlans": [
                                    {
                                        "id": "scene-001",
                                        "title": "废棚等死",
                                        "summary": "立住死局。",
                                        "startParagraph": 1,
                                        "endParagraph": 2,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n"
            "沈照在废棚里等死。\n\n"
            "旧灯芯忽然回亮了一线。\n",
            encoding="utf-8",
        )
        self._write_json(
            "reviews/change-requests.yaml",
            {
                "changeRequests": [
                    {"id": "cr-001", "status": "pending", "title": "强化章末钩子"},
                    {"id": "cr-002", "status": "accepted", "title": "补足命灯解释"},
                ]
            },
        )
        self._write_json(
            "reviews/story-reviews.yaml",
            {
                "rubricVersion": "chapter-review-v1",
                "sceneRubricVersion": "scene-review-v1",
                "chapterReviews": [
                    {
                        "reviewId": "chapter-review-001",
                        "chapterId": "chapter-001",
                        "chapterTitle": "灯尽人未绝",
                        "generatedAt": "2026-04-27T12:00:00+08:00",
                        "summary": "死局和代价感已经立住，章末追读还可再狠一点。",
                        "rating": "solid",
                        "scores": {"total": 82},
                        "weightedScores": {"total": 83.2},
                        "priorityActions": ["强化章末追读问题", "补足命灯规则解释"],
                        "ruleJudgements": [{"ruleId": "chapter-handoff-weak"}],
                        "styleAnalysis": {
                            "profile": "xuanhuan-zh",
                            "profileSource": "builtin",
                            "styleAnalysis": {
                                "overallScore": 91,
                                "totalDeduction": 3,
                                "summary": "检测到 1 项轻度风格问题。",
                                "patternResults": [
                                    {"id": "registerDrift", "label": "语域漂移", "detected": True},
                                    {"id": "narrativeFrameRepetition", "label": "支架句复用", "detected": False},
                                ],
                            },
                        },
                        "consistencySignals": {
                            "settingCandidates": [{"label": "命灯"}],
                            "settingConflicts": [{"issue": "命灯代价未完全解释"}],
                            "unintroducedNameReveals": [],
                            "capabilityTaskRisks": [],
                            "powerProgressionConflicts": [],
                        },
                    }
                ],
                "sceneReviews": [
                    {
                        "reviewId": "scene-review-001",
                        "chapterId": "chapter-001",
                        "generatedAt": "2026-04-27T12:03:00+08:00",
                        "summary": "场景推进明确。",
                        "rating": "solid",
                        "scores": {"total": 79},
                        "sceneRange": {
                            "sceneIndex": 1,
                            "startParagraph": 1,
                            "endParagraph": 2,
                        },
                    }
                ],
                "volumeSelfReviews": [
                    {
                        "rubricVersion": "volume-self-review-v1",
                        "volumeId": "volume-001",
                        "volumeTitle": "第一卷",
                        "generatedAt": "2026-04-27T12:10:00+08:00",
                        "conclusion": {
                            "closureStatus": "closed",
                            "allowHumanReview": True,
                            "strongestPoint": "死局和承接都成立",
                            "biggestRisk": "命灯规则解释仍略薄",
                        },
                        "scores": [],
                        "issues": [],
                        "closureAssessment": {},
                        "repairSuggestions": ["补一处命灯规则解释"],
                        "acceptedRisks": [],
                        "gateFailures": [],
                        "finalAllowHumanReview": True,
                        "scoreSummary": {
                            "average": 3.6,
                            "lowestScore": 3,
                            "lowestDimensions": ["世界与制度逻辑"],
                            "strongestDimension": {"dimensionId": "volumeClosure", "label": "卷级闭环", "score": 4},
                        },
                    }
                ],
            },
        )
        self._write_json(
            "projections/context-lens.yaml",
            {
                "currentChapterId": "chapter-001",
                "lenses": [
                    {
                        "chapterId": "chapter-001",
                        "chapterTitle": "灯尽人未绝",
                        "activeCharacters": [{"id": "char-shenzhao", "name": "沈照"}],
                        "activeRelations": [],
                        "dueForeshadows": [{"id": "fs-001", "description": "残灯为什么回亮"}],
                        "pendingChangeRequestCount": 1,
                        "chapterHandoff": {"previousChapter": {"id": ""}},
                        "updatedAt": "2026-04-27T12:05:00+08:00",
                    }
                ],
            },
        )
        self._write_json(
            "projections/consistency-check-chapter-001.yaml",
            {
                "checkedAt": "2026-04-27T12:06:00+08:00",
                "hardChecks": {
                    "stateContradictions": [{"issue": "状态矛盾"}],
                    "relationContradictions": [],
                },
                "softChecks": {
                    "outlineDeviations": [{"issue": "细纲兑现略弱"}],
                },
                "settingCandidates": [{"label": "命灯"}],
                "settingConflicts": [{"issue": "命灯规则未解释透"}],
                "unintroducedNameReveals": [],
                "capabilityTaskRisks": [],
                "powerProgressionConflicts": [],
                "judgements": [],
                "contextForAI": {},
            },
        )

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"]["title"], "命灯照骨")
        self.assertEqual(payload["project"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["targetVolume"]["volumeId"], "volume-001")
        self.assertEqual(payload["targetChapter"]["chapterId"], "chapter-001")
        self.assertTrue(payload["targetChapter"]["scenePlanStatus"]["valid"])
        self.assertTrue(payload["context"]["exists"])
        self.assertEqual(payload["context"]["dueForeshadowCount"], 1)
        self.assertTrue(payload["reviewStatus"]["volumeSelfReview"]["exists"])
        self.assertTrue(payload["reviewStatus"]["volumeSelfReview"]["finalAllowHumanReview"])
        self.assertTrue(payload["reviewStatus"]["chapterReview"]["exists"])
        self.assertEqual(payload["reviewStatus"]["chapterReview"]["totalScore"], 82)
        self.assertEqual(payload["reviewStatus"]["sceneReviews"]["count"], 1)
        self.assertEqual(payload["reviewStatus"]["style"]["overallScore"], 91)
        self.assertEqual(payload["reviewStatus"]["consistency"]["source"], "check-file")
        self.assertEqual(payload["reviewStatus"]["consistency"]["hardConflictCount"], 1)
        self.assertEqual(payload["workflow"]["currentStage"], "export_ready")
        self.assertEqual(payload["workflow"]["workflowStatus"], "completed")
        self.assertEqual(payload["workflow"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

    def test_status_reports_missing_project_prd_as_advisory(self) -> None:
        self._init_project()
        (self.temp_dir / "PRD.md").unlink()

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"]["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["project"]["projectAdvisories"][0]["path"], "PRD.md")
        self.assertEqual(payload["workflow"]["projectAdvisories"][0]["ruleId"], "missing-project-prd")

    def test_status_reports_incomplete_project_prd_as_advisory(self) -> None:
        self._init_project()
        self._write_incomplete_prd()

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertIn("压制源与预期爆发点", payload["project"]["projectAdvisories"][0]["message"])
        self.assertEqual(payload["workflow"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")

    def test_status_hides_prd_advisories_when_init_seeded_them(self) -> None:
        self._init_project_with_completed_prd()

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"]["projectAdvisories"], [])
        self.assertEqual(payload["workflow"]["projectAdvisories"], [])

    def test_status_exposes_review_rule_config_summary(self) -> None:
        self._init_project()
        (self.temp_dir / "review-rules.yaml").write_text(
            json.dumps(
                {
                    "activeProfile": "novel-meta",
                    "profiles": {
                        "novel-meta": {
                            "enabledRules": ["metaLeakage", "povOverreach"],
                            "exemptions": [
                                {
                                    "ruleId": "metaLeakage",
                                    "scope": {"chapterIds": ["chapter-012"]},
                                    "allowWhen": {"quotedOnly": True},
                                    "reason": "主角讨论书中书章节",
                                }
                            ],
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir)])

        self.assertEqual(exit_code, 0)
        review_rule_config = payload["project"]["reviewRuleConfig"]
        self.assertTrue(review_rule_config["exists"])
        self.assertEqual(review_rule_config["requestedProfile"], "novel-meta")
        self.assertEqual(review_rule_config["resolvedProfile"], "novel-meta")
        self.assertEqual(review_rule_config["profileSource"], "project")
        self.assertEqual(review_rule_config["enabledRuleCount"], 2)
        self.assertEqual(review_rule_config["exemptionCount"], 1)

    def test_status_supports_volume_scope_with_volume_self_review_and_gate_summary(self) -> None:
        self._init_project()
        self._write_json(
            "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "残灯初鸣",
                        "chapters": [
                            {"id": "chapter-001", "title": "灯尽人未绝", "status": "completed"},
                            {"id": "chapter-002", "title": "灰里递名", "status": "completed"},
                        ],
                    }
                ],
            },
        )
        self._write_json("foreshadowing.yaml", {"foreshadows": []})
        self._write_json(
            "worldbook.yaml",
            {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text("# 灯尽人未绝\n\n他熬过第一夜。\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-002.md").write_text("# 灰里递名\n\n第二天局势暂稳。\n", encoding="utf-8")
        self._write_json(
            "reviews/story-reviews.yaml",
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
                        "generatedAt": "2026-04-27T13:00:00+08:00",
                        "conclusion": {
                            "closureStatus": "closed",
                            "allowHumanReview": True,
                            "strongestPoint": "章间承接稳定",
                            "biggestRisk": "世界规则解释仍偏薄",
                        },
                        "editorPass": {
                            "completed": True,
                            "reviewerRole": "editor",
                            "mode": "independent_agent",
                            "contextIsolation": "no_context_proxy",
                            "notes": "独立编辑已完成评分。",
                        },
                        "editorAssessment": {
                            "overallVerdict": "pass",
                            "summaryComment": "独立编辑认为可进入人工审查。",
                            "topProblems": ["世界规则解释仍偏薄"],
                            "improvementPoints": ["补一处世界规则解释"],
                            "scores": [],
                        },
                        "scores": [],
                        "issues": [],
                        "closureAssessment": {},
                        "repairSuggestions": ["补一处世界规则解释"],
                        "acceptedRisks": [],
                        "gateFailures": [],
                        "finalAllowHumanReview": True,
                        "scoreSummary": {
                            "average": 3.5,
                            "lowestScore": 3,
                            "lowestDimensions": ["世界与制度逻辑"],
                            "strongestDimension": {"dimensionId": "volumeClosure", "label": "卷级闭环", "score": 4},
                        },
                        "repairCoverage": {
                            "weakDimensionIds": [],
                            "weakDimensionLabels": [],
                            "uncoveredWeakDimensionIds": [],
                            "uncoveredWeakDimensionLabels": [],
                            "issueCount": 0,
                            "repairSuggestionCount": 1,
                            "status": "complete",
                        },
                    }
                ],
            },
        )

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir), "--volume-id", "volume-001"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["scope"], "volume")
        self.assertEqual(payload["project"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(payload["targetVolume"]["volumeId"], "volume-001")
        self.assertEqual(payload["targetVolume"]["chapterCount"], 2)
        self.assertFalse(payload["targetChapter"]["exists"])
        self.assertTrue(payload["reviewStatus"]["volumeSelfReview"]["exists"])
        self.assertEqual(payload["reviewStatus"]["volumeSelfReview"]["closureStatus"], "closed")
        self.assertTrue(payload["reviewStatus"]["volumeSelfReview"]["editorPassCompleted"])
        self.assertEqual(payload["reviewStatus"]["volumeSelfReview"]["editorMode"], "independent_agent")
        self.assertEqual(payload["reviewStatus"]["volumeSelfReview"]["editorVerdict"], "pass")
        self.assertEqual(payload["reviewStatus"]["volumeSelfReview"]["repairCoverageStatus"], "complete")
        self.assertEqual(payload["reviewStatus"]["volumeSelfReview"]["weakDimensionLabels"], [])
        self.assertEqual(payload["reviewStatus"]["volumeSelfReview"]["uncoveredWeakDimensionLabels"], [])
        self.assertEqual(payload["workflow"]["scope"], "volume")
        self.assertEqual(payload["workflow"]["currentStage"], "human_review_ready")
        self.assertEqual(payload["workflow"]["workflowStatus"], "completed")
        self.assertEqual(payload["workflow"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertTrue(payload["workflow"]["volumeSelfReview"]["finalAllowHumanReview"])
        self.assertTrue(payload["workflow"]["volumeSelfReview"]["editorPassCompleted"])
        self.assertEqual(payload["workflow"]["volumeSelfReview"]["editorMode"], "independent_agent")
        self.assertEqual(payload["workflow"]["volumeSelfReview"]["editorVerdict"], "pass")
        self.assertEqual(payload["workflow"]["preflightSummary"]["mentionActionCount"], 0)

    def test_status_volume_scope_reports_missing_project_prd_as_advisory(self) -> None:
        self._init_project()
        (self.temp_dir / "PRD.md").unlink()
        self._write_json(
            "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "残灯初鸣",
                        "chapters": [{"id": "chapter-001", "title": "灯尽人未绝", "status": "draft"}],
                    }
                ],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text("# 灯尽人未绝\n\n沈照在废棚里等死。\n", encoding="utf-8")

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir), "--volume-id", "volume-001"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"]["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["workflow"]["projectAdvisories"][0]["ruleId"], "missing-project-prd")

    def test_status_flags_invalid_scene_plan_ranges(self) -> None:
        self._init_project()
        self._write_json(
            "outline.yaml",
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "灯尽人未绝",
                        "status": "draft",
                        "direction": "立住死局。",
                        "beats": [
                            {"id": "beat-001", "summary": "开场", "status": "planned"}
                        ],
                        "scenePlans": [
                            {
                                "id": "scene-001",
                                "title": "越界场景",
                                "summary": "段落边界错误。",
                                "startParagraph": 1,
                                "endParagraph": 3,
                            }
                        ],
                    }
                ],
                "chapterDirections": [],
                "volumes": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n"
            "只有一段正文。\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["targetChapter"]["scenePlanStatus"]["valid"])
        self.assertEqual(len(payload["targetChapter"]["scenePlanStatus"]["invalidScenePlans"]), 1)
        self.assertEqual(
            payload["targetChapter"]["scenePlanStatus"]["invalidScenePlans"][0]["issue"],
            "out-of-range",
        )

    def test_status_exposes_start_guide_for_bootstrap_chapter(self) -> None:
        self._init_project()

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        self.assertEqual(exit_code, 0)
        start_guide = payload["targetChapter"]["startGuide"]
        self.assertFalse(start_guide["hasBodyParagraphs"])
        self.assertIn("missing-direction", start_guide["missingCodes"])
        self.assertIn("missing-beats", start_guide["missingCodes"])
        self.assertIn("missing-scene-plans", start_guide["missingCodes"])
        self.assertTrue(any("structure apply" in item for item in start_guide["suggestedCommands"]))
        self.assertFalse(any("scene-detect" in item for item in start_guide["suggestedCommands"]))

    def test_status_start_guide_does_not_fall_back_to_fake_missing_codes_when_outline_is_ready(self) -> None:
        self._init_project()
        self._write_json(
            "outline.yaml",
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "灯尽人未绝",
                        "status": "draft",
                        "direction": "立住死局。",
                        "beats": [{"id": "beat-001", "summary": "死局开场", "status": "planned"}],
                        "scenePlans": [
                            {
                                "id": "scene-001",
                                "title": "废棚等死",
                                "summary": "立住死局。",
                                "startParagraph": 1,
                                "endParagraph": 2,
                            }
                        ],
                    }
                ],
                "chapterDirections": [],
                "volumes": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n沈照在废棚里等死。\n\n旧灯芯忽然回亮了一线。\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        self.assertEqual(exit_code, 0)
        start_guide = payload["targetChapter"]["startGuide"]
        self.assertEqual(start_guide["missingCodes"], [])
        self.assertTrue(any("chapter analyze" in item for item in start_guide["suggestedCommands"]))
        self.assertTrue(any("context refresh" in item for item in start_guide["suggestedCommands"]))

    def test_status_includes_mention_hygiene_summary_for_target_chapter(self) -> None:
        self._init_project()
        self._write_json(
            "outline.yaml",
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "灯尽人未绝",
                        "status": "draft",
                        "direction": "立住死局。",
                        "beats": [],
                        "scenePlans": [],
                    }
                ],
                "chapterDirections": [],
                "volumes": [],
            },
        )
        self._write_json(
            "entities.yaml",
            {
                "entities": [
                    {
                        "id": "char-shenzhao",
                        "name": "沈照",
                        "type": "character",
                        "aliases": [],
                        "profile": {},
                        "currentState": {},
                    },
                    {
                        "id": "char-yuechi",
                        "name": "岳池",
                        "type": "character",
                        "aliases": [],
                        "profile": {},
                        "currentState": {},
                    },
                ],
                "enrichmentProposals": [],
            },
        )
        self._write_json(
            "worldbook.yaml",
            {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [],
                "factions": [
                    {"id": "faction-qingyun", "name": "青云宗", "summary": "本地中型宗门"}
                ],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n"
            "沈照抬头看向青云宗的山门。\n\n"
            "@{顾寒山}站在暗处。\n\n"
            "“岳池”这个名字此刻没人敢提。\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(["status", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        self.assertEqual(exit_code, 0)
        mention_hygiene = payload["targetChapter"]["mentionHygiene"]
        self.assertTrue(mention_hygiene["exists"])
        self.assertEqual(mention_hygiene["knownUnwrappedCount"], 2)
        self.assertEqual(mention_hygiene["taggedMissingCount"], 1)
        self.assertEqual(mention_hygiene["ignoredQuotedKnownMentionCount"], 1)
        self.assertTrue(any(item["name"] == "沈照" for item in mention_hygiene["topKnownUnwrapped"]))
        self.assertTrue(any(item["name"] == "青云宗" for item in mention_hygiene["topKnownUnwrapped"]))
        self.assertEqual(mention_hygiene["topTaggedMissing"][0]["name"], "顾寒山")
        self.assertEqual(mention_hygiene["topIgnoredQuotedKnownMentions"][0]["name"], "岳池")


if __name__ == "__main__":
    unittest.main()
