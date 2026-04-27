#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from install_adapter import HOST_DIR_MAP, main as install_one_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Story Canvas adapters for one or more hosts.")
    parser.add_argument(
        "--hosts",
        nargs="+",
        choices=sorted(HOST_DIR_MAP),
        help="Hosts to install. Defaults to codex only, or codex+claude when --workspace is provided.",
    )
    parser.add_argument("--skill-name", default="story-harness-writing")
    parser.add_argument("--workspace", help="Workspace root for Claude adapter installation.")
    parser.add_argument("--force", action="store_true", help="Replace target directories if they already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved installs without copying files.")
    return parser


def resolve_hosts(args: argparse.Namespace) -> list[str]:
    if args.hosts:
        return args.hosts
    if args.workspace:
        return ["codex", "claude"]
    return ["codex"]


def run_install(host: str, args: argparse.Namespace) -> None:
    argv = [
        "--host",
        host,
        "--skill-name",
        args.skill_name,
    ]
    if args.workspace:
        argv.extend(["--workspace", args.workspace])
    if args.force:
        argv.append("--force")
    if args.dry_run:
        argv.append("--dry-run")
    install_one_main(argv)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    hosts = resolve_hosts(args)

    if "claude" in hosts and not args.workspace:
        raise SystemExit("Installing the Claude adapter requires --workspace.")

    result = {
        "hosts": hosts,
        "skillName": args.skill_name,
        "workspace": args.workspace,
        "mode": "dry-run" if args.dry_run else "install",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    for host in hosts:
        run_install(host, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
