# Story Canvas

[English](./README.en.md) | [简体中文](./README.md)

Story Canvas is an agent-native story and visual workflow project. The current primary command entrypoint is `story-canvas`, with an early single-page UI acting as the visual shell.

It helps AI agents and authors work with structured story state instead of relying on a single giant prompt. The workflow separates prose, proposals, reviews, projection, local context refresh, and an expanding illustration layer, so long-form writing can evolve with clearer constraints and less state drift.

If you want the canonical end-to-end writing loop first, read [docs/guides/creative-workflow.md](./docs/guides/creative-workflow.md).

This repository currently provides:

- a file-based story protocol
- a Python CLI for state transitions
- tracked sample projects under `projects/`
- smoke-test fixtures and validated story baselines
- optional provider foundation for external SDK / API integrations
- provider-backed illustration generation capabilities
- commercial long-form samples with project-level positioning and serial-writing blueprint

It is not yet a full creative workstation, but it is no longer just a standalone CLI either. The current product surface combines the file protocol, the Python workflow entrypoint, and an early single-page UI; in the short term, the command workflow stays primary while image generation and UI move forward in parallel. See [docs/plans/story-canvas-parallel-roadmap.md](./docs/plans/story-canvas-parallel-roadmap.md).

## What It Solves

- Keep proposals separate from canon
- Turn chapter analysis into explicit review steps
- Update machine-readable projection only after a decision step
- Refresh a local writing context for the next loop
- Review both chapter-level and scene-level quality before stopping
- Manage fiction as an iterative engineering workflow instead of a single drafting pass

## Writing Capability Matrix

The current writing stack is no longer just `characters + chapters`. It already covers a practical constraint-driven loop, but the maturity level differs by area.

| Capability area | Current status | What is already implemented | Current gap |
|------|------|------|------|
| Project scaffold and repo-style layout | Implemented | `init` creates a fixed project skeleton, chapter files, protocol files, projections, reviews, and sample-friendly layout modes | initialization still happens through commands; there is no visual project bootstrap yet |
| Project-level writing contract | Implemented | `project.yaml` stores positioning, story contract, emotional contract, story template, and commercial positioning | still file/protocol oriented rather than a dedicated PRD workspace |
| Worldbook / entities / foreshadow / threads / timeline | Implemented | explicit state files exist for world constraints, character cards, foreshadow ledger, suspense threads, timeline, and causality | editing experience is still relatively raw without UI |
| Outline and detailed outline | Implemented | chapter direction, beats, scene plans, detailed outline init/show, and structure scaffolding are available | still depends on CLI commands and manual review |
| Pre-writing gate and structural checks | Implemented | `outline check`, `doctor`, `consistency check`, and workflow gates validate readiness before drafting | checks are heuristic and not a formal proof system |
| Drafting support | Partially implemented | prose stays in `chapters/*.md`, while `context refresh` provides local writing context from active characters, world rules, threads, and foreshadows | there is no dedicated editor or desktop drafting UI yet |
| Post-draft review and iteration loop | Implemented | `chapter analyze -> chapter suggest -> review apply -> projection apply -> context refresh -> review chapter/scene` already forms a closed loop | human review is still less convenient without Web UI |
| Human-readable export | Implemented | `export` supports clean manuscript output in multiple formats | publishing and polished release packaging are still separate concerns |
| Human review surface | Partially implemented | the protocol is inspectable and all outputs are persisted as files | review ergonomics are still a known gap, now moved into an earlier parallel UI track |
| Template richness and workflow freedom | Partially implemented | structure templates, style profiles, story template fields, and workflow state machine already exist | broader genre templates and freer workflow composition are planned for `v1.2` |
| Illustration and visual asset flow | Partially implemented | `illustration` commands, provider abstraction, and provider-backed image requests already exist | asset history, parameter reuse, bulk review, and a practical visual surface are still missing |

In short: the repository already has a usable "story engineering core" for constrained writing, review, projection, and export. What it still lacks is mainly interface polish, easier human review, and richer template packs.

Current release-boundary note:

- `v1.0.x` remains anchored on stable story protocol, workflow closure, and sample-backed regression
- illustration generation and early UI work are no longer fully postponed to `v1.1`; they move in parallel to reduce manual testing cost in fiction workflows
- `story-canvas` is now the primary CLI command, while `story-harness` stays as a legacy compatibility alias

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
uv run story-canvas init --root .\demo --title "Fog Harbor" --genre "Mystery"
```

For a real web-serial project, initialize the commercial blueprint at the same time instead of leaving it as afterthought metadata:

```powershell
uv run story-canvas init `
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

For a constraint-heavy long-form project, initialize the emotional contract and template policy up front so the later review loop has something concrete to consume:

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "归墟" `
  --genre "奇幻" `
  --primary-genre fantasy `
  --sub-genre xuanhuan `
  --core-promise "暗线逐步拼合并持续兑现世界真相" `
  --pace-contract "中快节奏，卷末集中爆发" `
  --core-emotion "压迫下反制" `
  --core-emotion "真相落地时的原来如此" `
  --chapter-emotion-floor "每章至少有一个明确情绪推进点" `
  --forbidden-emotion "空转讲设定" `
  --default-reveal-mode partial-inference `
  --allow-direct-explain-at-climax `
  --story-template-id xianxia-revenge-serial `
  --story-template-label "仙侠复仇长篇" `
  --module-policy worldbook=required `
  --module-policy worldRules=required `
  --module-policy factions=required `
  --module-policy foreshadowLedger=required `
  --module-policy characterStateTracking=required `
  --review-focus "世界规则兑现" `
  --review-focus "伏笔长回收"
```

