"""The CAD's wire routes, sized from the connection list.

Each route in design/cad.yaml is a tube the CAD checks against the props and measures for
length. Its thickness comes from the wires the connection list runs through it: a bundle is
about 1.15 times the root of the sum of its wires' squared diameters (a rule of thumb for
round wires packed together, and never thinner than its thickest wire). Runs longer than a
short jumper need a route of their own; jumpers inside one stack of boards give a length.
"""

import math
import re
from pathlib import Path

from pcs14.electrical.model import ConnectionList

PACKING = 1.15
JUMPER_MM = 60.0  # longer than this, a wire needs a CAD route


def bundle_diameter(diameters_mm) -> float:
    diameters = list(diameters_mm)
    if len(diameters) == 1:
        return diameters[0]
    return max(max(diameters), PACKING * math.sqrt(sum(d * d for d in diameters)))


def route_diameters(design: ConnectionList, parts) -> dict[str, float]:
    """Each route's thickness in mm, from the wires in it."""
    inside: dict[str, list[float]] = {}
    for run in design.wires:
        if run.route is None:
            continue
        gauge = parts[run.wire].gauge(run.awg)
        inside.setdefault(run.route, []).append(gauge.outer_diameter_mm)
    return {route: bundle_diameter(sizes) for route, sizes in inside.items()}


def route_wires(design: ConnectionList) -> dict[str, tuple[str, ...]]:
    """{route: the labels of the wires run through it}, in the connection list's order."""
    inside: dict[str, list[str]] = {}
    for run in design.wires:
        if run.route is not None:
            inside.setdefault(run.route, []).append(run.label)
    return {route: tuple(labels) for route, labels in inside.items()}


def route_shares(design: ConnectionList, working: dict) -> dict:
    """{(setup, case): {route: share}}: each route at its hardest working wire, from
    thermal.wire_working."""
    inside = route_wires(design)
    return {
        key: {
            route: max(shares.get(label, 0.0) for label in labels)
            for route, labels in inside.items()
        }
        for key, shares in working.items()
    }


def update_cad_routes(cad_path: Path, diameters: dict[str, float]) -> list[str]:
    """Write the thicknesses into design/cad.yaml, leaving everything else as it is. Returns the
    routes that changed."""
    lines = Path(cad_path).read_text(encoding="utf-8").splitlines(keepends=True)
    changed = []
    current = None
    for i, line in enumerate(lines):
        name = re.match(r"^\s*- name: (.+?)\s*$", line)
        if name:
            current = name.group(1)
            continue
        size = re.match(r"^(\s*)diameter_mm: ([0-9.]+)", line)
        if size and current in diameters:
            new = f"{diameters[current]:.1f}"
            old = size.group(2)
            if float(old) != float(new) or "from the electrical connection list" not in line:
                lines[i] = (
                    f"{size.group(1)}diameter_mm: {new} # from the electrical connection list\n"
                )
                changed.append(current)
    Path(cad_path).write_text("".join(lines), encoding="utf-8")
    return changed
