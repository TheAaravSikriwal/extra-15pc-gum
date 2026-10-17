"""Every target as a check, with a verdict.

Each check runs twice: on the data as published (nominal) and on the pessimistic version
(see rotor.DERATE). Pass means it meets the target even pessimistically, marginal means it
only meets it on the published numbers, and fail means it misses either way.

Two targets needed a working definition:
- Holding position in a 10 m/s wind means flying at 10 m/s of airspeed at the 20% reserve,
  the worst point of the flight, with 30% more thrust available than it needs (GUST_HEADROOM),
  so there's something left for gusts.
- Top speed is checked at half charge, the middle of a flight.
"""

from dataclasses import dataclass, field

from pcs14 import units
from pcs14.design import Build, SetupTargets, Targets
from pcs14.sizing.battery import Pack
from pcs14.sizing.flight import Flight, fly, power_model, thrust_to_weight
from pcs14.sizing.mass import MassBudget, mass_budget
from pcs14.sizing.rotor import MAX_TILT, CannotHover, PowerModel

GUST_HEADROOM = 1.3
TOP_SPEED_SOC = 0.5
ORDER = {"pass": 0, "marginal": 1, "fail": 2}


def verdict_for(nominal: float, pessimistic: float, limit: float, higher_is_better: bool) -> str:
    def meets(value: float) -> bool:
        return value >= limit if higher_is_better else value <= limit

    if meets(nominal) and meets(pessimistic):
        return "pass"
    return "marginal" if meets(nominal) else "fail"


def worst(verdicts) -> str:
    return max(verdicts, key=ORDER.__getitem__, default="pass")


@dataclass(frozen=True)
class Check:
    name: str
    unit: str  # how the report shows it: min, :1, A, km/h, x, g
    nominal: float
    pessimistic: float
    limit: float
    higher_is_better: bool
    note: str = ""

    @property
    def verdict(self) -> str:
        return verdict_for(self.nominal, self.pessimistic, self.limit, self.higher_is_better)

    @property
    def margin(self) -> float:
        """How far the nominal value clears the limit, as a fraction of the limit."""
        gap = self.nominal - self.limit if self.higher_is_better else self.limit - self.nominal
        return gap / self.limit


@dataclass(frozen=True)
class SetupResult:
    setup: SetupTargets
    mass: MassBudget
    growth_margin: float
    checks: tuple[Check, ...]
    flights: dict[str, Flight] = field(default_factory=dict)  # hover/cruise, nominal/pessimistic
    least_power_speed: float | None = None  # m/s
    least_power_minutes: float | None = None
    top_speeds_kmh: dict[str, float] = field(default_factory=dict)  # at full, half, reserve

    @property
    def verdict(self) -> str:
        return worst(check.verdict for check in self.checks)

    def check(self, name: str) -> Check:
        for check in self.checks:
            if check.name == name:
                return check
        raise KeyError(f"no check called {name!r} for {self.setup.name}")


@dataclass(frozen=True)
class DesignResult:
    build: Build
    targets: Targets
    setups: tuple[SetupResult, ...]

    def setup(self, name: str) -> SetupResult:
        return next(result for result in self.setups if result.setup.name == name)

    @property
    def sizing(self) -> SetupResult:
        return self.setup(self.targets.sizing_case)

    @property
    def verdict(self) -> str:
        return worst(result.verdict for result in self.setups if result.setup.required)


def evaluate(build: Build, targets: Targets, recorder=None, dt: float = 5.0) -> DesignResult:
    """Every module combination, every check, with the growth margin on the sizing case."""
    results = []
    for setup in targets.combinations():
        margin = targets.growth_margin if setup.name == targets.sizing_case else 0.0
        result = evaluate_setup(build, targets, setup, growth_margin=margin, dt=dt)
        if recorder is not None:
            for key, flight in result.flights.items():
                kind, case = key.split("/")
                recorder.log_flight(
                    setup.name, kind, case, flight, highlight=setup.name == targets.sizing_case
                )
        results.append(result)
    if recorder is not None:
        pack = Pack(build.pack)
        longest = max((f.duration for r in results for f in r.flights.values()), default=0.0)
        recorder.log_reserve(pack.mah_used(targets.reserve_fraction), longest)
    return DesignResult(build=build, targets=targets, setups=tuple(results))


