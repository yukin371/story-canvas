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

from story_harness_cli.cli import main
from story_harness_cli.protocol.state import STATE_KEY_MAP
from story_harness_cli.protocol.files import resolve_state_path


def _write_json_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_minimal_project(root: Path, *, outline: dict, entities: dict):
    """Write a complete minimal project with given outline and entities."""
    defaults = {
        "project": {"title": "测试书名"},
        "timeline": {"events": []},
        "branches": {"branches": []},
        "proposals": {"draftProposals": []},
        "reviews": {"changeRequests": []},
        "story_reviews": {"chapterReviews": [], "sceneReviews": []},
        "projection": {"snapshotProjections": [], "relationProjections": [],
                       "sceneScopeProjections": [], "timelineProjections": [],
                       "causalityProjections": []},
        "context_lens": {"currentChapterId": None, "lenses": []},
        "projection_log": {"projectionChanges": []},
        "threads": {"threads": []},
        "structures": {"activeStructure": None, "mappings": []},
    }
    overrides = {"outline": outline, "entities": entities}
    for state_key, internal_key in STATE_KEY_MAP.items():
        data = overrides.get(internal_key, defaults.get(internal_key, {}))
        fpath = resolve_state_path(root, state_key)
        _write_json_yaml(fpath, data)

    # Ensure subdirectories exist
    for d in ["chapters", "proposals", "reviews", "projections", "logs"]:
        (root / d).mkdir(exist_ok=True)


class TestExportSpecOutline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh-export-spec-outline-"))
        outline = {
            "chapters": [],
            "chapterDirections": [],
            "volumes": [
                {
                    "id": "volume-001",
                    "title": "雾起",
                    "chapters": [
                        {
                            "id": "chapter-001",
                            "title": "裂痕之夜",
                            "status": "completed",
                            "direction": "建立主角困境与初始悬念",
                            "beats": [
                                {"description": "林舟从噩梦中惊醒"},
                                {"description": "老陈死讯传来"},
                            ],
                            "scenePlans": [
                                {"summary": "凌晨四点，林舟惊醒"},
                                {"summary": "三天后老陈死了"},
                            ],
                        },
                        {
                            "id": "chapter-002",
                            "title": "暗影追踪",
                            "status": "draft",
                            "beats": [],
                            "scenePlans": [],
                        },
                    ],
                },
            ],
        }
        entities = {"entities": [], "enrichmentProposals": []}
        _build_minimal_project(self.temp_dir, outline=outline, entities=entities)
        self.out_file = self.temp_dir / "output.md"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_spec_outline(self):
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "spec-outline",
            "--output", str(self.out_file),
        ])
        self.assertEqual(result, 0)
        content = self.out_file.read_text(encoding="utf-8")

        # Title
        self.assertIn("# 大纲: 测试书名", content)
        # Volume title
        self.assertIn("## 卷: 雾起", content)
        # Chapter title and status
        self.assertIn("### chapter-001: 裂痕之夜 [completed]", content)
        self.assertIn("### chapter-002: 暗影追踪 [draft]", content)
        # Direction
        self.assertIn("**方向:** 建立主角困境与初始悬念", content)
        # Beats
        self.assertIn("- 林舟从噩梦中惊醒", content)
        self.assertIn("- 老陈死讯传来", content)
        # Scenes
        self.assertIn("**场景:**", content)
        self.assertIn("1. 凌晨四点，林舟惊醒", content)
        self.assertIn("2. 三天后老陈死了", content)


