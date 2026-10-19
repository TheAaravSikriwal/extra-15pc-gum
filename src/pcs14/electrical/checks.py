"""The electrical checks, with the spec's numbers (design/electrical.yaml, under checks).

- Connectors: every contact carrying current runs at no more than 80% of its family's
  continuous rating, at the highest steady current it sees (hovering or cruising, anywhere).
- Supplies: typical draw at no more than 80% of the continuous rating; the worst case
  (every servo stalled) under the peak rating, or the continuous one if there's no peak.
- Load voltages: every load stays inside its range with the margin at both ends, in every
  case; some pins have firmer floors (the Pi's).
- The main path: no more than 2% of the pack's nominal voltage lost between the pack and the
  ESC at the current cap, out and back.
- Fuses: each holds 1.25 times its steady current, and lets through less energy (I2t) than it
  takes to heat the wire after it from the hot day's air to its insulation's limit.
- Cell links: through the burst at the cap, a link stays the spec's margin under its joint's
  limit; on a dead short at the far end of the battery leads, it melts in under a second.
  Both by Onderdonk's equation, which ignores cooling: right for the short, pessimistic for
  the burst.
- Backups: with a backed-up supply switched off, the loads that have a second feed still get
  their volts, and the supply behind the backup stays inside its continuous rating.

Wires get judged by how hot they run, in pcs14.electrical.thermal.
"""

import math
from dataclasses import dataclass

from pcs14.electrical.loads import Case, solve_case
from pcs14.electrical.model import PACK, CheckNumbers, ConnectionList
from pcs14.electrical.validate import Wiring

STEADY = ("hover", "cruise")
COPPER_DENSITY = 8960.0  # kg/m3
COPPER_HEAT = 385.0  # J/(kg K)
COPPER_RESISTIVITY = 1.724e-8  # ohm m at 20 C (the IACS standard)
COPPER_ALPHA = 0.00393  # per K, near 20 C
COPPER_MELTS = 1083.0  # C
CIRCULAR_MIL = 5.067075e-10  # m2


@dataclass(frozen=True)
class Finding:
    check: str
    subject: str
    passed: bool
    value: float | None
    limit: float | None
    unit: str
    where: str  # which combination and case gave the value
    detail: str
    rests_on: tuple[str, ...] = ()


def awg_area(awg: int) -> float:
    """Copper area in m2, from the AWG definition: 0.005 inches at 36, ninety-two steps to 0000."""
    diameter = 0.127e-3 * 92 ** ((36 - awg) / 39)
    return math.pi / 4 * diameter**2


def onderdonk_seconds(area: float, amps: float, ambient_c: float, melt_c: float = COPPER_MELTS):
    """How long `amps` takes to melt copper of this area (m2), with no cooling at all."""
    cmil = area / CIRCULAR_MIL
    return cmil**2 * math.log10(1 + (melt_c - ambient_c) / (234 + ambient_c)) / (33 * amps**2)


def onderdonk_celsius(area: float, amps: float, seconds: float, ambient_c: float) -> float:
    """How hot that copper gets after `seconds` at `amps`, the same equation turned around."""
    cmil = area / CIRCULAR_MIL
    return ambient_c + (234 + ambient_c) * (10 ** (33 * amps**2 * seconds / cmil**2) - 1)


def adiabatic_i2t(area: float, from_c: float, to_c: float) -> float:
    """A2s to heat copper of this area from one temperature to another, with no cooling, its
    resistance rising as it goes."""
    rise = math.log((1 + COPPER_ALPHA * (to_c - 20)) / (1 + COPPER_ALPHA * (from_c - 20)))
    return area**2 * COPPER_DENSITY * COPPER_HEAT / (COPPER_RESISTIVITY * COPPER_ALPHA) * rise


@dataclass
class Context:
    design: ConnectionList
    parts: dict
    wiring: Wiring
    numbers: CheckNumbers
    pack_nominal: float

    @classmethod
    def make(cls, design, parts, listed, numbers, pack_nominal, pack_max=25.2):
        return cls(
            design, parts, Wiring(design, parts, listed, set(), pack_max), numbers, pack_nominal
        )

    def part_id(self, board: str) -> str:
        return self.design.boards[board].part if board in self.design.boards else PACK

    def rests_on(self, board: str, *paths: str) -> tuple[str, ...]:
        """The estimates a check on these parts of a board rests on."""
        found = self.wiring.boards.get(board)
        if found is None or board == PACK:
            return ()
        block, part = found.block, self.part_id(board)
        out = []
        if block.source.kind.value == "estimate":
            out.append(f"{part}: its whole electrical block")
        for estimate in block.estimates:
            if any(estimate == p or estimate.startswith(f"{p}.") for p in paths):
                out.append(f"{part}: {estimate}")
        return tuple(out)


