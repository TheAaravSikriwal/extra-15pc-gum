"""Heat in the wires and connectors, steady and through the burst at the current cap.

A wire is copper inside a ring of insulation, hanging in still air. The copper makes I2R per
meter, its resistance rising as it warms; the heat crosses the insulation by conduction and
leaves the surface by natural convection and radiation. The convection is the textbook
correlation for a horizontal cylinder in air (h = 1.32 (dT/D)^1/4), scaled by 0.74 so the
model's free-air ampacity lands within 3% of Remington's published table for 12 to 22 AWG
(still a touch above it); unscaled, it ran about 10% optimistic, the wrong way round for a
check. Bundled wires run hotter than this, which the checks' margins have to cover.

A burst starts from the wire's hottest steady temperature and heats the copper and its
insulation together for the burst's length.

A connector is calibrated from its maker's rating: the rated current gives the rated rise, so
the rise goes as the current squared. Through a burst it heats with a time constant from its
contacts' resistance and the heat capacity of its contacts plus a short length of the wire on
each side, an estimate.
"""

import math
from dataclasses import dataclass

ALPHA = 0.00393  # copper's resistance, per K near 20 C
COPPER_DENSITY = 8960.0  # kg/m3
COPPER_HEAT = 385.0  # J/(kg K)
BRASS_HEAT = 380.0  # J/(kg K)
SIGMA = 5.670374e-8  # W/(m2 K4)
EMISSIVITY = 0.9  # silicone and PVC, a typical figure
CONVECTION_FACTOR = 0.74  # calibrated against Remington's free-air table
ATTACHED_WIRE = 0.02  # m of wire on each side of a connector that heats with it
BURST_STEPS = 200


@dataclass(frozen=True)
class Insulation:
    name: str
    conductivity: float  # W/(m K)
    density: float  # kg/m3
    heat: float  # J/(kg K)


SILICONE = Insulation("silicone", 0.20, 1200.0, 1300.0)  # typical figures for silicone rubber
PVC = Insulation("PVC", 0.19, 1400.0, 1000.0)
INSULATIONS = {"silicone": SILICONE, "pvc": PVC}


@dataclass(frozen=True)
class Hot:
    conductor_c: float
    surface_c: float


