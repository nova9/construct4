from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Common primitives
# ---------------------------------------------------------------------------

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
Coordinate = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveDimension = Annotated[float, Field(gt=0.0)]


class StrictModel(BaseModel):
    """Base model used by every object in a drawing-set result."""

    model_config = ConfigDict(extra="forbid")


class NormalizedBBox(StrictModel):
    """
    Normalized page coordinates.

    Origin: top-left
    x increases left -> right
    y increases top -> bottom
    """

    left: Coordinate
    top: Coordinate
    right: Coordinate
    bottom: Coordinate

    @model_validator(mode="after")
    def validate_order(self) -> NormalizedBBox:
        if self.left >= self.right:
            raise ValueError("bbox.left must be less than bbox.right")
        if self.top >= self.bottom:
            raise ValueError("bbox.top must be less than bbox.bottom")
        return self


# ---------------------------------------------------------------------------
# Drawing conventions
# ---------------------------------------------------------------------------

class ElementType(StrEnum):
    BEAM = "beam"
    COLUMN = "column"


class DimensionUnit(StrEnum):
    MM = "mm"
    INCH = "in"


class DimensionOrder(StrEnum):
    DEPTH_X_WIDTH = "depth_x_width"
    WIDTH_X_DEPTH = "width_x_depth"


class ResolutionSource(StrEnum):
    DIRECT_ANNOTATION = "direct_annotation"

    SHEET_DEFAULT = "sheet_default"
    DRAWING_DEFAULT = "drawing_default"

    BEAM_SCHEDULE = "beam_schedule"
    COLUMN_SCHEDULE = "column_schedule"

    BEAM_DETAIL = "beam_detail"
    COLUMN_DETAIL = "column_detail"

    INFERRED = "inferred"
    UNRESOLVED = "unresolved"


class BeamDimensionMethod(StrEnum):
    DIRECT_ANNOTATION = "direct_annotation"
    SHEET_DEFAULT = "sheet_default"
    DRAWING_DEFAULT = "drawing_default"
    BEAM_SCHEDULE = "beam_schedule"
    BEAM_DETAIL = "beam_detail"


class ColumnDimensionMethod(StrEnum):
    DIRECT_ANNOTATION = "direct_annotation"
    SHEET_DEFAULT = "sheet_default"
    DRAWING_DEFAULT = "drawing_default"
    COLUMN_SCHEDULE = "column_schedule"
    COLUMN_DETAIL = "column_detail"


