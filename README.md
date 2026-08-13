# Beam and Column Extraction from Construction Drawings

This project uses the Codex CLI to inspect a construction drawing PDF and produce structured JSON containing physical beam and column occurrences, locations, and dimensions.

It uses three passes:

```text
data/input/plan.pdf
   |
   +-- First pass: understand sheets, conventions, defaults, and references
   |      +-- data/results/first_pass.json
   |      +-- data/logs/first_pass.jsonl
   |
   +-- Second pass: independently inspect the PDF and extract occurrences
   |      +-- data/results/second_pass.json
   |      +-- data/logs/second_pass.jsonl
   |
   +-- Third pass: independently locate those members on their pages
          +-- data/results/third_pass.json
          +-- data/logs/third_pass.jsonl
```

Member facts live in `data/results/second_pass.json`; independently checked overlay
positions live in `data/results/third_pass.json`.

## What the final result contains

Each physical beam contains:

- Drawing ID, when one is printed
- Drawing page and level
- A location description
- Cross-section width and depth
- Physical longitudinal length
- Unit
- A reason for every dimension or unit that is `null`

Each physical column contains:

- Drawing ID, when one is printed
- Drawing page and level range
- A location description
- Cross-section width and depth
- Physical vertical height
- Unit
- A reason for every dimension or unit that is `null`

A dimension can be `null` when the drawing does not establish one exact value or when the extraction cannot resolve the available evidence safely. `null` does not mean zero.
Each nullable value has a matching `<field>_null_reason` field, such as
`length_null_reason`. The reason is required when its value is `null` and must
itself be `null` when the value is populated.

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
data/input/plan.pdf
```

For example:

```bash
cp "/path/to/my-structural-drawings.pdf" ./data/input/plan.pdf
```

Use the complete drawing set, not only the beam or column layout sheets. Sections, elevations, schedules, details, notes, and architectural levels may contain dimensions needed to resolve members.

## 4. Run the first pass

```bash
bash ./pipeline/runners/first_pass.sh
```

The first pass identifies:

- Drawing units and dimension-order conventions
- Beam and column defaults
- Schedules, details, and other reference locations
- Preliminary member occurrences and evidence
- Items that may need further verification

It writes:

- `data/results/first_pass.json`: structured drawing-set overview
- `data/logs/first_pass.jsonl`: complete Codex JSONL event log
- `data/schemas/first_pass.schema.json`: generated output schema

Do not manually create `data/results/first_pass.json`. The second pass requires the result produced by this command.

## 5. Run the second pass

After the first pass succeeds:

```bash
bash ./pipeline/runners/second_pass.sh
```

The second pass reads the first-pass overview and independently reinspects the complete PDF. It returns only physical member occurrences tied to locations in plans, layouts, sections, or elevations.

It writes:

- `data/results/second_pass.json`: final beams and columns
- `data/logs/second_pass.jsonl`: complete Codex JSONL event log
- `data/schemas/second_pass.schema.json`: generated output schema

The second pass explicitly uses the repository skill at:

```text
.agents/skills/extract-structural-members/SKILL.md
```

That skill instructs Codex to follow plan callouts into sections, elevations, and details; apply drawing conventions; use exact arithmetic; and revisit unresolved dimensions before returning `null`.

## 6. Run the third pass

After the second pass succeeds:

```bash
bash ./pipeline/runners/third_pass.sh
```

The third pass reads the final member inventory and independently locates every
member on its specified PDF page. It does not change member identities, pages,
locations, levels, or dimensions. It writes:

- `data/results/third_pass.json`: normalized member positions keyed to the second pass
- `data/logs/third_pass.jsonl`: complete positioning and visual-verification log
- `data/schemas/third_pass.schema.json`: generated position-output schema
- `output/member-overlays/`: one diagnostic full-page PNG per positioned member

The runner validates that the beam and column key sets and page numbers match
the second pass exactly.

## 7. Inspect the results

Pretty-print the complete final result:

```bash
jq . data/results/second_pass.json
```

Show only beams:

```bash
jq '.beams' data/results/second_pass.json
```

Show only columns:

```bash
jq '.columns' data/results/second_pass.json
```

### Generate one overlay image per member

Create a full-page PNG for every beam and column, with only that member's
third-pass position highlighted:

```bash
source .venv/bin/activate
python -m pipeline.tools.generate_member_overlays
```

The images are written to `output/member-overlays/beam/` and
`output/member-overlays/column/`. `output/member-overlays/manifest.json` maps
each image to its member key, page, normalized position, pixel position, and
location. Use `--dpi`, `--pdf`, `--result`, `--positions`, or `--output` to
override defaults.

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
}' data/results/second_pass.json
```

