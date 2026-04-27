# Releasing

## Goal

This repository is currently in a fast-iteration phase. The release process should stay lightweight, explicit, and easy to repeat.

## Pre-release Checklist

1. Confirm the working tree is clean.
2. Run `uv sync`.
3. Run `uv run story-canvas --help`.
4. Run `uv run python -m unittest discover -s tests`.
5. Run `uv run story-canvas doctor --root .\examples\minimal-project`.
6. If adapters changed, run:

```powershell
uv run python scripts/install_adapter.py --host codex --dry-run
uv run python scripts/install_adapter.py --host claude --workspace <workspace-root> --dry-run
```

## Versioning

The current package version lives in `pyproject.toml`.

Until a more formal release process exists, bump the version manually and keep the commit history readable with conventional commits.

## Publish Shape

The current recommended release shape is:

1. GitHub source release
2. tagged CLI snapshot
3. adapter sources included in the same repository

PyPI publishing can be added later once the command contract stabilizes.

## Post-release

1. Verify the tag or release notes mention any command contract changes.
2. Verify README installation and quickstart snippets still match the released version.
3. If host adapters changed, verify the install docs still point at the current repository structure.
