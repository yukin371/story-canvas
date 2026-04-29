from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from story_harness_cli.commands.illustration_support import (
    asset_records_from_entry,
    decorate_generated_entry,
    resolve_output_path_for_index,
)
from story_harness_cli.protocol import (
    chapter_path,
    default_illustration_batch_manifest_path,
    ensure_project_root,
    export_prompt_pack_document,
    load_available_prompt_packs,
    migrate_project_prompt_pack_documents,
    load_project_state,
    resolve_prompt_pack,
    resolve_state_path,
    save_state,
    summarize_prompt_pack,
)
from story_harness_cli.providers.image import OpenAIImageHTTPClient
from story_harness_cli.providers.image.openai_http import resolve_api_key, resolve_base_url
from story_harness_cli.services import (
    build_batch_delivery_payload,
    build_batch_manifest_summary,
    build_chapter_illustration_payload,
    build_entity_illustration_payload,
    build_freeform_illustration_payload,
    normalize_batch_delivery_mode,
    normalize_illustration_batch_spec,
)
from story_harness_cli.utils import now_iso, stable_hash

ILLUSTRATION_USE_CASE_CHOICES = [
    "character",
    "character-sheet",
    "chapter-scene",
    "cover-concept",
    "cover-poster",
    "ensemble-key-visual",
    "duel-scene",
    "chase-escape",
    "comic-relief",
    "promo",
    "product",
    "prop-relic",
    "creature-sheet",
    "manga-panel",
    "manga-page",
]


def _illustrations_path(root: Path) -> Path:
    return resolve_state_path(root, "illustrations")


def _normalize_mode(mode: str) -> str:
    if mode not in {"text-to-image", "image-to-image", "inpaint"}:
        raise SystemExit(f"未知 illustration mode: {mode}")
    return mode


def _normalize_batch_count(value: Any) -> int:
    raw_value = 1 if value in (None, "") else value
    try:
        count = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise SystemExit("batch count 必须是大于等于 1 的整数") from exc
    if count < 1:
        raise SystemExit("batch count 必须是大于等于 1 的整数")
    return count


def _normalize_delivery_mode(value: str) -> str:
    try:
        return normalize_batch_delivery_mode(value)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def _normalize_output_group(value: str, fallback: str) -> str:
    normalized = []
    for char in str(value or "").strip().lower():
        if char.isalnum() or char in {"-", "_"}:
            normalized.append(char)
        else:
            normalized.append("-")
    result = "".join(normalized).strip("-_")
    return result or fallback


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
    illustrations_state = state.get("illustrations", {})
    prompt_resolution = resolve_prompt_pack(root, illustrations_state, args.prompt_pack or "")
    prompt_system = illustrations_state.get("promptSystem", {})
    default_templates = prompt_system.get("defaultTemplateByUseCase", {}) if isinstance(prompt_system, dict) else {}
    default_modifier_refs = prompt_system.get("defaultModifierRefs", []) if isinstance(prompt_system, dict) else []
    commercial_mode = str(args.commercial_mode or prompt_system.get("commercialMode", "personal")).strip() or "personal"
    user_extra_prompt = str(args.extra_prompt or "").strip()
    modifier_refs = list(args.modifier or [])
    batch_count = _normalize_batch_count(getattr(args, "batch_count", 1))
    batch_payload = {
        "count": batch_count,
        "variantStrategy": "same-template",
    }

    if args.entity_id:
        entity = _resolve_entity(state, args.entity_id)
        payload = build_entity_illustration_payload(
            state,
            entity=entity,
            use_case=str(getattr(args, "use_case", "") or "character").strip() or "character",
            mode=mode,
            prompt_pack=prompt_resolution["pack"],
            pack_ref=prompt_resolution["packRef"],
            template_id=str(args.template_id or ""),
            modifier_refs=modifier_refs,
            user_extra_prompt=user_extra_prompt,
            commercial_mode=commercial_mode,
            default_template_by_use_case=default_templates,
            default_modifier_refs=default_modifier_refs,
            input_images=input_images,
            mask_path=mask_path,
            text_design_mode=str(getattr(args, "text_design_mode", "") or ""),
            title_text=str(getattr(args, "title_text", "") or ""),
            subtitle_text=str(getattr(args, "subtitle_text", "") or ""),
            body_text=str(getattr(args, "body_text", "") or ""),
            font_style_hint=str(getattr(args, "font_style_hint", "") or ""),
        )
        payload["batch"] = batch_payload
        return _apply_negative_prompt_override(payload, str(getattr(args, "negative_prompt", "") or ""))

    if getattr(args, "temp_label", ""):
        payload = build_freeform_illustration_payload(
            state,
            target_label=str(args.temp_label).strip(),
            use_case=str(getattr(args, "use_case", "") or "promo").strip() or "promo",
            subject=str(getattr(args, "subject", "") or "").strip(),
            mode=mode,
            prompt_pack=prompt_resolution["pack"],
            pack_ref=prompt_resolution["packRef"],
            template_id=str(args.template_id or ""),
            modifier_refs=modifier_refs,
            user_extra_prompt=user_extra_prompt,
            commercial_mode=commercial_mode,
            default_template_by_use_case=default_templates,
            default_modifier_refs=default_modifier_refs,
            input_images=input_images,
            mask_path=mask_path,
            text_design_mode=str(getattr(args, "text_design_mode", "") or ""),
            title_text=str(getattr(args, "title_text", "") or ""),
            subtitle_text=str(getattr(args, "subtitle_text", "") or ""),
            body_text=str(getattr(args, "body_text", "") or ""),
            font_style_hint=str(getattr(args, "font_style_hint", "") or ""),
        )
        payload["batch"] = batch_payload
        return _apply_negative_prompt_override(payload, str(getattr(args, "negative_prompt", "") or ""))

    chapter_id = args.chapter_id or state.get("project", {}).get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")
    payload = build_chapter_illustration_payload(
        state,
        chapter_id=chapter_id,
        chapter_title=_resolve_chapter_title(state, chapter_id),
        chapter_text=chapter_file.read_text(encoding="utf-8"),
        use_case=str(getattr(args, "use_case", "") or "chapter-scene").strip() or "chapter-scene",
        mode=mode,
        prompt_pack=prompt_resolution["pack"],
        pack_ref=prompt_resolution["packRef"],
        template_id=str(args.template_id or ""),
        modifier_refs=modifier_refs,
        user_extra_prompt=user_extra_prompt,
        commercial_mode=commercial_mode,
        default_template_by_use_case=default_templates,
        default_modifier_refs=default_modifier_refs,
        input_images=input_images,
        mask_path=mask_path,
        text_design_mode=str(getattr(args, "text_design_mode", "") or ""),
        title_text=str(getattr(args, "title_text", "") or ""),
        subtitle_text=str(getattr(args, "subtitle_text", "") or ""),
        body_text=str(getattr(args, "body_text", "") or ""),
        font_style_hint=str(getattr(args, "font_style_hint", "") or ""),
    )
    payload["batch"] = batch_payload
    return _apply_negative_prompt_override(payload, str(getattr(args, "negative_prompt", "") or ""))


