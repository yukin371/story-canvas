#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from subprocess import run


HINT_GROUPS = (
    (
        "commands",
        ("src/story_harness_cli/commands/",),
        "触及 commands 层：检查命令注册、参数解析归属、文件 I/O 是否仍停留在 commands 层。",
    ),
    (
        "services",
        ("src/story_harness_cli/services/",),
        "触及 services 层：检查纯业务逻辑边界、无文件 I/O、不变量和返回结构是否保持稳定。",
    ),
    (
        "protocol",
        ("src/story_harness_cli/protocol/",),
        "触及 protocol 层：检查文件协议、schema 默认值、兼容性和真相源是否保持单一 owner。",
    ),
    (
        "governance",
        (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "docs/ENGINEERING_GOVERNANCE.md",
            "docs/COMMIT_POLICY.md",
            ".github/workflows/",
            ".github/pull_request_template.md",
            ".githooks/",
        ),
        "触及治理资产：检查 AGENTS、工程治理、hooks、CI、PR 模板口径是否同步。",
    ),
)

DOC_SYNC_RULES = (
    (
        "commands",
        ("src/story_harness_cli/commands/",),
        ("src/story_harness_cli/commands/MODULE.md",),
        "commands 相关改动未看到 `commands/MODULE.md` 或 `docs/` 同步，确认是否遗漏模块文档或治理口径更新。",
    ),
    (
        "services",
        ("src/story_harness_cli/services/",),
        ("src/story_harness_cli/services/MODULE.md",),
        "services 相关改动未看到 `services/MODULE.md` 或 `docs/` 同步，确认是否遗漏模块文档更新。",
    ),
    (
        "protocol",
        ("src/story_harness_cli/protocol/",),
        ("src/story_harness_cli/protocol/MODULE.md",),
        "protocol 相关改动未看到 `protocol/MODULE.md` 或 `docs/` 同步，确认是否遗漏协议边界说明。",
    ),
    (
        "governance",
        (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "docs/ENGINEERING_GOVERNANCE.md",
            "docs/COMMIT_POLICY.md",
            ".github/workflows/",
            ".github/pull_request_template.md",
            ".githooks/",
        ),
        (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "docs/ENGINEERING_GOVERNANCE.md",
            "docs/COMMIT_POLICY.md",
        ),
        "治理资产改动未看到 AGENTS / CONTRIBUTING / ENGINEERING_GOVERNANCE / COMMIT_POLICY 同步，确认是否遗漏规则文档更新。",
    ),
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


def _matches(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in prefixes)


def analyze_staged_files(staged_files: list[str]) -> tuple[list[str], list[str]]:
    hints: list[str] = []
    warnings: list[str] = []
    if not staged_files:
        return hints, warnings

    touched_docs = any(path.startswith("docs/") for path in staged_files)

    for _, prefixes, message in HINT_GROUPS:
        if any(_matches(path, prefixes) for path in staged_files):
            hints.append(message)

    for _, watch_prefixes, sync_targets, message in DOC_SYNC_RULES:
        if not any(_matches(path, watch_prefixes) for path in staged_files):
            continue
        synced = any(path in sync_targets for path in staged_files) or touched_docs
        if not synced:
            warnings.append(message)

    return hints, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show local rule touchpoint reminders for staged files.")
    parser.add_argument("--staged-file-list", help="Optional file containing newline-delimited staged paths.")
    args = parser.parse_args(argv)
    try:
        staged_files = _load_staged_files(args)
    except Exception as exc:  # pragma: no cover - defensive CLI error handling
        print(f"[!!] 规则触点检查失败: {exc}", file=sys.stderr)
        return 1

    hints, warnings = analyze_staged_files(staged_files)
    if not hints and not warnings:
        return 0

    print("[rule-touchpoints] 本次暂存改动建议关注：")
    for item in hints:
        print(f"- {item}")
    for item in warnings:
        print(f"[!!] {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
