from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
Coordinate = Annotated[float, Field(ge=0.0, le=1.0)]
BBox = Annotated[list[Coordinate], Field(min_length=4, max_length=4)]
PositiveMillimetres = Annotated[int, Field(gt=0)]


class StrictModel(BaseModel):
    """Base model used by every object in a drawing-set result."""

    model_config = ConfigDict(extra="forbid")


class ElementType(StrEnum):
    BEAM = "beam"
    COLUMN = "column"


class DimensionOrder(StrEnum):
    DEPTH_X_WIDTH = "depth_x_width"
    WIDTH_X_DEPTH = "width_x_depth"


class ResolutionSource(StrEnum):
    DIRECT_ANNOTATION = "direct_annotation"
    SHEET_DEFAULT = "sheet_default"
    BEAM_DETAIL = "beam_detail"
    COLUMN_SCHEDULE = "column_schedule"


class Readability(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DrawingDimensionOrder(StrictModel):
    beam: Literal[DimensionOrder.DEPTH_X_WIDTH]
    column: Literal[DimensionOrder.WIDTH_X_DEPTH]
    confidence: Confidence


class DrawingSet(StrictModel):
    units: Literal["mm"]
    dimension_order: DrawingDimensionOrder


class Conventions(StrictModel):
    beam_dimension_methods: list[
        Literal[
            ResolutionSource.DIRECT_ANNOTATION,
            ResolutionSource.SHEET_DEFAULT,
            ResolutionSource.BEAM_DETAIL,
        ]
    ]
    column_dimension_methods: list[
        Literal[
            ResolutionSource.DIRECT_ANNOTATION,
            ResolutionSource.SHEET_DEFAULT,
            ResolutionSource.COLUMN_SCHEDULE,
        ]
    ]


class ElementDefault(StrictModel):
    element_type: ElementType
    floor: str = Field(min_length=1)
    size_raw: str = Field(pattern=r"^\d+x\d+$")
    page: int = Field(gt=0)
    confidence: Confidence


class ReferenceSource(StrictModel):
    type: Literal["column_schedule", "beam_details"]
    page: int = Field(gt=0)
    bbox: BBox
    readability: Readability
    needs_high_resolution: bool

    @model_validator(mode="after")
    def validate_bbox_order(self) -> ReferenceSource:
        left, top, right, bottom = self.bbox
        if left >= right or top >= bottom:
            raise ValueError("bbox must be ordered as [left, top, right, bottom]")
        return self


class ElementSize(StrictModel):
    raw: str = Field(pattern=r"^\d+x\d+$")
    first: PositiveMillimetres
    second: PositiveMillimetres
    unit: Literal["mm"]
    width: PositiveMillimetres
    depth: PositiveMillimetres

    @model_validator(mode="after")
    def validate_raw_dimensions(self) -> ElementSize:
        if self.raw != f"{self.first}x{self.second}":
            raise ValueError("raw must match first and second dimensions")
        return self


class Resolution(StrictModel):
    source_type: ResolutionSource
    source_page: int = Field(gt=0)
    confidence: Confidence


class Location(StrictModel):
    page: int = Field(gt=0)
    bbox: BBox

    @model_validator(mode="after")
    def validate_bbox_order(self) -> Location:
        left, top, right, bottom = self.bbox
        if left >= right or top >= bottom:
            raise ValueError("bbox must be ordered as [left, top, right, bottom]")
        return self


class Verification(StrictModel):
    reason: str = Field(min_length=1)
    page: int = Field(gt=0)
    bbox: BBox

    @model_validator(mode="after")
    def validate_bbox_order(self) -> Verification:
        left, top, right, bottom = self.bbox
        if left >= right or top >= bottom:
            raise ValueError("bbox must be ordered as [left, top, right, bottom]")
        return self


class Element(StrictModel):
    id: str = Field(min_length=1)
    type: ElementType
    floor: str = Field(min_length=1)
    size: ElementSize | None
    resolution: Resolution
    location: Location
    needs_verification: bool
    # This is deliberately required-but-nullable. Codex Structured Outputs expects
    # every property to be listed in `required`; use null when no check is needed.
    verification: Verification | None

    @model_validator(mode="after")
    def validate_element(self) -> Element:
        if self.needs_verification and self.verification is None:
            raise ValueError("verification details are required when needs_verification is true")
        if not self.needs_verification and self.verification is not None:
            raise ValueError("verification details require needs_verification to be true")

        if self.size is not None:
            if self.type == ElementType.BEAM and (
                self.size.depth != self.size.first
                or self.size.width != self.size.second
            ):
                raise ValueError("beam sizes must use depth_x_width dimension order")
            if self.type == ElementType.COLUMN and (
                self.size.width != self.size.first
                or self.size.depth != self.size.second
            ):
                raise ValueError("column sizes must use width_x_depth dimension order")
        return self


class VerificationRequest(StrictModel):
    page: int = Field(gt=0)
    bbox: BBox
    purpose: Literal["read_column_schedule"]
    required_for: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_bbox_order(self) -> VerificationRequest:
        left, top, right, bottom = self.bbox
        if left >= right or top >= bottom:
            raise ValueError("bbox must be ordered as [left, top, right, bottom]")
        return self


class DrawingExtraction(StrictModel):
    drawing_set: DrawingSet
    conventions: Conventions
    defaults: list[ElementDefault]
    reference_sources: list[ReferenceSource]
    elements: list[Element]
    verification_requests: list[VerificationRequest]

    @model_validator(mode="after")
    def validate_references(self) -> DrawingExtraction:
        element_ids = [element.id for element in self.elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("element ids must be unique")

        known_ids = set(element_ids)
        requested_ids = {
            element_id
            for request in self.verification_requests
            for element_id in request.required_for
        }
        unknown_ids = requested_ids - known_ids
        if unknown_ids:
            raise ValueError(
                "verification requests reference unknown elements: "
                + ", ".join(sorted(unknown_ids))
            )

        required_ids = {
            element.id for element in self.elements if element.needs_verification
        }
        missing_ids = required_ids - requested_ids
        if missing_ids:
            raise ValueError(
                "elements needing verification require a verification request: "
                + ", ".join(sorted(missing_ids))
            )
        return self