class TestExportSpecCharacters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh-export-spec-chars-"))
        outline = {"chapters": [], "chapterDirections": [], "volumes": []}
        entities = {
            "entities": [
                {
                    "id": "entity-lin-zhou",
                    "name": "林舟",
                    "type": "character",
                    "registeredAt": "2026-04-22T10:00:00+08:00",
                    "profile": {
                        "traits": ["敏锐", "固执", "孤独"],
                        "appearance": [
                            {"detail": "中年发福，眉头紧锁"},
                            {"detail": "左肩有旧伤疤"},
                        ],
                        "abilities": [
                            {"detail": "刑侦推理"},
                            {"detail": "格斗擒拿"},
                        ],
                    },
                },
                {
                    "id": "entity-shen-zhao",
                    "name": "沈昭",
                    "type": "character",
                    "registeredAt": "",
                    "profile": {
                        "traits": [],
                        "appearance": [{"detail": "面目模糊"}],
                        "abilities": [{"detail": "情报收集"}],
                    },
                },
            ],
            "enrichmentProposals": [],
        }
        _build_minimal_project(self.temp_dir, outline=outline, entities=entities)
        self.out_file = self.temp_dir / "output.md"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_spec_characters(self):
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "spec-characters",
            "--output", str(self.out_file),
        ])
        self.assertEqual(result, 0)
        content = self.out_file.read_text(encoding="utf-8")

        # Title
        self.assertIn("# 角色卡: 测试书名", content)
        # Entity name and type
        self.assertIn("## 林舟 (character)", content)
        self.assertIn("## 沈昭 (character)", content)
        # First mention for entity with registeredAt
        self.assertIn("> 首次出场: 2026-04-22T10:00:00+08:00", content)
        # Traits
        self.assertIn("**特质:** 敏锐, 固执, 孤独", content)
        # Appearance
        self.assertIn("**外貌:** 中年发福，眉头紧锁, 左肩有旧伤疤", content)
        self.assertIn("**外貌:** 面目模糊", content)
        # Abilities
        self.assertIn("**能力:** 刑侦推理, 格斗擒拿", content)
        self.assertIn("**能力:** 情报收集", content)


