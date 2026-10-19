"""The current in every wire and the voltage at every pin, for one module combination and one
flight phase.

Each net is a small resistor network: every wire is a resistor from its gauge and length,
every mated contact a resistor from its maker's contact resistance, and the joins inside a
board (its ground pins, a supply's several pins) next to nothing. Supplies hold their pins at
their voltage, measured from their own ground pin; loads draw their current; the battery's
plus sits at the pack's voltage under this phase's current. Nets are solved one at a time,
from the battery outward, through fuses (their cold resistance), regulators (a switching one
draws its output power over its efficiency, a linear one its output current) and diodes (the
one with the highest anode carries the load, less its forward drop). The ground net gets
solved last, with every board's return current, so parallel grounds split the way they
would. A few passes settle the regulators, whose input current depends on their input volts.

The ESC takes the battery current the sizing model says, less what everything else on the
pack takes, and each motor lead carries the motor's share. Lead currents are taken as the
motor's input current, a simplification: real phase currents depend on the ESC's duty cycle.
"""

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from pcs14.electrical.model import PACK, ConnectionList
from pcs14.electrical.validate import GROUND, Wiring

TINY = 1e-6  # ohms, a join inside a board
DEFAULT_CONTACT = 1e-3  # ohms, for a connector family with no published contact resistance
DEFAULT_EFFICIENCY = 0.85  # a switching supply that doesn't say
PASSES = 6  # demands and voltages, back and forth
SWEEPS = 6  # voltages outward through a chain of supplies
MOTORS = 4


@dataclass(frozen=True)
class Case:
    name: str  # hover, cruise, burst, worst
    pack_volts: float  # at the pack, under this phase's current
    draw: Literal["typical", "worst"]
    battery_amps: float | None = None  # the sizing model's total, when there's an ESC
    motor_amps: float = 0.0  # in each motor lead


@dataclass
class Solution:
    modules: frozenset[str]
    case: Case
    wires: dict[str, float] = field(default_factory=dict)  # label -> amps
    resistances: dict[str, float] = field(default_factory=dict)  # label -> ohms
    contacts: dict[str, float] = field(default_factory=dict)  # mated pin (a side) -> amps
    pins: dict[str, float] = field(default_factory=dict)  # volts over the board's own ground
    absolute: dict[str, float] = field(default_factory=dict)  # volts over the pack's minus
    ground: dict[str, float] = field(default_factory=dict)  # each board's ground, over the pack's
    supplies: dict[str, float] = field(default_factory=dict)  # board.output -> amps out
    inputs: dict[str, float] = field(default_factory=dict)  # board.output -> amps in
    elements: dict[str, float] = field(default_factory=dict)  # board.element -> amps

    def wire_amps(self, label: str) -> float:
        return self.wires[label]

    def volts(self, ref: str) -> float:
        return self.pins[ref]

    def supply_amps(self, name: str) -> float:
        return self.supplies[name]

    def element_amps(self, name: str) -> float:
        return self.elements.get(name, 0.0)


class _Network:
    """The wires, contacts and board joins, as resistor edges between pins."""

    def __init__(self, wiring: Wiring, design: ConnectionList, parts, lengths, boards):
        self.edges = []  # (a, b, ohms, kind, key)
        names = {b.name for b in boards}
        here = lambda ref: ref.split(".", 1)[0] in names  # noqa: E731
        for run in design.wires:
            if not all(here(ref) for ref in run.ends):
                continue
            table = parts[run.wire]
            length = run.length if run.length is not None else lengths.get(run.route, 0.0)
            ohms = max(table.gauge(run.awg).resistance_per_m * length, TINY)
            self.edges.append((*run.ends, ohms, "wire", run.label))
        for mate in design.mates:
            if not (here(mate.a) and here(mate.b)):
                continue
            connector = wiring.board_of(mate.a).block.connector(mate.a.split(".", 1)[1])
            family = parts.get(connector.family)
            rating = getattr(getattr(family, "electrical", None), "rating", None)
            ohms = (rating.contact_resistance if rating else None) or DEFAULT_CONTACT
            for pin in connector.pins:
                a, b = f"{mate.a}.{pin.name}", f"{mate.b}.{pin.name}"
                self.edges.append((a, b, ohms, "contact", a))
        for link in design.links:
            refs = [ref for ref in link.pins if here(ref)]
            for a, b in zip(refs, refs[1:], strict=False):
                self.edges.append((a, b, TINY, "link", link.name))
        for board in boards:
            grounds = [board.full(ref) for ref, pin in board.block.pins() if pin.role == GROUND]
            for a, b in zip(grounds, grounds[1:], strict=False):
                self.edges.append((a, b, TINY, "board", board.name))
            for group in board.block.joined:
                for a, b in zip(group, group[1:], strict=False):
                    self.edges.append((board.full(a), board.full(b), TINY, "board", board.name))
            for output in board.block.outputs:
                if output.kind == "through" and output.fed_from:
                    for ref in output.pins:
                        key = f"{board.name}.{output.name}"
                        self.edges.append(
                            (board.full(output.fed_from), board.full(ref), TINY, "through", key)
                        )


