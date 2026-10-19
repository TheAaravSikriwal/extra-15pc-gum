"""The connection list's own rules, before any current gets worked out.

For every module combination, the wires, mates and links join pins into nets (with each
board's ground pins, and each supply's pins, joined inside the board). Then:

- every pin, connector, wire table, gauge and route named exists, and every board sits where
  the build lists its part;
- modules join Base only through their connector, never by a wire of their own;
- no line has two drivers, and no two supplies share a net without diodes;
- no pin sees more volts than it takes, with every analog switch checked in both positions;
- every load is powered (from the pack, through fuses, regulators and diodes) and grounded;
- every fuse has a rating;
- the CAN bus has exactly two terminators.
"""

from dataclasses import dataclass, field

from pcs14.catalog.electrical import ElectricalBlock, Pin
from pcs14.electrical.model import PACK, ConnectionList

GROUND = "ground"


@dataclass(frozen=True)
class Problem:
    rule: str
    message: str
    combination: frozenset[str] | None = None  # None: the same in every combination

    def __str__(self) -> str:
        where = "" if self.combination is None else f" (with {_combo(self.combination)})"
        return f"{self.rule}: {self.message}{where}"


def _combo(modules: frozenset[str]) -> str:
    return "+".join(sorted(modules)) or "Base alone"


class _Nets:
    def __init__(self, pins):
        self.parent = {pin: pin for pin in pins}

    def find(self, pin):
        root = pin
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[pin] != root:
            self.parent[pin], pin = root, self.parent[pin]
        return root

    def join(self, a, b):
        if a in self.parent and b in self.parent:
            self.parent[self.find(a)] = self.find(b)

    def copy(self):
        other = _Nets([])
        other.parent = dict(self.parent)
        return other

    def groups(self):
        out = {}
        for pin in self.parent:
            out.setdefault(self.find(pin), []).append(pin)
        return list(out.values())


@dataclass
class _Board:
    name: str
    module: str
    block: ElectricalBlock
    modes: dict = field(default_factory=dict)
    terminator: bool | None = None

    def refs(self):
        return [f"{self.name}.{ref}" for ref, _ in self.block.pins()]

    def pin(self, ref: str) -> Pin | None:
        local = ref.split(".", 1)[1]
        try:
            return self.block.pin(local)
        except KeyError:
            return None

    def direction(self, ref: str) -> str | None:
        local = ref.split(".", 1)[1]
        return self.modes.get(local) or (self.pin(ref).direction if self.pin(ref) else None)

    def full(self, local: str) -> str:
        return f"{self.name}.{local}"


def _pack_block(volts: float) -> ElectricalBlock:
    return ElectricalBlock.model_validate(
        {
            "source": {"kind": "estimate", "note": "the battery, as the connection list sees it"},
            "connectors": [
                {
                    "name": "XT60",
                    "family": "amass-xt60",
                    "pins": [
                        {"name": "+", "role": "power", "volts": volts},
                        {"name": "-", "role": "ground"},
                    ],
                }
            ],
        }
    )


