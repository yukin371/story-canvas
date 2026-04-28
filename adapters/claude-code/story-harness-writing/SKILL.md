---
name: story-harness-writing
description: Structured Chinese novel writing and review adapter for Claude Code. Use when Claude Code needs to execute project-internal prose-first fiction work in Story Canvas: chapter planning, drafting, revision, chapter/scene review, context refresh, workflow gates, volume self-review, review-packet export, and evidence-based rewrite loops. Do not use this skill for pre-project idea exploration; use `story-harness-brainstorm` first when the user is still discovering premise, hook, serial loop, or PRD seed. Do not use this skill for illustration-only work; use `story-canvas-imagegen` separately when the task is about image generation.
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

1. chapter work must go through write-before gate, write-after review, and revision re-check
2. volume work must go through `review preflight`, `review volume-self`, `workflow status --volume-id`, and review packet export
3. if the host supports subagents and the user asked for independent review, use a fresh-context editor pass

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
