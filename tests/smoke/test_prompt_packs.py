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

from story_harness_cli.protocol.prompt_packs import (
    default_pack_ref_from_name,
    load_available_prompt_packs,
    resolve_prompt_pack,
    save_prompt_pack_document,
    serialize_prompt_pack_document,
    summarize_prompt_pack,
)


class PromptPackProtocolSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-prompt-packs-"))
        self.packs_dir = self.temp_dir / "prompts" / "illustration-packs"
        self.packs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_available_prompt_packs_normalizes_project_pack(self) -> None:
        raw_pack = {
            "label": "Noir Pack",
            "supports": {"commercial": True},
            "templates": [
                {
                    "id": "scene-noir",
                    "useCase": "chapter-scene",
                    "promptTemplate": "{subject}\n{userExtraPrompt}",
                },
                {
                    "label": "invalid-without-id",
                    "useCase": "chapter-scene",
                },
            ],
            "modifierGroups": [
                {
                    "id": "lighting-harsh",
                    "label": "硬光",
                    "promptFragment": "hard shadow",
                },
                {
                    "id": "lighting-harsh",
                    "label": "duplicate",
                },
            ],
            "policies": {
                "negativePolicies": [
                    {
                        "id": "safe-default",
                        "negativePrompt": "blurry",
                    }
                ],
                "commercialPolicies": [
                    {
                        "id": "commercial-default",
                        "extraPrompt": "clean deliverable",
                        "restrictions": ["no-logo-imitation"],
                    }
                ],
            },
        }
        pack_path = self.packs_dir / "custom-noir.yaml"
        pack_path.write_text(json.dumps(raw_pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        packs = load_available_prompt_packs(self.temp_dir)
        project_pack = next(pack for pack in packs if pack["id"] == "project/custom-noir")

        self.assertEqual(project_pack["source"], "project")
        self.assertEqual(project_pack["sourceFile"], str(pack_path))
        self.assertEqual(project_pack["version"], "project")
        self.assertEqual(project_pack["label"], "Noir Pack")
        self.assertEqual(project_pack["supports"]["modes"], ["text-to-image"])
        self.assertTrue(project_pack["supports"]["commercial"])
        self.assertEqual(len(project_pack["templates"]), 1)
        self.assertEqual(project_pack["templates"][0]["mode"], "text-to-image")
        self.assertEqual(project_pack["templates"][0]["complexity"], "standard")
        self.assertEqual(project_pack["templates"][0]["packId"], "project/custom-noir")
        self.assertEqual(len(project_pack["modifierGroups"]), 1)
        self.assertEqual(project_pack["modifierGroups"][0]["group"], "style")
        self.assertEqual(project_pack["policies"]["negativePolicies"][0]["label"], "safe-default")
        self.assertEqual(project_pack["policies"]["commercialPolicies"][0]["mode"], "personal")

    def test_resolve_prompt_pack_prefers_explicit_project_pack_and_summary_keeps_policy_meta(self) -> None:
        raw_pack = {
            "id": "project/storm-promo",
            "version": "2.0",
            "label": "Storm Promo",
            "templates": [
                {
                    "id": "promo-storm",
                    "label": "Storm Poster",
                    "useCase": "promo",
                    "mode": "text-to-image",
                    "complexity": "detailed",
                    "promptTemplate": "{subject}\n{styleModifiers}\n{commercialPrompt}",
                    "defaultCommercialPolicyRef": "commercial-default",
                }
            ],
            "policies": {
                "commercialPolicies": [
                    {
                        "id": "commercial-default",
                        "label": "Commercial",
                        "mode": "commercial",
                        "extraPrompt": "brand-safe presentation",
                        "restrictions": ["no-logo-imitation", "no-trademark-style-copy"],
                    }
                ]
            },
        }
        (self.packs_dir / "storm-promo.yaml").write_text(
            json.dumps(raw_pack, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        resolution = resolve_prompt_pack(
            self.temp_dir,
            {"promptSystem": {"defaultPack": default_pack_ref_from_name("default")}},
            "storm-promo",
        )
        summary = summarize_prompt_pack(resolution["pack"])

        self.assertEqual(resolution["packRef"]["source"], "project")
        self.assertEqual(resolution["packRef"]["packId"], "project/storm-promo")
        self.assertEqual(resolution["packName"], "storm-promo")
        self.assertEqual(summary["source"], "project")
        self.assertEqual(summary["commercialPolicies"][0]["id"], "commercial-default")
        self.assertEqual(
            summary["commercialPolicies"][0]["restrictions"],
            ["no-logo-imitation", "no-trademark-style-copy"],
        )

    def test_save_prompt_pack_document_writes_user_pack_without_builtin_shadowing(self) -> None:
        saved = save_prompt_pack_document(
            self.temp_dir,
            {
                "label": "Workspace Noir",
                "templates": [
                    {
                        "id": "scene-standard",
                        "label": "Noir Scene",
                        "useCase": "chapter-scene",
                        "mode": "text-to-image",
                        "promptTemplate": "{subject}\nnoir alley\n{userExtraPrompt}",
                    }
                ],
                "modifierGroups": [
                    {
                        "id": "lighting-harsh",
                        "label": "硬光",
                        "promptFragment": "hard shadow",
                    }
                ],
                "policies": {
                    "commercialPolicies": [
                        {
                            "id": "personal-default",
                            "extraPrompt": "",
                        }
                    ]
                },
            },
            file_name="workspace-noir",
        )
        saved_document = serialize_prompt_pack_document(saved)
        saved_path = self.packs_dir / "workspace-noir.yaml"

        self.assertTrue(saved_path.exists())
        self.assertEqual(saved["id"], "project/workspace-noir")
        self.assertEqual(saved["source"], "project")
        self.assertEqual(saved["sourceFile"], str(saved_path))
        self.assertTrue(saved_document["writable"])
        self.assertEqual(saved_document["templates"][0]["promptTemplate"], "{subject}\nnoir alley\n{userExtraPrompt}")

        on_disk = json.loads(saved_path.read_text(encoding="utf-8"))
        self.assertNotIn("source", on_disk)
        self.assertEqual(on_disk["templates"][0]["id"], "scene-standard")
        self.assertEqual(on_disk["modifierGroups"][0]["promptFragment"], "hard shadow")

    def test_save_prompt_pack_document_rejects_builtin_pack_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "系统 pack id"):
            save_prompt_pack_document(
                self.temp_dir,
                {
                    "id": "story-canvas/default",
                    "label": "Illegal Override",
                },
                file_name="illegal-override",
            )


if __name__ == "__main__":
    unittest.main()
