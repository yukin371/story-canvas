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


class WorldCommandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-world-"))
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

    def test_world_check_reports_world_onboarding_and_volume_context_gaps(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["activeChapterId"] = "chapter-002"
        project["storyTemplate"] = {
            "modulePolicy": {
                "worldRules": "required",
                "factions": "required",
            }
        }
        _write_json(self.temp_dir / "project.yaml", project)
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "volumes": [
                    {
                        "id": "volume-001",
                        "title": "第一卷",
                        "theme": "命火初现",
                        "chapters": [
                            {"id": "chapter-001", "title": "入山", "status": "draft"},
                            {"id": "chapter-002", "title": "压火", "status": "draft"},
                        ],
                    }
                ],
                "chapters": [],
                "chapterDirections": [],
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
                        "summary": "本地宗门",
                    }
                ],
                "locations": [
                    {
                        "id": "location-fire-valley",
                        "name": "火脉谷",
                        "summary": "压火矿谷",
                    }
                ],
                "artifacts": [],
                "mysteries": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n@{青云宗}山门前风声很冷。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 第二章\n\n@{青云宗}弟子押着杂役走入@{火脉谷}压火，林舟准备冲击灵台境。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["world", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-002"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-002")
        self.assertEqual(payload["targetVolume"]["volumeId"], "volume-001")
        self.assertEqual(payload["modulePolicy"]["missingRequiredModules"], ["worldRules"])
        self.assertEqual(payload["worldbookCoverage"]["factionCount"], 1)
        self.assertTrue(any(item["name"] == "青云宗" for item in payload["chapterWorldContext"]["referencedItems"]))
        self.assertTrue(any(item["name"] == "火脉谷" for item in payload["chapterWorldContext"]["referencedItems"]))
        self.assertTrue(any(item["code"] == "missing-power-progressions" for item in payload["onboardingGaps"]))
        self.assertTrue(any(item["code"] == "thin-early-world-onboarding" for item in payload["onboardingGaps"]))
        self.assertTrue(any(item["name"] == "青云宗" for item in payload["scaleRisks"]["factionRegistryGaps"]))
        volume_refs = payload["volumeWorldContext"]["referencedItems"]
        self.assertTrue(any(item["name"] == "青云宗" and item["mentionedChapterCount"] == 2 for item in volume_refs))

    def test_world_add_and_list_reduce_manual_worldbook_editing(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["activeChapterId"] = "chapter-001"
        _write_json(self.temp_dir / "project.yaml", project)

        add_buffer = StringIO()
        with redirect_stdout(add_buffer):
            exit_code = main(
                [
                    "world",
                    "add",
                    "--root",
                    str(self.temp_dir),
                    "--kind",
                    "faction",
                    "--id",
                    "faction-qingyun",
                    "--name",
                    "青云宗",
                    "--summary",
                    "本地中型宗门",
                    "--alias",
                    "青云外门",
                    "--field",
                    "level=middle",
                    "--field",
                    "status=active",
                ]
            )
        add_payload = json.loads(add_buffer.getvalue())
        worldbook = json.loads((self.temp_dir / "worldbook.yaml").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(add_payload["action"], "created")
        self.assertEqual(worldbook["factions"][0]["name"], "青云宗")
        self.assertEqual(worldbook["factions"][0]["level"], "middle")
        self.assertEqual(worldbook["factions"][0]["aliases"], ["青云外门"])

        list_buffer = StringIO()
        with redirect_stdout(list_buffer):
            list_exit_code = main(["world", "list", "--root", str(self.temp_dir), "--kind", "faction"])
        list_payload = json.loads(list_buffer.getvalue())

        self.assertEqual(list_exit_code, 0)
        self.assertEqual(list_payload["counts"]["faction"], 1)
        self.assertEqual(list_payload["items"][0]["name"], "青云宗")

    def test_world_mention_adopt_creates_worldbook_entry_from_tagged_missing(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["activeChapterId"] = "chapter-001"
        _write_json(self.temp_dir / "project.yaml", project)
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [
                    {"id": "chapter-001", "title": "入山", "status": "draft"},
                ],
                "chapterDirections": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n@{林舟}第一次听说 @{黑沼集} 这个地方。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "world",
                    "mention-adopt",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--kind",
                    "location",
                    "--id",
                    "location-heizhaoji",
                    "--name",
                    "黑沼集",
                    "--summary",
                    "边陲黑市据点",
                ]
            )

        payload = json.loads(buffer.getvalue())
        worldbook = json.loads((self.temp_dir / "worldbook.yaml").read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["action"], "created")
        self.assertEqual(payload["mentionSource"], "tagged")
        self.assertEqual(worldbook["locations"][0]["name"], "黑沼集")
        self.assertEqual(worldbook["locations"][0]["summary"], "边陲黑市据点")

    def test_world_progression_commands_manage_power_progressions(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["activeChapterId"] = "chapter-001"
        _write_json(self.temp_dir / "project.yaml", project)

        progression_buffer = StringIO()
        with redirect_stdout(progression_buffer):
            progression_exit_code = main(
                [
                    "world",
                    "progression-add",
                    "--root",
                    str(self.temp_dir),
                    "--id",
                    "cultivation",
                    "--label",
                    "修行境界",
                ]
            )
        progression_payload = json.loads(progression_buffer.getvalue())
        self.assertEqual(progression_exit_code, 0)
        self.assertEqual(progression_payload["progression"]["id"], "cultivation")

        stage_buffer = StringIO()
        with redirect_stdout(stage_buffer):
            stage_exit_code = main(
                [
                    "world",
                    "progression-stage-add",
                    "--root",
                    str(self.temp_dir),
                    "--progression-id",
                    "cultivation",
                    "--stage-name",
                    "炼气",
                    "--next-stage",
                    "筑基",
                    "--alias",
                    "练气",
                    "--requirement",
                    "稳固气海",
                    "--bottleneck",
                    "灵气不足",
                ]
            )
        stage_payload = json.loads(stage_buffer.getvalue())
        worldbook = json.loads((self.temp_dir / "worldbook.yaml").read_text(encoding="utf-8"))

        self.assertEqual(stage_exit_code, 0)
        self.assertEqual(stage_payload["stage"]["name"], "炼气")
        self.assertEqual(worldbook["powerProgressions"][0]["stages"][0]["nextStage"], "筑基")
        self.assertEqual(worldbook["powerProgressions"][0]["stages"][0]["aliases"], ["练气"])
        self.assertEqual(worldbook["powerProgressions"][0]["stages"][0]["breakthroughRequirements"], ["稳固气海"])

    def test_world_check_surfaces_power_progression_conflicts(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["activeChapterId"] = "chapter-001"
        _write_json(self.temp_dir / "project.yaml", project)
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [
                    {"id": "chapter-001", "title": "破关前夜", "status": "draft"},
                ],
                "chapterDirections": [],
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
                        "state": {
                            "powerLevel": {
                                "publicLevel": "炼气",
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
                "powerProgressions": [
                    {
                        "id": "cultivation",
                        "label": "修行境界",
                        "stages": [
                            {
                                "name": "炼气",
                                "nextStage": "筑基",
                                "breakthroughRequirements": ["稳固气海"],
                            },
                            {
                                "name": "筑基",
                                "nextStage": "金丹",
                            },
                            {
                                "name": "金丹",
                                "nextStage": "元婴",
                            },
                        ],
                    }
                ],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n林舟今夜便要冲击金丹境。\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["world", "check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["summary"]["powerProgressionConflictCount"], 1)
        self.assertEqual(payload["scaleRisks"]["powerProgressionConflicts"][0]["entityName"], "林舟")
        self.assertEqual(payload["scaleRisks"]["powerProgressionConflicts"][0]["targetStage"], "金丹")


if __name__ == "__main__":
    unittest.main()
