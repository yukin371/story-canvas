# Adapters

This directory stores host-specific adapters for the Story Canvas workflow core.

Read [ADAPTER_ARCHITECTURE.md](./ADAPTER_ARCHITECTURE.md) first for the current layered design.

## Current Design

Adapters are organized by:

1. host
2. skill family
3. internal layer

Current hosts:

1. `codex-skill/`
2. `claude-code/`

Current skill families:

1. `story-harness-brainstorm`
2. `story-harness-writing`
3. `story-canvas-imagegen`

## Brainstorm Skill Position

`story-harness-brainstorm` is the pre-project exploration skill family.

Use it when the user is still exploring:

1. premise candidates
2. hook directions
3. protagonist abnormal state
4. repeatable chapter engine
5. first-volume promise
6. one `PRD seed` before `init`

It should stop at:

1. ideation notes
2. narrowed directions
3. one usable `PRD seed`

It should not assume a project already exists, and it should not invent project-state files by itself.

## Writing Skill Layers

`story-harness-writing` is no longer treated as a single flat writing manual.

It should be read in layers:

1. universal writing base
2. workflow gates
3. genre / tag overlays

The universal layer now covers:

1. prose craft
2. character engine
3. chapter planning grain
4. hook design and payout rhythm

For character-card shaping and chapter/scene planning translation, use:

1. `references/planning-primitives.md`

The top-level `SKILL.md` should stay focused on:

1. trigger conditions
2. loading order
3. host-specific execution notes
4. mandatory workflow gates

Detailed material should live in `references/`.

## Image Skill Position

`story-canvas-imagegen` is a separate skill family, not just an appendix of the writing skill.

It must support two participation modes:

1. CLI-only / external-agent mode
2. human-assisted `webui-manual` mode

WebUI is optional participation infrastructure. It is not a required dependency for the main workflow and it is not a new source of truth.

## Adapter Invariants

1. the CLI repository owns adapter source
2. local installed skills are deployed copies
3. adapters stay thin and delegate execution to `story-canvas`
4. adapters may integrate writing methodology, but may not introduce a parallel state system
5. writing quality rules belong to repository guides and repo-owned references, not to host-only folklore

Canonical writing-quality references live in the repository guides:

1. `docs/guides/writing-rules.md`
2. `docs/guides/volume-self-review.md`
3. `docs/guides/creative-workflow.md`

Install adapters with:

```powershell
uv run python scripts/install_adapter.py --host codex --force
uv run python scripts/install_adapter.py --host claude --workspace <workspace-root> --force
uv run python scripts/install_adapters.py --workspace <workspace-root> --force
uv run python scripts/install_adapter.py --host codex --skill-name story-harness-brainstorm --force
uv run python scripts/install_adapter.py --host codex --skill-name story-canvas-imagegen --force
```

Rules:

1. Codex installs to `~/.codex/skills/<skill-name>` by default.
2. Claude installs to `<workspace>/.claude/skills/<skill-name>` by default.
3. Use `--target-dir` to override the default target.
4. Use `--dry-run` to inspect the resolved source and target without copying files.
5. `install_adapters.py` defaults to `codex` only, or `codex + claude` when `--workspace` is provided.
