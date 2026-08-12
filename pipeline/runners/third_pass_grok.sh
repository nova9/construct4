#!/usr/bin/env bash

source "$(dirname -- "${BASH_SOURCE[0]}")/_common.sh"
initialize_pipeline grok

if [[ ! -f ./data/results/second_pass.json ]]; then
    echo "Error: expected second-pass result at $PROJECT_ROOT/data/results/second_pass.json" >&2
    exit 1
fi

python -m pipeline.tools.export_schema third ./data/schemas/third_pass.schema.json

prompt_file="$(mktemp "${TMPDIR:-/tmp}/construct4-third-pass-grok.XXXXXX")"
result_file="$(mktemp ./data/results/third_pass_grok.XXXXXX)"
trap 'rm -f "$prompt_file" "$result_file"' EXIT

cat >"$prompt_file" <<'PROMPT'
Read and follow ./.agents/skills/extract-structural-members/SKILL.md for this
positioning pass.

Read ./data/results/second_pass.json and locate every listed physical beam and
column on the complete drawing set at ./data/input/plan.pdf. This third pass is
exclusively for member positions. Do not re-extract, rename, add, remove, or
change members, pages, locations, levels, or dimensions.

Return exactly one position record for every second-pass beam and column. Keep
each record in the matching beams or columns list, and copy its `key` and `page`
exactly. The runner will reject missing, additional, retyped, or page-mismatched
records.

Render each relevant full PDF page at high resolution before positioning. Work
through one physical occurrence at a time using its drawing ID, location text,
level, grids, nearby supports, orientation, and printed callouts. Visually
confirm the proposed box against the actual linework. Do not calculate a box
from prose, grid spacing, or assumed page proportions without seeing the member.

Return `position` in normalized full-page coordinates with a top-left origin:
`left`, `top`, `right`, and `bottom`, each from 0 to 1.

For beams, tightly bound only the physical beam linework between its actual end
supports. Exclude labels, dimension strings, grid lines, grid bubbles, columns,
walls, and unrelated extensions. For columns, tightly bound the physical column
footprint or symbol at the stated grid/location. Exclude its label, grid lines,
grid bubbles, footing outline, and nearby members.

Column records for different vertical ranges may share one position only when
they describe the same physical plan occurrence on the same page. Repeated IDs
at different grids must have distinct positions.

Before returning, create and inspect a one-member overlay preview for every
populated box. Reject any box that covers unrelated structure, misses an end,
selects a label instead of linework, or lies outside the named plan/view. Adjust
and reinspect it. If the member still cannot be localized confidently, return
null and give a concise, specific `position_null_reason`; do not invent a box.

Return only data conforming to the supplied structured output schema.
PROMPT

grok_args=(
    --prompt-file "$prompt_file"
    --cwd "$PROJECT_ROOT"
    --json-schema "$(<./data/schemas/third_pass.schema.json)"
    --reasoning-effort high
    --permission-mode auto
    --no-subagents
    --debug
    --debug-file ./data/logs/third_pass_grok.debug.log
)

if [[ -n "${GROK_MODEL:-}" ]]; then
    grok_args+=(--model "$GROK_MODEL")
fi

echo "Starting Grok third pass."
echo "Live debug log: $PROJECT_ROOT/data/logs/third_pass_grok.debug.log"
echo "Stderr log: $PROJECT_ROOT/data/logs/third_pass_grok.stderr.log"
echo "Structured JSON will be written when Grok completes."

: >./data/logs/third_pass_grok.debug.log
: >./data/logs/third_pass_grok.stderr.log
: >./data/logs/third_pass_grok.response.json
chmod 600 \
    ./data/logs/third_pass_grok.debug.log \
    ./data/logs/third_pass_grok.stderr.log \
    ./data/logs/third_pass_grok.response.json

grok "${grok_args[@]}" \
    2> >(tee ./data/logs/third_pass_grok.stderr.log >&2) \
    | tee ./data/logs/third_pass_grok.response.json \
    >"$result_file"

python - "$result_file" <<'PY'
import json
import sys
from pathlib import Path

from pipeline.schemas.second_pass import SecondPassResult
from pipeline.schemas.third_pass import ThirdPassResult, validate_against_second_pass

second = SecondPassResult.model_validate_json(
    Path("data/results/second_pass.json").read_text(encoding="utf-8")
)

result_path = Path(sys.argv[1])
response = json.loads(result_path.read_text(encoding="utf-8"))

# Grok's JSON output format wraps the schema-constrained value in a response
# envelope. Accept a direct schema object as well for compatibility with future
# CLI versions.
if "structuredOutput" in response:
    response = response["structuredOutput"]

third = ThirdPassResult.model_validate(response)
validate_against_second_pass(third, second)
result_path.write_text(
    json.dumps(third.model_dump(mode="json"), indent=2) + "\n",
    encoding="utf-8",
)
PY

mv "$result_file" ./data/results/third_pass.json

mkdir -p ./public
cp ./data/results/third_pass.json ./public/third_pass_result.json

python -m pipeline.tools.generate_member_overlays

echo
echo "Grok third pass complete."
echo "Positions written to: $PROJECT_ROOT/data/results/third_pass.json"
echo "Grok response copied to: $PROJECT_ROOT/data/logs/third_pass_grok.response.json"
echo "Grok debug log written to: $PROJECT_ROOT/data/logs/third_pass_grok.debug.log"
echo "Grok stderr written to: $PROJECT_ROOT/data/logs/third_pass_grok.stderr.log"
echo "Overlay images written to: $PROJECT_ROOT/output/member-overlays"
