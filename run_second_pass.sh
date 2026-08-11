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

# Regenerate the strict OpenAI JSON Schema from the second-pass Pydantic model.
python ./export_second_pass_schema.py

# Convert verification_requests from pass 1 into high-resolution crops
# and per-request context files.
#
# Expected output:
#
# second_pass/
#   request-001.png
#   request-001.json
#   request-002.png
#   request-002.json
#   ...
#
python ./prepare_second_pass.py

mkdir -p ./second_pass/results
mkdir -p ./second_pass/logs

shopt -s nullglob

REQUEST_FILES=(./second_pass/request-*.json)

if (( ${#REQUEST_FILES[@]} == 0 )); then
    echo "No second-pass verification requests were generated."
    exit 0
fi

for REQUEST_FILE in "${REQUEST_FILES[@]}"; do
    REQUEST_NAME="$(basename "$REQUEST_FILE" .json)"
    IMAGE_FILE="./second_pass/${REQUEST_NAME}.png"
    RESULT_FILE="./second_pass/results/${REQUEST_NAME}.json"
    LOG_FILE="./second_pass/logs/${REQUEST_NAME}.jsonl"

    if [[ ! -f "$IMAGE_FILE" ]]; then
        echo "Error: expected verification crop at $IMAGE_FILE" >&2
        exit 1
    fi

    echo "Running second-pass verification: $REQUEST_NAME"

    codex exec \
        --json \
        --skip-git-repo-check \
        -m gpt-5.6-sol \
        -c model_reasoning_effort=high \
        -c model_reasoning_summary=detailed \
        --image "$IMAGE_FILE" \
        --output-schema ./second_pass_result.schema.json \
        -o "$RESULT_FILE" \
        "
Perform a targeted second-pass verification of structural information.

The attached image is a high-resolution crop taken directly from ./plan.pdf.

The verification request and the relevant first-pass element records are stored at:

$REQUEST_FILE

Read that JSON file before analyzing the image.

Only verify the elements listed in its required_for field.

The purpose and reason fields in the request describe what this crop is intended to resolve.

For each requested element, resolve whatever structural facts are actually supported by this crop, including where applicable:

- beam or column cross-section
- beam horizontal extent or span
- column vertical extent or height

Rules:

- Treat the attached high-resolution crop as the primary visual evidence.
- Use ./first_pass_result.json only as contextual information.
- Do not blindly repeat dimensions or interpretations from the first pass.
- Do not invent information that is not visible or otherwise supported by the drawing.
- Preserve the original dimension notation and units.
- Distinguish member cross-section from member length or height.

For cross-sections:
- Read explicit annotations, schedules, defaults, and member details carefully.
- Preserve variable dimensions such as 30/32 x 18.
- Do not assume dimension order unless the drawing establishes it.
- If the numeric pair is readable but width/depth ordering is uncertain,
  preserve first and second dimensions and leave the semantic ordering unresolved.

For beam extent:
- Prefer explicit span dimensions where available.
- Otherwise use clearly established grid or support dimensions.
- Distinguish centreline span, clear span, and overall member length.
- Do not estimate beam length by measuring pixels from the rendered image.

For column vertical extent:
- Use explicit levels, elevations, dimensions, sections, and details.
- Distinguish floor-to-floor height from explicitly stated physical column height.
- Do not report floor-to-floor height as explicit column height unless the drawing
  clearly establishes that equivalence.

For evidence:
- observed_text should contain only short text actually readable from the crop.
- Do not provide chain-of-thought.
- Confidence should reflect confidence in the extracted structural fact.

Status:
- resolved: the requested structural facts visible in this crop were resolved confidently.
- partially_resolved: at least one useful requested fact was resolved, but another
  relevant requested fact remains unresolved.
- unresolved: no requested fact can be resolved reliably from this crop.
- conflict: authoritative evidence in the crop genuinely conflicts and cannot
  be reconciled safely.

Return exactly one result for every element key listed in required_for.

element_key must exactly match the corresponding key from the first-pass result.

Do not include unrelated elements.

Return only data conforming to the supplied structured output schema.
" \
        >"$LOG_FILE"

done

echo
echo "Second pass complete."
echo "Results written to: $SCRIPT_DIR/second_pass/results/"