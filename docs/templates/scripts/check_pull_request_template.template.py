#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "Applicable Rules",
    "Review Checklist",
    "Validation",
    "Risks",
)

REQUIRED_RULE_FIELDS = (
    "当前执行入口",
    "架构护栏 / canonical owner",
    "模块不变量",
    "兼容性约束",
)

REQUIRED_VALIDATION_FIELDS = ("运行命令", "结果")
REQUIRED_RISK_FIELDS = ("残留风险",)
ALLOW_EMPTY_VALUES = {"无", "none", "n/a", "not-applicable"}


def _load_pr_body(args: argparse.Namespace) -> str:
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8")
    if not args.event_path:
        raise ValueError("missing --body-file or --event-path")
    payload = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
    return str(payload.get("pull_request", {}).get("body") or "")


def _extract_sections(body: str) -> dict[str, str]:
    pattern = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip()] = body[start:end].strip()
    return sections


def _parse_labeled_fields(section_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_label = ""
    chunks: list[str] = []
    pattern = re.compile(r"^\s*-\s*(.+?):\s*(.*)$")
    for raw_line in section_text.splitlines():
        line = raw_line.rstrip()
        matched = pattern.match(line)
        if matched:
            if current_label:
                fields[current_label] = "\n".join(chunks).strip()
            current_label = matched.group(1).strip()
            initial = matched.group(2).strip()
            chunks = [initial] if initial else []
            continue
        if current_label and line.strip():
            chunks.append(line.strip())
    if current_label:
        fields[current_label] = "\n".join(chunks).strip()
    return fields


def _is_meaningful(value: str, *, allow_empty_alias: bool = False) -> bool:
    normalized = value.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if lowered in {"tbd", "todo"}:
        return False
    if allow_empty_alias and lowered in ALLOW_EMPTY_VALUES:
        return True
    return True


def _validate_required_fields(
    sections: dict[str, str],
    section_name: str,
    required_fields: tuple[str, ...],
    *,
    allow_empty_alias: bool = False,
) -> list[str]:
    errors: list[str] = []
    fields = _parse_labeled_fields(sections.get(section_name, ""))
    for field in required_fields:
        if field not in fields:
            errors.append(f"{section_name}: missing field `{field}`")
            continue
        if not _is_meaningful(fields[field], allow_empty_alias=allow_empty_alias):
            errors.append(f"{section_name}: field `{field}` is empty or placeholder")
    return errors


def _validate_checklist(section_text: str) -> list[str]:
    errors: list[str] = []
    checked = re.findall(r"^\s*-\s*\[[xX]\]\s+", section_text, flags=re.MULTILINE)
    unchecked = re.findall(r"^\s*-\s*\[\s\]\s+", section_text, flags=re.MULTILINE)
    if not checked and not unchecked:
        errors.append("Review Checklist: missing checklist items")
    if unchecked:
        errors.append("Review Checklist: contains unchecked items")
    return errors


def validate_pull_request_body(body: str) -> list[str]:
    if not body.strip():
        return ["pull request body is empty"]
    sections = _extract_sections(body)
    errors: list[str] = []
    for section_name in REQUIRED_SECTIONS:
        if section_name not in sections:
            errors.append(f"missing section `## {section_name}`")
    if errors:
        return errors
    errors.extend(_validate_required_fields(sections, "Applicable Rules", REQUIRED_RULE_FIELDS))
    errors.extend(_validate_checklist(sections["Review Checklist"]))
    errors.extend(_validate_required_fields(sections, "Validation", REQUIRED_VALIDATION_FIELDS))
    errors.extend(_validate_required_fields(sections, "Risks", REQUIRED_RISK_FIELDS, allow_empty_alias=True))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pull request body governance fields.")
    parser.add_argument("--body-file")
    parser.add_argument("--event-path")
    args = parser.parse_args(argv)
    try:
        body = _load_pr_body(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_pull_request_body(body)
    if errors:
        print("ERROR: Pull request governance check failed.", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("Pull request governance check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
