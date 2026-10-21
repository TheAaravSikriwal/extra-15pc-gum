"""Every wire in 3D, for the drone view: each wire's two pins in the drone's frame (the CAD's,
in mm, z up), the route between them, the pieces its ends ride with in the pulled-apart view,
its gauge, type and length, and where each connector's pins came from.

A pin's spot is its part's placement in design/cad.yaml (turned about x, then y, then z, then
moved) applied to the pin's place on the part (the catalog's cad connectors). The motors are
placed by the frame, at its corners; the wiring itself is routed in the drone's own frame. Like
the catalog's page, this reads the design rather than a report: it's the design's geometry.
"""

import math
from pathlib import Path

from pcs14.cad.settings import load_settings, parse_spots
from pcs14.catalog import load_catalog
from pcs14.design import load_build
from pcs14.electrical import pins
from pcs14.electrical.model import load_connection_list
from pcs14.site import schema


def placed(point, at, turn_deg) -> tuple[float, float, float]:
    """A point in a part's own frame on the drone: turned about x, then y, then z, then moved."""
    x, y, z = point
    for axis, degrees in zip("xyz", turn_deg, strict=True):
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        if axis == "x":
            y, z = c * y - s * z, s * y + c * z
        elif axis == "y":
            x, z = c * x + s * z, -s * x + c * z
        else:
            x, y = c * x - s * y, s * x + c * y
    return (x + at[0], y + at[1], z + at[2])


def _height(cad) -> float:
    """How high a part's top is in its own frame: where a pin on top sits."""
    for name in ("thickness_mm", "height_mm", "length_mm"):
        if hasattr(cad, name):
            return getattr(cad, name)
    return 0.0


def _motor_spots(build) -> dict[str, tuple[float, float, float]]:
    """Each motor's base, by its piece's name, the way pcs14.cad.frame places them."""
    cad = build.frame.cad
    corner = build.frame.wheelbase * 1000 / 2 / math.sqrt(2)
    z = cad.plate_thickness_mm + cad.arm_thickness_mm
    return {f"motor {'front' if sx > 0 else 'back'} {'left' if sy > 0 else 'right'}":
            (sx * corner, sy * corner, z) for sx in (1, -1) for sy in (1, -1)}  # fmt: skip


class _Spots:
    """Where each board sits: its piece's name, and its placement (at, turn)."""

    def __init__(self, settings, build, connections):
        self.spots = parse_spots(settings.place)
        self.motors = _motor_spots(build)
        self.connections = connections

    def of(self, board: str, part_id: str, instance: int):
        b = self.connections.boards[board]
        if b.piece in self.motors:
            return b.piece, self.motors[b.piece], (0, 0, 0)
        mine = [s for s in self.spots if s.part_id == part_id]
        matching = [s for s in mine if s.module == b.module] or [
            s for s in mine if s.module is None
        ]
        if not matching:
            return None  # the wiring: routed in the drone's own frame
        spot = matching[min(instance, len(matching) - 1)]
        return spot.name, spot.placement.at_mm, spot.placement.turn_deg


def wires3d(design: Path) -> schema.Wires3d:
    design = Path(design)
    catalog = load_catalog(design / "catalog")
    build = load_build(design / "build.yaml", catalog)
    settings = load_settings(design / "cad.yaml")
    connections = load_connection_list(design / "electrical.yaml")
    parts = {p.id: p for p in catalog.all_parts()}
    routes = {w.name: w for w in settings.wires}
    spots = _Spots(settings, build, connections)
    sources: dict[str, schema.PinSource] = {}

    def end(ref: str, route_piece: str | None) -> schema.WireEnd3d:
        where = pins.place(catalog, connections, ref)
        if where is None:
            raise ValueError(f"{ref} has no place on its part (the catalog's cad connectors)")
        part = parts[where.part_id]
        c = where.connector
        key = f"{where.board}.{c.name}"
        if key not in sources:
            sources[key] = schema.PinSource(
                connector=key, part_id=part.id, estimate=c.source.kind == "estimate",
                url=str(c.source.url) if c.source.url else None, note=c.source.note,
            )  # fmt: skip
        local = (where.x_mm, where.y_mm, c.z(_height(part.cad)))
        spot = spots.of(where.board, part.id, c.instance)
        if spot is None:
            at, piece = local, route_piece or part.id
        else:
            piece, origin, turn = spot
            at = placed(local, origin, turn)
        return schema.WireEnd3d(pin=ref, at_mm=[round(v, 2) for v in at], piece=piece)

    def role(ref: str) -> str:
        board, connector, pin = ref.split(".", 2)
        part = parts[connections.boards[board].part]
        found = next(c for c in part.electrical.connectors if c.name == connector)
        return next(p.role for p in found.pins if p.name == pin)

    out = []
    for run in connections.wires:
        route = routes.get(run.route) if run.route else None
        route_piece = f"wire {run.route}" if route else None
        a, b = (end(ref, route_piece) for ref in run.ends)
        path = [list(p) for p in route.path_mm] if route else []
        if path and (math.dist(a.at_mm, path[-1]) + math.dist(b.at_mm, path[0])
                     < math.dist(a.at_mm, path[0]) + math.dist(b.at_mm, path[-1])):  # fmt: skip
            path.reverse()
        length = sum(map(math.dist, path, path[1:])) if route else run.length_mm
        out.append(schema.Wire3d(
            label=run.label, harness=run.harness, ends=[a, b], route=run.route,
            route_piece=route_piece, path_mm=path, awg=run.awg, wire=parts[run.wire].model,
            role=role(run.ends[0]), length_mm=round(length, 1),
        ))  # fmt: skip
    return schema.Wires3d(schema_version=schema.SCHEMA_VERSION, wires=out,
                          connectors=list(sources.values()))  # fmt: skip
