from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from story_harness_cli.providers import load_style_similarity_scorer
from story_harness_cli.services.style_detector import detect_ai_style


class StyleDetectorTests(unittest.TestCase):
    def test_detect_ai_style_flags_repeated_special_terms(self) -> None:
        paragraphs = [
            "林舟第一次听见蝴蝶效应这个词，仍没意识到它会改变判断。",
            "沈昭又提起蝴蝶效应，像是在提醒他每个选择都会反噬。",
            "到了仓库门口，蝴蝶效应被第三次说出口，语气已经近乎口头禅。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "specialTermRepetition")

        self.assertTrue(pattern["detected"])
        self.assertIn("蝴蝶效应", "".join(pattern["evidence"]))

    def test_detect_ai_style_respects_allow_repeated_terms(self) -> None:
        paragraphs = [
            "林舟第一次听见蝴蝶效应这个词。",
            "沈昭第二次提起蝴蝶效应。",
            "第三次说起蝴蝶效应时，他已经不耐烦了。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(
            paragraphs,
            clean_text,
            profile_config={"termPolicy": {"allowRepeated": ["蝴蝶效应"]}},
        )
        pattern = next(item for item in result["patternResults"] if item["id"] == "specialTermRepetition")

        self.assertFalse(pattern["detected"])

    def test_detect_ai_style_uses_profile_watch_terms(self) -> None:
        paragraphs = [
            "林舟第一次听见归墟潮这个名字。",
            "第二段里，归墟潮再次被人提起。",
            "第三段中，归墟潮已经成了每个人嘴边的说法。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(
            paragraphs,
            clean_text,
            profile_config={"termPolicy": {"watchTerms": ["归墟潮"]}},
        )
        pattern = next(item for item in result["patternResults"] if item["id"] == "specialTermRepetition")

        self.assertTrue(pattern["detected"])
        self.assertIn("归墟潮", "".join(pattern["evidence"]))

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
