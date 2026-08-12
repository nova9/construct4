# UI: Structural Drawing Assistant

The React interface is a desktop review workspace for quantity surveyors.

## Flow

```text
Select PDF -> Prepare workspace -> Review members -> Resolve or edit -> Export
```

The bundled prototype loads member data only from `second_pass_result.json`. It does not use first-pass data.

## Workspace

- **Member navigator:** Search beams or columns and filter by all, unresolved, or changed records.
- **Drawing viewer:** Shows the selected member's source page from `plan.pdf`, with page and zoom controls. Cited pages in null reasons are directly accessible. Exact highlights are unavailable because the second-pass data has no bounding boxes.
- **Review tray:** Shows current and original dimensions, location, null reasons, suggested answers, manual editing, optional notes, and the next unresolved action.

Answers and manual edits update the same member record. Changes support undo and redo.

## Export

Reviewed data can be exported as JSON or CSV. If unresolved records remain, the interface requires confirmation and preserves missing values rather than converting them to zero.
