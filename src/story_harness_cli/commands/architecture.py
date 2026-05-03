"""
架构审查命令 - Architecture Review Commands
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from ..services.architecture_review import review_architecture
from ..services.setting_review import review_setting
from ..services.outline_review import review_outline
from ..protocol.io import load_state


def command_architecture_review(args: argparse.Namespace) -> int:
    """架构审查命令"""
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_state(root)

    result = review_architecture(
        state,
        scope=args.scope or "full"
    )

    # 输出结果
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_architecture_review(result)

    return 0


def _print_architecture_review(result: Dict[str, Any]) -> None:
    """打印架构审查结果"""
    print(f"=== 架构审查报告 ===")
    print(f"\n风险等级: {result['riskLabel']}")
    print(f"审查范围: {result['scope']}")
    print(f"\n{result['summary']}")

    issues = result.get("issues", [])
    risks = result.get("risks", [])

    if issues:
        print(f"\n=== 发现的问题 ({len(issues)}) ===")
        for i, issue in enumerate(issues, 1):
            level_icon = {
                "error": "❌",
                "warning": "⚠️ ",
                "info": "ℹ️ "
            }.get(issue.get("level", "info"), "•")

            print(f"\n{i}. {level_icon} {issue['message']}")
            print(f"   类别: {issue.get('category', 'unknown')}")

            if issue.get("details"):
                print(f"   详情: {issue['details']}")

            if issue.get("suggestion"):
                print(f"   建议: {issue['suggestion']}")

    if risks:
        print(f"\n=== 风险提示 ({len(risks)}) ===")
        for i, risk in enumerate(risks, 1):
            level_icon = {
                "warning": "⚠️ ",
                "info": "ℹ️ "
            }.get(risk.get("level", "info"), "•")

            print(f"\n{i}. {level_icon} {risk['message']}")

            if risk.get("suggestion"):
                print(f"   建议: {risk['suggestion']}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\n=== 改进建议 ===")
        for rec in recommendations:
            print(f"• {rec}")

    print(f"\n可以开始写作: {'是' if result.get('readyToWrite') else '否'}")


def command_review_setting(args: argparse.Namespace) -> int:
    """设定级审查命令"""
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_state(root)

    result = review_setting(
        state,
        strictness=args.strictness or "standard"
    )

    # 输出结果
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_setting_review(result)

    return 0


def _print_setting_review(result: Dict[str, Any]) -> None:
    """打印设定审查结果"""
    print(f"=== 设定审查报告 ===")
    print(f"\n总分: {result['overallScore']:.1f}/15")
    print(f"严格度: {result['strictness']}")
    print(f"\n{result['summary']}")

    scores = result.get("scores", {})
    if scores:
        print(f"\n=== 分项评分 ===")
        for key, score in scores.items():
            print(f"• {key}: {score.get('score', 0):.1f}/15")

    issues = result.get("issues", [])
    if issues:
        print(f"\n=== 发现的问题 ({len(issues)}) ===")
        for i, issue in enumerate(issues, 1):
            level_icon = {
                "error": "❌",
                "warning": "⚠️ ",
                "info": "ℹ️ "
            }.get(issue.get("level", "info"), "•")

            print(f"\n{i}. {level_icon} {issue['message']}")
            print(f"   类别: {issue.get('category', 'unknown')}")

            if issue.get("suggestion"):
                print(f"   建议: {issue['suggestion']}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\n=== 改进建议 ===")
        for rec in recommendations:
            print(f"• {rec}")

    print(f"\n设定完备: {'是' if result.get('ready') else '否'}")


def command_review_outline(args: argparse.Namespace) -> int:
    """大纲级审查命令"""
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_state(root)

    result = review_outline(
        state,
        check_consistency=args.check_consistency,
        check_foreshadowing=args.check_foreshadowing
    )

    # 输出结果
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_outline_review(result)

    return 0


def _print_outline_review(result: Dict[str, Any]) -> None:
    """打印大纲审查结果"""
    print(f"=== 大纲审查报告 ===")
    print(f"\n总分: {result['overallScore']:.1f}/15")
    print(f"\n{result['summary']}")

    scores = result.get("scores", {})
    if scores:
        print(f"\n=== 分项评分 ===")
        for key, score in scores.items():
            print(f"• {key}: {score.get('score', 0):.1f}/15")

    issues = result.get("issues", [])
    if issues:
        print(f"\n=== 发现的问题 ({len(issues)}) ===")
        for i, issue in enumerate(issues, 1):
            level_icon = {
                "error": "❌",
                "warning": "⚠️ ",
                "info": "ℹ️ "
            }.get(issue.get("level", "info"), "•")

            print(f"\n{i}. {level_icon} {issue['message']}")
            print(f"   类别: {issue.get('category', 'unknown')}")

            if issue.get("suggestion"):
                print(f"   建议: {issue['suggestion']}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\n=== 改进建议 ===")
        for rec in recommendations:
            print(f"• {rec}")

    print(f"\n大纲完备: {'是' if result.get('ready') else '否'}")


def ensure_project_root(root: Path) -> None:
    """确保在项目根目录"""
    from ..protocol.files import ensure_project_root
    ensure_project_root(root)


def register_architecture_commands(subparsers) -> None:
    """注册架构审查命令"""
    # architecture review 命令
    arch_parser = subparsers.add_parser("architecture", help="架构审查命令")
    arch_subparsers = arch_parser.add_subparsers(dest="architecture_command", required=True)

    # architecture review
    review_parser = arch_subparsers.add_parser("review", help="架构级审查")
    review_parser.add_argument("--root", required=True, help="项目根目录")
    review_parser.add_argument(
        "--scope",
        choices=["setting", "outline", "characters", "plot", "full"],
        default="full",
        help="审查范围"
    )
    review_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    review_parser.set_defaults(func=command_architecture_review)


def register_review_setting_command(subparsers) -> None:
    """注册设定审查命令"""
    setting_parser = subparsers.add_parser("review-setting", help="设定级审查")
    setting_parser.add_argument("--root", required=True, help="项目根目录")
    setting_parser.add_argument(
        "--strictness",
        choices=["minimal", "standard", "strict"],
        default="standard",
        help="严格程度"
    )
    setting_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    setting_parser.set_defaults(func=command_review_setting)


def register_review_outline_command(subparsers) -> None:
    """注册大纲审查命令"""
    outline_parser = subparsers.add_parser("review-outline", help="大纲级审查")
    outline_parser.add_argument("--root", required=True, help="项目根目录")
    outline_parser.add_argument("--check-consistency", action="store_true", default=True, help="检查设定一致性")
    outline_parser.add_argument("--check-foreshadowing", action="store_true", default=True, help="检查伏笔一致性")
    outline_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    outline_parser.set_defaults(func=command_review_outline)