def _where(key) -> str:
    return f"{key[0]}, {key[1]}"


def _ok(value, limit, below=True) -> bool:
    return value <= limit + 1e-9 if below else value >= limit - 1e-9


def connector_currents(ctx: Context, solutions) -> list[Finding]:
    worst = {}  # subject -> (amps, where, rating, connector)
    for key, solution in solutions.items():
        if key[1] not in STEADY:
            continue
        amps_at = dict(solution.contacts)
        for run in ctx.design.wires:
            amps = solution.wires.get(run.label, 0.0)
            for ref in run.ends:
                amps_at[ref] = max(amps_at.get(ref, 0.0), amps)
        for ref, amps in amps_at.items():
            board = ctx.wiring.board_of(ref)
            if board is None or amps < 1e-3:
                continue
            connector = board.block.connector(ref.split(".")[1])
            family = ctx.parts.get(connector.family)
            rating = getattr(getattr(family, "electrical", None), "rating", None)
            if rating is None:
                continue
            if ref not in worst or amps > worst[ref][0]:
                worst[ref] = (amps, _where(key), rating, connector)
    findings = []
    for ref, (amps, where, rating, connector) in sorted(worst.items()):
        limit = ctx.numbers.continuous_share * rating.continuous_a
        board = ref.split(".")[0]
        findings.append(
            Finding(
                "connector current",
                ref,
                _ok(amps, limit),
                amps,
                limit,
                "A",
                where,
                f"{amps:.2f} A through a {connector.family} contact rated "
                f"{rating.continuous_a:g} A",
                ctx.rests_on(board, f"connectors[{connector.name}]"),
            )
        )
    return findings


def supplies(ctx: Context, solutions) -> list[Finding]:
    seen = {}  # (name, kind) -> (amps, where)
    for key, solution in solutions.items():
        kind = "worst" if solution.case.draw == "worst" else "typical"
        if kind == "typical" and key[1] not in STEADY:
            continue
        for name, amps in solution.supplies.items():
            if (name, kind) not in seen or amps > seen[(name, kind)][0]:
                seen[(name, kind)] = (amps, _where(key))
    findings = []
    for (name, kind), (amps, where) in sorted(seen.items()):
        board, output_name = name.split(".", 1)
        output = ctx.wiring.boards[board].block.output(output_name)
        if kind == "typical":
            limit = ctx.numbers.supply_typical_share * output.continuous_a
            rated = f"{ctx.numbers.supply_typical_share:.0%} of its {output.continuous_a:g} A"
        else:
            limit = output.peak_a or output.continuous_a
            rated = f"its {limit:g} A {'peak' if output.peak_a else 'continuous'} rating"
        findings.append(
            Finding(
                f"supply, {kind}",
                name,
                _ok(amps, limit),
                amps,
                limit,
                "A",
                where,
                f"{amps:.2f} A against {rated}",
                ctx.rests_on(board, f"outputs[{output_name}]"),
            )
        )
    return findings


def load_voltages(ctx: Context, solutions) -> list[Finding]:
    m = ctx.numbers.load_margin_v
    lows, highs = {}, {}
    for key, solution in solutions.items():
        for board in ctx.wiring.boards.values():
            for draw in board.block.draws:
                ref = board.full(draw.pin)
                if ref not in solution.pins:
                    continue
                volts = solution.pins[ref]
                if ref not in lows or volts < lows[ref][0]:
                    lows[ref] = (volts, _where(key), draw)
                if ref not in highs or volts > highs[ref][0]:
                    highs[ref] = (volts, _where(key), draw)
    findings = []
    for ref in sorted(lows):
        low_v, low_where, draw = lows[ref]
        high_v, high_where, _ = highs[ref]
        floor = max(draw.min_v + m, ctx.numbers.pin_minimums.get(ref, -math.inf))
        ceiling = draw.max_v - m
        low_ok, high_ok = _ok(low_v, floor, below=False), _ok(high_v, ceiling)
        if not low_ok or high_ok:
            value, limit, where = low_v, floor, low_where
        else:
            value, limit, where = high_v, ceiling, high_where
        findings.append(
            Finding(
                "load voltage",
                ref,
                low_ok and high_ok,
                value,
                limit,
                "V",
                where,
                f"{low_v:.3f} to {high_v:.3f} V across the cases, inside {floor:.2f} to "
                f"{ceiling:.2f} V ({draw.min_v:g} to {draw.max_v:g} V, less the margin)",
                ctx.rests_on(ref.split(".")[0], f"draws[{draw.pin}]"),
            )
        )
    return findings


