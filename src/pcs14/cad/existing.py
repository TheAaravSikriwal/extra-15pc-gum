"""Existing CAD models: fetched into a local cache that never gets committed (most can't be
reposted), then compared with my parts.

The comparison doesn't trust their orientation or origin, only their shape: the bounding
box's three sizes, sorted, and the spacings between holes of a given size (every pairwise
distance, sorted), which is what bolting a part down depends on.
"""

import hashlib
import io
import json
import math
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from build123d import GeomType, import_step

MM = 0.001
CACHE = Path("cad/cache")
STEP_SUFFIXES = (".step", ".stp")
MAX_DOWNLOAD = 100_000_000  # bytes


@dataclass(frozen=True)
class Comparison:
    mine: list[float]  # m, the bounding box's sizes, smallest first
    theirs: list[float]
    size_ok: bool
    holes_ok: bool | None  # None if there were no holes to compare
    note: str


def cached_model(cache: Path, part_id: str) -> Path | None:
    folder = Path(cache) / part_id
    if not folder.is_dir():
        return None
    steps = sorted(p for p in folder.rglob("*") if p.suffix.lower() in STEP_SUFFIXES)
    return steps[0] if steps else None


def load_model(path: Path):
    """A STEP file, scaled from millimeters (how the reader hands it back) to meters."""
    return import_step(path).scale(MM)


def fetch(part, cache: Path = CACHE) -> Path:
    """Download a part's existing CAD model into the cache, unzip it if needed, and note where
    it came from. Only for parts whose terms allow downloading it for my own use."""
    existing = part.cad.existing
    url = str(existing.download_url) if existing.download_url else None
    if url is None:
        raise ValueError(f"{part.id} has no download link for its existing CAD model")
    folder = Path(cache) / part.id
    folder.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError(
            f"{part.id}'s model is over {MAX_DOWNLOAD // 1_000_000} MB, so it wasn't kept"
        )
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for name in archive.namelist():
                if (
                    Path(name).suffix.lower() in STEP_SUFFIXES
                    or Path(name).name.upper() == "LICENSE.TXT"
                ):
                    (folder / Path(name).name).write_bytes(archive.read(name))
    else:
        (folder / Path(url.split("?")[0]).name).write_bytes(data)
    manifest = {
        "part": part.id,
        "url": url,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "fetched": date.today().isoformat(),
        "terms": existing.terms,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return folder


def _sizes(shape) -> list[float]:
    size = shape.bounding_box().size
    return sorted([size.X, size.Y, size.Z])


def hole_spacings(shape, diameter: float, tolerance: float = 0.0003) -> list[float]:
    """Every distance between the centers of holes this size, smallest first. Each hole's
    center is its axis, so a hole cut through several layers still counts once."""
    centers = []
    for face in shape.faces():
        if face.geom_type != GeomType.CYLINDER or abs(2 * face.radius - diameter) > tolerance:
            continue
        axis = face.axis_of_rotation
        p, d = axis.position, axis.direction
        # the point on the axis nearest the origin stands for the whole axis
        t = -(p.X * d.X + p.Y * d.Y + p.Z * d.Z)
        point = (p.X + t * d.X, p.Y + t * d.Y, p.Z + t * d.Z)
        if all(math.dist(point, c) > tolerance for c in centers):
            centers.append(point)
    return sorted(math.dist(a, b) for i, a in enumerate(centers) for b in centers[i + 1 :])


def compare(
    mine, theirs, hole_diameter: float | None = None, tolerance: float = 0.001
) -> Comparison:
    """Sizes match within 1 mm (or 5% for big parts); every spacing between my holes has to
    show up between theirs, within 0.3 mm."""
    a, b = _sizes(mine), _sizes(theirs)
    size_ok = all(abs(x - y) <= max(tolerance, 0.05 * x) for x, y in zip(a, b, strict=True))
    holes_ok = None
    if hole_diameter is not None:
        my_spacings = hole_spacings(mine, hole_diameter)
        their_spacings = hole_spacings(theirs, hole_diameter)
        if my_spacings:
            holes_ok = all(any(abs(s - t) <= 0.0003 for t in their_spacings) for s in my_spacings)
    note = (
        f"mine {' x '.join(f'{v / MM:.1f}' for v in a)} mm, "
        f"theirs {' x '.join(f'{v / MM:.1f}' for v in b)} mm"
    )
    if holes_ok is not None:
        note += "; holes line up" if holes_ok else "; holes don't line up"
    return Comparison(a, b, size_ok, holes_ok, note)
