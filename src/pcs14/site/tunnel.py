"""The wind tunnel's page: its stills, with what each one says, and each case's frames along
the way, thinned to JPEGs the page can play on its clock. And for the drone view, each case's
flow moving (pcs14.aero.motion): particles carried through it, and the speed on a slice through
the drone, a loop's frames of each.

FluidX3D's license wants the altered source published with any results. My altered version is
public (FORK_URL, since 2026-10-22), so the site can carry them, crediting FluidX3D's origin. With
FORK_PUBLIC off, the data is for the site on my own machine: the page says so, and the build
check warns when the pictures are in a build.
"""

import json
import math
from pathlib import Path

import numpy as np

from pcs14.aero import flow, motion, tunnel
from pcs14.site import schema

FORK_PUBLIC = True  # my altered FluidX3D is on GitHub, in public, since 2026-10-22
FORK_URL = "https://github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum"
ORIGIN_URL = "https://github.com/ProjectPhysX/FluidX3D"  # FluidX3D itself, Dr. Moritz Lehmann's
FRAME_WIDTH = 960  # px: the page's frames, thinned from FluidX3D's 1920
NOTE = (
    "These are pictures, not measurements: FluidX3D runs high on force without a wall model, so "
    "the drag numbers will come from OpenFOAM."
)
LOCAL = (
    " And they stay on my machine until my fork of FluidX3D is public, since its license wants "
    "the changed source out first."
)


def _jpeg(source: Path, target: Path, width: int | None = None) -> None:
    from PIL import Image

    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image = image.convert("RGB")
        if width and image.width > width:
            image = image.resize((width, round(image.height * width / image.width)),
                                 Image.Resampling.LANCZOS)  # fmt: skip
        image.save(target, "JPEG", quality=86, optimize=True)


def _label(name: str) -> str:
    return name.split("-", 1)[-1].replace("-", " ").capitalize()


# each case by where the air comes from, as the drone view lists them
DIRECTION_OF = {"cruise": "front", "crosswind": "right"}
FLOW_WORDS = {
    "front": ("From the front", "Flying nose first at 10 m/s, pitched the way it cruises."),
    "back": ("From behind", "Flying tail first at 10 m/s, pitched back."),
    "right": (
        "From the right",
        "Flying sideways to its right at 10 m/s, or hovering in that wind.",
    ),
    "left": ("From the left", "Flying sideways to its left at 10 m/s."),
    "above": ("From above", "Climbing at 10 m/s, so the air comes down onto its top."),
    "below": ("From below", "Coming down at 10 m/s, so the air comes up into its belly."),
    "hover": ("Hovering", "Still air, and each prop pushing its share of the weight down."),
}


def direction_of(folder_name: str) -> str:
    end = folder_name.rsplit("-", 1)[-1]
    return DIRECTION_OF.get(end, end)


def _case_settings(folder: Path) -> dict:
    found = {}
    listed = folder / "case.txt"
    if listed.is_file():
        for line in listed.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                found[key.strip()] = value.strip()
    return found


def _write_bytes(out: Path, name: str, data: bytes) -> Path:
    """A binary data file, and its script version for a page opened from disk."""
    import base64

    path = out / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    text = base64.b64encode(data).decode("ascii")
    script = f'(window.pcs14Data = window.pcs14Data || {{}})["{name}"] = "{text}";\n'
    (out / f"{name}.js").write_bytes(script.encode("utf-8"))
    return path


# the slice's reach, m from the drone along the tunnel's y (the wind's way) and z (top first)
# (the wind's reaches to near the end of the snapshots' box, for the site to fade out over)
SLICE_REACH = {"tunnel": ((-0.45, 1.75), (0.45, -0.45)), "hover": ((-0.6, 0.6), (0.4, -1.4))}


def flow_for(folder: Path, out: Path) -> schema.TunnelFlowEntry | None:
    """A case's flow moving, under `out`/tunnel/flow: its particles and its slice, a loop's
    frames of each. None for a case run before the fork wrote its snapshots."""
    from pcs14.site.flights import _write

    moving = motion.read_motion(folder)
    field = flow.read_field(folder)
    if moving is None or field is None:
        return None
    settings = _case_settings(folder)
    direction = direction_of(folder.name)
    count = int(settings.get("props", 0))
    hubs = [tuple(float(settings[f"prop_{k}_{a}"]) for a in "xyz") for k in range(count)]
    color_max = float(settings.get("color_max_m_s", 17.0))
    loop = motion.Loop.of(moving)
    low, high = motion.outline_in_tunnel(field)
    seeds, births = motion.seeds_for(moving, low, high, hubs, float(settings.get("radius", 0.127)),
                                     seed=sum(folder.name.encode()))  # fmt: skip
    carried = motion.carry(moving, loop, seeds, births)
    across, up = SLICE_REACH["tunnel" if moving.speed > 0 else "hover"]
    frames, corners = motion.plane_frames(moving, loop, color_max, across, up)
    stem = f"tunnel/flow/{folder.name}"
    _write_bytes(out, f"{stem}-particles.bin", motion.particle_bytes(carried, color_max))
    _write_bytes(out, f"{stem}-slice.bin", frames.tobytes())
    # the force along the wind (the tunnel's y), FluidX3D's own visual-grade number
    force = round(float(field.force[1]), 2) if field.speed > 0 else None
    # the tilt it flies with, front and back; the side and vertical cases are drawn level
    pitch = float(settings.get("pitch_deg", 0.0))
    data = schema.TunnelFlow(
        schema_version=schema.SCHEMA_VERSION, name=folder.name, direction=direction,
        setup=settings.get("name", folder.name).rsplit("-", 1)[0], speed=moving.speed,
        color_max=color_max, force_n=force if force is not None and math.isfinite(force) else None,
        pitch_deg=round(pitch, 3) if abs(pitch) < 45 else 0.0,
        loop_s=round(loop.period, 5), frames=motion.LOOP_FRAMES,
        particles=schema.TunnelParticles(file=f"{stem}-particles.bin", count=len(seeds)),
        slice=schema.TunnelSlice(file=f"{stem}-slice.bin", width=frames.shape[2],
                                 height=frames.shape[1], corners=np.round(corners, 4).tolist()),
    )  # fmt: skip
    _write(out / f"{stem}.json", f"{stem}.json", data)
    label, about = FLOW_WORDS.get(direction, (_label(folder.name), ""))
    return schema.TunnelFlowEntry(name=folder.name, direction=direction, label=label,
                                  about=about, file=f"{stem}.json")  # fmt: skip


