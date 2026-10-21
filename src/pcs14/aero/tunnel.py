"""The wind tunnel's visual cases, run in FluidX3D.

FluidX3D lives in its own folder (C:\\dr\\fluidx3d, or wherever FLUIDX3D_DIR says), with this
project's setup added to it as marked, altered source. That setup reads one case file,
bin/case.txt, which this module writes, with the drone's meshes in meters in its own frame (x
forward, y left, z up) so the body and the props land together:

- cruise: the drone nose-first into its 10 m/s cruise, pitched forward the way it flies
- crosswind: the 10 m/s wind the hover holds against, from the drone's right
- hover: still air, and each prop an actuator disk pushing its share of the weight down. The
  first hover runs spun the real blades as moving boundaries, but at 3.4 mm cells a 10x5
  blade's pitch rises about one cell across its chord, so the blades came out as flat paddles
  that flung the air sideways and pushed none down. A disk of cells, each given its share of
  the thrust as a force on the air, makes the downwash the momentum says it should

Nothing FluidX3D makes goes into this repo until its public fork is up (its license wants the
altered source published with any results), so the frames and the stills land in
outputs/tunnel/. The force FluidX3D reports is visual-grade: its own docs say it runs 1.3 to 2x
high without a wall model. The drag numbers come from OpenFOAM.
"""

import math
import os
import shutil
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path

from pcs14.flight.generate import ORDER

DEFAULT_DIR = Path(r"C:\dr\fluidx3d")
VIEWS = ("side-streamlines", "quarter-streamlines", "side-speed", "quarter-vortices",
         "side-vortices")  # fmt: skip
# the frames along the way, for the project site to play the flow back: how many over a run,
# and of which views (FluidX3D names them play-<view>-<time step>.png)
PLAY_FRAMES = 40
PLAY_VIEWS = ("side-speed", "quarter-vortices")
G = 9.80665


@dataclass(frozen=True)
class Prop:
    stl: str  # file name, in FluidX3D's stl folder
    hub: tuple[float, float, float]  # m, in the drone's frame
    spin: int  # +1 counterclockwise seen from above, -1 clockwise


@dataclass(frozen=True)
class Case:
    name: str
    mode: str  # tunnel or hover
    setup: str  # the module combination
    body: str  # file name, in FluidX3D's stl folder
    speed: float = 10.0  # m/s, the wind
    yaw_deg: float = -90.0  # about up: -90 puts the nose into the wind
    pitch_deg: float = 0.0  # nose down
    box: tuple[float, float, float] = (1.4, 3.2, 1.1)  # m: across, along the wind, up
    at: tuple[float, float, float] = (0.5, 0.33, 0.5)  # the drone's origin, as a box share
    time_s: float = 0.48
    # MB of the GPU for the lattice. The 3060 has 12 GB, but its OpenCL driver caps any one
    # buffer at a quarter of that, and the biggest (the 19 populations, 2 bytes each) has to
    # fit: 6000 MB asked for a 3.4 GB buffer. 5000 is about 78 million cells
    memory_mb: int = 5000
    omega: float = 0.0  # rad/s, the props
    radius: float = 0.127  # m, the props' tips
    props: tuple[Prop, ...] = field(default_factory=tuple)
    slice_x_m: float = 0.0  # m along the box's x from the drone: where the slice cuts
    zoom: float = 2.6
    # m/s at the top of the speed colors: the 10 m/s wind at about 60% of the scale; in the
    # hover, the downwash, about 7 m/s at the disks by momentum theory and twice that below them
    color_max_m_s: float = 17.0
    rotor: str = "geometry"  # the props as spinning blades, or "disk": actuator disks
    thrust_n: float = 0.0  # N, each prop's push, for the disks
    frames: int = PLAY_FRAMES  # along the way, of PLAY_VIEWS

    def text(self) -> str:
        """The case file FluidX3D's setup reads: one key = value per line."""
        lines = [
            "# written by pcs14 tunnel; FluidX3D's Extra 15pc Gum setup reads it",
            f"name = {self.name}",
            f"mode = {self.mode}",
            f"body = {self.body}",
            f"memory_mb = {self.memory_mb}",
            f"time_s = {self.time_s:g}",
            f"box_x = {self.box[0]:g}",
            f"box_y = {self.box[1]:g}",
            f"box_z = {self.box[2]:g}",
            f"at_x = {self.at[0]:g}",
            f"at_y = {self.at[1]:g}",
            f"at_z = {self.at[2]:g}",
            f"speed = {self.speed:g}",
            f"yaw_deg = {self.yaw_deg:g}",
            f"pitch_deg = {self.pitch_deg:.3f}",
            f"omega = {self.omega:.3f}",
            f"radius = {self.radius:g}",
            f"slice_x_m = {self.slice_x_m:g}",
            f"zoom = {self.zoom:g}",
            f"color_max_m_s = {self.color_max_m_s:g}",
            f"rotor = {self.rotor}",
            f"thrust_n = {self.thrust_n:g}",
            f"frames = {self.frames}",
            f"props = {len(self.props)}",
        ]
        for k, p in enumerate(self.props):
            lines += [f"prop_{k} = {p.stl}", f"prop_{k}_x = {p.hub[0]:.5f}",
                      f"prop_{k}_y = {p.hub[1]:.5f}", f"prop_{k}_z = {p.hub[2]:.5f}",
                      f"prop_{k}_spin = {p.spin}"]  # fmt: skip
        return "\n".join(lines) + "\n"


