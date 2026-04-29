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


class FullCreativeLoopTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-full-"))
        fixture = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
        shutil.copytree(fixture, self.temp_dir, dirs_exist_ok=True)
        for d in ["proposals", "reviews", "projections", "logs"]:
            (self.temp_dir / d).mkdir(exist_ok=True)

        entities = {
            "entities": [
                {
                    "id": "char-linzhou", "name": "林舟", "source": "seed", "aliases": [],
                    "seed": {"archetype": "落魄侦探", "personality": "冷静、固执", "motivation": "追查真相", "background": "前刑侦"},
                    "profile": {"appearance": [], "abilities": [], "speech": [], "relationships": []},
                    "currentState": {"status": "active", "physicalState": [], "emotionalState": [], "location": "未知", "lastUpdatedChapter": None},
                    "createdAt": "2026-01-01T00:00:00",
                },
                {
                    "id": "char-shenzhao", "name": "沈昭", "source": "seed", "aliases": [],
                    "seed": {"archetype": "双重间谍", "personality": "冷静、多疑", "motivation": "生存", "background": "情报人员"},
                    "profile": {"appearance": [], "abilities": [], "speech": [], "relationships": []},
                    "currentState": {"status": "active", "physicalState": [], "emotionalState": [], "location": "未知", "lastUpdatedChapter": None},
                    "createdAt": "2026-01-01T00:00:00",
                },
            ],
            "enrichmentProposals": [],
        }
        outline = {
            "volumes": [
                {"id": "vol-001", "title": "迷雾序章", "theme": "真相", "chapters": [
                    {"id": "chapter-001", "title": "裂痕之夜", "status": "completed", "direction": "两人在仓库对峙", "beats": [
                        {"id": "beat-1", "summary": "开场", "status": "completed"},
                        {"id": "beat-2", "summary": "对峙", "status": "planned"},
                    ], "scenePlans": [
                        {"id": "scene-001", "title": "仓库对峙", "summary": "林舟与沈昭必须摊开彼此怀疑。", "startParagraph": 1, "endParagraph": 3}
                    ]},
                ]},
            ],
            "chapters": [{"id": "chapter-001", "title": "裂痕之夜", "status": "draft", "beats": [], "scenePlans": []}],
            "chapterDirections": [],
        }
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["positioning"] = {
            "primaryGenre": "mystery",
            "subGenre": "",
            "styleTags": [],
            "targetAudience": ["mystery-reader"],
        }
        project["storyContract"] = {
            "corePromises": ["每章推进账本谜团"],
            "avoidances": [],
            "endingContract": "",
            "paceContract": "中快节奏",
        }
        for name, content in [
            ("project.yaml", json.dumps(project, ensure_ascii=False)),
            ("entities.yaml", json.dumps(entities, ensure_ascii=False)),
            ("outline.yaml", json.dumps(outline, ensure_ascii=False)),
            ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
            ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
            ("projections/projection.yaml", '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}'),
            ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
            ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
        ]:
            p = self.temp_dir / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content + "\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_loop(self):
        r = str(self.temp_dir)
        # Phase 2: analyze -> enrich -> review -> suggest -> review -> projection -> context
        self.assertEqual(main(["chapter", "analyze", "--root", r, "--chapter-id", "chapter-001"]), 0)
        self.assertEqual(main(["entity", "enrich", "--root", r, "--chapter-id", "chapter-001"]), 0)
        self.assertEqual(main(["entity", "review", "--root", r, "--all-pending", "--decision", "accepted"]), 0)
        self.assertEqual(main(["chapter", "suggest", "--root", r, "--chapter-id", "chapter-001"]), 0)
        self.assertEqual(main(["review", "apply", "--root", r, "--chapter-id", "chapter-001", "--all-pending", "--decision", "accepted"]), 0)
        self.assertEqual(main(["projection", "apply", "--root", r, "--chapter-id", "chapter-001"]), 0)
        self.assertEqual(main(["context", "refresh", "--root", r, "--chapter-id", "chapter-001"]), 0)

        # Phase 3: consistency check
        self.assertEqual(main(["consistency", "check", "--root", r, "--chapter-id", "chapter-001"]), 0)

        check_file = self.temp_dir / "projections" / "consistency-check-chapter-001.yaml"
        self.assertTrue(check_file.exists())
        check_data = json.loads(check_file.read_text(encoding="utf-8"))
        self.assertIn("hardChecks", check_data)
        self.assertIn("softChecks", check_data)
        self.assertIn("contextForAI", check_data)

        # Verify projection was updated
        projection = json.loads((self.temp_dir / "projections" / "projection.yaml").read_text(encoding="utf-8"))
        self.assertTrue(len(projection["snapshotProjections"]) > 0 or len(projection["relationProjections"]) > 0)

        # Verify context lens was updated
        context = json.loads((self.temp_dir / "projections" / "context-lens.yaml").read_text(encoding="utf-8"))
        self.assertEqual(context["currentChapterId"], "chapter-001")

        # Verify scene-backed planned beat is no longer treated as an automatic deviation
        soft = check_data["softChecks"]
        self.assertEqual(soft.get("outlineDeviations", []), [])


if __name__ == "__main__":
    unittest.main()
