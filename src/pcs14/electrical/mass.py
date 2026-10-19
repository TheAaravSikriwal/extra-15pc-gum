"""The wiring's real weight, from the connection list, and closing the loop with the catalog.

Each wire weighs its length (its CAD route, or its own length for a short jumper) times its
gauge's grams per meter. On top of that:

- plugs: the wire's half of every plug it lands in. A per-connector family (an XT60, an XT30)
  counts one half once per connector; a JST family's catalog weight is one position with both
  halves, so each position a wire lands in counts half of it. The module plugs and sockets are
  parts of their own, already weighed with their plugs, and the pack's half of its XT60 is in
  the pack.
- heat shrink: a short sleeve over every soldered end.
- sleeving: braided sleeving over the battery leads, once along their route.

A wire belongs to its route's module, or for a jumper, to the module at either end (Base if
neither). Base's wiring goes into the catalog's base-wiring entry; each module gets an entry of
its own (v-wiring, p-wiring, c-wiring), which joins the build in that module.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from pcs14.cad.settings import WIRING_PARTS
from pcs14.electrical.model import PACK

SHRINK_G = 0.03  # a 10 mm sleeve of 3 mm heat shrink over a soldered joint, an estimate
SLEEVE_G_PER_M = 3.0  # braided PET sleeving about 6 mm across, an estimate
PER_POSITION = {"jst-gh", "jst-sh", "t-gh"}  # families weighed per contact position
SELF_WEIGHED = {"module-socket", "module-plug"}  # parts that already hold their plugs' weight
SOLDERED = "pads"
FOLDER = "components"


@dataclass(frozen=True)
class WiringMass:
    module: str
    meters: float
    wires: float  # kg
    plugs: float  # kg
    shrink: float  # kg
    sleeving: float  # kg
    soldered: int  # ends soldered to pads

    @property
    def total(self) -> float:
        return self.wires + self.plugs + self.shrink + self.sleeving


def _module_of(run, wiring, routes) -> str:
    if run.route is not None:
        return routes[run.route][0]
    modules = {wiring.boards[ref.split(".")[0]].module for ref in run.ends} - {"base"}
    return min(modules) if modules else "base"


def wiring_masses(design, parts, wiring, routes: dict, lead_part: str = "base-wiring") -> dict:
    """{module: WiringMass}. `routes` maps each CAD route to (its module, its length in m);
    `lead_part` is the battery lead's part, whose route gets the sleeving."""
    meters = {m: 0.0 for m in WIRING_PARTS}
    wires = {m: 0.0 for m in WIRING_PARTS}
    soldered = {m: 0 for m in WIRING_PARTS}
    plugs = {m: 0.0 for m in WIRING_PARTS}
    seen = set()
    sleeved = set()
    for run in design.wires:
        module = _module_of(run, wiring, routes)
        length = run.length if run.route is None else routes[run.route][1]
        meters[module] += length
        wires[module] += length * parts[run.wire].gauge(run.awg).mass_g_per_m / 1000
        for ref in run.ends:
            board_name, connector_name, pin = ref.split(".")
            if board_name == PACK:
                continue
            board = wiring.boards[board_name]
            part_id = design.boards[board_name].part
            if part_id == lead_part and run.route is not None:
                sleeved.add((module, run.route))
            family = board.block.connector(connector_name).family
            if family == SOLDERED:
                soldered[module] += 1
                continue
            if part_id in SELF_WEIGHED:
                continue
            weighs = getattr(parts.get(family), "mass", None)
            if not weighs:
                continue
            key = (board_name, connector_name, pin if family in PER_POSITION else None)
            if key in seen:
                continue
            seen.add(key)
            plugs[module] += weighs / 2 if family in PER_POSITION else weighs
    sleeving = {m: 0.0 for m in WIRING_PARTS}
    for module, route in sleeved:
        sleeving[module] += routes[route][1] * SLEEVE_G_PER_M / 1000
    return {
        m: WiringMass(
            m,
            meters[m],
            wires[m],
            plugs[m],
            soldered[m] * SHRINK_G / 1000,
            sleeving[m],
            soldered[m],
        )
        for m in WIRING_PARTS
    }


def masses_for(design, catalog, build, cad_settings) -> dict:
    """wiring_masses on the real drone."""
    from pcs14.cad.assembly import wire_length
    from pcs14.electrical.checks import design_context

    ctx = design_context(design, catalog, build, cad_settings)
    routes = {w.name: (w.module, wire_length(w)) for w in cad_settings.wires}
    return wiring_masses(design, ctx.parts, ctx.wiring, routes)


