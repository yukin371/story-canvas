# Story Harness CLI

Story Harness CLI is an agent-native fiction workflow tool for long-form narrative writing.

It helps AI agents and authors work with structured story state instead of relying on a single giant prompt. The workflow separates prose, proposals, reviews, projection, and local context refresh, so long-form writing can evolve with clearer constraints and less state drift.

If you want the canonical end-to-end writing loop first, read [docs/guides/creative-workflow.md](./docs/guides/creative-workflow.md).

This repository currently provides:

- a file-based story protocol
- a Python CLI for state transitions
- tracked sample projects under `projects/`
- smoke-test fixtures and validated story baselines
- optional provider foundation for external SDK / API integrations
- commercial long-form samples with project-level positioning and serial-writing blueprint

It does not aim to replace a writing UI. Instead, it provides the protocol and workflow core that different skills, editors, and future interfaces can reuse.

## What It Solves

- Keep proposals separate from canon
- Turn chapter analysis into explicit review steps
- Update machine-readable projection only after a decision step
- Refresh a local writing context for the next loop
- Review both chapter-level and scene-level quality before stopping
- Manage fiction as an iterative engineering workflow instead of a single drafting pass

## Core Model

The current workflow uses these layers:

1. `chapters/*.md` for prose
2. `proposals/draft-proposals.yaml` for write-before-canon proposals
3. `reviews/change-requests.yaml` for write-after-analysis suggestions
4. `projections/projection.yaml` for current machine-facing truth
5. `projections/context-lens.yaml` for local chapter context

## Quickstart

Option A: initialize a new project

```powershell
uv sync
uv run story-harness init --root .\demo --title "Fog Harbor" --genre "Mystery"
```

For a real web-serial project, initialize the commercial blueprint at the same time instead of leaving it as afterthought metadata:

```powershell
uv run story-harness init `
  --root .\demo `
  --title "夜巡收煞录" `
  --genre "奇幻" `
  --primary-genre fantasy `
  --sub-genre urban-occult `
  --style-tag web-serial `
  --target-audience qidian-reader `
  --core-promise "每章结尾保留追读钩子" `
  --pace-contract "中快节奏" `
  --premise "夜班接尸人继承城隍夜巡牌，处理都市异案并追查失踪父亲真相" `
  --hook-line "接尸抬到空棺的当夜，他被迫上岗做城隍夜巡。" `
  --hook-stack career-entry-hook `
  --hook-stack cliffhanger-end `
  --target-platform qidian `
  --serialization-model "2到3章一个单元异案，持续抬升主线阴谋" `
  --release-cadence "日更两章" `
  --chapter-word-floor 2000 `
  --chapter-word-target 3000
```

Then edit `demo/chapters/chapter-001.md` and run:

```powershell
uv run story-harness chapter analyze --root .\demo --chapter-id chapter-001
uv run story-harness chapter suggest --root .\demo --chapter-id chapter-001
uv run story-harness review apply --root .\demo --chapter-id chapter-001 --all-pending --decision accepted
uv run story-harness projection apply --root .\demo --chapter-id chapter-001
uv run story-harness context refresh --root .\demo --chapter-id chapter-001
uv run story-harness review chapter --root .\demo --chapter-id chapter-001
uv run story-harness outline scene-detect --root .\demo --chapter-id chapter-001
uv run story-harness review scene --root .\demo --chapter-id chapter-001 --scene-index 1
uv run story-harness doctor --root .\demo
```

Option B: run the validated short-story baseline

```powershell
uv run story-harness doctor --root .\projects\demo-short-story
uv run story-harness chapter analyze --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-harness chapter suggest --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-harness review apply --root .\projects\demo-short-story --chapter-id chapter-001 --all-pending --decision accepted
uv run story-harness projection apply --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-harness context refresh --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-harness review chapter --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-harness review scene --root .\projects\demo-short-story --chapter-id chapter-001 --scene-index 1
```

Option C: run the validated style-driven baseline

```powershell
uv run story-harness doctor --root .\projects\demo-light-novel-short
uv run story-harness chapter analyze --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-harness review chapter --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-harness review scene --root .\projects\demo-light-novel-short --chapter-id chapter-001 --scene-index 1
uv run story-harness export --root .\projects\demo-light-novel-short --format markdown --output .\projects\demo-light-novel-short\manuscript.md
```

Option D: run the validated xuanhuan web-serial baseline

```powershell
uv run story-harness doctor --root .\projects\demo-xuanhuan-short
uv run story-harness chapter analyze --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-harness review chapter --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-harness review scene --root .\projects\demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
uv run story-harness export --root .\projects\demo-xuanhuan-short --format markdown --output .\projects\demo-xuanhuan-short\manuscript.md
```

