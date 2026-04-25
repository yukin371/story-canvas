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

from story_harness_cli.protocol.style_profiles import (
    choose_style_profile_name,
    get_default_style_profiles,
    resolve_style_profile,
)


class StyleProfilesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-style-profile-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_defaults_include_expected_profiles(self) -> None:
        defaults = get_default_style_profiles()
        self.assertIn("default", defaults)
        self.assertIn("web-serial-zh", defaults)
        self.assertIn("literary-zh", defaults)
        self.assertIn("xuanhuan-zh", defaults)

    def test_load_with_project_override_merges_profile(self) -> None:
        custom = {
            "profiles": {
                "web-serial-zh": {
                    "patternThresholds": {"formulaicTransition": 4.0},
                    "extraPatterns": {"hedgeAdverbs": [r"蓦地"]},
                    "termPolicy": {
                        "watchTerms": ["归墟潮"],
                        "allowRepeated": ["蝴蝶效应"],
                        "perTermThresholds": {"归墟潮": 4},
                    },
                    "registerPolicy": {
                        "allowTerms": ["时间框架"],
                        "disallowedCategories": [
                            {
                                "id": "modern-planning",
                                "label": "现代项目管理语汇",
                                "terms": ["优先级"],
                                "suggestion": "避免使用现代项目管理语汇。",
                            }
                        ],
                    },
                    "framePolicy": {
                        "allowPrefixes": ["前世的"],
                        "perPrefixThresholds": {"前世的": 4},
                    },
                }
            }
        }
        (self.temp_dir / "style-profiles.yaml").write_text(json.dumps(custom, ensure_ascii=False), encoding="utf-8")

        profile, source = resolve_style_profile(self.temp_dir, "web-serial-zh")

        self.assertEqual(source, "project")
        self.assertEqual(profile["patternThresholds"]["formulaicTransition"], 4.0)
        self.assertIn(r"蓦地", profile["extraPatterns"]["hedgeAdverbs"])
        self.assertIn("归墟潮", profile["termPolicy"]["watchTerms"])
        self.assertIn("蝴蝶效应", profile["termPolicy"]["allowRepeated"])
        self.assertEqual(profile["termPolicy"]["perTermThresholds"]["归墟潮"], 4)
        self.assertIn("时间框架", profile["registerPolicy"]["allowTerms"])
        self.assertEqual(profile["registerPolicy"]["disallowedCategories"][0]["terms"], ["优先级"])
        self.assertIn("前世的", profile["framePolicy"]["allowPrefixes"])
        self.assertEqual(profile["framePolicy"]["perPrefixThresholds"]["前世的"], 4)

    def test_choose_profile_name_from_project_positioning(self) -> None:
        project = {"positioning": {"primaryGenre": "fantasy", "styleTags": ["web-serial"]}}
        self.assertEqual(choose_style_profile_name(project), "web-serial-zh")

        literary_project = {"positioning": {"primaryGenre": "literary", "styleTags": []}}
        self.assertEqual(choose_style_profile_name(literary_project), "literary-zh")

        xuanhuan_project = {"genre": "玄幻", "positioning": {"primaryGenre": "fantasy", "subGenre": "", "styleTags": []}}
        self.assertEqual(choose_style_profile_name(xuanhuan_project), "xuanhuan-zh")

        xuanhuan_subgenre_project = {
            "positioning": {"primaryGenre": "fantasy", "subGenre": "xuanhuan", "styleTags": []}
        }
        self.assertEqual(choose_style_profile_name(xuanhuan_subgenre_project), "xuanhuan-zh")

        default_project = {"positioning": {"primaryGenre": "mystery", "styleTags": []}}
        self.assertEqual(choose_style_profile_name(default_project), "default")


if __name__ == "__main__":
    unittest.main()
