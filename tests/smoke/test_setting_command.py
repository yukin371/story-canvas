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
        "project.yaml": {
            "title": "模板测试",
            "positioning": {"primaryGenre": "fantasy"},
            "storyContract": {"corePromises": ["每章推进一个异象谜团"]},
        },
        "outline.yaml": {
            "volumes": [
                {
                    "id": "volume-001",
                    "title": "第一卷",
                    "chapters": [{"id": "chapter-001", "title": "第一章"}],
                }
            ],
            "chapters": [],
            "chapterDirections": [],
        },
        "entities.yaml": {
            "entities": [{"id": "char-lin", "name": "林舟", "type": "character"}],
            "enrichmentProposals": [],
        },
        "timeline.yaml": {"events": []},
        "branches.yaml": {"branches": []},
        "threads.yaml": {"threads": []},
        "structures.yaml": {"templates": []},
        "worldbook.yaml": {"worldRules": [{"id": "rule-1", "rule": "夜巡牌只在子夜后响应。"}]},
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


class SettingCommandTest(unittest.TestCase):
    def test_setting_template_lists_builtin_genres(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            result = main(["setting", "template", "--list"])
        self.assertEqual(result, 0)
        output = buffer.getvalue()
        self.assertIn("fantasy: 奇幻", output)
        self.assertIn("mystery: 悬疑", output)

    def test_setting_assess_uses_explicit_root_and_project_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_project(root)
            buffer = StringIO()
            with redirect_stdout(buffer):
                result = main(["setting", "assess", "--root", str(root), "--format", "json"])
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertGreater(payload["readinessPercent"], 0)
            self.assertNotIn("缺少卷级结构", payload["issues"])

    def test_setting_expand_outputs_prompt_without_missing_provider_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_project(root)
            buffer = StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "setting",
                        "expand",
                        "--root",
                        str(root),
                        "--stage",
                        "1",
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertIn(payload["status"], {"prompt-ready", "low_readiness"})


if __name__ == "__main__":
    unittest.main()
