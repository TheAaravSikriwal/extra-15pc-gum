"""The electrical layer in Rerun.

- The drone from the CAD, with every wire route drawn along its path and colored by how hard
  its wires work (the share of their allowed heating they use, on the turbo colormap, magenta
  past the limit), stepping through each module combination and flight case on the "step"
  timeline. The power connectors the burst heats sit at the pack end of their route.
- The switch sims as scope traces on the "sim" timeline, in simulated time, one plot a case.
- Temperatures through the burst on the "burst" timeline, in seconds, with their limits.

Rerun shows one timeline at a time, so each of the three gets its own tab; the recording opens
on the wires and the "step" timeline.
"""

import math
from pathlib import Path

import numpy as np
import rerun as rr
import rerun.blueprint as rrb
from matplotlib import colormaps

from pcs14 import style
from pcs14.electrical.spice.switch import CASES as SWITCH_CASES
from pcs14.viz.cad_log import HIDDEN, _color, _mesh
from pcs14.viz.rerun_log import WHOLE_RUN, Recorder, _safe

# each scope trace: its color and what it is
TRACES = {
    "v(fc)": ("muted", "the FC's pin"),
    "v(esc)": ("accent", "at the ESC"),
    "v(no)": ("text", "the Teensy's side"),
    "v(ctl)": ("pop", "switch control"),
    "v(rx)": ("text", "the receiver's pin"),
    "v(fcrx)": ("accent", "at the FC"),
}
SCOPES = (*SWITCH_CASES, "Receiver, Teensy off")
MODULES = ("V", "P", "C")
CASES = ("hover", "cruise", "burst", "worst")
# turbo's bottom tenth is close to black, which vanishes on the black background
TURBO_FROM = 0.1
GLASS = 70  # the parts' alpha, so the wires inside show through
SHOWN = 0.05  # connectors working less than this aren't marked


def share_color(share: float) -> tuple[int, int, int]:
    """Turbo for 0 to 100% of a limit; magenta past it."""
    if share > 1.0:
        return style.rgb("pop")
    r, g, b, _ = colormaps["turbo"](TURBO_FROM + (1 - TURBO_FROM) * max(share, 0.0))
    return int(r * 255), int(g * 255), int(b * 255)


def thin(times, volts, step: float = 0.01):
    """A scope trace with its flat stretches dropped: a point stays where the voltage crosses
    into another `step`-volt band, along with the point before it, so every edge keeps its
    exact shape and a line that sits still costs two points."""
    times = np.asarray(times, dtype=np.float64)
    volts = np.asarray(volts, dtype=np.float64)
    band = np.round(volts / step)
    moved = np.flatnonzero(band[1:] != band[:-1]) + 1
    keep = np.unique(np.concatenate(([0, len(volts) - 1], moved, moved - 1)))
    return times[keep], volts[keep]


def _scope_path(case: str) -> str:
    return f"scope/{_name(case.replace(',', ''))}"


def electrical_blueprint(scopes=SCOPES) -> rrb.Blueprint:
    drone = rrb.Spatial3DView(
        origin="/drone",
        name="Wires by how hard they work",
        background=rrb.Background(color=[*style.rgb("background"), 255]),
        eye_controls=rrb.EyeControls3D(
            position=(0.45, -0.45, 0.32), look_target=(0.0, 0.0, 0.02), eye_up=(0, 0, 1)
        ),
    )
    legend = rrb.PlotLegend(corner=rrb.Corner2D.RightBottom)
    switch = rrb.Grid(
        *(
            rrb.TimeSeriesView(
                origin=f"/{_scope_path(case)}", name=case, axis_x=WHOLE_RUN, plot_legend=legend
            )
            for case in scopes
        ),
        name="The switch (sim timeline)",
    )
    heat = rrb.TimeSeriesView(
        origin="/heat", name="Through the burst (burst timeline)", axis_x=WHOLE_RUN
    )
    now = rrb.TextDocumentView(origin="/now", name="This step")
    summary = rrb.TextDocumentView(origin="/summary", name="Checks")
    wires = rrb.Horizontal(
        drone, rrb.Vertical(now, summary, row_shares=[1, 4]), column_shares=[3, 2], name="Wires"
    )
    return rrb.Blueprint(
        rrb.Tabs(wires, switch, heat),
        rrb.TimePanel(timeline="step", state="collapsed"),
        collapse_panels=True,
    )


