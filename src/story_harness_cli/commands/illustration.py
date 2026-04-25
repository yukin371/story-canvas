from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_harness_cli.protocol import (
    chapter_path,
    ensure_project_root,
    load_project_state,
    resolve_state_path,
    save_state,
)
from story_harness_cli.providers.image import OpenAIImageHTTPClient
from story_harness_cli.commands.illustration_support import (
    decorate_generated_entry,
    resolve_output_path_for_index,
)
from story_harness_cli.services import (
    build_chapter_illustration_payload,
    build_entity_illustration_payload,
)
from story_harness_cli.utils import now_iso, stable_hash


def _illustrations_path(root: Path) -> Path:
    return resolve_state_path(root, "illustrations")


def _normalize_mode(mode: str) -> str:
    if mode not in {"text-to-image", "image-to-image"}:
        raise SystemExit(f"未知 illustration mode: {mode}")
    return mode


def _resolve_entity(state: dict[str, Any], entity_id_or_name: str) -> dict[str, Any]:
    for entity in state.get("entities", {}).get("entities", []):
        if entity.get("id") == entity_id_or_name or entity.get("name") == entity_id_or_name:
            return entity
    raise SystemExit(f"Entity 不存在: {entity_id_or_name}")


def _resolve_chapter_title(state: dict[str, Any], chapter_id: str) -> str:
    for chapter in state.get("outline", {}).get("chapters", []):
        if chapter.get("id") == chapter_id:
            return chapter.get("title", chapter_id)
    return chapter_id


def _build_payload(root: Path, state: dict[str, Any], args) -> dict[str, Any]:
    mode = _normalize_mode(args.mode)
    input_images = [str(Path(item).resolve()) for item in (args.input_image or [])]
    mask_path = str(Path(args.mask).resolve()) if args.mask else ""
    prompt_pack_name = args.prompt_pack or state.get("illustrations", {}).get("promptPack", {}).get("name", "default")

    if args.entity_id:
        entity = _resolve_entity(state, args.entity_id)
        return build_entity_illustration_payload(
            state,
            entity=entity,
            mode=mode,
            input_images=input_images,
            mask_path=mask_path,
            prompt_pack_name=prompt_pack_name,
        )

    chapter_id = args.chapter_id or state.get("project", {}).get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")
    return build_chapter_illustration_payload(
        state,
        chapter_id=chapter_id,
        chapter_title=_resolve_chapter_title(state, chapter_id),
        chapter_text=chapter_file.read_text(encoding="utf-8"),
        mode=mode,
        input_images=input_images,
        mask_path=mask_path,
        prompt_pack_name=prompt_pack_name,
    )

