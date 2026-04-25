from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.protocol.state import load_project_state
from story_harness_cli.protocol.schema import default_project_state


class SchemaTest(unittest.TestCase):
    def test_entities_has_enrichment_proposals_field(self):
        state = default_project_state()
        entities = state["entities"]
        self.assertIn("entities", entities)
        self.assertIn("enrichmentProposals", entities)

    def test_outline_has_volumes(self):
        state = default_project_state()
        outline = state["outline"]
        self.assertIn("volumes", outline)
        self.assertIsInstance(outline["volumes"], list)

    def test_story_reviews_has_rubric_version_and_reports(self):
        state = default_project_state()
        story_reviews = state["story_reviews"]
        self.assertEqual(story_reviews["rubricVersion"], "chapter-review-v1")
        self.assertEqual(story_reviews["sceneRubricVersion"], "scene-review-v1")
        self.assertIn("chapterReviews", story_reviews)
        self.assertIn("sceneReviews", story_reviews)
        self.assertIsInstance(story_reviews["chapterReviews"], list)
        self.assertIsInstance(story_reviews["sceneReviews"], list)

    def test_project_has_positioning_and_story_contract(self):
        state = default_project_state()
        project = state["project"]
        self.assertIn("positioning", project)
        self.assertIn("storyContract", project)
        self.assertIn("commercialPositioning", project)
        self.assertIn("primaryGenre", project["positioning"])
        self.assertIn("targetAudience", project["positioning"])
        self.assertIn("corePromises", project["storyContract"])
        self.assertIn("endingContract", project["storyContract"])
        self.assertIn("premise", project["commercialPositioning"])
        self.assertIn("chapterWordTarget", project["commercialPositioning"])

    def test_workflow_progress_has_minimal_fields(self):
        state = default_project_state()
        workflow_progress = state["workflow_progress"]
        self.assertIn("currentStage", workflow_progress)
        self.assertIn("targetChapterId", workflow_progress)
        self.assertIn("workflowStatus", workflow_progress)
        self.assertIn("gateHistory", workflow_progress)
        self.assertIn("stageResults", workflow_progress)
        self.assertIn("updatedAt", workflow_progress)
        self.assertIn("lastRunMode", workflow_progress)

    def test_load_project_state_backfills_new_project_defaults(self):
        with tempfile.TemporaryDirectory(prefix="story-harness-project-schema-") as temp_dir:
            root = Path(temp_dir)
            (root / "project.yaml").write_text(
                '{\n  "title": "雾港疑案",\n  "genre": "悬疑",\n  "defaultMode": "driving",\n  "activeChapterId": "chapter-001"\n}\n',
                encoding="utf-8",
            )
            for relative, content in [
                ("outline.yaml", '{"chapters":[],"chapterDirections":[],"volumes":[]}'),
                ("entities.yaml", '{"entities":[],"enrichmentProposals":[]}'),
                ("timeline.yaml", '{"events":[]}'),
                ("branches.yaml", '{"branches":[]}'),
                ("threads.yaml", '{"threads":[]}'),
                ("structures.yaml", '{"activeStructure":null,"mappings":[]}'),
                ("proposals/draft-proposals.yaml", '{"draftProposals":[]}'),
                ("reviews/change-requests.yaml", '{"changeRequests":[]}'),
                ("reviews/story-reviews.yaml", '{"rubricVersion":"chapter-review-v1","chapterReviews":[]}'),
                ("projections/projection.yaml", '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}'),
                ("projections/context-lens.yaml", '{"currentChapterId":null,"lenses":[]}'),
                ("logs/projection-log.yaml", '{"projectionChanges":[]}'),
            ]:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content + "\n", encoding="utf-8")

            state = load_project_state(root)

            self.assertEqual(state["project"]["genre"], "悬疑")
            self.assertEqual(state["project"]["positioning"]["primaryGenre"], "")
            self.assertEqual(state["project"]["positioning"]["styleTags"], [])
            self.assertEqual(state["project"]["storyContract"]["corePromises"], [])
            self.assertEqual(state["project"]["commercialPositioning"]["hookStack"], [])
            self.assertEqual(state["project"]["commercialPositioning"]["chapterWordTarget"], 0)
            self.assertEqual(state["story_reviews"]["sceneRubricVersion"], "scene-review-v1")
            self.assertEqual(state["story_reviews"]["sceneReviews"], [])
            self.assertEqual(state["workflow_progress"]["currentStage"], "")
            self.assertEqual(state["workflow_progress"]["gateHistory"], [])




if __name__ == "__main__":
    unittest.main()
