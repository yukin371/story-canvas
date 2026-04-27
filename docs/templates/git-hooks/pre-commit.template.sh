#!/usr/bin/env sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

if [ -x "$REPO_ROOT/scripts/check_staged_governance.sh" ]; then
    sh "$REPO_ROOT/scripts/check_staged_governance.sh"
fi

if command -v python >/dev/null 2>&1 && [ -f "$REPO_ROOT/scripts/check_rule_touchpoints.py" ]; then
    python "$REPO_ROOT/scripts/check_rule_touchpoints.py"
elif command -v python3 >/dev/null 2>&1 && [ -f "$REPO_ROOT/scripts/check_rule_touchpoints.py" ]; then
    python3 "$REPO_ROOT/scripts/check_rule_touchpoints.py"
fi
