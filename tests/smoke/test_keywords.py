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

from story_harness_cli.protocol.keywords import get_defaults, load_keywords, merge_with_defaults
from story_harness_cli.utils.text import (
    STATE_KEYWORDS,
    set_keywords,
    state_tags_for_paragraph,
    _kw_override,
)


class KeywordsDefaultTest(unittest.TestCase):
    def test_defaults_contain_all_keys(self):
        defaults = get_defaults()
        for key in ("state", "relation", "appearance", "ability", "activeBehavior", "intimate", "negationPrefixes"):
            self.assertIn(key, defaults)

    def test_defaults_match_builtin(self):
        defaults = get_defaults()
        self.assertEqual(defaults["state"], dict(STATE_KEYWORDS))


class KeywordsCustomTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-kw-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Reset module-level override
        import story_harness_cli.utils.text as _text_mod
        _text_mod._kw_override = None

    def test_load_without_file_uses_defaults(self):
        kw = load_keywords(self.temp_dir)
        self.assertEqual(kw["state"], dict(STATE_KEYWORDS))

    def test_load_with_custom_file(self):
        custom = {"state": {"狂暴": "狂暴"}, "relation": {"狂暴": ["失控", "high-risk"]}}
        (self.temp_dir / "keywords.yaml").write_text(json.dumps(custom, ensure_ascii=False), encoding="utf-8")
        kw = load_keywords(self.temp_dir)
        # Custom overrides state
        self.assertEqual(kw["state"], {"狂暴": "狂暴"})
        # Non-overridden keys keep defaults
        self.assertIn("appearance", kw)
        self.assertIsInstance(kw["appearance"], dict)

    def test_merge_partial(self):
        custom = {"state": {"新词": "新标签"}}
        merged = merge_with_defaults(custom)
        self.assertEqual(merged["state"], {"新词": "新标签"})
        # Other keys untouched
        self.assertIn("受伤", get_defaults()["state"])

    def test_set_keywords_affects_tag_extraction(self):
        import story_harness_cli.utils.text as _text_mod
        _text_mod._kw_override = {"state": {"狂暴": "狂暴"}, "relation": {}, "appearance": {}, "ability": {}}
        tags = state_tags_for_paragraph("他变得狂暴无比")
        self.assertIn("狂暴", tags)
        # Default keyword "受伤" should NOT match when override is active
        tags2 = state_tags_for_paragraph("他受伤了")
        self.assertNotIn("受伤", tags2)

    def test_state_keywords_ignore_direct_negation(self):
        tags = state_tags_for_paragraph("她的手指没有离开屏幕，伤口也并未流血。")
        self.assertNotIn("离开", tags)
        self.assertNotIn("流血", tags)

        positive_tags = state_tags_for_paragraph("她终于离开会议室，手臂开始流血。")
        self.assertIn("离开", positive_tags)
        self.assertIn("流血", positive_tags)


if __name__ == "__main__":
    unittest.main()
