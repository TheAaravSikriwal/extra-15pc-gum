"""Stills of the drone in the project's look: front, side, top, three-quarter and exploded,
each on the same post-sized canvas as the sizing report's charts.

Matplotlib draws them (an orthographic 3D view, each triangle shaded by how much it faces a
light from above and in front), so they render anywhere with no GPU. Blender still does the
hero shots.
"""

from pathlib import Path

import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from pcs14 import style
from pcs14.report import charts

LIGHT = np.array([0.4, -0.5, 0.75]) / np.linalg.norm([0.4, -0.5, 0.75])
VIEWS = {  # name: (elevation, azimuth) in degrees; the nose points along +x
    "front": (8, 0),
    "side": (8, -90),
    "top": (90, -90),
    "three-quarter": (24, -52),
    "exploded": (24, -52),
}
BOUGHT = (128, 126, 120)


def _color(piece) -> np.ndarray:
    if piece.kind == "printed":
        rgb = style.rgb("accent")
    elif piece.kind in ("motor", "prop"):
        rgb = style.rgb("text")
    elif piece.kind in ("frame", "wire"):
        rgb = style.rgb("muted")
    else:
        rgb = BOUGHT
    return np.array(rgb) / 255


def _triangles(pieces, offsets=None):
    polygons, colors = [], []
    for piece in pieces:
        vertices, triangles = piece.solid.tessellate(0.0008, 0.4)
        points = np.array([(v.X, v.Y, v.Z) for v in vertices])
        if offsets is not None:
            points = points + offsets[piece.name]
        base = _color(piece)
        for a, b, c in triangles:
            tri = points[[a, b, c]]
            normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            length = np.linalg.norm(normal)
            shade = (
                0.35 + 0.65 * max(0.0, float(np.dot(normal / length, LIGHT))) if length else 0.35
            )
            polygons.append(tri)
            colors.append(np.clip(base * shade, 0, 1))
    return polygons, colors


def _exploded(pieces, spread: float = 1.6) -> dict:
    centers = {}
    for piece in pieces:
        c = piece.solid.bounding_box().center()
        centers[piece.name] = np.array([c.X, c.Y, c.Z])
    middle = np.mean(list(centers.values()), axis=0)
    return {name: (c - middle) * (spread - 1) for name, c in centers.items()}


def render_stills(pieces, folder: Path, title: str = "The drone, in CAD") -> list[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (elevation, azimuth) in VIEWS.items():
        offsets = _exploded(pieces) if name == "exploded" else None
        polygons, colors = _triangles(pieces, offsets)
        canvas = charts.Canvas(title, f"{name.capitalize()} view", made_up=False)
        flat = canvas.axes[0]
        rect = flat.get_position().bounds
        canvas.fig.delaxes(flat)
        ax = canvas.fig.add_axes(rect, projection="3d", facecolor=charts._c("background"))
        ax.add_collection3d(Poly3DCollection(polygons, facecolors=colors, edgecolors="none"))
        points = np.concatenate(polygons)
        low, high = points.min(axis=0), points.max(axis=0)
        middle, half = (low + high) / 2, (high - low).max() / 2
        for setter, m in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), middle, strict=True):
            setter(m - half, m + half)
        ax.set_box_aspect((1, 1, 1), zoom=1.45)  # matplotlib pads 3D views; this fills the frame
        ax.set_proj_type("ortho")
        ax.view_init(elev=elevation, azim=azimuth)
        ax.set_axis_off()
        path = folder / f"{name}.png"
        canvas.save(path)
        paths.append(path)
    return paths