def command_illustration_prompt(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = _build_payload(root, state, args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_generate(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = _build_payload(root, state, args)
    illustrations_state = state.setdefault("illustrations", {})
    adapter_config = illustrations_state.get("adapter", {})
    if payload["mode"] == "image-to-image" and not payload["inputImages"]:
        raise SystemExit("图生图至少需要一张 --input-image")

    provider_request = {
        "model": adapter_config.get("model", "gpt-image-2"),
        "prompt": payload["promptText"],
        "size": args.size or adapter_config.get("defaultSize", "1024x1024"),
        "quality": args.quality or adapter_config.get("quality", "standard"),
        "mode": payload["mode"],
        "inputImages": payload["inputImages"],
        "maskPath": payload["maskPath"],
        "metadata": payload["providerRequest"]["metadata"],
    }
    output_name = args.output_name or _default_output_name(payload)
    output_path = root / "assets" / "illustrations" / output_name

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dryRun": True,
                    "adapter": adapter_config,
                    "outputFile": str(output_path),
                    "providerRequest": provider_request,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if adapter_config.get("name") != "openai":
        raise SystemExit(f"暂不支持的 adapter: {adapter_config.get('name')}")

    api_key = args.api_key or ""
    if not api_key:
        raise SystemExit("缺少 API key；请通过 --api-key 传入")

    client = OpenAIImageHTTPClient(api_key=api_key)
    if payload["mode"] == "image-to-image":
        request = client.build_edit_request(
            provider_request["prompt"],
            model=provider_request["model"],
            size=provider_request["size"],
            quality=provider_request["quality"],
            input_images=provider_request["inputImages"],
            mask_path=provider_request["maskPath"],
        )
    else:
        request = client.build_generation_request(
            provider_request["prompt"],
            model=provider_request["model"],
            size=provider_request["size"],
            quality=provider_request["quality"],
        )
    result = client.generate_image(request)
    assets = client.materialize_artifacts(result)
    artifact_records = []
    for asset in assets:
        resolved_output_path = resolve_output_path_for_index(output_path, asset["index"], asset["extension"])
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_output_path.write_bytes(asset["content"])
        artifact_records.append(
            {
                "index": asset["index"],
                "filePath": str(resolved_output_path),
                "bytes": len(asset["content"]),
                "source": asset["source"],
                "extension": asset["extension"],
                "revisedPrompt": asset["revisedPrompt"],
                "isPrimary": asset["index"] == 0,
            }
        )
    primary_asset = artifact_records[0]

    generated = illustrations_state.setdefault("generated", [])
    entry = {
        "id": f"ill-{stable_hash(payload['targetType'] + payload['targetId'] + now_iso())}",
        "type": payload["targetType"],
        "mode": payload["mode"],
        "chapterId": payload["targetId"] if payload["targetType"] == "chapter" else None,
        "entityId": payload["targetId"] if payload["targetType"] == "entity" else None,
        "promptText": payload["promptText"],
        "revisedPrompt": primary_asset["revisedPrompt"] or payload["promptText"],
        "inputImages": payload["inputImages"],
        "maskPath": payload["maskPath"],
        "filePath": primary_asset["filePath"],
        "artifacts": artifact_records,
        "metadata": {
            "asset": {
                "source": primary_asset["source"],
                "extension": primary_asset["extension"],
                "bytes": primary_asset["bytes"],
            },
            "assetCount": len(artifact_records),
            "providerResult": result,
            "providerRequest": provider_request,
        },
        "generatedAt": now_iso(),
    }
    generated.append(entry)
    save_state(root, state)
    print(json.dumps({"saved": True, "illustration": entry}, ensure_ascii=False, indent=2))
    return 0


def command_illustration_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = {
        "illustrationsFile": str(_illustrations_path(root)),
        "adapter": state.get("illustrations", {}).get("adapter", {}),
        "promptPack": state.get("illustrations", {}).get("promptPack", {}),
        "generated": [
            decorate_generated_entry(root, entry)
            for entry in state.get("illustrations", {}).get("generated", [])
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_config(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    illustrations_state = state.setdefault("illustrations", {})
    adapter = illustrations_state.setdefault("adapter", {})
    if args.set_adapter:
        adapter["name"] = args.set_adapter
    if args.set_model:
        adapter["model"] = args.set_model
    if args.set_size:
        adapter["defaultSize"] = args.set_size
    if args.set_quality:
        adapter["quality"] = args.set_quality
    if args.set_prompt_pack:
        illustrations_state.setdefault("promptPack", {})["name"] = args.set_prompt_pack
    save_state(root, state)
    payload = {
        "illustrationsFile": str(_illustrations_path(root)),
        "adapter": illustrations_state.get("adapter", {}),
        "promptPack": illustrations_state.get("promptPack", {}),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _default_output_name(payload: dict[str, Any]) -> str:
    target_id = payload["targetId"] or payload["targetType"]
    suffix = "reference" if payload["targetType"] == "entity" else "scene"
    extension = "png"
    return f"{target_id}_{suffix}.{extension}"


def register_illustration_commands(subparsers) -> None:
    illustration_parser = subparsers.add_parser("illustration", help="Build and manage illustration requests")
    illustration_subparsers = illustration_parser.add_subparsers(dest="illustration_command", required=True)

    prompt_parser = illustration_subparsers.add_parser("prompt", help="Build an illustration prompt payload")
    prompt_parser.add_argument("--root", required=True)
    prompt_target = prompt_parser.add_mutually_exclusive_group(required=True)
    prompt_target.add_argument("--chapter-id")
    prompt_target.add_argument("--entity-id")
    prompt_parser.add_argument("--mode", required=True, choices=["text-to-image", "image-to-image"])
    prompt_parser.add_argument("--input-image", action="append")
    prompt_parser.add_argument("--mask")
    prompt_parser.add_argument("--prompt-pack")
    prompt_parser.set_defaults(func=command_illustration_prompt)

    generate_parser = illustration_subparsers.add_parser("generate", help="Generate an illustration or emit a dry-run request")
    generate_parser.add_argument("--root", required=True)
    generate_target = generate_parser.add_mutually_exclusive_group(required=True)
    generate_target.add_argument("--chapter-id")
    generate_target.add_argument("--entity-id")
    generate_parser.add_argument("--mode", required=True, choices=["text-to-image", "image-to-image"])
    generate_parser.add_argument("--input-image", action="append")
    generate_parser.add_argument("--mask")
    generate_parser.add_argument("--prompt-pack")
    generate_parser.add_argument("--size")
    generate_parser.add_argument("--quality")
    generate_parser.add_argument("--output-name")
    generate_parser.add_argument("--api-key")
    generate_parser.add_argument("--dry-run", action="store_true")
    generate_parser.set_defaults(func=command_illustration_generate)

    list_parser = illustration_subparsers.add_parser("list", help="List illustration config and generated records")
    list_parser.add_argument("--root", required=True)
    list_parser.set_defaults(func=command_illustration_list)

    config_parser = illustration_subparsers.add_parser("config", help="Show or update illustration config")
    config_parser.add_argument("--root", required=True)
    config_parser.add_argument("--set-adapter")
    config_parser.add_argument("--set-model")
    config_parser.add_argument("--set-size")
    config_parser.add_argument("--set-quality")
    config_parser.add_argument("--set-prompt-pack")
    config_parser.set_defaults(func=command_illustration_config)