class _Check:
    def __init__(self, design: ConnectionList, parts, listed, routes, pack_volts):
        self.design, self.parts, self.listed, self.routes = design, parts, listed, routes
        self.pack_volts = pack_volts
        self.problems: list[Problem] = []
        self.boards: dict[str, _Board] = {PACK: _Board(PACK, "base", _pack_block(pack_volts))}
        self._boards()

    def add(self, rule, message, combination=None):
        self.problems.append(Problem(rule, message, combination))

    # what's named exists

    def _boards(self):
        for name, board in self.design.boards.items():
            part = self.parts.get(board.part)
            if part is None:
                self.add("boards", f"{name}: there's no part {board.part} in the catalog")
                continue
            if part.electrical is None:
                self.add("boards", f"{name}: {board.part} has no electrical block in the catalog")
                continue
            places = self.listed.get(board.part, set())
            if not places:
                self.add("boards", f"{name}: {board.part} isn't in the build")
                continue
            if board.module is not None:
                module = board.module
                if module not in places:
                    where = ", ".join(sorted(places))
                    self.add(
                        "boards", f"{name}: the build lists {board.part} in {where}, not {module}"
                    )
                    continue
            elif len(places) == 1:
                module = next(iter(places))
            else:
                where = ", ".join(sorted(places))
                self.add("boards", f"{name}: {board.part} is in {where}, so say which with module")
                continue
            self.boards[name] = _Board(name, module, part.electrical, board.modes, board.terminator)
        for name, board in self.boards.items():
            for local in board.modes:
                pin = board.pin(f"{name}.{local}")
                if pin is None or pin.role != "signal":
                    self.add("boards", f"{name}: modes names {local}, which isn't a signal pin")

    def pin(self, ref: str) -> Pin | None:
        board = self.boards.get(ref.split(".", 1)[0])
        return None if board is None or "." not in ref else board.pin(ref)

    def board_of(self, ref: str) -> _Board | None:
        return self.boards.get(ref.split(".", 1)[0])

    def static(self):
        for run in self.design.wires:
            for ref in run.ends:
                if self.pin(ref) is None:
                    self.add("wires", f"{run.label}: {ref} isn't a pin")
            table = self.parts.get(run.wire)
            if table is None or getattr(table, "type", None) != "wire":
                self.add("wires", f"{run.label}: there's no wire table {run.wire}")
            else:
                try:
                    table.gauge(run.awg)
                except KeyError:
                    self.add("wires", f"{run.label}: {run.wire} has no {run.awg} AWG")
            if run.route is None and run.length_mm is None:
                self.add("wires", f"{run.label}: needs a route in design/cad.yaml, or a length")
            elif run.route is not None and run.route not in self.routes:
                self.add(
                    "wires", f"{run.label}: there's no route called {run.route} in design/cad.yaml"
                )
            a, b = (self.board_of(ref) for ref in run.ends)
            if a and b and a.module != b.module:
                self.add(
                    "modules",
                    f"{run.label} joins {a.module} and {b.module} directly: a module only "
                    "connects through its connector",
                )
        for mate in self.design.mates:
            sides = []
            for ref in (mate.a, mate.b):
                board = self.board_of(ref)
                try:
                    sides.append(board.block.connector(ref.split(".", 1)[1]) if board else None)
                except KeyError:
                    sides.append(None)
                if sides[-1] is None:
                    self.add("mates", f"{ref} isn't a connector")
            if None in sides:
                continue
            a, b = sides
            if a.family != b.family:
                self.add("mates", f"{mate.a} ({a.family}) can't plug into {mate.b} ({b.family})")
            names_a, names_b = {p.name for p in a.pins}, {p.name for p in b.pins}
            for name in sorted(names_a ^ names_b):
                self.add("mates", f"{mate.a} and {mate.b} don't both have a {name} pin")
        for link in self.design.links:
            for ref in link.pins:
                if self.pin(ref) is None:
                    self.add("links", f"{link.name}: {ref} isn't a pin")
        chosen = {}
        for choice in self.design.fuses:
            board_name, _, element = choice.element.partition(".")
            board = self.boards.get(board_name)
            found = None
            if board is not None:
                try:
                    found = board.block.element(element)
                except KeyError:
                    found = None
            if found is None or found.kind != "fuse":
                self.add("fuses", f"{choice.element} isn't a fuse")
                continue
            family = self.parts.get(choice.family)
            fuse = getattr(getattr(family, "electrical", None), "fuse", None)
            if fuse is None:
                self.add("fuses", f"{choice.element}: {choice.family} isn't a fuse family")
                continue
            try:
                fuse.rating(choice.rated_a)
            except KeyError:
                self.add(
                    "fuses", f"{choice.element}: {choice.family} has no {choice.rated_a:g} A fuse"
                )
            chosen[choice.element] = choice
        for board in self.boards.values():
            for element in board.block.elements:
                if element.kind == "fuse" and f"{board.name}.{element.name}" not in chosen:
                    self.add("fuses", f"{board.name}.{element.name} needs a rating in fuses")

    # nets, one module combination at a time

    def present(self, modules):
        return [b for b in self.boards.values() if b.module == "base" or b.module in modules]

    def nets(self, modules) -> _Nets:
        boards = self.present(modules)
        names = {b.name for b in boards}
        nets = _Nets([ref for b in boards for ref in b.refs()])
        for run in self.design.wires:
            if all(ref.split(".", 1)[0] in names for ref in run.ends):
                nets.join(*run.ends)
        for mate in self.design.mates:
            if mate.a.split(".", 1)[0] in names and mate.b.split(".", 1)[0] in names:
                for pin in self.board_of(mate.a).block.connector(mate.a.split(".", 1)[1]).pins:
                    nets.join(f"{mate.a}.{pin.name}", f"{mate.b}.{pin.name}")
        for link in self.design.links:
            here = [ref for ref in link.pins if ref.split(".", 1)[0] in names]
            for a, b in zip(here, here[1:], strict=False):
                nets.join(a, b)
        for board in boards:
            grounds = [board.full(ref) for ref, pin in board.block.pins() if pin.role == GROUND]
            for a, b in zip(grounds, grounds[1:], strict=False):
                nets.join(a, b)
            for group in board.block.joined:
                for a, b in zip(group, group[1:], strict=False):
                    nets.join(board.full(a), board.full(b))
            for output in board.block.outputs:
                rail = [board.full(ref) for ref in output.pins]
                if output.kind == "through" and output.fed_from:
                    rail.append(board.full(output.fed_from))
                for a, b in zip(rail, rail[1:], strict=False):
                    nets.join(a, b)
        return nets

    def supplies(self, boards):
        """Pins a supply drives, with its volts and which supply it is: the pack's plus, and
        every regulator's output (one supply, however many pins it comes out on)."""
        out = {f"{PACK}.XT60.+": (self.pack_volts, PACK)}
        for board in boards:
            for output in board.block.outputs:
                if output.kind != "through":
                    for ref in output.pins:
                        out[board.full(ref)] = (output.volts, f"{board.name}.{output.name}")
        return out

    def combination(self, modules):
        boards = self.present(modules)
        nets = self.nets(modules)
        supplies = self.supplies(boards)
        groups = {}
        for board in boards:
            for switch in board.block.switches:
                groups.setdefault((board.name, switch.control), []).append((board, switch))
        states = [("", [])]
        for (board_name, _control), channels in groups.items():
            states.append((f"with {board_name}'s switch high", channels))
        for label, high in states:
            joined = nets.copy()
            for board in boards:
                for switch in board.block.switches:
                    side = switch.high if (board, switch) in high else switch.low
                    joined.join(board.full(switch.common), board.full(side))
            # for voltages, a fuse is just wire, and a diode passes its anode's volts on
            through = joined.copy()
            for board in boards:
                for element in board.block.elements:
                    if element.kind in ("fuse", "diode"):
                        through.join(*(board.full(ref) for ref in element.between))
            self.lines(joined, through, supplies, modules, label)
        self.power(boards, nets, supplies, modules)
        self.can(boards, nets, modules)
        names = {b.name for b in boards}
        for need in self.design.requires:
            if not all(ref.split(".", 1)[0] in names for ref in need.pins):
                continue
            if any(self.pin(ref) is None for ref in need.pins):
                self.add("requires", f"{need.name}: names a pin that isn't there")
                continue
            if len({nets.find(ref) for ref in need.pins}) > 1:
                self.add(
                    "requires", f"{need.name}: {' and '.join(need.pins)} aren't connected", modules
                )

    def lines(self, nets, through, supplies, modules, label):
        suffix = f" {label}" if label else ""
        for group in nets.groups():
            drivers = [ref for ref in group if self.board_of(ref).direction(ref) == "out"]
            if len(drivers) > 1:
                self.add(
                    "drivers",
                    f"two drivers on one line: {', '.join(sorted(drivers))}{suffix}",
                    modules,
                )
            feeding = sorted({supplies[ref][1] for ref in group if ref in supplies})
            if len(feeding) > 1:
                self.add(
                    "supplies",
                    f"two supplies tied together: {', '.join(feeding)}{suffix}",
                    modules,
                )
        for group in through.groups():
            sources = [(supplies[ref][0], ref) for ref in group if ref in supplies]
            for ref in group:
                pin = self.pin(ref)
                if (
                    pin.role == "signal"
                    and pin.volts
                    and self.board_of(ref).direction(ref) in ("out", "both")
                ):
                    sources.append((pin.volts, ref))
            if not sources:
                continue
            volts, source = max(sources)
            for ref in group:
                pin = self.pin(ref)
                if ref != source and pin.max_volts is not None and volts > pin.max_volts + 1e-9:
                    self.add(
                        "levels",
                        f"{volts:g} V from {source} into {ref}, which takes "
                        f"{pin.max_volts:g} V at most{suffix}",
                        modules,
                    )

    def power(self, boards, nets, supplies, modules):
        powered = {nets.find(ref) for ref in supplies if ref.startswith(f"{PACK}.")}
        changed = True
        while changed:
            changed = False
            for board in boards:
                for output in board.block.outputs:
                    if output.fed_from and nets.find(board.full(output.fed_from)) in powered:
                        for ref in output.pins:
                            root = nets.find(board.full(ref))
                            if root not in powered:
                                powered.add(root)
                                changed = True
                for element in board.block.elements:
                    a, b = (nets.find(board.full(ref)) for ref in element.between)
                    if element.kind == "fuse" and (a in powered) != (b in powered):
                        powered |= {a, b}
                        changed = True
                    if element.kind == "diode" and a in powered and b not in powered:
                        powered.add(b)
                        changed = True
        for board in boards:
            needs = [d.pin for d in board.block.draws]
            needs += [
                o.fed_from for o in board.block.outputs if o.fed_from and o.fed_from not in needs
            ]
            for ref in needs:
                if nets.find(board.full(ref)) not in powered:
                    self.add("power", f"{board.full(ref)} isn't powered", modules)
        ground = nets.find(f"{PACK}.XT60.-")
        for board in boards:
            grounds = [board.full(ref) for ref, pin in board.block.pins() if pin.role == GROUND]
            if board.name != PACK and grounds and nets.find(grounds[0]) != ground:
                self.add("power", f"{board.name} isn't grounded", modules)
            for element in board.block.elements:
                a, b = (nets.find(board.full(ref)) for ref in element.between)
                if element.kind in ("fuse", "diode") and a == b:
                    self.add("power", f"{board.name}.{element.name} is shorted out", modules)

    def can(self, boards, nets, modules):
        buses, ports = {}, {}
        for board in boards:
            for connector in board.block.connectors:
                names = {p.name for p in connector.pins}
                if {"CAN_P", "CAN_N"} <= names:
                    p = nets.find(board.full(f"{connector.name}.CAN_P"))
                    n = nets.find(board.full(f"{connector.name}.CAN_N"))
                    buses.setdefault(p, set()).add(n)
                    ports.setdefault(p, set()).add(f"{board.name}.{connector.name}")
                    if board.terminator:
                        buses.setdefault((p, "ends"), set()).add(board.name)
        for p, ns in list(buses.items()):
            if isinstance(p, tuple):
                continue
            if len(ports[p]) < 2 and not any(
                nets.find(ref) == p for run in self.design.wires for ref in run.ends
            ):
                continue  # a CAN plug with nothing in it isn't a bus
            if len(ns) > 1:
                self.add(
                    "can", "CAN_P is joined to more than one CAN_N net: crossed wires", modules
                )
                continue
            n = next(iter(ns))
            if p == n:
                self.add("can", "CAN_P and CAN_N are joined together", modules)
                continue
            ends = set(buses.get((p, "ends"), set()))
            for board in boards:
                for element in board.block.elements:
                    if element.kind == "resistor":
                        a, b = (nets.find(board.full(ref)) for ref in element.between)
                        if {a, b} == {p, n}:
                            ends.add(f"{board.name}.{element.name}")
            if len(ends) != 2:
                listed = ", ".join(sorted(ends)) or "none"
                self.add(
                    "can",
                    f"the CAN bus has {len(ends)} terminator{'' if len(ends) == 1 else 's'} "
                    f"({listed}); it needs exactly two, one "
                    "at each end",
                    modules,
                )


