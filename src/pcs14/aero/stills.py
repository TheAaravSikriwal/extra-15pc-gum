"""The wind tunnel's stills: FluidX3D's frames on the project's post canvas (the header, the
title, a big number and a caption), cropped to each post size around the drone and its wake.

They land in outputs/tunnel/stills/, not in the repo, until the FluidX3D fork is public: its
license wants the altered source published with any results.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pcs14 import style
from pcs14.report import charts

SIZES = ("portrait", "square", "vertical", "wide")
VISUAL = "A picture, not a measurement: the drag numbers will come from OpenFOAM."


@dataclass(frozen=True)
class Still:
    view: str  # FluidX3D's frame name, pcs14.aero.tunnel.VIEWS
    title: str
    subtitle: str
    number: str
    caption: str
    focus: tuple[float, float] = (0.5, 0.5)  # where to center the crop, as a share of the frame


def stills_for(case, rpm: float | None = None) -> list[Still]:
    """What each case's stills say."""
    who = "the drone with every module on" if case.setup.lower() == "max" else case.setup
    if case.mode == "hover" and case.rotor == "disk":
        push = f"{case.thrust_n:.1f} N"
        return [
            Still("side-speed", "The downwash", f"{who}, hovering: each prop a disk pushing "
                  f"{push} down", f"{push} a prop", "Each prop drives a column of air down; red "
                  "is fastest. The props are modeled as disks, not blades. " + VISUAL,
                  (0.5, 0.42)),
            Still("quarter-vortices", "The wake's edge", f"{who}, hovering: each prop a disk "
                  f"pushing {push} down", f"{push} a prop", "The edge of each column rolls up "
                  "into rings of vortices as it falls. " + VISUAL, (0.5, 0.45)),
        ]  # fmt: skip
    if case.mode == "hover":
        turning = f"{rpm:,.0f} rpm" if rpm else "hover speed"
        return [
            Still("side-speed", "The downwash", f"{who}, hovering, props at {turning}",
                  turning, "Each prop pushes a column of air down; red is fastest. The four "
                  "columns merge under the drone. " + VISUAL, (0.5, 0.42)),
            Still("quarter-vortices", "Tip vortices", f"{who}, hovering, props at {turning}",
                  turning, "Every blade tip sheds a vortex, and they spiral down with the "
                  "downwash. " + VISUAL, (0.5, 0.45)),
        ]  # fmt: skip
    if case.yaw_deg == 0.0:
        return [
            Still("side-streamlines", "Wind from the side", f"{who}, holding still in a "
                  f"{case.speed:g} m/s crosswind", f"{case.speed:g} m/s", "The wind it has to "
                  "lean into to hold its spot, and the wake that wind leaves. " + VISUAL,
                  (0.42, 0.5)),
        ]  # fmt: skip
    return [
        Still("side-streamlines", "The drag lines", f"{who} at its {case.speed:g} m/s cruise",
              f"{case.speed:g} m/s", "The air bends around the body and leaves a slow, "
              "churning wake behind it (blue). That wake is the drag. " + VISUAL,
              (0.42, 0.5)),
        Still("quarter-vortices", "The wake", f"{who} at {case.speed:g} m/s: the vortices it "
              "sheds", f"{case.speed:g} m/s", "Every edge on the frame sheds little "
              "whirlpools, and they tumble away downstream. " + VISUAL, (0.5, 0.5)),
    ]  # fmt: skip


def crop(image: np.ndarray, aspect: float, focus=(0.5, 0.5)) -> np.ndarray:
    """The biggest part of `image` with width / height = `aspect`, centered as near `focus`
    as the edges allow."""
    h, w = image.shape[:2]
    if w / h > aspect:
        cw, ch = int(round(h * aspect)), h
    else:
        cw, ch = w, int(round(w / aspect))
    x = int(round(focus[0] * w - cw / 2))
    y = int(round(focus[1] * h - ch / 2))
    x, y = min(max(x, 0), w - cw), min(max(y, 0), h - ch)
    return image[y : y + ch, x : x + cw]


def compose(frame_path: Path, still: Still, path: Path, size: str = "portrait") -> Path:
    import matplotlib.image as mpimg

    canvas = charts.Canvas(still.title, still.subtitle, made_up=False, size=size)
    (ax,) = canvas.axes
    margin = style.load()["layout"]["margin_px"]
    box = ax.get_position()
    left = margin / canvas.width
    ax.set_position((left, box.y0, 1 - 2 * left, box.height))
    aspect = (1 - 2 * left) * canvas.width / (box.height * canvas.height)
    ax.imshow(crop(mpimg.imread(frame_path), aspect, still.focus), interpolation="lanczos")
    ax.set_axis_off()
    canvas.headline(still.number, still.caption)
    canvas.save(path)
    return path


def draw(case, frames: Path, out: Path, rpm: float | None = None) -> list[Path]:
    """Every still for one case, in every post size, from its frames folder."""
    from pcs14.aero.tunnel import frame

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    said = _said(out)
    for still in stills_for(case, rpm):
        found = frame(frames, still.view)
        if found is None:
            continue
        for size in SIZES:
            paths.append(compose(found, still, out / f"{case.name}-{still.view}-{size}.png", size))
        said[f"{case.name}-{still.view}"] = {
            "case": case.name, "view": still.view, "title": still.title,
            "subtitle": still.subtitle, "number": still.number, "caption": still.caption,
        }  # fmt: skip
    (out / "stills.json").write_bytes((json.dumps(said, indent=1) + "\n").encode("utf-8"))
    return paths


def _said(out: Path) -> dict:
    """What every still drawn so far says (stills.json): each case adds its own."""
    path = out / "stills.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
