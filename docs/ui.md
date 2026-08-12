# UI: Structural Drawing Assistant

The React interface is a desktop review workspace for quantity surveyors.

## Flow

```text
Select PDF -> Prepare workspace -> Review members -> Resolve or edit -> Export
```

The bundled prototype loads member facts from `second_pass_result.json` and
joins positions from `third_pass_result.json`. It does not use first-pass data.

## Workspace

- **Member navigator:** Search beams or columns and filter by all, unresolved, or changed records.
- **Drawing viewer:** Shows the selected member's source page from `plan.pdf`, with page and zoom controls. Third-pass member positions appear as selectable overlays. Cited pages in null reasons are directly accessible.
- **Review tray:** Shows current and original dimensions, location, null reasons, suggested answers, manual editing, optional notes, and the next unresolved action.

Answers and manual edits update the same member record. Changes support undo and redo.

## Export

Reviewed data can be exported as JSON or CSV. If unresolved records remain, the interface requires confirmation and preserves missing values rather than converting them to zero.