class TestExportReviewPacket(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh-export-review-packet-"))
        outline = {
            "chapters": [
                {
                    "id": "chapter-001",
                    "title": "灯尽人未绝",
                    "status": "completed",
                    "direction": "立住死局，并在章末留下残灯代价钩子。",
                    "beats": [
                        {"summary": "主角在废棚等死"},
                        {"summary": "旧炉异动逼出第一次借灯"},
                    ],
                    "scenePlans": [
                        {"title": "废棚", "summary": "展示底层生存处境", "startParagraph": 1, "endParagraph": 2},
                        {"title": "旧炉", "summary": "触发残灯回应", "startParagraph": 3, "endParagraph": 4},
                    ],
                }
            ],
            "chapterDirections": [],
            "volumes": [],
        }
        entities = {"entities": [], "enrichmentProposals": []}
        entities = {
            "entities": [
                {
                    "id": "char-shenzhao",
                    "name": "沈照",
                    "type": "character",
                    "aliases": [],
                    "profile": {},
                    "currentState": {},
                }
            ],
            "enrichmentProposals": [],
        }
        _build_minimal_project(self.temp_dir, outline=outline, entities=entities)
        _write_json_yaml(
            resolve_state_path(self.temp_dir, "worldbook"),
            {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [],
                "factions": [
                    {"id": "faction-qingyun", "name": "青云宗", "summary": "本地中型宗门"}
                ],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
        )

        chapter_path = self.temp_dir / "chapters" / "chapter-001.md"
        chapter_path.write_text(
            "# 灯尽人未绝\n\n沈照在废棚里等死。\n\n@{顾寒山}站在青云宗的人群后。\n\n旧炉忽然异动。\n\n他听见残灯回响。\n\n活下来了，但丢了东西。\n",
            encoding="utf-8",
        )

        story_reviews = {
            "chapterReviews": [
                {
                    "chapterId": "chapter-001",
                    "chapterTitle": "灯尽人未绝",
                    "generatedAt": "2026-04-26T18:00:00+08:00",
                    "summary": "本章死局、代价与钩子已经立住，但章末追读牵引还能再强一点。",
                    "rating": "solid",
                    "scores": {"total": 82},
                    "weightedScores": {"total": 83.2},
                    "strengths": ["场景清晰", "代价感明确"],
                    "priorityActions": ["强化章末追读问题"],
                    "contractAlignment": {"risks": ["残灯真相推进还偏保守"]},
                    "commercialAlignment": {"risks": ["章末钩子还可以更狠"]},
                    "styleAnalysis": {
                        "styleAnalysis": {
                            "summary": "检测到1项AI风格特征：段落均质。扣1分。"
                        }
                    },
                    "ruleJudgements": [
                        {
                            "message": "检测到段落均质问题。",
                            "severity": "medium",
                            "suggestion": "调整长短段交替。"
                        }
                    ],
                }
            ],
            "sceneReviews": [
                {
                    "chapterId": "chapter-001",
                    "generatedAt": "2026-04-26T18:01:00+08:00",
                    "summary": "场景推进明确，但伏笔与回收还能更紧。",
                    "rating": "solid",
                    "scores": {"total": 78},
                    "strengths": ["逻辑顺", "焦点清楚"],
                    "priorityActions": ["补一个更明确的后续兑现点"],
                    "sceneRange": {
                        "sceneIndex": 2,
                        "startParagraph": 3,
                        "endParagraph": 4,
                    },
                    "ruleJudgements": [],
                }
            ],
        }
        _write_json_yaml(resolve_state_path(self.temp_dir, "story_reviews"), story_reviews)
        self.out_file = self.temp_dir / "review-packet.md"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_review_packet(self):
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "review-packet",
            "--chapter-id", "chapter-001",
            "--output", str(self.out_file),
        ])
        self.assertEqual(result, 0)
        content = self.out_file.read_text(encoding="utf-8")

        self.assertIn("# 审查包: 测试书名 / 灯尽人未绝", content)
        self.assertIn("## 项目提示", content)
        self.assertIn("项目根目录缺少 PRD.md", content)
        self.assertIn("## 章节目标", content)
        self.assertIn("**方向:** 立住死局，并在章末留下残灯代价钩子。", content)
        self.assertIn("## 引用卫生", content)
        self.assertIn("- 已建档未包裹: `2`", content)
        self.assertIn("- 已包裹未建档: `1`", content)
        self.assertIn("**待补包裹:**", content)
        self.assertIn("沈照 (`1` 次，来源 `entities`)", content)
        self.assertIn("青云宗 (`1` 次，来源 `worldbook.factions`)", content)
        self.assertIn("**待补建档:**", content)
        self.assertIn("顾寒山 (`1` 次)", content)
        self.assertIn("## 机器审查摘要", content)
        self.assertIn("- chapter review: `82/100` (solid)", content)
        self.assertIn("- 加权总分: `83.2`", content)
        self.assertIn("**优先动作:**", content)
        self.assertIn("- 强化章末追读问题", content)
        self.assertIn("## 场景审查", content)
        self.assertIn("### 场景 2 (`3..4`)", content)
        self.assertIn("## 正文", content)
        self.assertIn("活下来了，但丢了东西。", content)

    def test_export_review_packet_reports_incomplete_prd(self):
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 读者钩子: TBD\n- 本章承接点: TBD\n",
            encoding="utf-8",
        )
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "review-packet",
            "--chapter-id", "chapter-001",
            "--output", str(self.out_file),
        ])
        self.assertEqual(result, 0)
        content = self.out_file.read_text(encoding="utf-8")
        self.assertIn("PRD.md 仍包含未填启动占位项", content)
        self.assertIn("卷目标", content)