def _validate_generation_payload(payload: dict[str, Any]) -> None:
    if payload["mode"] in {"image-to-image", "inpaint"} and not payload["inputImages"]:
        raise SystemExit("图生图 / 重绘至少需要一张 --input-image")
    if payload["mode"] == "inpaint" and not payload["maskPath"]:
        raise SystemExit("inpaint 模式需要提供 --mask")


def _build_provider_request(payload: dict[str, Any], args, adapter_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "responseModel": args.response_model or adapter_config.get("responseModel", "gpt-5.4"),
        "model": adapter_config.get("model", "gpt-image-2"),
        "prompt": payload["promptText"],
        "size": args.size or adapter_config.get("defaultSize", "1024x1024"),
        "quality": args.quality or adapter_config.get("quality", "auto"),
        "mode": payload["mode"],
        "inputImages": payload["inputImages"],
        "maskPath": payload["maskPath"],
        "batch": payload.get("batch", {"count": 1, "variantStrategy": "same-template"}),
        "metadata": payload["providerRequest"]["metadata"],
        "baseUrl": resolve_base_url(args.base_url or "", adapter_config.get("baseUrl", "")),
    }


def _apply_negative_prompt_override(payload: dict[str, Any], raw_negative_prompt: str) -> dict[str, Any]:
    override = raw_negative_prompt.strip()
    if not override:
        return payload

    policy_snapshot = payload.setdefault("policySnapshot", {})
    existing_negative = str(policy_snapshot.get("negativePrompt", "") or "").strip()
    merged_negative = ", ".join(part for part in (existing_negative, override) if part)
    policy_snapshot["negativePrompt"] = merged_negative

    prompt_snapshot = payload.setdefault("promptSnapshot", {})
    resolved_prompt = str(prompt_snapshot.get("resolvedPrompt", "") or "").strip()
    negative_clause = f"avoid: {merged_negative}"
    merged_prompt = "\n".join(part for part in (resolved_prompt, negative_clause) if part)
    prompt_snapshot["resolvedPrompt"] = merged_prompt
    prompt_snapshot["userNegativePrompt"] = override
    payload["promptText"] = merged_prompt

    provider_request = payload.setdefault("providerRequest", {})
    provider_request["prompt"] = merged_prompt
    provider_request["negativePrompt"] = merged_negative
    return payload


