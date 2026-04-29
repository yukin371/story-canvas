#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


HOST_DIR_MAP = {
    "codex": "codex-skill",
    "claude": "claude-code",
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def adapter_source(repo_root: Path, host: str, skill_name: str) -> Path:
    return repo_root / "adapters" / HOST_DIR_MAP[host] / skill_name


def default_codex_target(skill_name: str) -> Path:
    return Path.home() / ".codex" / "skills" / skill_name


def default_codex_repo_target(skill_name: str, workspace: Path) -> Path:
    return workspace / ".codex" / "skills" / skill_name


def default_claude_target(skill_name: str, workspace: Path | None) -> Path:
    if workspace is None:
        raise SystemExit("Claude adapter installation requires --workspace or --target-dir.")
    return workspace / ".claude" / "skills" / skill_name


def resolve_target(args: argparse.Namespace, repo_root: Path, skill_name: str) -> Path:
    if args.target_dir:
        return Path(args.target_dir).resolve()
    if args.host == "codex":
        if args.repo_skill:
            workspace = Path(args.workspace).resolve() if args.workspace else repo_root
            return default_codex_repo_target(skill_name, workspace)
        return default_codex_target(skill_name)
    if args.host == "claude":
        workspace = Path(args.workspace).resolve() if args.workspace else None
        return default_claude_target(skill_name, workspace)
    raise SystemExit(f"Unsupported host: {args.host}")


def install_tree(source: Path, target: Path, force: bool) -> None:
    if target.exists():
        if not force:
            raise SystemExit(f"Target already exists: {target}. Use --force to replace it.")
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install a Story Canvas host adapter.")
    parser.add_argument("--host", required=True, choices=sorted(HOST_DIR_MAP))
    parser.add_argument("--skill-name", default="story-harness-writing")
    parser.add_argument(
        "--workspace",
        help="Workspace root for Claude installs, or for Codex repo-skill installs when overriding the current repo root.",
    )
    parser.add_argument(
        "--repo-skill",
        action="store_true",
        help="For Codex only, install into <workspace>/.codex/skills or <repo>/.codex/skills instead of ~/.codex/skills.",
    )
    parser.add_argument("--target-dir", help="Explicit target directory for installation.")
    parser.add_argument("--force", action="store_true", help="Replace the target directory if it already exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved action without copying files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = repo_root_from_script()
    if args.repo_skill and args.host != "codex":
        raise SystemExit("--repo-skill is only supported for the codex host.")
    source = adapter_source(repo_root, args.host, args.skill_name)
    if not source.exists():
        raise SystemExit(f"Adapter source does not exist: {source}")
    target = resolve_target(args, repo_root, args.skill_name)

    result = {
        "host": args.host,
        "skillName": args.skill_name,
        "source": str(source),
        "target": str(target),
        "repoSkill": args.repo_skill,
        "mode": "dry-run" if args.dry_run else "install",
    }

    if not args.dry_run:
        install_tree(source, target, force=args.force)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
