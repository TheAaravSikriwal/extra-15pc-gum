"""What a sim can't prove, and the first thing to measure once the drone is built. Every report
carries its own list of these, written next to the numbers they qualify; the site's unproven
page and the build package's test plans read them from the reports' data files.
"""

from pydantic import BaseModel, ConfigDict


class Unproven(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    what: str
    measure: str  # the first thing to measure once it's built


def bullets(items) -> list[str]:
    return [f"- {u.what} *First to measure:* {u.measure}" for u in items]


def data(items) -> list[dict]:
    return [{"what": u.what, "measure": u.measure} for u in items]


def read(listed) -> list[Unproven]:
    """A report's list from its data file: pairs, or plain strings from before the
    measurements were written."""
    return [Unproven(what=x, measure="") if isinstance(x, str) else Unproven(**x) for x in listed]