@dataclass(frozen=True)
class WireModel:
    ohms_per_m: float  # at 20 C
    area: float  # copper, m2
    outer: float  # over the insulation, m
    insulation: Insulation

    @property
    def conductor(self) -> float:
        return math.sqrt(4 * self.area / math.pi)

    @property
    def insulation_ohms(self) -> float:
        """K per W per meter, across the insulation."""
        return math.log(self.outer / self.conductor) / (2 * math.pi * self.insulation.conductivity)

    def cooling(self, surface_c: float, air_c: float) -> float:
        """W/(m2 K) off the surface: natural convection plus radiation."""
        rise = max(surface_c - air_c, 1e-6)
        convection = CONVECTION_FACTOR * 1.32 * (rise / self.outer) ** 0.25
        radiation = EMISSIVITY * SIGMA * ((surface_c + 273.15) ** 4 - (air_c + 273.15) ** 4) / rise
        return convection + radiation

    def surface_for(self, conductor_c: float, air_c: float) -> float:
        """The surface temperature where heat across the insulation meets heat off the surface."""
        low, high = air_c, conductor_c
        for _ in range(60):
            surface = (low + high) / 2
            across = (conductor_c - surface) / self.insulation_ohms
            off = self.cooling(surface, air_c) * math.pi * self.outer * (surface - air_c)
            if off > across:
                high = surface
            else:
                low = surface
        return surface

    def heat_out(self, conductor_c: float, air_c: float) -> float:
        """W per meter leaving a conductor at this temperature."""
        if conductor_c <= air_c:
            return 0.0
        surface = self.surface_for(conductor_c, air_c)
        return (conductor_c - surface) / self.insulation_ohms

    def steady(self, amps: float, air_c: float) -> Hot:
        conductor = air_c
        for _ in range(200):
            watts = amps**2 * self.ohms_per_m * (1 + ALPHA * (conductor - 20))
            low, high = air_c, air_c + 5000
            for _ in range(60):
                surface = (low + high) / 2
                off = self.cooling(surface, air_c) * math.pi * self.outer * (surface - air_c)
                if off > watts:
                    high = surface
                else:
                    low = surface
            new = surface + watts * self.insulation_ohms
            if abs(new - conductor) < 1e-6:
                break
            conductor = 0.5 * conductor + 0.5 * new
        return Hot(new, surface)

    def ampacity(self, to_c: float, air_c: float) -> float:
        """The current that brings the copper to `to_c`."""
        low, high = 0.0, 1000.0
        for _ in range(60):
            amps = (low + high) / 2
            if self.steady(amps, air_c).conductor_c > to_c:
                high = amps
            else:
                low = amps
        return amps

    def heat_capacity(self, insulation_mass: bool = True) -> float:
        """J/K per meter."""
        copper = self.area * COPPER_DENSITY * COPPER_HEAT
        if not insulation_mass:
            return copper
        ring = math.pi / 4 * (self.outer**2 - self.conductor**2)
        return copper + ring * self.insulation.density * self.insulation.heat

    def trajectory(self, start_c, amps, seconds, air_c, points=51) -> list[tuple[float, float]]:
        """(seconds, copper temperature) through a burst, for plotting: the same steps as
        burst(), sampled along the way."""
        temps = self._heating(start_c, amps, seconds, air_c)
        picks = [round(i * BURST_STEPS / (points - 1)) for i in range(points)]
        return [(seconds * k / BURST_STEPS, temps[k]) for k in picks]

    def burst(
        self,
        start_c: float,
        amps: float,
        seconds: float,
        air_c: float,
        cooling: bool = True,
        insulation_mass: bool = True,
        alpha: float = ALPHA,
    ) -> float:
        """The copper's temperature after `seconds` at `amps`, from `start_c`."""
        return self._heating(start_c, amps, seconds, air_c, cooling, insulation_mass, alpha)[-1]

    def _heating(
        self, start_c, amps, seconds, air_c, cooling=True, insulation_mass=True, alpha=ALPHA
    ) -> list[float]:
        capacity = self.heat_capacity(insulation_mass)
        step = seconds / BURST_STEPS
        temps = [start_c]
        for _ in range(BURST_STEPS):
            temp = temps[-1]
            heat = amps**2 * self.ohms_per_m * (1 + alpha * (temp - 20))
            if cooling:
                heat -= self.heat_out(temp, air_c)
            temps.append(temp + heat * step / capacity)
        return temps


@dataclass(frozen=True)
class ConnectorModel:
    rated_a: float
    rise_c: float  # at the rated current
    contact_ohms: float
    heat_capacity: float  # J/K, of what heats with the contacts

    @property
    def rise_per_amp2(self) -> float:
        return self.rise_c / self.rated_a**2

    @property
    def time_constant(self) -> float:
        return self.rise_per_amp2 / self.contact_ohms * self.heat_capacity

    def steady_rise(self, amps: float) -> float:
        return self.rise_per_amp2 * amps**2

    def trajectory(self, start_rise, amps, seconds, points=51) -> list[tuple[float, float]]:
        """(seconds, rise over the air) through a burst, for plotting."""
        return [
            (
                seconds * i / (points - 1),
                self.burst_rise(start_rise, amps, seconds * i / (points - 1)),
            )
            for i in range(points)
        ]

    def burst_rise(self, start_rise: float, amps: float, seconds: float) -> float:
        final = self.steady_rise(amps)
        return final + (start_rise - final) * math.exp(-seconds / self.time_constant)


def _wire_model(ctx, run):
    """A run's heat model and its temperature limit (its insulation's, less the margin), or
    (None, None) for a wire table with no insulation rating."""
    from pcs14.electrical.checks import awg_area

    table = ctx.parts[run.wire]
    if table.insulation is None:
        return None, None
    gauge = table.gauge(run.awg)
    model = WireModel(
        gauge.resistance_per_m,
        awg_area(run.awg),
        gauge.outer_diameter,
        INSULATIONS[table.insulation],
    )
    return model, table.insulation_max_c - ctx.numbers.temp_margin_c


