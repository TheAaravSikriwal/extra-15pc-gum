"""Change detection (#11): the same ground mapped twice, the two orthomosaics differenced where
both saw it, and whatever changed flagged on the map, so the safe spots stay safe.

A moved thing shows up twice: where it was, and where it went. Specks smaller than half a
square meter are left out, which is most of what two runs disagree on without anything having
changed (a shadow's edge, a tall thing leaning a little differently from a slightly different
path).
"""

from dataclasses import dataclass

import numpy as np

TOLERANCE = 40.0  # color difference that counts as changed
MIN_AREA_M2 = 0.5


@dataclass(frozen=True)
class Blob:
    east: float
    north: float
    area_m2: float


def changes(before, after, tolerance: float = TOLERANCE,
            min_area_m2: float = MIN_AREA_M2) -> list[Blob]:  # fmt: skip
    """What changed between two orthomosaics of the same area (pcs14.smart.ortho.Mosaic)."""
    from scipy.ndimage import binary_opening, label

    a, b = before.image.astype(float), after.image.astype(float)
    seen = (a.sum(axis=2) > 0) & (b.sum(axis=2) > 0)
    differ = (np.linalg.norm(a - b, axis=2) > tolerance) & seen
    differ = binary_opening(differ, structure=np.ones((3, 3)))
    labels, count = label(differ)
    out = []
    px = before.m_per_px**2
    for k in range(1, count + 1):
        rows, cols = np.nonzero(labels == k)
        area = rows.size * px
        if area < min_area_m2:
            continue
        east = before.east0 + (cols.mean() + 0.5) * before.m_per_px
        north = before.north1 - (rows.mean() + 0.5) * before.m_per_px
        out.append(Blob(float(east), float(north), float(area)))
    return out
