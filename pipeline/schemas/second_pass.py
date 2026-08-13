from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DimensionUnit(StrEnum):
    MM = "mm"
    INCH = "in"


class BeamProfileShape(StrEnum):
    TAPERED = "tapered"
    HAUNCHED = "haunched"
    TEE = "tee"
    INVERTED_TEE = "inverted_tee"
    L_SHAPE = "l_shape"
    CUSTOM = "custom"


class CrossSectionPoint(StrictModel):
    """Exactly dimensioned section coordinate from its lower-left envelope."""

    x: float = Field(ge=0)
    y: float = Field(ge=0)


class BeamProfileStation(StrictModel):
    """Cross-section at an exact distance from the beam's start centreline."""

    distance: float = Field(ge=0)
    width: float | None = Field(gt=0)
    depth: float | None = Field(gt=0)
    vertices: list[CrossSectionPoint] | None = Field(default=None, min_length=3)

    @model_validator(mode="after")
    def validate_geometry(self) -> BeamProfileStation:
        has_any_dimension = self.width is not None or self.depth is not None
        has_dimensions = self.width is not None and self.depth is not None
        if has_any_dimension and not has_dimensions:
            raise ValueError("station width and depth must be populated together")
        if has_dimensions and self.vertices is not None:
            raise ValueError("station cannot combine width/depth with vertices")
        if not has_any_dimension and self.vertices is None:
            raise ValueError("station requires width/depth or cross-section vertices")
        if self.vertices is not None:
            area = abs(
                sum(
                    point.x * self.vertices[(index + 1) % len(self.vertices)].y
                    - self.vertices[(index + 1) % len(self.vertices)].x * point.y
                    for index, point in enumerate(self.vertices)
                )
                / 2
            )
            if area == 0:
                raise ValueError("station vertices must enclose a cross-section area")
        return self


class BeamProfile(StrictModel):
    """Exact non-rectangular or longitudinally varying beam geometry."""

    shape: BeamProfileShape
    start_location: str = Field(min_length=1)
    stations: list[BeamProfileStation] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_stations(self) -> BeamProfile:
        distances = [station.distance for station in self.stations]
        if distances != sorted(distances) or len(distances) != len(set(distances)):
            raise ValueError("profile station distances must be strictly increasing")
        polygon_shapes = {
            BeamProfileShape.TEE,
            BeamProfileShape.INVERTED_TEE,
            BeamProfileShape.L_SHAPE,
            BeamProfileShape.CUSTOM,
        }
        if self.shape in polygon_shapes and any(
            station.vertices is None for station in self.stations
        ):
            raise ValueError(
                f"{self.shape.value} profiles require vertices at every station"
            )
        return self


class Beam(StrictModel):
    """One physical beam occurrence visible in the drawing set."""

    key: str = Field(min_length=1)
    drawing_id: str | None
    page: int = Field(gt=0)
    level: str | None
    location: str = Field(min_length=1)

    # Numeric drawing dimensions; null means one exact value is not established.
    width: float | None
    width_null_reason: str | None
    depth: float | None
    depth_null_reason: str | None
    length: float | None
    length_null_reason: str | None
    unit: DimensionUnit | None
    unit_null_reason: str | None
    profile: BeamProfile | None = None
    profile_null_reason: str | None

    @model_validator(mode="after")
    def validate_null_reasons(self) -> Beam:
        _validate_null_reasons(
            self,
            ("width", "depth", "length", "unit"),
        )
        if self.profile is None:
            if self.profile_null_reason is None or not self.profile_null_reason.strip():
                raise ValueError(
                    "profile_null_reason is required when profile is null"
                )
        elif self.profile_null_reason is not None:
            raise ValueError(
                "profile_null_reason must be null when profile is populated"
            )
        if self.profile is not None and self.length is not None:
            if any(
                station.distance > self.length
                for station in self.profile.stations
            ):
                raise ValueError("profile station distance cannot exceed beam length")
        return self


class Column(StrictModel):
    """One physical column occurrence visible in the drawing set."""

    key: str = Field(min_length=1)
    drawing_id: str | None
    page: int = Field(gt=0)
    level: str | None
    location: str = Field(min_length=1)

    # Numeric drawing dimensions; null means one exact value is not established.
    width: float | None
    width_null_reason: str | None
    depth: float | None
    depth_null_reason: str | None
    height: float | None
    height_null_reason: str | None
    unit: DimensionUnit | None
    unit_null_reason: str | None

    @model_validator(mode="after")
    def validate_null_reasons(self) -> Column:
        _validate_null_reasons(
            self,
            ("width", "depth", "height", "unit"),
        )
        return self


class SecondPassResult(StrictModel):
    beams: list[Beam]
    columns: list[Column]

    @model_validator(mode="after")
    def validate_keys(self) -> SecondPassResult:
        keys = [member.key for member in (*self.beams, *self.columns)]
        if len(keys) != len(set(keys)):
            raise ValueError("member keys must be unique")
        return self


def _validate_null_reasons(
    member: Beam | Column,
    fields: tuple[str, ...],
) -> None:
    for field_name in fields:
        value = getattr(member, field_name)
        reason_name = f"{field_name}_null_reason"
        reason = getattr(member, reason_name)

        if value is None and (reason is None or not reason.strip()):
            raise ValueError(f"{reason_name} is required when {field_name} is null")
        if value is not None and reason is not None:
            raise ValueError(f"{reason_name} must be null when {field_name} is populated")
