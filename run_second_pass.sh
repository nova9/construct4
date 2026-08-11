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

if [[ ! -f ./first_pass_result.json ]]; then
    echo "Error: expected first-pass result at $SCRIPT_DIR/first_pass_result.json" >&2
    exit 1
fi

python ./export_second_pass_schema.py

codex exec \
    --json \
    --skip-git-repo-check \
    -m gpt-5.6-sol \
    -c model_reasoning_effort=high \
    -c model_reasoning_summary=detailed \
    --output-schema ./second_pass_result.schema.json \
    -o ./second_pass_result.json \
    '
Perform the final structural-member extraction from the complete drawing set at
./plan.pdf. Read ./first_pass_result.json first and use it only as an overview
of the drawing set and as a guide to relevant pages, schedules, details, notes,
and dimension conventions.

Independently inspect the complete PDF again. This is one full-document second
pass, not a crop-based verification pass.

Return only actual physical beam and column occurrences that can be tied to a
specific location in a plan, layout, elevation, or section.

Do not create members merely because an ID, size, schedule row, typical detail,
default note, or member type exists. Schedules, details, and defaults are
dimension evidence; they are not proof that a physical member occurs.

Create a separate record for each physical occurrence. If the same drawing ID
appears at multiple positions or levels, create a unique key for each occurrence
and describe its location precisely enough to distinguish it.

Each beam has exactly three dimension fields:
- width: cross-section width
- depth: cross-section depth
- length: physical longitudinal length

Each column has exactly three dimension fields:
- width: cross-section width
- depth: cross-section depth
- height: physical vertical height

Preserve exact drawing notation as strings, without unit conversion. Preserve
variable dimensions such as "450/400". Populate a dimension only when it is
explicitly stated or can be derived exactly from drawing dimensions, grids,
levels, and support geometry. Never estimate dimensions from rendered pixels.
Use null when an exact value cannot be established.

Use the unit applying to the three dimensions. If the unit cannot be established,
use null. Do not put units inside the dimension strings.

Return only data conforming to the supplied structured output schema.
' \
    >./second_pass_log.jsonl

echo
echo "Second pass complete."
echo "Result written to: $SCRIPT_DIR/second_pass_result.json"
