"""Safe spots, and the nearest-safe-spot landing: open ground that's level and clear of anything
the drone could hit, on a height map, and the nearest of it to where the drone was asked to
land.

The first height map is the world's own, which is exact in the sim. The second comes from a
mapping run's orthomosaic: anything that isn't the ground's color is an obstacle, which also
catches shadows and the way tall things lean in a flat projection, so it errs toward fewer safe
spots, never more. OpenDroneMap's surface model, with real heights, would sit between the two.
"""

from dataclasses import dataclass

import numpy as np

STEP_M = 0.15  # taller than this is an obstacle, not ground


@dataclass(frozen=True)
class Grid:
    values: np.ndarray  # rows from the north edge, columns from the west edge
    east0: float
    north1: float
    m_per_px: float

    def index(self, east: float, north: float) -> tuple[int, int]:
        return (int((self.north1 - north) / self.m_per_px),
                int((east - self.east0) / self.m_per_px))  # fmt: skip

    def at(self, east: float, north: float):
        row, col = self.index(east, north)
        return self.values[row, col]

    def place(self, row: int, col: int) -> tuple[float, float]:
        return (self.east0 + (col + 0.5) * self.m_per_px,
                self.north1 - (row + 0.5) * self.m_per_px)  # fmt: skip


def height_map(boxes, area, m_per_px: float = 0.25) -> Grid:
    """Heights over `area` ((east0, east1), (north0, north1)) from boxes: ((x, y, z) of each
    center, (size x, y, z)), the world's frame (x east, y north)."""
    (e0, e1), (n0, n1) = area
    rows, cols = int(round((n1 - n0) / m_per_px)), int(round((e1 - e0) / m_per_px))
    grid = Grid(np.zeros((rows, cols)), e0, n1, m_per_px)
    east = e0 + (np.arange(cols) + 0.5) * m_per_px
    north = n1 - (np.arange(rows) + 0.5) * m_per_px
    for (x, y, z), (sx, sy, sz) in boxes:
        inside_e = np.abs(east - x) <= sx / 2
        inside_n = np.abs(north - y) <= sy / 2
        top = z + sz / 2
        block = grid.values[np.ix_(inside_n, inside_e)]
        grid.values[np.ix_(inside_n, inside_e)] = np.maximum(block, top)
    return grid


def _grow(mask: np.ndarray, radius_px: int) -> np.ndarray:
    from scipy.ndimage import binary_dilation

    r = max(radius_px, 0)
    y, x = np.mgrid[-r : r + 1, -r : r + 1]
    return binary_dilation(mask, structure=(x * x + y * y) <= r * r)


def safe(heights: Grid, footprint_m: float = 0.6, clearance_m: float = 3.0,
         step_m: float = STEP_M) -> Grid:  # fmt: skip
    """Where the drone (its footprint's radius) can land with `clearance_m` from anything
    taller than `step_m`."""
    blocked = heights.values > step_m
    reach = int(np.ceil((footprint_m + clearance_m) / heights.m_per_px))
    return Grid(~_grow(blocked, reach), heights.east0, heights.north1, heights.m_per_px)


def nearest(safe_grid: Grid, east: float, north: float) -> tuple[float, float]:
    """The safe spot nearest (east, north)."""
    rows, cols = np.nonzero(safe_grid.values)
    if rows.size == 0:
        raise ValueError("nowhere on this map is safe")
    row, col = safe_grid.index(east, north)
    k = int(np.argmin((rows - row) ** 2 + (cols - col) ** 2))
    return safe_grid.place(int(rows[k]), int(cols[k]))


def obstacles_from_picture(picture, ground, tolerance: float = 30.0) -> np.ndarray:
    """Every pixel of an orthomosaic that isn't the ground's color, give or take."""
    diff = np.linalg.norm(picture.astype(float) - np.asarray(ground, dtype=float), axis=2)
    return diff > tolerance
