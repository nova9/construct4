---
name: Structural Drawing Assistant
description: Evidence-first structural member review for quantity surveyors.
colors:
  action-blue: "#1769e0"
  action-blue-strong: "#0f58c7"
  action-blue-soft: "#eaf3ff"
  ink-slate: "#172033"
  muted-slate: "#667085"
  separator: "#d8dee8"
  canvas-cool: "#eef2f6"
  surface: "#ffffff"
  surface-soft: "#f7f9fc"
  unresolved-amber: "#d58400"
  unresolved-amber-soft: "#fff7df"
  confirmed-green: "#168548"
  confirmed-green-soft: "#eaf7ef"
  error-red: "#c93636"
typography:
  display:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "31px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.25
  title:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "11px"
    fontWeight: 650
    lineHeight: 1.3
rounded:
  control: "6px"
  standard: "7px"
  panel: "12px"
  pill: "999px"
spacing:
  xs: "5px"
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.standard}"
    padding: "0 15px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.action-blue-strong}"
    textColor: "{colors.surface}"
    rounded: "{rounded.standard}"
    padding: "0 15px"
    height: "38px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-slate}"
    rounded: "{rounded.standard}"
    padding: "0 15px"
    height: "38px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-slate}"
    rounded: "{rounded.control}"
    padding: "0 10px"
    height: "37px"
  status-unresolved:
    backgroundColor: "{colors.unresolved-amber-soft}"
    textColor: "{colors.unresolved-amber}"
    rounded: "{rounded.pill}"
    padding: "4px 8px"
  status-confirmed:
    backgroundColor: "{colors.confirmed-green-soft}"
    textColor: "{colors.confirmed-green}"
    rounded: "{rounded.pill}"
    padding: "4px 8px"
---

# Design System: Structural Drawing Assistant

## Overview

**Creative North Star: "Evidence First"**

This is a cool white and slate operating environment for professional drawing review. It feels precise, quiet, and trustworthy: evidence occupies the dominant canvas while navigation and decisions stay compact and immediately adjacent. The interface behaves like a disciplined review instrument rather than a conversational dashboard.

Blue is deliberately scarce and signals selection, navigation, and intentional action. Amber identifies unresolved work, green confirms established values, and labels or icons always reinforce those meanings. The review experience joins member data from `second_pass_result.json` with independently verified positions from `third_pass_result.json`; first-pass data is not a UI source or visual dependency.

**Key Characteristics:**

- Evidence-dominant desktop composition with a narrow member navigator and contextual lower review tray.
- Crisp one-pixel separators, cool tonal layers, and compact controls instead of decorative panels.
- Restrained semantic color reinforced by text, icons, and state-specific shapes.
- Dense, scannable sans-serif typography with tabular numerals for quantities and dimensions.

## Colors

The palette is cool, restrained, and semantic: slate establishes hierarchy, blue directs action, amber preserves uncertainty, and green confirms reviewed values.

### Primary

- **Review Blue:** The sole action accent for primary buttons, active tabs, selected rows, links, focus treatment, and changed-value cues.
- **Deep Review Blue:** The primary-button hover state; it adds confidence without introducing a second accent.
- **Evidence Blue Wash:** The quiet selected-state background for rows, tools, and changed-state badges.

### Secondary

- **Unresolved Amber:** Flags missing or indeterminate values and review questions without implying failure.
- **Confirmed Green:** Marks completed extraction states and successful review outcomes.
- **Error Red:** Reserved for genuine loading or processing failure, never ordinary uncertainty.

### Neutral

- **Ink Slate:** Primary text, strong numeric values, and dark toast surfaces.
- **Muted Slate:** Supporting copy, labels, metadata, and inactive controls.
- **Crisp Separator:** One-pixel borders that articulate the workspace structure.
- **Cool Canvas:** The app shell around white working surfaces.
- **Paper White:** Toolbars, navigation, trays, fields, cards, and dialogs.
- **Soft Surface:** Quiet hover, summary, and read-only backgrounds.

### Named Rules

**The Semantic Reserve Rule.** Blue means action or selection, amber means unresolved, green means confirmed, and red means failure; do not use these colors as decoration.

**The Never Color Alone Rule.** Every state color is paired with a label, icon, shape, or positional treatment.

## Typography

**Display Font:** Native UI sans-serif stack
**Body Font:** Native UI sans-serif stack
**Label Font:** Native UI sans-serif stack

**Character:** Neutral, highly legible system typography keeps attention on drawing evidence. Hierarchy comes from compact size shifts, weight, and muted color rather than expressive typefaces.

### Hierarchy

- **Display** (700, 31px, 1.15): Setup-screen proposition only, with tight negative tracking.
- **Headline** (700, 20px, 1.25): Dialog and major process-state titles.
- **Title** (700, 16px, 1.3): Member, navigator, and tray headings.
- **Body** (400, 13px, 1.5): Explanations and setup guidance; long guidance stays near 62–72 characters.
- **Label** (650, 11px, 1.3): Metadata, field labels, badge copy, and compact operational guidance.

### Named Rules

**The Drawing Leads Rule.** Typography must remain compact enough that interface chrome never competes with the source sheet.

**The Numeric Clarity Rule.** Counts, zoom values, and member dimensions use tabular numerals wherever alignment aids scanning.

## Layout

The application is a fixed desktop workspace with a 64px top bar, a 320px member navigator, and a flexible evidence region. Within the evidence region, a 48px viewer toolbar sits above a dominant scrollable drawing canvas; the contextual review tray docks below and grows only as needed, generally capped at 300px. Its content divides into member facts and the current decision, keeping evidence visible while the user resolves uncertainty.

