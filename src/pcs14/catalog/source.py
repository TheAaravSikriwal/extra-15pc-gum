"""Where a number came from. Every number in the catalog has one of these behind it."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator


class SourceKind(StrEnum):
    MANUFACTURER = "manufacturer"
    INDEPENDENT_TEST = "independent_test"
    THRUST_STAND = "thrust_stand"
    ESTIMATE = "estimate"
    CAD = "cad"  # a weight worked out from the CAD geometry and a material's density
    MADE_UP = "made_up"  # test parts only; the real catalog refuses them


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(Strict):
    kind: SourceKind
    url: HttpUrl | None = None
    checked: date | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _enough_to_check_it(self):
        linked = (SourceKind.MANUFACTURER, SourceKind.INDEPENDENT_TEST)
        if self.kind in linked and self.url is None:
            raise ValueError(
                f"a {self.kind} source needs a link (url) to where the numbers came from"
            )
        explained = (SourceKind.ESTIMATE, SourceKind.THRUST_STAND, SourceKind.CAD)
        if self.kind in explained and not self.note:
            raise ValueError(
                f"a {self.kind} source needs a note saying how the numbers were worked out"
            )
        return self