def tunnel_data(source, out) -> schema.Tunnel:
    """The stills in `source`/stills (each one's wide size) and every case folder's frames
    along the way, copied under `out`/tunnel."""
    source, out = Path(source), Path(out)
    stills = []
    listed = source / "stills" / "stills.json"
    said = json.loads(listed.read_text(encoding="utf-8")) if listed.is_file() else {}
    from pcs14.aero.stills import VISUAL

    for name, s in said.items():
        wide = source / "stills" / f"{name}-wide.png"
        if not wide.is_file():
            continue
        file = f"tunnel/{name}.jpg"
        _jpeg(wide, out / file)
        # the page says once that these are pictures, not measurements
        fields = {k: s[k] for k in ("case", "view", "title", "subtitle", "number", "caption")}
        fields["caption"] = fields["caption"].replace(" " + VISUAL, "").replace(VISUAL, "").strip()
        stills.append(schema.TunnelStill(file=file, **fields))
    cases, flows = [], []
    found = sorted(p for p in source.iterdir() if p.is_dir()) if source.is_dir() else []
    # the cruise first, then the other ways the air meets it, then the hover
    order = {"cruise": 0, "back": 1, "crosswind": 2, "left": 3, "above": 4, "below": 5, "hover": 6}
    for folder in sorted(found, key=lambda p: order.get(p.name.rsplit("-", 1)[-1], 9)):
        frames = []
        for f in tunnel.playback(folder):
            files = {}
            for view, path in f.files.items():
                file = f"tunnel/{folder.name}/{view}-{f.step:09d}.jpg"
                _jpeg(path, out / file, FRAME_WIDTH)
                files[view] = file
            frames.append(schema.TunnelFrame(step=f.step, t_s=f.seconds, files=files))
        traced = flow_for(folder, out)
        if traced is not None:
            flows.append(traced)
        if frames:
            cases.append(_case(folder, frames, source))
    # every way the air comes, the ones not run yet too, so the drone view lists them all
    have = {f.direction for f in flows}
    for direction in tunnel.DIRECTIONS:
        if direction not in have:
            label, about = FLOW_WORDS[direction]
            flows.append(schema.TunnelFlowEntry(name=direction, direction=direction, label=label,
                                                about=about))  # fmt: skip
    flows.sort(key=lambda f: tunnel.DIRECTIONS.index(f.direction)
               if f.direction in tunnel.DIRECTIONS else 99)  # fmt: skip
    return schema.Tunnel(schema_version=schema.SCHEMA_VERSION, fork_public=FORK_PUBLIC,
                         note=NOTE + ("" if FORK_PUBLIC else LOCAL), stills=stills, cases=cases,
                         flows=flows, fork_url=FORK_URL if FORK_PUBLIC else None,
                         origin_url=ORIGIN_URL)  # fmt: skip


def _case(folder: Path, frames: list, source: Path) -> schema.TunnelCase:
    """A case for the page: its frames, its name as the drone view has it, and how it was run:
    the tunnel's size, FluidX3D's grid (from its log), the seconds of air and its force."""
    import re

    direction = direction_of(folder.name)
    label, about = FLOW_WORDS.get(direction, (_label(folder.name), ""))
    settings = _case_settings(folder)
    grid = cell = steps = None
    log = source / f"{folder.name}.log"
    if log.is_file():
        said = rf"{re.escape(folder.name)}: (\d+) x (\d+) x (\d+) cells of ([\d.]+) mm, (\d+) steps"
        found = re.search(said, log.read_text(encoding="utf-8", errors="replace"))
        if found:
            grid = " x ".join(found.groups()[:3])
            cell, steps = float(found.group(4)), int(found.group(5))
    field = flow.read_field(folder)
    force = round(float(field.force[1]), 2) if field is not None and field.speed > 0 else None
    box = [float(settings[k]) for k in ("box_x", "box_y", "box_z") if k in settings] or None
    return schema.TunnelCase(name=folder.name, label=label, frames=frames, direction=direction,
                             about=about, grid=grid, cell_mm=cell, steps=steps,
                             air_s=float(settings["time_s"]) if "time_s" in settings else None,
                             box_m=box, force_n=force)  # fmt: skip


def write_tunnel(out, source) -> list[Path]:
    """tunnel.json (and its script) and the pictures it names, under `out`."""
    from pcs14.site.data import _write

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return [_write(out, "tunnel", tunnel_data(source, out))]