def main_drop(ctx: Context, solutions) -> list[Finding]:
    esc = next(
        (
            b
            for b in ctx.wiring.boards.values()
            if getattr(ctx.parts.get(ctx.part_id(b.name)), "type", "") == "esc"
        ),
        None,
    )
    if esc is None or not esc.block.draws:
        return []
    pin = esc.full(esc.block.draws[0].pin)
    worst = None
    for key, solution in solutions.items():
        if key[1] != "burst" or pin not in solution.absolute:
            continue
        drop = (
            solution.absolute[f"{PACK}.XT60.+"] - solution.absolute[pin] + solution.ground[esc.name]
        )
        if worst is None or drop > worst[0]:
            worst = (drop, _where(key), solution.case.battery_amps)
    if worst is None:
        return []
    drop, where, amps = worst
    limit = ctx.numbers.main_drop_share * ctx.pack_nominal
    return [
        Finding(
            "main path drop",
            f"pack to {pin}",
            _ok(drop, limit),
            drop,
            limit,
            "V",
            where,
            f"{drop * 1000:.0f} mV lost out and back at {amps:.0f} A, against "
            f"{ctx.numbers.main_drop_share:.0%} of the pack's nominal {ctx.pack_nominal:g} V",
        )
    ]


def fuses(ctx: Context, solutions) -> list[Finding]:
    findings = []
    all_modules = frozenset({"V", "P", "C"})
    nets = ctx.wiring.nets(all_modules)
    for choice in ctx.design.fuses:
        board_name, element_name = choice.element.split(".", 1)
        board = ctx.wiring.boards[board_name]
        element = board.block.element(element_name)
        rating = ctx.parts[choice.family].electrical.fuse.rating(choice.rated_a)
        steady, where = 0.0, ""
        for key, solution in solutions.items():
            amps = solution.elements.get(choice.element, 0.0)
            if key[1] in STEADY and amps >= steady:
                steady, where = amps, _where(key)
        needed = ctx.numbers.fuse_hold_factor * steady
        findings.append(
            Finding(
                "fuse holds",
                choice.element,
                _ok(needed, choice.rated_a),
                needed,
                choice.rated_a,
                "A",
                where,
                f"{steady:.2f} A steady, so it needs {needed:.2f} A; "
                f"it's a {choice.rated_a:g} A fuse",
            )
        )
        after = nets.find(board.full(element.between[1]))
        thinnest = None
        for run in ctx.design.wires:
            if any(ref in nets.parent and nets.find(ref) == after for ref in run.ends):
                table = ctx.parts[run.wire]
                if thinnest is None or run.awg > thinnest[0]:
                    thinnest = (run.awg, table, run.label)
        if thinnest is None:
            continue
        awg, table, label = thinnest
        hottest = table.insulation_max_c if table.insulation_max_c is not None else COPPER_MELTS
        takes = adiabatic_i2t(awg_area(awg), ctx.numbers.air_c, hottest)
        findings.append(
            Finding(
                "fuse protects its wire",
                choice.element,
                _ok(rating.melting_i2t_a2s, takes),
                rating.melting_i2t_a2s,
                takes,
                "A2s",
                "on a short",
                f"it lets through {rating.melting_i2t_a2s:g} A2s; {label} ({awg} AWG) takes "
                f"{takes:.0f} A2s to go from {ctx.numbers.air_c:g} to {hottest:g} C",
            )
        )
    return findings


