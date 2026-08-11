# Beam and Column Extraction from Construction Drawings

This project uses the Codex CLI to inspect a construction drawing PDF and produce structured JSON containing physical beam and column occurrences, locations, and dimensions.

It uses two passes:

```text
plan.pdf
   |
   +-- First pass: understand sheets, conventions, defaults, and references
   |      +-- first_pass_result.json
   |      +-- first_pass_log.jsonl
   |
   +-- Second pass: independently inspect the PDF and extract occurrences
          +-- second_pass_result.json
          +-- second_pass_log.jsonl
```

The final file most users want is `second_pass_result.json`.

## What the final result contains

Each physical beam contains:

- Drawing ID, when one is printed
- Drawing page and level
- A location description
- Cross-section width and depth
- Physical longitudinal length
- Unit

Each physical column contains:

- Drawing ID, when one is printed
- Drawing page and level range
- A location description
- Cross-section width and depth
- Physical vertical height
- Unit

A dimension can be `null` when the drawing does not establish one exact value or when the extraction cannot resolve the available evidence safely. `null` does not mean zero.

## Requirements

You need:

- macOS or Linux with Bash
- Python 3.11 or newer
- The Codex CLI
- A Codex account with access to the model selected in the runner scripts
- A construction drawing set saved as a PDF

The extraction can use PDF rendering and image-processing commands. Installing Poppler and ImageMagick is recommended. The examples in this guide also use `jq` to inspect JSON and `rg` (ripgrep) to search logs.

On macOS with Homebrew:

```bash
brew install poppler imagemagick jq ripgrep
```

On Ubuntu or Debian:

```bash
sudo apt-get install poppler-utils imagemagick jq ripgrep
```

## 1. Install and sign in to Codex

Install the Codex CLI on macOS or Linux:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Open the project directory and start Codex:

```bash
codex
```

Follow the sign-in instructions shown the first time it starts. Exit the interactive session after authentication.

Confirm that the command is available:

```bash
codex --version
```

See the [official Codex CLI documentation](https://learn.chatgpt.com/docs/codex/cli) for other installation and authentication options.

## 2. Create the Python environment

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The Python packages are used to generate strict JSON schemas for the Codex output.

## 3. Add the drawing PDF

Copy the complete construction drawing set into the project directory and name it exactly:

```text
plan.pdf
```

For example:

```bash
cp "/path/to/my-structural-drawings.pdf" ./plan.pdf
```

Use the complete drawing set, not only the beam or column layout sheets. Sections, elevations, schedules, details, notes, and architectural levels may contain dimensions needed to resolve members.

## 4. Run the first pass

```bash
bash ./run_first_pass.sh
```

The first pass identifies:

- Drawing units and dimension-order conventions
- Beam and column defaults
- Schedules, details, and other reference locations
- Preliminary member occurrences and evidence
- Items that may need further verification

It writes:

- `first_pass_result.json`: structured drawing-set overview
- `first_pass_log.jsonl`: complete Codex JSONL event log
- `first_pass_result.schema.json`: generated output schema

Do not manually create `first_pass_result.json`. The second pass requires the result produced by this command.

## 5. Run the second pass

After the first pass succeeds:

```bash
bash ./run_second_pass.sh
```

The second pass reads the first-pass overview and independently reinspects the complete PDF. It returns only physical member occurrences tied to locations in plans, layouts, sections, or elevations.

It writes:

- `second_pass_result.json`: final beams and columns
- `second_pass_log.jsonl`: complete Codex JSONL event log
- `second_pass_result.schema.json`: generated output schema

The second pass explicitly uses the repository skill at:

```text
.agents/skills/extract-structural-members/SKILL.md
```

That skill instructs Codex to follow plan callouts into sections, elevations, and details; apply drawing conventions; use exact arithmetic; and revisit unresolved dimensions before returning `null`.

## 6. Inspect the results

Pretty-print the complete final result:

```bash
jq . second_pass_result.json
```

Show only beams:

```bash
jq '.beams' second_pass_result.json
```

Show only columns:

```bash
jq '.columns' second_pass_result.json
```

List members that still contain a missing dimension:

```bash
jq '{
  beams: [
    .beams[]
    | select(.width == null or .depth == null or .length == null or .unit == null)
  ],
  columns: [
    .columns[]
    | select(.width == null or .depth == null or .height == null or .unit == null)
  ]
}' second_pass_result.json
```

## Understanding the two JSON files

`first_pass_result.json` is an analysis and evidence map. It can contain defaults, reference sources, dimension conventions, preliminary elements, bounding boxes, confidence values, and verification flags.

`second_pass_result.json` is the simplified final inventory. It separates beams and columns and contains one record for each physical occurrence found by the second pass.

A schedule row alone does not prove that a member occurs. A plan or other positional drawing must establish the physical occurrence; schedules and details provide dimension evidence.

## Logs and troubleshooting

The `*.jsonl` logs contain reasoning summaries, commands, PDF-rendering activity, skill reads, errors, and final agent output.

Search a log for errors:

```bash
rg -n 'error|failed' first_pass_log.jsonl second_pass_log.jsonl
```

Confirm that the extraction skill was read:

```bash
rg -n 'extract-structural-members/SKILL.md' first_pass_log.jsonl second_pass_log.jsonl
```

Inspect commands used during a run:

```bash
jq -r 'select(.item.type? == "command_execution") | .item.command // empty' second_pass_log.jsonl
```

### Virtual environment not found

If a runner reports that `.venv` is missing, repeat the Python environment setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Codex command not found

Install Codex, restart the terminal if necessary, and check:

```bash
codex --version
```

### Input PDF not found

Confirm the file is in the project root and is named exactly `plan.pdf`:

```bash
ls -lh ./plan.pdf
```

### Requested model is unavailable

The runners currently request `gpt-5.6-sol`. If your account cannot use that model, update the `-m` value in both runner scripts to a Codex-capable model available to your account. Model changes can affect extraction quality, so review the result carefully after changing it.

### Some dimensions are null

First inspect the second-pass log to see which views Codex inspected. Then review the drawing for:

- Section or detail markers crossing the member
- Beam or column schedules
- Sheet-specific and drawing-wide defaults
- Grid dimension strings
- Floor, footing, and roof elevations
- Upstand, downstand, hidden, or edge-beam annotations

If the drawing contains a reliable resolution procedure that Codex missed, add that reusable procedure to `.agents/skills/extract-structural-members/SKILL.md` and rerun the second pass. Do not make schema fields non-null solely to suppress missing values; that can force fabricated dimensions.

## Running another drawing set

The scripts use fixed filenames and overwrite their previous outputs and logs. Before starting another project, copy any results you need to keep.

Then replace `plan.pdf` and run both passes again:

```bash
bash ./run_first_pass.sh
bash ./run_second_pass.sh
```

Do not reuse an old `first_pass_result.json` with a different `plan.pdf`.

## Main files

- `run_first_pass.sh`: runs drawing-set discovery and preliminary extraction
- `run_second_pass.sh`: runs the final physical-member extraction
- `first_pass_schema.py`: defines the detailed first-pass output
- `second_pass_schema.py`: defines the simplified final output
- `export_first_pass_schema.py`: generates the first-pass JSON Schema
- `export_second_pass_schema.py`: generates the second-pass JSON Schema
- `.agents/skills/extract-structural-members/SKILL.md`: reusable extraction and cross-view reasoning instructions
- `requirements.txt`: Python dependencies