Spacing is compact and consistent: 5–8px for related controls, 12px for toolbar and filter rhythm, 16–18px for working-area padding, and 28px for focused setup or dialog surfaces. The shipped workspace intentionally requires a minimum width of 1180px. At short viewport heights below 760px, the review tray contracts to 238px and reduces internal padding rather than shrinking the evidence canvas indiscriminately.

**The Evidence Ownership Rule.** The PDF canvas receives all flexible space; navigation remains narrow and review controls remain contextual below the canvas.

**The Two-Zone Rule.** Do not turn the workspace into a permanent three-pane chat layout. Conversation and direct editing belong in the same contextual review tray.

## Elevation & Depth

The system is flat by default. White surfaces are separated by crisp borders and cool tonal changes, not shadows. Elevation is reserved for genuinely floating layers: the drawing sheet, evidence notice, export menu, dialog, toast, and focused setup panels.

### Shadow Vocabulary

- **Drawing Lift** (`0 4px 18px rgba(24, 35, 53, .14)`): Separates the rendered sheet from the gray PDF stage.
- **Floating Notice** (`0 4px 15px rgba(24, 35, 53, .12)`): Keeps evidence context legible above the drawing.
- **Menu Lift** (`0 12px 32px rgba(26, 38, 58, .16)`): Used only for anchored menus.
- **Dialog Lift** (`0 24px 70px rgba(17, 28, 45, .28)`): Establishes modal priority over the dimmed workspace.
- **Action Lift** (`0 2px 6px rgba(15, 88, 199, .18)`): A restrained lift on the primary action.

**The Flat Until Floating Rule.** If a surface participates in the workspace grid, separate it with a border or tonal shift; use shadow only when it physically overlays another layer.

## Shapes

Controls use gently softened corners: 6px for compact tools and fields, 7px for standard buttons and notices, and 9–12px for isolated menus, dialogs, and setup panels. Pills are reserved for statuses and small tags. One-pixel borders are the dominant structural device, while circular forms are limited to status dots, progress markers, and compact confirmations.

**The Crisp Frame Rule.** Keep working surfaces rectangular and aligned; larger radii belong to isolated setup or modal moments, not the evidence workspace.

## Components

### Buttons

- **Shape:** Compact, gently softened rectangle (7px) with a standard height of 38px; compact toolbar actions may use 34–36px.
- **Primary:** Review Blue fill, white label, 15px horizontal padding, semibold weight, and a restrained action shadow.
- **Hover / Focus:** Hover deepens to Deep Review Blue. Keyboard focus uses a visible translucent blue 3px outline with 1px offset.
- **Secondary / Ghost:** Secondary buttons stay white with a crisp cool-gray border; icon and text actions use transparent backgrounds and quiet cool-gray hover fills.

### Chips

- **Style:** Status pills use semantic soft backgrounds, matching foreground colors, an icon, and concise 11px bold labels.
- **State:** Filter chips remain neutral until active; state badges communicate unresolved, confirmed, changed, skipped, and cannot-determine explicitly.

### Cards / Containers

- **Corner Style:** Grid-bound surfaces remain square; floating menus use 9px, dialogs 11px, and isolated setup panels 12px.
- **Background:** Paper White over Cool Canvas or a darker PDF-stage gray.
- **Shadow Strategy:** Flat in the grid; elevation only for overlays and isolated setup states.
- **Border:** Crisp Separator, normally one pixel.
- **Internal Padding:** 12–18px for operational surfaces; 28px for dialogs and upload panels.

### Inputs / Fields

- **Style:** White fill, crisp cool-gray stroke, 6px corner, compact 37–38px height, and Ink Slate text.
- **Focus:** Border shifts to Review Blue with a soft 3px blue focus halo.
- **Error / Disabled:** Disabled controls retain their structure at reduced opacity. Errors use text and icon alongside Error Red.

### Navigation

The member navigator is a 320px white rail with search, two compact member-type tabs, filter chips, and a dense scrolling list. A selected member uses an Evidence Blue Wash plus a 3px inset blue bar. Status dots and terminal icons make every row scannable without relying on color alone.

### Evidence Canvas

The drawing stage is the visual anchor. A compact toolbar centers page controls, keeps selection tools left, zoom controls right, and places the rendered sheet on a neutral gray stage. Context notices float at the lower right and offer direct links to the occurrence or cited pages.

### Contextual Review Tray

The tray docks beneath the evidence canvas and combines extracted facts, source-linked uncertainty, suggested answers, manual editing, and next-review actions. It is a single synchronized correction surface: conversational resolution and direct field edits update the same reviewed member record.

## Do's and Don'ts

### Do:

- **Do** keep the drawing canvas dominant and preserve the 320px navigator / flexible evidence split.
- **Do** use one-pixel separators and cool tonal layers for ordinary workspace structure.
- **Do** pair unresolved, confirmed, changed, skipped, and error colors with explicit text or icons.
- **Do** keep missing dimensions explicit as absent values; never visually imply that null equals zero.
- **Do** render member facts from `second_pass_result.json` and overlays from `third_pass_result.json`.

### Don't:

- **Don't** add a permanent chat column or reduce the drawing to a secondary preview.
- **Don't** decorate the interface with semantic blue, amber, green, or red.
- **Don't** use large cards, generous consumer-app spacing, or rounded containers throughout the operational workspace.
- **Don't** estimate exact dimensions from the rendered drawing or suggest pixel measurement as evidence.
- **Don't** expose, blend, or visually depend on first-pass extraction data.
