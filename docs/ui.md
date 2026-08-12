# UI Design Brief: Structural Drawing Assistant

## Product Idea

The user selects a construction drawing PDF. The AI reads it, extracts beam and column data, and asks the user questions when information is ambiguous.

The user can answer the AI or edit any extracted value manually.

## Main Flow

```text
Select PDF -> AI analyzes drawing -> AI asks questions -> User reviews or edits data -> Export
```

## Opening Screen

Keep it minimal:

- PDF drop zone
- Selected file name
- **Analyze drawing** button

## Main Workspace

Use three areas:

```text
+----------------------+----------------------+----------------------+
| Drawing              | AI Assistant         | Extracted Data       |
|                      |                      |                      |
| Relevant PDF page    | I found two possible | Beam 1B3             |
|                      | depths for beam 1B3: | Width    [225] mm    |
| Highlight evidence   | 400 mm and 450 mm.   | Depth    [   ] mm    |
| when available       |                      | Length   [7575] mm   |
|                      | Which is correct?    |                      |
|                      | [400] [450] [Varies] | [Save changes]       |
+----------------------+----------------------+----------------------+
```

### Drawing

- Show the relevant PDF page
- Provide page and zoom controls
- Highlight the member or evidence when possible

### AI assistant

- Ask one clear question at a time
- Explain why the value is uncertain
- Offer suggested answers
- Allow natural-language answers
- Include **Skip** and **Cannot determine**

### Extracted data

- Show all beams and columns
- Allow direct editing of dimensions and other fields
- Mark unresolved and manually changed values
- Allow undo
- Keep the original extracted value available for reference

## Important Interaction

When the user answers the AI, update the related field in the data panel.

When the user edits a field manually, show the change in the AI conversation and ask for an optional note.

The chat and manual editor are two ways of editing the same data.

## Main Actions

- Select a member
- Answer an AI question
- Edit data manually
- Skip an ambiguity
- Undo a change
- Export reviewed JSON or CSV
