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
from story_harness_cli.protocol import load_project_state


def _setup_project(tmp: Path, entities_data: dict | None = None):
    fixture = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
    shutil.copytree(fixture, tmp, dirs_exist_ok=True)
    for d in ["proposals", "reviews", "projections", "logs"]:
        (tmp / d).mkdir(exist_ok=True)
    for name, content in [
        ("entities.yaml", json.dumps(entities_data or {"entities": [], "enrichmentProposals": []})),
        ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
        ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
        (
            "projections/projection.yaml",
            '{"snapshotProjections":[],"relationProjections":[],'
            '"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}',
        ),
        ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
        ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
    ]:
        (tmp / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp / name).write_text(content + "\n", encoding="utf-8")


class ChapterAutoRegisterTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-chapter-reg-"))
        _setup_project(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_inferred_entities_auto_registered(self):
        """chapter analyze should auto-register inferred entities into entities.yaml."""
        # chapter-001.md mentions @{林舟} and @{沈昭} — these are tag-mentioned
        # but no seed entities exist, so they become inferred
        result = main(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(result, 0)

        state = load_project_state(self.temp_dir)
        entities = state["entities"]["entities"]
        self.assertGreater(len(entities), 0)

        names = {e["name"] for e in entities}
        self.assertIn("林舟", names)
        self.assertIn("沈昭", names)

        # All should be inferred since we had no seed entities
        for e in entities:
            self.assertEqual(e.get("source"), "inferred")
            self.assertTrue(e["id"].startswith("inferred::"))

    def test_no_duplicate_registration(self):
        """Running analyze twice should not create duplicates."""
        main(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        state1 = load_project_state(self.temp_dir)
        count1 = len(state1["entities"]["entities"])

        main(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        state2 = load_project_state(self.temp_dir)
        count2 = len(state2["entities"]["entities"])

        self.assertEqual(count1, count2)

    def test_seed_entities_not_overwritten(self):
        """Pre-existing seed entities should remain untouched."""
        seed_entities = {
            "entities": [
                {
                    "id": "char-linzhou",
                    "name": "林舟",
                    "type": "character",
                    "aliases": [],
                    "seed": {"archetype": "落魄侦探"},
                    "source": "seed",
                }
            ],
            "enrichmentProposals": [],
        }
        tmp2 = Path(tempfile.mkdtemp(prefix="story-harness-chapter-seed-"))
        try:
            _setup_project(tmp2, entities_data=seed_entities)
            main(["chapter", "analyze", "--root", str(tmp2), "--chapter-id", "chapter-001"])

            state = load_project_state(tmp2)
            linzhou = next(e for e in state["entities"]["entities"] if e["name"] == "林舟")
            # Seed entity should keep its original id and source
            self.assertEqual(linzhou["id"], "char-linzhou")
            self.assertEqual(linzhou["source"], "seed")
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    def test_alias_matched_entity_does_not_create_inferred_duplicate(self):
        """Alias hit should resolve to existing entity instead of registering a duplicate inferred one."""
        seed_entities = {
            "entities": [
                {
                    "id": "char-zhao",
                    "name": "赵局长",
                    "type": "character",
                    "aliases": ["赵继明"],
                    "seed": {"archetype": "幕后黑手"},
                    "source": "seed",
                }
            ],
            "enrichmentProposals": [],
        }
        tmp2 = Path(tempfile.mkdtemp(prefix="story-harness-chapter-alias-"))
        try:
            _setup_project(tmp2, entities_data=seed_entities)
            (tmp2 / "chapters" / "chapter-001.md").write_text(
                "# 第一章\n\n@{赵继明}站在办公室窗前，没有回头。\n",
                encoding="utf-8",
            )
            main(["chapter", "analyze", "--root", str(tmp2), "--chapter-id", "chapter-001"])

            state = load_project_state(tmp2)
            entities = state["entities"]["entities"]
            self.assertEqual(len(entities), 1)
            self.assertEqual(entities[0]["id"], "char-zhao")
            self.assertEqual(entities[0]["name"], "赵局长")
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    def test_worldbook_mentions_are_not_auto_registered_as_characters(self):
        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [],
                    "worldRules": [
                        {
                            "id": "rule-rain-injunction",
                            "label": "停雨临时禁令",
                            "rule": "法院可在公共风险扩大前暂时叫停人工降雨协议。",
                        }
                    ],
                    "factions": [{"id": "faction-yunheng", "name": "云衡气候"}],
                    "locations": [{"id": "loc-old-dike", "name": "旧南堤"}],
                    "artifacts": [{"id": "artifact-rain-log", "name": "雨量日志"}],
                    "mysteries": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n@{许澄}在@{旧南堤}事故后调取@{云衡气候}的@{雨量日志}，准备申请@{停雨临时禁令}。\n",
            encoding="utf-8",
        )

        result = main(["chapter", "analyze", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(result, 0)

        state = load_project_state(self.temp_dir)
        names = {e["name"] for e in state["entities"]["entities"]}
        self.assertIn("许澄", names)
        self.assertNotIn("旧南堤", names)
        self.assertNotIn("云衡气候", names)
        self.assertNotIn("雨量日志", names)
        self.assertNotIn("停雨临时禁令", names)


if __name__ == "__main__":
    unittest.main()
