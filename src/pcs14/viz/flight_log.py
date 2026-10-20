"""The flight sim in Rerun: the CAD drone flying its logged path on a "flight_time" timeline,
with its trail, and plots of its height, its speed and its motors' speeds next to it."""

from pathlib import Path

import numpy as np
import rerun as rr
import rerun.blueprint as rrb

from pcs14 import style
from pcs14.viz.cad_log import _color, _mesh
from pcs14.viz.rerun_log import WHOLE_RUN, Recorder, _safe

MOTOR_COLORS = ("accent", "text", "muted", "pop")


def flight_blueprint() -> rrb.Blueprint:
    world = rrb.Spatial3DView(
        origin="/world",
        name="The flight",
        background=rrb.Background(color=[*style.rgb("background"), 255]),
    )
    plots = rrb.Vertical(
        rrb.TimeSeriesView(origin="/height", name="Height (m)", axis_x=WHOLE_RUN),
        rrb.TimeSeriesView(origin="/speed", name="Speed (m/s)", axis_x=WHOLE_RUN),
        rrb.TimeSeriesView(
            origin="/motors", name="Motor speeds (share of their top)", axis_x=WHOLE_RUN
        ),
    )
    summary = rrb.TextDocumentView(origin="/summary", name="Checks")
    return rrb.Blueprint(
        rrb.Horizontal(
            world, rrb.Vertical(plots, summary, row_shares=[4, 1]), column_shares=[3, 2]
        ),
        rrb.TimePanel(timeline="flight_time", state="collapsed"),
        collapse_panels=True,
    )


class FlightRecorder(Recorder):
    def __init__(self, path: Path | None = None, live: bool = False):
        super().__init__(path, live, app="pcs14-flight-sim", layout=flight_blueprint())
        self.rec.log("/world", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    def log_drone(self, pieces) -> None:
        """The CAD's parts, once, riding on the drone's pose."""
        for piece in pieces:
            if piece.kind == "wire":
                continue
            path = f"world/drone/{_safe(piece.name.replace(' ', '_'))}"
            self.rec.log(path, _mesh(piece.solid, _color(piece)), static=True)

    def log_meshes(self, meshes) -> None:
        """Ready-made parts from drone_meshes, so a batch of replays tessellates each
        combination once."""
        for path, mesh in meshes:
            self.rec.log(path, mesh, static=True)

    def log_flight(self, name: str, log, max_rot_velocity: float) -> None:
        tag = _safe(name.replace(" ", "_").replace(",", ""))
        trail = np.asarray(log.position, dtype=np.float32)
        self.rec.log(
            f"world/trails/{tag}",
            rr.LineStrips3D([trail], colors=[style.rgb("accent")], radii=0.01),
            static=True,
        )
        for k, t in enumerate(log.t):
            self.rec.set_time("flight_time", duration=float(t))
            quaternion = None if log.attitude is None else rr.Quaternion(xyzw=log.attitude[k])
            self.rec.log(
                "world/drone",
                rr.Transform3D(translation=log.position[k], quaternion=quaternion),
            )
        times = rr.TimeColumn("flight_time", duration=np.asarray(log.t, dtype=np.float64))
        speed = np.linalg.norm(np.asarray(log.velocity)[:, :2], axis=1)
        # each series with its color, set where it's made (a run named "dead motor" once
        # fooled a lookup by name)
        series = [
            (f"height/{tag}", log.position[:, 2], style.rgb("accent")),
            (f"speed/{tag}", speed, style.rgb("accent")),
        ]
        for n in range(np.asarray(log.rotor_speed).shape[1]):
            series.append((f"motors/{tag}/motor_{n}", log.rotor_speed[:, n] / max_rot_velocity,
                           style.rgb(MOTOR_COLORS[n])))  # fmt: skip
        for path, values, color in series:
            self.rec.log(path, rr.SeriesLines(colors=[[*color, 255]]), static=True)
            self.rec.send_columns(
                path,
                indexes=[times],
                columns=rr.Scalars.columns(scalars=np.asarray(values, dtype=np.float64)),
            )
        for t, event in log.events:
            self.rec.set_time("flight_time", duration=float(t))
            self.rec.log(f"events/{tag}", rr.TextLog(event))

    def log_summary(self, text: str) -> None:
        self.rec.log(
            "summary", rr.TextDocument(text, media_type=rr.MediaType.MARKDOWN), static=True
        )


REPLAY_TOLERANCE = 0.001  # m: a flight replay doesn't need the CAD stills' 0.3 mm


def drone_meshes(pieces) -> list:
    """(entity path, mesh) for each of the CAD's parts but the wires, tessellated coarsely."""
    out = []
    for piece in pieces:
        if piece.kind == "wire":
            continue
        vertices, triangles = piece.solid.tessellate(REPLAY_TOLERANCE, 0.5)
        mesh = rr.Mesh3D(
            vertex_positions=np.array([(v.X, v.Y, v.Z) for v in vertices], dtype=np.float32),
            triangle_indices=np.array(triangles, dtype=np.uint32),
            albedo_factor=[*_color(piece), 255],
        )
        out.append((f"world/drone/{_safe(piece.name.replace(' ', '_'))}", mesh))
    return out


def record_run(path: Path, meshes, name: str, log, max_rot_velocity: float, summary: str) -> Path:
    """One flown run's recording: the drone flying its logged path, the plots and the checks."""
    recorder = FlightRecorder(path)
    recorder.log_meshes(meshes)
    recorder.log_flight(name, log, max_rot_velocity)
    recorder.log_summary(summary)
    recorder.close()
    return Path(path)
