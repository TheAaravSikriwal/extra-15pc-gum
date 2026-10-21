"""The wind tunnel's page: its stills, with what each one says, and each case's frames along
the way, thinned to JPEGs the page can play on its clock.

FluidX3D's license wants the altered source published with any results, so until my fork of it
is public (FORK_PUBLIC), this data is for the site on my own machine: the page says so, and
the build check warns when the pictures are in a build.
"""

import json
from pathlib import Path

from pcs14.aero import tunnel
from pcs14.site import schema

FORK_PUBLIC = False  # flip once my fork of FluidX3D is up on GitHub, in public
FRAME_WIDTH = 960  # px: the page's frames, thinned from FluidX3D's 1920
NOTE = (
    "These are pictures, not measurements: FluidX3D runs high on force without a wall model, so "
    "the drag numbers will come from OpenFOAM. And they stay on my machine until my fork of "
    "FluidX3D is public, since its license wants the changed source out first."
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


def tunnel_data(source, out) -> schema.Tunnel:
    """The stills in `source`/stills (each one's wide size) and every case folder's frames
    along the way, copied under `out`/tunnel."""
    source, out = Path(source), Path(out)
    stills = []
    listed = source / "stills" / "stills.json"
    said = json.loads(listed.read_text(encoding="utf-8")) if listed.is_file() else {}
    for name, s in said.items():
        wide = source / "stills" / f"{name}-wide.png"
        if not wide.is_file():
            continue
        file = f"tunnel/{name}.jpg"
        _jpeg(wide, out / file)
        stills.append(schema.TunnelStill(file=file, **{k: s[k] for k in (
            "case", "view", "title", "subtitle", "number", "caption")}))  # fmt: skip
    cases = []
    found = sorted(p for p in source.iterdir() if p.is_dir()) if source.is_dir() else []
    # the cruise first, then the crosswind and the hover, the way the stills go
    order = {"cruise": 0, "crosswind": 1, "hover": 2}
    for folder in sorted(found, key=lambda p: order.get(p.name.rsplit("-", 1)[-1], 9)):
        frames = []
        for f in tunnel.playback(folder):
            files = {}
            for view, path in f.files.items():
                file = f"tunnel/{folder.name}/{view}-{f.step:09d}.jpg"
                _jpeg(path, out / file, FRAME_WIDTH)
                files[view] = file
            frames.append(schema.TunnelFrame(step=f.step, t_s=f.seconds, files=files))
        if frames:
            cases.append(schema.TunnelCase(name=folder.name, label=_label(folder.name),
                                           frames=frames))  # fmt: skip
    return schema.Tunnel(schema_version=schema.SCHEMA_VERSION, fork_public=FORK_PUBLIC,
                         note=NOTE, stills=stills, cases=cases)  # fmt: skip


def write_tunnel(out, source) -> list[Path]:
    """tunnel.json (and its script) and the pictures it names, under `out`."""
    from pcs14.site.data import _write

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return [_write(out, "tunnel", tunnel_data(source, out))]
