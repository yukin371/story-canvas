from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.services.consistency_engine import check_consistency


class ConsistencyEngineTest(unittest.TestCase):
    def test_deceased_entity_active_in_text(self):
        state = {
            "entities": {
                "entities": [
                    {"id": "char-a", "name": "张三", "source": "seed", "aliases": [],
                     "seed": {}, "profile": {"appearance": [], "abilities": [], "speech": [], "relationships": []},
                     "currentState": {"status": "deceased", "physicalState": [], "emotionalState": [], "location": "未知", "lastUpdatedChapter": "chapter-002"},
                     "createdAt": "2026-01-01T00:00:00"},
                ],
                "enrichmentProposals": [],
            },
            "projection": {
                "snapshotProjections": [
                    {"entityId": "char-a", "entityName": "张三", "scopeRef": "chapter-002", "currentState": "deceased", "updatedAt": "2026-01-01"},
                ],
                "relationProjections": [],
                "sceneScopeProjections": [],
                "timelineProjections": [],
                "causalityProjections": [],
            },
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(state, "张三走进房间，坐了下来", "chapter-003")
        hard = result["hardChecks"]
        self.assertTrue(any("deceased" in str(c).lower() or "死亡" in str(c) for c in hard.get("stateContradictions", [])))

    def test_relation_contradiction(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {
                "snapshotProjections": [],
                "relationProjections": [
                    {"fromId": "a", "fromName": "A", "toId": "b", "toName": "B", "scopeRef": "chapter-001", "label": "裂痕", "updatedAt": "2026-01-01"},
                ],
                "sceneScopeProjections": [],
                "timelineProjections": [],
                "causalityProjections": [],
            },
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(state, "A和B亲密地拥抱在一起", "chapter-003")
        hard = result["hardChecks"]
        self.assertTrue(len(hard.get("relationContradictions", [])) > 0)

    def test_outline_deviation_soft_check(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {
                "volumes": [
                    {"id": "vol-1", "title": "第一卷", "theme": "", "chapters": [
                        {"id": "chapter-001", "title": "第一章", "status": "completed", "direction": "", "beats": [
                            {"id": "beat-1", "summary": "开场", "status": "completed"},
                            {"id": "beat-2", "summary": "揭示真相", "status": "planned"},
                        ]},
                    ]},
                ],
                "chapters": [],
                "chapterDirections": [],
            },
        }
        result = check_consistency(state, "一些正文", "chapter-001")
        soft = result["softChecks"]
        self.assertTrue(len(soft.get("outlineDeviations", [])) > 0)

    def test_no_issues(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(state, "天空飘着小雨", "chapter-001")
        self.assertEqual(len(result["hardChecks"]["stateContradictions"]), 0)
        self.assertEqual(len(result["hardChecks"]["relationContradictions"]), 0)

    def test_extracts_setting_candidates(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "所谓“守夜回响”，就是夜巡人借力后残留在现场的追踪痕迹。",
            "chapter-001",
        )
        self.assertTrue(result["settingCandidates"])
        self.assertEqual(result["settingCandidates"][0]["label"], "守夜回响")
        self.assertEqual(result["settingConflicts"], [])

    def test_flags_conflicting_setting_candidate(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {
                "premiseFacts": [],
                "worldRules": [
                    {"id": "rule-001", "label": "守夜代价", "rule": "每次借力都会留下追踪痕迹"}
                ],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "所谓守夜代价，就是每次借力都不会留下痕迹。",
            "chapter-002",
        )
        self.assertTrue(result["settingConflicts"])
        self.assertIn("守夜代价", result["settingConflicts"][0]["issue"])
        self.assertTrue(any(item["ruleId"] == "settingConflict" for item in result["judgements"]))

    def test_flags_unintroduced_name_reveal_after_anonymous_descriptor_block(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "人家是散修，想走哪条路走哪条路。不过青云宗的试炼她也报了名，说是要在试炼中找一条线索。\n\n"
            "女散修。黑鞘剑。冰寒的剑意。\n\n"
            "叶清漪。",
            "chapter-005",
        )
        self.assertTrue(result["unintroducedNameReveals"])
        self.assertEqual(result["unintroducedNameReveals"][0]["name"], "叶清漪")
        self.assertEqual(result["unintroducedNameReveals"][0]["paragraphIndex"], 3)
        judgement = next(item for item in result["judgements"] if item["ruleId"] == "unintroducedNameReveal")
        self.assertEqual(judgement["kind"], "soft")
        self.assertEqual(judgement["scopeRef"]["chapterId"], "chapter-005")

    def test_does_not_flag_name_with_explicit_intro_source(self):
        state = {
            "entities": {"entities": [], "enrichmentProposals": []},
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "女散修背着黑鞘剑站在山道尽头，周身寒意逼人。\n\n"
            "旁边有人低声说她叫叶清漪，是个独来独往的散修。",
            "chapter-005",
        )
        self.assertEqual(result["unintroducedNameReveals"], [])

    def test_flags_low_power_character_on_high_risk_task_without_safeguards(self):
        state = {
            "entities": {
                "entities": [
                    {
                        "id": "char-shenxuan",
                        "name": "沈玄",
                        "state": {"powerLevel": {"publicLevel": "练气一层"}},
                    }
                ],
                "enrichmentProposals": [],
            },
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "沈玄刚入青云宗不久，眼下还只是练气一层。\n\n"
            "可执事仍让沈玄参加宗门试炼，最终环节不是比武，而是进入秘境探索。",
            "chapter-006",
        )
        self.assertTrue(result["capabilityTaskRisks"])
        self.assertEqual(result["capabilityTaskRisks"][0]["entityName"], "沈玄")
        self.assertEqual(result["capabilityTaskRisks"][0]["taskLabel"], "秘境探索")
        self.assertTrue(any(item["ruleId"] == "capabilityTaskMismatch" for item in result["judgements"]))

    def test_does_not_flag_low_power_character_when_safeguards_are_explicit(self):
        state = {
            "entities": {
                "entities": [
                    {
                        "id": "char-shenxuan",
                        "name": "沈玄",
                        "state": {"powerLevel": {"publicLevel": "练气二层"}},
                    }
                ],
                "enrichmentProposals": [],
            },
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {"premiseFacts": [], "worldRules": [], "factions": [], "locations": [], "artifacts": [], "mysteries": []},
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "沈玄如今只是练气二层。\n\n"
            "这场宗门试炼只限练气弟子参加，秘境探索也只在外围进行，且有长老带队并提前发下护符，因此沈玄也在名单里。",
            "chapter-006",
        )
        self.assertEqual(result["capabilityTaskRisks"], [])

    def test_flags_power_progression_conflict_when_breakthrough_target_skips_registered_next_stage(self):
        state = {
            "entities": {
                "entities": [
                    {
                        "id": "char-shenxuan",
                        "name": "沈玄",
                        "state": {"powerLevel": {"publicLevel": "练气一层"}},
                    }
                ],
                "enrichmentProposals": [],
            },
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [
                    {
                        "id": "immortal-path",
                        "label": "仙道境界",
                        "stages": [
                            {"name": "练气一层", "nextStage": "练气二层", "breakthroughRequirements": ["凝气入脉"]},
                            {"name": "练气二层", "nextStage": "练气三层"},
                            {"name": "练气三层", "nextStage": "筑基"},
                            {"name": "筑基", "nextStage": "金丹"},
                        ],
                    }
                ],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
            "outline": { "volumes": [], "chapters": [], "chapterDirections": [] },
        }
        result = check_consistency(
            state,
            "沈玄如今仍停在练气一层，却想借这一夜直接突破筑基，连护法都还没备齐。",
            "chapter-007",
        )
        self.assertTrue(result["powerProgressionConflicts"])
        self.assertEqual(result["powerProgressionConflicts"][0]["entityName"], "沈玄")
        self.assertEqual(result["powerProgressionConflicts"][0]["expectedNextStage"], "练气二层")
        self.assertEqual(result["powerProgressionConflicts"][0]["targetStage"], "筑基")
        self.assertTrue(any(item["ruleId"] == "powerProgressionConflict" for item in result["judgements"]))

    def test_does_not_flag_power_progression_when_target_matches_registered_next_stage(self):
        state = {
            "entities": {
                "entities": [
                    {
                        "id": "char-shenxuan",
                        "name": "沈玄",
                        "state": {"powerLevel": {"publicLevel": "练气一层"}},
                    }
                ],
                "enrichmentProposals": [],
            },
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [
                    {
                        "id": "immortal-path",
                        "label": "仙道境界",
                        "stages": [
                            {"name": "练气一层", "nextStage": "练气二层"},
                            {"name": "练气二层", "nextStage": "练气三层"},
                        ],
                    }
                ],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
            "outline": { "volumes": [], "chapters": [], "chapterDirections": [] },
        }
        result = check_consistency(
            state,
            "沈玄这几日一直稳固气海，只等今夜一举突破练气二层。",
            "chapter-007",
        )
        self.assertEqual(result["powerProgressionConflicts"], [])

    def test_does_not_assign_other_characters_breakthrough_target_to_current_entity(self):
        state = {
            "entities": {
                "entities": [
                    {
                        "id": "char-shenxuan",
                        "name": "沈玄",
                        "state": {"powerLevel": {"publicLevel": "练气一层"}},
                    }
                ],
                "enrichmentProposals": [],
            },
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [
                    {
                        "id": "immortal-path",
                        "label": "仙道境界",
                        "stages": [
                            {"name": "练气一层", "nextStage": "练气二层"},
                            {"name": "练气二层", "nextStage": "练气三层"},
                            {"name": "练气三层", "nextStage": "筑基"},
                            {"name": "筑基", "nextStage": "金丹"},
                        ],
                    }
                ],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "沈玄仍停在练气一层，连气海都还没稳住。\n\n顾长渊昨夜已经开始冲击筑基。",
            "chapter-007",
        )
        self.assertEqual(result["powerProgressionConflicts"], [])

    def test_does_not_flag_negated_or_failed_breakthrough_target(self):
        state = {
            "entities": {
                "entities": [
                    {
                        "id": "char-shenxuan",
                        "name": "沈玄",
                        "state": {"powerLevel": {"publicLevel": "练气一层"}},
                    }
                ],
                "enrichmentProposals": [],
            },
            "projection": {"snapshotProjections": [], "relationProjections": [], "sceneScopeProjections": [], "timelineProjections": [], "causalityProjections": []},
            "worldbook": {
                "premiseFacts": [],
                "worldRules": [],
                "powerProgressions": [
                    {
                        "id": "immortal-path",
                        "label": "仙道境界",
                        "stages": [
                            {"name": "练气一层", "nextStage": "练气二层"},
                            {"name": "练气二层", "nextStage": "练气三层"},
                            {"name": "练气三层", "nextStage": "筑基"},
                            {"name": "筑基", "nextStage": "金丹"},
                        ],
                    }
                ],
                "factions": [],
                "locations": [],
                "artifacts": [],
                "mysteries": [],
            },
            "outline": {"volumes": [], "chapters": [], "chapterDirections": []},
        }
        result = check_consistency(
            state,
            "沈玄如今仍在练气一层，却还不敢冲击筑基，上次强行突破筑基失败后他已经收敛许多。",
            "chapter-007",
        )
        self.assertEqual(result["powerProgressionConflicts"], [])


if __name__ == "__main__":
    unittest.main()
