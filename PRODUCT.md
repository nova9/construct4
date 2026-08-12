# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React. The supporting extraction prototype currently uses Python 3.11+, Pydantic, the OpenAI SDK, Bash runner scripts, and the Codex CLI.

## Users

The primary users are quantity surveyors reviewing construction drawings to establish reliable beam and column quantities and dimensions.

## Product Purpose

The product turns a construction drawing PDF into structured beam and column data that a quantity surveyor can review, correct, and export. Success means reducing manual drawing review while keeping uncertain values visible and under the user's control.

## Positioning

Evidence-linked AI extraction with human resolution of ambiguities. The product connects each extracted value or uncertainty to drawing evidence, asks focused questions when an exact value cannot be established safely, and treats conversational answers and direct field edits as changes to the same underlying data.

## Operating Context

The user selects a complete construction drawing PDF. The system analyzes plans together with relevant schedules, sections, elevations, details, notes, and level information; extracts physical beam and column occurrences; presents relevant drawing evidence; asks one ambiguity question at a time; and lets the user review or edit the resulting data before exporting JSON or CSV.

The existing extraction prototype uses two passes: the first maps drawing conventions, defaults, references, and preliminary evidence; the second independently reinspects the complete PDF and produces the final member inventory.

## Capabilities and Constraints

- Accept a construction drawing PDF for analysis.
- Extract physical beam and column occurrences, locations, identifiers, levels, cross-section dimensions, longitudinal beam lengths, and vertical column heights.
- Show the relevant PDF page with page and zoom controls, and highlight supporting evidence when possible.
- Explain ambiguity, offer suggested answers, accept natural-language answers, and support **Skip** and **Cannot determine**.
- Let users select members, edit extracted values directly, add an optional note, undo changes, and retain the original extracted value for reference.
- Keep the assistant conversation and manual editor synchronized as two ways of editing the same underlying data.
- Mark unresolved and manually changed values.
- Export reviewed data as JSON or CSV.
- A schedule entry alone does not establish a physical occurrence; positional drawing evidence must establish it.
- Missing dimensions remain `null` with a specific null reason. A missing value never means zero, and the system must not estimate exact dimensions from pixels.
- The input should be the complete drawing set because dimensions may be established outside plan sheets.
- The authentication, persistence, collaboration, deployment, and commercial model are currently undecided.

## Evidence on Hand

- [`README.md`](README.md) documents the working two-pass CLI extraction workflow and output semantics.
- [`docs/ui.md`](docs/ui.md) contains the confirmed initial interaction model for PDF selection, evidence review, ambiguity resolution, synchronized editing, and export.
- [`plan.pdf`](plan.pdf) is a sample construction drawing set.
- [`first_pass_result.json`](first_pass_result.json) and [`second_pass_result.json`](second_pass_result.json) are existing structured extraction outputs.
- [`first_pass_result.schema.json`](first_pass_result.schema.json) and [`second_pass_result.schema.json`](second_pass_result.schema.json) define the current output structures.
- No testimonials, customer logos, performance benchmarks, production claims, or confirmed brand assets are on hand and future work must not fabricate them.

## Product Principles

1. Keep every consequential extraction traceable to drawing evidence.
2. Surface uncertainty honestly instead of manufacturing precision.
3. Keep the quantity surveyor in control of every correction and final export.
4. Make conversational answers and direct edits consistent, reversible changes to one data model.
5. Reduce review effort without weakening professional judgment.

## Accessibility & Inclusion

No product-specific accessibility standard has been confirmed. The interface should not rely on color alone to communicate unresolved, changed, or confirmed states; a formal conformance target remains undecided.
