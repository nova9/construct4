---
version: 1
slug: "workspace"
primary_target: "workspace"
related_targets: []
---

# Workspace

- Scope: desktop React workflow from PDF selection and analysis through review and JSON/CSV export. Visitor mode: Operate.
- Audience and job: quantity surveyors repeatedly review hundreds of extracted beams and columns, resolve ambiguity, and preserve traceability to drawing pages.
- Direction: familiar, simple enterprise document-review UI. The approved Evidence First composition keeps a narrow member navigator, dominant PDF canvas, and contextual bottom review tray. Approved comp: `.impeccable/mocks/workspace-b-evidence-first.webp`.
- Interaction: member selection navigates to its drawing page; the tray holds values, null reasons, suggested answers, manual editing, original values, notes, and history. Chat is contextual, never a permanent column.
- States: file selection, staged analysis, failure recovery, confirmed, unresolved, changed, skipped, cannot determine, undo, and export with unresolved acknowledgement.
- Data boundary: use `second_pass_result.json` only. Do not use first-pass data. The second pass establishes page numbers but not exact evidence bounding boxes, so page navigation is real and exact highlights must be reported unavailable rather than inferred.
- Constraints: desktop only, hundreds of records, virtualized/scrolling lists, React, keyboard-friendly, state labels never color-only, no fabricated dimensions or evidence.
