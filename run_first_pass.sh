#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f ./.venv/bin/activate ]]; then
  echo "Error: virtual environment not found at $SCRIPT_DIR/.venv" >&2
  echo "Create it with: python3 -m venv .venv" >&2
  exit 1
fi

# shellcheck disable=SC1091
source ./.venv/bin/activate

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex CLI is not installed or is not on PATH." >&2
  exit 1
fi

if [[ ! -f ./plan.pdf ]]; then
  echo "Error: expected input PDF at $SCRIPT_DIR/plan.pdf" >&2
  exit 1
fi

# Regenerate the strict OpenAI JSON Schema from the first-pass Pydantic model.
python ./export_first_pass_schema.py

codex exec \
  --json \
  --skip-git-repo-check \
  -m gpt-5.6-sol \
  -c model_reasoning_effort=high \
  -c model_reasoning_summary=detailed \
  --output-schema ./first_pass_result.schema.json \
  -o ./first_pass_result.json \
  '
Analyze the construction drawing set at ./plan.pdf.

Determine how this drawing set specifies beam and column dimensions, then extract and resolve those dimensions using all relevant pages in the PDF.

Pay particular attention to:
- general arrangement plans
- column layouts
- beam layouts
- member schedules
- beam and column details
- general/default notes
- local overrides and exceptions

Use cross-page references where necessary.

Return the result using the supplied structured output schema.

If a dimension cannot be read or resolved confidently from the supplied rendering, do not guess. Add an appropriate verification request for a targeted higher-resolution second pass.
'
