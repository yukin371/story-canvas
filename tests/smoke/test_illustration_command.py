from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main


def _load_story_canvas_ui_api_module():
    module_path = REPO_ROOT / "scripts" / "story_canvas_ui_api.py"
    spec = importlib.util.spec_from_file_location("story_canvas_ui_api", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IllustrationCommandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-illustration-"))
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "init",
                    "--root",
                    str(self.temp_dir),
                    "--title",
                    "Fog Harbor",
                    "--genre",
                    "Mystery",
                    "--primary-genre",
                    "mystery",
                    "--core-promise",
                    "异案持续升级",
                    "--pace-contract",
                    "中快节奏",
                ]
            )
        self.assertEqual(exit_code, 0)

        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 第一章\n\n林舟推开仓库铁门，雨水顺着衣角往下淌。墙角的木箱被人撬开，露出半截烧焦的账册。\n",
            encoding="utf-8",
        )

        entities_path = self.temp_dir / "entities.yaml"
        entities = json.loads(entities_path.read_text(encoding="utf-8"))
        entities["entities"] = [
            {
                "id": "char-linzhou",
                "name": "林舟",
                "type": "character",
                "seed": {"archetype": "夜班调查员"},
                "profile": {"role": "主角", "summary": "长期夜巡、警觉克制的调查者。"},
                "currentState": {"physicalState": "疲惫但稳定"},
            }
        ]
        entities_path.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_illustration_prompt_for_entity(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "prompt",
                    "--root",
                    str(self.temp_dir),
                    "--entity-id",
                    "char-linzhou",
                    "--mode",
                    "text-to-image",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["targetType"], "entity")
        self.assertEqual(payload["mode"], "text-to-image")
        self.assertIn("林舟", payload["promptText"])

    def test_illustration_prompt_for_chapter_image_to_image(self) -> None:
        reference = self.temp_dir / "reference.png"
        reference.write_bytes(b"fake-image")
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "prompt",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--mode",
                    "image-to-image",
                    "--input-image",
                    str(reference),
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["targetType"], "chapter")
        self.assertEqual(payload["mode"], "image-to-image")
        self.assertEqual(len(payload["inputImages"]), 1)

    def test_illustration_config_persists_and_list_reads(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "config",
                    "--root",
                    str(self.temp_dir),
                    "--set-model",
                    "gpt-image-2",
                    "--set-response-model",
                    "gpt-5.5",
                    "--set-size",
                    "1536x1024",
                    "--set-quality",
                    "high",
                    "--set-base-url",
                    "https://example.invalid/v1",
                    "--set-prompt-pack",
                    "light-novel",
                    "--set-scene-template",
                    "scene-standard",
                    "--set-commercial-mode",
                    "commercial",
                ]
            )
        self.assertEqual(exit_code, 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["illustration", "list", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["adapter"]["model"], "gpt-image-2")
        self.assertEqual(payload["adapter"]["responseModel"], "gpt-5.5")
        self.assertEqual(payload["adapter"]["defaultSize"], "1536x1024")
        self.assertEqual(payload["adapter"]["quality"], "high")
        self.assertEqual(payload["adapter"]["baseUrl"], "https://example.invalid/v1")
        self.assertEqual(payload["promptPack"]["name"], "light-novel")
        self.assertEqual(payload["promptSystem"]["commercialMode"], "commercial")
        self.assertEqual(payload["promptSystem"]["defaultTemplateByUseCase"]["chapter-scene"], "scene-standard")
        self.assertEqual(payload["batchSystem"]["defaultDeliveryMode"], "webui-manual")
        self.assertEqual(payload["batchSystem"]["externalAgentSkill"], "story-canvas-imagegen")
        self.assertTrue(payload["availablePromptPacks"])

    def test_illustration_config_updates_batch_system(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "config",
                    "--root",
                    str(self.temp_dir),
                    "--set-batch-delivery-mode",
                    "external-agent",
                    "--set-external-agent-skill",
                    "story-canvas-imagegen-agent",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["batchSystem"]["defaultDeliveryMode"], "external-agent")
        self.assertEqual(payload["batchSystem"]["externalAgentSkill"], "story-canvas-imagegen-agent")

    def test_illustration_generate_dry_run_outputs_provider_request(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "generate",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--mode",
                    "text-to-image",
                    "--template-id",
                    "scene-standard",
                    "--modifier",
                    "style-cinematic",
                    "--extra-prompt",
                    "雨夜港口，强调湿润路面反光和门口对峙。",
                    "--commercial-mode",
                    "commercial",
                    "--dry-run",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["dryRun"])
        self.assertEqual(payload["providerRequest"]["model"], "gpt-image-2")
        self.assertEqual(payload["providerRequest"]["responseModel"], "gpt-5.4")
        self.assertEqual(payload["providerRequest"]["mode"], "text-to-image")
        self.assertEqual(payload["providerRequest"]["baseUrl"], "https://api.openai.com/v1")
        self.assertEqual(payload["providerRequest"]["metadata"]["templateRef"], "scene-standard")
        self.assertEqual(payload["promptSnapshot"]["templateRef"], "scene-standard")
        self.assertEqual(payload["promptSnapshot"]["modifierRefs"], ["style-cinematic"])
        self.assertEqual(payload["policySnapshot"]["commercialMode"], "commercial")
        self.assertIn("雨夜港口", payload["promptSnapshot"]["resolvedPrompt"])

    def test_illustration_generate_dry_run_supports_batch_count(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "generate",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--mode",
                    "text-to-image",
                    "--batch-count",
                    "3",
                    "--dry-run",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["payload"]["batch"]["count"], 3)
        self.assertEqual(payload["providerRequest"]["batch"]["count"], 3)
        self.assertEqual(payload["outputFile"], payload["outputFiles"][0])
        self.assertEqual(len(payload["outputFiles"]), 3)
        self.assertTrue(payload["outputFiles"][1].endswith("_02.png"))
        self.assertTrue(payload["outputFiles"][2].endswith("_03.png"))

    def test_illustration_generate_temp_target_uses_staging_dir(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "generate",
                    "--root",
                    str(self.temp_dir),
                    "--temp-label",
                    "marketing-banner",
                    "--use-case",
                    "promo",
                    "--subject",
                    "港口怪谈宣传横幅，强调冷色雾气与霓虹标题留白。",
                    "--mode",
                    "text-to-image",
                    "--dry-run",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["payload"]["targetType"], "temporary")
        self.assertEqual(payload["payload"]["targetId"], "marketing-banner")
        self.assertIn("tmp", payload["outputFile"])
        self.assertIn("staging", payload["outputFile"])
        self.assertTrue(payload["outputFile"].endswith("marketing-banner_promo.png"))

    def test_illustration_batch_export_writes_manifest_for_webui_manual(self) -> None:
        spec_path = self.temp_dir / "batch-spec.json"
        spec_path.write_text(
            json.dumps(
                {
                    "label": "fog-harbor-batch",
                    "defaults": {
                        "mode": "text-to-image",
                        "templateId": "scene-standard",
                        "commercialMode": "personal",
                    },
                    "jobs": [
                        {
                            "chapterId": "chapter-001",
                            "extraPrompt": "强调仓库门口和被撬开的木箱。",
                        },
                        {
                            "entityId": "char-linzhou",
                            "templateId": "character-standard",
                        },
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "batch-export",
                    "--root",
                    str(self.temp_dir),
                    "--spec",
                    str(spec_path),
                    "--delivery-mode",
                    "webui-manual",
                ]
            )
        payload = json.loads(buffer.getvalue())
        manifest = payload["manifest"]

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["saved"])
        self.assertTrue(Path(payload["manifestPath"]).exists())
        self.assertEqual(manifest["deliveryMode"], "webui-manual")
        self.assertEqual(manifest["summary"]["jobCount"], 2)
        self.assertEqual(len(manifest["jobs"]), 2)
        self.assertEqual(manifest["jobs"][0]["targetRef"]["targetId"], "chapter-001")
        self.assertEqual(manifest["jobs"][1]["targetRef"]["targetId"], "char-linzhou")
        self.assertEqual(manifest["jobs"][0]["delivery"]["mode"], "webui-manual")
        self.assertTrue(manifest["jobs"][0]["outputFiles"][0].endswith(".png"))

    def test_illustration_batch_export_supports_temp_label_jobs(self) -> None:
        spec_path = self.temp_dir / "temp-batch-spec.json"
        spec_path.write_text(
            json.dumps(
                {
                    "label": "promo-assets",
                    "defaults": {
                        "mode": "text-to-image",
                        "useCase": "promo",
                    },
                    "jobs": [
                        {
                            "tempLabel": "home-hero",
                            "subject": "首页横幅，强调冷色雾港、主角剪影和标题留白。",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "batch-export",
                    "--root",
                    str(self.temp_dir),
                    "--spec",
                    str(spec_path),
                ]
            )
        payload = json.loads(buffer.getvalue())
        job = payload["manifest"]["jobs"][0]

        self.assertEqual(exit_code, 0)
        self.assertEqual(job["targetRef"]["type"], "temporary")
        self.assertEqual(job["targetRef"]["targetId"], "home-hero")
        self.assertIn("tmp", job["outputFiles"][0])
        self.assertIn("staging", job["outputFiles"][0])

    def test_illustration_batch_record_imports_generated_outputs(self) -> None:
        spec_path = self.temp_dir / "batch-record-spec.json"
        spec_path.write_text(
            json.dumps(
                {
                    "label": "fog-harbor-import",
                    "defaults": {
                        "mode": "text-to-image",
                    },
                    "jobs": [
                        {
                            "chapterId": "chapter-001",
                            "batchCount": 2,
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        export_buffer = StringIO()
        with redirect_stdout(export_buffer):
            export_exit_code = main(
                [
                    "illustration",
                    "batch-export",
                    "--root",
                    str(self.temp_dir),
                    "--spec",
                    str(spec_path),
                ]
            )
        export_payload = json.loads(export_buffer.getvalue())
        self.assertEqual(export_exit_code, 0)

        manifest = export_payload["manifest"]
        for index, file_path in enumerate(manifest["jobs"][0]["outputFiles"]):
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_bytes(f"img-{index}".encode("utf-8"))

        record_buffer = StringIO()
        with redirect_stdout(record_buffer):
            record_exit_code = main(
                [
                    "illustration",
                    "batch-record",
                    "--root",
                    str(self.temp_dir),
                    "--manifest",
                    export_payload["manifestPath"],
                ]
            )
        record_payload = json.loads(record_buffer.getvalue())

        self.assertEqual(record_exit_code, 0)
        self.assertTrue(record_payload["saved"])
        self.assertEqual(record_payload["importedCount"], 1)
        self.assertEqual(record_payload["illustrations"][0]["batch"]["count"], 2)
        self.assertEqual(record_payload["illustrations"][0]["metadata"]["import"]["importMode"], "webui-manual")

        illustrations_state = json.loads((self.temp_dir / "illustrations.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(illustrations_state["generated"]), 1)
        self.assertEqual(illustrations_state["generated"][0]["metadata"]["assetCount"], 2)

    def test_illustration_prompt_supports_project_custom_pack(self) -> None:
        packs_dir = self.temp_dir / "prompts" / "illustration-packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        custom_pack = {
            "id": "project/custom-noir",
            "version": "1.0",
            "label": "Custom Noir Pack",
            "description": "黑色电影风格的项目自定义模板。",
            "supports": {"modes": ["text-to-image"], "commercial": True},
            "templates": [
                {
                    "id": "scene-standard",
                    "label": "Noir Scene",
                    "useCase": "chapter-scene",
                    "complexity": "standard",
                    "mode": "text-to-image",
                    "promptTemplate": "{subject}\nvisual direction: noir alley, hard shadow\n{styleModifiers}\nuser direction: {userExtraPrompt}\ncommercial direction: {commercialPrompt}",
                    "defaultNegativePolicyRef": "default-safe",
                    "defaultCommercialPolicyRef": "personal-default",
                }
            ],
            "modifierGroups": [
                {
                    "id": "lighting-harsh",
                    "group": "lighting",
                    "label": "硬光",
                    "promptFragment": "hard shadow, sharp rim light",
                    "negativeFragment": "",
                    "commercialTags": [],
                }
            ],
            "policies": {
                "negativePolicies": [
                    {
                        "id": "default-safe",
                        "label": "默认负向",
                        "negativePrompt": "blurry, flat lighting",
                    }
                ],
                "commercialPolicies": [
                    {
                        "id": "personal-default",
                        "label": "个人默认",
                        "mode": "personal",
                        "extraPrompt": "",
                        "restrictions": [],
                    }
                ],
            },
        }
        (packs_dir / "pack-custom-noir.yaml").write_text(
            json.dumps(custom_pack, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "prompt",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--mode",
                    "text-to-image",
                    "--prompt-pack",
                    "custom-noir",
                    "--template-id",
                    "scene-standard",
                    "--modifier",
                    "lighting-harsh",
                    "--extra-prompt",
                    "强调巷口对视和地面积水。",
                ]
            )

        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["promptPackRef"]["packId"], "project/custom-noir")
        self.assertEqual(payload["templateId"], "scene-standard")
        self.assertEqual(payload["modifierRefs"], ["lighting-harsh"])
        self.assertIn("noir alley", payload["promptText"])
        self.assertIn("强调巷口对视", payload["promptSnapshot"]["resolvedPrompt"])

    def test_illustration_generate_image_to_image_real_path_persists_record(self) -> None:
        reference = self.temp_dir / "reference.png"
        mask = self.temp_dir / "mask.png"
        reference.write_bytes(b"fake-reference")
        mask.write_bytes(b"fake-mask")
        captured: dict[str, object] = {}

        def fake_generate_image(self, request):
            captured["request"] = request
            return {
                "provider": "openai-http",
                "artifacts": [
                    {
                        "index": 0,
                        "b64Json": "ZmFrZQ==",
                        "url": "",
                        "revisedPrompt": "",
                        "outputFormat": "png",
                    }
                ],
                "payload": {"data": [{"b64_json": "ZmFrZQ=="}]},
            }

        buffer = StringIO()
        with patch("story_harness_cli.commands.illustration.OpenAIImageHTTPClient.generate_image", new=fake_generate_image):
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "illustration",
                        "generate",
                        "--root",
                        str(self.temp_dir),
                        "--chapter-id",
                        "chapter-001",
                        "--mode",
                        "image-to-image",
                        "--input-image",
                        str(reference),
                        "--mask",
                        str(mask),
                        "--api-key",
                        "test-key",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        request = captured["request"]

        self.assertEqual(exit_code, 0)
        self.assertEqual(request["transport"], "json")
        self.assertTrue(request["stream"])
        self.assertEqual(request["endpoint"], "https://api.openai.com/v1/responses")
        self.assertEqual(request["json"]["model"], "gpt-5.4")
        self.assertEqual(request["json"]["tools"][0]["model"], "gpt-image-2")
        self.assertEqual(request["json"]["tools"][0]["action"], "edit")
        self.assertEqual(payload["illustration"]["mode"], "image-to-image")
        self.assertEqual(len(payload["illustration"]["inputImages"]), 1)
        self.assertTrue(payload["illustration"]["maskPath"].endswith("mask.png"))
        self.assertTrue(payload["illustration"]["filePath"].endswith(".png"))
        self.assertEqual(len(payload["illustration"]["artifacts"]), 1)
        self.assertTrue(payload["illustration"]["artifacts"][0]["isPrimary"])
        self.assertEqual(payload["illustration"]["metadata"]["asset"]["source"], "b64_json")
        self.assertEqual(payload["illustration"]["metadata"]["asset"]["bytes"], 4)
        self.assertEqual(payload["illustration"]["metadata"]["assetCount"], 1)
        self.assertEqual(
            payload["illustration"]["metadata"]["providerRequest"]["mode"],
            "image-to-image",
        )
        output_file = Path(payload["illustration"]["filePath"])
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_bytes(), b"fake")

        illustrations_state = json.loads((self.temp_dir / "illustrations.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(illustrations_state["generated"]), 1)
        self.assertEqual(illustrations_state["generated"][0]["mode"], "image-to-image")
        self.assertEqual(illustrations_state["generated"][0]["metadata"]["asset"]["bytes"], 4)

    def test_illustration_generate_text_to_image_real_path_uses_revised_prompt(self) -> None:
        buffer = StringIO()

        def fake_generate_image(self, request):
            return {
                "provider": "openai-http",
                "artifacts": [
                    {
                        "index": 0,
                        "b64Json": "ZmFrZQ==",
                        "url": "",
                        "revisedPrompt": "revised by provider",
                        "outputFormat": "png",
                    }
                ],
                "payload": {"data": [{"b64_json": "ZmFrZQ==", "revised_prompt": "revised by provider"}]},
            }

        with patch("story_harness_cli.commands.illustration.OpenAIImageHTTPClient.generate_image", new=fake_generate_image):
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "illustration",
                        "generate",
                        "--root",
                        str(self.temp_dir),
                        "--chapter-id",
                        "chapter-001",
                        "--mode",
                        "text-to-image",
                        "--api-key",
                        "test-key",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        output_file = Path(payload["illustration"]["filePath"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["illustration"]["revisedPrompt"], "revised by provider")
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_bytes(), b"fake")

    def test_illustration_export_copies_temp_assets(self) -> None:
        generate_buffer = StringIO()

        def fake_generate_image(self, request):
            return {
                "provider": "openai-http",
                "artifacts": [
                    {
                        "index": 0,
                        "b64Json": "ZmFrZQ==",
                        "url": "",
                        "revisedPrompt": "temp revised",
                        "outputFormat": "png",
                    }
                ],
                "payload": {"data": [{"b64_json": "ZmFrZQ==", "revised_prompt": "temp revised"}]},
            }

        with patch("story_harness_cli.commands.illustration.OpenAIImageHTTPClient.generate_image", new=fake_generate_image):
            with redirect_stdout(generate_buffer):
                generate_exit_code = main(
                    [
                        "illustration",
                        "generate",
                        "--root",
                        str(self.temp_dir),
                        "--temp-label",
                        "poster-kit",
                        "--use-case",
                        "promo",
                        "--subject",
                        "角色海报套图，强调暗蓝色海雾和标题留白。",
                        "--mode",
                        "text-to-image",
                        "--api-key",
                        "test-key",
                    ]
                )
        generate_payload = json.loads(generate_buffer.getvalue())
        illustration_id = generate_payload["illustration"]["id"]
        export_dir = self.temp_dir / "custom-exports"

        export_buffer = StringIO()
        with redirect_stdout(export_buffer):
            export_exit_code = main(
                [
                    "illustration",
                    "export",
                    "--root",
                    str(self.temp_dir),
                    "--illustration-id",
                    illustration_id,
                    "--output-dir",
                    str(export_dir),
                ]
            )
        export_payload = json.loads(export_buffer.getvalue())

        self.assertEqual(generate_exit_code, 0)
        self.assertEqual(export_exit_code, 0)
        self.assertTrue(Path(generate_payload["illustration"]["filePath"]).exists())
        self.assertEqual(generate_payload["illustration"]["metadata"]["storageScope"], "project-temp")
        self.assertEqual(export_payload["illustrationId"], illustration_id)
        self.assertTrue((export_dir / Path(generate_payload["illustration"]["filePath"]).name).exists())

    def test_illustration_generate_dry_run_supports_custom_base_url(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "illustration",
                    "generate",
                    "--root",
                    str(self.temp_dir),
                    "--chapter-id",
                    "chapter-001",
                    "--mode",
                    "text-to-image",
                    "--base-url",
                    "https://api.asxs.top/v1",
                    "--response-model",
                    "gpt-5.5",
                    "--dry-run",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["providerRequest"]["baseUrl"], "https://api.asxs.top/v1")
        self.assertEqual(payload["providerRequest"]["responseModel"], "gpt-5.5")

    def test_illustration_generate_multiple_artifacts_and_list_summary(self) -> None:
        buffer = StringIO()

        def fake_generate_image(self, request):
            return {
                "provider": "openai-http",
                "artifacts": [
                    {
                        "index": 0,
                        "b64Json": "ZmFrZQ==",
                        "url": "",
                        "revisedPrompt": "primary revised",
                        "outputFormat": "png",
                    },
                    {
                        "index": 1,
                        "b64Json": "c2Vjb25k",
                        "url": "",
                        "revisedPrompt": "secondary revised",
                        "outputFormat": "png",
                    },
                ],
                "payload": {
                    "data": [
                        {"b64_json": "ZmFrZQ==", "revised_prompt": "primary revised"},
                        {"b64_json": "c2Vjb25k", "revised_prompt": "secondary revised"},
                    ]
                },
            }

        with patch("story_harness_cli.commands.illustration.OpenAIImageHTTPClient.generate_image", new=fake_generate_image):
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "illustration",
                        "generate",
                        "--root",
                        str(self.temp_dir),
                        "--chapter-id",
                        "chapter-001",
                        "--mode",
                        "text-to-image",
                        "--output-name",
                        "chapter-001-scene.png",
                        "--api-key",
                        "test-key",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        artifacts = payload["illustration"]["artifacts"]
        first_output = Path(artifacts[0]["filePath"])
        second_output = Path(artifacts[1]["filePath"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(artifacts), 2)
        self.assertTrue(artifacts[0]["isPrimary"])
        self.assertFalse(artifacts[1]["isPrimary"])
        self.assertTrue(first_output.exists())
        self.assertTrue(second_output.exists())
        self.assertEqual(first_output.read_bytes(), b"fake")
        self.assertEqual(second_output.read_bytes(), b"second")
        self.assertTrue(second_output.name.endswith("_02.png"))
        self.assertEqual(payload["illustration"]["metadata"]["assetCount"], 2)

        list_buffer = StringIO()
        with redirect_stdout(list_buffer):
            list_exit_code = main(["illustration", "list", "--root", str(self.temp_dir)])
        list_payload = json.loads(list_buffer.getvalue())
        generated_entry = list_payload["generated"][0]

        self.assertEqual(list_exit_code, 0)
        self.assertEqual(generated_entry["assetCount"], 2)
        self.assertEqual(generated_entry["existingAssetCount"], 2)
        self.assertTrue(generated_entry["allAssetsPresent"])
        self.assertEqual(generated_entry["targetRef"]["type"], "chapter")
        self.assertEqual(generated_entry["targetRef"]["targetId"], "chapter-001")
        self.assertTrue(generated_entry["targetRef"]["declaredInState"])
        self.assertTrue(generated_entry["targetRef"]["contentFileExists"])
        self.assertTrue(generated_entry["allInputsPresent"])
        self.assertTrue(generated_entry["maskPresent"])
        self.assertEqual(len(generated_entry["artifacts"]), 2)
        self.assertTrue(all(item["exists"] for item in generated_entry["artifacts"]))

    def test_illustration_generate_batch_count_repeats_generation_and_persists_snapshot(self) -> None:
        buffer = StringIO()
        encoded_payloads = ["ZmFrZQ==", "c2Vjb25k", "dGhpcmQ="]
        revised_prompts = ["batch one", "batch two", "batch three"]
        call_count = {"value": 0}

        def fake_generate_image(self, request):
            index = call_count["value"]
            call_count["value"] += 1
            return {
                "provider": "openai-http",
                "artifacts": [
                    {
                        "index": 0,
                        "b64Json": encoded_payloads[index],
                        "url": "",
                        "revisedPrompt": revised_prompts[index],
                        "outputFormat": "png",
                    }
                ],
                "payload": {
                    "data": [
                        {
                            "b64_json": encoded_payloads[index],
                            "revised_prompt": revised_prompts[index],
                        }
                    ]
                },
            }

        with patch("story_harness_cli.commands.illustration.OpenAIImageHTTPClient.generate_image", new=fake_generate_image):
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "illustration",
                        "generate",
                        "--root",
                        str(self.temp_dir),
                        "--chapter-id",
                        "chapter-001",
                        "--mode",
                        "text-to-image",
                        "--batch-count",
                        "3",
                        "--output-name",
                        "chapter-001-batch.png",
                        "--api-key",
                        "test-key",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        artifacts = payload["illustration"]["artifacts"]

        self.assertEqual(exit_code, 0)
        self.assertEqual(call_count["value"], 3)
        self.assertEqual(payload["illustration"]["batch"]["count"], 3)
        self.assertEqual(payload["illustration"]["batch"]["variantStrategy"], "same-template")
        self.assertEqual(len(artifacts), 3)
        self.assertTrue(Path(artifacts[0]["filePath"]).exists())
        self.assertTrue(Path(artifacts[1]["filePath"]).name.endswith("_02.png"))
        self.assertTrue(Path(artifacts[2]["filePath"]).name.endswith("_03.png"))
        self.assertEqual(payload["illustration"]["metadata"]["assetCount"], 3)
        self.assertEqual(len(payload["illustration"]["metadata"]["providerResults"]), 3)

        illustrations_state = json.loads((self.temp_dir / "illustrations.yaml").read_text(encoding="utf-8"))
        self.assertEqual(illustrations_state["generated"][0]["batch"]["count"], 3)
        self.assertEqual(len(illustrations_state["generated"][0]["artifacts"]), 3)

    def test_story_canvas_ui_api_generate_returns_saved_illustration_and_summary(self) -> None:
        api_module = _load_story_canvas_ui_api_module()

        encoded_payloads = ["ZmFrZQ==", "c2Vjb25k"]
        revised_prompts = ["ui api revised 1", "ui api revised 2"]
        call_count = {"value": 0}

        def fake_generate_image(self, request):
            index = call_count["value"]
            call_count["value"] += 1
            return {
                "provider": "openai-http",
                "artifacts": [
                    {
                        "index": 0,
                        "b64Json": encoded_payloads[index],
                        "url": "",
                        "revisedPrompt": revised_prompts[index],
                        "outputFormat": "png",
                    }
                ],
                "payload": {
                    "data": [
                        {
                            "b64_json": encoded_payloads[index],
                            "revised_prompt": revised_prompts[index],
                        }
                    ]
                },
            }

        with patch("story_harness_cli.commands.illustration.OpenAIImageHTTPClient.generate_image", new=fake_generate_image):
            payload = api_module._build_illustration_generate(
                {
                    "root": str(self.temp_dir),
                    "chapterId": "chapter-001",
                    "mode": "text-to-image",
                    "templateId": "scene-standard",
                    "extraPrompt": "雨夜码头，门缝里透出冷白色灯。",
                    "batchCount": 2,
                    "apiKey": "test-key",
                }
            )

        self.assertTrue(payload["saved"])
        self.assertEqual(call_count["value"], 2)
        self.assertEqual(payload["illustration"]["mode"], "text-to-image")
        self.assertEqual(payload["illustration"]["revisedPrompt"], "ui api revised 1")
        self.assertEqual(payload["illustration"]["batch"]["count"], 2)
        self.assertEqual(len(payload["illustration"]["artifacts"]), 2)
        self.assertTrue(payload["illustration"]["artifacts"][0]["exists"])
        self.assertTrue(Path(payload["illustration"]["filePath"]).exists())
        self.assertEqual(payload["summary"]["stats"]["illustrationCount"], 1)
        self.assertEqual(payload["summary"]["illustrations"][0]["templateId"], "scene-standard")
        self.assertEqual(payload["summary"]["illustrations"][0]["batch"]["count"], 2)
        self.assertEqual(
            payload["summary"]["illustrations"][0]["promptSnapshot"]["userExtraPrompt"],
            "雨夜码头，门缝里透出冷白色灯。",
        )

    def test_story_canvas_ui_api_prompt_pack_endpoint_saves_user_pack(self) -> None:
        api_module = _load_story_canvas_ui_api_module()

        payload = api_module._save_prompt_pack_request(
            {
                "root": str(self.temp_dir),
                "fileName": "ui-custom-pack",
                "setAsDefault": True,
                "pack": {
                    "label": "UI Custom Pack",
                    "description": "给前端编辑器保存的自定义模板。",
                    "templates": [
                        {
                            "id": "scene-standard",
                            "label": "UI Scene",
                            "useCase": "chapter-scene",
                            "mode": "text-to-image",
                            "promptTemplate": "{subject}\nui scene\n{userExtraPrompt}",
                        }
                    ],
                    "modifierGroups": [
                        {
                            "id": "tone-cold",
                            "label": "冷调",
                            "promptFragment": "cold palette, restrained contrast",
                        }
                    ],
                },
            }
        )

        self.assertTrue(payload["saved"])
        self.assertEqual(payload["scope"], "project")
        self.assertEqual(payload["savedPack"]["id"], "project/ui-custom-pack")
        self.assertEqual(payload["savedPack"]["source"], "project")
        self.assertTrue(payload["savedPack"]["sourceFile"].endswith("ui-custom-pack.yaml"))
        self.assertTrue(any(item["id"] == "project/ui-custom-pack" for item in payload["userPacks"]))

        config = json.loads((self.temp_dir / "illustrations.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["promptPack"]["name"], "ui-custom-pack")
        self.assertEqual(config["promptSystem"]["defaultPack"]["packId"], "project/ui-custom-pack")

        library = api_module._build_prompt_pack_library_response(self.temp_dir)
        saved_pack = next(item for item in library["userPacks"] if item["id"] == "project/ui-custom-pack")
        self.assertEqual(saved_pack["templates"][0]["promptTemplate"], "{subject}\nui scene\n{userExtraPrompt}")
        self.assertEqual(saved_pack["modifierGroups"][0]["promptFragment"], "cold palette, restrained contrast")


if __name__ == "__main__":
    unittest.main()
