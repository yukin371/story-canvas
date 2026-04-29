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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ReviewPreflightSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-review-preflight-"))
        fixture = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
        shutil.copytree(fixture, self.temp_dir, dirs_exist_ok=True)
        for relative in ["proposals", "reviews", "projections", "logs"]:
            (self.temp_dir / relative).mkdir(exist_ok=True)
        _write_json(self.temp_dir / "proposals" / "draft-proposals.yaml", {"draftProposals": []})
        _write_json(self.temp_dir / "reviews" / "change-requests.yaml", {"changeRequests": []})
        _write_json(
            self.temp_dir / "projections" / "projection.yaml",
            {
                "snapshotProjections": [],
                "relationProjections": [],
                "sceneScopeProjections": [],
                "timelineProjections": [],
                "causalityProjections": [],
            },
        )
        _write_json(self.temp_dir / "projections" / "context-lens.yaml", {"currentChapterId": None, "lenses": []})
        _write_json(self.temp_dir / "logs" / "projection-log.yaml", {"projectionChanges": []})

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_incomplete_prd(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 读者钩子: TBD\n- 本章承接点: TBD\n",
            encoding="utf-8",
        )

    def test_review_preflight_chapter_aggregates_existing_checks(self) -> None:
        _write_json(
            self.temp_dir / "project.yaml",
            {
                "title": "命灯",
                "genre": "玄幻",
                "activeChapterId": "chapter-002",
                "storyTemplate": {
                    "modulePolicy": {
                        "worldRules": "required",
                        "factions": "required",
                    }
                },
            },
        )
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "命火初现",
                        "chapters": [
                            {"id": "chapter-001", "title": "入山"},
                            {"id": "chapter-002", "title": "压火"},
                        ],
                    }
                ],
            },
        )
        _write_json(
            self.temp_dir / "entities.yaml",
            {
                "entities": [
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
                ],
                "enrichmentProposals": [],
            },
        )
        _write_json(
            self.temp_dir / "worldbook.yaml",
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
        )
        _write_json(
            self.temp_dir / "foreshadowing.yaml",
            {
                "foreshadows": [
                    {
                        "id": "fs-001",
                        "title": "压火令",
                        "plannedPayoffChapter": "chapter-002",
                        "status": "planted",
                        "payoffPoints": [],
                    },
                    {
                        "id": "fs-002",
                        "title": "命灯裂纹",
                        "status": "planted",
                        "payoffPoints": [],
                    },
                ]
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n@{青云宗}山门前风很冷。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 第二章\n\n林舟被押去青云宗压火，@{岳池}站在高处看着他。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "preflight", "--root", str(self.temp_dir), "--chapter-id", "chapter-002"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["scope"], "chapter")
        self.assertEqual(payload["chapterId"], "chapter-002")
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["targetVolume"]["volumeId"], "volume-001")
        self.assertEqual(payload["summary"]["mentionActionCount"], 3)
        self.assertEqual(payload["summary"]["knownUnwrappedActionCount"], 2)
        self.assertEqual(payload["summary"]["taggedMissingActionCount"], 1)
        self.assertEqual(payload["summary"]["dueForeshadowCount"], 1)
        self.assertEqual(payload["summary"]["unresolvedWithoutScheduleCount"], 1)
        self.assertEqual(payload["summary"]["worldOnboardingGapCount"], 3)
        self.assertEqual(payload["mentionPlan"]["summary"]["totalActionCount"], 3)
        self.assertTrue(any(item["name"] == "岳池" for item in payload["mentionPlan"]["taggedMissingActions"]))
        self.assertTrue(any(item["id"] == "fs-001" for item in payload["foreshadowCheck"]["dueForeshadows"]))
        self.assertTrue(any(item["code"] == "missing-power-progressions" for item in payload["worldCheck"]["onboardingGaps"]))

    def test_review_preflight_volume_aggregates_chapter_preflights(self) -> None:
        _write_json(
            self.temp_dir / "project.yaml",
            {
                "title": "命灯",
                "genre": "玄幻",
                "activeChapterId": "chapter-001",
                "storyTemplate": {
                    "modulePolicy": {
                        "worldRules": "required",
                        "factions": "required",
                    }
                },
            },
        )
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "命火初现",
                        "chapters": [
                            {"id": "chapter-001", "title": "入山"},
                            {"id": "chapter-002", "title": "压火"},
                        ],
                    }
                ],
            },
        )
        _write_json(
            self.temp_dir / "entities.yaml",
            {
                "entities": [
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
                ],
                "enrichmentProposals": [],
            },
        )
        _write_json(
            self.temp_dir / "worldbook.yaml",
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
        )
        _write_json(
            self.temp_dir / "foreshadowing.yaml",
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
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 第二章\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "preflight", "--root", str(self.temp_dir), "--volume-id", "volume-001"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["scope"], "volume")
        self.assertEqual(payload["volumeId"], "volume-001")
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["summary"]["chapterPreflightCount"], 2)
        self.assertEqual(payload["summary"]["mentionActionCount"], 5)
        self.assertEqual(payload["summary"]["dueForeshadowCount"], 3)
        self.assertEqual(payload["summary"]["worldOnboardingGapCount"], 6)
        self.assertEqual(payload["mentionPlan"]["summary"]["knownUnwrappedActionCount"], 4)
        self.assertEqual(payload["mentionPlan"]["summary"]["taggedMissingActionCount"], 1)
        self.assertTrue(any(item["name"] == "青云宗" for item in payload["volumeWorldContext"]["referencedItems"]))
        self.assertEqual(payload["volumeStructureCheck"]["role"], "intro-volume")
        self.assertEqual(payload["volumeStructureCheck"]["summary"]["riskCount"], 3)
        self.assertEqual(payload["volumeStructureCheck"]["summary"]["missingCount"], 1)
        self.assertTrue(any(item["phase"] == "opening" for item in payload["volumeStructureCheck"]["phaseAssignments"]))
        self.assertTrue(
            any(
                item["id"] == "intro-world-onboarding" and item["status"] == "risk"
                for item in payload["volumeStructureCheck"]["checklist"]
            )
        )
        outline_coverage_check = next(
            item
            for item in payload["volumeStructureCheck"]["checklist"]
            if item["id"] == "outline-coverage"
        )
        self.assertEqual(outline_coverage_check["targetChapterIds"], ["chapter-001", "chapter-002"])
        first_chapter = next(item for item in payload["chapterPreflights"] if item["chapterId"] == "chapter-001")
        second_chapter = next(item for item in payload["chapterPreflights"] if item["chapterId"] == "chapter-002")
        self.assertEqual(first_chapter["summary"]["mentionActionCount"], 2)
        self.assertEqual(second_chapter["summary"]["mentionActionCount"], 3)
        self.assertEqual(first_chapter["summary"]["dueForeshadowCount"], 2)
        self.assertEqual(second_chapter["summary"]["dueForeshadowCount"], 1)
        self.assertTrue(any(item["name"] == "岳池" for item in second_chapter["mentionPlan"]["taggedMissingActions"]))
        self.assertTrue(second_chapter["worldCheck"]["onboardingGaps"])

    def test_review_preflight_uses_latest_scene_review_per_scope(self) -> None:
        _write_json(
            self.temp_dir / "project.yaml",
            {
                "title": "雨证",
                "genre": "职业悬疑",
                "activeChapterId": "chapter-001",
            },
        )
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "临时禁令",
                        "chapters": [
                            {
                                "id": "chapter-001",
                                "title": "停雨申请",
                                "direction": "完成第一场听证钩子",
                                "beats": [{"summary": "递交申请"}],
                                "scenePlans": [{"title": "听证", "goal": "留下日志异常"}],
                            }
                        ],
                    }
                ],
            },
        )
        _write_json(self.temp_dir / "entities.yaml", {"entities": [], "enrichmentProposals": []})
        _write_json(
            self.temp_dir / "worldbook.yaml",
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
        _write_json(self.temp_dir / "foreshadowing.yaml", {"foreshadows": []})
        _write_json(
            self.temp_dir / "reviews" / "story-reviews.yaml",
            {
                "rubricVersion": "chapter-review-v1",
                "sceneRubricVersion": "scene-review-v1",
                "chapterReviews": [
                    {
                        "chapterId": "chapter-001",
                        "chapterTitle": "停雨申请",
                        "generatedAt": "2026-04-29T10:00:00+08:00",
                        "scores": {"total": 50},
                        "ruleJudgements": [{"ruleId": "oldChapterRule", "message": "旧章节问题"}],
                    },
                    {
                        "chapterId": "chapter-001",
                        "chapterTitle": "停雨申请",
                        "generatedAt": "2026-04-29T11:00:00+08:00",
                        "scores": {"total": 86},
                        "ruleJudgements": [{"ruleId": "newChapterRule", "message": "新章节问题"}],
                    },
                ],
                "sceneReviews": [
                    {
                        "chapterId": "chapter-001",
                        "generatedAt": "2026-04-29T10:10:00+08:00",
                        "rating": "workable",
                        "scores": {"total": 50},
                        "sceneRange": {"sceneIndex": 1, "startParagraph": 1, "endParagraph": 2},
                        "priorityActions": ["旧场景问题"],
                        "ruleJudgements": [{"ruleId": "oldSceneRule", "message": "旧场景问题"}],
                    },
                    {
                        "chapterId": "chapter-001",
                        "generatedAt": "2026-04-29T11:10:00+08:00",
                        "rating": "strong",
                        "scores": {"total": 90},
                        "sceneRange": {"sceneIndex": 1, "startParagraph": 1, "endParagraph": 3},
                        "priorityActions": [],
                        "ruleJudgements": [{"ruleId": "newSceneRule", "message": "新场景问题"}],
                    },
                ],
                "volumeSelfReviews": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n雨量日志出现异常。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "preflight", "--root", str(self.temp_dir), "--volume-id", "volume-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["reviewEvidence"]["lowSceneReviews"], [])
        rule_ids = {item["ruleId"] for item in payload["reviewEvidence"]["topRuleJudgements"]}
        self.assertIn("newChapterRule", rule_ids)
        self.assertIn("newSceneRule", rule_ids)
        self.assertNotIn("oldChapterRule", rule_ids)
        self.assertNotIn("oldSceneRule", rule_ids)

    def test_review_preflight_volume_closure_readiness_consumes_required_chapter_contract(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: 完成临时禁令听证前的证据争夺，并交出第一场程序胜负\n",
            encoding="utf-8",
        )
        _write_json(
            self.temp_dir / "project.yaml",
            {
                "title": "雨证协议",
                "genre": "职业悬疑",
                "activeChapterId": "chapter-001",
                "commercialPositioning": {
                    "releaseCadence": "测试用三章首卷",
                },
            },
        )
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [],
                "chapterDirections": [],
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "临时禁令",
                        "chapters": [
                            {
                                "id": "chapter-001",
                                "title": "停雨申请",
                                "status": "completed",
                                "direction": "许澄递交停雨申请，并暴露证据缺口。",
                            }
                        ],
                    }
                ],
            },
        )
        _write_json(self.temp_dir / "entities.yaml", {"entities": [], "enrichmentProposals": []})
        _write_json(
            self.temp_dir / "worldbook.yaml",
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
        _write_json(self.temp_dir / "foreshadowing.yaml", {"foreshadows": []})
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n许澄递交停雨申请，但日志缺口还没有补上。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "preflight", "--root", str(self.temp_dir), "--volume-id", "volume-001"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["volumeClosureContract"]["requiredChapterCount"], 3)
        self.assertEqual(payload["volumeClosureContract"]["actualChapterCount"], 1)
        closure_check = next(
            item
            for item in payload["volumeStructureCheck"]["checklist"]
            if item["id"] == "closure-readiness"
        )
        self.assertEqual(closure_check["status"], "risk")
        self.assertEqual(closure_check["requiredChapterCount"], 3)
        self.assertEqual(closure_check["actualChapterCount"], 1)
        self.assertIn("三章首卷", "".join(closure_check["evidence"]))
        self.assertIn("卷目标", "".join(closure_check["evidence"]))

    def test_review_preflight_reports_incomplete_prd(self) -> None:
        self._write_incomplete_prd()
        _write_json(
            self.temp_dir / "project.yaml",
            {
                "title": "命灯",
                "genre": "玄幻",
                "activeChapterId": "chapter-001",
            },
        )
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [
                    {"id": "chapter-001", "title": "入山", "direction": "开场立住主角死局", "beats": [], "scenePlans": []}
                ],
                "chapterDirections": [],
                "volumes": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text("# 第一章\n\n林舟抬头看向山门。\n", encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["review", "preflight", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertIn("卷目标", payload["projectAdvisories"][0]["message"])


if __name__ == "__main__":
    unittest.main()