def _prepare_generation_request(args) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = _build_payload(root, state, args)
    _validate_generation_payload(payload)
    illustrations_state = state.get("illustrations", {})
    adapter_config = illustrations_state.get("adapter", {})
    provider_request = _build_provider_request(payload, args, adapter_config)
    output_name = args.output_name or _default_output_name(payload)
    output_path = _resolve_output_path(root, payload, output_name)
    return root, state, payload, provider_request, output_path


def _resolve_output_path(root: Path, payload: dict[str, Any], output_name: str) -> Path:
    target_type = str(payload.get("targetType") or "").strip()
    target_id = str(payload.get("targetId") or "").strip()
    use_case = _normalize_output_group(str(payload.get("useCase") or ""), "general")
    if target_type == "chapter":
        return root / "assets" / "illustrations" / "chapters" / target_id / use_case / output_name
    if target_type == "entity":
        return root / "assets" / "illustrations" / "entities" / target_id / use_case / output_name
    return root / "tmp" / "illustrations" / "staging" / (target_id or "temporary") / use_case / output_name


def build_illustration_dry_run_response(args) -> dict[str, Any]:
    root, _, payload, provider_request, output_path = _prepare_generation_request(args)
    batch_count = _normalize_batch_count((payload.get("batch") or {}).get("count", 1))
    output_files = [
        str(resolve_output_path_for_index(output_path, index, output_path.suffix.lstrip(".") or "png"))
        for index in range(batch_count)
    ]
    return {
        "dryRun": True,
        "projectRoot": str(root),
        "payload": payload,
        "promptSnapshot": payload.get("promptSnapshot", {}),
        "policySnapshot": payload.get("policySnapshot", {}),
        "providerRequest": provider_request,
        "outputFile": output_files[0],
        "outputFiles": output_files,
    }


def run_illustration_generation(args) -> dict[str, Any]:
    root, state, payload, provider_request, output_path = _prepare_generation_request(args)
    illustrations_state = state.setdefault("illustrations", {})
    adapter_config = illustrations_state.get("adapter", {})
    if adapter_config.get("name") != "openai":
        raise SystemExit(f"暂不支持的 adapter: {adapter_config.get('name')}")

    api_key = resolve_api_key(args.api_key or "")
    if not api_key:
        raise SystemExit("缺少 API key；请通过 --api-key 传入，或设置 OPENAI_API_KEY / IMAGEGEN_API_KEY")

    client = OpenAIImageHTTPClient(api_key=api_key, base_url=provider_request["baseUrl"])
    if payload["mode"] in {"image-to-image", "inpaint"}:
        request = client.build_edit_request(
            provider_request["prompt"],
            model=provider_request["model"],
            size=provider_request["size"],
            quality=provider_request["quality"],
            input_images=provider_request["inputImages"],
            mask_path=provider_request["maskPath"],
            response_model=provider_request["responseModel"],
        )
    else:
        request = client.build_generation_request(
            provider_request["prompt"],
            model=provider_request["model"],
            size=provider_request["size"],
            quality=provider_request["quality"],
            response_model=provider_request["responseModel"],
        )
    batch = payload.get("batch", {}) if isinstance(payload.get("batch"), dict) else {}
    batch_count = _normalize_batch_count(batch.get("count", 1))
    provider_results: list[dict[str, Any]] = []
    artifact_records = []
    next_artifact_index = 0
    for batch_index in range(batch_count):
        result = client.generate_image(request)
        provider_results.append(result)
        assets = client.materialize_artifacts(result)
        for asset in assets:
            artifact_index = next_artifact_index
            next_artifact_index += 1
            resolved_output_path = resolve_output_path_for_index(output_path, artifact_index, asset["extension"])
            resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_output_path.write_bytes(asset["content"])
            artifact_records.append(
                {
                    "index": artifact_index,
                    "filePath": str(resolved_output_path),
                    "bytes": len(asset["content"]),
                    "source": asset["source"],
                    "extension": asset["extension"],
                    "revisedPrompt": asset["revisedPrompt"],
                    "isPrimary": artifact_index == 0,
                    "batchIndex": batch_index,
                }
            )
    entry = _build_generated_entry(
        payload=payload,
        provider_request=provider_request,
        artifact_records=artifact_records,
        provider_results=provider_results,
        import_metadata={},
    )
    illustrations_state.setdefault("generated", []).append(entry)
    save_state(root, state)
    return {"saved": True, "projectRoot": str(root), "illustration": entry}


