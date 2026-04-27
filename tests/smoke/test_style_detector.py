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
        self.assertTrue(any(item["ruleId"] == "specialTermRepetition" for item in result["judgements"]))

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

    def test_detect_ai_style_flags_register_drift_terms(self) -> None:
        paragraphs = [
            "沈玄先把所有线索整合成一个时间框架。",
            "第一优先级是隐藏归墟体，第二优先级是站稳脚跟。",
            "他决定暂时不再用这种框架式的说法。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(
            paragraphs,
            clean_text,
            profile_config={
                "registerPolicy": {
                    "disallowedCategories": [
                        {
                            "id": "modern-planning",
                            "label": "现代项目管理语汇",
                            "terms": ["时间框架", "优先级", "框架"],
                            "suggestion": "避免使用现代项目管理语汇。",
                        }
                    ]
                }
            },
        )
        pattern = next(item for item in result["patternResults"] if item["id"] == "registerDrift")

        self.assertTrue(pattern["detected"])
        self.assertIn("优先级", "".join(pattern["evidence"]))
        judgement = next(item for item in result["judgements"] if item["ruleId"] == "registerDrift")
        self.assertEqual(judgement["kind"], "style")
        self.assertEqual(judgement["source"], "genre-pack")

    def test_detect_ai_style_flags_structured_plan_block(self) -> None:
        paragraphs = [
            "目标：先压住体内失控的潮息。\n风险：顾长渊可能提前察觉异样。",
            "约束：不能在宗门长老面前暴露归墟体。\n时间窗口：只剩今夜到天明前这段空档。",
            "沈玄意识到自己又把念头排成了清单，连呼吸都带着不合时宜的执行味道。",
        ]
        clean_text = "".join(paragraphs) * 3

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "structuredPlanBlock")

        self.assertTrue(pattern["detected"])
        self.assertIn("目标：", "".join(pattern["evidence"]))
        judgement = next(item for item in result["judgements"] if item["ruleId"] == "structuredPlanBlock")
        self.assertEqual(judgement["kind"], "style")
        self.assertEqual(judgement["source"], "core")

    def test_detect_ai_style_respects_plan_block_allow_labels(self) -> None:
        paragraphs = [
            "目标：先压住体内失控的潮息。\n风险：顾长渊可能提前察觉异样。",
            "约束：不能在宗门长老面前暴露归墟体。\n时间窗口：只剩今夜到天明前这段空档。",
        ]
        clean_text = "".join(paragraphs) * 4

        result = detect_ai_style(
            paragraphs,
            clean_text,
            profile_config={"planBlockPolicy": {"allowLabels": ["目标", "风险", "约束", "时间窗口"]}},
        )
        pattern = next(item for item in result["patternResults"] if item["id"] == "structuredPlanBlock")

        self.assertFalse(pattern["detected"])

    def test_detect_ai_style_respects_register_allow_terms(self) -> None:
        paragraphs = [
            "沈玄先把所有线索整合成一个时间框架。",
            "第一优先级是隐藏归墟体。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(
            paragraphs,
            clean_text,
            profile_config={
                "registerPolicy": {
                    "allowTerms": ["时间框架", "优先级"],
                    "disallowedCategories": [
                        {
                            "id": "modern-planning",
                            "label": "现代项目管理语汇",
                            "terms": ["时间框架", "优先级"],
                            "suggestion": "避免使用现代项目管理语汇。",
                        }
                    ],
                }
            },
        )
        pattern = next(item for item in result["patternResults"] if item["id"] == "registerDrift")

        self.assertFalse(pattern["detected"])

    def test_detect_ai_style_flags_repeated_narrative_frames(self) -> None:
        paragraphs = [
            "前世的记忆在他心里翻涌，让他不敢轻信眼前的一切。",
            "前世的经验提醒他，越是看似平静的局面越藏着杀机。",
            "前世的判断曾救过他一次，可这一次他不想再完全依赖旧路。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "narrativeFrameRepetition")

        self.assertTrue(pattern["detected"])
        self.assertIn("前世的", "".join(pattern["evidence"]))

    def test_detect_ai_style_flags_contrast_flip_patterns(self) -> None:
        paragraphs = [
            "那不是犹豫，是多年压下去的旧火重新顶了上来。",
            "这不是侥幸，不是误打误撞，是他早就留在袖里的后手。",
            "他没有再退，只让那点发烫的念头继续往前推。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "contrastFlipPattern")

        self.assertTrue(pattern["detected"])
        self.assertIn("不是", "".join(pattern["evidence"]))
        self.assertTrue(any(item["ruleId"] == "contrastFlipPattern" for item in result["judgements"]))

    def test_detect_ai_style_flags_analogical_pivot_patterns(self) -> None:
        paragraphs = [
            "那不像试探，更像有人故意把门缝留给他。",
            "这不是风声。更像旧灯室深处有人轻轻拨了一下灯芯。",
            "他越往里走，越觉得那股旧意不是在提醒，更像在把他往深处拽。",
        ]
        clean_text = "".join(paragraphs) * 2

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "analogicalPivotPattern")

        self.assertTrue(pattern["detected"])
        self.assertIn("更像", "".join(pattern["evidence"]))
        self.assertTrue(any(item["ruleId"] == "analogicalPivotPattern" for item in result["judgements"]))

    def test_detect_ai_style_flags_template_catchphrases(self) -> None:
        paragraphs = [
            "真正值钱的，从来都是这盏灯现在指着的地方。",
            "岳怀川压低声音问了一句：“还有什么？”",
            "沈照没有立刻回答，可那句追问还在耳边一下一下敲着。",
        ]
        clean_text = "".join(paragraphs) * 3

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "templateCatchphrasePattern")

        self.assertTrue(pattern["detected"])
        self.assertTrue(any("真正值钱的" in item or "还有什么" in item for item in pattern["evidence"]))
        self.assertTrue(any(item["ruleId"] == "templateCatchphrasePattern" for item in result["judgements"]))

    def test_detect_ai_style_flags_paragraph_readability(self) -> None:
        paragraphs = [
            "沈照沿着废灯棚外那条狭窄的灰沟慢慢往前挪，脚下每一块松动的砖都像会突然塌下去，他一边盯着风里晃动的残灯，一边还得分神去记那些被夜色吞没的脚印、火痕和断裂木梁的位置，整个人绷得像一根被拉到快断的旧弦。",
            "岳怀川跟在后面，同样没有开口，只是把呼吸压得更轻，可他眼角的余光始终在扫四周那些被烟熏黑的墙角、塌陷的梁柱和半埋在灰里的旧灯座，像是生怕下一瞬又有什么被人从黑暗里轻轻拨动，让他们前面所有的判断都变成了更深一层的误导。",
            "短段落用来形成对比。",
        ]
        clean_text = "".join(paragraphs)

        result = detect_ai_style(paragraphs, clean_text)
        pattern = next(item for item in result["patternResults"] if item["id"] == "paragraphReadability")

        self.assertTrue(pattern["detected"])
        self.assertGreaterEqual(pattern["count"], 2)
        self.assertIn("第1段", "".join(pattern["evidence"]))
        self.assertTrue(any(item["ruleId"] == "paragraphReadability" for item in result["judgements"]))

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