def _note(m: WiringMass) -> str:
    sleeved = ""
    if m.sleeving:
        grams = m.sleeving * 1000
        sleeved = f", and {grams:.1f} g of sleeving on the battery leads at {SLEEVE_G_PER_M:g} g/m"
    return (
        f"From the connection list (pcs14 electrical --update-catalog): {m.meters:.2f} m of wire, "
        f"{m.wires * 1000:.1f} g at each gauge's grams per meter; {m.plugs * 1000:.1f} g of "
        f"plugs, the wire's half of each; {m.shrink * 1000:.1f} g of heat shrink on "
        f"{m.soldered} soldered ends at {SHRINK_G:g} g each{sleeved}. "
        + (
            "The grams per meter, the heat shrink and the sleeving are estimates"
            if m.sleeving
            else "The grams per meter and the heat shrink are estimates"
        )
    )


def _source(m: WiringMass) -> str:
    today = date.today().isoformat()
    return f'source: {{kind: estimate, checked: {today}, note: "{_note(m)}"}}'


def _replace_top_level(text: str, key: str, line: str) -> str:
    lines = text.splitlines()
    for i, existing in enumerate(lines):
        if existing.startswith(f"{key}:"):
            lines[i] = line
            return "\n".join(lines) + "\n"
    raise ValueError(f"no top-level {key} to replace")


def _new_part(part_id: str, module: str, m: WiringMass) -> str:
    cad = {
        "shape": "routed",
        "source": {
            "kind": "estimate",
            "checked": date.today().isoformat(),
            "note": f"Module {module}'s wire routes in design/cad.yaml",
        },
        "existing": {
            "found": "none",
            "checked": date.today().isoformat(),
            "note": "Wires, so there's nothing to look for",
        },
    }
    return "\n".join(
        [
            f"# Module {module}'s wiring, added by pcs14 electrical --update-catalog.",
            "type: component",
            f"id: {part_id}",
            "maker: Various",
            f"model: Module {module}'s wiring",
            f"checked: {date.today().isoformat()}",
            _source(m),
            f"mass_g: {round(m.total * 1000, 1)}",
            yaml.safe_dump({"cad": cad}, sort_keys=False, width=100).rstrip(),
            "",
        ]
    )


def _add_to_build(lines: list[str], part_id: str, module: str) -> list[str]:
    data = yaml.safe_load("\n".join(lines))
    if part_id in data["modules"].get(module, []):
        return lines
    start = lines.index(f"  {module}:")
    end = next(
        (i for i in range(start + 1, len(lines)) if not lines[i].startswith("    -")), len(lines)
    )
    return [*lines[:end], f"    - {part_id} # its wires, from the connection list", *lines[end:]]


def _pack_lines(lines: list[str], ohms: float) -> list[str]:
    note = (
        "  note: \"overhead_g is an estimate: nickel strip, balance and power leads, the pack's "
        "XT60 half and wrap for a 6S2P 18650 pack. wiring_mohm is the drone's side, the leads "
        "and the XT60 from the pack's terminals to the ESC, worked out from the connection list "
        "(pcs14 electrical --update-catalog); the pack's own strip and leads aren't in it\""
    )
    out = []
    for line in lines:
        if line.startswith("  wiring_mohm:"):
            out.append(f"  wiring_mohm: {round(ohms * 1000, 1)}")
        elif line.startswith("  note:") and out and any(o.startswith("pack:") for o in out):
            out.append(note)
        else:
            out.append(line)
    return out


def update_catalog(masses: dict, catalog_root: Path, build_path: Path, main_path_ohms: float):
    """Write the wiring's weights into its catalog entries and the main path's resistance into
    the build. Returns the files it changed."""
    catalog_root, build_path = Path(catalog_root), Path(build_path)
    changed = []
    lines = build_path.read_text(encoding="utf-8").splitlines()
    for module, part_id in WIRING_PARTS.items():
        m = masses[module]
        path = catalog_root / FOLDER / f"{part_id}.yaml"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            new = _replace_top_level(text, "source", _source(m))
            new = _replace_top_level(new, "mass_g", f"mass_g: {round(m.total * 1000, 1)}")
            new = _replace_top_level(new, "checked", f"checked: {date.today().isoformat()}")
        else:
            text, new = None, _new_part(part_id, module, m)
        if new != text:
            path.write_bytes(new.encode("utf-8"))
            changed.append(path)
        if module != "base":
            lines = _add_to_build(lines, part_id, module)
    lines = _pack_lines(lines, main_path_ohms)
    new_build = "\n".join(lines) + "\n"
    if new_build != build_path.read_text(encoding="utf-8"):
        build_path.write_bytes(new_build.encode("utf-8"))
        changed.append(build_path)
    return changed
