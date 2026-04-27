# Story Canvas Parallel Roadmap

This document defines the parallel development track that moves the project from a CLI-first fiction workflow tool toward a broader story-and-visual creation surface.

Current product direction:

- product name: `Story Canvas`
- current package / CLI continuity: keep Python package `story_harness_cli` and command `story-harness` for now
- short-term scope: strengthen the core protocol and provider layer while introducing an early visual surface for high-friction workflows

## Why Parallel Development

Manual validation is currently too expensive in the novel-generation loop. The biggest time sinks are no longer only prompt quality or protocol completeness; they are repeated human inspection, asset lookup, reruns, and illustration-side trial-and-error.

Because of that, image generation and UI should not wait until all fiction workflow details are "done". They should evolve in parallel with the writing loop so they can reduce operator cost early.

## Track A: Story Core

Goal: keep the writing protocol and CLI stable enough to remain the source of truth.

Deliverables:

- keep chapter analyze / suggest / review / projection / context refresh stable
- continue tightening structured state files and review outputs
- preserve smoke-test baselines for short-story and serial-writing samples
- keep CLI as the most scriptable and regression-friendly interface

Exit criteria:

- baseline projects remain replayable
- core state transitions stay backward-compatible within the `v1.x` line
- story review loops remain usable without the UI

## Track B: Image Generation

Goal: make illustration generation a first-class, provider-backed capability instead of a side extension.

Deliverables:

- stable text-to-image flow
- stable image-to-image flow
- mask-guided edit support
- provider config that supports official OpenAI by default and third-party compatible gateways by override
- persisted output records including prompt, revised prompt, response id, provider request, and saved artifact paths
- later additions: partial image save, output format control, background control, history reuse

Exit criteria:

- a project can generate and re-generate illustration assets from structured story context
- generated assets are persisted and traceable
- provider behavior is testable through smoke coverage and dry-run inspection

## Track C: Early UI

Goal: reduce manual testing cost before the project is ready for a "full studio" positioning.

Phase 1 UI scope:

- project chooser / active project surface
- chapter list and chapter detail surface
- illustration generation panel
- generated asset preview and history
- rerun from previous prompt / settings
- basic provider configuration surface

Phase 2 UI scope:

- review packet browsing
- pending change-request triage
- context-lens inspection
- scene-level review navigation

Explicit non-goals for the first UI cut:

- full prose editor replacement
- complex multi-user collaboration
- full comic page layout tooling

Exit criteria:

- the most common manual test steps no longer require repeated shell commands and file hopping
- illustration preview / rerun / output inspection become materially faster than CLI-only flow

## Versioning Direction

- `v1.0.x`: keep CLI and protocol as release anchor, but allow illustration and UI groundwork to move in parallel
- `v1.1`: no longer framed as "first UI ever"; instead framed as the first public visual surface for Story Canvas
- `v1.2+`: expand template richness, visual review ergonomics, and cross-media workflows such as storyboard / comic-oriented support

## Naming Migration

- repository target name: `story-canvas`
- public product name: `Story Canvas`
- keep `story-harness` CLI command during the transition window
- defer Python package rename until API and adapter migration costs are justified

## Current Progress Snapshot

1. Repository and product-facing docs have been moved to `Story Canvas`, while keeping `story-harness` CLI and `story_harness_cli` package continuity.
2. Illustration provider flow has moved to `Responses API + image_generation`, with official OpenAI as the default path and gateway compatibility via `base_url`.
3. The first local UI skeleton is in place with `Vue 3 + Vite + TDesign`.
4. Local API wiring now exposes project list, project summary, chapter/review data, and illustration dry-run for the UI.

## Immediate Next Steps

1. Turn illustration dry-run into real generate / save / history-refresh actions in the UI.
2. Add a lightweight provider settings surface so official key and compatible gateway config are manageable without hand-editing files.
3. Expose review packet, context lens, and change-request browsing in the UI to reduce novel QA time further.
4. Decide how the early UI should ship in `v1.0.x`: hidden preview feature, documented local companion, or explicit experimental surface.
