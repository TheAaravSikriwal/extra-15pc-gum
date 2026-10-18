"""The sweep: every motor, prop, cell, pack layout and frame that fit together, ranked.

Builds that can't go together (a prop too big for the frame, a pack outside what the motor
or ESC takes, a motor with no thrust table for the prop) get skipped, with the reason kept.
The rest are ranked by verdict, then by how far their tightest required check clears its
limit, then by the sizing case's cruise time. A check that a firmware setting holds (the
current cap) doesn't count toward the ranking, since it says nothing about the parts.
"""

from dataclasses import dataclass

from pcs14.catalog import Catalog
from pcs14.design import Build, DesignError, Targets
from pcs14.sizing.battery import Pack
from pcs14.sizing.checks import ORDER, DesignResult, evaluate
from pcs14.sizing.flight import fly, power_model
from pcs14.sizing.rotor import CannotHover
from pcs14.units import g_to_kg

LAYOUTS = (2, 3)  # cells in parallel; the series count stays at the build's 6S


@dataclass(frozen=True)
class Candidate:
    build: Build
    result: DesignResult

    @property
    def verdict(self) -> str:
        return self.result.verdict

    @property
    def tightest_margin(self) -> float:
        margins = [
            check.margin
            for setup in self.result.setups
            if setup.setup.required
            for check in setup.checks
            if check.ranked
        ]
        return min(margins, default=float("-inf"))

    @property
    def sizing_cruise_minutes(self) -> float:
        flight = self.result.sizing.flights.get("cruise/nominal")
        return flight.minutes if flight is not None else 0.0


@dataclass(frozen=True)
class SweepResult:
    ranked: tuple[Candidate, ...]
    skipped: tuple[tuple[str, str], ...]  # (build label, why it can't go together)

    @property
    def best(self) -> Candidate:
        return self.ranked[0]


def candidate_builds(base: Build, catalog: Catalog) -> tuple[list[Build], list[tuple[str, str]]]:
    builds, skipped = [], []
    for motor in catalog.motors.values():
        for prop_id in dict.fromkeys(table.prop for table in motor.thrust_tables):
            prop = catalog.prop(prop_id)
            for cell in catalog.cells.values():
                for parallel in LAYOUTS:
                    fits = False
                    reasons = []
                    for frame in catalog.frames.values():
                        try:
                            builds.append(
                                base.variant(
                                    motor=motor,
                                    prop=prop,
                                    cell=cell,
                                    parallel=parallel,
                                    frame=frame,
                                )
                            )
                            fits = True
                        except DesignError as error:
                            reasons.append(str(error))
                    if not fits:
                        layout = f"{base.pack.series}S{parallel}P"
                        label = f"{motor.model} / {prop.model} / {layout} {cell.model}"
                        skipped.append((label, "; ".join(reasons)))
    return builds, skipped


def sweep(base: Build, catalog: Catalog, targets: Targets, recorder=None) -> SweepResult:
    builds, skipped = candidate_builds(base, catalog)
    candidates = []
    for index, build in enumerate(builds):
        candidate = Candidate(build=build, result=evaluate(build, targets))
        candidates.append(candidate)
        if recorder is not None:
            recorder.log_candidate(index, candidate.sizing_cruise_minutes, candidate.verdict)
    ranked = sorted(
        candidates,
        key=lambda c: (ORDER[c.verdict], -c.tightest_margin, -c.sizing_cruise_minutes),
    )
    return SweepResult(ranked=tuple(ranked), skipped=tuple(skipped))


@dataclass(frozen=True)
class MarginPoint:
    grams: float
    hover_minutes: float
    cruise_minutes: float


def margin_curve(build: Build, targets: Targets, grams=range(0, 601, 100)) -> dict:
    """For every setup: hover and cruise minutes as extra mass goes on, 100 g at a time."""
    pack = Pack(build.pack)
    curve: dict[str, list[MarginPoint]] = {}
    for setup in targets.combinations():
        points = []
        for extra in grams:
            try:
                model = power_model(build, setup, growth_margin=g_to_kg(extra))
            except CannotHover:
                break
            hover = fly(model, pack, 0.0, targets.reserve_fraction)
            cruise = fly(model, pack, targets.cruise_speed, targets.reserve_fraction)
            points.append(MarginPoint(extra, hover.minutes, cruise.minutes))
        curve[setup.name] = points
    return curve
