#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

initialize_pipeline() {
    cd "$PROJECT_ROOT"

    if [[ ! -f ./.venv/bin/activate ]]; then
        echo "Error: virtual environment not found at $PROJECT_ROOT/.venv" >&2
        echo "Create it with: python3 -m venv .venv" >&2
        exit 1
    fi

    # shellcheck disable=SC1091
    source ./.venv/bin/activate

    if ! command -v codex >/dev/null 2>&1; then
        echo "Error: codex CLI is not installed or is not on PATH." >&2
        exit 1
    fi

    if [[ ! -f ./data/input/plan.pdf ]]; then
        echo "Error: expected input PDF at $PROJECT_ROOT/data/input/plan.pdf" >&2
        exit 1
    fi

    mkdir -p ./data/results ./data/schemas ./data/logs ./public
}