class Readability(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReferenceSourceType(StrEnum):
    COLUMN_SCHEDULE = "column_schedule"
    BEAM_SCHEDULE = "beam_schedule"
    COLUMN_DETAILS = "column_details"
    BEAM_DETAILS = "beam_details"
    GENERAL_NOTES = "general_notes"
    DEFAULT_SIZE_NOTE = "default_size_note"


class DimensionOrderAssessment(StrictModel):
    # Required-but-nullable.
    # null means the model could not safely establish an ordering convention.
    order: DimensionOrder | None
    confidence: Confidence


class DrawingDimensionOrder(StrictModel):
    beam: DimensionOrderAssessment
    column: DimensionOrderAssessment


class DrawingSet(StrictModel):
    # A drawing set can use inches or millimetres.
    # Normally one entry, but multiple units are allowed.
    units: list[DimensionUnit] = Field(min_length=1)

    dimension_order: DrawingDimensionOrder


class Conventions(StrictModel):
    beam_dimension_methods: list[BeamDimensionMethod]
    column_dimension_methods: list[ColumnDimensionMethod]


# ---------------------------------------------------------------------------
# Dimension representation
# ---------------------------------------------------------------------------

class DimensionComponent(StrictModel):
    """
    One side of an AxB member size.

    Examples:

        450
        -> raw = "450"
        -> values = [450]

        30/32
        -> raw = "30/32"
        -> values = [30, 32]

    This lets us preserve tapered/variable dimensions rather than
    forcing them into one scalar.
    """

    raw: str = Field(min_length=1)

    values: list[PositiveDimension] = Field(
        min_length=1,
        max_length=2,
    )


class ElementSize(StrictModel):
    """
    Preserve drawing notation separately from normalized interpretation.

    Example:
        raw = '30"/32" x 18"'
        first.raw = '30/32'
        first.values = [30, 32]
        second.values = [18]

    width/depth can remain null if the ordering convention is uncertain.
    """

    raw: str = Field(min_length=1)

    first: DimensionComponent
    second: DimensionComponent

    unit: DimensionUnit

    # Required-but-nullable.
    width: DimensionComponent | None
    depth: DimensionComponent | None


class VerticalExtent(StrictModel):
    bottom_level: str | None
    top_level: str | None

    bottom_elevation: float | None
    top_elevation: float | None

    floor_to_floor_height: float | None

    unit: DimensionUnit | None
    confidence: Confidence


class BeamExtent(StrictModel):
    start_support: str | None
    end_support: str | None

    start_grid: str | None
    end_grid: str | None

    centreline_span: float | None
    clear_span: float | None
    overall_length: float | None

    unit: DimensionUnit | None

    confidence: Confidence


# ---------------------------------------------------------------------------
# Defaults and cross-page references
# ---------------------------------------------------------------------------

class ElementDefault(StrictModel):
    element_type: ElementType

    # Human-readable scope exactly as understood from the drawing.
    # Examples:
    #   "first floor"
    #   "2nd floor typical up to roof terrace"
    #   "drawing-wide"
    scope: str = Field(min_length=1)

    size: ElementSize

    page: int = Field(gt=0)

    bbox: NormalizedBBox

    confidence: Confidence


class ReferenceSource(StrictModel):
    type: ReferenceSourceType

    page: int = Field(gt=0)

    bbox: NormalizedBBox

    readability: Readability

    needs_high_resolution: bool


# ---------------------------------------------------------------------------
# Member location and evidence
# ---------------------------------------------------------------------------

class ElementLocation(StrictModel):
    """
    Location of the actual structural member on the plan.

    bbox is nullable because the model may identify a member semantically
    without being confident enough to provide its physical region.
    """

    page: int = Field(gt=0)

    bbox: NormalizedBBox | None


class Evidence(StrictModel):
    """
    Where the evidence for the dimension came from.

    This is intentionally separate from ElementLocation.

    Example:
        element is on page 9
        dimension is resolved from a schedule on page 12
    """

    source_type: ResolutionSource

    # Null is allowed for unresolved cases.
    page: int | None

    bbox: NormalizedBBox | None

    # Exact short annotation when useful, e.g.:
    #   "Col. 24x12"
    #   "B-32x18"
    #   "ALL BEAMS ARE 450x225 UNLESS OTHERWISE STATED"
    #
    # Null if there is no useful directly readable text.
    raw_text: str | None


class Resolution(StrictModel):
    source_type: ResolutionSource

    confidence: Confidence

    evidence: Evidence

    @model_validator(mode="after")
    def validate_source_consistency(self) -> Resolution:
        if self.source_type != self.evidence.source_type:
            raise ValueError(
                "resolution.source_type must match evidence.source_type"
            )
        return self


# ---------------------------------------------------------------------------
# Extracted elements
# ---------------------------------------------------------------------------

class Element(StrictModel):
    """
    One dimension-resolved member occurrence / level scope.

    `key` is unique within the JSON output.

    `drawing_id` is the actual designation printed on the drawing, if one
    exists. The same drawing_id may legitimately occur at several levels.
    """

    # Stable unique identifier generated for this output.
    #
    # Examples:
    #   "C1@ground_to_first"
    #   "C1@first_to_roof"
    #   "1B4@first_floor"
    #   "unnamed_beam_p4_01"
    key: str = Field(min_length=1)

    # Actual ID printed on the drawing.
    # null for unnamed members.
    drawing_id: str | None

    type: ElementType

    # Required-but-nullable because a level may genuinely be unclear.
    #
    # Examples:
    #   "ground floor"
    #   "first floor"
    #   "ground floor to first floor"
    #   "1st floor up to roof terrace"
    level: str | None

    size: ElementSize | None

    # Only meaningful for columns.
    vertical_extent: VerticalExtent | None

    # Only meaningful for beams.
    beam_extent: BeamExtent | None

    resolution: Resolution

    location: ElementLocation

    needs_verification: bool

    @model_validator(mode="after")
    def validate_element(self) -> Element:
        if self.size is None:
            if self.resolution.source_type != ResolutionSource.UNRESOLVED:
                # We also permit a low-confidence source with verification,
                # because the model may know where the answer lives but not
                # be able to read it.
                if not self.needs_verification:
                    raise ValueError(
                        "an element with no size must either be unresolved "
                        "or require verification"
                    )

        if (
            self.resolution.source_type == ResolutionSource.UNRESOLVED
            and self.size is not None
        ):
            raise ValueError(
                "unresolved elements must not contain a resolved size"
            )

        return self


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

class VerificationPurpose(StrEnum):
    READ_DIRECT_ANNOTATION = "read_direct_annotation"

    READ_COLUMN_SCHEDULE = "read_column_schedule"
    READ_BEAM_SCHEDULE = "read_beam_schedule"

    READ_COLUMN_DETAIL = "read_column_detail"
    READ_BEAM_DETAIL = "read_beam_detail"

    RESOLVE_MEMBER_ASSOCIATION = "resolve_member_association"

    DETERMINE_DIMENSION_ORDER = "determine_dimension_order"

    RESOLVE_CONFLICTING_EVIDENCE = "resolve_conflicting_evidence"


class VerificationRequest(StrictModel):
    """
    A targeted region worth sending through a higher-resolution second pass.
    """

    page: int = Field(gt=0)

    bbox: NormalizedBBox

    purpose: VerificationPurpose

    reason: str = Field(min_length=1)

    # References Element.key, NOT drawing_id.
    required_for: list[str] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Root output
# ---------------------------------------------------------------------------

class DrawingExtraction(StrictModel):
    drawing_set: DrawingSet

    conventions: Conventions

    defaults: list[ElementDefault]

    reference_sources: list[ReferenceSource]

    elements: list[Element]

    verification_requests: list[VerificationRequest]

    @model_validator(mode="after")
    def validate_references(self) -> DrawingExtraction:
        # `key`, rather than drawing_id, must be globally unique.
        keys = [element.key for element in self.elements]

        if len(keys) != len(set(keys)):
            raise ValueError("element keys must be unique")

        known_keys = set(keys)

        requested_keys = {
            key
            for request in self.verification_requests
            for key in request.required_for
        }

        unknown_keys = requested_keys - known_keys

        if unknown_keys:
            raise ValueError(
                "verification requests reference unknown elements: "
                + ", ".join(sorted(unknown_keys))
            )

        required_keys = {
            element.key
            for element in self.elements
            if element.needs_verification
        }

        missing_keys = required_keys - requested_keys

        if missing_keys:
            raise ValueError(
                "elements needing verification require a verification request: "
                + ", ".join(sorted(missing_keys))
            )

        # Prevent unnecessary verification references.
        unnecessary_keys = requested_keys - required_keys

        if unnecessary_keys:
            raise ValueError(
                "verification requests reference elements not marked "
                "needs_verification: "
                + ", ".join(sorted(unnecessary_keys))
            )

        return self
