# Contributing

## Development Environment

```powershell
uv sync
```

The current repository keeps the Python workflow core stdlib-first on Python 3.10+ so iteration stays fast and packaging stays simple, while the early UI remains a separate shell over the same file protocol.

## Common Commands

```powershell
uv run story-canvas --help
uv run story-canvas doctor --root .\examples\minimal-project
uv run python -m unittest discover -s tests
```

## Enable Local Git Hooks

The repository ships hook templates under `.githooks/`, but Git does not enable them automatically.

Enable them locally with:

```powershell
git config core.hooksPath .githooks
```

Current hooks:

1. `pre-commit`: checks obvious sensitive files, AI co-author markers, and generated artifacts.
2. `commit-msg`: enforces conventional commit format.
3. Pull request template: requires `Applicable Rules`, validation results, and residual risk notes before merge.
4. `pre-commit` also prints rule touchpoint hints based on staged files, so boundary-sensitive changes surface before PR time.

## Adapter Development

Codex adapter install:

```powershell
uv run python scripts/install_adapter.py --host codex --force
```

Codex repo-local skill install:

```powershell
uv run python scripts/install_adapter.py --host codex --repo-skill --force
```

Claude Code adapter install:

```powershell
uv run python scripts/install_adapter.py --host claude --workspace <workspace-root> --force
```

Batch install:

```powershell
uv run python scripts/install_adapters.py --workspace <workspace-root> --force
```

Use `--dry-run` before copying when you only want to inspect resolved paths.

## Before Opening A PR

1. Run `uv run story-canvas --help`.
2. Run `uv run python -m unittest discover -s tests`.
3. Run `uv run story-canvas doctor --root .\examples\minimal-project`.
4. If you changed adapters or install scripts, run at least one adapter install in `--dry-run` mode.
   For repo-local Codex discovery, prefer `uv run python scripts/install_adapter.py --host codex --repo-skill --dry-run`.
5. Update `README.md` or `docs/` when command contract or workflow semantics change.
6. Fill `.github/pull_request_template.md`, especially `Applicable Rules`, checked review checklist items, `Validation`, and `Risks`.

