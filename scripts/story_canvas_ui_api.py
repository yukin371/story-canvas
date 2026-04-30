#!/usr/bin/env python3
from __future__ import annotations

import cgi
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import uuid
from functools import lru_cache
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.commands.illustration import (
    build_illustration_dry_run_response,
    run_illustration_generation,
    update_illustration_config,
)
from story_harness_cli.commands.illustration_support import decorate_generated_entry, resolve_output_path_for_index
from story_harness_cli.protocol import (
    chapter_path,
    ensure_project_root,
    export_prompt_pack_document,
    load_available_prompt_packs,
    load_project_state,
    migrate_project_prompt_pack_documents,
    resolve_prompt_pack,
    resolve_state_path,
    save_prompt_pack_document,
    save_state,
    serialize_prompt_pack_document,
    summarize_prompt_pack,
)
from story_harness_cli.protocol.files import LAYOUT_FLAT
from story_harness_cli.protocol.io import dump_json_compatible_yaml
from story_harness_cli.protocol.schema import default_project_state
from story_harness_cli.providers.image import OpenAIImageHTTPClient
from story_harness_cli.providers.image.openai_http import resolve_api_key
from story_harness_cli.providers.image.openai_http import resolve_base_url
from story_harness_cli.providers import load_embedding_provider
from story_harness_cli.providers.embedding import resolve_model_name as resolve_embedding_model_name
from story_harness_cli.providers.text import (
    OpenAITextHTTPClient,
    resolve_api_key as resolve_text_api_key,
    resolve_base_url as resolve_text_base_url,
)
from story_harness_cli.services import build_chapter_illustration_payload, build_entity_illustration_payload
from story_harness_cli.services.text_provider_review import parse_text_provider_json_object
from story_harness_cli.utils import now_iso
from story_harness_cli.utils.project_meta import normalize_primary_genre
from story_harness_cli.utils.text import count_words, paragraphs_from_text

PROJECTS_ROOT = REPO_ROOT / "projects"
WORKBENCH_STATE_ROOT = Path.home() / ".story-canvas"
WORKBENCH_SETTINGS_FILE = WORKBENCH_STATE_ROOT / "workbench-settings.json"
WORKBENCH_PROJECTS_FILE = WORKBENCH_STATE_ROOT / "project-registry.json"
WORKBENCH_TEMP_UPLOAD_ROOT = WORKBENCH_STATE_ROOT / "tmp" / "illustration-inputs"
WORKBENCH_ILLUSTRATION_SANDBOX_ROOT = WORKBENCH_STATE_ROOT / "workspace-illustration-sandbox"


