#!/usr/bin/env bash

source "$(dirname -- "${BASH_SOURCE[0]}")/_common.sh"
initialize_pipeline

if [[ ! -f ./data/results/first_pass.json ]]; then
    echo "Error: expected first-pass result at $PROJECT_ROOT/data/results/first_pass.json" >&2
    exit 1
fi

python - <<'PY'
from pathlib import Path

from pydantic import ValidationError

from pipeline.schemas.first_pass import DrawingExtraction

try:
    DrawingExtraction.model_validate_json(
        Path("data/results/first_pass.json").read_text(encoding="utf-8")
    )
except ValidationError as error:
    raise SystemExit(
        "Error: first-pass result does not match the current schema. "
        "Rerun ./pipeline/runners/first_pass.sh before the second pass."
    ) from error
PY

python -m pipeline.tools.export_schema second ./data/schemas/second_pass.schema.json

codex exec \
    --ignore-user-config \
    --json \
    --skip-git-repo-check \
    -m gpt-5.6-sol \
    -c model_reasoning_effort=high \
    -c model_reasoning_summary=detailed \
    --output-schema ./data/schemas/second_pass.schema.json \
    -o ./data/results/second_pass.json \
    '
Use $extract-structural-members for this extraction.

Perform the final structural-member extraction from the complete drawing set at
./data/input/plan.pdf. Read ./data/results/first_pass.json first and use it only as an overview
of the drawing set and as a guide to relevant pages, schedules, details, notes,
and dimension conventions.

Independently inspect the complete PDF again. This is one full-document second
pass, not a crop-based verification pass.

Before emitting any beam, perform a cross-section shape audit for it even when
the plan already provides one width and depth. Search every beam and roof detail
sheet for a dedicated section naming that member, typical sections that apply
to it, and `similar` or `R/F similar` notes. A dedicated named member section
controls cross-section geometry over a nominal plan callout, schedule value, or
default. Do not interpret a two-number plan callout as proof of a rectangular
section when a detail shows a step, flange, haunch, or L-shape.

Return only actual physical beam and column occurrences that can be tied to a
specific location in a plan, layout, elevation, or section.

Do not create members merely because an ID, size, schedule row, typical detail,
default note, or member type exists. Schedules, details, and defaults are
dimension evidence; they are not proof that a physical member occurs.

Create a separate record for each physical occurrence. If the same drawing ID
appears at multiple locations or levels, create a unique key for each occurrence
and describe its location precisely enough to distinguish it.

This pass does not produce visual positions. Do not return bounding boxes,
normalized coordinates, pixel coordinates, or overlay geometry. A separate
third pass is responsible for locating these fixed member records on the page.

Each beam has three scalar dimension fields:
- width: cross-section width
- depth: cross-section depth
- length: physical longitudinal length

For a beam with a tapered, haunched, tee, inverted-tee, L-shaped, or custom
profile, also populate `profile`. Use exact longitudinal stations measured from
the grid or support centreline named in `profile.start_location`. At each
station, provide either width and depth together or at least three exactly
dimensioned cross-section vertices. Vertex coordinates start at the lower-left
of the section bounding envelope, with positive x right and positive y up;
the last vertex connects back to the first. Use vertices for every station of
tee, inverted-tee, L-shaped, and custom profiles. Set `profile` to null for a
constant rectangular beam.

Every beam must contain `profile_null_reason`. When `profile` is null, identify
the exact named section/detail or other evidence checked and why it establishes
a constant rectangular section or leaves the shape unresolved. When `profile`
is populated, `profile_null_reason` must be null.

Do not split one physical beam merely because its profile varies. When one
scalar width or depth cannot describe the complete beam, keep that scalar null
and explain that the exact values are recorded in `profile.stations`.

Each column has exactly three dimension fields:
- width: cross-section width
- depth: cross-section depth
- height: physical vertical height

Each nullable dimension and unit field has a matching `<field>_null_reason`.
When the value is null, give a concise, specific reason describing which exact
evidence was searched and why it did not establish one value. When the value is
populated, its null-reason field must be null. Do not use a generic phrase such
as "not found" when the missing evidence can be identified more precisely.

Return dimensions as numbers, without unit conversion. Every dimension field
must contain one numeric value or null; never return combined notation such as
"450/400". Populate a dimension only when it is
explicitly stated or can be derived exactly from drawing dimensions, grids,
levels, and support geometry. Never estimate dimensions from rendered pixels.

Use the unit applying to the three dimensions. If the unit cannot be established,
use null.

Return only data conforming to the supplied structured output schema.
' \
    >./data/logs/second_pass.jsonl

python - <<'PY'
from pathlib import Path

from pipeline.schemas.second_pass import SecondPassResult

result_path = Path("data/results/second_pass.json")
SecondPassResult.model_validate_json(result_path.read_text(encoding="utf-8"))
PY

mkdir -p ./public
cp ./data/results/second_pass.json ./public/second_pass_result.json

echo
echo "Second pass complete."
echo "Result written to: $PROJECT_ROOT/data/results/second_pass.json"