def spin_at(x: float, y: float) -> int:
    """+1 or -1, the way the prop at (x, y) turns: PX4's quad X (pcs14.flight.generate.ORDER),
    0 front right and 1 back left counterclockwise, 2 front left and 3 back right clockwise."""
    for front, left, direction in ORDER:
        if (x > 0) == front and (y > 0) == left:
            return 1 if direction == "ccw" else -1
    raise ValueError(f"no rotor at {x}, {y}")


def cases(setup_name: str, cruise_pitch_deg: float, hover_omega: float, radius: float,
          props: tuple[Prop, ...], slice_x_m: float,
          hover_thrust_n: float = 0.0) -> list[Case]:  # fmt: skip
    """The three visual cases for one combination."""
    body = f"{setup_name.lower().replace('+', '_')}-body.stl"
    cruise = Case(f"{setup_name}-cruise", "tunnel", setup_name, body,
                  pitch_deg=cruise_pitch_deg)  # fmt: skip
    crosswind = replace(cruise, name=f"{setup_name}-crosswind", yaw_deg=0.0, pitch_deg=0.0)
    # still air and spinning props: a tall box with the drone a little above its middle, where
    # the side views center, so the downwash has room below it in the picture; 0.3 s (about 30
    # turns of the props) for it to reach down past a meter
    hover = Case(f"{setup_name}-hover", "hover", setup_name, body, speed=0.0, yaw_deg=0.0,
                 box=(1.2, 1.2, 2.2), at=(0.5, 0.5, 0.6), time_s=0.3, omega=hover_omega,
                 radius=radius, props=props, slice_x_m=slice_x_m, zoom=1.6,
                 color_max_m_s=15.0, rotor="disk", thrust_n=hover_thrust_n)  # fmt: skip
    return [cruise, crosswind, hover]


def fluidx3d_dir(environ=None) -> Path:
    environ = os.environ if environ is None else environ
    return Path(environ.get("FLUIDX3D_DIR") or DEFAULT_DIR)


