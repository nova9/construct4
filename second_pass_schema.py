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
    depth: float | None
    length: float | None
    unit: DimensionUnit | None


class Column(StrictModel):
    """One physical column occurrence visible in the drawing set."""

    key: str = Field(min_length=1)
    drawing_id: str | None
    page: int = Field(gt=0)
    level: str | None
    location: str = Field(min_length=1)

    # Numeric drawing dimensions; null means one exact value is not established.
    width: float | None
    depth: float | None
    height: float | None
    unit: DimensionUnit | None


class SecondPassResult(StrictModel):
    beams: list[Beam]
    columns: list[Column]

    @model_validator(mode="after")
    def validate_keys(self) -> SecondPassResult:
        keys = [member.key for member in (*self.beams, *self.columns)]
        if len(keys) != len(set(keys)):
            raise ValueError("member keys must be unique")
        return self