def _connector_model(ctx, ref):
    """A mated pin's connector as a heat model, with its limit, or (None, None) when its maker
    doesn't publish enough to make one."""
    from pcs14.electrical.checks import awg_area

    connector = ctx.wiring.board_of(ref).block.connector(ref.split(".")[1])
    family = ctx.parts.get(connector.family)
    rating = getattr(getattr(family, "electrical", None), "rating", None)
    if rating is None or not (rating.temp_rise_c and rating.contact_mass_g and rating.contact_mohm):
        return None, None
    wire = awg_area(rating.wire_awg) * 2 * ATTACHED_WIRE * COPPER_DENSITY * COPPER_HEAT
    capacity = rating.contact_mass_g / 1000 * BRASS_HEAT + wire
    model = ConnectorModel(
        rating.continuous_a, rating.temp_rise_c, rating.contact_resistance, capacity
    )
    return model, rating.max_c - ctx.numbers.temp_margin_c


def _steady_temps(ctx, solutions, models) -> dict:
    """Each wire's hottest steady temperature in each combination, where its burst starts."""
    from pcs14.electrical.checks import STEADY

    air = ctx.numbers.air_c
    out: dict[str, dict[str, float]] = {}
    for (setup, case), solution in solutions.items():
        if case not in STEADY:
            continue
        temps = out.setdefault(setup, {})
        for label, amps in solution.wires.items():
            model = models[label][0]
            if model is not None:
                hot = model.steady(amps, air).conductor_c
                temps[label] = max(temps.get(label, air), hot)
    return out


def _connector_steady(solutions, setup) -> dict[str, float]:
    """Each contact's highest steady current in one combination."""
    from pcs14.electrical.checks import STEADY

    out: dict[str, float] = {}
    for (name, case), solution in solutions.items():
        if name == setup and case in STEADY:
            for ref, amps in solution.contacts.items():
                out[ref] = max(out.get(ref, 0.0), amps)
    return out


def wire_working(ctx, solutions) -> dict:
    """How hard each wire works, in each combination and case: the share of its allowed heating
    it uses, which is its temperature rise over the air against the rise to its limit. Past 1,
    it fails a heat check. Steady cases sit at their steady temperature; the burst starts from
    that combination's hottest steady temperature and runs for the burst's length."""
    air, seconds = ctx.numbers.air_c, ctx.numbers.burst_s
    models = {run.label: _wire_model(ctx, run) for run in ctx.design.wires}
    starts = _steady_temps(ctx, solutions, models)
    out = {}
    for (setup, case), solution in solutions.items():
        shares = {}
        for label, amps in solution.wires.items():
            model, limit_c = models[label]
            if model is None:
                continue
            if amps < 0.01:
                shares[label] = 0.0
                continue
            if case == "burst":
                hot = model.burst(starts.get(setup, {}).get(label, air), amps, seconds, air)
            else:
                hot = model.steady(amps, air).conductor_c
            shares[label] = (hot - air) / (limit_c - air)
        out[(setup, case)] = shares
    return out


def connector_working(ctx, solutions) -> dict:
    """How hard each rated power connector works, the same way as wire_working: its rise over
    the air against the rise to its limit, steady or at the end of the burst."""
    air, seconds = ctx.numbers.air_c, ctx.numbers.burst_s
    models: dict[str, tuple] = {}
    out = {}
    for (setup, case), solution in solutions.items():
        steady = _connector_steady(solutions, setup)
        shares = {}
        for ref, amps in solution.contacts.items():
            if ref not in models:
                models[ref] = _connector_model(ctx, ref)
            model, limit_c = models[ref]
            if model is None:
                continue
            if case == "burst":
                rise = model.burst_rise(model.steady_rise(steady.get(ref, 0.0)), amps, seconds)
            else:
                rise = model.steady_rise(amps)
            shares[ref] = rise / (limit_c - air)
        out[(setup, case)] = shares
    return out