def command_illustration_prompt(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = _build_payload(root, state, args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_generate(args) -> int:
    if args.dry_run:
        print(json.dumps(build_illustration_dry_run_response(args), ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(run_illustration_generation(args), ensure_ascii=False, indent=2))
    return 0


def command_illustration_batch_export(args) -> int:
    payload = export_illustration_batch_manifest(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_batch_record(args) -> int:
    payload = record_illustration_batch_manifest(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_export(args) -> int:
    payload = export_illustration_assets(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_list(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    payload = build_illustration_config_payload(root, state)
    payload["generated"] = [
        decorate_generated_entry(root, state, entry)
        for entry in state.get("illustrations", {}).get("generated", [])
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_illustration_config_payload(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    illustrations_state = state.get("illustrations", {})
    return {
        "illustrationsFile": str(_illustrations_path(root)),
        "adapter": illustrations_state.get("adapter", {}),
        "promptPack": illustrations_state.get("promptPack", {}),
        "promptSystem": illustrations_state.get("promptSystem", {}),
        "batchSystem": illustrations_state.get("batchSystem", {}),
        "availablePromptPacks": [
            summarize_prompt_pack(pack)
            for pack in load_available_prompt_packs(root)
        ],
    }


def update_illustration_config(
    root: Path,
    *,
    set_adapter: str | None = None,
    set_model: str | None = None,
    set_response_model: str | None = None,
    set_size: str | None = None,
    set_quality: str | None = None,
    set_base_url: str | None = None,
    set_prompt_pack: str | None = None,
    set_character_template: str | None = None,
    set_scene_template: str | None = None,
    set_promo_template: str | None = None,
    set_commercial_mode: str | None = None,
    set_batch_delivery_mode: str | None = None,
    set_external_agent_skill: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    illustrations_state = state.setdefault("illustrations", {})
    adapter = illustrations_state.setdefault("adapter", {})
    if set_adapter:
        adapter["name"] = set_adapter
    if set_model:
        adapter["model"] = set_model
    if set_response_model:
        adapter["responseModel"] = set_response_model
    if set_size:
        adapter["defaultSize"] = set_size
    if set_quality:
        adapter["quality"] = set_quality
    if set_base_url is not None:
        adapter["baseUrl"] = set_base_url.strip()
    prompt_system = illustrations_state.setdefault("promptSystem", {})
    if set_prompt_pack:
        illustrations_state.setdefault("promptPack", {})["name"] = set_prompt_pack
        prompt_resolution = resolve_prompt_pack(root, illustrations_state, set_prompt_pack)
        prompt_system["defaultPack"] = prompt_resolution["packRef"]
        illustrations_state.setdefault("promptPack", {})["version"] = str(prompt_resolution["packRef"].get("version") or "builtin")
    default_templates = prompt_system.setdefault("defaultTemplateByUseCase", {})
    if set_character_template:
        default_templates["character"] = set_character_template
    if set_scene_template:
        default_templates["chapter-scene"] = set_scene_template
    if set_promo_template:
        default_templates["promo"] = set_promo_template
    if set_commercial_mode:
        prompt_system["commercialMode"] = set_commercial_mode
    batch_system = illustrations_state.setdefault("batchSystem", {})
    if set_batch_delivery_mode:
        batch_system["defaultDeliveryMode"] = _normalize_delivery_mode(set_batch_delivery_mode)
    if set_external_agent_skill is not None:
        batch_system["externalAgentSkill"] = set_external_agent_skill.strip()
    save_state(root, state)
    payload = build_illustration_config_payload(root, state)
    return payload


def command_illustration_config(args) -> int:
    payload = update_illustration_config(
        Path(args.root),
        set_adapter=args.set_adapter,
        set_model=args.set_model,
        set_response_model=args.set_response_model,
        set_size=args.set_size,
        set_quality=args.set_quality,
        set_base_url=args.set_base_url,
        set_prompt_pack=args.set_prompt_pack,
        set_character_template=args.set_character_template,
        set_scene_template=args.set_scene_template,
        set_promo_template=args.set_promo_template,
        set_commercial_mode=args.set_commercial_mode,
        set_batch_delivery_mode=args.set_batch_delivery_mode,
        set_external_agent_skill=args.set_external_agent_skill,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_pack_migrate(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    payload = migrate_project_prompt_pack_documents(root, dry_run=bool(args.dry_run))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_illustration_pack_export(args) -> int:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    saved_pack = export_prompt_pack_document(
        root,
        state.get("illustrations", {}),
        requested_pack_name=str(args.prompt_pack or "").strip(),
        file_name=str(args.file_name or "").strip(),
    )
    if bool(args.set_as_default):
        saved_summary = summarize_prompt_pack(saved_pack)
        next_pack_name = str(saved_summary.get("name") or saved_pack.get("id") or "").strip()
        if next_pack_name:
            update_illustration_config(root, set_prompt_pack=next_pack_name)
            state = load_project_state(root)
    payload = build_illustration_config_payload(root, state)
    payload["exported"] = True
    payload["exportedPack"] = {
        "summary": summarize_prompt_pack(saved_pack),
        "document": saved_pack,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def export_illustration_batch_manifest(args) -> dict[str, Any]:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    spec_path = Path(args.spec).resolve()
    raw_spec = _load_json_compatible_object(spec_path)
    try:
        spec = normalize_illustration_batch_spec(raw_spec)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    illustrations_state = state.get("illustrations", {})
    batch_system = illustrations_state.get("batchSystem", {})
    delivery_mode = _normalize_delivery_mode(
        str(args.delivery_mode or batch_system.get("defaultDeliveryMode") or "webui-manual")
    )
    external_agent_skill = str(batch_system.get("externalAgentSkill") or "story-canvas-imagegen").strip()
    manifest_label = str(spec.get("label") or spec_path.stem or "illustration-batch").strip()
    manifest_path = Path(args.output).resolve() if args.output else default_illustration_batch_manifest_path(root, manifest_label)
    jobs = []

    for index, job_spec in enumerate(spec.get("jobs", [])):
        job_args = _build_batch_job_args(
            root=root,
            spec_dir=spec_path.parent,
            defaults=spec.get("defaults", {}),
            job_spec=job_spec,
        )
        payload = _build_payload(root, state, job_args)
        _validate_generation_payload(payload)
        provider_request = _build_provider_request(payload, job_args, illustrations_state.get("adapter", {}))
        output_name = job_args.output_name or _default_output_name(payload)
        output_path = _resolve_output_path(root, payload, output_name)
        output_files = [
            str(resolve_output_path_for_index(output_path, output_index, output_path.suffix.lstrip(".") or "png"))
            for output_index in range(_normalize_batch_count((payload.get("batch") or {}).get("count", 1)))
        ]
        delivery = build_batch_delivery_payload(
            delivery_mode=delivery_mode,
            payload=payload,
            provider_request=provider_request,
            output_files=output_files,
            external_agent_skill=external_agent_skill,
        )
        jobs.append(
            {
                "jobId": f"ill-batch-job-{index + 1:03d}",
                "targetRef": {
                    "type": payload.get("targetType", ""),
                    "targetId": payload.get("targetId", ""),
                },
                "targetName": payload.get("targetName", ""),
                "mode": payload.get("mode", ""),
                "batch": payload.get("batch", {}),
                "outputName": output_name,
                "outputFiles": output_files,
                "payload": payload,
                "promptSnapshot": payload.get("promptSnapshot", {}),
                "policySnapshot": payload.get("policySnapshot", {}),
                "providerRequest": provider_request,
                "delivery": delivery,
            }
        )

    manifest = {
        "batchId": f"ill-batch-{stable_hash(str(root) + manifest_label + now_iso())}",
        "version": "1.0",
        "label": manifest_label,
        "projectRoot": str(root),
        "illustrationsFile": str(_illustrations_path(root)),
        "sourceSpec": str(spec_path),
        "deliveryMode": delivery_mode,
        "externalAgentSkill": external_agent_skill if delivery_mode == "external-agent" else "",
        "generatedAt": now_iso(),
        "jobs": jobs,
    }
    manifest["summary"] = build_batch_manifest_summary(manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "saved": True,
        "manifestPath": str(manifest_path),
        "manifest": manifest,
    }


def record_illustration_batch_manifest(args) -> dict[str, Any]:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    manifest_path = Path(args.manifest).resolve()
    manifest = _load_json_compatible_object(manifest_path)
    if not isinstance(manifest, dict):
        raise SystemExit("batch manifest 必须是对象")
    jobs = manifest.get("jobs", [])
    if not isinstance(jobs, list) or not jobs:
        raise SystemExit("batch manifest jobs 必须是非空数组")

    delivery_mode = _normalize_delivery_mode(str(manifest.get("deliveryMode") or "webui-manual"))
    illustrations_state = state.setdefault("illustrations", {})
    generated = illustrations_state.setdefault("generated", [])
    imported_entries = []

    for job in jobs:
        payload = job.get("payload", {})
        provider_request = job.get("providerRequest", {})
        output_files = job.get("outputFiles", [])
        if not isinstance(payload, dict) or not isinstance(provider_request, dict) or not isinstance(output_files, list):
            raise SystemExit("batch manifest job 缺少合法的 payload/providerRequest/outputFiles")
        artifact_records = _artifact_records_from_output_files(output_files)
        entry = _build_generated_entry(
            payload=payload,
            provider_request=provider_request,
            artifact_records=artifact_records,
            provider_results=[],
            import_metadata={
                "importMode": delivery_mode,
                "manifestPath": str(manifest_path),
                "batchId": str(manifest.get("batchId") or ""),
                "jobId": str(job.get("jobId") or ""),
            },
        )
        generated.append(entry)
        imported_entries.append(entry)

    save_state(root, state)
    return {
        "saved": True,
        "manifestPath": str(manifest_path),
        "importedCount": len(imported_entries),
        "illustrations": imported_entries,
    }


def export_illustration_assets(args) -> dict[str, Any]:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)
    generated = state.get("illustrations", {}).get("generated", [])
    illustration_id = str(args.illustration_id or "").strip()
    if not illustration_id:
        raise SystemExit("缺少 illustration id")
    entry = next((item for item in generated if str(item.get("id") or "") == illustration_id), None)
    if entry is None:
        raise SystemExit(f"illustration 不存在: {illustration_id}")
    assets = asset_records_from_entry(root, entry)
    if not assets:
        raise SystemExit(f"illustration 没有可导出的资产: {illustration_id}")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else root / "exports" / "illustrations" / illustration_id
    output_dir.mkdir(parents=True, exist_ok=True)
    exported_files = []
    for asset in assets:
        source = Path(asset.get("filePath", ""))
        if not source.exists():
            raise SystemExit(f"导出源文件不存在: {source}")
        destination = output_dir / source.name
        shutil.copy2(source, destination)
        exported_files.append(str(destination))
    return {
        "saved": True,
        "illustrationId": illustration_id,
        "outputDir": str(output_dir),
        "files": exported_files,
    }


def _build_generated_entry(
    *,
    payload: dict[str, Any],
    provider_request: dict[str, Any],
    artifact_records: list[dict[str, Any]],
    provider_results: list[dict[str, Any]],
    import_metadata: dict[str, Any],
) -> dict[str, Any]:
    if not artifact_records:
        raise SystemExit("生成结果缺少 artifacts")
    primary_asset = artifact_records[0]
    storage_scope = "project-temp" if payload["targetType"] == "temporary" else "story-project"
    entry = {
        "id": f"ill-{stable_hash(payload['targetType'] + payload['targetId'] + now_iso())}",
        "type": payload["targetType"],
        "mode": payload["mode"],
        "useCase": payload["useCase"],
        "targetName": payload.get("targetName", ""),
        "chapterId": payload["targetId"] if payload["targetType"] == "chapter" else None,
        "entityId": payload["targetId"] if payload["targetType"] == "entity" else None,
        "tempLabel": payload["targetId"] if payload["targetType"] == "temporary" else None,
        "promptText": payload["promptText"],
        "promptPackRef": payload["promptPackRef"],
        "templateId": payload["templateId"],
        "modifierRefs": payload["modifierRefs"],
        "commercialMode": payload["commercialMode"],
        "promptSnapshot": payload["promptSnapshot"],
        "policySnapshot": payload["policySnapshot"],
        "revisedPrompt": primary_asset.get("revisedPrompt") or payload["promptText"],
        "inputImages": payload["inputImages"],
        "maskPath": payload["maskPath"],
        "targetRef": {
            "type": payload["targetType"],
            "targetId": payload["targetId"],
        },
        "batch": {
            "count": _normalize_batch_count((payload.get("batch") or {}).get("count", 1)),
            "variantStrategy": str((payload.get("batch") or {}).get("variantStrategy") or "same-template"),
        },
        "filePath": primary_asset["filePath"],
        "artifacts": artifact_records,
        "metadata": {
            "asset": {
                "source": primary_asset["source"],
                "extension": primary_asset["extension"],
                "bytes": primary_asset["bytes"],
            },
            "assetCount": len(artifact_records),
            "storageScope": storage_scope,
            "providerRequest": provider_request,
        },
        "generatedAt": now_iso(),
    }
    if provider_results:
        if len(provider_results) == 1:
            entry["metadata"]["providerResult"] = provider_results[0]
        else:
            entry["metadata"]["providerResults"] = provider_results
    if import_metadata:
        entry["metadata"]["import"] = import_metadata
    return entry


def _artifact_records_from_output_files(output_files: list[str]) -> list[dict[str, Any]]:
    records = []
    for index, file_path in enumerate(output_files):
        path = Path(str(file_path))
        if not path.exists():
            raise SystemExit(f"batch output 不存在: {path}")
        records.append(
            {
                "index": index,
                "filePath": str(path),
                "bytes": path.stat().st_size,
                "source": "batch-import",
                "extension": path.suffix.lstrip(".") or "png",
                "revisedPrompt": "",
                "isPrimary": index == 0,
                "batchIndex": index,
            }
        )
    return records


def _build_batch_job_args(
    *,
    root: Path,
    spec_dir: Path,
    defaults: dict[str, Any],
    job_spec: dict[str, Any],
) -> SimpleNamespace:
    mode = str(job_spec.get("mode") or defaults.get("mode") or "text-to-image").strip() or "text-to-image"
    input_images = job_spec.get("inputImages") or defaults.get("inputImages") or []
    modifier_refs = job_spec.get("modifierRefs") or defaults.get("modifierRefs") or []
    mask_path = str(job_spec.get("mask") or defaults.get("mask") or "").strip()
    output_name = str(job_spec.get("outputName") or "").strip()
    if not output_name:
        output_prefix = str(defaults.get("outputNamePrefix") or "").strip()
        target_id = str(job_spec.get("chapterId") or job_spec.get("entityId") or job_spec.get("tempLabel") or "target").strip()
        if output_prefix:
            output_name = f"{output_prefix}-{target_id}.png"
    return SimpleNamespace(
        root=str(root),
        chapter_id=str(job_spec.get("chapterId") or "").strip() or None,
        entity_id=str(job_spec.get("entityId") or "").strip() or None,
        temp_label=str(job_spec.get("tempLabel") or "").strip() or None,
        use_case=str(job_spec.get("useCase") or defaults.get("useCase") or "promo").strip() or "promo",
        subject=str(job_spec.get("subject") or "").strip(),
        mode=mode,
        input_image=[_resolve_batch_input_path(spec_dir, item) for item in input_images],
        mask=_resolve_batch_input_path(spec_dir, mask_path) if mask_path else "",
        prompt_pack=str(job_spec.get("promptPack") or defaults.get("promptPack") or "").strip(),
        template_id=str(job_spec.get("templateId") or defaults.get("templateId") or "").strip(),
        modifier=list(modifier_refs),
        extra_prompt=str(job_spec.get("extraPrompt") or "").strip(),
        commercial_mode=str(job_spec.get("commercialMode") or defaults.get("commercialMode") or "").strip(),
        batch_count=_normalize_batch_count(job_spec.get("batchCount", defaults.get("batchCount", 1))),
        negative_prompt=str(job_spec.get("negativePrompt") or defaults.get("negativePrompt") or "").strip(),
        size=str(job_spec.get("size") or defaults.get("size") or "").strip(),
        quality=str(job_spec.get("quality") or defaults.get("quality") or "").strip(),
        output_name=output_name,
        api_key="",
        base_url="",
        response_model=str(job_spec.get("responseModel") or defaults.get("responseModel") or "").strip(),
        dry_run=True,
    )


def _resolve_batch_input_path(spec_dir: Path, raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = (spec_dir / path).resolve()
    return str(path)


def _load_json_compatible_object(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise SystemExit(f"文件不存在: {path}") from exc
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"文件不是合法 JSON-compatible YAML: {path}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"文件顶层必须是对象: {path}")
    return loaded


def _default_output_name(payload: dict[str, Any]) -> str:
    target_id = payload["targetId"] or payload["targetType"]
    if payload["targetType"] == "temporary":
        suffix = payload.get("useCase", "promo") or "promo"
    elif payload["mode"] == "inpaint":
        suffix = "inpaint"
    else:
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
    prompt_target.add_argument("--temp-label")
    prompt_parser.add_argument("--mode", required=True, choices=["text-to-image", "image-to-image", "inpaint"])
    prompt_parser.add_argument("--use-case", choices=ILLUSTRATION_USE_CASE_CHOICES)
    prompt_parser.add_argument("--subject")
    prompt_parser.add_argument("--input-image", action="append")
    prompt_parser.add_argument("--mask")
    prompt_parser.add_argument("--prompt-pack")
    prompt_parser.add_argument("--template-id")
    prompt_parser.add_argument("--modifier", action="append")
    prompt_parser.add_argument("--extra-prompt")
    prompt_parser.add_argument("--text-design-mode", choices=["none", "designed"])
    prompt_parser.add_argument("--title-text")
    prompt_parser.add_argument("--subtitle-text")
    prompt_parser.add_argument("--body-text")
    prompt_parser.add_argument("--font-style-hint")
    prompt_parser.add_argument("--commercial-mode", choices=["personal", "commercial"])
    prompt_parser.add_argument("--negative-prompt")
    prompt_parser.add_argument("--batch-count", type=int, default=1)
    prompt_parser.set_defaults(func=command_illustration_prompt)

    generate_parser = illustration_subparsers.add_parser("generate", help="Generate an illustration or emit a dry-run request")
    generate_parser.add_argument("--root", required=True)
    generate_target = generate_parser.add_mutually_exclusive_group(required=True)
    generate_target.add_argument("--chapter-id")
    generate_target.add_argument("--entity-id")
    generate_target.add_argument("--temp-label")
    generate_parser.add_argument("--mode", required=True, choices=["text-to-image", "image-to-image", "inpaint"])
    generate_parser.add_argument("--use-case", choices=ILLUSTRATION_USE_CASE_CHOICES)
    generate_parser.add_argument("--subject")
    generate_parser.add_argument("--input-image", action="append")
    generate_parser.add_argument("--mask")
    generate_parser.add_argument("--prompt-pack")
    generate_parser.add_argument("--template-id")
    generate_parser.add_argument("--modifier", action="append")
    generate_parser.add_argument("--extra-prompt")
    generate_parser.add_argument("--text-design-mode", choices=["none", "designed"])
    generate_parser.add_argument("--title-text")
    generate_parser.add_argument("--subtitle-text")
    generate_parser.add_argument("--body-text")
    generate_parser.add_argument("--font-style-hint")
    generate_parser.add_argument("--commercial-mode", choices=["personal", "commercial"])
    generate_parser.add_argument("--negative-prompt")
    generate_parser.add_argument("--size")
    generate_parser.add_argument("--quality")
    generate_parser.add_argument("--output-name")
    generate_parser.add_argument("--api-key")
    generate_parser.add_argument("--base-url")
    generate_parser.add_argument("--response-model")
    generate_parser.add_argument("--dry-run", action="store_true")
    generate_parser.add_argument("--batch-count", type=int, default=1)
    generate_parser.set_defaults(func=command_illustration_generate)

    batch_export_parser = illustration_subparsers.add_parser("batch-export", help="Export a batch illustration manifest")
    batch_export_parser.add_argument("--root", required=True)
    batch_export_parser.add_argument("--spec", required=True)
    batch_export_parser.add_argument("--delivery-mode", choices=["webui-manual", "external-agent"])
    batch_export_parser.add_argument("--output")
    batch_export_parser.set_defaults(func=command_illustration_batch_export)

    batch_record_parser = illustration_subparsers.add_parser("batch-record", help="Record generated files from a batch manifest")
    batch_record_parser.add_argument("--root", required=True)
    batch_record_parser.add_argument("--manifest", required=True)
    batch_record_parser.set_defaults(func=command_illustration_batch_record)

    export_parser = illustration_subparsers.add_parser("export", help="Export generated illustration files to another directory")
    export_parser.add_argument("--root", required=True)
    export_parser.add_argument("--illustration-id", required=True)
    export_parser.add_argument("--output-dir")
    export_parser.set_defaults(func=command_illustration_export)

    list_parser = illustration_subparsers.add_parser("list", help="List illustration config and generated records")
    list_parser.add_argument("--root", required=True)
    list_parser.set_defaults(func=command_illustration_list)

    config_parser = illustration_subparsers.add_parser("config", help="Show or update illustration config")
    config_parser.add_argument("--root", required=True)
    config_parser.add_argument("--set-adapter")
    config_parser.add_argument("--set-model")
    config_parser.add_argument("--set-response-model")
    config_parser.add_argument("--set-size")
    config_parser.add_argument("--set-quality")
    config_parser.add_argument("--set-base-url")
    config_parser.add_argument("--set-prompt-pack")
    config_parser.add_argument("--set-character-template")
    config_parser.add_argument("--set-scene-template")
    config_parser.add_argument("--set-promo-template")
    config_parser.add_argument("--set-commercial-mode", choices=["personal", "commercial"])
    config_parser.add_argument("--set-batch-delivery-mode", choices=["webui-manual", "external-agent"])
    config_parser.add_argument("--set-external-agent-skill")
    config_parser.set_defaults(func=command_illustration_config)

    pack_migrate_parser = illustration_subparsers.add_parser("pack-migrate", help="Migrate project prompt packs to canonical templates")
    pack_migrate_parser.add_argument("--root", required=True)
    pack_migrate_parser.add_argument("--dry-run", action="store_true")
    pack_migrate_parser.set_defaults(func=command_illustration_pack_migrate)

    pack_export_parser = illustration_subparsers.add_parser("pack-export", help="Export a builtin or selected prompt pack into the project")
    pack_export_parser.add_argument("--root", required=True)
    pack_export_parser.add_argument("--prompt-pack")
    pack_export_parser.add_argument("--file-name")
    pack_export_parser.add_argument("--set-as-default", action="store_true")
    pack_export_parser.set_defaults(func=command_illustration_pack_export)
