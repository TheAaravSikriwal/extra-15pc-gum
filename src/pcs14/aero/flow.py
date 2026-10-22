"""The wind tunnel's averaged flow, and how the drone sits in the tunnel.

FluidX3D's setup (in my fork) writes each case's air velocity averaged over the end of the run:
field.bin (float32, x fastest, three components a cell, m/s, in the tunnel's frame), solid.bin
(each coarse cell's share of solid, 0 to 255) and field.txt (the grid, its scale, where the drone
sits and how it's turned, and the mean force on it). The flow moving is pcs14.aero.motion's; this
gives it the drone's outline in the tunnel and the force.

The force is FluidX3D's own number, visual-grade: it runs high without a wall model, so the drag
numbers come from OpenFOAM.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def rotation(yaw_deg: float, pitch_deg: float) -> np.ndarray:
    """The drone's frame into the tunnel's, the way FluidX3D's setup turns the mesh: about its
    left (pitch, nose down) first, then about up (yaw)."""
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    return rz @ ry


@dataclass(frozen=True)
class Field:
    u: np.ndarray  # (nz, ny, nx, 3) m/s, in the tunnel's frame
    solid: np.ndarray  # (nz, ny, nx), each coarse cell's share of solid, 0 to 1
    cell_m: float  # a coarse cell's size
    origin: np.ndarray  # the drone's origin, in coarse cells (x, y, z)
    turn: np.ndarray  # 3 x 3, the drone's frame into the tunnel's
    speed: float  # m/s, the wind (0 in the hover)
    force: np.ndarray  # N, the mean force on the drone, in the tunnel's frame (visual-grade)

    def to_drone(self, cells: np.ndarray) -> np.ndarray:
        """Points in coarse cells to m in the drone's frame."""
        return (np.asarray(cells, dtype=float) - self.origin) * self.cell_m @ self.turn

    def to_cells(self, metres: np.ndarray) -> np.ndarray:
        """Points in m in the drone's frame to coarse cells."""
        return np.asarray(metres, dtype=float) @ self.turn.T / self.cell_m + self.origin


def _settings(path: Path) -> dict:
    found = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            found[key.strip()] = float(value)
    return found


def read_field(folder: Path) -> Field | None:
    """A case's averaged flow, or None for a case run before the fork wrote one."""
    folder = Path(folder)
    if not (folder / "field.txt").is_file():
        return None
    s = _settings(folder / "field.txt")
    nx, ny, nz, coarsen = (int(s[k]) for k in ("nx", "ny", "nz", "coarsen"))
    u = np.fromfile(folder / "field.bin", dtype="<f4").reshape(nz, ny, nx, 3)
    solid = np.fromfile(folder / "solid.bin", dtype=np.uint8).reshape(nz, ny, nx) / 255.0
    # a coarse cell's middle sits half a fine cell short of its first fine cell's, times coarsen
    origin = (np.array([s["origin_x"], s["origin_y"], s["origin_z"]]) - (coarsen - 1) / 2) / coarsen
    force = np.array([s.get("force_x_n", 0.0), s.get("force_y_n", 0.0), s.get("force_z_n", 0.0)])
    turn = rotation(s["yaw_deg"], s["pitch_deg"])
    return Field(u, solid, coarsen / s["cells_per_m"], origin, turn, s["speed"], force)