def burst_curves(ctx, solutions, wires: int = 3) -> list[tuple[str, list, float]]:
    """Temperature through the burst for the few wires that end it nearest their limits, and
    for the power connectors the burst heats: (name, [(s, C)], limit in C), the hardest
    working first. Each comes from the combination where it ends hottest."""
    air, seconds = ctx.numbers.air_c, ctx.numbers.burst_s
    models = {run.label: _wire_model(ctx, run) for run in ctx.design.wires}
    starts = _steady_temps(ctx, solutions, models)
    worst: dict[str, tuple] = {}  # name -> (share at the end, draw it)

    def keep(name, end_c, limit_c, draw):
        share = (end_c - air) / (limit_c - air)
        if share > worst.get(name, (-1.0,))[0]:
            worst[name] = (share, draw)

    contacts = set()
    for (setup, case), solution in solutions.items():
        if case != "burst":
            continue
        for label, amps in solution.wires.items():
            model, limit_c = models[label]
            if model is None or amps < 0.01:
                continue
            start = starts.get(setup, {}).get(label, air)
            end = model.burst(start, amps, seconds, air)
            keep(label, end, limit_c, (model.trajectory, (start, amps, seconds, air), limit_c))
        steady = _connector_steady(solutions, setup)
        for ref, amps in solution.contacts.items():
            model, limit_c = _connector_model(ctx, ref)
            if model is None or amps <= 1.05 * steady.get(ref, 0.0):
                continue
            contacts.add(ref)
            rise = model.steady_rise(steady.get(ref, 0.0))
            end = air + model.burst_rise(rise, amps, seconds)
            keep(ref, end, limit_c, (model.trajectory, (rise, amps, seconds), limit_c, air))

    ranked = sorted(worst.items(), key=lambda item: item[1][0], reverse=True)
    chosen = [item for item in ranked if item[0] not in contacts][:wires]
    chosen += [item for item in ranked if item[0] in contacts]
    out = []
    for name, (_, draw) in sorted(chosen, key=lambda item: item[1][0], reverse=True):
        trajectory, args, limit_c, *offset = draw
        lift = offset[0] if offset else 0.0
        out.append((name, [(t, lift + c) for t, c in trajectory(*args)], limit_c))
    return out


def wire_heat(ctx, solutions) -> list:
    """Each wire's current against 80% of its ampacity in the day's air, its steady temperature,
    and its temperature after the burst, against its insulation's limit less the margin."""
    from pcs14.electrical.checks import STEADY, Finding, _ok, _where

    numbers = ctx.numbers
    steady, bursts = {}, {}
    for key, solution in solutions.items():
        for label, amps in solution.wires.items():
            if key[1] in STEADY and amps >= steady.get(label, (-1.0,))[0]:
                steady[label] = (amps, _where(key))
            if key[1] == "burst" and amps >= bursts.get(label, (-1.0,))[0]:
                bursts[label] = (amps, _where(key))
    runs = {run.label: run for run in ctx.design.wires}
    ratings = {}
    findings = []
    for label, (amps, where) in sorted(steady.items()):
        run = runs[label]
        table = ctx.parts[run.wire]
        burst_amps, burst_where = bursts.get(label, (0.0, ""))
        model, limit_c = _wire_model(ctx, run)
        if model is None or max(amps, burst_amps) < 0.01:
            continue
        if (run.wire, run.awg) not in ratings:
            ratings[(run.wire, run.awg)] = model.ampacity(table.insulation_max_c, numbers.air_c)
        rating = ratings[(run.wire, run.awg)]
        share = numbers.continuous_share * rating
        kind = f"{run.awg} AWG {model.insulation.name}"
        findings.append(
            Finding(
                "wire current",
                label,
                _ok(amps, share),
                amps,
                share,
                "A",
                where,
                f"{amps:.2f} A in {kind}, which carries {rating:.1f} A to its "
                f"{table.insulation_max_c:g} C limit in {numbers.air_c:g} C air",
            )
        )
        hot = model.steady(amps, numbers.air_c).conductor_c
        findings.append(
            Finding(
                "wire temperature",
                label,
                _ok(hot, limit_c),
                hot,
                limit_c,
                "C",
                where,
                f"{hot:.0f} C at {amps:.2f} A in {kind}, good to {table.insulation_max_c:g} C",
            )
        )
        if burst_amps > amps + 0.5:  # only wires the burst really changes
            end = model.burst(hot, burst_amps, numbers.burst_s, numbers.air_c)
            findings.append(
                Finding(
                    "wire burst",
                    label,
                    _ok(end, limit_c),
                    end,
                    limit_c,
                    "C",
                    burst_where,
                    f"{burst_amps:.1f} A for {numbers.burst_s:g} s from {hot:.0f} C ends at "
                    f"{end:.0f} C in {kind}",
                )
            )
    return findings


