"""
设定扩展命令 - Setting Expansion Commands
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from ..protocol import ensure_project_root
from ..protocol.io import load_state, save_state
from ..services.analyzer import chapter_title
from ..services.setting_expansion import (
    assess_setting_readiness,
    default_genre_templates,
    get_genre_template,
    get_next_expansion_stage,
    list_available_genres,
    parse_setting_expansion_response,
    suggest_setting_expansions,
    validate_setting_for_writing,
)


def _load_templates() -> Dict[str, Any]:
    return default_genre_templates()


def _load_project_state_from_args(args: argparse.Namespace) -> tuple[Path, Dict[str, Any]]:
    root = Path(args.root).resolve()
    ensure_project_root(root)
    return root, load_state(root)


def command_setting_assess(args: argparse.Namespace):
    """评估设定完备性 - Assess setting completeness"""
    _root, state = _load_project_state_from_args(args)
    templates = _load_templates()

    readiness = assess_setting_readiness(state, templates)

    if args.format == "json":
        print(json.dumps(readiness, ensure_ascii=False, indent=2))
        return 0

    # 文本格式输出
    print(f"设定准备度：{readiness['readinessLabel']} ({readiness['readinessPercent']}%)")
    print(f"评分：{readiness['score']}/{readiness['maxScore']}")

    if readiness["issues"]:
        print("\n⚠️  问题：")
        for issue in readiness["issues"]:
            print(f"  - {issue}")

    if readiness["warnings"]:
        print("\n⚡ 警告：")
        for warning in readiness["warnings"]:
            print(f"  - {warning}")

    if readiness["recommendations"]:
        print("\n💡 建议：")
        for rec in readiness["recommendations"]:
            print(f"  - {rec}")
    return 0


def command_setting_expand(args: argparse.Namespace):
    """扩展设定 - Expand settings"""
    root, state = _load_project_state_from_args(args)
    templates = _load_templates()

    # 自动选择阶段
    if args.auto:
        stage = get_next_expansion_stage(state, templates)
        if stage is None:
            print("✓ 设定已完善，无需进一步扩展")
            return 0
    else:
        stage = args.stage

    # 获取扩展建议
    result = suggest_setting_expansions(
        state=state,
        mode=args.mode,
        focus_area=args.focus,
        current_stage=stage,
        templates=templates,
    )

    if result["status"] == "low_readiness":
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["message"])
            if result.get("recommendations"):
                print("\n建议：")
                for rec in result["recommendations"]:
                    print(f"  - {rec}")
        return 0

    suggestions = []
    if args.input:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = root / input_path
        raw = input_path.read_text(encoding="utf-8")
        suggestions = parse_setting_expansion_response(raw)
        if not suggestions:
            raise SystemExit(f"无法从输入文件解析 suggestions: {input_path}")
    elif args.apply:
        raise SystemExit("setting expand --apply 需要配合 --input <json-file> 使用")

    if suggestions and args.apply:
        _apply_expansion_suggestions(state, suggestions)
        save_state(state, root)
        payload = {
            "status": "applied",
            "appliedCount": len(suggestions),
            "mode": result["mode"],
            "currentStage": result.get("currentStage"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    payload = {
        "status": "prompt-ready",
        "mode": result["mode"],
        "focusArea": result.get("focusArea"),
        "currentStage": result.get("currentStage"),
        "readiness": result.get("readiness"),
        "message": result.get("message"),
        "prompt": result.get("prompt", ""),
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"扩展模式：{payload['mode']}")
    if payload.get("focusArea"):
        print(f"目标领域：{payload['focusArea']}")
    if payload.get("currentStage"):
        print(f"扩展阶段：{payload['currentStage']}")
    print(f"\n{payload['message']}")
    print("\n当前命令只生成可交给文本 provider 的设定扩展 prompt；如需落盘，先把 provider 返回保存为 JSON，再用 --input <json-file> --apply。")
    print("\n--- prompt ---")
    print(payload["prompt"])
    return 0


def _apply_expansion_suggestions(state: Dict[str, Any], suggestions: list) -> None:
    """应用扩展建议到状态"""
    world = state.setdefault("world", {})
    items = world.setdefault("items", [])

    for suggestion in suggestions:
        name = suggestion.get("name", "")
        description = suggestion.get("description", "")

        if not name:
            continue

        # 检查是否已存在
        existing = next((item for item in items if item.get("name") == name), None)
        if existing:
            continue

        # 添加新设定
        items.append({
            "name": name,
            "brief": description,
            "kind": "world_element",  # 可以根据建议调整
            "tags": [],
        })

def command_setting_template(args: argparse.Namespace):
    """查看类型模板 - View genre templates"""
    templates = _load_templates()
    if args.list:
        genres = list_available_genres(templates)
        print("可用类型：")
        for g in genres:
            template = get_genre_template(g, templates)
            if template:
                print(f"  {g}: {template.get('name', g)}")
        return 0

    if not args.genre:
        print("请指定类型或使用 --list 查看所有类型")
        return 0

    template = get_genre_template(args.genre, templates)
    if not template:
        print(f"❌ 未找到类型 '{args.genre}' 的模板")
        return 0

    print(f"# {template.get('name', args.genre)}")
    print()

    # 核心承诺
    core_promises = template.get("core_promises", [])
    if core_promises:
        print("## 核心承诺")
        for promise in core_promises:
            print(f"- {promise}")
        print()

    # 设定要素
    elements = template.get("setting_elements", [])
    if elements:
        print("## 设定要素")
        for elem in elements:
            print(f"- {elem}")
        print()

    # 扩展阶段
    stages = template.get("expansion_stages", [])
    if stages:
        print("## 扩展阶段")

        if args.stage is not None:
            # 显示特定阶段
            stage_data = next((s for s in stages if s.get("stage") == args.stage), None)
            if stage_data:
                _display_stage(stage_data)
            else:
                print(f"❌ 阶段 {args.stage} 不存在")
        else:
            # 显示所有阶段
            for stage_data in stages:
                _display_stage(stage_data)
                print()
    return 0


def _display_stage(stage_data: Dict[str, Any]):
    """显示扩展阶段信息"""
    print(f"### 阶段 {stage_data['stage']}: {stage_data['name']}")
    print(f"重点：{stage_data.get('focus', '')}")

    questions = stage_data.get("questions", [])
    if questions:
        print("\n指导问题：")
        for q in questions:
            print(f"  - {q}")

    examples = stage_data.get("examples", [])
    if examples:
        print("\n参考示例：")
        for ex in examples:
            print(f"  - {ex}")


def command_setting_validate(args: argparse.Namespace):
    """验证设定是否支持写作 - Validate setting for writing"""
    _root, state = _load_project_state_from_args(args)

    if not args.chapter_id:
        # 如果没有指定章节，检查所有章节
        outline = state.get("outline", {})
        all_issues = []

        for volume in outline.get("volumes", []):
            for chapter in volume.get("chapters", []):
                chapter_id = chapter.get("id", "")
                result = validate_setting_for_writing(state, chapter_id)

                if not result["valid"] or result.get("warnings"):
                    all_issues.append({
                        "chapterId": chapter_id,
                        "chapterTitle": chapter_title(outline, chapter_id),
                        "result": result,
                    })

        if not all_issues:
            print("✓ 所有章节的设定验证通过")
            return 0

        print(f"发现 {len(all_issues)} 个章节存在问题：\n")

        for issue in all_issues:
            print(f"章节：{issue['chapterTitle']} ({issue['chapterId']})")

            if not issue["result"]["valid"]:
                for err in issue["result"]["issues"]:
                    print(f"  ❌ {err}")

            for warning in issue["result"].get("warnings", []):
                print(f"  ⚠️  {warning}")

            print()
        return 0
    else:
        # 验证特定章节
        result = validate_setting_for_writing(state, args.chapter_id)

        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if result["valid"]:
            print("✓ 设定验证通过")
        else:
            print("❌ 设定验证失败")

        if result.get("issues"):
            print("\n问题：")
            for issue in result["issues"]:
                print(f"  - {issue}")

        if result.get("warnings"):
            print("\n警告：")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        return 0


def register_setting_commands(subparsers) -> None:
    """注册设定扩展命令"""
    # setting 命令组
    setting_parser = subparsers.add_parser("setting", help="设定扩展命令")
    setting_subparsers = setting_parser.add_subparsers(dest="setting_command", required=True)

    # setting assess
    assess_parser = setting_subparsers.add_parser("assess", help="评估设定完备性")
    assess_parser.add_argument("--root", required=True, help="项目根目录")
    assess_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    assess_parser.set_defaults(func=command_setting_assess)

    # setting expand
    expand_parser = setting_subparsers.add_parser("expand", help="扩展设定")
    expand_parser.add_argument("--root", required=True, help="项目根目录")
    expand_parser.add_argument(
        "--mode",
        choices=["progressive", "targeted", "brainstorm"],
        default="progressive",
        help="扩展模式",
    )
    expand_parser.add_argument("--focus", type=str, help="目标扩展领域（用于targeted模式）")
    expand_parser.add_argument("--stage", type=int, help="指定扩展阶段（用于progressive模式）")
    expand_parser.add_argument("--auto", action="store_true", help="自动选择阶段")
    expand_parser.add_argument("--apply", action="store_true", help="自动应用建议")
    expand_parser.add_argument("--input", type=str, help="包含 suggestions 的 provider JSON 输出")
    expand_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    expand_parser.set_defaults(func=command_setting_expand)

    # setting template
    template_parser = setting_subparsers.add_parser("template", help="查看类型模板")
    template_parser.add_argument("genre", type=str, nargs="?", help="类型名称")
    template_parser.add_argument("--list", action="store_true", help="列出所有可用类型")
    template_parser.add_argument("--stage", type=int, help="显示特定阶段")
    template_parser.set_defaults(func=command_setting_template)

    # setting validate
    validate_parser = setting_subparsers.add_parser("validate", help="验证设定是否支持写作")
    validate_parser.add_argument("--root", required=True, help="项目根目录")
    validate_parser.add_argument("chapter_id", type=str, nargs="?", help="章节ID")
    validate_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    validate_parser.set_defaults(func=command_setting_validate)

    # setting check (别名)
    check_parser = setting_subparsers.add_parser("check", help="检查设定完备性（别名）")
    check_parser.add_argument("--root", required=True, help="项目根目录")
    check_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    check_parser.set_defaults(func=command_setting_assess)
