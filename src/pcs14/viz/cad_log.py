"""The CAD in Rerun, on one "step" timeline: the drone builds up part by part, then steps
through every module combination (modules coming and going, the pack sliding to its trim,
the center of gravity and the center of thrust marked, anything failing a check lit up in
magenta), then comes apart into an exploded view and goes back together.

Each part's mesh is sent once; the timeline only moves it, and a part that isn't there is
scaled down to nothing.
"""

from pathlib import Path

import numpy as np
import rerun as rr
import rerun.blueprint as rrb

from pcs14 import style
from pcs14.viz.rerun_log import Recorder, _safe

HIDDEN = 1e-6  # a scale that makes a part vanish
BOUGHT = (128, 126, 120)


def cad_blueprint() -> rrb.Blueprint:
    view = rrb.Spatial3DView(
        origin="/drone",
        name="The drone",
        background=rrb.Background(color=[*style.rgb("background"), 255]),
        eye_controls=rrb.EyeControls3D(
            position=(0.55, -0.55, 0.38), look_target=(0.0, 0.0, 0.02), eye_up=(0, 0, 1)
        ),
    )
    summary = rrb.TextDocumentView(origin="/summary", name="Checks")
    return rrb.Blueprint(rrb.Horizontal(view, summary, column_shares=[3, 1]), collapse_panels=True)


def _xyz(vector) -> np.ndarray:
    return np.array([vector.X, vector.Y, vector.Z])


def _color(piece) -> tuple[int, int, int]:
    if piece.kind in ("printed",):
        return style.rgb("accent")
    if piece.kind in ("motor", "prop"):
        return style.rgb("text")
    if piece.kind == "frame":
        return style.rgb("muted")
    if piece.kind == "wire":
        return style.rgb("muted")
    return BOUGHT


def _mesh(shape, color, alpha: int = 255) -> rr.Mesh3D:
    vertices, triangles = shape.tessellate(0.0003, 0.3)
    points = np.array([(v.X, v.Y, v.Z) for v in vertices], dtype=np.float32)
    return rr.Mesh3D(
        vertex_positions=points,
        triangle_indices=np.array(triangles, dtype=np.uint32),
        albedo_factor=[*color, alpha],
    )


class CadRecorder(Recorder):
    def __init__(self, path: Path | None = None, live: bool = False):
        super().__init__(path, live, app="pcs14-cad", layout=cad_blueprint())
        self.rec.log("/drone", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    def _path(self, name: str) -> str:
        return f"drone/parts/{_safe(name.replace(' ', '_'))}"

    def _place(self, name: str, scale: float = 1.0, shift=(0.0, 0.0, 0.0)) -> None:
        self.rec.log(self._path(name), rr.Transform3D(translation=shift, scale=scale))

    def log_pieces(self, pieces) -> None:
        """Every part's mesh, in place on the drone, hidden until the build-up shows it."""
        self.rec.set_time("step", sequence=0)
        for piece in pieces:
            self.rec.log(self._path(piece.name), _mesh(piece.solid, _color(piece)), static=True)
            self._place(piece.name, HIDDEN)

    def log_build_up(self, names) -> None:
        for k, name in enumerate(names, start=1):
            self.rec.set_time("step", sequence=k)
            self._place(name)

    def log_prop_disks(self, disks, step: int = 0) -> None:
        """The disks the props sweep, as rings, from `step` on."""
        self.rec.set_time("step", sequence=step)
        rings = []
        for disk in disks:
            box = disk.bounding_box()
            cx, cy, z = box.center().X, box.center().Y, box.max.Z
            r = box.size.X / 2
            angles = np.linspace(0, 2 * np.pi, 97)
            rings.append([(cx + r * np.cos(t), cy + r * np.sin(t), z) for t in angles])
        self.rec.log(
            "drone/prop_disks", rr.LineStrips3D(rings, colors=[style.rgb("accent")], radii=0.0005)
        )

    def log_cone(self, mouth, mouth_radius: float, half_angle_deg: float, height: float, step: int):
        """The parachute's clear cone, as rings and lines, from `step` on."""
        self.rec.set_time("step", sequence=step)
        top = mouth_radius + height * np.tan(np.radians(half_angle_deg))
        x, y, z = mouth
        angles = np.linspace(0, 2 * np.pi, 49)
        strips = [
            [(x + r * np.cos(t), y + r * np.sin(t), z + h) for t in angles]
            for r, h in ((mouth_radius, 0.0), ((mouth_radius + top) / 2, height / 2), (top, height))
        ]
        for t in angles[:-1:6]:
            strips.append(
                [
                    (x + mouth_radius * np.cos(t), y + mouth_radius * np.sin(t), z),
                    (x + top * np.cos(t), y + top * np.sin(t), z + height),
                ]
            )
        self.rec.log(
            "drone/chute_cone", rr.LineStrips3D(strips, colors=[style.rgb("muted")], radii=0.0004)
        )

    def clear(self, path: str, step: int) -> None:
        self.rec.set_time("step", sequence=step)
        self.rec.log(path, rr.Clear(recursive=True))

    def log_combination(
        self, step, label, shown, all_names, pack_shift, center, thrust, problems, passed
    ) -> None:
        """One module combination: its parts shown, the pack slid to its trim, the two centers
        marked, and anything failing a check in magenta."""
        self.rec.set_time("step", sequence=step)
        for name in all_names:
            if name == "pack":
                self._place(name, 1.0, (pack_shift, 0.0, 0.0))
            else:
                self._place(name, 1.0 if name in shown else HIDDEN)
        self.rec.log(
            "drone/centers",
            rr.Points3D(
                [center, thrust],
                radii=[0.005, 0.004],
                colors=[style.rgb("accent"), style.rgb("text")],
                labels=["center of gravity", "center of thrust"],
                show_labels=True,
            ),
        )
        self.rec.log("drone/problems", rr.Clear(recursive=True))
        for piece in problems:
            self.rec.log(
                f"drone/problems/{_safe(piece.name.replace(' ', '_'))}",
                _mesh(piece.solid, style.rgb("pop")),
            )
        verdict = "passes every check" if passed else f"{len(problems)} parts in trouble"
        self.rec.log("drone/label", rr.TextLog(f"{label}: {verdict}"))

    def log_explode(self, start: int, pieces, frames: int = 12, spread: float = 1.6) -> int:
        """Every part flies out from the middle and comes back. Returns the step after it."""
        centers = {p.name: _xyz(p.solid.bounding_box().center()) for p in pieces}
        middle = np.mean(list(centers.values()), axis=0)
        step = start
        for frame in list(range(frames + 1)) + list(range(frames - 1, -1, -1)):
            self.rec.set_time("step", sequence=step)
            amount = (spread - 1) * frame / frames
            for piece in pieces:
                c = centers[piece.name]
                self._place(piece.name, 1.0, tuple((c - middle) * amount))
            step += 1
        return step

    def close(self) -> None:
        self.rec.flush()