class TestExportVolumeReviewPacket(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh-export-volume-review-packet-"))
        outline = {
            "chapters": [],
            "chapterDirections": [],
            "volumes": [
                {
                    "id": "volume-001",
                    "title": "第一卷",
                    "theme": "残灯初鸣",
                    "chapters": [
                        {
                            "id": "chapter-001",
                            "title": "灯尽人未绝",
                            "status": "completed",
                            "direction": "立住死局。",
                            "beats": [],
                            "scenePlans": [],
                        },
                        {
                            "id": "chapter-002",
                            "title": "灰里递名",
                            "status": "completed",
                            "direction": "把交易推上台面。",
                            "beats": [],
                            "scenePlans": [],
                        },
                    ],
                },
                {
                    "id": "volume-002",
                    "title": "第二卷",
                    "chapters": [
                        {
                            "id": "chapter-003",
                            "title": "别卷章节",
                            "status": "draft",
                            "beats": [],
                            "scenePlans": [],
                        }
                    ],
                },
            ],
        }
        entities = {
            "entities": [
                {
                    "id": "char-shenzhao",
                    "name": "沈照",
                    "type": "character",
                    "aliases": [],
                    "profile": {},
                    "currentState": {},
                }
            ],
            "enrichmentProposals": [],
        }
        _build_minimal_project(self.temp_dir, outline=outline, entities=entities)
        _write_json_yaml(
            resolve_state_path(self.temp_dir, "worldbook"),
            {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [],
                "factions": [
                    {"id": "faction-qingyun", "name": "青云宗", "summary": "本地中型宗门"}
                ],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
        )

        (self.temp_dir / "chapters" / "chapter-001.md").write_text("# 灯尽人未绝\n\n沈照看向青云宗。\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-002.md").write_text("# 灰里递名\n\n@{顾寒山}递来一张纸。\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-003.md").write_text("# 别卷章节\n\n卷二正文。\n", encoding="utf-8")

        story_reviews = {
            "chapterReviews": [
                {
                    "chapterId": "chapter-001",
                    "summary": "第一章死局已立住。",
                    "rating": "solid",
                    "scores": {"total": 80},
                    "priorityActions": ["强化章末钩子"],
                    "strengths": ["死局压迫感成立"],
                    "contractAlignment": {"risks": ["世界规则解释略少"]},
                    "commercialAlignment": {"risks": []},
                },
                {
                    "chapterId": "chapter-002",
                    "summary": "第二章承接顺畅。",
                    "rating": "strong",
                    "scores": {"total": 86},
                    "priorityActions": ["补一次短线回收"],
                    "strengths": ["交易张力明确"],
                    "contractAlignment": {"risks": []},
                    "commercialAlignment": {"risks": ["爽点兑现仍偏晚"]},
                },
            ],
            "sceneReviews": [
                {
                    "chapterId": "chapter-001",
                    "summary": "场景一成立。",
                    "sceneRange": {"sceneIndex": 1, "startParagraph": 1, "endParagraph": 1},
                },
                {
                    "chapterId": "chapter-002",
                    "summary": "场景二成立。",
                    "sceneRange": {"sceneIndex": 1, "startParagraph": 1, "endParagraph": 1},
                },
            ],
            "volumeSelfReviews": [
                {
                    "rubricVersion": "volume-self-review-v1",
                    "volumeId": "volume-001",
                    "volumeTitle": "第一卷",
                    "generatedAt": "2026-04-27T10:00:00+08:00",
                    "conclusion": {
                        "closureStatus": "closed",
                        "allowHumanReview": True,
                        "strongestPoint": "章间承接稳定",
                        "biggestRisk": "世界规则解释仍可更厚",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "label": "卷级闭环", "score": 4, "conclusion": "小闭环已成立"},
                        {"dimensionId": "openingOnboarding", "label": "开篇 onboarding", "score": 3, "conclusion": "最低可读性已建立"},
                        {"dimensionId": "worldLogic", "label": "世界与制度逻辑", "score": 3, "conclusion": "底层逻辑基本成立"},
                        {"dimensionId": "chapterHandoff", "label": "章间承接", "score": 4, "conclusion": "承接自然"},
                        {"dimensionId": "characterContinuity", "label": "角色连续性", "score": 4, "conclusion": "角色反应连续"},
                        {"dimensionId": "antagonistShaping", "label": "对手塑造", "score": 3, "conclusion": "对手基本成立"},
                        {"dimensionId": "conflictEscalation", "label": "冲突升级", "score": 4, "conclusion": "冲突抬升明确"},
                        {"dimensionId": "payoffDelivery", "label": "爽点兑现", "score": 3, "conclusion": "阶段性兑现成立"},
                        {"dimensionId": "foreshadowRhythm", "label": "伏笔与回收节奏", "score": 3, "conclusion": "伏笔节奏可控"},
                        {"dimensionId": "styleReadability", "label": "风格与可读性", "score": 3, "conclusion": "可读性达标"},
                    ],
                    "issues": [
                        {
                            "issue": "世界规则解释仍偏薄",
                            "evidence": ["压火制度解释仍少"],
                            "impact": "前段理解成本偏高",
                            "primaryCause": "tooling_miss",
                            "fixAction": "补一处制度代价解释",
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "主角如何从死局中拿到第一层主动",
                        "delivered": ["主角活下来", "拿到一条主动线索"],
                        "missing": ["卷尾胜负感还可继续加强"],
                        "reasoning": "当前卷已形成完整的小故事单元。",
                    },
                    "repairSuggestions": ["补制度解释", "强化卷尾胜负感"],
                    "acceptedRisks": ["保留一条长线谜团到下一卷"],
                    "gateFailures": [],
                    "finalAllowHumanReview": True,
                    "scoreSummary": {
                        "average": 3.4,
                        "lowestScore": 3,
                        "lowestDimensions": ["开篇 onboarding", "世界与制度逻辑"],
                        "strongestDimension": {"dimensionId": "volumeClosure", "label": "卷级闭环", "score": 4},
                    },
                    "repairCoverage": {
                        "weakDimensionIds": [],
                        "weakDimensionLabels": [],
                        "uncoveredWeakDimensionIds": [],
                        "uncoveredWeakDimensionLabels": [],
                        "issueCount": 1,
                        "repairSuggestionCount": 2,
                        "status": "complete",
                    },
                }
            ],
        }
        _write_json_yaml(resolve_state_path(self.temp_dir, "story_reviews"), story_reviews)
        self.out_dir = self.temp_dir / "exports"
        self.out_dir.mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_volume_review_packet(self):
        result = main([
            "export", "--root", str(self.temp_dir),
            "--format", "review-packet",
            "--volume-id", "volume-001",
            "--output", str(self.out_dir),
        ])
        self.assertEqual(result, 0)

        out_file = self.out_dir / "第一卷-review-packet.md"
        self.assertTrue(out_file.exists())
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("# 卷级审查包: 测试书名 / 第一卷", content)
        self.assertIn("## 项目提示", content)
        self.assertIn("项目根目录缺少 PRD.md", content)
        self.assertIn("## 卷级 AI 自审", content)
        self.assertIn("## 卷级结构检查", content)
        self.assertIn("- 闭环状态: `closed`", content)
        self.assertIn("- 人工审查许可: 声明 `yes` / 工具判定 `yes`", content)
        self.assertIn("- 修复覆盖状态: `complete`", content)
        self.assertIn("- 未覆盖弱项: 无", content)
        self.assertIn("- 结构角色: `intro-volume`", content)
        self.assertIn("**阶段映射:**", content)
        self.assertIn("灯尽人未绝: `opening`", content)
        self.assertIn("灰里递名: `close`", content)
        self.assertIn("**结构检查项:**", content)
        self.assertIn("**评分:**", content)
        self.assertIn("- 卷级闭环: `4/5` - 小闭环已成立", content)
        self.assertIn("**主要问题:**", content)
        self.assertIn("世界规则解释仍偏薄（tooling_miss）；修正：补一处制度代价解释", content)
        self.assertIn("- 卷主题: 残灯初鸣", content)
        self.assertIn("灯尽人未绝", content)
        self.assertIn("灰里递名", content)
        self.assertIn("强化章末钩子", content)
        self.assertIn("补一次短线回收", content)
        self.assertIn("**待补包裹:**", content)
        self.assertIn("灯尽人未绝: 沈照 (`1` 次，来源 `entities`)", content)
        self.assertIn("灯尽人未绝: 青云宗 (`1` 次，来源 `worldbook.factions`)", content)
        self.assertIn("**待补建档:**", content)
        self.assertIn("灰里递名: 顾寒山 (`1` 次)", content)
        self.assertIn("沈照看向青云宗。", content)
        self.assertIn("顾寒山递来一张纸。", content)
        self.assertNotIn("别卷章节", content)
        self.assertNotIn("卷二正文。", content)


if __name__ == "__main__":
    unittest.main()
