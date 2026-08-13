from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pipeline.schemas.second_pass import SecondPassResult


Coordinate = Annotated[float, Field(ge=0.0, le=1.0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NormalizedBBox(StrictModel):
    """Member linework position using top-left normalized page coordinates."""

    left: Coordinate
    top: Coordinate
    right: Coordinate
    bottom: Coordinate

    @model_validator(mode="after")
    def validate_order(self) -> NormalizedBBox:
        if self.left >= self.right:
            raise ValueError("position.left must be less than position.right")
        if self.top >= self.bottom:
            raise ValueError("position.top must be less than position.bottom")
        return self


class MemberPosition(StrictModel):
    key: str = Field(min_length=1)
    page: int = Field(gt=0)
    position: NormalizedBBox | None
    positions: list[NormalizedBBox] | None = Field(default=None, min_length=1)
    position_null_reason: str | None

    @model_validator(mode="after")
    def validate_null_reason(self) -> MemberPosition:
        if self.position is not None and self.positions is not None:
            raise ValueError("use position or positions, not both")
        if self.position is None and self.positions is None:
            if self.position_null_reason is None or not self.position_null_reason.strip():
                raise ValueError(
                    "position_null_reason is required when no position is populated"
                )
        elif self.position_null_reason is not None:
            raise ValueError(
                "position_null_reason must be null when a position is populated"
            )
        return self

    @property
    def boxes(self) -> list[NormalizedBBox]:
        if self.positions is not None:
            return self.positions
        return [self.position] if self.position is not None else []


class ThirdPassResult(StrictModel):
    beams: list[MemberPosition]
    columns: list[MemberPosition]

    @model_validator(mode="after")
    def validate_keys(self) -> ThirdPassResult:
        keys = [member.key for member in (*self.beams, *self.columns)]
        if len(keys) != len(set(keys)):
            raise ValueError("position keys must be unique")
        return self


def validate_against_second_pass(
    positions: ThirdPassResult,
    members: SecondPassResult,
) -> None:
    for kind in ("beams", "columns"):
        expected = {member.key: member.page for member in getattr(members, kind)}
        actual = {member.key: member.page for member in getattr(positions, kind)}

        missing = sorted(expected.keys() - actual.keys())
        unexpected = sorted(actual.keys() - expected.keys())
        if missing or unexpected:
            raise ValueError(
                f"third-pass {kind} keys do not match second pass; "
                f"missing={missing}, unexpected={unexpected}"
            )

        wrong_pages = {
            key: {"expected": expected[key], "actual": actual[key]}
            for key in expected.keys() & actual.keys()
            if expected[key] != actual[key]
        }
        if wrong_pages:
            raise ValueError(f"third-pass {kind} pages do not match: {wrong_pages}")
