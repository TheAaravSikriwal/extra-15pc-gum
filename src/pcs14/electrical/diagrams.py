"""Harness diagrams (WireViz), pin maps and the power tree, all from the connection list.

A harness diagram shows every wire in one harness: each board's connector with all its pins,
each wire with its gauge and length (from its CAD route) and a color for what it carries (red
for power, black for ground, yellow and green for CAN high and low, turquoise for DShot, blue
for other signals). WireViz can't set its text color, so the boxes are light on the project's
black.
"""

from dataclasses import dataclass
from pathlib import Path

from pcs14 import style
from pcs14.electrical import tools
from pcs14.electrical.model import ConnectionList
from pcs14.electrical.validate import GROUND, Wiring, listed_in

DSHOT = "TQ"  # WireViz prints a color's code on the wire, so a named one reads better than hex


@dataclass
class Sources:
    design: ConnectionList
    catalog: object
    build: object
    lengths: dict  # CAD route name -> m
    wiring: Wiring
    parts: dict

    @classmethod
    def make(cls, design, catalog, build, lengths):
        parts = {p.id: p for p in catalog.all_parts()}
        pack_max = build.pack.cell.max_voltage_v * build.pack.series
        wiring = Wiring(design, parts, listed_in(build), set(lengths), pack_max)
        return cls(design, catalog, build, lengths, wiring, parts)

    def length(self, run) -> float:
        return run.length if run.length is not None else self.lengths.get(run.route, 0.0)


def _color(src: Sources, run) -> str:
    pins = [src.wiring.pin(ref) for ref in run.ends]
    names = [ref.rsplit(".", 1)[1] for ref in run.ends]
    if any(p.role == GROUND for p in pins):
        return "BK"
    if any(p.role == "power" for p in pins):
        return "RD"
    if any("CAN_P" in n for n in names):
        return "YE"
    if any("CAN_N" in n for n in names):
        return "GN"
    if any(any("DShot" in f for f in p.functions) for p in pins):
        return DSHOT
    return "BU"


def _font() -> str:
    from matplotlib import font_manager

    wanted = style.load()["fonts"]["body"]
    names = {font.name for font in font_manager.fontManager.ttflist}
    return wanted if wanted in names else "Arial"


def harnesses(src: Sources) -> dict[str, dict]:
    """A WireViz harness for each harness in the connection list."""
    out = {}
    options = {
        "bgcolor": style.color("background"),
        "bgcolor_node": style.color("text"),
        "bgcolor_connector": style.color("text"),
        "bgcolor_cable": style.color("text"),
        "fontname": _font(),
    }
    for n, run in enumerate(src.design.wires, start=1):
        spec = out.setdefault(
            run.harness, {"options": options, "connectors": {}, "cables": {}, "connections": []}
        )
        ends = []
        for ref in run.ends:
            board, connector_name, pin = ref.split(".", 2)
            designator = f"{board}-{connector_name}"
            block = src.wiring.boards[board].block
            connector = block.connector(connector_name)
            labels = [p.name for p in connector.pins]
            if designator not in spec["connectors"]:
                part = src.design.boards[board].part if board in src.design.boards else "pack"
                spec["connectors"][designator] = {
                    "type": connector.family,
                    "subtype": part,
                    "pinlabels": labels,
                }
            ends.append({designator: [labels.index(pin) + 1]})
        cable = f"W{n}"
        spec["cables"][cable] = {
            "wirecount": 1,
            "gauge": f"{run.awg} AWG",
            "length": round(src.length(run), 3),
            "colors": [_color(src, run)],
        }
        spec["connections"].append([ends[0], {cable: [1]}, ends[1]])
    return out


