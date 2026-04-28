---
name: story-harness-writing
description: Structured Chinese fiction writing adapter for Codex. Use when Codex needs to plan, draft, revise, and review a long-form Chinese novel with the Story Canvas workflow. This skill combines writing-method guidance with CLI workflow routing, story-state awareness, volume closure, and quality gates.
---

# Story Canvas Writing

## Overview

Use this skill as the Codex writing adapter for the Story Canvas repository.

The repository remains the source of truth:

```text
<story-canvas-repo-root>
```

This skill is intentionally still a thin adapter:

1. it tells Codex how to write
2. it tells Codex which CLI workflow to run
3. it does not replace the repository protocol or invent a parallel state system

The closure is:

```text
external agent -> skill guidance -> story-canvas CLI -> protocol files
```

Before heavy drafting or review inside this repository, read:

1. `docs/guides/writing-rules.md`
2. `docs/guides/volume-self-review.md`
3. `docs/guides/creative-workflow.md`

## Layered Skill Use

Use this skill in two layers, not as one giant writing manual.

### Layer A: Universal Base

Always start with a small base rule set:

1. title promise
2. protagonist abnormal state
3. first-volume delivery
4. scene engine
5. chapter-level incremental progress

This layer is cross-genre and should be loaded first.

### Layer B: Genre Overlay

Only after genre / archetype / platform is clear, load one primary overlay:

1. male cultivation / web-serial power
2. female cultivation growth
3. urban supernatural
4. light novel romcom
5. western fantasy light novel
6. horror-game
7. historical power
8. post-apoc scifi
9. entertainment industry

Do not load multiple genre overlays unless the project genuinely mixes them and the user needs that blend.

### Progressive Disclosure

Reveal guidance in phases:

1. PRD stage:
   use universal base + a thin genre promise layer
2. outline stage:
   add first-volume delivery and chapter loop rules
3. chapter drafting stage:
   add scene-engine and beat-increment rules
4. review stage:
   add genre-specific high-risk checks

The rule is:

```text
base rules -> genre overlay -> phase overlay
```

Do not front-load all layers when the task only needs the first one.

### Chinese-First Prompting

For Chinese fiction projects:

1. keep prompt bodies in Chinese
2. keep review comments in Chinese
3. keep rewrite instructions in Chinese
4. keep examples in Chinese

English may still appear, but only as:

1. internal field aliases
2. code-facing identifiers
3. compatibility labels

Do not let English natural-language instructions become the main writing prompt for Chinese prose. That often pushes the output toward translated phrasing or an English reasoning skeleton.

## Core Principles

### Write Like a Novelist, Not a Form Filler

1. Show through action, reaction, and dialogue instead of abstract explanation.
2. Let conflict drive scenes; each chapter needs movement, pressure, or reversal.
3. End chapters with a reason to continue, but do not pile up mysteries without staged payoff.
4. Treat each volume as a small story unit, not just a bucket of chapters.

### Respect Story Truth Over Rigid Outline Execution

Detailed outlines are execution paths, not the highest truth source.

If a scene path conflicts with:

1. already established consequences
2. current world rules
3. character state
4. relationship logic
5. the current volume's required delivery

then preserve those truths first and adjust the scene path second.

Do not use “character growth” as an excuse to drift aimlessly. If a chapter bends the original path, it must still deliver the chapter and volume responsibility.

### Use the CLI as the Execution Layer

1. Prose and Markdown documents may be edited directly when needed.
2. Protocol YAML should preferably be created, updated, checked, and exported through `story-canvas` commands.
3. Do not treat “the agent can directly edit YAML” as the normal workflow.
4. If no CLI path exists yet and a manual protocol edit is unavoidable, record it as a tooling gap.

## What Good Output Looks Like

### At Chapter Level

Before writing, Codex should know:

1. previous chapter result
2. current chapter handoff point
3. current chapter delivery point
4. active world rules
5. active character state and relationship pressure
6. due foreshadows and entity constraints

After writing, Codex should not stop at prose completion. It must loop through analysis, review, revision, and re-check.

### At Volume Level

A finished volume should give:

1. a clear volume question
2. a staged escalation
3. at least one meaningful payoff or release
4. a partial closure that feels like a small story was delivered
5. a remaining tail for the larger novel

高潮不等于闭环。 If the volume only escalates but does not deliver a small-story closure, it is not done.

## Anti-Patterns To Avoid

### Do Not Write Like This

1. Do not translate outline bullets directly into prose.
2. Do not keep stacking mysteries just to simulate suspense.
3. Do not let the entire opening volume stay only in suppression and never in release.
4. Do not leak chapter/volume/outline/workflow language into prose.
5. Do not write information the current POV cannot perceive or reasonably infer.

### High-Risk AI Style Habits

Limit repeated use of these expression skeletons:

1. `不是……是……`
2. `不是……不是……是……`
3. `不是……更像……`
4. high-frequency `像……`
5. `不重/不轻/不偏/不倚`
6. `真正……的，从来都是……`
7. half-question dialogue like `还有什么？`

These are not absolutely forbidden, but if they become the chapter’s dominant habit, the text starts sounding synthetic.

Also avoid:

1. abstract reaction ladders
2. fake-profound phrasing
3. proposal-document tone
4. summary-first narration

## Workflow Decision Tree

### If `story-canvas` is not installed or not executable

Use the repository fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas <command> ...
```

Legacy compatibility note: `story-harness` and `python -m story_harness_cli` still work, but they are no longer the primary entrypoints.

### If no story project exists yet

Use the repository workflow instead of creating an external parallel folder system.

Suggested order:

1. create or update `PRD.md`
2. initialize the project
3. establish outline and story state through CLI

```powershell
uv run story-canvas init --root <project-dir> --title "<title>" --genre "<genre>" --layout layered
```

For long-form novels, prefer layered layout.

### If the user is still shaping the book

Use a planning-first path:

1. clarify premise, hook, target readers, core experience
2. clarify volume responsibility
3. clarify opening-world onboarding and first-volume payoff
4. only then enter detailed outline and chapter work

Recommended CLI path:

```powershell
uv run story-canvas brainstorm outline --root <project-dir> --prompt "<idea>"
uv run story-canvas outline propose --root <project-dir> --mode chapter --chapter-id <chapter-id> --title "<title>" --summary "<summary>" --prompt "<prompt>"
uv run story-canvas outline promote --root <project-dir> --proposal-id <proposal-id> --chapter-id <chapter-id>
```

If `PRD.md` is missing, add or update it before heavy drafting.

### If the user wants a single-chapter writing loop

Run:

```powershell
uv run story-canvas chapter analyze --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas chapter suggest --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas review apply --root <project-dir> --all-pending --decision accepted --chapter-id <chapter-id>
uv run story-canvas projection apply --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas context refresh --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas review chapter --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas review scene --root <project-dir> --chapter-id <chapter-id> --list-scenes
```

If review is weak, revise prose and run the loop again. Do not stop at the first score.

### If the user wants a full volume writing-and-review loop

Use this path:

```text
define volume responsibility
  -> write / revise chapter prose
  -> chapter analyze
  -> chapter suggest
  -> review apply
  -> projection apply
  -> context refresh
  -> review chapter
  -> review scene
  -> revise if weak
  -> repeat until chapter acceptable
  -> continue until the whole volume reaches small-story closure
  -> export volume packet
  -> AI volume self-review
  -> independent editor pass
  -> targeted revision
  -> re-check
  -> hand off to human review