def _solve_net(nodes, edges, fixed, injections):
    """Nodal analysis: `fixed` maps nodes to volts, `injections` maps nodes to amps flowing
    into the network there (a load is negative). Returns every node's volts."""
    index = {node: i for i, node in enumerate(nodes)}
    n = len(nodes)
    g = np.zeros((n, n))
    for a, b, ohms, *_ in edges:
        i, j = index[a], index[b]
        c = 1.0 / ohms
        g[i, i] += c
        g[j, j] += c
        g[i, j] -= c
        g[j, i] -= c
    free = [i for i, node in enumerate(nodes) if node not in fixed]
    held = [i for i, node in enumerate(nodes) if node in fixed]
    volts = np.zeros(n)
    for i in held:
        volts[i] = fixed[nodes[i]]
    if free:
        rhs = np.array([injections.get(nodes[i], 0.0) for i in free])
        if held:
            rhs -= g[np.ix_(free, held)] @ volts[held]
        volts[free] = np.linalg.solve(g[np.ix_(free, free)], rhs)
    return {node: volts[index[node]] for node in nodes}


def solve_case(
    design: ConnectionList, parts, listed, lengths, modules, case: Case, pack_volts_max: float
) -> Solution:
    """`lengths` maps the CAD's wire routes to meters."""
    return _Solver(design, parts, listed, lengths, frozenset(modules), case, pack_volts_max).run()


