from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DimensionUnit(StrEnum):
    MM = "mm"
    INCH = "in"


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

    @model_validator(mode="after")
    def validate_null_reasons(self) -> Beam:
        _validate_null_reasons(
            self,
            ("width", "depth", "length", "unit"),
        )
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