def _send_cors_headers(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


def _json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    _send_cors_headers(handler)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _load_json_request(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _file_response(handler: BaseHTTPRequestHandler, path: Path) -> None:
    body = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    handler.send_response(HTTPStatus.OK)
    _send_cors_headers(handler)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _parse_form_request(handler: BaseHTTPRequestHandler) -> cgi.FieldStorage:
    return cgi.FieldStorage(
        fp=handler.rfile,
        headers=handler.headers,
        environ={
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": handler.headers.get("Content-Type", ""),
        },
    )


def _coerce_form_value(form: cgi.FieldStorage, name: str, default: str = "") -> str:
    value = form.getfirst(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _save_upload(field: cgi.FieldStorage, target_dir: Path, prefix: str) -> Path | None:
    if not getattr(field, "file", None) or not field.filename:
        return None
    suffix = Path(field.filename).suffix or ".png"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns()}{suffix}"
    with file_path.open("wb") as handle:
        while True:
            chunk = field.file.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    return file_path.resolve()


def _cleanup_paths(paths: list[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _build_illustration_body_from_form(
    form: cgi.FieldStorage,
    *,
    persist_uploads: bool,
) -> tuple[dict[str, Any], list[Path]]:
    root_value = _coerce_form_value(form, "root")
    root = _coerce_project_root(root_value) if root_value else None

    cleanup_paths: list[Path] = []
    temp_dir = WORKBENCH_TEMP_UPLOAD_ROOT
    target_dir = root / "assets" / "illustration-inputs" / "ui-uploads" if root is not None else temp_dir
    upload_dir = target_dir if persist_uploads and root is not None else temp_dir

    input_images: list[str] = []
    input_image_path = _coerce_form_value(form, "inputImagePath")
    if input_image_path:
        input_images.append(input_image_path)
    if "inputImageFile" in form:
        uploaded_input = _save_upload(form["inputImageFile"], upload_dir, "input")
        if uploaded_input is not None:
            input_images = [str(uploaded_input.resolve())]
            if not persist_uploads:
                cleanup_paths.append(uploaded_input)

    mask_path = _coerce_form_value(form, "maskPath")
    if "maskFile" in form:
        uploaded_mask = _save_upload(form["maskFile"], upload_dir, "mask")
        if uploaded_mask is not None:
            mask_path = str(uploaded_mask.resolve())
            if not persist_uploads:
                cleanup_paths.append(uploaded_mask)

    body: dict[str, Any] = {
        "root": str(root) if root is not None else "",
        "targetType": _coerce_form_value(form, "targetType") or None,
        "useCase": _coerce_form_value(form, "useCase") or None,
        "textDesignMode": _coerce_form_value(form, "textDesignMode") or None,
        "titleText": _coerce_form_value(form, "titleText") or None,
        "subtitleText": _coerce_form_value(form, "subtitleText") or None,
        "bodyText": _coerce_form_value(form, "bodyText") or None,
        "fontStyleHint": _coerce_form_value(form, "fontStyleHint") or None,
        "manualTargetName": _coerce_form_value(form, "manualTargetName") or None,
        "mode": _coerce_form_value(form, "mode", "text-to-image"),
        "chapterId": _coerce_form_value(form, "chapterId") or None,
        "entityId": _coerce_form_value(form, "entityId") or None,
        "promptText": _coerce_form_value(form, "promptText") or None,
        "extraPrompt": _coerce_form_value(form, "extraPrompt") or None,
        "negativePrompt": _coerce_form_value(form, "negativePrompt") or None,
        "promptPack": _coerce_form_value(form, "promptPack") or None,
        "templateId": _coerce_form_value(form, "templateId") or None,
        "modifierRefs": [str(item).strip() for item in form.getlist("modifierRefs") if str(item).strip()],
        "commercialMode": _coerce_form_value(form, "commercialMode") or None,
        "size": _coerce_form_value(form, "size") or None,
        "quality": _coerce_form_value(form, "quality") or None,
        "responseModel": _coerce_form_value(form, "responseModel") or None,
        "baseUrl": _coerce_form_value(form, "baseUrl") or None,
        "apiKey": _coerce_form_value(form, "apiKey") or None,
        "batchCount": _coerce_form_value(form, "batchCount") or None,
        "inputImages": input_images,
        "maskPath": mask_path or None,
    }
    return body, cleanup_paths


def _load_illustration_request(
    handler: BaseHTTPRequestHandler,
    *,
    persist_uploads: bool,
) -> tuple[dict[str, Any], list[Path]]:
    content_type, _ = cgi.parse_header(handler.headers.get("Content-Type", ""))
    if content_type == "multipart/form-data":
        form = _parse_form_request(handler)
        return _build_illustration_body_from_form(form, persist_uploads=persist_uploads)
    return _load_json_request(handler), []


def _resolve_project_asset_path(root: Path, raw_path: str) -> Path:
    if not raw_path:
        raise ValueError("缺少资产路径。")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (root / path).resolve()
    else:
        path = path.resolve()
    assets_root = (root / "assets").resolve()
    if not _is_within(path, assets_root):
        raise ValueError("只允许预览项目 assets 目录下的文件。")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)
    return path


def _resolve_workbench_asset_path(raw_path: str) -> Path:
    if not raw_path:
        raise ValueError("缺少工作台资产路径。")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (WORKBENCH_STATE_ROOT / path).resolve()
    else:
        path = path.resolve()
    if not _is_within(path, WORKBENCH_STATE_ROOT.resolve()):
        raise ValueError("只允许预览工作台状态目录下的文件。")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)
    return path


def _resolve_project_local_path(root: Path, raw_path: str) -> Path:
    if not raw_path:
        raise ValueError("缺少本地路径。")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (root / path).resolve()
    else:
        path = path.resolve()
    if not _is_within(path, root.resolve()):
        raise ValueError("只允许打开项目目录内的文件或文件夹。")
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _resolve_workbench_local_path(raw_path: str) -> Path:
    if not raw_path:
        raise ValueError("缺少工作台路径。")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (WORKBENCH_STATE_ROOT / path).resolve()
    else:
        path = path.resolve()
    if not _is_within(path, WORKBENCH_STATE_ROOT.resolve()):
        raise ValueError("只允许打开工作台状态目录下的文件或文件夹。")
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _open_path_in_shell(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=True)
        return
    subprocess.run(["xdg-open", str(path)], check=True)


def _open_local_folder_request(body: dict[str, Any]) -> dict[str, Any]:
    scope = str(body.get("scope") or "project").strip() or "project"
    raw_path = str(body.get("path") or "").strip()
    if scope == "workspace":
        target = _resolve_workbench_local_path(raw_path)
    else:
        root = _coerce_project_root(str(body.get("root") or ""))
        target = _resolve_project_local_path(root, raw_path)
    folder = target if target.is_dir() else target.parent
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(folder)
    _open_path_in_shell(folder)
    return {"opened": True, "path": str(folder), "scope": scope}


def _project_key(path: Path) -> str:
    return path.name


def _coerce_project_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    ensure_project_root(root)
    return root


def _resolve_existing_directory(value: str) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        candidate = Path(text).expanduser()
    except OSError:
        return None
    if candidate.exists():
        target = candidate if candidate.is_dir() else candidate.parent
        try:
            return target.resolve()
        except OSError:
            return target
    parent = candidate.parent
    if parent.exists() and parent.is_dir():
        try:
            return parent.resolve()
        except OSError:
            return parent
    return None


def _pick_folder_with_tk(initial_dir: Path | None) -> str:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    try:
        return str(
            filedialog.askdirectory(
                parent=root,
                title="选择 Story Canvas 项目目录",
                initialdir=str(initial_dir) if initial_dir else str(PROJECTS_ROOT),
                mustexist=True,
            )
            or ""
        )
    finally:
        root.destroy()


def _pick_folder_with_powershell(initial_dir: Path | None) -> str:
    if os.name != "nt":
        return ""
    selected_path = initial_dir or (PROJECTS_ROOT.resolve() if PROJECTS_ROOT.exists() else Path.home().resolve())
    literal = str(selected_path).replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
        "$dialog.Description = '选择 Story Canvas 项目目录'; "
        "$dialog.ShowNewFolderButton = $false; "
        f"$dialog.SelectedPath = '{literal}'; "
        "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
        "[Console]::Out.Write($dialog.SelectedPath) }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell folder dialog failed")
    return result.stdout.strip()


def _select_folder_dialog(body: dict[str, Any]) -> dict[str, Any]:
    initial_dir = _resolve_existing_directory(str(body.get("initialPath") or ""))
    if initial_dir is None:
        initial_dir = PROJECTS_ROOT.resolve() if PROJECTS_ROOT.exists() else Path.home().resolve()

    last_error: Exception | None = None
    for picker in (_pick_folder_with_tk, _pick_folder_with_powershell):
        try:
            selected = picker(initial_dir).strip()
        except Exception as exc:
            last_error = exc
            continue
        if not selected:
            raise ValueError("未选择目录。")
        root = Path(selected).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("选择的路径不是目录。")
        return {"path": str(root)}

    if last_error is not None:
        raise ValueError(f"无法打开目录选择器: {last_error}") from last_error
    raise ValueError("无法打开目录选择器。")


def _normalize_project_dir_name(raw_value: str, title: str) -> str:
    source = (raw_value or title).strip()
    source = re.sub(r'[<>:"/\\|?*]+', "-", source)
    source = re.sub(r"\s+", "-", source)
    source = source.strip(" .-_")
    if source:
        return source
    return f"project-{time.strftime('%Y%m%d-%H%M%S')}"


def _create_project(body: dict[str, Any]) -> dict[str, Any]:
    title = str(body.get("title") or "").strip()
    if not title:
        raise ValueError("缺少项目标题。")

    genre = str(body.get("genre") or "").strip()
    directory_name = _normalize_project_dir_name(str(body.get("directoryName") or ""), title)
    root = (PROJECTS_ROOT / directory_name).resolve()
    if root.exists():
        raise ValueError(f"项目目录已存在: {root.name}")

    root.mkdir(parents=True, exist_ok=False)
    for relative in ("chapters", "proposals", "reviews", "projections", "logs"):
        (root / relative).mkdir(exist_ok=True)

    defaults = default_project_state()
    now = now_iso()
    chapter_id = "chapter-001"
    chapter_title = str(body.get("chapterTitle") or "第一章").strip() or "第一章"
    project = defaults["project"] | {
        "title": title,
        "genre": genre,
        "defaultMode": "driving",
        "activeChapterId": chapter_id,
        "positioning": {
            "primaryGenre": normalize_primary_genre(genre),
            "subGenre": "",
            "styleTags": [],
            "targetAudience": [],
        },
        "storyContract": {
            "corePromises": [],
            "avoidances": [],
            "endingContract": "",
            "paceContract": "",
        },
        "emotionalContract": defaults["project"].get("emotionalContract", {}),
        "storyTemplate": defaults["project"].get("storyTemplate", {}),
        "commercialPositioning": defaults["project"].get("commercialPositioning", {}),
        "createdAt": now,
        "updatedAt": now,
    }
    outline = {
        "chapters": [
            {
                "id": chapter_id,
                "title": chapter_title,
                "status": "draft",
                "beats": [],
                "scenePlans": [],
            }
        ],
        "chapterDirections": [],
        "volumes": [],
    }

    dump_json_compatible_yaml(resolve_state_path(root, "project", layout=LAYOUT_FLAT), project)
    dump_json_compatible_yaml(resolve_state_path(root, "outline", layout=LAYOUT_FLAT), outline)
    dump_json_compatible_yaml(resolve_state_path(root, "entities", layout=LAYOUT_FLAT), defaults["entities"])
    dump_json_compatible_yaml(resolve_state_path(root, "timeline", layout=LAYOUT_FLAT), defaults["timeline"])
    dump_json_compatible_yaml(resolve_state_path(root, "threads", layout=LAYOUT_FLAT), defaults["threads"])
    dump_json_compatible_yaml(resolve_state_path(root, "structures", layout=LAYOUT_FLAT), defaults["structures"])
    dump_json_compatible_yaml(resolve_state_path(root, "worldbook", layout=LAYOUT_FLAT), defaults["worldbook"])
    dump_json_compatible_yaml(resolve_state_path(root, "foreshadowing", layout=LAYOUT_FLAT), defaults["foreshadowing"])
    dump_json_compatible_yaml(root / "branches.yaml", defaults["branches"])
    dump_json_compatible_yaml(resolve_state_path(root, "proposals", layout=LAYOUT_FLAT), defaults["proposals"])
    dump_json_compatible_yaml(resolve_state_path(root, "reviews", layout=LAYOUT_FLAT), defaults["reviews"])
    dump_json_compatible_yaml(resolve_state_path(root, "story_reviews", layout=LAYOUT_FLAT), defaults["story_reviews"])
    dump_json_compatible_yaml(resolve_state_path(root, "projection", layout=LAYOUT_FLAT), defaults["projection"])
    dump_json_compatible_yaml(resolve_state_path(root, "context_lens", layout=LAYOUT_FLAT), {"currentChapterId": chapter_id, "lenses": []})
    dump_json_compatible_yaml(resolve_state_path(root, "projection_log", layout=LAYOUT_FLAT), defaults["projection_log"])

    chapter_file = chapter_path(root, chapter_id)
    chapter_file.write_text(
        (
            f"# {chapter_title}\n\n"
            "先补章节方向、beats 或 scenePlans，再开始细化正文。"
            "建议在中文连续正文中使用 `@{实体}`，"
            "或在有明确分隔符时使用 `@实体`，以便原型分析器识别。\n"
        ),
        encoding="utf-8",
    )

    _register_project_root(root, imported=True, recent=True)

    return {
        "project": _build_project_summary(root),
    }


def _scan_projects() -> list[Path]:
    if not PROJECTS_ROOT.exists():
        return []
    roots: list[Path] = []
    for child in PROJECTS_ROOT.iterdir():
        if not child.is_dir():
            continue
        try:
            ensure_project_root(child)
        except SystemExit:
            continue
        roots.append(child.resolve())
    return sorted(roots)


def _default_project_registry() -> dict[str, Any]:
    return {
        "activeRoot": "",
        "recentRoots": [],
        "importedRoots": [],
    }


def _load_project_registry() -> dict[str, Any]:
    registry = _default_project_registry()
    if not WORKBENCH_PROJECTS_FILE.exists():
        return registry
    try:
        payload = json.loads(WORKBENCH_PROJECTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return registry
    if not isinstance(payload, dict):
        return registry
    active_root = str(payload.get("activeRoot") or "").strip()
    if active_root:
        registry["activeRoot"] = active_root
    for key in ("recentRoots", "importedRoots"):
        values = payload.get(key)
        if isinstance(values, list):
            registry[key] = [str(item).strip() for item in values if str(item).strip()]
    return registry


def _save_project_registry(registry: dict[str, Any]) -> None:
    WORKBENCH_PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKBENCH_PROJECTS_FILE.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def _dedupe_roots(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw).strip()
        if not text:
            continue
        try:
            normalized = str(Path(text).expanduser().resolve())
        except OSError:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _register_project_root(root: Path, *, imported: bool, recent: bool) -> dict[str, Any]:
    ensure_project_root(root)
    registry = _load_project_registry()
    normalized_root = str(root.resolve())

    imported_roots = _dedupe_roots([*registry.get("importedRoots", [])])
    recent_roots = _dedupe_roots([*registry.get("recentRoots", [])])

    if imported and normalized_root not in imported_roots:
        imported_roots.append(normalized_root)
    if recent:
        recent_roots = [normalized_root, *[item for item in recent_roots if item != normalized_root]]
        registry["activeRoot"] = normalized_root

    registry["importedRoots"] = imported_roots
    registry["recentRoots"] = recent_roots[:12]
    _save_project_registry(registry)
    return registry


def _coerce_registered_roots(values: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in _dedupe_roots(values):
        path = Path(raw)
        try:
            ensure_project_root(path)
        except SystemExit:
            continue
        roots.append(path.resolve())
    return roots


def _import_project(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root") or "").strip()
    if not root_value:
        raise ValueError("缺少项目路径。")
    root = _coerce_project_root(root_value)
    _register_project_root(root, imported=True, recent=True)
    return {
        "project": _build_project_summary(root),
    }


def _mark_recent_project(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root") or "").strip()
    if not root_value:
        raise ValueError("缺少项目路径。")
    root = _coerce_project_root(root_value)
    _register_project_root(root, imported=False, recent=True)
    return {"ok": True, "root": str(root)}


def _set_active_project(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root") or "").strip()
    registry = _load_project_registry()
    if not root_value:
        registry["activeRoot"] = ""
        _save_project_registry(registry)
        return {"ok": True, "activeRoot": ""}

    root = _coerce_project_root(root_value)
    registry = _register_project_root(root, imported=False, recent=True)
    return {"ok": True, "activeRoot": registry.get("activeRoot", "")}


def _chapter_review_lookup(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for review in state.get("story_reviews", {}).get("chapterReviews", []):
        chapter_id = review.get("chapterId")
        if not chapter_id:
            continue
        current = latest.get(chapter_id)
        if current is None or str(review.get("generatedAt", "")) >= str(current.get("generatedAt", "")):
            latest[chapter_id] = review
    return latest


def _flatten_chapters(outline: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    chapters: list[dict[str, Any]] = []
    for chapter in outline.get("chapters", []):
        chapter_id = chapter.get("id")
        if chapter_id and chapter_id not in seen:
            chapters.append(chapter)
            seen.add(chapter_id)
    for volume in outline.get("volumes", []):
        for chapter in volume.get("chapters", []):
            chapter_id = chapter.get("id")
            if chapter_id and chapter_id not in seen:
                chapters.append(chapter)
                seen.add(chapter_id)
    return chapters


def _chapter_preview(root: Path, chapter_id: str) -> str:
    paragraphs = paragraphs_from_text(_chapter_content(root, chapter_id))
    return paragraphs[0][:120] if paragraphs else ""


def _chapter_content(root: Path, chapter_id: str) -> str:
    path = chapter_path(root, chapter_id)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _context_index_path(root: Path) -> Path:
    return root / ".story-canvas" / "context-index.json"


@lru_cache(maxsize=4)
def _load_context_embedding_provider_cached(resolved_model_name: str):
    return load_embedding_provider(resolved_model_name)


def _load_context_embedding_provider(model_name: str = ""):
    resolved_model_name = resolve_embedding_model_name(model_name)
    return _load_context_embedding_provider_cached(resolved_model_name)


def _split_context_chunks(text: str, size: int = 900) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in paragraphs_from_text(text) if paragraph.strip()]
    if not paragraphs:
        return [text[i : i + size].strip() for i in range(0, len(text), size) if text[i : i + size].strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue
        if len(current) + len(paragraph) + 2 <= size:
            current = f"{current}\n\n{paragraph}"
        else:
            chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def _embedding_provider_info(provider: Any, result: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = result or {}
    return {
        "provider": str(payload.get("provider") or getattr(provider, "provider_name", "builtin")),
        "model": str(payload.get("model") or getattr(provider, "model_name", "")),
        "dimension": int(payload.get("dimension") or getattr(provider, "dimension", 0) or 0),
    }


def _embedding_provider_matches(index_provider: dict[str, Any], provider: Any) -> bool:
    current = _embedding_provider_info(provider)
    return (
        str(index_provider.get("provider") or "") == current["provider"]
        and str(index_provider.get("model") or "") == current["model"]
        and int(index_provider.get("dimension") or 0) == current["dimension"]
    )


def _embedding_vectors(payload: dict[str, Any]) -> list[list[float]]:
    embeddings = payload.get("embeddings", [])
    if not isinstance(embeddings, list):
        return []
    normalized: list[list[float]] = []
    for vector in embeddings:
        if not isinstance(vector, list):
            continue
        normalized.append([float(value) for value in vector])
    return normalized


def _vector_cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    dimension = min(len(left), len(right))
    if dimension <= 0:
        return 0.0
    dot = sum(left[index] * right[index] for index in range(dimension))
    if dot <= 0:
        return 0.0
    left_norm = sum(value * value for value in left[:dimension]) ** 0.5
    right_norm = sum(value * value for value in right[:dimension]) ** 0.5
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _load_context_index(root: Path) -> dict[str, Any]:
    path = _context_index_path(root)
    if not path.exists():
        return {"version": 2, "provider": {}, "chunks": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "provider": {}, "chunks": []}
    if not isinstance(payload, dict):
        return {"version": 2, "provider": {}, "chunks": []}
    chunks = payload.get("chunks", [])
    if not isinstance(chunks, list):
        chunks = []
    normalized_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        normalized_chunk = dict(chunk)
        embedding = normalized_chunk.get("embedding", [])
        if isinstance(embedding, list):
            normalized_chunk["embedding"] = [float(value) for value in embedding]
        else:
            normalized_chunk["embedding"] = []
        normalized_chunks.append(normalized_chunk)
    provider = payload.get("provider", {})
    if not isinstance(provider, dict):
        provider = {}
    normalized_provider = {
        "provider": str(provider.get("provider") or ""),
        "model": str(provider.get("model") or ""),
        "dimension": int(provider.get("dimension") or 0),
    }
    return {
        "version": int(payload.get("version") or 1),
        "provider": normalized_provider,
        "chunks": normalized_chunks,
    }


def _save_context_index(root: Path, payload: dict[str, Any]) -> None:
    path = _context_index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rebuild_context_index(root: Path, provider: Any | None = None) -> dict[str, Any]:
    state = load_project_state(root)
    provider = provider or _load_context_embedding_provider()
    chunks: list[dict[str, Any]] = []
    for chapter_order, chapter in enumerate(_flatten_chapters(state.get("outline", {})), start=1):
        chapter_id = str(chapter.get("id") or "").strip()
        if not chapter_id:
            continue
        chapter_title = str(chapter.get("title") or chapter_id).strip()
        chapter_text = _chapter_content(root, chapter_id).strip()
        if not chapter_text:
            continue
        chunk_texts = _split_context_chunks(chapter_text)
        chunk_embeddings = _embedding_vectors(provider.embed_texts(chunk_texts))
        for chunk_index, chunk_text in enumerate(chunk_texts, start=1):
            chunks.append(
                {
                    "chapterId": chapter_id,
                    "chapterTitle": chapter_title,
                    "chapterOrder": chapter_order,
                    "chunkIndex": chunk_index,
                    "text": chunk_text,
                    "embedding": chunk_embeddings[chunk_index - 1] if chunk_index - 1 < len(chunk_embeddings) else [],
                }
            )
    payload = {
        "version": 2,
        "provider": _embedding_provider_info(provider),
        "chunks": chunks,
    }
    _save_context_index(root, payload)
    return payload


def _load_or_rebuild_context_index(root: Path, provider: Any | None = None) -> dict[str, Any]:
    provider = provider or _load_context_embedding_provider()
    payload = _load_context_index(root)
    if (
        int(payload.get("version") or 0) >= 2
        and payload.get("chunks")
        and _embedding_provider_matches(payload.get("provider", {}), provider)
    ):
        return payload
    return _rebuild_context_index(root, provider)


def _outline_chapter_lookup(root: Path) -> dict[str, dict[str, Any]]:
    state = load_project_state(root)
    lookup: dict[str, dict[str, Any]] = {}
    for order, chapter in enumerate(_flatten_chapters(state.get("outline", {})), start=1):
        chapter_id = str(chapter.get("id") or "").strip()
        if not chapter_id:
            continue
        lookup[chapter_id] = {
            "chapterId": chapter_id,
            "chapterTitle": str(chapter.get("title") or chapter_id).strip(),
            "chapterOrder": order,
            "direction": str(chapter.get("direction") or chapter.get("summary") or "").strip(),
        }
    return lookup


def _build_related_context(root: Path, chapter_id: str, n: int = 3) -> list[dict[str, Any]]:
    provider = _load_context_embedding_provider()
    index = _load_or_rebuild_context_index(root, provider)
    outline_lookup = _outline_chapter_lookup(root)
    query_text = _chapter_content(root, chapter_id).strip()
    if not query_text:
        lookup_entry = outline_lookup.get(chapter_id, {})
        query_text = f"{lookup_entry.get('chapterTitle', '')}\n{lookup_entry.get('direction', '')}".strip()
    query_embedding_payload = provider.embed_texts([query_text])
    query_embeddings = _embedding_vectors(query_embedding_payload)
    query_embedding = query_embeddings[0] if query_embeddings else []
    scored_items: list[tuple[float, dict[str, Any]]] = []
    for chunk in index.get("chunks", []):
        if not isinstance(chunk, dict):
            continue
        if str(chunk.get("chapterId") or "") == chapter_id:
            continue
        chunk_embedding = chunk.get("embedding", [])
        if not isinstance(chunk_embedding, list):
            continue
        score = _vector_cosine_similarity(query_embedding, [float(value) for value in chunk_embedding])
        if score <= 0:
            continue
        scored_items.append((score, chunk))

    if not scored_items:
        ordered_ids = [chapter.get("chapterId", "") for chapter in sorted(outline_lookup.values(), key=lambda item: int(item.get("chapterOrder") or 0))]
        try:
            current_index = ordered_ids.index(chapter_id)
        except ValueError:
            current_index = len(ordered_ids)
        fallback_ids = [item for item in ordered_ids[:current_index] if item and item != chapter_id][-n:]
        result: list[dict[str, Any]] = []
        for fallback_id in reversed(fallback_ids):
            text = _chapter_content(root, fallback_id).strip()
            if not text:
                continue
            lookup_entry = outline_lookup.get(fallback_id, {})
            result.append(
                {
                    "chapterId": fallback_id,
                    "chapterTitle": lookup_entry.get("chapterTitle", fallback_id),
                    "chapterOrder": lookup_entry.get("chapterOrder", 0),
                    "chunkIndex": 1,
                    "score": 0.0,
                    "text": paragraphs_from_text(text)[0][:600] if paragraphs_from_text(text) else text[:600],
                }
            )
        return result

    scored_items.sort(
        key=lambda item: (
            item[0],
            int(item[1].get("chapterOrder") or 0),
            int(item[1].get("chunkIndex") or 0),
        ),
        reverse=True,
    )
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for score, chunk in scored_items:
        chapter_key = str(chunk.get("chapterId") or "")
        if not chapter_key or chapter_key in seen:
            continue
        seen.add(chapter_key)
        result.append(
            {
                "chapterId": chapter_key,
                "chapterTitle": chunk.get("chapterTitle", chapter_key),
                "chapterOrder": chunk.get("chapterOrder", 0),
                "chunkIndex": chunk.get("chunkIndex", 0),
                "score": round(float(score), 4),
                "text": str(chunk.get("text") or "")[:900],
            }
        )
        if len(result) >= n:
            break
    return result


def _upsert_context_index(root: Path, chapter_id: str, chapter_text: str) -> None:
    provider = _load_context_embedding_provider()
    index = _load_or_rebuild_context_index(root, provider)
    outline_lookup = _outline_chapter_lookup(root)
    chapter_info = outline_lookup.get(chapter_id, {"chapterId": chapter_id, "chapterTitle": chapter_id, "chapterOrder": 0})
    chunks = [chunk for chunk in index.get("chunks", []) if str(chunk.get("chapterId") or "") != chapter_id]
    chunk_texts = _split_context_chunks(chapter_text)
    chunk_embeddings = _embedding_vectors(provider.embed_texts(chunk_texts))
    for chunk_index, chunk_text in enumerate(chunk_texts, start=1):
        chunks.append(
            {
                "chapterId": chapter_id,
                "chapterTitle": chapter_info.get("chapterTitle", chapter_id),
                "chapterOrder": chapter_info.get("chapterOrder", 0),
                "chunkIndex": chunk_index,
                "text": chunk_text,
                "embedding": chunk_embeddings[chunk_index - 1] if chunk_index - 1 < len(chunk_embeddings) else [],
            }
        )
    _save_context_index(
        root,
        {
            "version": 2,
            "provider": _embedding_provider_info(provider),
            "chunks": chunks,
        },
    )


def _load_workbench_text_provider_profile() -> dict[str, str]:
    if not WORKBENCH_SETTINGS_FILE.exists():
        return {}
    try:
        settings = json.loads(WORKBENCH_SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    providers = settings.get("illustration", {}).get("providers", [])
    if not isinstance(providers, list):
        return {}
    enabled_profiles = [
        item
        for item in providers
        if isinstance(item, dict) and item.get("enabled", True) and str(item.get("apiKey", "")).strip()
    ]
    if not enabled_profiles:
        return {}
    enabled_profiles.sort(key=lambda item: int(item.get("priority", 100) or 100))
    selected = enabled_profiles[0]
    return {
        "label": str(selected.get("label") or selected.get("id") or "workbench-provider"),
        "apiKey": str(selected.get("apiKey", "")).strip(),
        "baseUrl": str(selected.get("baseUrl", "")).strip(),
    }


def _build_workflow_generation_prompt(
    stage: str,
    body: dict[str, Any],
    *,
    related_context: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    title = str(body.get("projectTitle") or body.get("title") or "").strip()
    genre = str(body.get("genre") or "").strip()
    topic = str(body.get("topic") or "").strip()
    num_chapters = int(body.get("numChapters") or body.get("chapterCount") or 0)
    setting_text = str(body.get("settingText") or body.get("setting") or "").strip()
    outline_text = str(body.get("outlineText") or body.get("outline") or "").strip()
    chapter_num = int(body.get("chapterNum") or 1)
    chapter_title = str(body.get("chapterTitle") or "").strip()
    context_text = "\n\n".join(
        f"[{item.get('chapterId')}] {item.get('chapterTitle')}\n{item.get('text')}" for item in (related_context or [])
    ).strip()

    system_prompt = "你是中文连载故事工作流助手。只返回 JSON 对象，不要返回解释、序言或 Markdown。"
    if stage == "setting":
        user_prompt = (
            "请生成小说设定 JSON，对象必须包含 setting 字段。\n"
            f"项目标题：{title or '未命名项目'}\n"
            f"题材：{genre or '未指定'}\n"
            f"主题：{topic or '未指定'}\n"
            f"章节数：{num_chapters or '未指定'}\n"
            "请输出适合后续章节写作的设定，包含主线、核心承诺、节奏和卷级钩子。"
        )
    elif stage == "outline":
        user_prompt = (
            "请基于设定生成章节大纲 JSON，对象必须包含 outline 字段。\n"
            f"设定：\n{setting_text or '（未提供设定）'}\n"
            f"章节数：{num_chapters or '未指定'}\n"
            "请输出每章的标题、目的和推进要点。"
        )
    elif stage == "chapter":
        user_prompt = (
            "请生成章节正文 JSON，对象必须包含 chapter 字段。\n"
            f"章号：第{chapter_num}章\n"
            f"章标题：{chapter_title or '未指定'}\n"
            f"大纲：\n{outline_text or '（未提供大纲）'}\n"
            f"相关前文：\n{context_text or '（暂无相关前文）'}\n"
            "请写出可直接继续的章节正文，并保持和前文一致的语气与事实。"
        )
    else:
        user_prompt = (
            "请生成 workflow 辅助 JSON，对象必须包含 chapter 字段或 setting 字段。\n"
            "如果你无法识别阶段，请返回一个包含 error 的 JSON 对象。"
        )
    return system_prompt, user_prompt


def _run_workflow_generation(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root") or "").strip()
    if not root_value:
        raise ValueError("缺少 root。")
    root = _coerce_project_root(root_value)
    stage = str(body.get("stage") or "").strip().lower()
    if stage not in {"setting", "outline", "chapter"}:
        raise ValueError("未知 workflow 阶段。")

    workbench_profile = _load_workbench_text_provider_profile()
    api_key = resolve_text_api_key(str(body.get("apiKey") or ""))
    credential_source = "request" if str(body.get("apiKey") or "").strip() else ""
    if not api_key and workbench_profile.get("apiKey"):
        api_key = workbench_profile["apiKey"]
        credential_source = "workbench"
    base_url_source = "request" if str(body.get("baseUrl") or "").strip() else ""
    configured_base_url = str(body.get("baseUrl") or "").strip()
    if not configured_base_url and workbench_profile.get("baseUrl"):
        configured_base_url = workbench_profile["baseUrl"]
        base_url_source = "workbench"
    base_url = resolve_text_base_url(str(body.get("baseUrl") or ""), configured_base_url)
    model = str(body.get("model") or body.get("responseModel") or "gpt-5.4-mini").strip() or "gpt-5.4-mini"
    timeout_seconds = int(body.get("timeoutSeconds") or 300)
    client = OpenAITextHTTPClient(
        api_key=api_key or "dry-run",
        base_url=base_url,
        timeout_seconds=timeout_seconds,
    )
    related_context = _build_related_context(root, str(body.get("chapterId") or ""), n=int(body.get("contextCount") or 3)) if stage == "chapter" else []
    system_prompt, user_prompt = _build_workflow_generation_prompt(stage, body, related_context=related_context)
    provider_request = client.build_response_request(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=body.get("temperature"),
    )
    if body.get("dryRun"):
        return {
            "saved": False,
            "dryRun": True,
            "stage": stage,
            "model": model,
            "providerCredential": {
                "source": credential_source or "env",
                "available": bool(api_key),
                "workbenchProviderLabel": workbench_profile.get("label", ""),
            },
            "providerBaseUrl": {
                "source": base_url_source or "default",
                "workbenchProviderLabel": workbench_profile.get("label", "") if base_url_source == "workbench" else "",
            },
            "providerRequest": provider_request,
        }

    if not api_key:
        raise ValueError("缺少文本 provider API key。请在本地工作台配置中启用 provider，或通过请求体传入 apiKey。")

    if stage == "chapter" and not str(body.get("chapterId") or "").strip():
        raise ValueError("生成章节时缺少 chapterId。")

    provider_result = client.generate_text(provider_request)
    raw_payload = parse_text_provider_json_object(provider_result.get("text", ""))
    response: dict[str, Any] = {
        "saved": False,
        "dryRun": False,
        "stage": stage,
        "model": model,
        "provider": provider_result.get("provider", "openai-text-http"),
        "responseId": provider_result.get("responseId", ""),
        "providerCredentialSource": credential_source or "env",
        "providerBaseUrlSource": base_url_source or "default",
        "providerRequest": provider_request,
        "raw": raw_payload,
    }

    if stage == "setting":
        setting_text = str(raw_payload.get("setting") or raw_payload.get("text") or provider_result.get("text", "")).strip()
        response["setting"] = setting_text
    elif stage == "outline":
        outline_text = str(raw_payload.get("outline") or raw_payload.get("text") or provider_result.get("text", "")).strip()
        response["outline"] = outline_text
    elif stage == "chapter":
        chapter_text = str(raw_payload.get("chapter") or raw_payload.get("text") or provider_result.get("text", "")).strip()
        response["chapter"] = chapter_text
        response["contextUsed"] = related_context
    return response


def _finalize_workflow_chapter(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root") or "").strip()
    if not root_value:
        raise ValueError("缺少 root。")
    root = _coerce_project_root(root_value)
    chapter_num = int(body.get("chapterNum") or 1)
    chapter_id = f"chapter-{chapter_num:03d}"
    chapter_text = str(body.get("chapterText") or body.get("chapter") or "").strip()
    if not chapter_text:
        raise ValueError("缺少 chapterText。")
    chapter_file = chapter_path(root, chapter_id)
    chapter_file.parent.mkdir(parents=True, exist_ok=True)
    chapter_file.write_text(chapter_text + ("\n" if not chapter_text.endswith("\n") else ""), encoding="utf-8")
    _upsert_context_index(root, chapter_id, chapter_text)
    return {
        "saved": True,
        "stage": "finalize",
        "chapterId": chapter_id,
        "chapterFile": str(chapter_file.resolve()),
        "indexed": True,
    }


def _coerce_text_fragments(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                result.append(normalized)
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    normalized = item.strip()
                    if normalized:
                        result.append(normalized)
    return result


def _entity_appearance_summary(entity: dict[str, Any]) -> str:
    profile = entity.get("profile", {}) if isinstance(entity.get("profile"), dict) else {}
    seed = entity.get("seed", {}) if isinstance(entity.get("seed"), dict) else {}
    current_state = entity.get("currentState")
    current_physical = ""
    if isinstance(current_state, dict):
        current_physical = str(current_state.get("physicalState") or current_state.get("physical") or "").strip()
    fragments = _coerce_text_fragments(
        entity.get("appearance"),
        profile.get("appearance"),
        profile.get("visual"),
        profile.get("look"),
        seed.get("appearance"),
        seed.get("visual"),
        current_physical,
    )
    if not fragments:
        fragments = _coerce_text_fragments(entity.get("summary"), profile.get("summary"))

    compact: list[str] = []
    seen: set[str] = set()
    for item in fragments:
        if item in seen:
            continue
        seen.add(item)
        compact.append(item)
        if len(compact) >= 3:
            break
    return "；".join(compact)


def _compact_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "；".join(_compact_value(item) for item in value if _compact_value(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).strip()


def _first_text(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _compact_value(source.get(key))
        if value:
            return value
    return ""


def _build_worldbook_cards(state: dict[str, Any]) -> dict[str, Any]:
    worldbook = state.get("worldbook", {}) if isinstance(state.get("worldbook"), dict) else {}
    groups = [
        ("premiseFacts", "premise-fact", "前提"),
        ("worldRules", "world-rule", "规则"),
        ("powerProgressions", "progression", "进阶"),
        ("factions", "faction", "势力"),
        ("locations", "location", "地点"),
        ("artifacts", "artifact", "物件"),
        ("mysteries", "mystery", "谜团"),
    ]
    entries: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for state_key, item_type, label in groups:
        values = worldbook.get(state_key, [])
        if not isinstance(values, list):
            values = []
        counts[state_key] = len(values)
        for index, item in enumerate(values, start=1):
            payload = item if isinstance(item, dict) else {"name": _compact_value(item)}
            name = _first_text(payload, "name", "title", "label", "id") or f"{label} {index}"
            summary = _first_text(payload, "summary", "description", "rule", "premise", "currentStage", "condition")
            detail = _first_text(payload, "detail", "notes", "status", "source", "nextStage")
            entries.append(
                {
                    "id": str(payload.get("id") or f"{item_type}-{index}"),
                    "type": item_type,
                    "label": label,
                    "name": name,
                    "summary": summary,
                    "detail": detail,
                    "sourceKey": state_key,
                }
            )
    return {
        "entries": entries,
        "stats": counts,
    }


def _read_text_preview(path: Path, limit: int = 1200) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with path.open("r", encoding="utf-8") as handle:
        return handle.read(limit).strip()


def _review_packet_summary(root: Path, volume_id: str) -> dict[str, Any]:
    path = root / "reviews" / f"{volume_id}-review-packet.md"
    exists = path.exists()
    return {
        "id": f"review-packet::{volume_id}",
        "volumeId": volume_id,
        "title": f"{volume_id} 审查包",
        "filePath": str(path.relative_to(root)) if exists else str(Path("reviews") / f"{volume_id}-review-packet.md"),
        "exists": exists,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(path.stat().st_mtime)) if exists else "",
        "preview": _read_text_preview(path) if exists else "",
    }


def _build_volume_cards(root: Path, state: dict[str, Any]) -> list[dict[str, Any]]:
    volumes = state.get("outline", {}).get("volumes", [])
    if not isinstance(volumes, list):
        return []
    result: list[dict[str, Any]] = []
    for index, volume in enumerate(volumes, start=1):
        if not isinstance(volume, dict):
            continue
        volume_id = str(volume.get("id") or f"volume-{index:03d}")
        chapters = [
            {
                "id": str(chapter.get("id", "")),
                "title": str(chapter.get("title") or chapter.get("id") or ""),
                "status": str(chapter.get("status") or ""),
                "summary": str(chapter.get("direction") or chapter.get("summary") or ""),
            }
            for chapter in volume.get("chapters", [])
            if isinstance(chapter, dict) and chapter.get("id")
        ]
        result.append(
            {
                "id": volume_id,
                "title": str(volume.get("title") or volume_id),
                "theme": str(volume.get("theme") or volume.get("summary") or ""),
                "chapterCount": len(chapters),
                "chapters": chapters,
                "reviewPacket": _review_packet_summary(root, volume_id),
            }
        )
    return result


def _build_chapter_cards(root: Path, state: dict[str, Any]) -> list[dict[str, Any]]:
    review_map = _chapter_review_lookup(state)
    result: list[dict[str, Any]] = []
    for chapter in _flatten_chapters(state.get("outline", {})):
        chapter_id = str(chapter.get("id", ""))
        if not chapter_id:
            continue
        review = review_map.get(chapter_id, {})
        chapter_text = _chapter_content(root, chapter_id)
        review_score = int(review.get("scores", {}).get("total", 0) or 0)
        priority_actions = review.get("priorityActions", []) or []
        result.append(
            {
                "id": chapter_id,
                "title": chapter.get("title", chapter_id),
                "status": review.get("rating") or ("已写作" if chapter_text else "未开始"),
                "summary": _chapter_preview(root, chapter_id),
                "reviewSummary": str(review.get("summary") or ""),
                "content": chapter_text,
                "reviewScore": review_score,
                "updatedAt": review.get("generatedAt") or "",
                "issues": priority_actions[:3],
                "wordCount": count_words(chapter_text) if chapter_text else 0,
            }
        )
    return result


def _build_project_summary(root: Path) -> dict[str, Any]:
    state = load_project_state(root)
    chapters = _build_chapter_cards(root, state)
    illustrations_state = state.get("illustrations", {})
    adapter = illustrations_state.get("adapter", {})
    prompt_system = illustrations_state.get("promptSystem", {})
    illustrations = [
        decorate_generated_entry(root, state, entry)
        for entry in illustrations_state.get("generated", [])
    ]
    entities = [
        {
            "id": entity.get("id", ""),
            "name": entity.get("name", ""),
            "type": entity.get("type", ""),
            "summary": entity.get("summary", "") or _first_text(
                entity.get("profile", {}) if isinstance(entity.get("profile"), dict) else {},
                "summary",
                "role",
            ),
            "aliases": entity.get("aliases", []) if isinstance(entity.get("aliases"), list) else [],
            "seed": entity.get("seed", {}) if isinstance(entity.get("seed"), dict) else {},
            "profile": entity.get("profile", {}) if isinstance(entity.get("profile"), dict) else {},
            "currentState": entity.get("currentState", ""),
            "appearanceSummary": _entity_appearance_summary(entity),
        }
        for entity in state.get("entities", {}).get("entities", [])
        if entity.get("id")
    ]
    workflow = state.get("workflow_progress", {})
    project = state.get("project", {})
    volumes = _build_volume_cards(root, state)
    return {
        "project": {
            "key": _project_key(root),
            "root": str(root),
            "title": project.get("title", root.name),
            "genre": project.get("genre", ""),
            "activeChapterId": project.get("activeChapterId"),
            "positioning": project.get("positioning", {}),
            "storyContract": project.get("storyContract", {}),
            "commercialPositioning": project.get("commercialPositioning", {}),
        },
        "workflow": {
            "currentStage": workflow.get("currentStage", ""),
            "workflowStatus": workflow.get("workflowStatus", ""),
            "updatedAt": workflow.get("updatedAt", ""),
        },
        "illustrationConfig": {
            "adapterName": adapter.get("name", "openai"),
            "responseModel": adapter.get("responseModel", "gpt-5.4"),
            "imageModel": adapter.get("model", "gpt-image-2"),
            "defaultSize": adapter.get("defaultSize", "1024x1024"),
            "quality": adapter.get("quality", "auto"),
            "baseUrl": adapter.get("baseUrl", ""),
            "promptPackName": illustrations_state.get("promptPack", {}).get("name", "default"),
            "promptPackVersion": illustrations_state.get("promptPack", {}).get("version", "builtin"),
            "promptPackDir": str(root / "prompts" / "illustration-packs"),
            "commercialMode": prompt_system.get("commercialMode", "personal"),
            "defaultTemplateByUseCase": prompt_system.get("defaultTemplateByUseCase", {}),
            "defaultModifierRefs": prompt_system.get("defaultModifierRefs", []),
            "availablePromptPacks": [
                summarize_prompt_pack(pack)
                for pack in load_available_prompt_packs(root)
            ],
        },
        "chapters": chapters,
        "illustrations": illustrations,
        "entities": entities,
        "worldbook": _build_worldbook_cards(state),
        "volumes": volumes,
        "reviewPackets": [volume["reviewPacket"] for volume in volumes if volume.get("reviewPacket")],
        "stats": {
            "chapterCount": len(chapters),
            "reviewedChapterCount": sum(1 for item in chapters if item.get("reviewScore", 0) > 0),
            "illustrationCount": len(illustrations),
            "entityCount": len(entities),
        },
    }


def _build_project_option(root: Path, *, source: str) -> dict[str, Any]:
    summary = _build_project_summary(root)
    return {
        "key": summary["project"]["key"],
        "root": summary["project"]["root"],
        "title": summary["project"]["title"],
        "genre": summary["project"]["genre"],
        "activeChapterId": summary["project"]["activeChapterId"],
        "chapterCount": summary["stats"]["chapterCount"],
        "illustrationCount": summary["stats"]["illustrationCount"],
        "source": source,
    }


def _build_project_list_payload() -> dict[str, Any]:
    registry = _load_project_registry()
    scanned_roots = _scan_projects()
    imported_roots = _coerce_registered_roots(registry.get("importedRoots", []))
    recent_roots = _coerce_registered_roots(registry.get("recentRoots", []))
    active_root = ""
    active_root_value = str(registry.get("activeRoot") or "").strip()
    if active_root_value:
        try:
            active_root = str(_coerce_project_root(active_root_value))
        except (Exception, SystemExit):
            active_root = ""

    library_roots: list[Path] = []
    seen_roots: set[str] = set()
    for root in [*scanned_roots, *imported_roots]:
        normalized = str(root.resolve())
        if normalized in seen_roots:
            continue
        seen_roots.add(normalized)
        library_roots.append(root.resolve())

    recent_projects = [_build_project_option(root, source="recent") for root in recent_roots]
    library_projects = [_build_project_option(root, source="library") for root in library_roots]

    return {
        "recentProjects": recent_projects,
        "libraryProjects": library_projects,
        "activeRoot": active_root,
        "registryFile": str(WORKBENCH_PROJECTS_FILE),
    }


ILLUSTRATION_DEFAULTS: dict[str, str] = {
    "defaultModel": "gpt-5.4",
    "defaultSize": "1024x1024",
    "defaultQuality": "high",
    "defaultCommercialMode": "personal",
    "defaultBatchCount": "1",
}


def _default_workbench_settings() -> dict[str, Any]:
    return {
        "illustration": {
            "apiKey": "",
            "baseUrl": "",
            "providers": [],
            **ILLUSTRATION_DEFAULTS,
        }
    }


def _load_workbench_settings() -> dict[str, Any]:
    settings = _default_workbench_settings()
    if not WORKBENCH_SETTINGS_FILE.exists():
        return settings
    try:
        payload = json.loads(WORKBENCH_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return settings
    if isinstance(payload, dict):
        illustration = payload.get("illustration")
        if isinstance(illustration, dict):
            settings["illustration"].update(illustration)
    return settings


def _save_workbench_settings(settings: dict[str, Any]) -> None:
    WORKBENCH_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKBENCH_SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def _mask_api_key(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    if len(normalized) <= 8:
        return "*" * len(normalized)
    return f"{normalized[:3]}***{normalized[-4:]}"


def _provider_fingerprint(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:10]


def _normalize_provider_profiles(settings: dict[str, Any]) -> list[dict[str, Any]]:
    illustration = settings.setdefault("illustration", {})
    providers = illustration.get("providers")
    normalized: list[dict[str, Any]] = []

    if isinstance(providers, list):
        for index, raw in enumerate(providers):
            if not isinstance(raw, dict):
                continue
            provider_id = str(raw.get("id") or f"provider-{index + 1}").strip() or f"provider-{index + 1}"
            label = str(raw.get("label") or "").strip() or f"Provider {index + 1}"
            base_url = str(raw.get("baseUrl") or "").strip()
            api_key = str(raw.get("apiKey") or "").strip()
            try:
                priority = int(raw.get("priority", index + 1))
            except (TypeError, ValueError):
                priority = index + 1
            normalized.append(
                {
                    "id": provider_id,
                    "label": label,
                    "baseUrl": base_url,
                    "apiKey": api_key,
                    "enabled": bool(raw.get("enabled", True)),
                    "priority": priority,
                }
            )

    # Migrate legacy single-provider local settings into the new profile list in memory.
    if not normalized:
        legacy_api_key = str(illustration.get("apiKey", "")).strip()
        legacy_base_url = str(illustration.get("baseUrl", "")).strip()
        if legacy_api_key or legacy_base_url:
            normalized.append(
                {
                    "id": "provider-legacy-default",
                    "label": "默认提供商",
                    "baseUrl": legacy_base_url,
                    "apiKey": legacy_api_key,
                    "enabled": True,
                    "priority": 1,
                }
            )

    normalized.sort(key=lambda item: (item["priority"], item["label"], item["id"]))
    illustration["providers"] = normalized
    return normalized


def _write_provider_profiles(settings: dict[str, Any], raw_profiles: Any) -> None:
    profiles = raw_profiles if isinstance(raw_profiles, list) else []
    existing_by_id = {
        item["id"]: item
        for item in _normalize_provider_profiles(settings)
    }
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(profiles):
        if not isinstance(raw, dict):
            continue
        provider_id = str(raw.get("id") or uuid.uuid4().hex[:12]).strip() or uuid.uuid4().hex[:12]
        previous = existing_by_id.get(provider_id, {})
        label = str(raw.get("label") or "").strip() or previous.get("label") or f"Provider {index + 1}"
        base_url = str(raw.get("baseUrl") or "").strip()
        enabled = bool(raw.get("enabled", True))
        try:
            priority = int(raw.get("priority", index + 1))
        except (TypeError, ValueError):
            priority = index + 1
        clear_api_key = bool(raw.get("clearApiKey"))
        replacement_api_key = str(raw.get("apiKey") or "").strip()
        if clear_api_key:
            api_key = ""
        elif replacement_api_key:
            api_key = replacement_api_key
        else:
            api_key = str(previous.get("apiKey") or "").strip()
        normalized.append(
            {
                "id": provider_id,
                "label": label,
                "baseUrl": base_url,
                "apiKey": api_key,
                "enabled": enabled,
                "priority": priority,
            }
        )

    normalized.sort(key=lambda item: (item["priority"], item["label"], item["id"]))
    illustration = settings.setdefault("illustration", {})
    illustration["providers"] = normalized
    if normalized:
        first_available = next((item for item in normalized if item["enabled"] and item["apiKey"]), normalized[0])
        illustration["apiKey"] = first_available.get("apiKey", "")
        illustration["baseUrl"] = first_available.get("baseUrl", "")
    else:
        illustration["apiKey"] = ""
        illustration["baseUrl"] = ""


def _provider_summaries(settings: dict[str, Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for item in _normalize_provider_profiles(settings):
        summaries.append(
            {
                "id": item["id"],
                "label": item["label"],
                "baseUrl": item["baseUrl"],
                "apiKey": item["apiKey"],
                "enabled": item["enabled"],
                "priority": item["priority"],
                "hasApiKey": bool(item["apiKey"]),
                "maskedKey": _mask_api_key(item["apiKey"]),
                "fingerprint": _provider_fingerprint(item["apiKey"]),
            }
        )
    return summaries


def _runtime_provider_profiles(settings: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in _normalize_provider_profiles(settings)
        if item["enabled"] and item["apiKey"]
    ]


def _apply_provider_profile(body: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    payload = dict(body)
    if not str(payload.get("apiKey") or "").strip():
        payload["apiKey"] = provider.get("apiKey", "")
    if not str(payload.get("baseUrl") or "").strip():
        payload["baseUrl"] = provider.get("baseUrl", "")
    return payload


def _build_settings_response(root: Path | None = None) -> dict[str, Any]:
    settings = _load_workbench_settings()
    illustration = settings.get("illustration", {})
    provider_summaries = _provider_summaries(settings)
    local_profiles = _runtime_provider_profiles(settings)
    env_api_key = resolve_api_key("")
    workspace_root = _ensure_workbench_illustration_sandbox()
    workspace_summary = _build_project_summary(workspace_root)
    workspace_packs = [summarize_prompt_pack(pack) for pack in load_available_prompt_packs(workspace_root)]
    if local_profiles:
        api_key_source = "local"
    elif env_api_key:
        api_key_source = "env"
    else:
        api_key_source = "none"

    project_payload = None
    if root is not None:
        summary = _build_project_summary(root)
        config = summary["illustrationConfig"]
        project_payload = {
            "root": summary["project"]["root"],
            "title": summary["project"]["title"],
            "adapterName": config["adapterName"],
            "responseModel": config["responseModel"],
            "imageModel": config["imageModel"],
            "defaultSize": config["defaultSize"],
            "quality": config["quality"],
            "baseUrl": config["baseUrl"],
            "promptPackName": config["promptPackName"],
            "commercialMode": config["commercialMode"],
        }

    return {
        "local": {
            "apiKeyConfigured": bool(local_profiles) or bool(env_api_key),
            "apiKeySource": api_key_source,
            "configFile": str(WORKBENCH_SETTINGS_FILE),
            "providers": provider_summaries,
            "fallbackCount": max(len(local_profiles) - 1, 0),
            "defaultModel": illustration.get("defaultModel") or ILLUSTRATION_DEFAULTS["defaultModel"],
            "defaultSize": illustration.get("defaultSize") or ILLUSTRATION_DEFAULTS["defaultSize"],
            "defaultQuality": illustration.get("defaultQuality") or ILLUSTRATION_DEFAULTS["defaultQuality"],
            "defaultCommercialMode": illustration.get("defaultCommercialMode") or ILLUSTRATION_DEFAULTS["defaultCommercialMode"],
            "defaultBatchCount": illustration.get("defaultBatchCount") or ILLUSTRATION_DEFAULTS["defaultBatchCount"],
        },
        "workspaceIllustration": {
            "root": str(workspace_root),
            "title": workspace_summary["project"]["title"],
            "adapterName": "openai",
            "responseModel": illustration.get("defaultModel") or ILLUSTRATION_DEFAULTS["defaultModel"],
            "imageModel": "gpt-image-2",
            "defaultSize": illustration.get("defaultSize") or ILLUSTRATION_DEFAULTS["defaultSize"],
            "quality": illustration.get("defaultQuality") or ILLUSTRATION_DEFAULTS["defaultQuality"],
            "baseUrl": str((local_profiles[0].get("baseUrl", "") if local_profiles else "") or ""),
            "promptPackName": "default",
            "promptPackDir": str(workspace_root / "prompts" / "illustration-packs"),
            "commercialMode": illustration.get("defaultCommercialMode") or ILLUSTRATION_DEFAULTS["defaultCommercialMode"],
            "defaultTemplateByUseCase": {},
            "defaultModifierRefs": [],
            "availablePromptPacks": workspace_packs,
            "defaultBatchCount": illustration.get("defaultBatchCount") or ILLUSTRATION_DEFAULTS["defaultBatchCount"],
            "recentIllustrations": workspace_summary["illustrations"],
        },
        "project": project_payload,
        "capabilities": {
            "supportedProviders": ["openai"],
        },
    }


def _save_settings_request(body: dict[str, Any]) -> dict[str, Any]:
    settings = _load_workbench_settings()
    illustration = settings.setdefault("illustration", {})
    if "providers" in body:
        _write_provider_profiles(settings, body.get("providers"))
    elif "apiKey" in body or "localBaseUrl" in body:
        legacy_api_key = str(body.get("apiKey", "")).strip() if "apiKey" in body else ""
        legacy_base_url = str(body.get("localBaseUrl", "")).strip() if "localBaseUrl" in body else ""
        _write_provider_profiles(
            settings,
            [
                {
                    "id": "provider-default",
                    "label": "默认提供商",
                    "baseUrl": legacy_base_url,
                    "apiKey": legacy_api_key,
                    "enabled": True,
                    "priority": 1,
                }
            ]
            if legacy_api_key or legacy_base_url
            else [],
        )

    for key in ("defaultModel", "defaultSize", "defaultQuality", "defaultCommercialMode", "defaultBatchCount"):
        if key in body and str(body[key]).strip():
            illustration[key] = str(body[key]).strip()

    _save_workbench_settings(settings)

    root_value = str(body.get("root", "")).strip()
    root = _coerce_project_root(root_value) if root_value else None
    if root is not None:
        update_illustration_config(
            root,
            set_adapter=str(body.get("adapterName", "")).strip() or None,
            set_model=str(body.get("imageModel", "")).strip() or None,
            set_response_model=str(body.get("responseModel", "")).strip() or None,
            set_size=str(body.get("defaultSize", "")).strip() or None,
            set_quality=str(body.get("quality", "")).strip() or None,
            set_base_url=str(body.get("baseUrl", "")).strip() if "baseUrl" in body else None,
            set_prompt_pack=str(body.get("promptPackName", "")).strip() or None,
            set_commercial_mode=str(body.get("commercialMode", "")).strip() or None,
        )

    return _build_settings_response(root)


def _resolve_prompt_pack_scope(root: Path | None = None) -> tuple[Path, str]:
    if root is not None:
        return root.resolve(), "project"
    return _ensure_workbench_illustration_sandbox(), "workspace"


def _build_prompt_pack_library_response(root: Path | None = None) -> dict[str, Any]:
    library_root, scope = _resolve_prompt_pack_scope(root)
    packs = load_available_prompt_packs(library_root)
    pack_documents = [serialize_prompt_pack_document(pack) for pack in packs]
    return {
        "scope": scope,
        "root": str(library_root),
        "userPromptPackDir": str(library_root / "prompts" / "illustration-packs"),
        "packs": pack_documents,
        "systemPacks": [pack for pack in pack_documents if str(pack.get("source") or "") == "builtin"],
        "userPacks": [pack for pack in pack_documents if str(pack.get("source") or "") != "builtin"],
        "availablePromptPacks": [summarize_prompt_pack(pack) for pack in packs],
    }


def _save_prompt_pack_request(body: dict[str, Any]) -> dict[str, Any]:
    raw_pack = body.get("pack")
    if not isinstance(raw_pack, dict):
        raise SystemExit("prompt pack 请求必须包含 pack 对象")
    root_value = str(body.get("root", "")).strip()
    root = _coerce_project_root(root_value) if root_value else None
    library_root, scope = _resolve_prompt_pack_scope(root)
    try:
        saved_pack = save_prompt_pack_document(
            library_root,
            raw_pack,
            file_name=str(body.get("fileName") or "").strip(),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if scope == "project" and bool(body.get("setAsDefault")):
        saved_summary = summarize_prompt_pack(saved_pack)
        next_pack_name = str(saved_summary.get("name") or saved_pack.get("id") or "").strip()
        if next_pack_name:
            update_illustration_config(library_root, set_prompt_pack=next_pack_name)
    payload = _build_prompt_pack_library_response(root)
    payload["saved"] = True
    payload["savedPack"] = serialize_prompt_pack_document(saved_pack)
    return payload


def _migrate_prompt_packs_request(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root", "")).strip()
    root = _coerce_project_root(root_value) if root_value else None
    library_root, scope = _resolve_prompt_pack_scope(root)
    migration = migrate_project_prompt_pack_documents(library_root, dry_run=bool(body.get("dryRun")))
    payload = _build_prompt_pack_library_response(root)
    payload["migration"] = migration
    payload["scope"] = scope
    return payload


def _export_prompt_pack_request(body: dict[str, Any]) -> dict[str, Any]:
    root_value = str(body.get("root", "")).strip()
    root = _coerce_project_root(root_value) if root_value else None
    library_root, scope = _resolve_prompt_pack_scope(root)
    state = load_project_state(library_root)
    saved_pack = export_prompt_pack_document(
        library_root,
        state.get("illustrations", {}),
        requested_pack_name=str(body.get("promptPackName", "")).strip(),
        file_name=str(body.get("fileName", "")).strip(),
    )
    if scope == "project" and bool(body.get("setAsDefault")):
        saved_summary = summarize_prompt_pack(saved_pack)
        next_pack_name = str(saved_summary.get("name") or saved_pack.get("id") or "").strip()
        if next_pack_name:
            update_illustration_config(library_root, set_prompt_pack=next_pack_name)
    payload = _build_prompt_pack_library_response(root)
    payload["exported"] = True
    payload["exportedPack"] = serialize_prompt_pack_document(saved_pack)
    return payload


def _build_illustration_args(body: dict[str, Any]) -> SimpleNamespace:
    root = _coerce_project_root(str(body.get("root", "")))
    return SimpleNamespace(
        root=str(root),
        chapter_id=body.get("chapterId"),
        entity_id=body.get("entityId"),
        use_case=body.get("useCase") or "",
        text_design_mode=body.get("textDesignMode") or "",
        title_text=body.get("titleText") or "",
        subtitle_text=body.get("subtitleText") or "",
        body_text=body.get("bodyText") or "",
        font_style_hint=body.get("fontStyleHint") or "",
        mode=body.get("mode", "text-to-image"),
        input_image=body.get("inputImages") or [],
        mask=body.get("maskPath") or "",
        prompt_pack=body.get("promptPack") or "",
        template_id=body.get("templateId") or "",
        modifier=body.get("modifierRefs") or [],
        extra_prompt=body.get("extraPrompt") or body.get("promptText") or "",
        negative_prompt=body.get("negativePrompt") or "",
        commercial_mode=body.get("commercialMode") or "",
        size=body.get("size") or "",
        quality=body.get("quality") or "",
        output_name=body.get("outputName") or "",
        response_model=body.get("responseModel") or "",
        base_url=body.get("baseUrl") or "",
        api_key=body.get("apiKey") or "",
        batch_count=body.get("batchCount", 1),
    )


def _ensure_workbench_illustration_sandbox() -> Path:
    root = WORKBENCH_ILLUSTRATION_SANDBOX_ROOT.resolve()
    project_file = resolve_state_path(root, "project", layout=LAYOUT_FLAT)
    if project_file.exists():
        return root

    root.mkdir(parents=True, exist_ok=True)
    for relative in ("chapters", "proposals", "reviews", "projections", "logs", "assets"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    defaults = default_project_state()
    now = now_iso()
    chapter_id = "workspace-scene"
    project = defaults["project"] | {
        "title": "自由生图工作台",
        "genre": "",
        "defaultMode": "driving",
        "activeChapterId": chapter_id,
        "createdAt": now,
        "updatedAt": now,
    }
    outline = {
        "chapters": [
            {
                "id": chapter_id,
                "title": "自由场景",
                "status": "draft",
                "beats": [],
                "scenePlans": [],
            }
        ],
        "chapterDirections": [],
        "volumes": [],
    }
    entities = {
        "entities": [
            {
                "id": "workspace-entity",
                "name": "自由角色",
                "summary": "用于未绑定项目的自由角色生图。",
                "appearance": "按用户提示词决定",
                "currentState": {},
            }
        ]
    }

    dump_json_compatible_yaml(resolve_state_path(root, "project", layout=LAYOUT_FLAT), project)
    dump_json_compatible_yaml(resolve_state_path(root, "outline", layout=LAYOUT_FLAT), outline)
    dump_json_compatible_yaml(resolve_state_path(root, "entities", layout=LAYOUT_FLAT), entities)
    dump_json_compatible_yaml(resolve_state_path(root, "timeline", layout=LAYOUT_FLAT), defaults["timeline"])
    dump_json_compatible_yaml(resolve_state_path(root, "threads", layout=LAYOUT_FLAT), defaults["threads"])
    dump_json_compatible_yaml(resolve_state_path(root, "structures", layout=LAYOUT_FLAT), defaults["structures"])
    dump_json_compatible_yaml(resolve_state_path(root, "worldbook", layout=LAYOUT_FLAT), defaults["worldbook"])
    dump_json_compatible_yaml(resolve_state_path(root, "foreshadowing", layout=LAYOUT_FLAT), defaults["foreshadowing"])
    dump_json_compatible_yaml(root / "branches.yaml", defaults["branches"])
    dump_json_compatible_yaml(resolve_state_path(root, "proposals", layout=LAYOUT_FLAT), defaults["proposals"])
    dump_json_compatible_yaml(resolve_state_path(root, "reviews", layout=LAYOUT_FLAT), defaults["reviews"])
    dump_json_compatible_yaml(resolve_state_path(root, "story_reviews", layout=LAYOUT_FLAT), defaults["story_reviews"])
    dump_json_compatible_yaml(resolve_state_path(root, "projection", layout=LAYOUT_FLAT), defaults["projection"])
    dump_json_compatible_yaml(resolve_state_path(root, "context_lens", layout=LAYOUT_FLAT), {"currentChapterId": chapter_id, "lenses": []})
    dump_json_compatible_yaml(resolve_state_path(root, "projection_log", layout=LAYOUT_FLAT), defaults["projection_log"])
    chapter_path(root, chapter_id).write_text("# 自由场景\n\n用于未绑定项目的自由生图。", encoding="utf-8")
    return root


def _prepare_workspace_illustration_body(body: dict[str, Any]) -> dict[str, Any]:
    root = _ensure_workbench_illustration_sandbox()
    state = load_project_state(root)
    state.setdefault("project", {})["title"] = "自由生图工作台"
    state.setdefault("project", {})["genre"] = ""
    state.setdefault("illustrations", {}).setdefault("adapter", {}).update(
        {
            "name": "openai",
            "model": "gpt-image-2",
            "responseModel": "gpt-5.4",
            "defaultSize": "1024x1024",
            "quality": "high",
        }
    )

    target_type = str(body.get("targetType") or "entity").strip() or "entity"
    manual_target_name = str(body.get("manualTargetName") or "").strip()
    candidate_body = dict(body)
    candidate_body["root"] = str(root)
    candidate_body["targetType"] = target_type
    candidate_body["manualTargetName"] = manual_target_name

    if target_type == "entity":
        state["entities"] = {
            "entities": [
                {
                    "id": "workspace-entity",
                    "name": manual_target_name or "自由角色",
                    "summary": manual_target_name or "自由角色",
                    "appearance": manual_target_name or "按用户提示词决定",
                    "currentState": {},
                }
            ]
        }
        candidate_body["entityId"] = "workspace-entity"
        candidate_body["chapterId"] = None
    else:
        chapter_id = "workspace-scene"
        state["outline"] = {
            "chapters": [
                {
                    "id": chapter_id,
                    "title": manual_target_name or "自由场景",
                    "status": "draft",
                    "beats": [],
                    "scenePlans": [],
                }
            ],
            "chapterDirections": [],
            "volumes": [],
        }
        state.setdefault("project", {})["activeChapterId"] = chapter_id
        chapter_path(root, chapter_id).write_text(
            f"# {manual_target_name or '自由场景'}\n\n{manual_target_name or '按用户提示词决定场景内容。'}",
            encoding="utf-8",
        )
        candidate_body["chapterId"] = chapter_id
        candidate_body["entityId"] = None

    save_state(root, state)
    return candidate_body


def _build_illustration_dry_run(body: dict[str, Any]) -> dict[str, Any]:
    active_body = body if str(body.get("root") or "").strip() else _prepare_workspace_illustration_body(body)
    settings = _load_workbench_settings()
    explicit_api_key = str(active_body.get("apiKey") or "").strip()
    if explicit_api_key:
        payload = build_illustration_dry_run_response(_build_illustration_args(active_body))
        payload["scope"] = "project" if str(body.get("root") or "").strip() else "workspace"
        payload["targetLabel"] = str(active_body.get("manualTargetName") or "") or str(
            (payload.get("payload", {}) if isinstance(payload.get("payload"), dict) else {}).get("targetName", "") or ""
        )
        payload["providerSelection"] = {
            "mode": "explicit",
            "selectedProviderLabel": "request",
        }
        return payload

    runtime_profiles = _runtime_provider_profiles(settings)
    if runtime_profiles:
        selected = runtime_profiles[0]
        candidate_body = _apply_provider_profile(active_body, selected)
        payload = build_illustration_dry_run_response(_build_illustration_args(candidate_body))
        payload["scope"] = "project" if str(body.get("root") or "").strip() else "workspace"
        payload["targetLabel"] = str(active_body.get("manualTargetName") or "") or str(
            (payload.get("payload", {}) if isinstance(payload.get("payload"), dict) else {}).get("targetName", "") or ""
        )
        payload["providerSelection"] = {
            "mode": "local-fallback",
            "selectedProviderLabel": selected["label"],
            "selectedProviderId": selected["id"],
            "attemptOrder": [item["label"] for item in runtime_profiles],
        }
        return payload

    payload = build_illustration_dry_run_response(_build_illustration_args(active_body))
    payload["scope"] = "project" if str(body.get("root") or "").strip() else "workspace"
    payload["targetLabel"] = str(active_body.get("manualTargetName") or "") or str(
        (payload.get("payload", {}) if isinstance(payload.get("payload"), dict) else {}).get("targetName", "") or ""
    )
    payload["providerSelection"] = {
        "mode": "env-or-request",
        "selectedProviderLabel": "environment",
    }
    return payload


def _build_illustration_generate(body: dict[str, Any]) -> dict[str, Any]:
    active_body = body if str(body.get("root") or "").strip() else _prepare_workspace_illustration_body(body)
    settings = _load_workbench_settings()
    explicit_api_key = str(active_body.get("apiKey") or "").strip()
    attempted_providers: list[str] = []
    scope = "project" if str(body.get("root") or "").strip() else "workspace"
    target_label = str(active_body.get("manualTargetName") or "").strip()

    def _materialize(candidate_body: dict[str, Any], provider_label: str, provider_id: str = "") -> dict[str, Any]:
        args = _build_illustration_args(candidate_body)
        result = run_illustration_generation(args)
        root = Path(result["projectRoot"])
        summary = _build_project_summary(root)
        illustration = decorate_generated_entry(root, load_project_state(root), result["illustration"])
        if target_label:
            illustration["targetLabel"] = target_label
        return {
            "saved": True,
            "scope": scope,
            "illustration": illustration,
            "summary": summary if scope == "project" else None,
            "providerSelection": {
                "selectedProviderLabel": provider_label,
                "selectedProviderId": provider_id,
                "attemptOrder": attempted_providers or [provider_label],
            },
        }

    if explicit_api_key:
        attempted_providers.append("request")
        return _materialize(active_body, "request")

    runtime_profiles = _runtime_provider_profiles(settings)
    last_error: Exception | SystemExit | None = None
    for provider in runtime_profiles:
        attempted_providers.append(provider["label"])
        try:
            return _materialize(_apply_provider_profile(active_body, provider), provider["label"], provider["id"])
        except (Exception, SystemExit) as exc:
            last_error = exc
            continue

    if runtime_profiles and last_error is not None:
        raise SystemExit(
            "本地 provider fallback 全部失败: "
            + ", ".join(attempted_providers)
            + f"；最后错误: {last_error}"
        )

    attempted_providers.append("environment")
    return _materialize(active_body, "environment")


class StoryCanvasApiHandler(BaseHTTPRequestHandler):
    server_version = "StoryCanvasAPI/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        _send_cors_headers(self)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            _json_response(self, {"ok": True})
            return
        if parsed.path == "/api/projects":
            _json_response(self, _build_project_list_payload())
            return
        if parsed.path == "/api/project":
            query = parse_qs(parsed.query)
            root_value = (query.get("root") or [""])[0]
            try:
                summary = _build_project_summary(_coerce_project_root(root_value))
            except Exception as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, summary)
            return
        if parsed.path == "/api/settings":
            query = parse_qs(parsed.query)
            root_value = (query.get("root") or [""])[0]
            try:
                root = _coerce_project_root(root_value) if root_value else None
                payload = _build_settings_response(root)
            except Exception as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/context":
            query = parse_qs(parsed.query)
            root_value = (query.get("root") or [""])[0]
            chapter_id = (query.get("chapterId") or [""])[0].strip()
            n_value = (query.get("n") or ["3"])[0]
            try:
                root = _coerce_project_root(root_value)
                payload = {
                    "chapterId": chapter_id,
                    "contexts": _build_related_context(root, chapter_id, n=max(1, int(n_value or 3))),
                }
            except Exception as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/prompt-packs":
            query = parse_qs(parsed.query)
            root_value = (query.get("root") or [""])[0]
            try:
                root = _coerce_project_root(root_value) if root_value else None
                payload = _build_prompt_pack_library_response(root)
            except Exception as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/assets":
            query = parse_qs(parsed.query)
            root_value = (query.get("root") or [""])[0]
            path_value = (query.get("path") or [""])[0]
            try:
                root = _coerce_project_root(root_value)
                target = _resolve_project_asset_path(root, path_value)
            except FileNotFoundError:
                _json_response(self, {"error": "Asset not found"}, HTTPStatus.NOT_FOUND)
                return
            except Exception as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _file_response(self, target)
            return
        if parsed.path == "/api/workbench-assets":
            query = parse_qs(parsed.query)
            path_value = (query.get("path") or [""])[0]
            try:
                target = _resolve_workbench_asset_path(path_value)
            except FileNotFoundError:
                _json_response(self, {"error": "Asset not found"}, HTTPStatus.NOT_FOUND)
                return
            except Exception as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _file_response(self, target)
            return
        _json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/dialogs/select-folder":
            try:
                body = _load_json_request(self)
                payload = _select_folder_dialog(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/projects":
            try:
                body = _load_json_request(self)
                payload = _create_project(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload, HTTPStatus.CREATED)
            return
        if parsed.path == "/api/projects/import":
            try:
                body = _load_json_request(self)
                payload = _import_project(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload, HTTPStatus.CREATED)
            return
        if parsed.path == "/api/projects/recent":
            try:
                body = _load_json_request(self)
                payload = _mark_recent_project(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/projects/active":
            try:
                body = _load_json_request(self)
                payload = _set_active_project(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/illustration/dry-run":
            cleanup_paths: list[Path] = []
            try:
                body, cleanup_paths = _load_illustration_request(self, persist_uploads=False)
                payload = _build_illustration_dry_run(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            finally:
                _cleanup_paths(cleanup_paths)
            _json_response(self, payload)
            return
        if parsed.path == "/api/illustration/generate":
            cleanup_paths: list[Path] = []
            try:
                body, cleanup_paths = _load_illustration_request(self, persist_uploads=True)
                payload = _build_illustration_generate(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            finally:
                _cleanup_paths(cleanup_paths)
            _json_response(self, payload)
            return
        if parsed.path == "/api/system/open-folder":
            try:
                body = _load_json_request(self)
                payload = _open_local_folder_request(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/settings":
            try:
                body = _load_json_request(self)
                payload = _save_settings_request(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/workflow/generate":
            try:
                body = _load_json_request(self)
                payload = _run_workflow_generation(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/workflow/finalize":
            try:
                body = _load_json_request(self)
                payload = _finalize_workflow_chapter(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/prompt-packs":
            try:
                body = _load_json_request(self)
                payload = _save_prompt_pack_request(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/prompt-packs/migrate":
            try:
                body = _load_json_request(self)
                payload = _migrate_prompt_packs_request(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        if parsed.path == "/api/prompt-packs/export":
            try:
                body = _load_json_request(self)
                payload = _export_prompt_pack_request(body)
            except json.JSONDecodeError:
                _json_response(self, {"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
                return
            except (Exception, SystemExit) as exc:
                _json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            _json_response(self, payload)
            return
        _json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        print(format % args)


def main() -> int:
    host = os.environ.get("STORY_CANVAS_API_HOST", "127.0.0.1")
    port = int(os.environ.get("STORY_CANVAS_API_PORT", "43188"))
    server = ThreadingHTTPServer((host, port), StoryCanvasApiHandler)
    print(f"Story Canvas API listening at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