def export(drone, setup, folder: Path) -> tuple[str, tuple[Prop, ...], float]:
    """The combination's body (watertight, props and wires left out) and each prop, as STL in
    meters in the drone's frame, into `folder`. Returns the body's file name, the props, and
    how far forward the front props' hubs are (for the slice through them)."""
    from build123d import Plane, Pos, export_stl, mirror

    from pcs14.cad.checks import trim
    from pcs14.cad.export import export_cfd

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stem = setup.name.lower().replace("+", "_")
    assembly = trim(drone, setup.modules)
    body = f"{stem}-body.stl"
    export_cfd(assembly.pieces, folder / body)
    props = []
    for piece in assembly.pieces:
        if piece.kind != "prop":
            continue
        # the hub is where the CAD put the prop (a three-blade prop's bounding box isn't
        # centered on it)
        at = piece.solid.location.position
        hub = (at.X, at.Y, at.Z)
        spin = spin_at(hub[0], hub[1])
        solid = piece.solid
        if spin < 0:  # the clockwise pair: mirrored blades, the way real props come
            solid = Pos(*hub) * mirror(Pos(-hub[0], -hub[1], -hub[2]) * solid, Plane.XZ)
        name = f"{stem}-prop-{len(props)}.stl"
        export_stl(solid, folder / name, tolerance=0.0002, angular_tolerance=0.2)  # binary
        props.append(Prop(name, hub, spin))
    front = max(p.hub[0] for p in props) if props else 0.0
    return body, tuple(props), front


def case_for(drone, build, targets, setup, folder: Path) -> list[Case]:
    """Exports the meshes and works out the cases for one combination: the cruise pitch from
    the sizing model, the props' hover speed from the flight sim's motor model."""
    from pcs14.flight.generate import flight_model
    from pcs14.sizing.flight import power_model

    body, props, front = export(drone, setup, folder)
    model = flight_model(drone, build, targets, setup, mesh=None)
    power = power_model(build, setup, 0.0, pessimistic=True)
    pitch = math.degrees(power.tilt(targets.cruise_speed))
    # the box's x is the drone's x in the hover case (no yaw), so the slice sits on the front pair
    found = cases(setup.name, pitch, model.motor.hover_rot_velocity, build.prop.radius, props,
                  slice_x_m=front, hover_thrust_n=model.total_mass * G / 4)  # fmt: skip
    return [replace(c, body=body) for c in found]


def run(case: Case, home: Path, out: Path, stl_folder: Path) -> Path:
    """Runs one case in FluidX3D (Windows, with its build in `home`/bin) and copies its frames
    to `out`/<case>/. Returns that folder."""
    stl = home / "stl"
    stl.mkdir(exist_ok=True)
    for name in [case.body] + [p.stl for p in case.props]:
        shutil.copy2(Path(stl_folder) / name, stl / name)
    (home / "bin" / "case.txt").write_text(case.text(), encoding="utf-8")
    frames = home / "bin" / "export" / case.name
    if frames.exists():
        shutil.rmtree(frames)
    log = Path(out) / f"{case.name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "wb") as f:
        subprocess.run([str(home / "bin" / "FluidX3D.exe")], cwd=home / "bin", stdout=f,
                       stderr=subprocess.STDOUT, check=True)  # fmt: skip
    target = Path(out) / case.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(frames, target)
    shutil.copy2(home / "bin" / "case.txt", target / "case.txt")  # what it was asked to run
    return target


@dataclass(frozen=True)
class PlayFrame:
    step: int  # FluidX3D's time step
    seconds: float  # into the run
    files: dict  # {view: Path}, of the PLAY_VIEWS it wrote


def playback(folder: Path) -> list[PlayFrame]:
    """The frames FluidX3D wrote along the way, in order: its setup lists each one's time step
    and time in frames.txt. Empty for a case run before the frames were."""
    listed = Path(folder) / "frames.txt"
    if not listed.is_file():
        return []
    found = []
    for line in listed.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        step, seconds = line.split()[:2]
        files = {view: Path(folder) / f"play-{view}-{int(step):09d}.png" for view in PLAY_VIEWS}
        found.append(PlayFrame(int(step), float(seconds),
                               {v: f for v, f in files.items() if f.is_file()}))  # fmt: skip
    return sorted(found, key=lambda f: f.step)


def frame(folder: Path, view: str) -> Path | None:
    """The newest frame FluidX3D wrote for a view (it names them by time step)."""
    found = sorted(Path(folder).glob(f"{view}-*.png"))
    return found[-1] if found else None