class _Solver:
    def __init__(self, design, parts, listed, lengths, modules, case, pack_volts_max):
        self.design, self.parts, self.case, self.modules = design, parts, case, modules
        self.wiring = Wiring(design, parts, listed, set(lengths), pack_volts_max)
        self.boards = self.wiring.present(modules)
        self.network = _Network(self.wiring, design, parts, lengths, self.boards)
        nets = self.wiring.nets(modules)
        self.net_of = {ref: nets.find(ref) for b in self.boards for ref in b.refs()}
        self.members = {}
        for ref, root in self.net_of.items():
            self.members.setdefault(root, []).append(ref)
        self.edges_in = {}
        for edge in self.network.edges:
            self.edges_in.setdefault(self.net_of[edge[0]], []).append(edge)
        self.fuse_ohms = {}
        for choice in design.fuses:
            family = parts[choice.family].electrical.fuse
            self.fuse_ohms[choice.element] = family.rating(choice.rated_a).cold_resistance
        self.plus, self.minus = f"{PACK}.XT60.+", f"{PACK}.XT60.-"
        self.ground_net = self.net_of[self.minus]
        self.esc = next((b for b in self.boards if _kind(design, parts, b) == "esc"), None)
        self.cathodes = {}  # the diodes feeding each cathode net, by anode
        for board in self.boards:
            for element in board.block.elements:
                if element.kind == "diode":
                    anode, cathode = (board.full(ref) for ref in element.between)
                    self.cathodes.setdefault(self.net_of[cathode], []).append(anode)
        self.absolute = {ref: 0.0 for ref in self.net_of}
        self.absolute[self.plus] = case.pack_volts
        self.ground = {b.name: 0.0 for b in self.boards}
        for board in self.boards:  # start every supply at its own voltage
            for output in board.block.outputs:
                for ref in output.pins:
                    self.absolute[board.full(ref)] = output.volts
        self.fixed_at = {}

    def run(self) -> Solution:
        self.cache, self.sinks = {}, {}  # first, every net at its no-load voltage
        self.supplies, self.inputs, self.elements = {}, {}, {}
        self.voltages()
        for _ in range(PASSES):
            self.demands()
            self.voltages()
            self.grounds()
        return self.results()

    # how much each pin takes out of its net

    def demands(self):
        self.cache, self.sinks = {}, {}
        self.supplies, self.inputs, self.elements = {}, {}, {}
        for root in self.members:
            self.net_demand(root)
        if self.esc is not None and self.case.battery_amps is not None and self.esc.block.draws:
            pack_net = self.net_of[self.plus]
            others = sum(a for ref, a in self.sinks.items() if self.net_of[ref] == pack_net)
            pin = self.esc.full(self.esc.block.draws[0].pin)
            self.sinks[pin] = self.sinks.get(pin, 0.0) + max(self.case.battery_amps - others, 0.0)

    def net_demand(self, root, seen=()):
        if root in self.cache:
            return self.cache[root]
        if root in seen:
            return 0.0
        seen = (*seen, root)
        total = sum(self.sink_amps(ref, seen) for ref in self.members[root])
        self.cache[root] = total
        return total

    def sink_amps(self, ref, seen):
        board = self.wiring.board_of(ref)
        local = ref.split(".", 1)[1]
        amps = 0.0
        for draw in board.block.draws:
            if draw.pin == local:
                amps += draw.typical_a if self.case.draw == "typical" else draw.worst_a
        for output in board.block.outputs:
            if output.fed_from == local and output.kind != "through":
                out_net = self.net_of[board.full(output.pins[0])]
                out = self.net_demand(out_net, seen) + output.own_a
                name = f"{board.name}.{output.name}"
                self.supplies[name] = out
                if output.kind == "linear":
                    draw_in = out
                else:
                    # a buck converter can't run on less than its own output
                    v_in = max(self.absolute.get(ref, 0.0) - self.ground[board.name], output.volts)
                    efficiency = output.efficiency or DEFAULT_EFFICIENCY
                    draw_in = output.volts * out / (efficiency * v_in)
                self.inputs[name] = draw_in
                amps += draw_in
        for element in board.block.elements:
            a, b = (board.full(r) for r in element.between)
            if a != ref:
                continue
            name = f"{board.name}.{element.name}"
            if element.kind == "fuse":
                self.elements[name] = self.net_demand(self.net_of[b], seen)
            elif element.kind == "diode":
                feeders = self.cathodes[self.net_of[b]]
                best = max(self.absolute.get(f, 0.0) for f in feeders)
                winners = [f for f in feeders if self.absolute.get(f, 0.0) >= best - 1e-6]
                demand = self.net_demand(self.net_of[b], seen)
                self.elements[name] = demand / len(winners) if ref in winners else 0.0
            else:
                continue
            amps += self.elements[name]
        self.sinks[ref] = amps
        return amps

    # the voltages, from the battery outward

    def voltages(self):
        # a few sweeps, so a chain (pack, fuse, regulator, diode, regulator) settles in order
        for _ in range(SWEEPS):
            self.sweep()

    def sweep(self):
        fixed_at = {self.net_of[self.plus]: {self.plus: self.case.pack_volts}}
        for board in self.boards:
            for output in board.block.outputs:
                if output.kind == "through":
                    continue
                for ref in output.pins:
                    held = output.volts + self.ground[board.name]
                    fixed_at.setdefault(self.net_of[board.full(ref)], {})[board.full(ref)] = held
            for element in board.block.elements:
                a, b = (board.full(r) for r in element.between)
                name = f"{board.name}.{element.name}"
                amps = self.elements.get(name, 0.0)
                if element.kind == "fuse":
                    drop = amps * self.fuse_ohms.get(name, TINY)
                elif element.kind == "diode" and amps > 0:
                    drop = board.block.diode.forward_volts(amps)
                else:
                    continue
                fixed_at.setdefault(self.net_of[b], {})[b] = self.absolute.get(a, 0.0) - drop
        self.fixed_at = fixed_at
        for root, refs in self.members.items():
            if root == self.ground_net or not fixed_at.get(root):
                continue
            injections = {ref: -self.sinks.get(ref, 0.0) for ref in refs}
            edges = self.edges_in.get(root, [])
            self.absolute.update(_solve_net(refs, edges, fixed_at[root], injections))

    # the ground net, with every board's return current

    def grounds(self):
        returns = {}
        for root, refs in self.members.items():
            if root == self.ground_net or not self.fixed_at.get(root):
                continue
            for ref in refs:
                board = ref.split(".", 1)[0]
                if ref in self.fixed_at[root]:
                    out = 0.0
                    for a, b, ohms, *_ in self.edges_in.get(root, []):
                        if ref in (a, b):
                            other = b if a == ref else a
                            out += (self.absolute[ref] - self.absolute[other]) / ohms
                    returns[board] = returns.get(board, 0.0) - out
                else:
                    returns[board] = returns.get(board, 0.0) + self.sinks.get(ref, 0.0)
        injections = {}
        for board in self.boards:
            grounds = [board.full(r) for r, p in board.block.pins() if p.role == GROUND]
            if board.name == PACK or not grounds or self.net_of[grounds[0]] != self.ground_net:
                continue
            injections[grounds[0]] = injections.get(grounds[0], 0.0) + returns.get(board.name, 0.0)
        refs = self.members[self.ground_net]
        edges = self.edges_in.get(self.ground_net, [])
        self.absolute.update(_solve_net(refs, edges, {self.minus: 0.0}, injections))
        for board in self.boards:
            grounds = [board.full(r) for r, p in board.block.pins() if p.role == GROUND]
            self.ground[board.name] = self.absolute[grounds[0]] if grounds else 0.0

    def results(self) -> Solution:
        solution = Solution(self.modules, self.case)
        solved = {r for r in self.members if r == self.ground_net or self.fixed_at.get(r)}
        motors = {b.name for b in self.boards if _kind(self.design, self.parts, b) == "motor"}
        supplies = dict(self.supplies)
        for a, b, ohms, kind, key in self.network.edges:
            amps = 0.0
            if self.net_of[a] in solved:
                amps = abs(self.absolute[a] - self.absolute[b]) / ohms
            if kind == "wire":
                if a.split(".", 1)[0] in motors or b.split(".", 1)[0] in motors:
                    amps = self.case.motor_amps
                solution.wires[key] = amps
                solution.resistances[key] = ohms
            elif kind == "contact":
                solution.contacts[key] = amps
            elif kind == "through":
                supplies[key] = supplies.get(key, 0.0) + amps
        for ref, root in self.net_of.items():
            if root in solved:
                board = ref.split(".", 1)[0]
                solution.absolute[ref] = self.absolute[ref]
                solution.pins[ref] = self.absolute[ref] - self.ground.get(board, 0.0)
        solution.ground = dict(self.ground)
        solution.supplies = supplies
        solution.inputs = dict(self.inputs)
        solution.elements = dict(self.elements)
        return solution