def validate(
    design: ConnectionList, parts, listed, routes, combinations, pack_volts
) -> list[Problem]:
    """Every problem with the connection list. `parts` maps catalog ids to parts (wire tables
    included), `listed` maps each part id to where the build lists it (base, V, P, C), `routes`
    is the CAD's wire route names, and `pack_volts` the pack's fully charged voltage."""
    check = _Check(design, parts, listed, routes, pack_volts)
    check.static()
    for modules in combinations:
        check.combination(frozenset(modules))
    everywhere = {frozenset(m) for m in combinations}
    seen: dict[tuple[str, str], set] = {}
    order = []
    for problem in check.problems:
        key = (problem.rule, problem.message)
        if key not in seen:
            seen[key] = set()
            order.append(key)
        seen[key].add(problem.combination)
    out = []
    for key in order:
        where = seen[key]
        if None in where or where == everywhere:
            out.append(Problem(*key))
        else:
            out += [Problem(*key, modules) for modules in sorted(where, key=sorted)]
    return out


def listed_in(build) -> dict[str, set[str]]:
    """Where the build lists each part: base, V, P or C."""
    where = {build.esc.id: {"base"}, build.motor.id: {"base"}}
    for part in build.base:
        where.setdefault(part.id, set()).add("base")
    for module, parts in build.modules.items():
        for part in parts:
            where.setdefault(part.id, set()).add(module)
    return where


def validate_design(design: ConnectionList, catalog, build, cad_settings, combinations):
    """The rules on the real thing: the catalog's parts, the build's modules, the CAD's routes."""
    parts = {part.id: part for part in catalog.all_parts()}
    routes = {wire.name for wire in cad_settings.wires}
    pack_volts = build.pack.cell.max_voltage_v * build.pack.series
    return validate(design, parts, listed_in(build), routes, combinations, pack_volts)
