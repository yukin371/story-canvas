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

from story_harness_cli.protocol.review_rules import (
    get_default_review_rules_config,
    load_review_rules,
    resolve_review_rule_profile,
)


class ReviewRulesProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-review-rules-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_defaults_include_default_profile(self) -> None:
        config = get_default_review_rules_config()
        self.assertEqual(config["activeProfile"], "default")
        self.assertIn("default", config["profiles"])
        self.assertEqual(config["profiles"]["default"]["enabledRules"], [])
        self.assertEqual(config["profiles"]["default"]["exemptions"], [])

    def test_load_review_rules_normalizes_profile_and_exemptions(self) -> None:
        (self.temp_dir / "review-rules.yaml").write_text(
            json.dumps(
                {
                    "activeProfile": "novel-meta",
                    "profiles": {
                        "novel-meta": {
                            "enabledRules": ["metaLeakage", "metaLeakage", "povOverreach"],
                            "exemptions": [
                                {
                                    "ruleId": "metaLeakage",
                                    "scope": {
                                        "chapterIds": ["chapter-012", "chapter-012"],
                                        "scenePlanIds": ["scene-003"],
                                    },
                                    "allowWhen": {
                                        "quotedOnly": True,
                                        "matchPatterns": ["第[0-9一二三四五六七八九十]+章"],
                                    },
                                    "reason": "主角在讨论自己写的小说章节",
                                },
                                {
                                    "ruleId": "",
                                    "reason": "invalid should be dropped",
                                },
                            ],
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        config = load_review_rules(self.temp_dir)
        profile, resolved_name, source = resolve_review_rule_profile(self.temp_dir)

        self.assertEqual(config["activeProfile"], "novel-meta")
        self.assertEqual(resolved_name, "novel-meta")
        self.assertEqual(source, "project")
        self.assertEqual(profile["enabledRules"], ["metaLeakage", "povOverreach"])
        self.assertEqual(len(profile["exemptions"]), 1)
        exemption = profile["exemptions"][0]
        self.assertEqual(exemption["ruleId"], "metaLeakage")
        self.assertEqual(exemption["scope"]["chapterIds"], ["chapter-012"])
        self.assertEqual(exemption["scope"]["scenePlanIds"], ["scene-003"])
        self.assertTrue(exemption["allowWhen"]["quotedOnly"])
        self.assertEqual(exemption["allowWhen"]["matchPatterns"], ["第[0-9一二三四五六七八九十]+章"])
        self.assertEqual(exemption["reason"], "主角在讨论自己写的小说章节")

    def test_resolve_review_rule_profile_falls_back_to_default(self) -> None:
        (self.temp_dir / "review-rules.yaml").write_text(
            json.dumps(
                {
                    "activeProfile": "missing-profile",
                    "profiles": {
                        "custom": {
                            "enabledRules": ["metaLeakage"],
                            "exemptions": [],
                        }
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        profile, resolved_name, source = resolve_review_rule_profile(self.temp_dir)

        self.assertEqual(resolved_name, "default")
        self.assertEqual(source, "builtin")
        self.assertEqual(profile["enabledRules"], [])
        self.assertEqual(profile["exemptions"], [])


if __name__ == "__main__":
    unittest.main()