def _kind(design: ConnectionList, parts, board) -> str:
    """The catalog type of a board's part: esc, motor, component; the battery is "pack"."""
    if board.name not in design.boards:
        return PACK
    return getattr(parts[design.boards[board.name].part], "type", "")


def flight_cases(build, targets, setup) -> list[Case]:
    """The phases each combination gets checked in, from the sizing model. Hover and cruise use
    the pessimistic power model at the reserve, where the pack is lowest and the current
    highest; the burst is full throttle at the reserve, which the firmware caps; and "worst"
    is a hover with every 5 V part at its worst (servos stalled, the Pi flat out)."""
    from pcs14.sizing.battery import Pack
    from pcs14.sizing.flight import avionics_power, fly, power_model

    margin = targets.growth_margin if setup.name == targets.sizing_case else 0.0
    model = power_model(build, setup, margin, pessimistic=True)
    pack = Pack(build.pack)
    reserve = pack.soc_at_reserve(targets.reserve_fraction)
    avionics = avionics_power(build, setup)
    cases = []
    for name, speed in (("hover", 0.0), ("cruise", targets.cruise_speed)):
        end = fly(model, pack, speed, targets.reserve_fraction).samples[-1]
        motors = max(end.current - avionics / end.voltage, 0.0) / MOTORS
        cases.append(Case(name, end.voltage, "typical", end.current, motors))
    full = model.rotor.full_throttle(pack, reserve)
    volts = pack.terminal_voltage(reserve, full.current)
    motors = max(full.current - avionics / volts, 0.0) / MOTORS
    cases.append(Case("burst", volts, "typical", full.current, motors))
    hover = cases[0]
    cases.append(Case("worst", hover.pack_volts, "worst", hover.battery_amps, hover.motor_amps))
    return cases


def solve_all(design: ConnectionList, catalog, build, targets, cad_settings) -> dict:
    """Every module combination in every flight case: {(setup name, case name): Solution}."""
    from pcs14.cad.assembly import wire_length
    from pcs14.electrical.validate import listed_in

    parts = {part.id: part for part in catalog.all_parts()}
    listed = listed_in(build)
    lengths = {wire.name: wire_length(wire) for wire in cad_settings.wires}
    pack_max = build.pack.cell.max_voltage_v * build.pack.series
    out = {}
    for setup in targets.combinations():
        for case in flight_cases(build, targets, setup):
            out[(setup.name, case.name)] = solve_case(
                design, parts, listed, lengths, setup.modules, case, pack_max
            )
    return out
