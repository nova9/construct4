#!/usr/bin/env bash

source "$(dirname -- "${BASH_SOURCE[0]}")/_common.sh"
initialize_pipeline

# Regenerate the strict OpenAI JSON Schema from the first-pass Pydantic model.
python -m pipeline.tools.export_schema first ./data/schemas/first_pass.schema.json

codex exec \
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

Use cross-page references where necessary.

Return the result using the supplied structured output schema.

If a dimension cannot be read or resolved confidently from the supplied rendering, do not guess. Mark the element as needing verification. A mandatory higher-resolution second pass will process every beam and column.
' \
  >./data/logs/first_pass.jsonl

echo
echo "First pass complete."
echo "Result written to: $PROJECT_ROOT/data/results/first_pass.json"
echo "Log written to: $PROJECT_ROOT/data/logs/first_pass.jsonl"
