from __future__ import annotations

import json
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


def _write_project(root: Path) -> None:
    for directory in ["chapters", "proposals", "reviews", "projections", "logs"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    files = {
        "project.yaml": {"title": "写作辅助测试", "activeChapterId": "chapter-001"},
        "outline.yaml": {
            "volumes": [{"id": "volume-001", "chapters": [{"id": "chapter-001", "title": "第一章"}]}],
            "chapters": [],
            "chapterDirections": [],
        },
        "entities.yaml": {
            "entities": [{"id": "char-lin", "name": "林舟", "type": "character", "aliases": []}],
            "enrichmentProposals": [],
        },
        "timeline.yaml": {"events": []},
        "branches.yaml": {"branches": []},
        "threads.yaml": {"threads": []},
        "structures.yaml": {"templates": []},
        "proposals/draft-proposals.yaml": {"draftProposals": []},
        "reviews/change-requests.yaml": {"changeRequests": []},
        "reviews/story-reviews.yaml": {"chapterReviews": [], "sceneReviews": [], "volumeSelfReviews": []},
        "projections/projection.yaml": {
            "snapshotProjections": [],
            "relationProjections": [],
            "sceneScopeProjections": [],
            "timelineProjections": [],
            "causalityProjections": [],
        },
        "projections/context-lens.yaml": {"currentChapterId": None, "lenses": []},
        "logs/projection-log.yaml": {"projectionChanges": []},
    }
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "chapters" / "chapter-001.md").write_text(
        "# 第一章\n\n林舟走进旧楼。林舟听见门后有响声。\n",
        encoding="utf-8",
    )


class WritingCommandTest(unittest.TestCase):
    def test_writing_assist_accepts_entity_only_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_project(root)
            buffer = StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "writing",
                        "assist",
                        "--root",
                        str(root),
                        "--chapter-id",
                        "chapter-001",
                        "--assistance-type",
                        "entity-only",
                    ]
                )
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["assistanceType"], "mention-only")
            self.assertEqual(payload["mentionSuggestions"][0]["name"], "林舟")

    def test_writing_auto_wrap_dry_run_does_not_write_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_project(root)
            chapter_file = root / "chapters" / "chapter-001.md"
            before = chapter_file.read_text(encoding="utf-8")
            buffer = StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "writing",
                        "auto-wrap",
                        "--root",
                        str(root),
                        "--chapter-id",
                        "chapter-001",
                        "--dry-run",
                    ]
                )
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertTrue(payload["dryRun"])
            self.assertTrue(payload["wouldUpdate"])
            self.assertEqual(before, chapter_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
