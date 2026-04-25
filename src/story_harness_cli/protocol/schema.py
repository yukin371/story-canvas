from __future__ import annotations

from typing import Any, Dict


def default_project_state() -> Dict[str, Dict[str, Any]]:
    return {
        "project": {
            "title": "",
            "genre": "",
            "defaultMode": "driving",
            "activeChapterId": None,
            "positioning": {
                "primaryGenre": "",
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
            "emotionalContract": {
                "coreEmotions": [],
                "chapterEmotionFloor": [],
                "forbiddenEmotions": [],
                "revealPreference": {
                    "defaultMode": "",
                    "allowDirectExplainAtClimax": False,
                },
            },
            "storyTemplate": {
                "id": "",
                "label": "",
                "modulePolicy": {},
                "reviewFocus": [],
            },
            "commercialPositioning": {
                "premise": "",
                "hookLine": "",
                "hookStack": [],
                "benchmarkWorks": [],
                "targetPlatform": "",
                "serializationModel": "",
                "releaseCadence": "",
                "chapterWordFloor": 0,
                "chapterWordTarget": 0,
            },
            "createdAt": "",
            "updatedAt": "",
        },
        "outline": {"chapters": [], "chapterDirections": [], "volumes": []},
        "entities": {"entities": [], "enrichmentProposals": []},
        "timeline": {"events": []},
        "branches": {"branches": []},
        "proposals": {"draftProposals": []},
        "reviews": {"changeRequests": []},
        "story_reviews": {
            "rubricVersion": "chapter-review-v1",
            "sceneRubricVersion": "scene-review-v1",
            "chapterReviews": [],
            "sceneReviews": [],
        },
        "projection": {
            "snapshotProjections": [],
            "relationProjections": [],
            "sceneScopeProjections": [],
            "timelineProjections": [],
            "causalityProjections": [],
        },
        "context_lens": {"currentChapterId": None, "lenses": []},
        "projection_log": {"projectionChanges": []},
        "workflow_progress": {
            "currentStage": "",
            "targetChapterId": None,
            "workflowStatus": "",
            "gateHistory": [],
            "stageResults": {},
            "updatedAt": "",
            "lastRunMode": "",
        },
        "illustrations": {
            "adapter": {
                "name": "openai",
                "model": "gpt-image-2",
                "defaultSize": "1024x1024",
                "quality": "standard",
            },
            "promptPack": {
                "name": "default",
                "version": "builtin",
            },
            "generated": [],
        },
        "threads": {"threads": []},
        "structures": {"activeStructure": None, "mappings": []},
        "worldbook": {
            "premiseFacts": [],
            "worldRules": [],
            "factions": [],
            "locations": [],
            "artifacts": [],
            "mysteries": [],
        },
        "foreshadowing": {"foreshadows": []},
        "detailed_outlines": {"entries": []},
    }
