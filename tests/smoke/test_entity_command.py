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


def _setup_project(tmp: Path):
    fixture = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
    shutil.copytree(fixture, tmp, dirs_exist_ok=True)
    for d in ["proposals", "reviews", "projections", "logs"]:
        (tmp / d).mkdir(exist_ok=True)
    entities = {
        "entities": [
            {
                "id": "char-linzhou", "name": "林舟", "source": "seed", "aliases": [],
                "seed": {"archetype": "落魄侦探", "personality": "冷静", "motivation": "追查真相", "background": "前刑侦"},
                "profile": {"appearance": [], "abilities": [], "speech": [], "relationships": []},
                "currentState": {"status": "active", "physicalState": [], "emotionalState": [], "location": "未知", "lastUpdatedChapter": None},
                "createdAt": "2026-01-01T00:00:00",
            }
        ],
        "enrichmentProposals": [],
    }
    (tmp / "entities.yaml").write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, content in [
        ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
        ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
        ("projections/projection.yaml", '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}'),
        ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
        ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
    ]:
        (tmp / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp / name).write_text(content + "\n", encoding="utf-8")


class EntityCommandTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-entity-"))
        _setup_project(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_entity_enrich_command(self):
        result = main([
            "entity", "enrich",
            "--root", str(self.temp_dir),
            "--chapter-id", "chapter-001",
        ])
        self.assertEqual(result, 0)

    def test_entity_add_creates_entity_card_without_manual_yaml_edit(self):
        from contextlib import redirect_stdout
        from io import StringIO

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(
                [
                    "entity",
                    "add",
                    "--root",
                    str(self.temp_dir),
                    "--id",
                    "char-shenzhao",
                    "--name",
                    "沈照",
                    "--type",
                    "character",
                    "--source",
                    "manual",
                    "--summary",
                    "谨慎而沉默的杂役弟子",
                    "--alias",
                    "沈师弟",
                    "--status-tag",
                    "受压制",
                    "--status",
                    "active",
                    "--location",
                    "外门",
                    "--power-public",
                    "凡人",
                    "--chapter-id",
                    "chapter-001",
                ]
            )
        self.assertEqual(result, 0)
        payload = json.loads(buf.getvalue())
        entities = json.loads((self.temp_dir / "entities.yaml").read_text(encoding="utf-8"))
        created = next(item for item in entities["entities"] if item["id"] == "char-shenzhao")
        self.assertEqual(payload["action"], "created")
        self.assertEqual(created["name"], "沈照")
        self.assertEqual(created["aliases"], ["沈师弟"])
        self.assertEqual(created["state"]["statusTags"], ["受压制"])
        self.assertEqual(created["currentState"]["location"], "外门")
        self.assertEqual(created["seed"]["background"], "")

    def test_entity_state_update_updates_state_and_change_log(self):
        from contextlib import redirect_stdout
        from io import StringIO

        main(
            [
                "entity",
                "add",
                "--root",
                str(self.temp_dir),
                "--id",
                "char-shenzhao",
                "--name",
                "沈照",
                "--type",
                "character",
                "--status",
                "active",
                "--location",
                "外门",
                "--chapter-id",
                "chapter-001",
            ]
        )

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(
                [
                    "entity",
                    "state-update",
                    "--root",
                    str(self.temp_dir),
                    "--entity-id",
                    "char-shenzhao",
                    "--chapter-id",
                    "chapter-002",
                    "--reason",
                    "夜巡后受伤并决定隐瞒实力",
                    "--status-tag",
                    "受伤",
                    "--status-tag",
                    "隐瞒实力",
                    "--physical-state",
                    "右臂灼伤",
                    "--emotional-state",
                    "警惕",
                    "--location",
                    "废照棚",
                    "--power-public",
                    "练气",
                    "--power-true",
                    "半觉醒",
                ]
            )
        self.assertEqual(result, 0)
        payload = json.loads(buf.getvalue())
        entities = json.loads((self.temp_dir / "entities.yaml").read_text(encoding="utf-8"))
        updated = next(item for item in entities["entities"] if item["id"] == "char-shenzhao")
        self.assertEqual(payload["action"], "updated")
        self.assertEqual(updated["state"]["statusTags"], ["受伤", "隐瞒实力"])
        self.assertEqual(updated["currentState"]["location"], "废照棚")
        self.assertEqual(updated["state"]["powerLevel"]["publicLevel"], "练气")
        self.assertEqual(updated["state"]["powerLevel"]["trueLevel"], "半觉醒")
        self.assertEqual(updated["currentState"]["lastUpdatedChapter"], "chapter-002")
        self.assertTrue(any(item["field"] == "state.powerLevel" for item in updated["changeLog"]))

    def test_entity_review_apply(self):
        main(["entity", "enrich", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        result = main([
            "entity", "review",
            "--root", str(self.temp_dir),
            "--all-pending",
            "--decision", "accepted",
        ])
        self.assertEqual(result, 0)

    def test_entity_list_command(self):
        from contextlib import redirect_stdout
        from io import StringIO
        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "list", "--root", str(self.temp_dir)])
        self.assertEqual(result, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "char-linzhou")
        self.assertEqual(data[0]["name"], "林舟")
        self.assertEqual(data[0]["archetype"], "落魄侦探")

    def test_entity_list_with_type_filter(self):
        from contextlib import redirect_stdout
        from io import StringIO
        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "list", "--root", str(self.temp_dir), "--type", "location"])
        self.assertEqual(result, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data, [])

    def test_entity_show_by_id(self):
        from contextlib import redirect_stdout
        from io import StringIO
        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "show", "--root", str(self.temp_dir), "--entity-id", "char-linzhou"])
        self.assertEqual(result, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["id"], "char-linzhou")
        self.assertIn("seed", data)
        self.assertIn("profile", data)
        self.assertIn("currentState", data)
        self.assertIn("latestProjection", data)
        self.assertIn("relations", data)

    def test_entity_show_by_name(self):
        from contextlib import redirect_stdout
        from io import StringIO
        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "show", "--root", str(self.temp_dir), "--name", "林舟"])
        self.assertEqual(result, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["name"], "林舟")

    def test_entity_show_not_found(self):
        with self.assertRaises(SystemExit):
            main(["entity", "show", "--root", str(self.temp_dir), "--entity-id", "nonexistent"])

    def test_entity_mention_check_reports_wrapped_missing_unwrapped_known_and_quote_ignored(self):
        from contextlib import redirect_stdout
        from io import StringIO

        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [],
                    "worldRules": [],
                    "powerProgressions": [],
                    "factions": [
                        {"id": "faction-qingyun", "name": "青云宗", "summary": "本地中型宗门"}
                    ],
                    "locations": [],
                    "artifacts": [
                        {"id": "artifact-zhenhai", "name": "镇海印", "summary": "压制潮息的旧印"}
                    ],
                    "mysteries": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        entities = json.loads((self.temp_dir / "entities.yaml").read_text(encoding="utf-8"))
        entities["entities"].append(
            {
                "id": "char-shenzhao",
                "name": "沈昭",
                "source": "seed",
                "aliases": [],
                "seed": {},
                "profile": {"appearance": [], "abilities": [], "speech": [], "relationships": []},
                "currentState": {"status": "active", "physicalState": [], "emotionalState": [], "location": "未知", "lastUpdatedChapter": None},
                "createdAt": "2026-01-01T00:00:00",
            }
        )
        (self.temp_dir / "entities.yaml").write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n"
            "@{林舟}抬头望向 @{青云宗} 的山门，又低头看了一眼掌中的 @{镇海印} 与 @{岳池}。\n\n"
            "林舟没有回头。\n\n"
            "“沈昭”这个名字此刻没人敢提。\n",
            encoding="utf-8",
        )

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "mention-check", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(result, 0)
        data = json.loads(buf.getvalue())

        self.assertEqual(data["chapterId"], "chapter-001")
        self.assertEqual(data["summary"]["taggedCoveredCount"], 3)
        self.assertEqual(data["summary"]["taggedMissingCount"], 1)
        self.assertEqual(data["summary"]["knownUnwrappedCount"], 1)
        self.assertEqual(data["summary"]["ignoredQuotedKnownMentionCount"], 1)
        self.assertTrue(any(item["name"] == "岳池" for item in data["taggedMissing"]))
        self.assertTrue(any(item["name"] == "林舟" and item["plainCount"] == 1 for item in data["knownUnwrapped"]))
        self.assertTrue(any(item["name"] == "沈昭" and item["quotedCount"] == 1 for item in data["ignoredQuotedKnownMentions"]))
        self.assertTrue(any(item["name"] == "青云宗" and item["source"] == "worldbook.factions" for item in data["taggedCovered"]))
        self.assertTrue(any(item["name"] == "镇海印" and item["source"] == "worldbook.artifacts" for item in data["relatedContext"]))

    def test_entity_mention_adopt_creates_entity_from_tagged_missing(self):
        from contextlib import redirect_stdout
        from io import StringIO

        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n@{林舟}看见了 @{岳池} 手里的旧灯。\n",
            encoding="utf-8",
        )

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(
                [
                    "entity",
                    "mention-adopt",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--id",
                    "char-yuechi",
                    "--name",
                    "岳池",
                    "--summary",
                    "与旧灯相关的神秘人物",
                    "--status",
                    "active",
                    "--location",
                    "废照棚",
                ]
            )
        self.assertEqual(result, 0)
        payload = json.loads(buf.getvalue())
        entities = json.loads((self.temp_dir / "entities.yaml").read_text(encoding="utf-8"))
        adopted = next(item for item in entities["entities"] if item["id"] == "char-yuechi")

        self.assertEqual(payload["action"], "created")
        self.assertEqual(payload["mentionSource"], "tagged")
        self.assertEqual(adopted["name"], "岳池")
        self.assertEqual(adopted["source"], "tagged-mention")
        self.assertEqual(adopted["currentState"]["lastUpdatedChapter"], "chapter-001")

    def test_entity_mention_plan_previews_known_tag_actions_and_missing_adopt_candidates(self):
        from contextlib import redirect_stdout
        from io import StringIO

        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
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
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n林舟抬头望向青云宗的山门。\n\n@{岳池}在暗处看着他。\n",
            encoding="utf-8",
        )

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "mention-plan", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(result, 0)

        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["summary"]["knownUnwrappedActionCount"], 2)
        self.assertEqual(payload["summary"]["taggedMissingActionCount"], 1)
        self.assertTrue(any(item["name"] == "林舟" for item in payload["knownUnwrappedActions"]))
        self.assertTrue(any(item["name"] == "青云宗" and item["source"] == "worldbook.factions" for item in payload["knownUnwrappedActions"]))
        self.assertTrue(any(item["name"] == "岳池" for item in payload["taggedMissingActions"]))
        adopt_action = next(item for item in payload["taggedMissingActions"] if item["name"] == "岳池")
        self.assertEqual(adopt_action["suggestedTargets"][0]["target"], "entity")

    def test_entity_mention_apply_applies_selected_plan_action_only(self):
        from contextlib import redirect_stdout
        from io import StringIO

        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
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
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n林舟抬头望向青云宗的山门。\n",
            encoding="utf-8",
        )

        plan_buf = StringIO()
        with redirect_stdout(plan_buf):
            plan_result = main(["entity", "mention-plan", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(plan_result, 0)
        plan_payload = json.loads(plan_buf.getvalue())
        target_action = next(item for item in plan_payload["knownUnwrappedActions"] if item["name"] == "青云宗")

        apply_buf = StringIO()
        with redirect_stdout(apply_buf):
            apply_result = main(
                [
                    "entity",
                    "mention-apply",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--action-id",
                    target_action["actionId"],
                ]
            )
        self.assertEqual(apply_result, 0)
        apply_payload = json.loads(apply_buf.getvalue())
        updated_text = chapter_path.read_text(encoding="utf-8")

        self.assertEqual(apply_payload["appliedActionCount"], 1)
        self.assertIn("林舟抬头望向@{青云宗}的山门。", updated_text)
        self.assertNotIn("@{林舟}抬头", updated_text)

    def test_entity_mention_apply_rejects_missing_adopt_action(self):
        from contextlib import redirect_stdout
        from io import StringIO

        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        original_text = "# 第一章\n\n@{岳池}在暗处看着林舟。\n"
        chapter_path.write_text(original_text, encoding="utf-8")

        plan_buf = StringIO()
        with redirect_stdout(plan_buf):
            plan_result = main(["entity", "mention-plan", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(plan_result, 0)
        plan_payload = json.loads(plan_buf.getvalue())
        target_action = next(item for item in plan_payload["taggedMissingActions"] if item["name"] == "岳池")

        with self.assertRaises(SystemExit):
            main(
                [
                    "entity",
                    "mention-apply",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--action-id",
                    target_action["actionId"],
                ]
            )

        self.assertEqual(chapter_path.read_text(encoding="utf-8"), original_text)

    def test_entity_mention_plan_supports_volume_scope(self):
        from contextlib import redirect_stdout
        from io import StringIO

        (self.temp_dir / "outline.yaml").write_text(
            json.dumps(
                {
                    "chapters": [],
                    "chapterDirections": [],
                    "volumes": [
                        {
                            "id": "volume-001",
                            "title": "第一卷",
                            "chapters": [
                                {"id": "chapter-001", "title": "第一章"},
                                {"id": "chapter-002", "title": "第二章"},
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
        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
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
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n林舟看向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 第二章\n\n@{岳池}站在暗处。\n",
            encoding="utf-8",
        )

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(["entity", "mention-plan", "--root", str(self.temp_dir), "--volume-id", "volume-001"])
        self.assertEqual(result, 0)

        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["scope"], "volume")
        self.assertEqual(payload["volumeId"], "volume-001")
        self.assertEqual(payload["summary"]["chapterPlanCount"], 2)
        self.assertEqual(payload["summary"]["knownUnwrappedActionCount"], 2)
        self.assertEqual(payload["summary"]["taggedMissingActionCount"], 1)
        first_plan = next(item for item in payload["chapterPlans"] if item["chapterId"] == "chapter-001")
        second_plan = next(item for item in payload["chapterPlans"] if item["chapterId"] == "chapter-002")
        self.assertTrue(any(item["name"] == "林舟" for item in first_plan["knownUnwrappedActions"]))
        self.assertTrue(any(item["name"] == "青云宗" for item in first_plan["knownUnwrappedActions"]))
        self.assertEqual(second_plan["taggedMissingActions"][0]["name"], "岳池")

    def test_entity_mention_tag_apply_wraps_known_unwrapped_mentions_only(self):
        from contextlib import redirect_stdout
        from io import StringIO

        entities = json.loads((self.temp_dir / "entities.yaml").read_text(encoding="utf-8"))
        entities["entities"].append(
            {
                "id": "char-shenzhao",
                "name": "沈昭",
                "source": "seed",
                "aliases": [],
                "seed": {},
                "profile": {"appearance": [], "abilities": [], "speech": [], "relationships": []},
                "currentState": {"status": "active", "physicalState": [], "emotionalState": [], "location": "未知", "lastUpdatedChapter": None},
                "createdAt": "2026-01-01T00:00:00",
            }
        )
        (self.temp_dir / "entities.yaml").write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 第一章\n\n林舟没有回头。\n\n“沈昭”这个名字此刻没人敢提。\n",
            encoding="utf-8",
        )

        buf = StringIO()
        with redirect_stdout(buf):
            result = main(
                [
                    "entity",
                    "mention-tag-apply",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--all-known-unwrapped",
                ]
            )
        self.assertEqual(result, 0)
        payload = json.loads(buf.getvalue())
        updated_text = chapter_path.read_text(encoding="utf-8")

        self.assertEqual(payload["replacementCount"], 1)
        self.assertIn("@{林舟}没有回头。", updated_text)
        self.assertIn("“沈昭”这个名字此刻没人敢提。", updated_text)


if __name__ == "__main__":
    unittest.main()