Repository fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_harness_cli chapter analyze --root .\demo --chapter-id chapter-001
```

Use `demo-short-story` when you want a genre-neutral regression baseline. Use `demo-light-novel-short` when you want to verify that `subGenre`, `styleTags`, and `targetAudience` survive the review loop. Use `demo-xuanhuan-short` when you want to verify `xuanhuan + web-serial` weighting and short-form progression pacing. For the current sample catalog, see [docs/guides/sample-matrix.md](./docs/guides/sample-matrix.md).

Use `demo-urban-occult-long` when you want a more realistic commercial-serial baseline with explicit `commercialPositioning`, volume skeleton, and chapter word targets.

For the full close-the-loop sequence and stop conditions, see [docs/guides/creative-workflow.md](./docs/guides/creative-workflow.md) and [docs/guides/quickstart.md](./docs/guides/quickstart.md).

## Example Workflow

Single chapter loop:

```text
chapter.md
  -> chapter analyze
  -> chapter suggest
  -> review apply
  -> projection apply
  -> context refresh
  -> review chapter
  -> scene detect / maintain scenePlans
  -> review scene
  -> revise prose or scene plan if score is weak
  -> repeat until acceptable
```

Outline loop:

```text
goal or reasoning
  -> outline propose
  -> outline promote
  -> projection apply
```

## Command Overview

- `story-harness init`
- `story-harness brainstorm character|world|outline`
- `story-harness chapter analyze`
- `story-harness chapter suggest`
- `story-harness review apply`
- `story-harness review chapter`
- `story-harness review scene`
- `story-harness outline propose`
- `story-harness outline promote`
- `story-harness outline beat-add`
- `story-harness outline beat-complete`
- `story-harness outline beat-list`
- `story-harness outline scene-add`
- `story-harness outline scene-list`
- `story-harness outline scene-detect`
- `story-harness outline scene-update`
- `story-harness outline scene-remove`
- `story-harness outline detail-init`
- `story-harness outline detail-show`
- `story-harness projection apply`
- `story-harness context refresh|show`
- `story-harness entity enrich|review|list|show|graph`
- `story-harness style check|constraints|report|repair`
- `story-harness illustration prompt|generate|list|config`
- `story-harness structure list|apply|show|check|map|scaffold`
- `story-harness thread plant|resolve|list|check`
- `story-harness foreshadow plant|resolve|list`
- `story-harness arc define|milestone|list|check`
- `story-harness workflow status|run|advance|reset|export`
- `story-harness timeline add/list/check`
- `story-harness causality add/list/check`
- `story-harness search`
- `story-harness consistency check`
- `story-harness stats`
- `story-harness migrate`
- `story-harness export --format json|markdown|txt`
- `story-harness doctor`

## Project Layout

- `src/story_harness_cli/` - CLI implementation
- `adapters/` - host-specific adapter sources for Codex, Claude Code, and future hosts
- `scripts/install_adapter.py` - install a host adapter into Codex or Claude skill directories
- `scripts/install_adapters.py` - batch-install adapters for multiple hosts
- `docs/` - protocol and guide docs
- `projects/` - tracked sample projects and regression baselines
- `tests/` - smoke tests and fixtures

## Implemented Features

The current implementation already covers:

- layered file protocol for prose, proposals, reviews, projections, and context
- chapter analysis, suggestion generation, and explicit review-then-apply workflow
- chapter review, scene review, and style review with profile-driven constraints
- style repair guidance plus illustration prompt, dry-run, real OpenAI text-to-image / image-to-image request flows, multi-asset persistence, and asset-state listing
- outline-first gating, beat tracking, scene plan maintenance, and detailed outline helpers
- project positioning, story contract, and commercial serial blueprint validation
- timeline, causality, suspense thread, foreshadow, structure, and character-arc tracking
- entity enrichment, review, listing, and relationship graph export
- workflow stage inference, persisted `workflow.yaml`, gate decisions, reset/export, and `run --resume-from` rewind support
- project stats, cross-chapter search, consistency check, and layered-layout migration
- tracked sample projects in `projects/` covering short-form, style-driven, xuanhuan, and commercial long-form baselines
- optional dependency boundary for provider-backed capabilities, while keeping base install stdlib-only

## Improvement Directions

The next round should stay focused on a small set of practical gaps:

- stabilize the provider layer with one or two real integrations beyond the current foundation
- externalize more algorithm, dictionary, and prompt resources while keeping builtin fallback paths
- harden schema and workflow validation for richer long-form state, especially graph, thread, and structure semantics
- keep expanding `projects/` sample coverage so regression baselines represent more commercial genres and production workflows
- prepare release and distribution work once command contracts and sample baselines stop moving

## Development

Sync the environment:

```powershell
uv sync
```

Run smoke tests:

```powershell
uv run python -m unittest discover -s tests
```

Run structural validation against a story project:

```powershell
uv run story-harness doctor --root .\projects\demo-short-story
```

Install a host adapter:

```powershell
uv run python scripts/install_adapter.py --host codex --force
uv run python scripts/install_adapter.py --host claude --workspace <workspace-root> --force
```

Install multiple adapters in one shot:

```powershell
uv run python scripts/install_adapters.py --workspace <workspace-root> --force
```

Contributor and release docs:

- `CONTRIBUTING.md`
- `docs/guides/creative-workflow.md`
- `docs/guides/quickstart.md`
- `docs/guides/sample-matrix.md`
- `docs/guides/releasing.md`

## Roadmap

- Stabilize provider-backed extension points and optional dependency packaging
- Expand sample-project baselines under `projects/` and keep them aligned with smoke coverage
- Add deeper schema validation for graph, thread, structure, and commercial workflow semantics
- Validate richer production workflows against real long-form projects
- Revisit distribution strategy only after the Python CLI contract is stable
