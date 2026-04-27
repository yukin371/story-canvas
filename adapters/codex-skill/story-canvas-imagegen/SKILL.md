---
name: story-canvas-imagegen
description: Thin Story Canvas image generation adapter for Codex. Use when Codex needs to export illustration batch manifests, generate images through WebUI-manual or external-agent mode, and record outputs back into the project.
---

# Story Canvas Image Generation

## Overview

Use this skill as the Codex image-generation adapter for the Story Canvas repository.

The repository remains the source of truth:

```text
story-canvas CLI -> batch manifest -> generated files -> illustrations.yaml
```

This skill stays thin:

1. it decides whether to use `webui-manual` or `external-agent`
2. it routes image work through `story-canvas illustration ...`
3. it does not invent a parallel image job database or write `illustrations.yaml` directly

## Decision Rule

Use:

1. `illustration generate`
   when the request is a single image and direct provider generation is acceptable
2. `illustration batch-export`
   when the user wants multiple chapter/entity images, or wants WebUI / external-agent generation

## Two Delivery Modes

### `webui-manual`

Use this when a human will copy prompt / negative prompt into a local WebUI.

Flow:

1. export manifest
2. open manifest and read each job's `delivery.prompt`, `negativePrompt`, `size`, `outputFiles`
3. generate images manually in WebUI
4. write final files to the declared `outputFiles`
5. run `illustration batch-record`

### `external-agent`

Use this when Codex itself or another external image agent should execute the generation.

Flow:

1. export manifest with `--delivery-mode external-agent`
2. read each job's `delivery` block
3. generate the image and write it to `outputFiles`
4. run `illustration batch-record`

Important:

1. the external agent may generate files
2. only `story-canvas illustration batch-record` should import them into project history

## Rules

1. Prefer the repository CLI over direct YAML edits.
2. Treat batch manifests as derived artifacts, not long-term state.
3. Do not change manifest structure inside the skill.
4. Do not bypass `batch-record`.

## References

Read [references/cli.md](./references/cli.md) for the exact commands.

## Validation

Use:

```powershell
uv run story-canvas illustration batch-export --help
uv run story-canvas illustration batch-record --help
uv run python -m unittest tests.smoke.test_illustration_command
```