```

If the user explicitly wants uninterrupted full-run drafting, do not stop mid-volume unless:

1. the user interrupts
2. the repository workflow blocks
3. a true contradiction or missing requirement makes continuation unsafe

### Independent Editor Pass

For volume review, do not let the same drafting context both self-review and score itself if the host supports an independent path.

Default requirement:

1. run `review volume-self-template`
2. create a second pass in a no-context proxy / fresh thread / independent editor channel
3. let that pass read the volume packet and necessary CLI outputs first, not the earlier self-review conclusion
4. make it produce its own scores, comments, top problems, and improvement points
5. only then compare:
   - what the CLI already detected
   - what the first self-review noticed
   - what the independent editor still found

Preferred isolation order:

1. subagent with no prior drafting context
2. fresh thread
3. human editor
4. same agent fallback with explicit disclosure

If the host supports subagents, use one for the independent editor pass.

Minimum evidence bundle for that pass:

1. `review volume-self-template --root <project-dir> --volume-id <volume-id>`
2. `export --root <project-dir> --format review-packet --volume-id <volume-id>`
3. `style report --root <project-dir> --volume-id <volume-id>`
4. targeted `style check` / `review chapter` / `review scene` outputs for cited chapters or scenes

Do not allow `allowHumanReview=true` unless the independent editor pass is attached.

### If the user wants foreshadow tracking

```powershell
uv run story-canvas foreshadow plant --root <project-dir> --description "<伏笔描述>" --chapter-id <chapter-id> --planned-payoff <payoff-chapter-id>
uv run story-canvas foreshadow resolve --root <project-dir> --foreshadow-id <fs-id> --payoff-chapter <chapter-id>
uv run story-canvas foreshadow list --root <project-dir>
```

Do not manually edit `foreshadowing.yaml`.

### If the user wants structure review or human-readable review material

```powershell
uv run story-canvas export --root <project-dir> --format spec-outline --output <path>.md
uv run story-canvas export --root <project-dir> --format spec-characters --output <path>.md
uv run story-canvas export --root <project-dir> --format markdown --output <path>.md
```

Prefer exported review material over raw protocol browsing where possible.

## Operational Rules

1. Treat `chapters/*.md` as prose and `*.yaml` as machine-facing state.
2. Prefer repo-native commands for YAML changes.
3. Use `review chapter` and `review scene` as quality gates, not optional reports.
4. Read `project.yaml`, `context-lens.yaml`, and the relevant outline before drafting.
5. Use explicit `@{实体}` for key canon entities in normal narration when appropriate.
6. Do not mechanically force wrapped tags into quoted aliases or emotional address terms.
7. If `scenePlans` exist, treat them as canonical scene boundaries before heuristic splits.
8. If a project uses layered layout, read spec files in `spec/`.
9. Prefer `chapter create` over directly editing `project.yaml` or `outline.yaml` when moving into a new chapter.
10. If a CLI path is missing and manual protocol edits are unavoidable, surface that as a tooling gap after the writing pass.
11. During volume review, every major issue should explain:
    - why tooling missed it
    - why self-review missed it
    - what rule, prompt, or re-check step should be improved
12. During volume review, record which commands or rule ids already detected the issue whenever possible.

## Core Files

Read [references/protocol.md](./references/protocol.md) for file layout and state semantics.

The most important files in practice are:

1. `project.yaml`
2. `PRD.md` when present
3. `outline.yaml` or `spec/outline.yaml`
4. `entities.yaml` or `spec/entities.yaml`
5. `foreshadowing.yaml` or `spec/foreshadowing.yaml`
6. `chapters/*.md`
7. `reviews/story-reviews.yaml`
8. `projections/context-lens.yaml`
9. `workflow.yaml` when present

## Recommended Agent Behavior

1. Read repository writing rules first, not just the chapter title.
2. Read `docs/guides/writing-rules.md` before drafting.
3. Read `docs/guides/volume-self-review.md` before any volume-level handoff.
4. Read `context-lens.yaml` first if it exists.
5. Read `project.yaml`, especially positioning, story contract, and commercial positioning.
6. Read the relevant outline and current chapter state.
7. Draft or revise prose.
8. Route all stateful workflow actions through `uv run story-canvas ...`.
9. Run review and continue revising until the weakest dimensions no longer contradict the story contract or current volume duty.
10. Summarize:
   - accepted strengths
   - top risks
   - missing payoff
   - tooling gaps
   - next-step context

## Stop Conditions

You may stop after one pass only when at least one of the following is true:

1. the user explicitly asked for a single pass
2. the current chapter or volume is already acceptable for its target
3. remaining weaknesses are explicitly called out as accepted risk

For full-run volume work, do not stop just because a single chapter was written. Stop only when:

1. the volume reached explicit pause or closure criteria
2. the user asked to pause
3. a real blocker prevents safe continuation

## Validation

Use the repository for validation:

```powershell
uv run story-canvas --help
uv run python -m unittest discover -s tests
```
