from __future__ import annotations

from copy import deepcopy
from typing import Any


DELIVERY_MODES = ("webui-manual", "external-agent")


def normalize_batch_delivery_mode(value: str) -> str:
    normalized = str(value or "").strip() or "webui-manual"
    if normalized not in DELIVERY_MODES:
        raise ValueError(f"未知 batch delivery mode: {normalized}")
    return normalized


def normalize_illustration_batch_spec(raw_spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_spec, dict):
        raise ValueError("batch spec 必须是对象")

    defaults = raw_spec.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise ValueError("batch spec defaults 必须是对象")

    jobs = raw_spec.get("jobs", [])
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("batch spec jobs 必须是非空数组")

    normalized_jobs: list[dict[str, Any]] = []
    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            raise ValueError(f"batch spec job[{index}] 必须是对象")
        chapter_id = str(job.get("chapterId") or "").strip()
        entity_id = str(job.get("entityId") or "").strip()
        temp_label = str(job.get("tempLabel") or "").strip()
        target_count = sum(1 for item in (chapter_id, entity_id, temp_label) if item)
        if target_count != 1:
            raise ValueError(f"batch spec job[{index}] 必须且只能指定 chapterId、entityId 或 tempLabel 之一")
        normalized_job = deepcopy(job)
        normalized_job["chapterId"] = chapter_id
        normalized_job["entityId"] = entity_id
        normalized_job["tempLabel"] = temp_label
        normalized_job["useCase"] = str(job.get("useCase") or defaults.get("useCase") or "promo").strip() or "promo"
        normalized_job["subject"] = str(job.get("subject") or "").strip()
        normalized_job["mode"] = str(job.get("mode") or "").strip()
        normalized_job["promptPack"] = str(job.get("promptPack") or "").strip()
        normalized_job["templateId"] = str(job.get("templateId") or "").strip()
        normalized_job["extraPrompt"] = str(job.get("extraPrompt") or "").strip()
        normalized_job["commercialMode"] = str(job.get("commercialMode") or "").strip()
        normalized_job["negativePrompt"] = str(job.get("negativePrompt") or "").strip()
        normalized_job["outputName"] = str(job.get("outputName") or "").strip()
        normalized_job["responseModel"] = str(job.get("responseModel") or "").strip()
        normalized_job["size"] = str(job.get("size") or "").strip()
        normalized_job["quality"] = str(job.get("quality") or "").strip()
        normalized_job["mask"] = str(job.get("mask") or "").strip()
        modifier_refs = job.get("modifierRefs", [])
        if modifier_refs is None:
            modifier_refs = []
        if not isinstance(modifier_refs, list):
            raise ValueError(f"batch spec job[{index}] modifierRefs 必须是数组")
        input_images = job.get("inputImages", [])
        if input_images is None:
            input_images = []
        if not isinstance(input_images, list):
            raise ValueError(f"batch spec job[{index}] inputImages 必须是数组")
        normalized_job["modifierRefs"] = [str(item).strip() for item in modifier_refs if str(item).strip()]
        normalized_job["inputImages"] = [str(item).strip() for item in input_images if str(item).strip()]
        normalized_job["batchCount"] = _normalize_positive_int(job.get("batchCount", defaults.get("batchCount", 1)))
        normalized_jobs.append(normalized_job)

    normalized_defaults = {
        "mode": str(defaults.get("mode") or "").strip(),
        "useCase": str(defaults.get("useCase") or "promo").strip() or "promo",
        "promptPack": str(defaults.get("promptPack") or "").strip(),
        "templateId": str(defaults.get("templateId") or "").strip(),
        "commercialMode": str(defaults.get("commercialMode") or "").strip(),
        "negativePrompt": str(defaults.get("negativePrompt") or "").strip(),
        "outputNamePrefix": str(defaults.get("outputNamePrefix") or "").strip(),
        "responseModel": str(defaults.get("responseModel") or "").strip(),
        "size": str(defaults.get("size") or "").strip(),
        "quality": str(defaults.get("quality") or "").strip(),
        "batchCount": _normalize_positive_int(defaults.get("batchCount", 1)),
    }
    modifier_refs = defaults.get("modifierRefs", [])
    if modifier_refs is None:
        modifier_refs = []
    if not isinstance(modifier_refs, list):
        raise ValueError("batch spec defaults modifierRefs 必须是数组")
    input_images = defaults.get("inputImages", [])
    if input_images is None:
        input_images = []
    if not isinstance(input_images, list):
        raise ValueError("batch spec defaults inputImages 必须是数组")
    normalized_defaults["modifierRefs"] = [str(item).strip() for item in modifier_refs if str(item).strip()]
    normalized_defaults["inputImages"] = [str(item).strip() for item in input_images if str(item).strip()]
    normalized_defaults["mask"] = str(defaults.get("mask") or "").strip()

    return {
        "label": str(raw_spec.get("label") or "").strip(),
        "defaults": normalized_defaults,
        "jobs": normalized_jobs,
    }


def build_batch_delivery_payload(
    *,
    delivery_mode: str,
    payload: dict[str, Any],
    provider_request: dict[str, Any],
    output_files: list[str],
    external_agent_skill: str,
) -> dict[str, Any]:
    normalized_mode = normalize_batch_delivery_mode(delivery_mode)
    delivery = {
        "mode": normalized_mode,
        "prompt": payload.get("promptText", ""),
        "negativePrompt": payload.get("policySnapshot", {}).get("negativePrompt", ""),
        "size": provider_request.get("size", ""),
        "quality": provider_request.get("quality", ""),
        "inputImages": list(payload.get("inputImages", [])),
        "maskPath": payload.get("maskPath", ""),
        "outputFiles": list(output_files),
    }
    if normalized_mode == "webui-manual":
        delivery["notes"] = [
            "将 prompt / negativePrompt 和尺寸手动填入 WebUI。",
            "生成结果必须写回 outputFiles 指定路径后，再执行 story-canvas illustration batch-record。",
        ]
        return delivery

    delivery["skillName"] = external_agent_skill or "story-canvas-imagegen"
    delivery["action"] = "edit" if payload.get("mode") in {"image-to-image", "inpaint"} else "generate"
    delivery["instructions"] = [
        "外部 agent 应逐条消费 manifest jobs，并把生成结果写入 outputFiles。",
        "写回完成后，返回仓库执行 story-canvas illustration batch-record 导入历史。",
    ]
    return delivery


def build_batch_manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    jobs = manifest.get("jobs", [])
    target_refs = []
    total_outputs = 0
    for job in jobs:
        target_ref = job.get("targetRef", {})
        target_refs.append(
            {
                "type": target_ref.get("type", ""),
                "targetId": target_ref.get("targetId", ""),
                "targetName": job.get("targetName", ""),
            }
        )
        total_outputs += len(job.get("outputFiles", []))
    return {
        "jobCount": len(jobs),
        "plannedOutputCount": total_outputs,
        "targets": target_refs,
    }


def _normalize_positive_int(value: Any) -> int:
    raw_value = 1 if value in (None, "") else value
    try:
        count = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("batchCount 必须是大于等于 1 的整数") from exc
    if count < 1:
        raise ValueError("batchCount 必须是大于等于 1 的整数")
    return count
