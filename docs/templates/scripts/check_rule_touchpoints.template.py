#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from subprocess import run


HINT_GROUPS = (
    ("commands", ("src/", "cmd/", "commands/"), "触及命令/入口层：检查注册入口、参数解析归属和 I/O 边界。"),
    ("services", ("services/", "internal/", "src/"), "触及服务/业务层：检查 owner、不变量和副作用边界。"),
    ("governance", ("AGENTS.md", ".github/", ".githooks/", "docs/"), "触及治理资产：检查适用规则、文档同步和 PR/CI 口径。"),
)


def _load_staged_files(args: argparse.Namespace) -> list[str]:
    if args.staged_file_list:
        content = Path(args.staged_file_list).read_text(encoding="utf-8")
        return [line.strip() for line in content.splitlines() if line.strip()]
    completed = run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to read staged files")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def analyze_staged_files(staged_files: list[str]) -> list[str]:
    hints: list[str] = []
    for _, prefixes, message in HINT_GROUPS:
        if any(path == prefix or path.startswith(prefix) for prefix in prefixes for path in staged_files):
            hints.append(message)
    return hints


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show rule touchpoint hints for staged files.")
    parser.add_argument("--staged-file-list")
    args = parser.parse_args(argv)
    staged_files = _load_staged_files(args)
    hints = analyze_staged_files(staged_files)
    if not hints:
        return 0
    print("[rule-touchpoints] 本次暂存改动建议关注：")
    for item in hints:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