## Understanding the three JSON files

`data/results/first_pass.json` is an analysis and evidence map. It can contain defaults, reference sources, dimension conventions, preliminary elements, bounding boxes, confidence values, and verification flags.

`data/results/second_pass.json` is the simplified final inventory. It separates beams
and columns and contains one record for each physical occurrence found by the
second pass. It contains semantic locations and dimensions, but no page
coordinates.

`data/results/third_pass.json` contains normalized bounding boxes keyed to
second-pass members, or a specific `position_null_reason` when an occurrence
cannot be localized confidently. A straight member uses one `position`; a bent
or irregular beam can use `positions` with several tight boxes while remaining
one physical occurrence.

Complex beam geometry is optional and backward-compatible. A constant
rectangular beam continues to use scalar `width`, `depth`, and `length`. A
tapered, haunched, tee, inverted-tee, L-shaped, or custom beam uses
`profile.stations`; non-rectangular sections use exactly dimensioned ordered
vertices. Profile geometry must come from stated dimensions, never pixel
measurement.

The first pass records a `beam_shape` assessment for every beam occurrence. The
second pass independently audits every beam against dedicated named sections,
typical sections, and `similar` notes. Each second-pass beam must either contain
a complex `profile` or a specific `profile_null_reason`; a two-number plan
callout alone is not proof that the complete cross-section is rectangular.

A schedule row alone does not prove that a member occurs. A plan or other positional drawing must establish the physical occurrence; schedules and details provide dimension evidence.

## Logs and troubleshooting

The `*.jsonl` logs contain reasoning summaries, commands, PDF-rendering activity, skill reads, errors, and final agent output.

Search a log for errors:

```bash
rg -n 'error|failed' data/logs/first_pass.jsonl data/logs/second_pass.jsonl
```

Confirm that the extraction skill was read:

```bash
rg -n 'extract-structural-members/SKILL.md' data/logs/first_pass.jsonl data/logs/second_pass.jsonl data/logs/third_pass.jsonl
```

Inspect commands used during a run:

```bash
jq -r 'select(.item.type? == "command_execution") | .item.command // empty' data/logs/second_pass.jsonl
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

Confirm the file is under `data/input/` and is named exactly `plan.pdf`:

```bash
ls -lh ./data/input/plan.pdf
```

### Requested model is unavailable

The runners currently request `gpt-5.6-sol`. If your account cannot use that model, update the `-m` value in the runner scripts to a Codex-capable model available to your account. Model changes can affect extraction quality, so review the result carefully after changing it.

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

Then replace `data/input/plan.pdf` and run all three passes again:

```bash
bash ./pipeline/runners/first_pass.sh
bash ./pipeline/runners/second_pass.sh
bash ./pipeline/runners/third_pass.sh
```

Do not reuse an old `data/results/first_pass.json` with a different `data/input/plan.pdf`.

## Repository layout

```text
pipeline/
  runners/        three pass runners and shared shell setup
  schemas/        strict Pydantic contracts
  tools/          schema export and overlay rendering
data/
  input/          source construction drawing PDF
  results/        structured pass outputs
  schemas/        generated JSON Schemas
  logs/           Codex JSONL logs
src/              React application source
public/           browser-ready drawing pages and result copies
docs/             supporting documentation
output/           generated diagnostic overlays (ignored by Git)
tools/            unrelated repository maintenance utilities
```

Run the complete pipeline with:

```bash
bash ./pipeline/runners/all_passes.sh
```

The reusable extraction instructions remain in
`.agents/skills/extract-structural-members/SKILL.md`.
