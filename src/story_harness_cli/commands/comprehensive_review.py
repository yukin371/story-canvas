"""
综合审查命令 - Comprehensive Review Commands
审查AI作为严格编辑，全面检查小说质量
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from ..services.comprehensive_review import comprehensive_review
from ..protocol.io import load_state
from ..protocol.files import chapter_path


def command_review_comprehensive(args: argparse.Namespace) -> int:
    """综合审查命令"""
    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_state(root)

    chapter_id = args.chapter_id or state.get("project", {}).get("activeChapterId")
    if not chapter_id:
        print("错误：缺少 chapter id")
        return 1

    # 读取章节文本
    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        print(f"错误：章节文件不存在: {chapter_file}")
        return 1

    chapter_text = chapter_file.read_text(encoding="utf-8")

    # 确定审查范围
    focus_areas = []
    if args.focus:
        focus_areas = [args.focus]
    elif args.all_areas:
        focus_areas = ["entities", "logic", "satisfaction", "structure"]
    else:
        # 默认审查所有区域
        focus_areas = ["entities", "logic", "satisfaction", "structure"]

    # 执行综合审查
    review_result = comprehensive_review(
        state=state,
        chapter_id=chapter_id,
        chapter_text=chapter_text,
        focus_areas=focus_areas,
        strictness=args.strictness or "standard"
    )

    # 输出结果
    if args.format == "json":
        print(json.dumps(review_result, ensure_ascii=False, indent=2))
    else:
        _print_comprehensive_review(review_result)

    return 0


def _print_comprehensive_review(result: Dict[str, Any]) -> None:
    """打印综合审查结果"""
    print(f"=== 综合审查报告 ===")
    print(f"\n章节: {result['chapterId']}")
    print(f"审查时间: {result['generatedAt']}")
    print(f"严格度: {result['strictness']}")
    print(f"审查范围: {', '.join(result['focusAreas'])}")

    # 总体评估
    overall = result.get("overallAssessment", {})
    print(f"\n=== 总体评估 ===")
    print(f"总分: {overall.get('totalScore', 0)}/15")
    print(f"可继续下一章: {'是' if overall.get('readyForNext') else '否'}")

    if overall.get("criticalIssues", 0) > 0:
        print(f"⚠️  严重问题: {overall['criticalIssues']} 个")
    if overall.get("majorIssues", 0) > 0:
        print(f"⚠️  重要问题: {overall['majorIssues']} 个")

    # 分项评分
    area_scores = overall.get("areaScores", [])
    if area_scores:
        print(f"\n=== 分项评分 ===")
        for area in area_scores:
            print(f"  {area['area']}: {area['score']}/15")
            if area.get("issue"):
                print(f"    {area['issue']}")

    # 实体审查
    if "entityReview" in result:
        _print_entity_review(result["entityReview"])

    # 逻辑一致性
    if "logicalConsistency" in result:
        _print_logic_review(result["logicalConsistency"])

    # 爽点分析
    if "satisfactionAnalysis" in result:
        _print_satisfaction_review(result["satisfactionAnalysis"])

    # 结构分析
    if "structureAnalysis" in result:
        _print_structure_review(result["structureAnalysis"])

    # 优先级建议
    priorities = overall.get("priorities", [])
    if priorities:
        print(f"\n=== 改进建议 ===")
        for priority in priorities:
            print(priority)

    # 总体摘要
    print(f"\n{overall.get('summary', '')}")


def _print_entity_review(entity_review: Dict) -> None:
    """打印实体审查结果"""
    print(f"\n=== 实体审查 ===")

    known_compliance = entity_review.get("knownEntityCompliance", {})
    if known_compliance:
        print(f"已知实体: {known_compliance.get('totalEntities', 0)} 个")
        print(f"已包裹: {known_compliance.get('wrappedEntities', 0)} 个")

    unknown_discovery = entity_review.get("unknownEntityDiscovery", {})
    if unknown_discovery:
        discovered_count = unknown_discovery.get("discoveredCount", 0)
        print(f"\n发现未知实体: {discovered_count} 个")

        entities = unknown_discovery.get("entities", [])
        if entities:
            print("\n未知实体详情:")
            for entity in entities[:5]:  # 最多显示5个
                print(f"\n  名称: {entity['name']}")
                print(f"  预测类型: {entity['predictedType']}")
                print(f"  出现次数: {entity['occurrenceCount']}")
                print(f"  优先级: {entity['priority']}")
                print(f"  建议: {entity['suggestedAction']}")
                if entity.get("context"):
                    print(f"  上下文: {entity['context'][:80]}...")

                required_fields = entity.get("requiredFields", [])
                if required_fields:
                    print(f"  必需字段: {', '.join(required_fields)}")


def _print_logic_review(logic_review: Dict) -> None:
    """打印逻辑审查结果"""
    print(f"\n=== 逻辑一致性审查 ===")

    print(f"评分: {logic_review.get('overallScore', 0)}/15")
    print(f"问题: {logic_review.get('errorCount', 0)} 个错误, {logic_review.get('warningCount', 0)} 个警告")

    issues = logic_review.get("issues", [])
    if issues:
        print("\n发现的问题:")
        for i, issue in enumerate(issues[:5], 1):
            severity_icon = {
                "major": "❌",
                "moderate": "⚠️ ",
                "minor": "ℹ️ "
            }.get(issue.get("severity", "minor"), "•")

            print(f"\n{i}. {severity_icon} {issue.get('type', '')}")
            print(f"   {issue.get('description', '')}")
            if issue.get("suggestion"):
                print(f"   建议: {issue['suggestion']}")

    print(f"\n{logic_review.get('summary', '')}")


def _print_satisfaction_review(satisfaction_review: Dict) -> None:
    """打印爽点审查结果"""
    print(f"\n=== 爽点分析 ===")

    print(f"评分: {satisfaction_review.get('overallScore', 0)}/15")
    print(f"爽点数量: {satisfaction_review.get('pointCount', 0)} 个")
    print(f"密度: {satisfaction_review.get('density', '')}")

    distribution = satisfaction_review.get("distribution", {})
    if distribution:
        print("\n爽点分布:")
        for point_type, count in distribution.items():
            print(f"  {point_type}: {count} 个")

    contract_alignment = satisfaction_review.get("contractAlignment", {})
    if contract_alignment:
        print(f"\n商业契约履行: {'✓' if contract_alignment.get('fulfilled') else '✗'}")
        if contract_alignment.get("hookQuality"):
            print(f"结尾钩子质量: {contract_alignment['hookQuality']}")

    suggestions = satisfaction_review.get("suggestions", [])
    if suggestions:
        print("\n改进建议:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")

    print(f"\n{satisfaction_review.get('summary', '')}")


def _print_structure_review(structure_review: Dict) -> None:
    """打印结构审查结果"""
    print(f"\n=== 结构分析 ===")

    print(f"评分: {structure_review.get('overallScore', 0)}/15")

    # 3幕结构
    three_act = structure_review.get("threeActStructure", {})
    if three_act and not three_act.get("error"):
        print("\n3幕结构:")
        print(f"  第一幕（铺垫）: {three_act.get('act1', {}).get('chapterRange', 'N/A')}")
        print(f"  第二幕（冲突）: {three_act.get('act2', {}).get('chapterRange', 'N/A')}")
        print(f"  第三幕（结局）: {three_act.get('act3', {}).get('chapterRange', 'N/A')}")

    # 卷级闭环
    closure = structure_review.get("volumeClosure", {})
    if closure:
        print(f"\n卷级闭环: {'✓ 可以结束' if closure.get('canClose') else '✗ 不建议结束'}")

    # 剧情节奏
    rhythm = structure_review.get("plotRhythm", {})
    if rhythm:
        print(f"\n剧情节奏: {rhythm.get('rhythm', '')}")
        if rhythm.get("avgParagraphLength"):
            print(f"  平均段落长度: {rhythm['avgParagraphLength']:.0f} 字")

    issues = structure_review.get("issues", [])
    if issues:
        print("\n结构问题:")
        for issue in issues[:3]:
            print(f"  • {issue.get('description', '')}")

    print(f"\n{structure_review.get('summary', '')}")


def ensure_project_root(root: Path) -> None:
    """确保在项目根目录"""
    from ..protocol.files import ensure_project_root
    ensure_project_root(root)


def register_comprehensive_review_commands(subparsers) -> None:
    """注册综合审查命令"""
    # review comprehensive 命令
    comprehensive_parser = subparsers.add_parser(
        "review-comprehensive",
        help="综合审查（审查AI全面检查）"
    )
    comprehensive_parser.add_argument("--root", required=True, help="项目根目录")
    comprehensive_parser.add_argument("--chapter-id", type=str, help="章节ID")
    comprehensive_parser.add_argument(
        "--focus",
        choices=["entities", "logic", "satisfaction", "structure"],
        help="审查特定区域"
    )
    comprehensive_parser.add_argument("--all-areas", action="store_true", help="审查所有区域")
    comprehensive_parser.add_argument(
        "--strictness",
        choices=["minimal", "standard", "commercial"],
        default="standard",
        help="严格程度"
    )
    comprehensive_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    comprehensive_parser.set_defaults(func=command_review_comprehensive)
