#!/usr/bin/env bash

source "$(dirname -- "${BASH_SOURCE[0]}")/_common.sh"
initialize_pipeline

# Regenerate the strict OpenAI JSON Schema from the first-pass Pydantic model.
python -m pipeline.tools.export_schema first ./data/schemas/first_pass.schema.json

codex exec \
  --ignore-user-config \
  --json \
  --skip-git-repo-check \
  -m gpt-5.6-sol \
  -c model_reasoning_effort=high \
  -c model_reasoning_summary=detailed \
  --output-schema ./data/schemas/first_pass.schema.json \
  -o ./data/results/first_pass.json \
  '
Analyze the construction drawing set at ./data/input/plan.pdf.

Determine how this drawing set specifies beam and column dimensions, then extract and resolve those dimensions using all relevant pages in the PDF.

Pay particular attention to:
- general arrangement plans
- column layouts
- beam layouts
- member schedules
- beam and column details
- general/default notes
- local overrides and exceptions
- dedicated named member sections and notes marking other members similar

For every beam occurrence, perform and return a `beam_shape` assessment. Do not
assume a beam is rectangular merely because its plan callout contains two
numbers. Search the complete set for a section or detail naming that beam and
for `similar` or `R/F similar` notes. A dedicated named section controls the
cross-section shape over a nominal plan callout, schedule size, or default.
Use `unknown` when the complete cross-section shape cannot be established.
Set `beam_shape` to null only for columns.

Use cross-page references where necessary.

Return the result using the supplied structured output schema.

If a dimension cannot be read or resolved confidently from the supplied rendering, do not guess. Mark the element as needing verification. A mandatory higher-resolution second pass will process every beam and column.
' \
  >./data/logs/first_pass.jsonl

python - <<'PY'
from pathlib import Path

from pipeline.schemas.first_pass import DrawingExtraction

result_path = Path("data/results/first_pass.json")
DrawingExtraction.model_validate_json(result_path.read_text(encoding="utf-8"))
PY

echo
echo "First pass complete."
echo "Result written to: $PROJECT_ROOT/data/results/first_pass.json"
echo "Log written to: $PROJECT_ROOT/data/logs/first_pass.jsonl"