def _name(text: str) -> str:
    return _safe(text.replace(" ", "_").replace(".", "_").replace("(", "_"))


class ElectricalRecorder(Recorder):
    def __init__(self, path: Path | None = None, live: bool = False):
        super().__init__(path, live, app="pcs14-electrical", layout=electrical_blueprint())
        self.rec.log("/drone", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
        self._drawn: set[str] = set()

    def log_drone(self, pieces) -> None:
        """The drone's parts, once, grouped by module so a combination can hide the rest. The
        CAD's wire tubes are left out: the wires get drawn by how hard they work."""
        for piece in pieces:
            if piece.kind == "wire":
                continue
            path = f"drone/parts/{piece.module}/{_name(piece.name)}"
            self.rec.log(path, _mesh(piece.solid, _color(piece), GLASS), static=True)

    def log_wires(
        self,
        step: int,
        label: str,
        routes: dict,
        shares: dict,
        modules=(),
        connectors: dict | None = None,
    ) -> None:
        """One combination in one case. `routes` maps each route in it to (points in m,
        thickness in m); `shares` maps a route to its hardest working wire's share of its limit;
        `connectors` maps a connector to (point, share)."""
        self.rec.set_time("step", sequence=step)
        for module in MODULES:
            scale = 1.0 if module in modules else HIDDEN
            self.rec.log(f"drone/parts/{module}", rr.Transform3D(scale=scale))
        for name in self._drawn - set(routes):
            self.rec.log(f"drone/wires/{_name(name)}", rr.Clear(recursive=True))
        for name, (points, thickness) in routes.items():
            share = shares.get(name, 0.0)
            self.rec.log(
                f"drone/wires/{_name(name)}",
                rr.LineStrips3D(
                    [np.asarray(points, dtype=np.float32)],
                    radii=[thickness / 2],
                    colors=[share_color(share)],
                    labels=[f"{name}: {share:.0%}"],
                    show_labels=False,
                ),
            )
        self._drawn = set(routes)
        if connectors:
            names = sorted(connectors)
            self.rec.log(
                "drone/connectors",
                rr.Points3D(
                    [connectors[n][0] for n in names],
                    radii=[0.006] * len(names),
                    colors=[share_color(connectors[n][1]) for n in names],
                    labels=[f"{n}: {connectors[n][1]:.0%}" for n in names],
                    show_labels=True,
                ),
            )
        self.rec.log("now", rr.TextDocument(label, media_type=rr.MediaType.MARKDOWN))

    def log_scope(self, case: str, times, waves: dict) -> None:
        for name, volts in waves.items():
            path = f"{_scope_path(case)}/{_name(name.replace(')', ''))}"
            color, meaning = TRACES.get(name, ("muted", name))
            self.rec.log(
                path,
                rr.SeriesLines(colors=[[*style.rgb(color), 255]], names=[meaning]),
                static=True,
            )
            t, v = thin(times, volts)
            self.rec.send_columns(
                path,
                indexes=[rr.TimeColumn("sim", duration=t)],
                columns=rr.Scalars.columns(scalars=v),
            )

    def log_heat(self, name: str, curve, limit_c: float) -> None:
        """A temperature through the burst, magenta if it passes its limit, and its limit as a
        thin line."""
        times = np.array([t for t, _ in curve], dtype=np.float64)
        temps = np.array([c for _, c in curve], dtype=np.float64)
        color = style.rgb("pop") if temps.max() > limit_c else style.rgb("accent")
        lines = (
            (f"heat/{_name(name)}", name, temps, color, 2.0),
            (f"heat/limit_{limit_c:g}", f"{limit_c:g} C limit", [limit_c] * len(times), None, 1.0),
        )
        for path, label, values, line, width in lines:
            line = line or style.rgb("muted")
            self.rec.log(
                path,
                rr.SeriesLines(colors=[[*line, 255]], names=[label], widths=[width]),
                static=True,
            )
            self.rec.send_columns(
                path,
                indexes=[rr.TimeColumn("burst", duration=times)],
                columns=rr.Scalars.columns(scalars=np.asarray(values, dtype=np.float64)),
            )

    def log_summary(self, text: str) -> None:
        self.rec.log(
            "summary", rr.TextDocument(text, media_type=rr.MediaType.MARKDOWN), static=True
        )


def route_shares(design, working: dict) -> dict:
    """{(setup, case): {route: share}}: each route at its hardest working wire."""
    inside: dict[str, list[str]] = {}
    for run in design.wires:
        if run.route is not None:
            inside.setdefault(run.route, []).append(run.label)
    return {
        key: {
            route: max(shares.get(label, 0.0) for label in labels)
            for route, labels in inside.items()
        }
        for key, shares in working.items()
    }


def connector_points(design, cad_wires, near) -> dict:
    """Where each connector pin sits: the end of its wires' route nearest `near` (the pack's
    center, for the main power connector). A pin's wires can be on its own board or on the
    board its connector mates with."""
    paths = {wire.name: wire.path for wire in cad_wires}
    mates = {}
    for mate in design.mates:
        mates[mate.a], mates[mate.b] = mate.b, mate.a
    points = {}
    for run in design.wires:
        if run.route not in paths:
            continue
        path = paths[run.route]
        tip = min((path[0], path[-1]), key=lambda p: math.dist(p, near))
        for end in run.ends:
            board, connector, pin = end.split(".")
            for side in (f"{board}.{connector}", mates.get(f"{board}.{connector}")):
                if side is not None:
                    points.setdefault(f"{side}.{pin}", tip)
    return points


def record(recorder, pieces, cad_wires, design, setups, working, connectors, curves, sims, summary):
    """Everything into one recording. `setups` maps each combination's name to its modules, in
    order; `working` and `connectors` come from wire_working and connector_working, `curves`
    from burst_curves, and `sims` from the switch runs (or None)."""
    recorder.log_drone(pieces)
    pack = next((p for p in pieces if p.kind == "pack"), None)
    near = (0.0, 0.0, 0.0)
    if pack is not None:
        c = pack.solid.bounding_box().center()
        near = (c.X, c.Y, c.Z)
    places = connector_points(design, cad_wires, near)
    shares = route_shares(design, working)
    step = 0
    for setup, modules in setups.items():
        routes = {
            w.name: (w.path, w.diameter)
            for w in cad_wires
            if w.module == "base" or w.module in modules
        }
        for case in CASES:
            if (setup, case) not in shares:
                continue
            hot = {
                ref: (places[ref], share)
                for ref, share in connectors.get((setup, case), {}).items()
                if ref in places and share >= SHOWN
            }
            label = _step_label(setup, case, shares[(setup, case)], hot)
            recorder.log_wires(step, label, routes, shares[(setup, case)], modules, hot)
            step += 1
    for name, curve, limit_c in curves:
        recorder.log_heat(name, curve, limit_c)
    for name, run in (sims or {}).items():
        waves = {k: v for k, v in run.waves.items() if k in TRACES}
        if waves:
            recorder.log_scope(name, run.waves["time"], waves)
    recorder.log_summary(summary)


def _step_label(setup, case, routes, connectors) -> str:
    """One line on what's working hardest in this step."""
    words = [f"**{setup}, {case}**"]
    if routes:
        route, share = max(routes.items(), key=lambda item: item[1])
        words.append(f"hardest working route: {route}, at {share:.0%} of its heating limit")
    if connectors:
        ref, (_, share) = max(connectors.items(), key=lambda item: item[1][1])
        words.append(f"{ref} at {share:.0%} of its limit")
    return "  \n".join(words)
