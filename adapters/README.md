# Adapters

This directory stores host-specific adapters for the Story Canvas workflow core.

The current adapters are no longer just thin “which command to run” notes.

`story-harness-writing` intentionally combines:

1. Chinese fiction writing guidance
2. Story Canvas workflow routing
3. protocol-bound execution rules

Even after that integration, the adapters must stay thin in one important sense:

- they teach the agent how to write and how to use the CLI
- they do not become a second source of truth beside the repository protocol

Current rule:

1. the CLI repository owns adapter source
2. local installed skills are treated as deployed copies
3. adapters must stay thin and delegate execution to `story-canvas`

Current hosts:

1. `codex-skill/`
2. `claude-code/`

Current adapter families:

1. `story-harness-writing`: long-form writing workflow
2. `story-canvas-imagegen`: illustration batch manifest consumption for WebUI / external agent image generation

Each adapter should explain:

1. when to invoke the CLI
2. which protocol files matter
3. which commands correspond to the writing loop
4. what the complete close-the-loop workflow is after scoring
5. which fallback command path to use when `story-canvas` is unavailable
6. how to write within the repository's actual story-quality constraints
7. which actions should prefer repo-native CLI over direct YAML editing

Canonical writing-quality references live in the repository guides:

1. `docs/guides/writing-rules.md`
2. `docs/guides/volume-self-review.md`
3. `docs/guides/creative-workflow.md`

Install adapters with:

```powershell
uv run python scripts/install_adapter.py --host codex --force
uv run python scripts/install_adapter.py --host claude --workspace <workspace-root> --force
uv run python scripts/install_adapters.py --workspace <workspace-root> --force
uv run python scripts/install_adapter.py --host codex --skill-name story-canvas-imagegen --force
```

Rules:

1. Codex installs to `~/.codex/skills/<skill-name>` by default.
2. Claude installs to `<workspace>/.claude/skills/<skill-name>` by default.
3. Use `--target-dir` to override the default target.
4. Use `--dry-run` to inspect the resolved source and target without copying files.
5. `install_adapters.py` defaults to `codex` only, or `codex + claude` when `--workspace` is provided.