def evaluate_setup(
    build: Build,
    targets: Targets,
    setup: SetupTargets,
    growth_margin: float = 0.0,
    dt: float = 5.0,
) -> SetupResult:
    budget = mass_budget(build, setup, growth_margin)
    try:
        nominal = power_model(build, setup, growth_margin)
    except CannotHover as error:
        hovers = Check("Hovers at all", "", 0, 0, 1, True, note=str(error))
        return SetupResult(setup, budget, growth_margin, (hovers,))
    try:
        pessimistic: PowerModel | None = power_model(build, setup, growth_margin, pessimistic=True)
    except CannotHover:
        pessimistic = None

    pack = Pack(build.pack)
    reserve = pack.soc_at_reserve(targets.reserve_fraction)
    cruise = targets.cruise_speed
    flights = {"hover/nominal": fly(nominal, pack, 0.0, targets.reserve_fraction, dt)}
    flights["cruise/nominal"] = fly(nominal, pack, cruise, targets.reserve_fraction, dt)
    if pessimistic is not None:
        flights["hover/pessimistic"] = fly(pessimistic, pack, 0.0, targets.reserve_fraction, dt)
        flights["cruise/pessimistic"] = fly(pessimistic, pack, cruise, targets.reserve_fraction, dt)

    def both(measure, missing: float = 0.0) -> tuple[float, float]:
        return measure(nominal), (measure(pessimistic) if pessimistic is not None else missing)

    def minutes(kind: str, case: str) -> float:
        flight = flights.get(f"{kind}/{case}")
        return flight.minutes if flight is not None else 0.0

    checks = [
        Check(
            "Hover time",
            "min",
            minutes("hover", "nominal"),
            minutes("hover", "pessimistic"),
            units.seconds_to_minutes(setup.min_hover_time),
            True,
            note=_ended_note(flights, "hover"),
        ),
        Check(
            f"Cruise time at {cruise:g} m/s",
            "min",
            minutes("cruise", "nominal"),
            minutes("cruise", "pessimistic"),
            units.seconds_to_minutes(setup.min_cruise_time),
            True,
            note=_ended_note(flights, "cruise"),
        ),
        Check(
            "Thrust-to-weight at the reserve",
            ":1",
            *both(lambda m: thrust_to_weight(m, pack, reserve)),
            targets.min_thrust_to_weight,
            True,
            note="Full throttle at 20% charge, with the pack sagging under the load",
        ),
    ]
    if targets.current_within_battery_rating:
        full_current = nominal.rotor.full_throttle(pack, 1.0).current
        checks.append(
            Check(
                "Full-throttle current",
                "A",
                full_current,
                full_current,
                pack.max_continuous_current,
                False,
                note="All four motors flat out on a full pack, against the pack's rating",
            )
        )
    tops = {
        label: units.ms_to_kmh(nominal.top_speed(nominal.rotor.full_throttle(pack, soc)))
        for label, soc in (("full", 1.0), ("half", TOP_SPEED_SOC), ("reserve", reserve))
    }
    if setup.min_top_speed is not None:
        checks.append(
            Check(
                "Top speed at half charge",
                "km/h",
                *both(
                    lambda m: units.ms_to_kmh(
                        m.top_speed(m.rotor.full_throttle(pack, TOP_SPEED_SOC))
                    )
                ),
                units.ms_to_kmh(setup.min_top_speed),
                True,
            )
        )
    if setup.hold_position_in_wind is not None:
        wind = setup.hold_position_in_wind
        checks.append(
            Check(
                f"Holds position in {wind:g} m/s wind",
                "x",
                *both(lambda m: _wind_headroom(m, pack, wind, reserve)),
                GUST_HEADROOM,
                True,
                note="Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge",
            )
        )
    if setup.max_takeoff_weight is not None:
        grams = units.kg_to_g(budget.total)
        checks.append(
            Check(
                "Takeoff weight",
                "g",
                grams,
                grams,
                units.kg_to_g(setup.max_takeoff_weight),
                False,
            )
        )

    speed, _ = nominal.least_power_speed()
    best = fly(nominal, pack, speed, targets.reserve_fraction, dt)
    return SetupResult(
        setup=setup,
        mass=budget,
        growth_margin=growth_margin,
        checks=tuple(checks),
        flights=flights,
        least_power_speed=speed,
        least_power_minutes=best.minutes,
        top_speeds_kmh=tops,
    )


def _wind_headroom(model: PowerModel, pack: Pack, airspeed: float, soc: float) -> float:
    if model.tilt(airspeed) > MAX_TILT:
        return 0.0
    full = model.rotor.full_throttle(pack, soc)
    return model.available_thrust_per_motor(airspeed, full) / model.thrust_per_motor(airspeed)


def _ended_note(flights: dict[str, Flight], kind: str) -> str:
    early = {f.ended for key, f in flights.items() if key.startswith(kind) and f.ended != "reserve"}
    reasons = {
        "power": "the pack couldn't deliver the power",
        "voltage": "the voltage fell below the cells' minimum",
        "thrust": "full throttle couldn't hold it",
    }
    if not early:
        return ""
    return "Ended before the reserve: " + "; ".join(reasons[e] for e in sorted(early))
