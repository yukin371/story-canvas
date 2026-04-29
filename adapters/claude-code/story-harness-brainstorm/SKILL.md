---
name: story-harness-brainstorm
description: "Pre-project Chinese fiction brainstorming adapter for Claude Code. Use when Claude Code needs to explore raw story ideas before a Story Canvas project exists: premise discovery, hook finding, protagonist abnormal state, serial-loop design, first-volume promise, direction comparison, and PRD seed drafting. Use this skill when the user is still exploring and does not yet need chapter drafting, project-state workflow gates, or illustration generation."
---

# Story Canvas Brainstorm

Use this skill before project creation.

This skill is intentionally separate from:

1. `story-harness-writing`
2. `story-canvas-imagegen`

Goal:

1. explore ideas
2. narrow options
3. draft one `PRD seed`
4. stop before project-state execution

## Read Order

Always read:

1. `references/brainstorm-loop.md`

Read `references/prd-seed-contract.md` only when:

1. the user wants to converge
2. you need to turn exploration into a usable brief
3. you are handing off to `story-harness-writing` or `story-canvas init`

Read `references/question-packs.md` only when:

1. the user's spark is too vague
2. you need sharper follow-up questions
3. you need to branch by story type without writing a giant custom prompt

Read `references/direction-comparison.md` only when:

1. there are multiple viable directions
2. you need to compare them instead of averaging them
3. you need to decide which direction to kill

Read `references/challenger-pass.md` only when:

1. the host supports subagents or fresh threads
2. you want one independent challenger before convergence
3. the leading direction still feels under-tested

Read `references/classic-genre-tags.md` only when:

1. the user asks for classic genres or tags
2. you need a starting vocabulary for genre combination
3. you need to branch ideation by broad category before a project exists

## Operating Mode

Start with exploration, then converge.

Default loop:

1. identify the smallest usable spark
2. expand `2-4` materially different directions
3. compare why each one may sustain pursuit
4. pressure-test protagonist, conflict, and serial loop
5. converge into one `PRD seed`

Keep the session exploratory, but not vague.

If the host supports subagents or a fresh thread, use one optional challenger pass before final convergence when the user wants stronger exploration quality.

The challenger pass should:

1. see the current spark and current leading direction
2. propose one stronger alternative or one fatal weakness
3. avoid inheriting your full drafting bias
4. return a compact structured verdict, not a second sprawling brainstorm

## Brainstorm Policy

Prefer:

1. concrete reader-facing appeal
2. protagonist abnormal state
3. repeatable chapter engine
4. first-volume deliverable
5. larger board that connects after the early chapters

## Handoff Rule

When the idea is stable enough, hand off in one of two directions:

1. if the user still wants project-free exploration, stop at `PRD seed`
2. if the user wants execution, switch to `story-harness-writing` and then initialize a real project

## Completion Rule

When you finish a pass, report:

```text
Spark:
Candidate directions:
Chosen direction:
PRD seed status:
Open questions:
Suggested next step:
```
