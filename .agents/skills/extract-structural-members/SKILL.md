---
name: extract-structural-members
description: Extract beam and column occurrences and exact dimensions from construction drawing PDFs. Use for resolving member sizes, lengths, heights, levels, schedules, plan callouts, sections, elevations, details, defaults, and cross-page or cross-view drawing evidence. Do not estimate dimensions from pixels.
---

# Extract structural members

Inspect the complete drawing set before producing the final result.

## Resolve dimensions

When a dimension is not immediately visible:

1. Locate the member occurrence on the plan.
2. Search schedules, sections, elevations, details, and general notes.
3. Apply drawing-wide or sheet-specific defaults unless a local override exists.
4. Establish grid spacings and level elevations before calculating lengths or heights.
5. Derive dimensions only through exact arithmetic from stated dimensions.
6. Reinspect relevant pages at higher resolution when annotations are difficult to read.
7. Do not estimate dimensions from rendered pixel distances.

## Column heights

Before emitting columns, construct a level table containing every stated elevation:

- footing or foundation level
- ground-floor level
- first-floor level
- roof level
- parapet or other applicable top level

Calculate column height as:

`top elevation - bottom elevation`

Account for explicitly stated slab, beam, footing, or pedestal interfaces when the drawing defines column endpoints that way.

## Beam dimensions

Resolve width and depth using this priority:

1. Local member annotation
2. Member detail
3. Beam schedule
4. Sheet-specific default
5. Drawing-wide default

Use the drawing’s established dimension order. Do not assume that the first value is width.

## Beam lengths

Report beam length as the centreline-to-centreline distance between its end
supports or bounding grid lines. When the endpoints span several grid bays, sum
the stated intermediate grid spacings exactly. For example, a beam from grid A
to grid D has length `A-B + B-C + C-D`.

Do not convert a centreline span into a clear span, face-to-face length, or
outer-face overall length by adding or subtracting beam, column, or wall widths.
Do not infer endpoint offsets from the drawn linework. Use a non-grid endpoint
only when the drawing explicitly dimensions that endpoint from a grid or support
centreline; then calculate it using exact stated dimensions and record the
arithmetic as evidence.

## Member positions

When the output schema requests a member position, return a tight bounding box
around the physical member linework on its occurrence page. Use normalized page
coordinates with a top-left origin: `left`, `top`, `right`, and `bottom`, each
from 0 to 1. Do not use the member label, schedule row, dimension string, or
cross-page evidence as the occurrence position. Return null with a specific
reason when the member linework cannot be localized confidently.

## Trace plan callouts into other views

Do not treat the plan as the only source of a member's dimensions. Plans usually establish that a physical member occurs; sections, elevations, and details can supply dimensions that are absent from the plan.

For every missing beam width, depth, or length:

1. Inspect the plan around the member for section cuts, detail callouts, elevation markers, grid references, and view-direction arrows.
2. Record each callout identifier and its referenced sheet or drawing number. Follow same-sheet callouts too.
3. Open the referenced section, elevation, or detail at sufficient resolution to read its annotations.
4. Correlate the member across views using all available anchors:
   - intersection of the section cut with the member
   - view direction
   - grid label and which side of the grid the member occupies
   - level or elevation
   - adjacent slab thicknesses and steps
   - nearby supports, columns, walls, and offsets
   - member ID when repeated in the alternate view
5. Assign an annotation from the alternate view only when these anchors identify the same physical occurrence uniquely. A member ID does not have to be repeated in the section when the section line, grid, side, level, and geometry establish the correspondence.
6. If several beams appear in one section, map each annotation to the correct side of the grid or support. Do not apply a nearby beam size to every member in the view.
7. Parse the annotation using the established drawing convention. For example, when the drawing uses `depth x width`, `450x225 BM` resolves to depth `450` and width `225`.

Treat labels such as upstand, downstand, edge, hidden, or underside beam as geometry qualifiers. Preserve the annotated cross-section values, and use the qualifier plus slab/level geometry to verify that the label belongs to the target beam.

## Close unresolved fields

Before returning any null dimension, perform a targeted closure pass:

1. List every member and missing field.
2. Search plan annotations, intersecting section cuts, referenced sections/elevations/details, schedules, and applicable defaults for that field.
3. Record the exact evidence or exact arithmetic that resolves it.
4. Reinspect ambiguous callouts and referenced views at higher resolution.
5. Keep null only after the targeted search fails or the drawing genuinely provides multiple incompatible values that the scalar output field cannot represent.

## Final verification

Before returning the result:

- Revisit every null dimension.
- Search the complete drawing set for supporting evidence.
- Trace every section/detail marker that intersects or terminates at a member with a missing dimension.
- Confirm alternate-view annotations using grid, side, level, view direction, and surrounding geometry.
- Check sections and elevations for missing vertical dimensions.
- Check grids and dimension strings for beam lengths.
- Keep null only when no exact value can be established.
