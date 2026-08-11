---
name: extract-structural-members
description: Extract beam and column occurrences and exact dimensions from construction drawing PDFs. Use for resolving member sizes, lengths, heights, levels, schedules, details, defaults, and cross-page drawing evidence. Do not estimate dimensions from pixels.
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

## Final verification

Before returning the result:

- Revisit every null dimension.
- Search the complete drawing set for supporting evidence.
- Check sections and elevations for missing vertical dimensions.
- Check grids and dimension strings for beam lengths.
- Keep null only when no exact value can be established.