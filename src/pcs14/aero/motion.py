"""The wind tunnel's flow moving, for the project site to play around the 3D drone in Fly it.

FluidX3D's setup (in my fork) writes 64 snapshots of each case's flow over the end of its run
(snaps/): the air's velocity in a box around the drone on 12 mm cells (int16, x fastest, three
components a cell, in units of u_max/32767 m/s, in the tunnel's frame), and the speed on the plane
through the drone at full resolution (uint16, in units of u_max/65535). This turns them into a loop
the site can play over and over without a seam, and carries particles through it.

- The loop runs the snapshots from first to last, and over its first BLEND_SHARE it eases from the
  flow at the end of that stretch into the flow at its start, so the end meets the start.
- The particles are released all through the loop, upstream of the drone and wide of it (more of
  them where they'll meet it), and some in its wake. Each is carried through the moving flow
  (midpoint steps, two a frame) until it leaves the box or has lived a whole loop. The flow loops,
  so each particle's path does too, and every loop plays the same.
- The plane is the speed on the slice through the drone at each frame of the loop, cropped and
  thinned to bytes.

All of it is a picture of the flow, not a measurement: the drag numbers come from OpenFOAM.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pcs14.aero.flow import rotation

LOOP_FRAMES = 64  # the frames one loop plays
BLEND_SHARE = 0.2  # how much of the snapshots' stretch the loop's seam takes to ease across
SUBSTEPS = 2  # midpoint steps a frame
PARTICLES = 2400
WAKE_SHARE = 0.3  # released in the wake, the rest upstream (or, in the hover, above and around)
NEAR_SHARE = 0.8  # of those upstream, the share released in front of the drone itself
NEAR_MARGIN_M = 0.08  # how far past the drone's outline "in front of it" reaches
AHEAD_M = 0.45  # how far ahead of its nose the upstream ones start, inside the box
STOPPED_M_S = 0.05  # slower than this at its release, a particle is inside the drone: moved
PLANE_WIDTH = 320  # px across the slice


def _settings(path: Path) -> dict:
    found = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            found[key.strip()] = float(value)
    return found


@dataclass(frozen=True)
class Motion:
    u: np.ndarray  # (frames, nz, ny, nx, 3) m/s, the tunnel's frame
    times: np.ndarray  # (frames,) s into the run
    planes: np.ndarray  # (frames, nz, ny) m/s on the plane through the drone, full resolution
    cell_m: float  # a snapshot cell
    low: np.ndarray  # m from the drone along the tunnel's axes: the first snapshot cell's middle
    fine_m: float  # a full-resolution cell, the plane's
    plane_low: np.ndarray  # m from the drone: the plane's x, and its first cell's y and z
    turn: np.ndarray  # 3 x 3, the drone's frame into the tunnel's
    speed: float  # m/s, the wind (0 in the hover)

    def index(self, points: np.ndarray) -> np.ndarray:
        """Points (m from the drone, the tunnel's frame) in snapshot cells (x, y, z)."""
        return (np.asarray(points, dtype=float) - self.low) / self.cell_m

    def inside(self, points: np.ndarray) -> np.ndarray:
        nz, ny, nx = self.u.shape[1:4]
        i = self.index(points)
        return np.all((i >= 0) & (i <= np.array([nx, ny, nz]) - 1.0001), axis=1)


def read_motion(folder: Path) -> Motion | None:
    """A case's snapshots, or None for a case run before the fork wrote them."""
    snaps = Path(folder) / "snaps"
    if not (snaps / "snaps.txt").is_file():
        return None
    s = _settings(snaps / "snaps.txt")
    count, nx, ny, nz, coarsen = (int(s[k]) for k in ("count", "nx", "ny", "nz", "coarsen"))
    fine = 1.0 / s["cells_per_m"]
    origin = np.array([s["origin_x"], s["origin_y"], s["origin_z"]])
    corner = np.array([s["x0"], s["y0"], s["z0"]]) + (coarsen - 1) / 2
    to_m = s["u_max"] / 32767
    u = np.empty((count, nz, ny, nx, 3), dtype=np.float32)
    pny, pnz = int(s["plane_ny"]), int(s["plane_nz"])
    planes = np.empty((count, pnz, pny), dtype=np.float32)
    for k in range(count):
        raw = np.fromfile(snaps / f"snap-{k:03d}.bin", dtype="<i2")
        u[k] = raw.reshape(nz, ny, nx, 3) * to_m
        plane = np.fromfile(snaps / f"plane-{k:03d}.bin", dtype="<u2")
        planes[k] = plane.reshape(pnz, pny) * (s["u_max"] / 65535)
    times = np.array([float(t) for t in (snaps / "times.txt").read_text().split()][:count])
    plane_low = (np.array([s["plane_x"], 0.0, 0.0]) - origin) * fine
    return Motion(u, times, planes, coarsen * fine, (corner - origin) * fine, fine, plane_low,
                  rotation(s["yaw_deg"], s["pitch_deg"]), s["speed"])  # fmt: skip


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


@dataclass(frozen=True)
class Loop:
    """The snapshots as a loop: `period` seconds of the air's time that end where they began."""

    times: np.ndarray  # s from the first snapshot
    blend: float  # s, the seam's ease
    period: float  # s

    @classmethod
    def of(cls, motion: Motion, blend_share: float = BLEND_SHARE) -> "Loop":
        t = motion.times - motion.times[0]
        blend = blend_share * t[-1]
        return cls(t, blend, t[-1] - blend)

    def mix(self, tau: np.ndarray):
        """For loop times `tau`, the snapshots to blend: two fractional snapshot indices and the
        weight of the first. Past the seam it's one snapshot; across it, the end eases into the
        start."""
        tau = np.mod(np.asarray(tau, dtype=float), self.period)
        frame = np.arange(len(self.times), dtype=float)
        here = np.interp(tau, self.times, frame)
        later = np.interp(tau + self.period, self.times, frame)
        weight = np.where(tau < self.blend, _smooth(tau / max(self.blend, 1e-9)), 1.0)
        return here, later, weight


def _trilinear(volume: np.ndarray, k: np.ndarray, cells: np.ndarray) -> np.ndarray:
    """`volume` (frames, z, y, x, ...) in snapshot k (per point) at cells (x, y, z)."""
    nz, ny, nx = volume.shape[1:4]
    x = np.clip(cells[:, 0], 0, nx - 1.0001)
    y = np.clip(cells[:, 1], 0, ny - 1.0001)
    z = np.clip(cells[:, 2], 0, nz - 1.0001)
    i, j, m = x.astype(int), y.astype(int), z.astype(int)
    fx, fy, fz = (x - i)[:, None], (y - j)[:, None], (z - m)[:, None]
    out = 0.0
    for dz, wz in ((0, 1 - fz), (1, fz)):
        for dy, wy in ((0, 1 - fy), (1, fy)):
            for dx, wx in ((0, 1 - fx), (1, fx)):
                out = out + volume[k, m + dz, j + dy, i + dx] * (wx * wy * wz)
    return out


def velocity(motion: Motion, loop: Loop, points: np.ndarray, tau: np.ndarray) -> np.ndarray:
    """The air's velocity (m/s, the tunnel's frame) at points and loop times."""
    cells = motion.index(points)
    last = len(motion.times) - 2

    def at(index):
        k = np.clip(np.floor(index).astype(int), 0, last)
        a = (index - k)[:, None]
        return (1 - a) * _trilinear(motion.u, k, cells) + a * _trilinear(motion.u, k + 1, cells)

    here, later, weight = loop.mix(tau)
    v = at(here)
    seam = weight < 1.0
    if np.any(seam):
        w = weight[seam][:, None]
        v[seam] = w * v[seam] + (1 - w) * at(later)[seam]
    return v


@dataclass(frozen=True)
class Particles:
    births: np.ndarray  # (n,) the loop frame each is released at
    tracks: list  # each (frames, 3) m, the drone's frame, a frame apart from its release
    speeds: list  # each (frames,) m/s


def carry(motion: Motion, loop: Loop, seeds: np.ndarray, births: np.ndarray,
          frames: int = LOOP_FRAMES) -> Particles:  # fmt: skip
    """Each seed (m from the drone, the tunnel's frame) released at its loop frame and carried
    through the flow for up to a loop, until it leaves the box."""
    dt = loop.period / frames
    h = dt / SUBSTEPS
    p = np.asarray(seeds, dtype=float).copy()
    tau = np.asarray(births, dtype=float) * dt
    alive = motion.inside(p)
    n = len(p)
    tracks = [[] for _ in range(n)]
    speeds = [[] for _ in range(n)]
    for _ in range(frames):
        idx = np.flatnonzero(alive)
        if not len(idx):
            break
        v = velocity(motion, loop, p[idx], tau[idx])
        drone = p[idx] @ motion.turn  # into the drone's frame: turn.T @ each point
        speed = np.linalg.norm(v, axis=1)
        for n_, i in enumerate(idx):
            tracks[i].append(drone[n_])
            speeds[i].append(speed[n_])
        for _ in range(SUBSTEPS):
            q = p[idx]
            v1 = velocity(motion, loop, q, tau[idx])
            v2 = velocity(motion, loop, q + 0.5 * h * v1, tau[idx] + 0.5 * h)
            p[idx] = q + h * v2
            tau[idx] += h
        alive[idx] = motion.inside(p[idx])
    return Particles(np.asarray(births), [np.array(t) for t in tracks],
                     [np.array(s) for s in speeds])  # fmt: skip


def outline_in_tunnel(field) -> tuple[np.ndarray, np.ndarray]:
    """The drone's extent, m from it along the tunnel's axes, from the averaged field's solid."""
    z, y, x = np.nonzero(field.solid > 0.3)
    metres = (np.column_stack([x, y, z]) - field.origin) * field.cell_m
    return metres.min(axis=0), metres.max(axis=0)


def seeds_for(motion: Motion, low: np.ndarray, high: np.ndarray, hubs=(), radius: float = 0.0,
              count: int = PARTICLES, seed: int = 0):  # fmt: skip
    """Where and when each particle is released, m from the drone along the tunnel's axes: in a
    wind, upstream (most in front of the drone, the rest spread wide) and some in the wake; in the
    hover, above it, around it, and just over each disk. Each one's loop frame too."""
    rng = np.random.default_rng(seed)
    box_low = motion.low + motion.cell_m
    box_high = motion.low + motion.cell_m * (np.array(motion.u.shape[3:0:-1]) - 2)
    wake = int(count * WAKE_SHARE)
    if motion.speed > 0:
        rest = count - wake
        near = int(rest * NEAR_SHARE)
        y = max(low[1] - AHEAD_M, box_low[1])
        front = np.column_stack([
            rng.uniform(low[0] - NEAR_MARGIN_M, high[0] + NEAR_MARGIN_M, near),
            np.full(near, y),
            rng.uniform(low[2] - NEAR_MARGIN_M, high[2] + NEAR_MARGIN_M, near),
        ])  # fmt: skip
        wide = np.column_stack([
            rng.uniform(box_low[0], box_high[0], rest - near),
            np.full(rest - near, y),
            rng.uniform(box_low[2], box_high[2], rest - near),
        ])  # fmt: skip
        behind = np.column_stack([
            rng.uniform(low[0], high[0], wake),
            rng.uniform(high[1] - 0.05, high[1] + 0.35, wake),
            rng.uniform(low[2], high[2], wake),
        ])  # fmt: skip
        points = np.vstack([front, wide, behind])
    else:
        above_n = int(count * 0.5)
        side_n = int(count * 0.25)
        disk_n = count - above_n - side_n
        # spread through the air above it, not on one plane: the air drawn in up there is slow,
        # and releases on a plane would sit in a visible disk while they faded in
        r = 0.45 * np.sqrt(rng.uniform(0, 1, above_n))
        a = rng.uniform(0, 2 * math.pi, above_n)
        top = box_high[2] - 0.05
        z = rng.uniform(min(high[2] + 0.06, top), top, above_n)
        above = np.column_stack([r * np.cos(a), r * np.sin(a), z])

        r = rng.uniform(0.40, 0.48, side_n)
        a = rng.uniform(0, 2 * math.pi, side_n)
        side = np.column_stack([r * np.cos(a), r * np.sin(a), rng.uniform(-0.6, 0.3, side_n)])
        disks = []
        for k in range(disk_n):
            hx, hy, hz = hubs[k % len(hubs)] if hubs else (0.0, 0.0, 0.0)
            rr = 0.9 * radius * math.sqrt(rng.uniform())
            aa = rng.uniform(0, 2 * math.pi)
            disks.append((hx + rr * math.cos(aa), hy + rr * math.sin(aa), hz + 0.02))
        points = np.vstack([above, side, np.array(disks).reshape(-1, 3)])
    births = rng.integers(0, LOOP_FRAMES, len(points))
    # a release inside the drone (where the air's still) moves upstream until it's in moving air
    loop = Loop.of(motion)
    for _ in range(8):
        still = np.linalg.norm(velocity(motion, loop, points, births * loop.period / LOOP_FRAMES),
                               axis=1) < STOPPED_M_S  # fmt: skip
        still &= motion.speed > 0
        if not np.any(still):
            break
        points[still, 1] -= 0.03
    return np.clip(points, box_low, box_high), births


def plane_frames(motion: Motion, loop: Loop, color_max: float, across, up,
                 frames: int = LOOP_FRAMES, width: int = PLANE_WIDTH):  # fmt: skip
    """The speed on the slice through the drone at each loop frame, from `across` (m from the
    drone along the tunnel's y, the wind's way) and `up` (its z, top first), as bytes (the share
    of color_max), first row at the top; and the slice's corners in the drone's frame."""
    (y0, y1), (z_top, z_bottom) = across, up
    height = round(width * abs(z_top - z_bottom) / (y1 - y0))
    ys = np.linspace(y0, y1, width)
    zs = np.linspace(z_top, z_bottom, height)
    # the plane's cells for those, fractional
    jy = (ys - motion.plane_low[1]) / motion.fine_m
    kz = (zs - motion.plane_low[2]) / motion.fine_m
    pnz, pny = motion.planes.shape[1:]
    jy, kz = np.clip(jy, 0, pny - 1.0001), np.clip(kz, 0, pnz - 1.0001)
    j0, k0 = jy.astype(int), kz.astype(int)
    fj, fk = (jy - j0)[None, :], (kz - k0)[:, None]

    def cut(plane):
        a = plane[np.ix_(k0, j0)] * (1 - fj) + plane[np.ix_(k0, j0 + 1)] * fj
        b = plane[np.ix_(k0 + 1, j0)] * (1 - fj) + plane[np.ix_(k0 + 1, j0 + 1)] * fj
        return a * (1 - fk) + b * fk

    out = np.empty((frames, height, width), dtype=np.uint8)
    last = len(motion.times) - 2
    for f in range(frames):
        here, later, weight = loop.mix(np.array([f * loop.period / frames]))

        def at(index):
            k = int(np.clip(np.floor(index), 0, last))
            a = index - k
            return (1 - a) * cut(motion.planes[k]) + a * cut(motion.planes[k + 1])

        speed = at(here[0])
        if weight[0] < 1:
            speed = weight[0] * speed + (1 - weight[0]) * at(later[0])
        out[f] = np.clip(np.round(speed / color_max * 255), 0, 255).astype(np.uint8)
    x = motion.plane_low[0]
    corners = np.array([[x, y0, z_top], [x, y1, z_top], [x, y1, z_bottom], [x, y0, z_bottom]])
    return out, corners @ motion.turn  # into the drone's frame


def particle_bytes(particles: Particles, color_max: float) -> bytes:
    """The particles for the site, little-endian: the count, the frames a loop and the points in
    all (uint32 each); each one's release frame and its number of points (uint16 each); then
    every point, one particle after another, in mm in the drone's frame (int16 x, y, z), and each
    point's speed as a share of color_max (uint8)."""
    tracks = [t if len(t) else np.zeros((0, 3)) for t in particles.tracks]
    lengths = np.array([len(t) for t in tracks], dtype=np.uint16)
    points = np.vstack(tracks) if lengths.sum() else np.zeros((0, 3))
    speeds = np.concatenate([s for s in particles.speeds if len(s)] or [np.zeros(0)])
    header = np.array([len(tracks), LOOP_FRAMES, len(points)], dtype="<u4").tobytes()
    mm = np.clip(np.round(points * 1000), -32767, 32767).astype("<i2")
    share = np.clip(np.round(speeds / color_max * 255), 0, 255).astype(np.uint8)
    return (header + particles.births.astype("<u2").tobytes() + lengths.astype("<u2").tobytes()
            + mm.tobytes() + share.tobytes())  # fmt: skip