def draw_harnesses(src: Sources, folder: Path) -> list[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, spec in harnesses(src).items():
        path = folder / f"{name.replace(' ', '-')}.svg"
        path.write_text(tools.draw_harness(spec), encoding="utf-8")
        written.append(path)
    return written


def pin_map(src: Sources, board: str) -> list[dict]:
    """Every pin on a board: what it is, what PX4 or the chip calls it, and where it goes."""
    nets = src.wiring.nets(frozenset({"V", "P", "C"}))
    groups = {}
    for ref in nets.parent:
        groups.setdefault(nets.find(ref), []).append(ref)
    harness_of = {}
    for run in src.design.wires:
        for ref in run.ends:
            harness_of.setdefault(ref, set()).add(run.harness)
    rows = []
    found = src.wiring.boards[board]
    for local, pin in found.block.pins():
        ref = f"{board}.{local}"
        others = sorted(r for r in groups.get(nets.find(ref), []) if not r.startswith(f"{board}."))
        if pin.role == GROUND and others:
            others = ["ground"]
        shown = others[:5] + ([f"and {len(others) - 5} more"] if len(others) > 5 else [])
        rows.append(
            {
                "pin": local,
                "role": pin.role if pin.role != "signal" else found.direction(ref) or "signal",
                "functions": ", ".join(pin.functions),
                "to": ", ".join(shown),
                "harness": ", ".join(sorted(harness_of.get(ref, ()))),
            }
        )
    return rows


def pin_map_markdown(src: Sources, board: str, used_only: bool = True) -> str:
    rows = [r for r in pin_map(src, board) if r["to"] or not used_only]
    lines = ["| Pin | What it is | Called | Goes to |", "|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['pin']} | {row['role']} | {row['functions']} | {row['to']} |")
    return "\n".join(lines)


def power_tree_markdown(src: Sources, typical=None, worst=None) -> str:
    """Where every amp comes from, as a nested list, with currents when solutions are given."""
    nets = src.wiring.nets(frozenset({"V", "P", "C"}))
    members = {}
    for ref in nets.parent:
        members.setdefault(nets.find(ref), []).append(ref)
    seen, lines = set(), []

    def amps(kind, name):
        def one(solution):
            if solution is None:
                return None
            return getattr(solution, kind).get(name)

        a, b = one(typical), one(worst)
        if a is None and b is None:
            return ""
        return f": {a or 0:.2f} A typical, {b or 0:.2f} A worst"

    def walk(root, depth):
        if root in seen:
            return
        seen.add(root)
        pad = "  " * depth
        for ref in sorted(members[root]):
            board_name, local = ref.split(".", 1)
            board = src.wiring.boards[board_name]
            part = (
                src.parts.get(src.design.boards[board_name].part) if board_name != "pack" else None
            )
            for draw in board.block.draws:
                if draw.pin != local:
                    continue
                if getattr(part, "type", "") == "esc" and typical is not None:
                    branches = sum(typical.elements.get(c.element, 0.0) for c in src.design.fuses)
                    motors = (typical.case.battery_amps or 0.0) - branches
                    lines.append(f"{pad}- {ref}: the ESC and its motors, {motors:.1f} A hovering")
                else:
                    lines.append(
                        f"{pad}- {ref}: {draw.typical_a:.2f} A typical, {draw.worst_a:.2f} A worst"
                    )
            for output in board.block.outputs:
                if output.fed_from == local and output.kind != "through":
                    name = f"{board_name}.{output.name}"
                    lines.append(
                        f"{pad}- {name}, a {output.kind} {output.volts:g} V supply rated "
                        f"{output.continuous_a:g} A{amps('supplies', name)}"
                    )
                    walk(nets.find(board.full(output.pins[0])), depth + 1)
            for element in board.block.elements:
                if board.full(element.between[0]) != ref or element.kind == "resistor":
                    continue
                name = f"{board_name}.{element.name}"
                rating = next(
                    (f"{c.rated_a:g} A " for c in src.design.fuses if c.element == name), ""
                )
                lines.append(f"{pad}- {name}, a {rating}{element.kind}{amps('elements', name)}")
                walk(nets.find(board.full(element.between[1])), depth + 1)

    lines.append("- pack (the battery, through its XT60)")
    walk(nets.find("pack.XT60.+"), 1)
    return "\n".join(lines)
