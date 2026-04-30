from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.cli import main
from story_harness_cli.protocol.state import load_project_state, save_state
from story_harness_cli.services import normalize_editor_provider_fragment, parse_text_provider_json_object


class ReviewVolumeSelfSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-review-volume-self-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_incomplete_prd(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 读者钩子: TBD\n- 本章交付点: TBD\n",
            encoding="utf-8",
        )

    def _write_minimal_volume_chapters(self) -> None:
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )

    def _run_json(self, args: list[str]) -> tuple[int, dict]:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(args)
        return exit_code, json.loads(buffer.getvalue())

    def _init_volume_project(self) -> None:
        exit_code, _ = self._run_json(
            [
                "init",
                "--root",
                str(self.temp_dir),
                "--title",
                "命灯",
                "--genre",
                "玄幻",
            ]
        )
        self.assertEqual(exit_code, 0)

        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["chapters"] = []
        outline["chapterDirections"] = []
        outline["volumes"] = [
            {
                "id": "volume-001",
                "title": "第一卷",
                "chapters": [
                    {"id": "chapter-001", "title": "灯尽人未绝", "status": "completed"},
                    {"id": "chapter-002", "title": "灰里递名", "status": "completed"},
                ],
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_review_volume_self_persists_structured_review(self) -> None:
        self._init_volume_project()
        self._write_minimal_volume_chapters()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T09:30:00+08:00",
                    "conclusion": {
                        "closureStatus": "closed",
                        "allowHumanReview": True,
                        "strongestPoint": "章间承接稳定",
                        "biggestRisk": "世界规则解释仍偏薄",
                    },
                    "editorPass": {
                        "completed": True,
                        "reviewerRole": "editor",
                        "mode": "independent_agent",
                        "contextIsolation": "no_context_proxy",
                        "notes": "由无上下文代理独立完成评分与评语。",
                    },
                    "editorAssessment": {
                        "overallVerdict": "pass",
                        "summaryComment": "独立编辑视角认为本卷已可进入人工审查，但世界规则解释仍需补强。",
                        "topProblems": ["世界规则解释仍偏薄"],
                        "improvementPoints": ["补一处制度代价解释", "复检卷尾胜负感"],
                        "scores": [
                            {"dimensionId": "volumeClosure", "score": 4, "conclusion": "闭环成立"},
                            {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性已建立"},
                            {"dimensionId": "worldLogic", "score": 3, "conclusion": "制度逻辑基本成立"},
                            {"dimensionId": "chapterHandoff", "score": 4, "conclusion": "章间承接自然"},
                            {"dimensionId": "characterContinuity", "score": 4, "conclusion": "主角反应连续"},
                            {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手动机基本可读"},
                            {"dimensionId": "conflictEscalation", "score": 4, "conclusion": "冲突逐步抬升"},
                            {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "阶段性兑现成立"},
                            {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔密度可控"},
                            {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读性基本达标"},
                        ],
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 4, "conclusion": "已形成阶段性闭环"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性已建立"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "制度逻辑基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 4, "conclusion": "章间承接自然"},
                        {"dimensionId": "characterContinuity", "score": 4, "conclusion": "主角反应连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手动机基本可读"},
                        {"dimensionId": "conflictEscalation", "score": 4, "conclusion": "冲突逐步抬升"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "阶段性兑现成立"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔密度可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读性基本达标"},
                    ],
                    "issues": [
                        {
                            "issue": "世界规则解释仍偏薄",
                            "evidence": ["压火制度只体现压迫，解释仍少"],
                            "impact": "读者理解成本偏高",
                            "primaryCause": "tooling_miss",
                            "fixAction": "补一处制度代价解释",
                            "secondaryCauses": ["self_review_miss"],
                            "whyToolingMissed": "现有工具能报 world onboarding 缺口，但还不能稳定把‘压火制度解释偏薄’收敛成单独问题。",
                            "whySelfReviewMissed": "自审更关注闭环和节奏，没有逐章核对设定解释责任。",
                            "optimizationAction": "补制度解释相关规则，并在卷级模板里要求逐条核对 onboarding 责任。",
                            "chapterRefs": ["chapter-001"],
                            "evidenceRefs": [
                                "chapter-001#paragraph-1",
                                "review-packet:volume-001:chapter-001",
                            ],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "主角如何在压火死局中活下来并拿到第一条主动线索",
                        "delivered": ["主角活下来了", "拿到第一条真相线索"],
                        "missing": ["阶段性反制仍偏弱"],
                        "reasoning": "已完成小闭环，但卷尾胜负感还可以更强。",
                    },
                    "repairSuggestions": ["先补制度解释", "再强化卷尾胜负感"],
                    "acceptedRisks": ["保留一条长线谜团到下一卷"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["saved"])
        self.assertEqual(payload["volumeId"], "volume-001")
        self.assertTrue(payload["finalAllowHumanReview"])
        self.assertTrue(payload["reviewPacketRefreshed"])
        self.assertEqual(payload["reviewPacketRefreshError"], "")
        self.assertEqual(payload["review"]["rubricVersion"], "volume-self-review-v1")
        self.assertEqual(payload["review"]["scoreSummary"]["lowestScore"], 3)
        review_packet_file = self.temp_dir / "reviews" / "volume-001-review-packet.md"
        self.assertEqual(payload["reviewPacketFile"], str(review_packet_file.resolve()))
        self.assertTrue(review_packet_file.exists())
        review_packet_content = review_packet_file.read_text(encoding="utf-8")
        self.assertIn("## 卷级 AI 自审", review_packet_content)
        self.assertIn("章间承接稳定", review_packet_content)
        state = load_project_state(self.temp_dir)
        self.assertEqual(state["story_reviews"]["volumeSelfReviewRubricVersion"], "volume-self-review-v1")
        self.assertEqual(len(state["story_reviews"]["volumeSelfReviews"]), 1)
        saved_review = state["story_reviews"]["volumeSelfReviews"][0]
        self.assertEqual(saved_review["volumeId"], "volume-001")
        self.assertTrue(saved_review["finalAllowHumanReview"])
        self.assertEqual(saved_review["conclusion"]["closureStatus"], "closed")
        self.assertTrue(saved_review["editorPass"]["completed"])
        self.assertEqual(saved_review["editorAssessment"]["overallVerdict"], "pass")
        self.assertEqual(saved_review["issues"][0]["chapterRefs"], ["chapter-001"])
        self.assertEqual(saved_review["issues"][0]["secondaryCauses"], ["self_review_miss"])
        self.assertIn("制度解释", saved_review["issues"][0]["whyToolingMissed"])
        self.assertIn("逐条核对", saved_review["issues"][0]["optimizationAction"])
        self.assertEqual(
            saved_review["issues"][0]["evidenceRefs"],
            ["chapter-001#paragraph-1", "review-packet:volume-001:chapter-001"],
        )

    def test_review_editor_draft_dry_run_builds_provider_request(self) -> None:
        self._init_volume_project()
        self._write_minimal_volume_chapters()

        exit_code, payload = self._run_json(
            [
                "review",
                "editor-draft",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--model",
                "test-text-model",
                "--dry-run",
            ]
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["dryRun"])
        self.assertFalse(payload["saved"])
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "test-text-model")
        self.assertTrue((self.temp_dir / "reviews" / "volume-001-review-packet.md").exists())
        request = payload["providerRequest"]
        self.assertEqual(request["transport"], "json")
        self.assertTrue(request["endpoint"].endswith("/v1/responses"))
        self.assertEqual(request["json"]["model"], "test-text-model")
        self.assertEqual(request["json"]["text"]["format"]["type"], "json_object")
        self.assertIn("reviewPacketMarkdown", payload["prompt"]["userPrompt"])

    def test_text_provider_editor_fragment_normalization_accepts_fenced_json(self) -> None:
        raw = parse_text_provider_json_object(
            """```json
{
  "editorAssessment": {
    "overallVerdict": "revise",
    "summaryComment": "需要补强卷尾兑现。",
    "topProblems": ["卷尾胜负感不足"],
    "improvementPoints": ["补一处明确代价和结果"],
    "scores": [
      {"dimensionId": "volumeClosure", "score": 2, "conclusion": "闭环不足"},
      {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "开篇可读"},
      {"dimensionId": "worldLogic", "score": 3, "conclusion": "逻辑基本成立"},
      {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "承接基本成立"},
      {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续性基本成立"},
      {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手可读"},
      {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突递进"},
      {"dimensionId": "payoffDelivery", "score": 2, "conclusion": "兑现偏弱"},
      {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔可控"},
      {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"}
    ]
  }
}
```"""
        )
        fragment = normalize_editor_provider_fragment(
            raw,
            provider_name="openai-text-http",
            model="test-text-model",
            generated_at="2026-04-30T00:00:00+08:00",
        )

        self.assertTrue(fragment["editorPass"]["completed"])
        self.assertEqual(fragment["editorPass"]["mode"], "independent_agent")
        self.assertEqual(fragment["editorPass"]["contextIsolation"], "no_context_proxy")
        self.assertEqual(fragment["editorAssessment"]["overallVerdict"], "revise")
        self.assertIn("openai-text-http", fragment["editorPass"]["notes"])

    def test_review_volume_self_template_generates_prefilled_template_file(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )
        state = load_project_state(self.temp_dir)
        state["story_reviews"]["chapterReviews"] = [
            {
                "reviewId": "chapter-review-001",
                "chapterId": "chapter-001",
                "chapterTitle": "灯尽人未绝",
                "generatedAt": "2026-04-27T12:00:00+08:00",
                "summary": "死局已立住，但命灯规则解释还能更清楚。",
                "rating": "solid",
                "scores": {"total": 82},
                "weightedScores": {"total": 83.2},
                "priorityActions": ["补足命灯规则解释", "强化章末追读问题"],
                "styleAnalysis": {
                    "styleAnalysis": {
                        "summary": "检测到1项AI风格特征：段落均质。扣1分。"
                    }
                },
                "ruleJudgements": [{"ruleId": "chapter-handoff-weak", "severity": "medium"}],
                "contractAlignment": {"risks": ["残灯真相推进还偏保守"]},
                "commercialAlignment": {"risks": ["章末钩子还可以更狠"]},
            }
        ]
        state["story_reviews"]["sceneReviews"] = [
            {
                "reviewId": "scene-review-001",
                "chapterId": "chapter-001",
                "generatedAt": "2026-04-27T12:03:00+08:00",
                "summary": "场景推进明确，但伏笔兑现点还不够狠。",
                "rating": "solid",
                "scores": {"total": 78},
                "priorityActions": ["补一个更明确的后续兑现点"],
                "sceneRange": {
                    "sceneIndex": 1,
                    "startParagraph": 1,
                    "endParagraph": 1,
                },
            }
        ]
        save_state(self.temp_dir, state)
        out_dir = self.temp_dir / "templates"
        out_dir.mkdir(exist_ok=True)

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self-template",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--output",
                str(out_dir),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["saved"])
        output_file = out_dir / "volume-001-volume-self-review.template.yaml"
        self.assertTrue(output_file.exists())
        self.assertEqual(payload["outputFile"], str(output_file.resolve()))
        template = payload["template"]
        self.assertEqual(template["conclusion"]["closureStatus"], "not_closed")
        self.assertFalse(template["conclusion"]["allowHumanReview"])
        self.assertEqual(template["editorPass"]["mode"], "independent_agent")
        self.assertEqual(template["editorPass"]["contextIsolation"], "no_context_proxy")
        self.assertEqual(template["editorAssessment"]["overallVerdict"], "revise")
        self.assertEqual(len(template["editorAssessment"]["scores"]), 10)
        self.assertEqual(len(template["scores"]), 10)
        self.assertEqual(template["_templateHints"]["scoreScale"], "all score fields must be integers in 0..5")
        self.assertEqual(template["_templateHints"]["issuesType"], "object[]")
        self.assertIn("issue", template["_templateHints"]["issuesRequiredFields"])
        self.assertEqual(template["_templateHints"]["topProblemsType"], "string[]")
        self.assertEqual(template["_templateHints"]["improvementPointsType"], "string[]")
        self.assertEqual(template["_templateHints"]["issueExample"]["primaryCause"], "generation_miss")
        self.assertIn("_templateContext", template)
        self.assertEqual(template["_templateContext"]["volumeId"], "volume-001")
        self.assertEqual(template["_templateContext"]["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertEqual(len(template["_templateContext"]["chapterSignals"]), 2)
        self.assertEqual(len(template["_templateContext"]["chapterReviewSummaries"]), 1)
        self.assertEqual(template["_templateContext"]["chapterReviewSummaries"][0]["chapterId"], "chapter-001")
        self.assertEqual(len(template["_templateContext"]["lowSceneReviews"]), 1)
        self.assertEqual(template["_templateContext"]["lowSceneReviews"][0]["sceneIndex"], 1)
        self.assertEqual(template["_templateContext"]["styleAggregate"]["volumeId"], "volume-001")
        self.assertEqual(template["_templateContext"]["styleAggregate"]["chapterCount"], 2)
        self.assertIn("review-packet:volume-001:chapter-001", template["_templateContext"]["reviewPacketRefs"])
        self.assertIn("残灯真相推进还偏保守", template["_templateContext"]["contractAlignmentRisks"])
        self.assertIn("章末钩子还可以更狠", template["_templateContext"]["commercialAlignmentRisks"])
        self.assertNotEqual(template["conclusion"]["strongestPoint"], "待填写")
        self.assertNotEqual(template["closureAssessment"]["mainProblem"], "待填写")
        self.assertNotEqual(template["closureAssessment"]["reasoning"], "待填写")
        self.assertTrue(template["issues"])
        self.assertTrue(any(item["score"] > 0 for item in template["scores"]))
        self.assertTrue(any(item["score"] <= 2 for item in template["scores"]))
        self.assertEqual(template["_templateContext"]["draftAutofill"]["used"], True)
        self.assertGreater(template["_templateContext"]["preflightSummary"]["mentionActionCount"], 0)
        self.assertTrue(template["repairSuggestions"])
        self.assertEqual(template["_templateContext"]["volumeStructureCheck"]["role"], "intro-volume")
        self.assertTrue(template["_templateContext"]["volumeStructureCheck"]["checklist"])
        self.assertEqual(
            template["_templateContext"]["independentEditorExpectation"]["preferredMode"],
            "independent_agent",
        )
        self.assertIn("chapter-001#scene-1", template["_templateContext"]["evidenceRefExamples"])

    def test_review_volume_self_template_carries_missing_project_prd_advisory(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "PRD.md").unlink()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self-template",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            payload["template"]["_templateContext"]["projectAdvisories"][0]["ruleId"],
            "missing-project-prd",
        )

    def test_review_volume_self_template_maps_contract_tension_to_conflict(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 停雨申请\n\n许澄在法庭里提交原始日志，要求停雨临时禁令。\n",
            encoding="utf-8",
        )
        state = load_project_state(self.temp_dir)
        state["outline"]["volumes"] = [
            {
                "id": "volume-001",
                "title": "第一卷",
                "chapters": [
                    {"id": "chapter-001", "title": "停雨申请", "status": "completed"},
                ],
            }
        ]
        state["story_reviews"]["chapterReviews"] = [
            {
                "reviewId": "chapter-review-001",
                "chapterId": "chapter-001",
                "chapterTitle": "停雨申请",
                "generatedAt": "2026-04-29T12:00:00+08:00",
                "summary": "职业流程清楚，证据压力已建立。",
                "rating": "strong",
                "scores": {"total": 86},
                "contractAlignment": {
                    "risks": [
                        "核心承诺“用职业流程、证据压力和人物选择制造悬疑”：悬疑/反转承诺在本章里的张力兑现偏弱。"
                    ]
                },
                "commercialAlignment": {"risks": []},
            }
        ]
        save_state(self.temp_dir, state)

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self-template",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
            ]
        )

        self.assertEqual(exit_code, 0)
        scores = {
            item["dimensionId"]: item
            for item in payload["template"]["scores"]
        }
        self.assertEqual(scores["conflictEscalation"]["score"], 2)
        self.assertEqual(scores["characterContinuity"]["score"], 3)
        conflict_issues = [
            item
            for item in payload["template"]["issues"]
            if "张力兑现偏弱" in item["issue"]
        ]
        self.assertTrue(conflict_issues)
        self.assertEqual(conflict_issues[0]["chapterRefs"], ["chapter-001"])
        self.assertIn("review-packet:volume-001:chapter-001", conflict_issues[0]["evidenceRefs"])

    def test_review_volume_self_template_carries_incomplete_project_prd_advisory(self) -> None:
        self._init_volume_project()
        self._write_incomplete_prd()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self-template",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            payload["template"]["_templateContext"]["projectAdvisories"][0]["ruleId"],
            "project-prd-incomplete",
        )

    def test_review_volume_self_template_can_merge_partial_and_editor_inputs(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )
        author_input = self.temp_dir / "author-fragment.json"
        author_input.write_text(
            json.dumps(
                {
                    "conclusion": {
                        "strongestPoint": "线索承接清楚",
                        "biggestRisk": "卷尾收束不足",
                    },
                    "closureAssessment": {
                        "mainProblem": "主角能否拿到第一条主动线索",
                    },
                    "repairSuggestions": ["先补卷尾收束"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        editor_input = self.temp_dir / "editor-fragment.json"
        editor_input.write_text(
            json.dumps(
                {
                    "editorPass": {
                        "completed": True,
                        "reviewerRole": "editor",
                        "mode": "independent_agent",
                        "contextIsolation": "no_context_proxy",
                        "notes": "独立编辑已完成。",
                    },
                    "editorAssessment": {
                        "overallVerdict": "revise",
                        "summaryComment": "卷尾仍需补强。",
                        "topProblems": ["卷尾收束不足"],
                        "improvementPoints": ["补一处阶段性交付"],
                        "scores": [
                            {"dimensionId": "volumeClosure", "score": 2, "conclusion": "收束不足"},
                            {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                            {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                            {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "承接自然"},
                            {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                            {"dimensionId": "antagonistShaping", "score": 2, "conclusion": "仍偏弱"},
                            {"dimensionId": "conflictEscalation", "score": 2, "conclusion": "升级不足"},
                            {"dimensionId": "payoffDelivery", "score": 2, "conclusion": "兑现不足"},
                            {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                            {"dimensionId": "styleReadability", "score": 3, "conclusion": "基本可读"},
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        out_dir = self.temp_dir / "drafts"
        out_dir.mkdir(exist_ok=True)

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self-template",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--merge-input",
                str(author_input),
                "--editor-input",
                str(editor_input),
                "--output",
                str(out_dir),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "draft")
        self.assertEqual(payload["mergedInputs"], [str(author_input.resolve())])
        self.assertEqual(payload["editorInput"], str(editor_input.resolve()))
        self.assertTrue(payload["outputFile"].endswith(".draft.yaml"))
        self.assertEqual(payload["template"]["conclusion"]["strongestPoint"], "线索承接清楚")
        self.assertEqual(payload["template"]["closureAssessment"]["mainProblem"], "主角能否拿到第一条主动线索")
        self.assertTrue(payload["template"]["editorPass"]["completed"])
        self.assertEqual(payload["template"]["editorAssessment"]["overallVerdict"], "revise")
        self.assertEqual(payload["template"]["editorAssessment"]["scores"][0]["score"], 2)

    def test_review_volume_self_rejects_unfilled_template_placeholders(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n林舟抬头望向青云宗。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n@{岳池}站在高处，看着林舟被押去青云宗压火。\n",
            encoding="utf-8",
        )
        template_file = self.temp_dir / "volume-self-review-input.yaml"

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self-template",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--output",
                str(template_file),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["saved"])

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(template_file),
                    ]
                )
        self.assertIn("模板占位值", str(exc_info.exception))

    def test_review_volume_self_merges_editor_input_before_validation(self) -> None:
        self._init_volume_project()
        self._write_minimal_volume_chapters()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T09:30:00+08:00",
                    "conclusion": {
                        "closureStatus": "closed",
                        "allowHumanReview": True,
                        "strongestPoint": "章间承接稳定",
                        "biggestRisk": "世界规则解释仍偏薄",
                    },
                    "editorPass": {
                        "completed": False,
                        "reviewerRole": "editor",
                        "mode": "same_agent_fallback",
                        "contextIsolation": "same_thread",
                        "notes": "待导入独立编辑结果。",
                    },
                    "editorAssessment": {
                        "overallVerdict": "not_provided",
                        "summaryComment": "",
                        "topProblems": [],
                        "improvementPoints": [],
                        "scores": [],
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 4, "conclusion": "已形成阶段性闭环"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性已建立"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "制度逻辑基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 4, "conclusion": "章间承接自然"},
                        {"dimensionId": "characterContinuity", "score": 4, "conclusion": "主角反应连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手动机基本可读"},
                        {"dimensionId": "conflictEscalation", "score": 4, "conclusion": "冲突逐步抬升"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "阶段性兑现成立"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔密度可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读性基本达标"},
                    ],
                    "issues": [
                        {
                            "issue": "世界规则解释仍偏薄",
                            "evidence": ["压火制度只体现压迫，解释仍少"],
                            "impact": "读者理解成本偏高",
                            "primaryCause": "tooling_miss",
                            "fixAction": "补一处制度代价解释",
                            "secondaryCauses": ["self_review_miss"],
                            "whyToolingMissed": "现有工具还不能稳定把制度解释偏薄收敛成单独问题。",
                            "whySelfReviewMissed": "自审更关注闭环和节奏，没有逐章核对设定解释责任。",
                            "optimizationAction": "补制度解释相关规则，并在卷级模板里要求逐条核对 onboarding 责任。",
                            "chapterRefs": ["chapter-001"],
                            "evidenceRefs": [
                                "chapter-001#paragraph-1",
                                "review-packet:volume-001:chapter-001",
                            ],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "主角如何在压火死局中活下来并拿到第一条主动线索",
                        "delivered": ["主角活下来了", "拿到第一条真相线索"],
                        "missing": ["阶段性反制仍偏弱"],
                        "reasoning": "已完成小闭环，但卷尾胜负感还可以更强。",
                    },
                    "repairSuggestions": ["先补制度解释", "再强化卷尾胜负感"],
                    "acceptedRisks": ["保留一条长线谜团到下一卷"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        editor_input = self.temp_dir / "volume-self-editor-input.yaml"
        editor_input.write_text(
            json.dumps(
                {
                    "editorPass": {
                        "completed": True,
                        "reviewerRole": "editor",
                        "mode": "independent_agent",
                        "contextIsolation": "no_context_proxy",
                        "notes": "由无上下文代理独立完成评分与评语。",
                    },
                    "editorAssessment": {
                        "overallVerdict": "pass",
                        "summaryComment": "独立编辑视角认为本卷已可进入人工审查，但世界规则解释仍需补强。",
                        "topProblems": ["世界规则解释仍偏薄"],
                        "improvementPoints": ["补一处制度代价解释", "复检卷尾胜负感"],
                        "scores": [
                            {"dimensionId": "volumeClosure", "score": 4, "conclusion": "闭环成立"},
                            {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性已建立"},
                            {"dimensionId": "worldLogic", "score": 3, "conclusion": "制度逻辑基本成立"},
                            {"dimensionId": "chapterHandoff", "score": 4, "conclusion": "章间承接自然"},
                            {"dimensionId": "characterContinuity", "score": 4, "conclusion": "主角反应连续"},
                            {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手动机基本可读"},
                            {"dimensionId": "conflictEscalation", "score": 4, "conclusion": "冲突逐步抬升"},
                            {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "阶段性兑现成立"},
                            {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔密度可控"},
                            {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读性基本达标"},
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
                "--editor-input",
                str(editor_input),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["saved"])
        self.assertEqual(payload["editorInput"], str(editor_input.resolve()))
        self.assertTrue(payload["finalAllowHumanReview"])
        self.assertTrue(payload["review"]["editorPass"]["completed"])
        self.assertEqual(payload["review"]["editorAssessment"]["overallVerdict"], "pass")
        self.assertEqual(payload["review"]["repairCoverage"]["editorWeakDimensionLabels"], [])

    def test_review_volume_self_repair_coverage_includes_editor_weak_dimensions(self) -> None:
        self._init_volume_project()
        self._write_minimal_volume_chapters()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T09:30:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "开篇钩子成立",
                        "biggestRisk": "卷级闭环不足",
                    },
                    "editorPass": {
                        "completed": False,
                        "reviewerRole": "editor",
                        "mode": "same_agent_fallback",
                        "contextIsolation": "same_thread",
                        "notes": "待导入独立编辑结果。",
                    },
                    "editorAssessment": {
                        "overallVerdict": "not_provided",
                        "summaryComment": "",
                        "topProblems": [],
                        "improvementPoints": [],
                        "scores": [],
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "工具侧暂未暴露阻塞"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性已建立"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "制度逻辑基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "承接待后续验证"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "主角反应连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手动机基本可读"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突已抬升"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "局部兑现成立"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔密度可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读性基本达标"},
                    ],
                    "issues": [
                        {
                            "issue": "卷级闭环不足",
                            "evidence": ["当前只完成开篇案件钩子"],
                            "impact": "不适合进入人工终审",
                            "primaryCause": "generation_miss",
                            "fixAction": "补足阶段性交付和短线兑现",
                            "chapterRefs": ["chapter-001"],
                            "evidenceRefs": ["review-packet:volume-001:chapter-001"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "当前卷尚未形成完整小故事闭环",
                        "delivered": ["完成开篇案件钩子"],
                        "missing": ["缺少阶段性胜负和短线兑现"],
                        "reasoning": "作者自审已判未闭环，等待独立编辑补充弱项。",
                    },
                    "repairSuggestions": ["先补卷级闭环，再补短线兑现。"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        editor_input = self.temp_dir / "volume-self-editor-input.yaml"
        editor_input.write_text(
            json.dumps(
                {
                    "editorPass": {
                        "completed": True,
                        "reviewerRole": "editor",
                        "mode": "independent_agent",
                        "contextIsolation": "no_context_proxy",
                        "notes": "独立编辑已完成。",
                    },
                    "editorAssessment": {
                        "overallVerdict": "block",
                        "summaryComment": "卷级闭环和爽点兑现仍不足。",
                        "topProblems": ["卷级闭环不足，短线兑现不足。"],
                        "improvementPoints": ["补阶段性交付和禁令胜负结果。"],
                        "scores": [
                            {"dimensionId": "volumeClosure", "score": 1, "conclusion": "未闭环"},
                            {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                            {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                            {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "待后续验证"},
                            {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                            {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "可读"},
                            {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "有开局升级"},
                            {"dimensionId": "payoffDelivery", "score": 2, "conclusion": "兑现不足"},
                            {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                            {"dimensionId": "styleReadability", "score": 3, "conclusion": "基本可读"},
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
                "--editor-input",
                str(editor_input),
            ]
        )

        self.assertEqual(exit_code, 0)
        coverage = payload["review"]["repairCoverage"]
        self.assertEqual(coverage["rootWeakDimensionLabels"], [])
        self.assertEqual(coverage["editorWeakDimensionLabels"], ["卷级闭环", "爽点兑现"])
        self.assertEqual(coverage["weakDimensionLabels"], ["卷级闭环", "爽点兑现"])
        self.assertEqual(coverage["uncoveredWeakDimensionLabels"], [])

    def test_review_volume_self_rejects_all_zero_scores_even_after_placeholder_replacement(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T10:30:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了第一轮整卷回看",
                        "biggestRisk": "卷级问题仍未收束",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "openingOnboarding", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "worldLogic", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "chapterHandoff", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "characterContinuity", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "antagonistShaping", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "conflictEscalation", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "payoffDelivery", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "foreshadowRhythm", "score": 0, "conclusion": "仍需继续评估"},
                        {"dimensionId": "styleReadability", "score": 0, "conclusion": "仍需继续评估"},
                    ],
                    "issues": [],
                    "closureAssessment": {
                        "mainProblem": "这一卷还没有形成完整小闭环",
                        "delivered": [],
                        "missing": ["卷尾还缺少阶段性交付"],
                        "reasoning": "虽然已经回看，但还没形成有效维度判断。",
                    },
                    "repairSuggestions": ["先补卷尾交付"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("scores 不能全部为 0", str(exc_info.exception))

    def test_review_volume_self_rejects_human_review_yes_when_threshold_not_met(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T10:40:00+08:00",
                    "conclusion": {
                        "closureStatus": "closed",
                        "allowHumanReview": True,
                        "strongestPoint": "至少形成了阶段性承接",
                        "biggestRisk": "风格与承接仍不稳",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 4, "conclusion": "阶段性闭环成立"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性成立"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "世界逻辑基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "章间承接仍偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "角色基本连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手基本成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突抬升可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "有阶段性交付"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔节奏可控"},
                        {"dimensionId": "styleReadability", "score": 2, "conclusion": "风格仍有明显问题"},
                    ],
                    "issues": [
                        {
                            "issue": "章间承接和风格仍偏弱",
                            "evidence": ["第 12 章与第 13 章过渡不足"],
                            "impact": "人工审查前仍有明显阅读断裂",
                            "primaryCause": "self_review_miss",
                            "fixAction": "补承接段并重写两处高 AI 味句子",
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "这一卷能否形成完整小闭环",
                        "delivered": ["主角拿到第一层主动"],
                        "missing": [],
                        "reasoning": "虽然已形成闭环，但仍不该进入人工审查。",
                    },
                    "repairSuggestions": ["补承接段并做一轮风格精修"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("allowHumanReview=true 与评分门槛不一致", str(exc_info.exception))

    def test_review_volume_self_rejects_human_review_yes_without_completed_editor_pass(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T10:45:00+08:00",
                    "conclusion": {
                        "closureStatus": "closed",
                        "allowHumanReview": True,
                        "strongestPoint": "基本闭环已成立",
                        "biggestRisk": "独立编辑审查尚未完成",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 4, "conclusion": "阶段性闭环成立"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "最低可读性成立"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "世界逻辑基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "章间承接可用"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "角色基本连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手基本成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突抬升可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "有阶段性交付"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔节奏可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "风格可读"},
                    ],
                    "issues": [
                        {
                            "issue": "独立编辑审查尚未完成",
                            "evidence": ["当前只有同线程自审，没有独立评分结果"],
                            "impact": "人工审查前缺少独立编辑视角",
                            "primaryCause": "self_review_miss",
                            "fixAction": "补做独立编辑审查",
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "当前版本是否具备进入人工审查的独立编辑背书",
                        "delivered": ["卷级闭环基本成立"],
                        "missing": [],
                        "reasoning": "主闭环已成立，但缺少独立编辑审查，不应进入人工审查。",
                    },
                    "repairSuggestions": ["启用无上下文代理补做独立编辑评分"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("editorPass.completed 必须为 true", str(exc_info.exception))

    def test_review_volume_self_rejects_not_closed_without_issues(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T10:50:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了第一轮回看",
                        "biggestRisk": "卷尾仍未形成阶段性交付",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 2, "conclusion": "卷尾未收住"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "基础可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "世界逻辑可用"},
                        {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "承接基本顺"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "角色连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突可用"},
                        {"dimensionId": "payoffDelivery", "score": 2, "conclusion": "兑现不足"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔节奏可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "风格可读"},
                    ],
                    "issues": [],
                    "closureAssessment": {
                        "mainProblem": "这一卷还没形成完整闭环",
                        "delivered": [],
                        "missing": ["卷尾还缺少阶段性交付"],
                        "reasoning": "能看出问题，但还没把问题正式列出来。",
                    },
                    "repairSuggestions": ["补卷尾阶段性交付"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("issues 不能为空；未闭环时至少要明确一项主要问题", str(exc_info.exception))

    def test_review_volume_self_rejects_weak_dimensions_not_covered_by_issues_or_repairs(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:00:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "角色连续性仍然稳定",
                        "biggestRisk": "卷尾兑现和伏笔节奏仍有明显问题",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读但未完全收住"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "开篇可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "世界规则基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "承接基本顺畅"},
                        {"dimensionId": "characterContinuity", "score": 4, "conclusion": "角色连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突可用"},
                        {"dimensionId": "payoffDelivery", "score": 2, "conclusion": "阶段性爆发不足"},
                        {"dimensionId": "foreshadowRhythm", "score": 2, "conclusion": "伏笔回收节奏失衡"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "风格可读"},
                    ],
                    "issues": [
                        {
                            "issue": "世界规则解释仍偏薄",
                            "evidence": ["前段制度解释仍然不足"],
                            "impact": "读者理解成本偏高",
                            "primaryCause": "generation_miss",
                            "fixAction": "补一段制度规则解释",
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "本卷还没有交出足够明确的阶段性结果",
                        "delivered": [],
                        "missing": ["卷尾还缺少阶段性胜负和回收"],
                        "reasoning": "能看出卷尾还没收住，但当前问题清单没覆盖最弱项。",
                    },
                    "repairSuggestions": ["补一段制度规则解释"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("低分维度还没有被 issues / repairSuggestions 明确覆盖", str(exc_info.exception))

    def test_review_volume_self_rejects_low_score_without_verifiable_refs(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:05:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少已经完成一轮问题归纳",
                        "biggestRisk": "低分项没有给出可核对锚点",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "开篇基本可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "世界规则基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "章间承接仍偏弱"},
                        {"dimensionId": "characterContinuity", "score": 4, "conclusion": "角色连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "对手成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "冲突可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "兑现可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "伏笔节奏可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "风格可读"},
                    ],
                    "issues": [
                        {
                            "issue": "章间承接仍偏弱",
                            "evidence": ["第二章开头没有接住第一章余波"],
                            "impact": "读者会感到跳转过快",
                            "primaryCause": "generation_miss",
                            "fixAction": "补一段承接上一章余波的过渡",
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键过渡还没补齐"],
                        "reasoning": "虽然已经指出问题，但当前还没有可核对的章节锚点。",
                    },
                    "repairSuggestions": ["补一段承接上一章余波的过渡"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("低分维度还缺少可核对的章节或证据锚点", str(exc_info.exception))

    def test_review_volume_self_rejects_malformed_evidence_refs(self) -> None:
        self._init_volume_project()
        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:10:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了卷级回看",
                        "biggestRisk": "问题定位锚点格式不规范",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "章间承接仍偏弱",
                            "evidence": ["两章之间缺少直接过渡"],
                            "impact": "读者会感到跳跃",
                            "primaryCause": "generation_miss",
                            "fixAction": "补一段承接段",
                            "evidenceRefs": ["chapter-002 paragraph-4"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键过渡还没补齐"],
                        "reasoning": "问题已经识别，但引用锚点写法错误。",
                    },
                    "repairSuggestions": ["补一段承接段"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("evidenceRefs[1] 格式无效", str(exc_info.exception))

    def test_review_volume_self_rejects_nonexistent_paragraph_and_scene_refs(self) -> None:
        self._init_volume_project()
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["volumes"][0]["chapters"][0]["scenePlans"] = [
            {
                "id": "scene-001",
                "title": "第一幕",
                "summary": "开场死局",
                "startParagraph": 1,
                "endParagraph": 1,
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n只有一段正文。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章也只有一段。\n",
            encoding="utf-8",
        )

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:20:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了回看",
                        "biggestRisk": "章节锚点不存在",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第一章承接问题定位错了段落",
                            "evidence": ["正文只有一段，但引用了第四段"],
                            "impact": "定位会失真",
                            "primaryCause": "tooling_miss",
                            "fixAction": "改成真实存在的 paragraph ref，并明确承接问题",
                            "evidenceRefs": ["chapter-001#paragraph-4"],
                        },
                        {
                            "issue": "第二章承接问题定位错了场景",
                            "evidence": ["章节根本没有第二幕"],
                            "impact": "定位会失真",
                            "primaryCause": "tooling_miss",
                            "fixAction": "改成真实存在的 scene ref，并补承接说明",
                            "evidenceRefs": ["chapter-001#scene-2"],
                        },
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键问题的锚点还没写对"],
                        "reasoning": "先保证问题定位正确。",
                    },
                    "repairSuggestions": ["先修正承接问题的 evidenceRefs 再继续自审"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("paragraph-4", str(exc_info.exception))

    def test_review_volume_self_rejects_nonexistent_scene_refs(self) -> None:
        self._init_volume_project()
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["volumes"][0]["chapters"][0]["scenePlans"] = [
            {
                "id": "scene-001",
                "title": "第一幕",
                "summary": "开场死局",
                "startParagraph": 1,
                "endParagraph": 1,
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n只有一段正文。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章也只有一段。\n",
            encoding="utf-8",
        )

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:25:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了回看",
                        "biggestRisk": "scene 锚点不存在",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第一章承接问题定位错了场景",
                            "evidence": ["章节只有第一幕，但引用了第二幕"],
                            "impact": "定位会失真",
                            "primaryCause": "tooling_miss",
                            "fixAction": "改成真实存在的 scene ref，并补承接说明",
                            "evidenceRefs": ["chapter-001#scene-2"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键问题的锚点还没写对"],
                        "reasoning": "先保证问题定位正确。",
                    },
                    "repairSuggestions": ["先修正承接问题的 scene evidenceRef"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("scene-2", str(exc_info.exception))

    def test_review_volume_self_accepts_scene_refs_when_scene_review_exists(self) -> None:
        self._init_volume_project()
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["volumes"][0]["chapters"][0]["scenePlans"] = [
            {
                "id": "scene-001",
                "title": "第一幕",
                "summary": "开场死局",
                "startParagraph": 1,
                "endParagraph": 1,
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n只有一段正文。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章也只有一段。\n",
            encoding="utf-8",
        )
        story_reviews_path = self.temp_dir / "reviews" / "story-reviews.yaml"
        story_reviews = json.loads(story_reviews_path.read_text(encoding="utf-8"))
        story_reviews["sceneReviews"] = [
            {
                "reviewId": "scene-review-001",
                "chapterId": "chapter-001",
                "sceneRange": {
                    "sceneIndex": 1,
                    "scenePlanId": "scene-001",
                    "startParagraph": 1,
                    "endParagraph": 1,
                },
                "summary": "第一幕成立。",
            }
        ]
        story_reviews_path.write_text(json.dumps(story_reviews, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:30:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了回看",
                        "biggestRisk": "承接问题仍需继续修",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第一章承接问题仍需补强",
                            "evidence": ["第一幕死局之后的余波还不够直接"],
                            "impact": "读者会感到承接偏弱",
                            "primaryCause": "generation_miss",
                            "fixAction": "补一段第一幕后余波",
                            "evidenceRefs": ["chapter-001#scene-1"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键过渡还没补齐"],
                        "reasoning": "问题已定位到可审查的场景。",
                    },
                    "repairSuggestions": ["先补第一幕余波，再复检承接"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["review"]["issues"][0]["evidenceRefs"], ["chapter-001#scene-1"])

    def test_review_volume_self_rejects_scene_refs_without_scene_review_mapping(self) -> None:
        self._init_volume_project()
        outline_path = self.temp_dir / "outline.yaml"
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        outline["volumes"][0]["chapters"][0]["scenePlans"] = [
            {
                "id": "scene-001",
                "title": "第一幕",
                "summary": "开场死局",
                "startParagraph": 1,
                "endParagraph": 1,
            }
        ]
        outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n只有一段正文。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章也只有一段。\n",
            encoding="utf-8",
        )

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:35:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了回看",
                        "biggestRisk": "scene 锚点还没映射到审查结果",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第一章承接问题仍需补强",
                            "evidence": ["第一幕死局之后的余波还不够直接"],
                            "impact": "读者会感到承接偏弱",
                            "primaryCause": "generation_miss",
                            "fixAction": "补一段第一幕后余波",
                            "evidenceRefs": ["chapter-001#scene-1"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键过渡还没补齐"],
                        "reasoning": "问题已经指向 scene，但还没有对应审查结果。",
                    },
                    "repairSuggestions": ["先补第一幕余波，再复检承接"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("尚未映射到已持久化的 scene review", str(exc_info.exception))

    def test_review_volume_self_accepts_world_rule_onboarding_semantic_ref(self) -> None:
        self._init_volume_project()
        worldbook_path = self.temp_dir / "worldbook.yaml"
        worldbook = json.loads(worldbook_path.read_text(encoding="utf-8"))
        worldbook["factions"] = [
            {
                "id": "faction-001",
                "name": "青云宗",
                "summary": "负责压火的本地宗门。",
            }
        ]
        worldbook_path.write_text(json.dumps(worldbook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n@{青云宗}的人又来押人压火。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章补了一点余波。\n",
            encoding="utf-8",
        )

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:40:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "主线已经立住",
                        "biggestRisk": "开篇设定 onboarding 仍偏薄",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 2, "conclusion": "解释仍偏薄"},
                        {"dimensionId": "worldLogic", "score": 2, "conclusion": "制度逻辑还没讲透"},
                        {"dimensionId": "chapterHandoff", "score": 3, "conclusion": "承接基本成立"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第一章世界规则 onboarding 仍偏薄",
                            "evidence": ["青云宗压火已经出现，但制度代价与命灯规则解释不足"],
                            "impact": "读者会难以理解主角为何必须留下",
                            "primaryCause": "generation_miss",
                            "fixAction": "补一段青云宗压火制度与命灯规则的解释",
                            "evidenceRefs": ["chapter-001#world-rule-onboarding"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "开篇设定 onboarding 仍需补强",
                        "delivered": [],
                        "missing": ["命灯规则和压火制度解释还不够清楚"],
                        "reasoning": "问题已经锚到具体的世界规则 onboarding 缺口。",
                    },
                    "repairSuggestions": ["先补命灯规则和青云宗压火制度解释，再复检开篇 onboarding"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["review"]["issues"][0]["evidenceRefs"], ["chapter-001#world-rule-onboarding"])

    def test_review_volume_self_accepts_handoff_gap_semantic_ref(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n第一章埋下了余波。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章开头直接切到集市。\n",
            encoding="utf-8",
        )
        story_reviews_path = self.temp_dir / "reviews" / "story-reviews.yaml"
        story_reviews = json.loads(story_reviews_path.read_text(encoding="utf-8"))
        story_reviews["chapterReviews"] = [
            {
                "reviewId": "chapter-review-002",
                "chapterId": "chapter-002",
                "chapterHandoffSignals": {
                    "detected": True,
                    "previousChapterId": "chapter-001",
                    "previousChapterTitle": "灯尽人未绝",
                },
                "ruleJudgements": [
                    {
                        "ruleId": "chapterHandoffWeak",
                    }
                ],
            }
        ]
        story_reviews_path.write_text(json.dumps(story_reviews, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:45:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "核心冲突已经起来",
                        "biggestRisk": "章间承接仍偏弱",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第二章承接仍偏弱",
                            "evidence": ["第二章开头没有明显接住第一章余波"],
                            "impact": "读者会感到章间跳跃",
                            "primaryCause": "tooling_miss",
                            "fixAction": "补一段承接第一章余波的过渡",
                            "evidenceRefs": ["chapter-002#handoff-gap"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键过渡还没补齐"],
                        "reasoning": "问题已经锚到持久化 chapter review 的承接信号。",
                    },
                    "repairSuggestions": ["先补章间承接过渡，再复检第二章开头"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, payload = self._run_json(
            [
                "review",
                "volume-self",
                "--root",
                str(self.temp_dir),
                "--volume-id",
                "volume-001",
                "--input",
                str(input_path),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["review"]["issues"][0]["evidenceRefs"], ["chapter-002#handoff-gap"])

    def test_review_volume_self_rejects_missing_semantic_ref(self) -> None:
        self._init_volume_project()
        (self.temp_dir / "chapters" / "chapter-001.md").write_text(
            "# 灯尽人未绝\n\n第一章只有一段正文。\n",
            encoding="utf-8",
        )
        (self.temp_dir / "chapters" / "chapter-002.md").write_text(
            "# 灰里递名\n\n第二章也只有一段正文。\n",
            encoding="utf-8",
        )

        input_path = self.temp_dir / "volume-self-review-input.yaml"
        input_path.write_text(
            json.dumps(
                {
                    "generatedAt": "2026-04-27T11:50:00+08:00",
                    "conclusion": {
                        "closureStatus": "not_closed",
                        "allowHumanReview": False,
                        "strongestPoint": "至少完成了回看",
                        "biggestRisk": "承接问题锚点并不存在",
                    },
                    "scores": [
                        {"dimensionId": "volumeClosure", "score": 3, "conclusion": "整体可读"},
                        {"dimensionId": "openingOnboarding", "score": 3, "conclusion": "可读"},
                        {"dimensionId": "worldLogic", "score": 3, "conclusion": "基本成立"},
                        {"dimensionId": "chapterHandoff", "score": 2, "conclusion": "承接偏弱"},
                        {"dimensionId": "characterContinuity", "score": 3, "conclusion": "连续"},
                        {"dimensionId": "antagonistShaping", "score": 3, "conclusion": "成立"},
                        {"dimensionId": "conflictEscalation", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "payoffDelivery", "score": 3, "conclusion": "可用"},
                        {"dimensionId": "foreshadowRhythm", "score": 3, "conclusion": "可控"},
                        {"dimensionId": "styleReadability", "score": 3, "conclusion": "可读"},
                    ],
                    "issues": [
                        {
                            "issue": "第一章承接问题锚点不存在",
                            "evidence": ["当前卷里还没有对应的 handoff 审查信号"],
                            "impact": "定位会失真",
                            "primaryCause": "tooling_miss",
                            "fixAction": "先产出真实承接信号，再回填引用",
                            "evidenceRefs": ["chapter-001#handoff-gap"],
                        }
                    ],
                    "closureAssessment": {
                        "mainProblem": "卷内承接仍需补强",
                        "delivered": [],
                        "missing": ["关键承接锚点还没建立"],
                        "reasoning": "先保证问题引用确实能对上真实信号。",
                    },
                    "repairSuggestions": ["先跑章节审查确认承接问题，再回填 handoff-gap evidenceRef"],
                    "acceptedRisks": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc_info:
                main(
                    [
                        "review",
                        "volume-self",
                        "--root",
                        str(self.temp_dir),
                        "--volume-id",
                        "volume-001",
                        "--input",
                        str(input_path),
                    ]
                )
        self.assertIn("语义锚点不存在", str(exc_info.exception))
        self.assertIn("handoff-gap", str(exc_info.exception))


if __name__ == "__main__":
    unittest.main()
