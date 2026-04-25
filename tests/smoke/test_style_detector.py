from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services.style_detector import detect_ai_style


class StyleDetectorTests(unittest.TestCase):
    def test_detect_ai_style_uses_builtin_repetition_fallback(self) -> None:
        paragraphs = [
            "他慢慢走进屋里，手指还按在门框上。",
            "他慢慢停在桌前，视线落在杯口裂痕。",
            "他慢慢抬起头来，像在等对面先开口。",
        ]
        clean_text = "".join(paragraphs) * 3

        result = detect_ai_style(paragraphs, clean_text)

        self.assertTrue(result["sentenceRepetition"]["hasRepetition"])
        self.assertEqual(result["sentenceRepetition"]["source"], "builtin")
        self.assertEqual(result["sources"]["sentenceRepetition"], "builtin")

    def test_detect_ai_style_accepts_injected_similarity_scorer(self) -> None:
        paragraphs = [
            "他慢慢走进屋里，手指还按在门框上。",
            "她慢慢停在桌前，视线落在杯口裂痕。",
            "它慢慢抬起头来，像在等对面先开口。",
        ]
        clean_text = "".join(paragraphs) * 3

        def score(left: str, right: str) -> float:
            return 95.0 if left[1:3] == right[1:3] else 0.0

        result = detect_ai_style(
            paragraphs,
            clean_text,
            opener_similarity_scorer=score,
            repetition_source="rapidfuzz",
        )

        self.assertTrue(result["sentenceRepetition"]["hasRepetition"])
        self.assertEqual(result["sentenceRepetition"]["source"], "rapidfuzz")

    def test_load_style_similarity_scorer_uses_optional_dependency_when_available(self) -> None:
        rapidfuzz_module = types.ModuleType("rapidfuzz")
        rapidfuzz_module.fuzz = types.SimpleNamespace(ratio=lambda left, right: 91 if left != right else 100)

        with patch.dict(sys.modules, {"rapidfuzz": rapidfuzz_module}):
            scorer, source = load_style_similarity_scorer()

        self.assertIsNotNone(scorer)
        self.assertEqual(source, "rapidfuzz")
        assert scorer is not None
        self.assertEqual(scorer("甲乙", "甲丙"), 91.0)


if __name__ == "__main__":
    unittest.main()