def connector_heat(ctx, solutions) -> list:
    """The power connectors' temperature, steady and through the burst, from their makers'
    rated rise."""
    from pcs14.electrical.checks import STEADY, Finding, _ok, _where

    numbers = ctx.numbers
    steady, bursts = {}, {}
    for key, solution in solutions.items():
        for ref, amps in solution.contacts.items():
            if key[1] in STEADY and amps >= steady.get(ref, (-1.0,))[0]:
                steady[ref] = (amps, _where(key))
            if key[1] == "burst" and amps >= bursts.get(ref, (-1.0,))[0]:
                bursts[ref] = (amps, _where(key))
    findings = []
    for ref, (amps, where) in sorted(steady.items()):
        model, limit_c = _connector_model(ctx, ref)
        if model is None:
            continue
        connector = ctx.wiring.board_of(ref).block.connector(ref.split(".")[1])
        family = ctx.parts[connector.family]
        rating = family.electrical.rating
        rests = ctx.rests_on(connector.family, "rating")
        family_rests = tuple(
            f"{connector.family}: {e}"
            for e in family.electrical.estimates
            if e.startswith("rating")
        )
        rise = model.steady_rise(amps)
        findings.append(
            Finding(
                "connector temperature",
                ref,
                _ok(numbers.air_c + rise, limit_c),
                numbers.air_c + rise,
                limit_c,
                "C",
                where,
                f"{amps:.1f} A rises {rise:.0f} K over the {numbers.air_c:g} C air; Amass rates "
                f"{rating.temp_rise_c:g} K at {rating.continuous_a:g} A",
                rests + family_rests,
            )
        )
        burst_amps, burst_where = bursts.get(ref, (0.0, ""))
        if burst_amps > 1.05 * amps:
            end = model.burst_rise(rise, burst_amps, numbers.burst_s)
            findings.append(
                Finding(
                    "connector burst",
                    ref,
                    _ok(numbers.air_c + end, limit_c),
                    numbers.air_c + end,
                    limit_c,
                    "C",
                    burst_where,
                    f"{burst_amps:.0f} A for {numbers.burst_s:g} s ends {end:.0f} K over the air "
                    f"(heating with a {model.time_constant:.0f} s time constant)",
                    family_rests,
                )
            )
    return findings


def esc_and_motors(ctx, solutions, build) -> list:
    """Each motor's current against the ESC's per-motor ratings and the motor's own."""
    from pcs14.electrical.checks import STEADY, Finding, _ok, _where

    steady = max(
        ((s.case.motor_amps, _where(k)) for k, s in solutions.items() if k[1] in STEADY),
        default=None,
    )
    burst = max(
        ((s.case.motor_amps, _where(k)) for k, s in solutions.items() if k[1] == "burst"),
        default=None,
    )
    if steady is None or burst is None:
        return []
    esc, motor = build.esc, build.motor
    share = ctx.numbers.continuous_share * esc.continuous_a_per_motor
    return [
        Finding(
            "ESC current",
            esc.id,
            _ok(steady[0], share),
            steady[0],
            share,
            "A",
            steady[1],
            f"{steady[0]:.1f} A a motor, against {ctx.numbers.continuous_share:.0%} of its "
            f"{esc.continuous_a_per_motor:g} A",
        ),
        Finding(
            "ESC burst",
            esc.id,
            _ok(burst[0], esc.burst_a_per_motor),
            burst[0],
            esc.burst_a_per_motor,
            "A",
            burst[1],
            f"{burst[0]:.1f} A a motor at the cap, against its {esc.burst_a_per_motor:g} A burst",
        ),
        Finding(
            "motor current",
            motor.id,
            _ok(burst[0], motor.max_current_a),
            burst[0],
            motor.max_current_a,
            "A",
            burst[1],
            f"{burst[0]:.1f} A at the cap, against its {motor.max_current_a:g} A peak",
        ),
    ]