This creates the normal project scaffold and also seeds:

- `project.emotionalContract`
- `project.storyTemplate`
- `worldbook.yaml`
- `foreshadowing.yaml`

Then edit `demo/chapters/chapter-001.md` and run:

```powershell
uv run story-canvas chapter analyze --root .\demo --chapter-id chapter-001
uv run story-canvas chapter suggest --root .\demo --chapter-id chapter-001
uv run story-canvas review apply --root .\demo --chapter-id chapter-001 --all-pending --decision accepted
uv run story-canvas projection apply --root .\demo --chapter-id chapter-001
uv run story-canvas context refresh --root .\demo --chapter-id chapter-001
uv run story-canvas review chapter --root .\demo --chapter-id chapter-001
uv run story-canvas outline scene-detect --root .\demo --chapter-id chapter-001
uv run story-canvas review scene --root .\demo --chapter-id chapter-001 --scene-index 1
uv run story-canvas doctor --root .\demo
```

Option B: run the validated short-story baseline

```powershell
uv run story-canvas doctor --root .\projects\demo-short-story
uv run story-canvas chapter analyze --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas chapter suggest --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review apply --root .\projects\demo-short-story --chapter-id chapter-001 --all-pending --decision accepted
uv run story-canvas projection apply --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas context refresh --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-short-story --chapter-id chapter-001 --scene-index 1
```

Option C: run the validated style-driven baseline

```powershell
uv run story-canvas doctor --root .\projects\demo-light-novel-short
uv run story-canvas chapter analyze --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-light-novel-short --chapter-id chapter-001 --scene-index 1
uv run story-canvas export --root .\projects\demo-light-novel-short --format markdown --output .\projects\demo-light-novel-short\manuscript.md
```

Option D: run the validated xuanhuan web-serial baseline

```powershell
uv run story-canvas doctor --root .\projects\demo-xuanhuan-short
uv run story-canvas chapter analyze --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
uv run story-canvas export --root .\projects\demo-xuanhuan-short --format markdown --output .\projects\demo-xuanhuan-short\manuscript.md
```

Repository fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas chapter analyze --root .\demo --chapter-id chapter-001
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

- `story-canvas init`
- `story-canvas brainstorm character|world|outline`
- `story-canvas chapter analyze`
- `story-canvas chapter suggest`
- `story-canvas review apply`
- `story-canvas review chapter`
- `story-canvas review scene`
- `story-canvas outline propose`
- `story-canvas outline promote`
- `story-canvas outline beat-add`
- `story-canvas outline beat-complete`
- `story-canvas outline beat-list`
- `story-canvas outline scene-add`
- `story-canvas outline scene-list`
- `story-canvas outline scene-detect`
- `story-canvas outline scene-update`
- `story-canvas outline scene-remove`
- `story-canvas outline detail-init`
- `story-canvas outline detail-show`
- `story-canvas projection apply`
- `story-canvas context refresh|show`
- `story-canvas entity enrich|review|list|show|graph`
- `story-canvas style check|constraints|report|repair`
- `story-canvas illustration prompt|generate|list|config`
- `story-canvas structure list|apply|show|check|map|scaffold`
- `story-canvas thread plant|resolve|list|check`
- `story-canvas foreshadow plant|resolve|list`
- `story-canvas arc define|milestone|list|check`
- `story-canvas workflow status|run|advance|reset|export`
- `story-canvas timeline add/list/check`
- `story-canvas causality add/list/check`
- `story-canvas search`
- `story-canvas consistency check`
- `story-canvas stats`
- `story-canvas migrate`
- `story-canvas export --format json|markdown|txt`
- `story-canvas doctor`

## Project Layout

- `src/story_canvas/` - public Python module and primary CLI entry wrapper
- `src/story_harness_cli/` - current internal owner for commands, protocol, and service implementation
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
- style repair guidance plus provider-backed illustration prompt, dry-run, real OpenAI text-to-image / image-to-image request flows, multi-asset persistence, and asset-state listing
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

- improve human review ergonomics for structured story state while the early UI track advances in parallel
- move illustration asset-management ergonomics into the Story Canvas visual surface instead of widening the `v1.0.x` CLI-only release scope
- deepen story-constraint consumption in review and workflow, especially worldbook, foreshadow payoff windows, and dynamic character state
- expand genre/template packs so different novel skeletons do not all depend on the same baseline assumptions
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
uv run story-canvas doctor --root .\projects\demo-short-story
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

