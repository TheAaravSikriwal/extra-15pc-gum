"""Mapping (#7), the orthomosaic: a picture of the ground built from a grid run's camera frames
and the poses they were taken from. Each spot on the ground gets the color the frames that saw
it agree on, weighted toward each frame's middle, where its lens is best.

This is what a GPS-tagged mapping run does once it knows its poses. It makes a picture, not a
3D model: OpenDroneMap's photogrammetry, which works out the ground's heights from how the
overlapping photos disagree, isn't installed here. Everything is projected onto flat ground,
so anything tall (the shed, the trees) leans away from the camera that saw it.

Frames: the world is x east, y north, z up. A camera looks along its own x, with its left along
its y and its up along its z, as Gazebo's cameras do; the picture's right is the camera's -y
and its down is the camera's -z.
"""

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Camera:
    width: int
    height: int
    hfov_rad: float

    @property
    def focal_px(self) -> float:
        return (self.width / 2) / math.tan(self.hfov_rad / 2)

    @property
    def center(self) -> tuple[float, float]:
        return (self.height - 1) / 2, (self.width - 1) / 2

    def rays(self, pose: "Pose") -> np.ndarray:
        """Each pixel's direction in the world, row by row: (height * width, 3)."""
        rows, cols = np.mgrid[0 : self.height, 0 : self.width]
        cy, cx = self.center
        cam = np.stack([np.full(rows.size, self.focal_px), -(cols.ravel() - cx),
                        -(rows.ravel() - cy)], axis=1)  # fmt: skip
        world = cam @ pose.rotation.T
        return world / np.linalg.norm(world, axis=1, keepdims=True)

    def project(self, pose: "Pose", points) -> tuple[np.ndarray, np.ndarray]:
        """(rows, cols) of world points in the picture; NaN for points behind the camera."""
        d = (np.asarray(points, dtype=float) - pose.position) @ pose.rotation
        ahead = d[:, 0] > 1e-6
        cy, cx = self.center
        with np.errstate(divide="ignore", invalid="ignore"):
            col = np.where(ahead, cx - self.focal_px * d[:, 1] / d[:, 0], np.nan)
            row = np.where(ahead, cy - self.focal_px * d[:, 2] / d[:, 0], np.nan)
        return row, col


NADIR = np.array([[0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]])  # looking down, north up


@dataclass(frozen=True)
class Pose:
    position: np.ndarray  # m: east, north, up
    rotation: np.ndarray = None  # the camera's frame into the world's, columns x y z
    down: bool = False  # straight down with north at the picture's top, when no rotation

    def __post_init__(self):
        if self.rotation is None:
            object.__setattr__(self, "rotation", NADIR if self.down else np.eye(3))

    @classmethod
    def on_drone(cls, position, quat_xyzw, offset=(0.0, 0.0, 0.0), pitch_rad: float = 0.0):
        """The camera's pose on a drone at `position` with attitude `quat_xyzw` (its body
        forward-left-up into the world), mounted at `offset` in the body and tipped `pitch_rad`
        down about the body's left axis."""
        body = _matrix(quat_xyzw)
        c, s = math.cos(pitch_rad), math.sin(pitch_rad)
        mount = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])  # about y, x tips down
        return cls(position=np.asarray(position, dtype=float) + body @ np.asarray(offset),
                   rotation=body @ mount)  # fmt: skip


def _matrix(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])  # fmt: skip


@dataclass(frozen=True)
class Mosaic:
    image: np.ndarray  # rows from the north edge, columns from the west edge
    east0: float
    north1: float  # the north edge
    m_per_px: float
    covered: float  # the share of the area some frame saw

    def color_at(self, east: float, north: float) -> np.ndarray:
        row = int((self.north1 - north) / self.m_per_px)
        col = int((east - self.east0) / self.m_per_px)
        return self.image[row, col]

    def nearest_color(self, east: float, north: float, color, within_m: float) -> np.ndarray:
        """The pixel nearest `color` within `within_m` of (east, north)."""
        row = int((self.north1 - north) / self.m_per_px)
        col = int((east - self.east0) / self.m_per_px)
        r = int(round(within_m / self.m_per_px))
        patch = self.image[max(row - r, 0) : row + r + 1, max(col - r, 0) : col + r + 1]
        flat = patch.reshape(-1, 3).astype(float)
        return flat[np.argmin(np.linalg.norm(flat - np.asarray(color, dtype=float), axis=1))]


def mosaic(frames, camera: Camera, east, north, m_per_px: float = 0.1) -> Mosaic:
    """Every (picture, pose) in `frames`, onto flat ground over `east` x `north` (m)."""
    cols = int(round((east[1] - east[0]) / m_per_px))
    rows = int(round((north[1] - north[0]) / m_per_px))
    ge = east[0] + (np.arange(cols) + 0.5) * m_per_px
    gn = north[1] - (np.arange(rows) + 0.5) * m_per_px
    grid_e, grid_n = np.meshgrid(ge, gn)
    points = np.stack([grid_e.ravel(), grid_n.ravel(), np.zeros(grid_e.size)], axis=1)
    total = np.zeros((points.shape[0], 3))
    weight = np.zeros(points.shape[0])
    cy, cx = camera.center
    reach = math.hypot(cx, cy)
    for picture, pose in frames:
        r, c = camera.project(pose, points)
        seen = np.isfinite(r) & (r >= 0) & (r <= camera.height - 1) & (c >= 0) & (
            c <= camera.width - 1)  # fmt: skip
        if not seen.any():
            continue
        ri, ci = np.rint(r[seen]).astype(int), np.rint(c[seen]).astype(int)
        # heavier toward the frame's middle
        w = 1.0 - np.hypot(r[seen] - cy, c[seen] - cx) / reach
        total[seen] += picture[ri, ci, :3].astype(float) * w[:, None]
        weight[seen] += w
    image = np.zeros_like(total)
    got = weight > 0
    image[got] = total[got] / weight[got][:, None]
    return Mosaic(image.reshape(rows, cols, 3).astype(np.uint8), east[0], north[1], m_per_px,
                  float(got.mean()))  # fmt: skip
