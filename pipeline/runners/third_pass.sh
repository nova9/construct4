#!/usr/bin/env bash

source "$(dirname -- "${BASH_SOURCE[0]}")/_common.sh"
initialize_pipeline

if [[ ! -f ./data/results/second_pass.json ]]; then
    echo "Error: expected second-pass result at $PROJECT_ROOT/data/results/second_pass.json" >&2
    exit 1
fi

python -m pipeline.tools.export_schema third ./data/schemas/third_pass.schema.json

codex exec \
    --ignore-user-config \
    --json \
    --skip-git-repo-check \
    -m gpt-5.6-sol \
    -c model_reasoning_effort=high \
    -c model_reasoning_summary=detailed \
    --output-schema ./data/schemas/third_pass.schema.json \
    -o ./data/results/third_pass.json \
    '
Use $extract-structural-members for this positioning pass.

Read ./data/results/second_pass.json and locate every listed physical beam and column
on the complete drawing set at ./data/input/plan.pdf. This third pass is exclusively for
member positions. Do not re-extract, rename, add, remove, or change members,
pages, locations, levels, or dimensions.

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

When one tight box cannot represent a bent, stepped, or otherwise irregular
beam without covering unrelated structure, leave `position` null and populate
`positions` with the smallest set of tight boxes that collectively covers the
member linework. Do not populate both `position` and `positions`. This remains
one position record for one physical beam.

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
' \
    >./data/logs/third_pass.jsonl

python - <<'PY'
from pathlib import Path

from pipeline.schemas.second_pass import SecondPassResult
from pipeline.schemas.third_pass import ThirdPassResult, validate_against_second_pass

second = SecondPassResult.model_validate_json(
    Path("data/results/second_pass.json").read_text(encoding="utf-8")
)
third = ThirdPassResult.model_validate_json(
    Path("data/results/third_pass.json").read_text(encoding="utf-8")
)
validate_against_second_pass(third, second)
PY

mkdir -p ./public
cp ./data/results/third_pass.json ./public/third_pass_result.json

python -m pipeline.tools.generate_member_overlays

echo
echo "Third pass complete."
echo "Positions written to: $PROJECT_ROOT/data/results/third_pass.json"
echo "Overlay images written to: $PROJECT_ROOT/output/member-overlays"
