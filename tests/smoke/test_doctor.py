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


class DoctorSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-doctor-"))
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
        shutil.copytree(fixture_root, self.temp_dir, dirs_exist_ok=True)
        for relative in [
            "proposals",
            "reviews",
            "projections",
            "logs",
        ]:
            (self.temp_dir / relative).mkdir(exist_ok=True)
        (self.temp_dir / "threads.yaml").write_text('{"threads":[]}\n', encoding="utf-8")
        (self.temp_dir / "structures.yaml").write_text('{"activeStructure":null,"mappings":[]}\n', encoding="utf-8")
        (self.temp_dir / "proposals" / "draft-proposals.yaml").write_text('{"draftProposals":[]}\n', encoding="utf-8")
        (self.temp_dir / "reviews" / "change-requests.yaml").write_text('{"changeRequests":[]}\n', encoding="utf-8")
        (self.temp_dir / "reviews" / "story-reviews.yaml").write_text(
            '{"rubricVersion":"chapter-review-v1","chapterReviews":[]}\n',
            encoding="utf-8",
        )
        (self.temp_dir / "projections" / "projection.yaml").write_text(
            '{"snapshotProjections":[],"relationProjections":[],"sceneScopeProjections":[],"timelineProjections":[],"causalityProjections":[]}\n',
            encoding="utf-8",
        )
        (self.temp_dir / "projections" / "context-lens.yaml").write_text(
            '{"currentChapterId":"chapter-001","lenses":[]}\n',
            encoding="utf-8",
        )
        (self.temp_dir / "logs" / "projection-log.yaml").write_text('{"projectionChanges":[]}\n', encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_doctor_passes_for_minimal_project(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["errors"], 0)

    def test_doctor_fails_for_missing_chapter_file(self) -> None:
        (self.temp_dir / "chapters" / "chapter-001.md").unlink()
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertGreaterEqual(payload["summary"]["errors"], 1)

    def test_doctor_warns_for_missing_positioning_contract(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item["code"] for item in payload["checks"] if "code" in item}
        warning_items = [item for item in payload["checks"] if item["level"] == "warning"]

        self.assertEqual(exit_code, 0)
        self.assertIn("missing-target-audience", codes)
        self.assertIn("missing-core-promises", codes)
        self.assertIn("missing-core-emotions", codes)
        self.assertGreaterEqual(payload["summary"]["warnings"], len(warning_items))
        self.assertGreater(payload["summary"]["warnings"], 0)

    def test_doctor_warns_when_story_template_requires_worldbook(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["storyTemplate"] = {
            "id": "xianxia-rebirth-revenge-longform",
            "label": "仙侠重生复仇长篇",
            "modulePolicy": {
                "worldbook": "required",
                "worldRules": "required",
                "factions": "required",
            },
            "reviewFocus": [],
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") == "warning"}

        self.assertEqual(exit_code, 0)
        self.assertIn("missing-required-worldbook", codes)
        self.assertIn("missing-required-world-rules", codes)
        self.assertIn("missing-required-factions", codes)

    def test_doctor_warns_when_story_template_requires_foreshadow_and_character_state(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["storyTemplate"] = {
            "id": "mystery-longform",
            "label": "悬疑长篇",
            "modulePolicy": {
                "foreshadowLedger": "required",
                "characterStateTracking": "required",
            },
            "reviewFocus": [],
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") == "warning"}

        self.assertEqual(exit_code, 0)
        self.assertIn("missing-required-foreshadow-ledger", codes)
        self.assertIn("missing-character-state-tracking", codes)

    def test_doctor_reads_worldbook_when_present(self) -> None:
        (self.temp_dir / "worldbook.yaml").write_text(
            json.dumps(
                {
                    "premiseFacts": [{"id": "wf-001", "label": "时间线偏移", "fact": "世界线改变"}],
                    "worldRules": [{"id": "rule-001", "label": "代价", "rule": "力量有代价"}],
                    "factions": [{"id": "faction-001", "name": "青云宗"}],
                    "locations": [],
                    "artifacts": [],
                    "mysteries": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["storyTemplate"] = {
            "id": "xianxia-rebirth-revenge-longform",
            "label": "仙侠重生复仇长篇",
            "modulePolicy": {
                "worldbook": "required",
                "worldRules": "required",
                "factions": "required",
            },
            "reviewFocus": [],
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") == "warning"}

        self.assertEqual(exit_code, 0)
        self.assertNotIn("missing-required-worldbook", codes)
        self.assertNotIn("missing-required-world-rules", codes)
        self.assertNotIn("missing-required-factions", codes)

    def test_doctor_warns_for_missing_commercial_blueprint_on_serial_project(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["positioning"] = {
            "primaryGenre": "fantasy",
            "subGenre": "urban-occult",
            "styleTags": ["web-serial"],
            "targetAudience": ["qidian-reader"],
        }
        project["storyContract"] = {
            "corePromises": ["每章留钩子"],
            "avoidances": [],
            "endingContract": "",
            "paceContract": "中快节奏",
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") in {"warning", "info"} and item.get("code")}

        self.assertEqual(exit_code, 0)
        self.assertIn("missing-commercial-premise", codes)
        self.assertIn("missing-commercial-hook-line", codes)
        self.assertIn("missing-commercial-target-platform", codes)

    def test_doctor_uses_project_commercial_word_targets(self) -> None:
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["positioning"] = {
            "primaryGenre": "fantasy",
            "subGenre": "urban-occult",
            "styleTags": ["web-serial"],
            "targetAudience": ["qidian-reader"],
        }
        project["storyContract"] = {
            "corePromises": ["每章留钩子"],
            "avoidances": [],
            "endingContract": "",
            "paceContract": "中快节奏",
        }
        project["commercialPositioning"] = {
            "premise": "夜班接尸人继承城隍夜巡牌",
            "hookLine": "夜班抬尸抬到厉鬼名册，普通人被迫上岗做城隍夜巡。",
            "hookStack": ["unit-case", "cliffhanger-end"],
            "benchmarkWorks": ["都市职业捉诡文"],
            "targetPlatform": "qidian",
            "serializationModel": "单元案推进长线阴谋",
            "releaseCadence": "日更两章",
            "chapterWordFloor": 2500,
            "chapterWordTarget": 3200,
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        short_chapter_items = [item for item in payload["checks"] if item.get("code") == "chapter-below-minimum"]

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(short_chapter_items), 1)
        self.assertIn("最低 2500 字", short_chapter_items[0]["message"])

    def test_doctor_warns_for_short_chapter_by_default(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        short_chapter_items = [item for item in payload["checks"] if item.get("code") == "chapter-below-minimum"]
        self.assertEqual(len(short_chapter_items), 1)
        self.assertIn("chapter-001", short_chapter_items[0]["message"])
        self.assertIn("最低 2000 字", short_chapter_items[0]["message"])

    def test_doctor_reports_gap_to_target_with_custom_thresholds(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "doctor",
                    "--root",
                    str(self.temp_dir),
                    "--min-chapter-words",
                    "100",
                    "--target-chapter-words",
                    "300",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        target_gap_items = [item for item in payload["checks"] if item.get("code") == "chapter-below-target"]
        self.assertEqual(len(target_gap_items), 1)
        self.assertIn("建议 300 字", target_gap_items[0]["message"])

    def test_doctor_warns_when_chapter_has_no_outline_gate(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        outline_items = [item for item in payload["checks"] if item.get("code") == "chapter-outline-not-ready"]
        self.assertEqual(len(outline_items), 1)
        self.assertIn("chapter-001", outline_items[0]["message"])

    def test_doctor_passes_for_layered_project(self) -> None:
        """Doctor should pass for a layered (spec/ dir) project layout."""
        # Create spec/ directory and move spec files there
        spec_dir = self.temp_dir / "spec"
        spec_dir.mkdir(exist_ok=True)
        for fname in ["outline.yaml", "entities.yaml", "timeline.yaml", "threads.yaml", "structures.yaml"]:
            src = self.temp_dir / fname
            if src.exists():
                src.rename(spec_dir / fname)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["errors"], 0)

    def test_doctor_reports_style_profile_override(self) -> None:
        (self.temp_dir / "style-profiles.yaml").write_text(
            json.dumps(
                {
                    "profiles": {
                        "web-serial-zh": {
                            "patternThresholds": {"formulaicTransition": 4.0}
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["positioning"] = {
            "primaryGenre": "fantasy",
            "subGenre": "urban-occult",
            "styleTags": ["web-serial"],
            "targetAudience": ["qidian-reader"],
        }
        (self.temp_dir / "project.yaml").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"]}

        self.assertEqual(exit_code, 0)
        self.assertIn("active-style-profile", codes)
        self.assertIn("parsed-style-profiles", codes)
        self.assertIn("style-profile-override", codes)

    def test_doctor_warns_for_invalid_style_profile_shape(self) -> None:
        (self.temp_dir / "style-profiles.yaml").write_text(
            json.dumps(
                {
                    "profiles": {
                        "web-serial-zh": {
                            "patternThresholds": {"formulaicTransition": 0},
                            "extraPatterns": {"hedgeAdverbs": "蓦地"},
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") == "warning"}

        self.assertEqual(exit_code, 0)
        self.assertIn("invalid-style-threshold-value", codes)
        self.assertIn("invalid-style-pattern-list", codes)

    def test_doctor_warns_for_missing_illustration_asset(self) -> None:
        (self.temp_dir / "illustrations.yaml").write_text(
            json.dumps(
                {
                    "adapter": {
                        "name": "openai",
                        "model": "gpt-image-2",
                        "defaultSize": "1024x1024",
                        "quality": "standard",
                    },
                    "promptPack": {"name": "default", "version": "builtin"},
                    "generated": [
                        {
                            "id": "ill-001",
                            "type": "chapter",
                            "mode": "text-to-image",
                            "chapterId": "chapter-001",
                            "entityId": None,
                            "promptText": "test",
                            "revisedPrompt": "test",
                            "inputImages": [],
                            "maskPath": "",
                            "filePath": str(self.temp_dir / "assets" / "illustrations" / "chapter-001_scene.png"),
                            "artifacts": [
                                {
                                    "index": 0,
                                    "filePath": str(self.temp_dir / "assets" / "illustrations" / "chapter-001_scene.png"),
                                    "bytes": 4,
                                    "source": "b64_json",
                                    "extension": "png",
                                    "isPrimary": True,
                                }
                            ],
                            "metadata": {"assetCount": 1},
                            "generatedAt": "2026-04-25T00:00:00+08:00",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") == "warning"}

        self.assertEqual(exit_code, 0)
        self.assertIn("missing-illustration-asset", codes)

    def test_doctor_reports_orphan_illustration_asset(self) -> None:
        asset_dir = self.temp_dir / "assets" / "illustrations"
        asset_dir.mkdir(parents=True, exist_ok=True)
        (asset_dir / "orphan.png").write_bytes(b"orphan")

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"]}
        orphan_items = [item for item in payload["checks"] if item.get("code") == "orphan-illustration-asset"]

        self.assertEqual(exit_code, 0)
        self.assertIn("orphan-illustration-asset", codes)
        self.assertEqual(len(orphan_items), 1)
        self.assertIn("assets", orphan_items[0]["message"])

    def test_doctor_warns_for_missing_illustration_target_and_inputs(self) -> None:
        missing_reference = self.temp_dir / "missing-reference.png"
        missing_mask = self.temp_dir / "missing-mask.png"
        (self.temp_dir / "illustrations.yaml").write_text(
            json.dumps(
                {
                    "adapter": {
                        "name": "openai",
                        "model": "gpt-image-2",
                        "defaultSize": "1024x1024",
                        "quality": "standard",
                    },
                    "promptPack": {"name": "default", "version": "builtin"},
                    "generated": [
                        {
                            "id": "ill-broken",
                            "type": "chapter",
                            "mode": "image-to-image",
                            "chapterId": "chapter-999",
                            "entityId": None,
                            "promptText": "test",
                            "revisedPrompt": "test",
                            "inputImages": [str(missing_reference)],
                            "maskPath": str(missing_mask),
                            "filePath": "",
                            "artifacts": [],
                            "metadata": {"assetCount": 0},
                            "generatedAt": "2026-04-25T00:00:00+08:00",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["doctor", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())
        codes = {item.get("code") for item in payload["checks"] if item.get("level") == "warning"}

        self.assertEqual(exit_code, 0)
        self.assertIn("illustration-target-not-found", codes)
        self.assertIn("illustration-input-not-found", codes)
        self.assertIn("illustration-mask-not-found", codes)


if __name__ == "__main__":
    unittest.main()
