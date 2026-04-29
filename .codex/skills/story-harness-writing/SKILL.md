---
name: story-harness-writing
description: "Structured Chinese novel writing and review adapter for Codex. Use when Codex needs to execute project-internal prose-first fiction work in Story Canvas: chapter planning, drafting, revision, chapter/scene review, context refresh, workflow gates, volume self-review, review-packet export, and evidence-based rewrite loops. Do not use this skill for pre-project idea exploration; use `story-harness-brainstorm` first when the user is still discovering premise, hook, serial loop, or PRD seed. Do not use this skill for illustration-only work; use `story-canvas-imagegen` separately when the task is about image generation."
---

# Story Canvas Writing

Use this skill as the novel-writing adapter for the Story Canvas repository.

This skill is intentionally separate from `story-canvas-imagegen`.

If the user is still before project creation and mainly wants premise exploration, use `story-harness-brainstorm` instead.

Separation rule:

1. if the task is only about novel text, load this skill only
2. if the task is only about illustration generation, load `story-canvas-imagegen` only
3. only load both when the user is doing mixed text + illustration workflow

The repository remains the source of truth:

```text
agent -> story-canvas CLI -> protocol files
```

Do not invent a parallel state system.

## Read Order

Always read in this order:

1. `docs/guides/writing-rules.md`
2. `docs/guides/volume-self-review.md`
3. `docs/guides/creative-workflow.md`
4. `references/protocol.md`
5. `references/writing-universal.md`
6. `references/workflow-gates.md`

Read `references/genre-overlays.md` only when:

1. the task genuinely depends on genre / tag differences
2. the user explicitly asks for a specific platform,类型,或风格目标

Read `references/planning-primitives.md` only when:

1. the task is about character cards, arc design, chapter direction, beats, or scene planning
2. you need to translate old writing-template fields into Story Canvas-compatible planning

Read [../../ADAPTER_ARCHITECTURE.md](../../ADAPTER_ARCHITECTURE.md) when you need the full layered design.

## Layer Model

This skill uses progressive disclosure:

1. universal writing base
2. workflow gates
3. optional genre / tag overlay

Do not front-load all layers when the task only needs the first one.

## Role Model

This skill uses two explicit AI roles:

1. `author`
   - owns brainstorming-to-draft execution inside the current creative thread
   - writes chapters, revises prose, consumes `startGuide`, and follows chapter / volume gates
2. `editor`
   - owns review, scoring, defect attribution, and release judgement
   - does not continue drafting while acting as editor
   - should review against the repository rubric, not against personal taste

Keep the roles separate:

1. the `author` writes and revises
2. the `editor` reviews and scores
3. do not let the same pass mix “continue drafting” and “declare ready for human review”

`fresh-context editor pass` does not mean “no project rules”.
It means:

1. do not inherit the current creative thread, prior self-justification, or previous verdict
2. do inherit the project rules needed for fair review: this skill, `docs/guides/volume-self-review.md`, the generated template, and the review packet
3. the editor is independent from the drafting context, not independent from the scoring standard

## Runtime

Prefer:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas <command> ...
```

If the installed command is known-good, `uv run story-canvas ...` is also acceptable.

Legacy compatibility:

1. `story-harness`
2. `python -m story_harness_cli`

They still work, but they are not the primary entrypoints.

## Mandatory Workflow

For real project execution, do not freestyle the loop. Use the repository gates from `references/workflow-gates.md`.

At minimum:

1. before inventing a chapter-start plan, run `status --chapter-id` or `workflow status` and consume `startGuide`
2. treat `startGuide` as the canonical startup handoff between skill and CLI; do not ignore it and improvise a parallel bootstrap flow
3. if `startGuide.hasBodyParagraphs=false`, do not pretend `scenePlans` can be completed from nothing; first create chapter skeleton prose, then run the CLI steps it suggests
4. if `startGuide` and your own assumption conflict, prefer the CLI output and adjust your plan
5. chapter work must go through write-before gate, write-after review, and revision re-check
6. volume work must go through `review preflight`, `review volume-self`, `workflow status --volume-id`, and review packet export
7. volume self-review should be driven by the `editor` role, not by the drafting `author` role
8. if the host supports subagents and the user asked for independent review, use a fresh-context `editor` pass
9. the `editor` must score with the repository's shared 10-dimension rubric; do not invent a second editor-only score table

## Skill + CLI Contract

This skill is not the source of truth for project readiness. The CLI is.

Use this split:

1. the skill decides which repository layer to read and how to interpret the task
2. the CLI decides whether the target chapter is actually ready, blocked, or still bootstrap-only
3. the skill should summarize CLI output for the user, but should not replace it with invented readiness claims
4. chapter work still has to pass the repository gates before it is described as ready

When starting a brand-new chapter or project:

1. run `status --root <project-dir> --chapter-id <chapter-id>` first
2. read `targetChapter.startGuide`
3. if `missing-direction` or `missing-beats` is present, prefer `structure apply/scaffold` or explicit beat commands before drafting
4. if only `missing-scene-plans` remains and `hasBodyParagraphs=false`, write 1 short scene skeleton paragraph per intended scene before `outline scene-detect`
5. if `hasBodyParagraphs=true`, `outline scene-detect` is acceptable for first-pass scene boundaries
6. re-run `outline check` after each structural step instead of assuming the gate is now open

## Writing Policy

Use this skill to improve fiction quality, not to mechanically pass rules.

Preferred fixes:

1. concrete consequences
2. object and scene residue
3. dialogue carry-over
4. state aftereffects
5. active thread pressure

Avoid stock bridge patches such as `上一章之后` unless the prose genuinely needs that wording.

## References

- `references/protocol.md`: project layout and protocol constraints
- `references/writing-universal.md`: prose-first universal writing base
- `references/workflow-gates.md`: mandatory CLI gates and stop conditions
- `references/planning-primitives.md`: Story Canvas-compatible character and chapter planning primitives
- `references/genre-overlays.md`: genre / tag overlay index and current maturity state

## Completion Rule

When you finish a pass, report:

```text
Ran:
Key findings:
Revisions made:
Recheck result:
Accepted risks:
Next gate:
```

If a normally expected gate was not run, say why.
