from __future__ import annotations

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
                    "--set-size",
                    "1536x1024",
                    "--set-quality",
                    "high",
                ]
            )
        self.assertEqual(exit_code, 0)

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["illustration", "list", "--root", str(self.temp_dir)])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["adapter"]["model"], "gpt-image-2")
        self.assertEqual(payload["adapter"]["defaultSize"], "1536x1024")
        self.assertEqual(payload["adapter"]["quality"], "high")

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
                    "--dry-run",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["dryRun"])
        self.assertEqual(payload["providerRequest"]["model"], "gpt-image-2")
        self.assertEqual(payload["providerRequest"]["mode"], "text-to-image")

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
        self.assertEqual(request["transport"], "multipart")
        self.assertEqual(request["endpoint"], "https://api.openai.com/v1/images/edits")
        self.assertEqual(request["files"][0]["field"], "image[]")
        self.assertEqual(request["files"][1]["field"], "mask")
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
        self.assertEqual(len(generated_entry["artifacts"]), 2)
        self.assertTrue(all(item["exists"] for item in generated_entry["artifacts"]))


if __name__ == "__main__":
    unittest.main()
