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

    def test_context_refresh_includes_story_constraints(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["context", "refresh", "--root", str(self.temp_dir), "--chapter-id", "chapter-001"])

        payload = json.loads(buffer.getvalue())
        context_lens = json.loads((self.temp_dir / "projections" / "context-lens.yaml").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["chapterId"], "chapter-001")
        self.assertEqual(payload["emotionalContract"]["coreEmotions"], ["压迫下反制", "暗线拼合时的原来如此"])
        self.assertEqual(payload["storyTemplate"]["id"], "xianxia-revenge-serial")
        self.assertEqual(payload["activeCharacters"][0]["stateTags"], ["受伤", "怀疑守夜人"])
        self.assertEqual(payload["activeCharacters"][0]["recentChange"]["chapterId"], "chapter-001")
        self.assertEqual(payload["activeRelations"][0]["label"], "互相试探")
        self.assertEqual(payload["activeWorldRules"][0]["id"], "rule-night")
        self.assertEqual(payload["activeFactions"][0]["name"], "城北守夜人")
        self.assertEqual(payload["activeThreads"][0]["id"], "thread-night-watch")
        self.assertEqual(payload["activeForeshadows"][0]["id"], "fs-night-watch")
        self.assertEqual(payload["dueForeshadows"][0]["id"], "fs-night-watch")
        self.assertEqual(payload["pendingChangeRequestCount"], 1)
        self.assertEqual(context_lens["currentChapterId"], "chapter-001")
        self.assertEqual(context_lens["lenses"][0]["dueForeshadows"][0]["id"], "fs-night-watch")


if __name__ == "__main__":
    unittest.main()
