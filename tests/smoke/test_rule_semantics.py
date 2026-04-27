from __future__ import annotations

import re
import unittest
from pathlib import Path

from story_harness_cli.services.rule_registry import get_rule_definition
from story_harness_cli.services.rule_semantics import build_rule_judgement


class RuleSemanticsTests(unittest.TestCase):
    def test_build_rule_judgement_uses_registry_defaults(self) -> None:
        judgement = build_rule_judgement(
            rule_id="capabilityTaskMismatch",
            message="检测到角色能力与任务门槛可能不匹配。",
        )

        self.assertEqual(judgement["source"], "core")
        self.assertEqual(judgement["scope"], "chapter")
        self.assertEqual(judgement["kind"], "soft")
        self.assertEqual(judgement["severity"], "warning")
        self.assertIn("plausibility", judgement["tags"])

    def test_build_rule_judgement_allows_metadata_override(self) -> None:
        judgement = build_rule_judgement(
            rule_id="registerDrift",
            source="genre-pack",
            severity="high",
            message="检测到题材语域失真。",
        )

        self.assertEqual(judgement["source"], "genre-pack")
        self.assertEqual(judgement["scope"], "chapter")
        self.assertEqual(judgement["kind"], "style")
        self.assertEqual(judgement["severity"], "high")

    def test_build_rule_judgement_merges_registry_tags_with_extra_tags(self) -> None:
        judgement = build_rule_judgement(
            rule_id="registerDrift",
            message="检测到题材语域失真。",
            tags=["style", "workflow"],
        )

        self.assertEqual(judgement["tags"], ["style", "register-policy", "workflow"])

    def test_build_rule_judgement_inherits_project_gate_alias_metadata(self) -> None:
        judgement = build_rule_judgement(
            rule_id="project-missing-target-audience",
            scope="chapter",
            kind="gate",
            severity="warning",
            message="项目前置约束未完成：缺少 targetAudience",
        )

        self.assertEqual(judgement["source"], "core")
        self.assertEqual(judgement["scope"], "chapter")
        self.assertEqual(judgement["kind"], "gate")
        self.assertEqual(judgement["severity"], "warning")
        self.assertIn("project-gate", judgement["tags"])

    def test_doctor_literal_record_check_codes_are_registered(self) -> None:
        doctor_path = Path(__file__).resolve().parents[2] / "src" / "story_harness_cli" / "commands" / "doctor.py"
        content = doctor_path.read_text(encoding="utf-8")
        codes = set(
            re.findall(
                r'record_check\(\s*checks,\s+"(?:warning|error|info)",\s+"([^"]+)"',
                content,
                re.S,
            )
        )

        self.assertTrue(codes)
        missing = sorted(code for code in codes if not get_rule_definition(code))
        self.assertEqual(missing, [])

    def test_dynamic_doctor_service_warning_codes_are_registered(self) -> None:
        service_root = Path(__file__).resolve().parents[2] / "src" / "story_harness_cli" / "services"
        dynamic_code_families = {
            "thread.py": "thread",
            "arc.py": "arc",
            "structure.py": "structure",
        }

        missing: list[str] = []
        for filename, prefix in dynamic_code_families.items():
            content = (service_root / filename).read_text(encoding="utf-8")
            warning_types = set(re.findall(r'"type":\s*"([^"]+)"', content))
            missing.extend(
                sorted(
                    code
                    for code in (f"{prefix}-{warning_type}" for warning_type in warning_types)
                    if not get_rule_definition(code)
                )
            )

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
