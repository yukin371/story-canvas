# Protocol

This Claude Code adapter follows the Story Canvas file protocol.

## Flat Layout (default, for short projects < 5万字)

```text
story-project/
  project.yaml
  outline.yaml
  entities.yaml
  timeline.yaml
  branches.yaml
  threads.yaml
  structures.yaml
  foreshadowing.yaml
  chapters/
    chapter-001.md
  proposals/
    draft-proposals.yaml
  reviews/
    change-requests.yaml
    story-reviews.yaml
  projections/
    projection.yaml
    context-lens.yaml
  logs/
    latest-analysis.yaml
    projection-log.yaml
```

## Layered Layout (for long novels >= 5万字, use `--layout layered`)

```text
story-project/
  project.yaml                     # stays at root
  branches.yaml                    # stays at root
  spec/                            # spec-eligible files
    outline.yaml                   # thin index (volume id + title)
    outlines/
      vol-001.yaml                 # volume details + chapters
      vol-002.yaml
    entities.yaml
    timeline.yaml
    threads.yaml
    structures.yaml
    foreshadowing.yaml             # foreshadow → callback pairs
  chapters/
    chapter-001.md                 # stays at root
  proposals/
    draft-proposals.yaml
  reviews/
    change-requests.yaml
    story-reviews.yaml
  projections/
    projection.yaml
    context-lens.yaml
  logs/
    latest-analysis.yaml
    projection-log.yaml
```

Layout is auto-detected: if `spec/` directory exists, layered paths are used. No manual configuration needed.

## Key Constraints

1. `Draft Proposal` is not canon.
2. `Change Request` is not canon.
3. `Projection` only consumes accepted or applied inputs.
4. `Context Lens` is derived from projection and recent analysis.
5. `reviews/story-reviews.yaml` stores both chapter-level and scene-level review outputs.
6. `outline.yaml` may contain explicit `scenePlans`, and `review scene --scene-index` should prefer them.
7. In layered layout, `spec/outline.yaml` is a thin index; per-volume chapters live in `spec/outlines/vol-NNN.yaml`.
8. Context refresh in layered layout only loads the active volume's outline, saving AI context tokens.
9. `detailed_outlines.yaml` stores per-chapter direction, beats, and scenePlans separately from the global outline.
10. Use `outline detail-init` to create a detailed plan for a chapter, and `outline detail-show` to view it.

## Outline Hierarchy

The outline system has two levels:

1. **Global outline** (`outline.yaml`): volumes, chapter index (id, title, status), major arcs. This is the "architecture" — locked early.
2. **Detailed outlines** (`detailed_outlines.yaml`): per-chapter direction, beats, scenePlans. This is the "sprint plan" — created progressively.

On load, detailed entries are merged into outline chapters transparently. All existing commands work with the merged view.

## New Commands

| Command | Purpose |
|---------|---------|
| `foreshadow plant` | Plant a foreshadow setup |
| `foreshadow resolve` | Mark a foreshadow as resolved |
| `foreshadow list` | List foreshadows (filter by status) |
| `migrate --root <path>` | Convert flat layout to layered |
| `export --format spec-outline` | Human-readable outline as Markdown |
| `export --format spec-characters` | Human-readable character cards as Markdown |
| `init --layout layered` | Create project with layered file structure |
| `outline detail-init` | Initialize detailed outline for a chapter |
| `outline detail-show` | Show detailed outline for a chapter |

## Chinese Prose Guidance

1. Use `@{实体}` in continuous Chinese prose.
2. Use `@entity` when the mention is already delimited by whitespace or punctuation.

## Protocol Docs

For repository-owned protocol docs, read:

1. `docs/protocol/overview.md`
2. `docs/protocol/file-layout.md`
3. `docs/protocol/lifecycle.md`
