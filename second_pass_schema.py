from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Common primitives
# ---------------------------------------------------------------------------

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveDimension = Annotated[float, Field(gt=0.0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ElementType(StrEnum):
    BEAM = "beam"
    COLUMN = "column"


class VerificationStatus(StrEnum):
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    UNRESOLVED = "unresolved"
    CONFLICT = "conflict"


class DimensionUnit(StrEnum):
    MM = "mm"
    INCH = "in"


class DimensionOrder(StrEnum):
    DEPTH_X_WIDTH = "depth_x_width"
    WIDTH_X_DEPTH = "width_x_depth"


class EvidenceType(StrEnum):
    DIRECT_ANNOTATION = "direct_annotation"

    SHEET_DEFAULT = "sheet_default"
    DRAWING_DEFAULT = "drawing_default"

    BEAM_SCHEDULE = "beam_schedule"
    COLUMN_SCHEDULE = "column_schedule"

    BEAM_DETAIL = "beam_detail"
    COLUMN_DETAIL = "column_detail"

    GRID_DIMENSION = "grid_dimension"
    EXPLICIT_SPAN_DIMENSION = "explicit_span_dimension"

    LEVEL_ELEVATION = "level_elevation"
    EXPLICIT_HEIGHT_DIMENSION = "explicit_height_dimension"

    SUPPORT_ASSOCIATION = "support_association"

    UNRESOLVED = "unresolved"


# ---------------------------------------------------------------------------
# Generic dimension representation
# ---------------------------------------------------------------------------

class DimensionComponent(StrictModel):
    """
    Examples:

    450
        raw = "450"
        values = [450]

    30/32
        raw = "30/32"
        values = [30, 32]
    """

    raw: str = Field(min_length=1)

    values: list[PositiveDimension] = Field(
        min_length=1,
        max_length=2,
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class VerificationEvidence(StrictModel):
    """
    Short factual evidence only.

    Do not place chain-of-thought here.
    """

    evidence_type: EvidenceType

    # Short text actually visible in the crop, when applicable.
    # Examples:
    #   "C3 300x225"
    #   "ALL BEAMS ARE 450x225 UNLESS OTHERWISE STATED"
    #   "4200"
    #   "+13.400"
    observed_text: str | None

    confidence: Confidence


# ---------------------------------------------------------------------------
# Cross-section verification
# ---------------------------------------------------------------------------

class VerifiedCrossSection(StrictModel):
    raw: str = Field(min_length=1)

    first: DimensionComponent
    second: DimensionComponent

    unit: DimensionUnit

    # null if the numbers are readable but their semantic order
    # cannot be established safely.
    dimension_order: DimensionOrder | None

    width: DimensionComponent | None
    depth: DimensionComponent | None

    evidence: VerificationEvidence

    @model_validator(mode="after")
    def validate_dimension_order(self) -> VerifiedCrossSection:
        if self.dimension_order == DimensionOrder.WIDTH_X_DEPTH:
            if self.width != self.first or self.depth != self.second:
                raise ValueError(
                    "width_x_depth requires width=first and depth=second"
                )

        if self.dimension_order == DimensionOrder.DEPTH_X_WIDTH:
            if self.depth != self.first or self.width != self.second:
                raise ValueError(
                    "depth_x_width requires depth=first and width=second"
                )

        if self.dimension_order is None:
            if self.width is not None or self.depth is not None:
                raise ValueError(
                    "width and depth must be null when dimension_order is unknown"
                )

        return self


# ---------------------------------------------------------------------------
# Beam-length verification
# ---------------------------------------------------------------------------

class BeamExtent(StrictModel):
    """
    Drawing-supported longitudinal beam information.

    Do not estimate lengths from image pixels.
    """

    start_support: str | None
    end_support: str | None

    start_grid: str | None
    end_grid: str | None

    # Centreline of support -> centreline of support.
    centreline_span: PositiveDimension | None

    # Face of support -> face of support.
    clear_span: PositiveDimension | None

    # Actual overall beam/member extent when explicitly determinable.
    overall_length: PositiveDimension | None

    unit: DimensionUnit

    evidence: VerificationEvidence

    @model_validator(mode="after")
    def validate_extent(self) -> BeamExtent:
        if (
            self.centreline_span is None
            and self.clear_span is None
            and self.overall_length is None
        ):
            raise ValueError(
                "beam extent requires at least one resolved length"
            )

        return self


# ---------------------------------------------------------------------------
# Column-height verification
# ---------------------------------------------------------------------------

class ColumnVerticalExtent(StrictModel):
    """
    Vertical drawing facts for a column.

    floor_to_floor_height is not automatically the final QS measured
    concrete height.
    """

    bottom_level: str | None
    top_level: str | None

    bottom_elevation: float | None
    top_elevation: float | None

    # Difference between stated structural levels where reliably known.
    floor_to_floor_height: PositiveDimension | None

    # Populate ONLY if an actual column/member height is explicitly
    # dimensioned or unambiguously established by the structural detail.
    explicit_column_height: PositiveDimension | None

    unit: DimensionUnit

    evidence: VerificationEvidence

    @model_validator(mode="after")
    def validate_vertical_extent(self) -> ColumnVerticalExtent:
        if (
            self.bottom_elevation is None
            and self.top_elevation is None
            and self.floor_to_floor_height is None
            and self.explicit_column_height is None
        ):
            raise ValueError(
                "column vertical extent requires at least one resolved value"
            )

        return self


# ---------------------------------------------------------------------------
# Per-element verification result
# ---------------------------------------------------------------------------

class VerificationResult(StrictModel):
    """
    One result for one Element.key generated by pass 1.

    All major fact objects are required-but-nullable so the JSON schema
    remains rigid while still supporting beams and columns.
    """

    element_key: str = Field(min_length=1)

    element_type: ElementType

    status: VerificationStatus

    cross_section: VerifiedCrossSection | None

    beam_extent: BeamExtent | None

    column_vertical_extent: ColumnVerticalExtent | None

    confidence: Confidence

    # Short explanation suitable for logs / UI.
    # Not chain-of-thought.
    note: str | None

    @model_validator(mode="after")
    def validate_result(self) -> VerificationResult:
        # ---------------------------------------------------------------
        # Beam/column-specific fields
        # ---------------------------------------------------------------

        if self.element_type == ElementType.BEAM:
            if self.column_vertical_extent is not None:
                raise ValueError(
                    "beam cannot contain column_vertical_extent"
                )

        if self.element_type == ElementType.COLUMN:
            if self.beam_extent is not None:
                raise ValueError(
                    "column cannot contain beam_extent"
                )

        # ---------------------------------------------------------------
        # Status constraints
        # ---------------------------------------------------------------

        resolved_objects = [
            self.cross_section,
            self.beam_extent,
            self.column_vertical_extent,
        ]

        resolved_count = sum(
            value is not None for value in resolved_objects
        )

        if self.status == VerificationStatus.UNRESOLVED:
            if resolved_count != 0:
                raise ValueError(
                    "unresolved result must not contain resolved facts"
                )

        if self.status == VerificationStatus.CONFLICT:
            if resolved_count != 0:
                raise ValueError(
                    "conflict result must not silently choose resolved facts"
                )

        if self.status == VerificationStatus.RESOLVED:
            if resolved_count == 0:
                raise ValueError(
                    "resolved result requires at least one resolved fact"
                )

        if self.status == VerificationStatus.PARTIALLY_RESOLVED:
            if resolved_count == 0:
                raise ValueError(
                    "partially_resolved requires at least one resolved fact"
                )

        return self


# ---------------------------------------------------------------------------
# Batch output
# ---------------------------------------------------------------------------

class VerificationBatch(StrictModel):
    results: list[VerificationResult] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_results(self) -> VerificationBatch:
        keys = [result.element_key for result in self.results]

        if len(keys) != len(set(keys)):
            raise ValueError(
                "element_key values must be unique within the batch"
            )

        return self