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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ContextRefreshSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-context-refresh-"))
        fixture = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
        shutil.copytree(fixture, self.temp_dir, dirs_exist_ok=True)
        for relative in ["proposals", "reviews", "projections", "logs"]:
            (self.temp_dir / relative).mkdir(exist_ok=True)

        project = json.loads((self.temp_dir / "project.yaml").read_text(encoding="utf-8"))
        project["emotionalContract"] = {
            "coreEmotions": ["压迫下反制", "暗线拼合时的原来如此"],
            "chapterEmotionFloor": ["每章至少有一个情绪推进点"],
            "forbiddenEmotions": ["空转讲设定"],
            "revealPreference": {
                "defaultMode": "partial-inference",
                "allowDirectExplainAtClimax": True,
            },
        }
        project["storyTemplate"] = {
            "id": "xianxia-revenge-serial",
            "label": "仙侠复仇连载长篇",
            "modulePolicy": {
                "worldbook": "required",
                "factions": "required",
                "foreshadowLedger": "required",
            },
            "reviewFocus": ["世界规则兑现", "伏笔长回收"],
        }
        _write_json(self.temp_dir / "project.yaml", project)

        _write_json(
            self.temp_dir / "entities.yaml",
            {
                "entities": [
                    {
                        "id": "char-linzhou",
                        "name": "林舟",
                        "type": "character",
                        "state": {
                            "statusTags": ["受伤", "怀疑守夜人"],
                            "powerLevel": {"publicLevel": "凡人", "trueLevel": "半觉醒"},
                            "injuries": ["右臂撕裂伤"],
                        },
                        "changeLog": [
                            {
                                "id": "chg-001",
                                "chapterId": "chapter-001",
                                "field": "state.statusTags",
                                "reason": "仓库冲突后确认自己被盯上",
                            }
                        ],
                    },
                    {
                        "id": "char-shenzhao",
                        "name": "沈昭",
                        "type": "character",
                        "currentState": "试探；隐瞒",
                    },
                ],
                "enrichmentProposals": [],
            },
        )
        _write_json(
            self.temp_dir / "threads.yaml",
            {
                "threads": [
                    {
                        "id": "thread-night-watch",
                        "label": "守夜人暗线",
                        "type": "main",
                        "status": "active",
                        "relatedEntities": ["char-linzhou"],
                        "relatedForeshadows": ["fs-night-watch"],
                        "targetPayoffScope": "volume",
                    }
                ]
            },
        )
        _write_json(
            self.temp_dir / "worldbook.yaml",
            {
                "premiseFacts": [],
                "worldRules": [
                    {
                        "id": "rule-night",
                        "label": "守夜代价",
                        "rule": "每次借力都会留下被反向追踪的痕迹",
                        "scope": "global",
                        "status": "active",
                    }
                ],
                "factions": [
                    {
                        "id": "faction-night-watch",
                        "name": "城北守夜人",
                        "type": "organization",
                        "status": "active",
                    }
                ],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
        )
        _write_json(
            self.temp_dir / "foreshadowing.yaml",
            {
                "foreshadows": [
                    {
                        "id": "fs-night-watch",
                        "title": "守夜人名册缺页",
                        "origin": {"type": "outline-seeded"},
                        "plantPoints": [{"chapterId": "chapter-001", "signalType": "concept-hint"}],
                        "payoffPlan": {
                            "window": {
                                "type": "short",
                                "targetChapterStart": "chapter-001",
                                "targetChapterEnd": "chapter-001",
                            },
                            "style": "partial-reveal",
                            "readerRealizationMode": "infer-before-confirm",
                        },
                        "lineBinding": {
                            "threads": ["thread-night-watch"],
                            "entities": ["char-linzhou"],
                        },
                        "emotionGoal": ["逼近感", "原来如此"],
                        "status": "planted",
                        "payoffPoints": [],
                    },
                    {
                        "id": "fs-unrelated",
                        "title": "远处钟声",
                        "origin": {"type": "emergent"},
                        "plantPoints": [{"chapterId": "chapter-003", "signalType": "background"}],
                        "payoffPlan": {
                            "window": {
                                "type": "long",
                                "targetChapterStart": "chapter-010",
                                "targetChapterEnd": "chapter-012",
                            },
                            "style": "background-payoff",
                            "readerRealizationMode": "never-explicitly-confirmed",
                        },
                        "lineBinding": {"threads": [], "entities": []},
                        "emotionGoal": ["隐约不安"],
                        "status": "planted",
                        "payoffPoints": [],
                    },
                ]
            },
        )
        _write_json(self.temp_dir / "proposals" / "draft-proposals.yaml", {"draftProposals": []})
        _write_json(
            self.temp_dir / "reviews" / "change-requests.yaml",
            {
                "changeRequests": [
                    {
                        "id": "cr-001",
                        "chapterId": "chapter-001",
                        "title": "补强沈昭试探的情绪层",
                        "kind": "emotion",
                        "status": "pending",
                    },
                    {
                        "id": "cr-002",
                        "chapterId": "chapter-001",
                        "title": "补一段旧案背景",
                        "kind": "continuity",
                        "status": "accepted",
                    },
                ]
            },
        )
        _write_json(
            self.temp_dir / "projections" / "projection.yaml",
            {
                "snapshotProjections": [],
                "relationProjections": [
                    {
                        "fromId": "char-linzhou",
                        "fromName": "林舟",
                        "toId": "char-shenzhao",
                        "toName": "沈昭",
                        "label": "互相试探",
                        "scopeRef": "chapter-001",
                    }
                ],
                "sceneScopeProjections": [],
                "timelineProjections": [],
                "causalityProjections": [],
            },
        )
        _write_json(self.temp_dir / "projections" / "context-lens.yaml", {"currentChapterId": None, "lenses": []})
        _write_json(self.temp_dir / "logs" / "projection-log.yaml", {"projectionChanges": []})
        _write_json(
            self.temp_dir / "logs" / "analysis-chapter-001.yaml",
            {
                "chapterId": "chapter-001",
                "sceneScope": {
                    "activeEntityIds": ["char-linzhou", "char-shenzhao"],
                },
            },
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_incomplete_prd(self) -> None:
        (self.temp_dir / "PRD.md").write_text(
            "# PRD\n\n- 卷目标: TBD\n- 关键设定 onboarding: TBD\n- 本章交付点: TBD\n",
            encoding="utf-8",
        )

    def test_context_refresh_includes_story_constraints(self) -> None:
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "裂痕之夜",
                        "status": "draft",
                        "direction": "林舟在仓库冲突后确认自己被盯上。",
                        "beats": [{"summary": "确认风险来源"}],
                        "scenePlans": [{"title": "仓库对峙", "goal": "暴露追踪风险"}],
                    },
                    {
                        "id": "chapter-002",
                        "title": "追踪余波",
                        "status": "draft",
                        "direction": "承接仓库冲突后的追踪风险，决定是否继续深查守夜人。",
                        "beats": [{"summary": "接住余波"}, {"summary": "做出选择"}],
                        "scenePlans": [{"title": "回到住处", "goal": "处理伤势并判断下一步"}],
                    },
                    {
                        "id": "chapter-003",
                        "title": "旧案入口",
                        "status": "draft",
                        "direction": "顺着缺页线索切入旧案。",
                        "beats": [],
                        "scenePlans": [],
                    },
                ],
                "chapterDirections": [],
            },
        )
        _write_json(
            self.temp_dir / "logs" / "analysis-chapter-002.yaml",
            {
                "chapterId": "chapter-002",
                "sceneScope": {
                    "activeEntityIds": ["char-linzhou", "char-shenzhao"],
                },
            },
        )
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["context", "refresh", "--root", str(self.temp_dir), "--chapter-id", "chapter-002"])

        payload = json.loads(buffer.getvalue())
        context_lens = json.loads((self.temp_dir / "projections" / "context-lens.yaml").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-002")
        self.assertEqual(payload["emotionalContract"]["coreEmotions"], ["压迫下反制", "暗线拼合时的原来如此"])
        self.assertEqual(payload["storyTemplate"]["id"], "xianxia-revenge-serial")
        self.assertEqual(payload["activeCharacters"][0]["stateTags"], ["受伤", "怀疑守夜人"])
        self.assertEqual(payload["activeCharacters"][0]["recentChange"]["chapterId"], "chapter-001")
        self.assertEqual(payload["activeWorldRules"][0]["id"], "rule-night")
        self.assertEqual(payload["activeFactions"][0]["name"], "城北守夜人")
        self.assertEqual(payload["activeThreads"][0]["id"], "thread-night-watch")
        self.assertEqual(payload["activeForeshadows"][0]["id"], "fs-night-watch")
        self.assertEqual(payload["chapterHandoff"]["previousChapter"]["id"], "chapter-001")
        self.assertEqual(payload["chapterHandoff"]["currentChapter"]["id"], "chapter-002")
        self.assertEqual(payload["chapterHandoff"]["nextChapter"]["id"], "chapter-003")
        self.assertEqual(payload["chapterHandoff"]["carryOverEntityChanges"][0]["name"], "林舟")
        self.assertIn("守夜人暗线", payload["chapterHandoff"]["activeThreadLabels"])
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertEqual(payload["pendingChangeRequestCount"], 0)
        self.assertEqual(context_lens["currentChapterId"], "chapter-002")
        self.assertEqual(context_lens["lenses"][0]["chapterHandoff"]["previousChapter"]["id"], "chapter-001")
        self.assertNotIn("projectAdvisories", context_lens["lenses"][0])

    def test_context_refresh_prefers_current_analysis_over_stale_projection_scope(self) -> None:
        _write_json(
            self.temp_dir / "projections" / "projection.yaml",
            {
                "snapshotProjections": [
                    {
                        "entityId": "inferred::旧南堤",
                        "entityName": "旧南堤",
                        "scopeRef": "chapter-001",
                        "currentState": "离开",
                    },
                    {
                        "entityId": "char-linzhou",
                        "entityName": "林舟",
                        "scopeRef": "chapter-001",
                        "currentState": "离开",
                    },
                ],
                "relationProjections": [],
                "sceneScopeProjections": [
                    {
                        "chapterId": "chapter-001",
                        "activeEntityIds": ["char-linzhou", "inferred::旧南堤"],
                    }
                ],
                "timelineProjections": [],
                "causalityProjections": [],
            },
        )
        _write_json(
            self.temp_dir / "logs" / "analysis-chapter-001.yaml",
            {
                "chapterId": "chapter-001",
                "sceneScope": {
                    "activeEntityIds": ["char-linzhou"],
                },
                "snapshotCandidates": [],
            },
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["context", "refresh", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        active_ids = [item["id"] for item in payload["activeCharacters"]]
        self.assertEqual(active_ids, ["char-linzhou"])
        self.assertNotEqual(payload["activeCharacters"][0]["currentState"], "离开")

    def test_context_show_includes_project_advisories_without_persisting_them(self) -> None:
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "裂痕之夜",
                        "status": "draft",
                        "direction": "林舟确认追踪风险。",
                        "beats": [{"summary": "确认风险来源"}],
                        "scenePlans": [{"title": "仓库对峙", "goal": "暴露追踪风险"}],
                    }
                ],
                "chapterDirections": [],
            },
        )
        _write_json(
            self.temp_dir / "logs" / "analysis-chapter-001.yaml",
            {
                "chapterId": "chapter-001",
                "sceneScope": {
                    "activeEntityIds": ["char-linzhou", "char-shenzhao"],
                },
            },
        )

        refresh_buffer = StringIO()
        with redirect_stdout(refresh_buffer):
            refresh_exit_code = main(["context", "refresh", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])
        self.assertEqual(refresh_exit_code, 0)

        show_buffer = StringIO()
        with redirect_stdout(show_buffer):
            show_exit_code = main(["context", "show", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        payload = json.loads(show_buffer.getvalue())
        context_lens = json.loads((self.temp_dir / "projections" / "context-lens.yaml").read_text(encoding="utf-8"))

        self.assertEqual(show_exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "missing-project-prd")
        self.assertNotIn("projectAdvisories", context_lens["lenses"][0])

    def test_context_refresh_reports_incomplete_prd_without_persisting_it(self) -> None:
        self._write_incomplete_prd()
        _write_json(
            self.temp_dir / "outline.yaml",
            {
                "chapters": [
                    {
                        "id": "chapter-001",
                        "title": "裂痕之夜",
                        "status": "draft",
                        "direction": "林舟确认追踪风险。",
                        "beats": [{"summary": "确认风险来源"}],
                        "scenePlans": [{"title": "仓库对峙", "goal": "暴露追踪风险"}],
                    }
                ],
                "chapterDirections": [],
            },
        )
        _write_json(
            self.temp_dir / "logs" / "analysis-chapter-001.yaml",
            {
                "chapterId": "chapter-001",
                "sceneScope": {
                    "activeEntityIds": ["char-linzhou", "char-shenzhao"],
                },
            },
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["context", "refresh", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        payload = json.loads(buffer.getvalue())
        context_lens = json.loads((self.temp_dir / "projections" / "context-lens.yaml").read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["projectAdvisories"][0]["ruleId"], "project-prd-incomplete")
        self.assertIn("关键设定 onboarding", payload["projectAdvisories"][0]["message"])
        self.assertNotIn("projectAdvisories", context_lens["lenses"][0])


if __name__ == "__main__":
    unittest.main()