def cell_links(numbers, awg, area, cell_burst_amps, cell_short_amps, joint_max_c) -> list[Finding]:
    subject = f"{awg} AWG cell links"
    hot = onderdonk_celsius(area, cell_burst_amps, numbers.burst_s, numbers.air_c)
    limit = joint_max_c - numbers.temp_margin_c
    blow = onderdonk_seconds(area, cell_short_amps, numbers.air_c)
    return [
        Finding(
            "cell link holds the burst",
            subject,
            _ok(hot, limit),
            hot,
            limit,
            "C",
            "burst",
            f"{cell_burst_amps:.0f} A for {numbers.burst_s:g} s takes it from {numbers.air_c:g} to "
            f"{hot:.0f} C with no cooling; the joint is good to {joint_max_c:g} C",
        ),
        Finding(
            "cell link blows on a short",
            subject,
            _ok(blow, numbers.cell_link_blow_s),
            blow,
            numbers.cell_link_blow_s,
            "s",
            "dead short",
            f"{cell_short_amps:.0f} A a cell melts it in {blow:.2f} s",
        ),
    ]


def backups(ctx: Context, design, parts, listed, lengths, combinations, cases, pack_max):
    """With each backed-up supply off, every load still powered stays in range, and every
    supply stays inside its continuous rating."""
    findings = []
    for name in ctx.numbers.backups:
        for setup_name, modules in combinations:
            hover = next(c for c in cases[setup_name] if c.name == "hover")
            case = Case(
                f"{name} off",
                hover.pack_volts,
                "worst",
                hover.battery_amps,
                hover.motor_amps,
                frozenset({name}),
            )
            solution = solve_case(design, parts, listed, lengths, modules, case, pack_max)
            key = (setup_name, case.name)
            for finding in load_voltages(ctx, {key: solution}):
                findings.append(
                    finding.__class__(**{**finding.__dict__, "check": f"backup: {finding.check}"})
                )
            for supply, amps in solution.supplies.items():
                board, output_name = supply.split(".", 1)
                output = ctx.wiring.boards[board].block.output(output_name)
                findings.append(
                    Finding(
                        "backup: supply",
                        supply,
                        _ok(amps, output.continuous_a),
                        amps,
                        output.continuous_a,
                        "A",
                        _where(key),
                        f"{amps:.2f} A with {name} off, against its {output.continuous_a:g} A",
                    )
                )
    return findings


LI_ION_NOMINAL = 3.6  # V a cell, the usual figure for Li-ion and the P42A's own


def check_design(design: ConnectionList, catalog, build, targets, cad_settings, solutions=None):
    """Every check on the real drone. `solutions` can come from solve_all, to save a rerun."""
    from pcs14.cad.assembly import wire_length
    from pcs14.electrical.loads import flight_cases, solve_all
    from pcs14.electrical.validate import listed_in
    from pcs14.sizing.battery import Pack

    parts = {part.id: part for part in catalog.all_parts()}
    listed = listed_in(build)
    lengths = {wire.name: wire_length(wire) for wire in cad_settings.wires}
    cells = build.pack
    pack_max = cells.cell.max_voltage_v * cells.series
    numbers = design.checks
    ctx = Context(
        design,
        parts,
        Wiring(design, parts, listed, set(lengths), pack_max),
        numbers,
        LI_ION_NOMINAL * cells.series,
    )
    if solutions is None:
        solutions = solve_all(design, catalog, build, targets, cad_settings)
    findings = [
        *connector_currents(ctx, solutions),
        *supplies(ctx, solutions),
        *load_voltages(ctx, solutions),
        *main_drop(ctx, solutions),
        *fuses(ctx, solutions),
    ]
    if design.cell_links is not None:
        pack = Pack(cells)
        bursts = [s for k, s in solutions.items() if k[1] == "burst"]
        burst = max(bursts, key=lambda s: s.case.battery_amps)
        esc_pin = next(
            b.full(b.block.draws[0].pin)
            for b in ctx.wiring.boards.values()
            if getattr(parts.get(ctx.part_id(b.name)), "type", "") == "esc"
        )
        esc_board = esc_pin.split(".")[0]
        lost = burst.absolute[f"{PACK}.XT60.+"] - burst.absolute[esc_pin] + burst.ground[esc_board]
        leads = lost / burst.case.battery_amps
        cells_only = pack.resistance - cells.wiring_resistance
        short = pack.ocv(1.0) / (cells_only + leads)
        links = design.cell_links
        findings += cell_links(
            numbers,
            links.awg,
            awg_area(links.awg),
            burst.case.battery_amps / cells.parallel,
            short / cells.parallel,
            links.joint_max_c,
        )
    setups = targets.combinations()
    cases = {s.name: flight_cases(build, targets, s) for s in setups}
    findings += backups(
        ctx, design, parts, listed, lengths, [(s.name, s.modules) for s in setups], cases, pack_max
    )
    return findings
