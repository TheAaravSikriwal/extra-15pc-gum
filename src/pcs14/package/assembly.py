"""The assembly guide: the build order, each step's parts and the hardware that holds them, and
a render of the drone built up to that step, its new parts in spearmint.

The order is mine (written down in the step 8 spec): the frame, the motors, the stack, power,
the safety monitor, the sensors and radios, the module rail, the legs and tray, the wiring, the
pack, then each module. The words come from where the CAD puts each part (design/cad.yaml's
`place` notes) and what holds it (its `hardware`, with that list's own notes). Props go on
last, and only for the first tethered flight.
"""

from dataclasses import dataclass
from pathlib import Path

from pcs14.cad.hardware import HARDWARE_PARTS
from pcs14.cad.settings import WIRING_PARTS


@dataclass(frozen=True)
class Step:
    title: str
    module: str  # base, V, P or C
    parts: tuple[str, ...]  # catalog ids, and "wiring" for the module's wires
    words: str


STEPS = (
    Step(
        "The frame",
        "base",
        ("iflight-nazgul-xl10-v6",),
        "Build the Nazgul XL10's frame from iFlight's own instructions, the arms between the "
        "bottom plates. Leave the top plate off until the stack and the safety monitor are "
        "in: everything in the bay goes in from above.",
    ),
    Step(
        "The motors",
        "base",
        ("emax-e3-2814-850kv",),
        "One motor on each arm, with the screws that come with it. A screw that's too long "
        "reaches the windings and shorts them, so check each one's length against the motor's "
        "mount before it goes in. Leave the motor leads long for now; they're cut to their "
        "routes in the wiring.",
    ),
    Step(
        "The stack",
        "base",
        ("holybro-tekko32-f4-50a", "ark-fpv"),
        "The ESC on the middle plate on its silicone grommets, then the nylon spacers, then "
        "the ARK FPV with its arrow pointing forward, the four M3 x 30 screws through all of "
        "it. The flight controller's top sits under the top plate.",
    ),
    Step(
        "Power",
        "base",
        ("matek-bec12s-pro", "branch-fuses"),
        "The BEC goes in the bay behind the ESC, turned across. The two fuses are soldered "
        "inline later, in the wiring, off the frame's back edge beside the battery leads, end "
        "to end.",
    ),
    Step(
        "The safety monitor",
        "base",
        (
            "safety-monitor-carrier",
            "pjrc-teensy-41",
            "adafruit-lsm6dsox",
            "cjmcu-5018",
            "safety-monitor-buffers",
            "bat54c-on-adapter",
            "pololu-d36v6f3",
        ),
        "The printed carrier in front of the stack, and the Teensy on it. The motor cut board "
        "sits on the Teensy, with the 3.3 V regulator on the cut board; the buffers go on the "
        "Teensy's front half and the BAT54C behind them. The monitor's own IMU sits ahead of "
        "the Teensy, on its own, so it never shares the flight controller's vibration "
        "mounts.",
    ),
    Step(
        "Sensors and radios",
        "base",
        ("radiomaster-rp2-v2", "lidar-bracket", "benewake-tf-luna", "remote-id-mount", "ruko-r111"),
        "The receiver at the back of the bay, its ceramic antenna at the back. The lidar "
        "bracket under the nose of the bottom plate, and the TF-Luna on it by its two ears, "
        "looking straight down with nothing in its view. The Remote ID module on its mount "
        "at the front of the top plate, away from the GPS.",
    ),
    Step(
        "The module rail",
        "base",
        ("module-mount", "module-socket"),
        "Press the three brass inserts into the rail with a soldering iron, then fix the rail "
        "to the top plate. V's and P's sockets sink into the rail; C's sits off the bottom "
        "plate's back edge.",
    ),
    Step(
        "Legs and tray",
        "base",
        ("landing-legs", "battery-tray"),
        "The four TPU legs, two screws through each leg's flange and its arm, and the battery "
        "tray under the bottom plate.",
    ),
    Step(
        "Base's wiring",
        "base",
        ("base-wiring",),
        "Follow the wiring guide harness by harness, and make its meter checks before "
        "anything gets power. Then the top plate goes on.",
    ),
    Step(
        "The pack",
        "base",
        ("molicel-p45b",),
        "Build the 6S2P pack: 12 cells, two in parallel for each of six in series, joined "
        "with 10 by 0.3 mm nickel-plated copper strip (not nickel strip, which would run hot "
        "at 90 A), fish paper on every positive end, the balance lead to each junction and "
        "the 12 AWG leads to an XT60. Spot-weld the strip, never solder a cell. If you've "
        "never built a pack, buy one built to the same spec instead: a pack fire is the "
        "worst thing that can happen on this bench.",
    ),
    Step(
        "V: the GPS mast",
        "V",
        ("gps-mast", "ark-gps"),
        "The mast's carbon tube into its printed foot and cradle, and the ARK GPS on top with "
        "four pads of foam tape, its arrow forward. The mast keeps the GPS's compass away "
        "from the power wiring.",
    ),
    Step(
        "V: the camera",
        "V",
        ("camera-bracket", "rpi-camera-module-3", "rpi-camera-cable-standard-mini"),
        "The camera bracket's tab to the top plate's nose, and the Camera Module 3 on it, "
        "looking forward and tipped 30 degrees down. The ribbon runs back to the Pi under "
        "the top plate's edge.",
    ),
    Step(
        "V: the Pi stack",
        "V",
        (
            "v-housing",
            "module-plug",
            "rpi-5-4gb",
            "rpi-active-cooler",
            "heltec-ht-hc01p",
            "halow-antenna-915",
            "v-wiring",
        ),
        "The module plug through the housing's floor, then the Pi on 6 mm standoffs above "
        "it, the active cooler on the Pi, the HaLow HAT on 11 mm standoffs on a stacking "
        "header, and the antenna out the back of the housing, high and to the left. The "
        "housing slides onto the rail and locks with its thumb screw.",
    ),
    Step(
        "P: the parachute",
        "P",
        (
            "p-mount",
            "fruity-chutes-harrier-40-42",
            "module-plug",
            "ark-cannode",
            "p-chute-switch",
            "pololu-d36v6f3",
            "adafruit-lm66200",
            "p-wiring",
        ),
        "The printed cradle on the rail with its two screws (two, for the opening shock), the "
        "module plug inside it, and the Harrier on the cradle's lip by the three 4-40 screws "
        "in its base. The CANnode straps to one side of the cradle, the chute switch, its "
        "regulator and the ideal-diode board to the other, inline on the servo's leads.",
    ),
    Step(
        "C: the claws",
        "C",
        ("claws-placeholder", "ark-cannode", "module-plug", "c-wiring"),
        "A placeholder: the claws aren't designed yet. The CANnode sits on top of them, "
        "behind the pack, and the module plug mates to C's socket from behind.",
    ),
    Step(
        "Props, last",
        "base",
        ("gemfan-1050x3",),
        "Not until the bench checks pass and the first flight is tethered: props off for "
        "every test before that. Two turn each way; match each to its motor's direction in "
        "the firmware guide, and check every prop nut before every flight.",
    ),
)


def hardware_label(f) -> str:
    size = (
        f"{f.size} x {f.length_mm:g} "
        if f.size and f.length_mm
        else (f"{f.size} " if f.size else "")
    )
    material = f", {f.material}" if f.material else ""
    return f"{f.count} x {size}{f.what}{material}"


def step_hardware(step: Step, fasteners) -> list[str]:
    """The hardware lines that hold this step's parts, with their notes."""
    out = []
    for f in fasteners:
        if f.holds in step.parts and (f.module is None or f.module == step.module):
            out.append(hardware_label(f) + (f": {f.note}" if f.note else ""))
    return out


def covered(build) -> tuple[set[str], set[str]]:
    """The build's part ids the steps place, and any they miss (the wiring and hardware
    bundles go with their module's wiring step and every step's hardware)."""
    wanted = {build.motor.id, build.prop.id, build.esc.id, build.frame.id, build.pack.cell.id}
    wanted |= {p.id for p in build.base}
    for parts in build.modules.values():
        wanted |= {p.id for p in parts}
    bundles = set(HARDWARE_PARTS.values())
    placed = {p for s in STEPS for p in s.parts} | bundles
    return placed & wanted, wanted - placed - set(WIRING_PARTS.values()) - bundles


def render(fasteners, generated: str, stills: dict[str, str] | None = None) -> str:
    stills = stills or {}
    out = [
        "# The assembly guide",
        "",
        f"*Generated {generated} by `pcs14 package`, from the build, the CAD's placements and "
        "its hardware list. Each picture is the CAD's drone built up to that step, the new "
        "parts in spearmint. Parts lists are in [parts.md](parts.md), the wiring in "
        "[wiring.md](wiring.md).*",
        "",
        "Work on a clean bench with the pack nowhere near it until the pack's own step. The "
        "props stay off until the first tethered flight.",
    ]
    for k, step in enumerate(STEPS, start=1):
        out += ["", f"## {k}. {step.title}", "", step.words, ""]
        hold = step_hardware(step, fasteners)
        if hold:
            out += ["What holds it:", ""] + [f"- {h}" for h in hold] + [""]
        if step.title in stills:
            out += [f"![{step.title}]({stills[step.title]})", ""]
    return "\n".join(out)


def render_stills(drone_pieces, folder: Path) -> dict[str, str]:
    """A three-quarter render for each step: the drone so far in gray, the step's new parts in
    spearmint. Module steps show Base and that module only. Returns {step title: relative
    path}."""
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    from pcs14 import style
    from pcs14.cad import views
    from pcs14.report import charts

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    cache = {}
    for piece in drone_pieces:
        polygons, _ = views._triangles([piece])
        cache[piece.name] = polygons
    shades = {}
    for piece in drone_pieces:
        shades[piece.name] = [_shade(p) for p in cache[piece.name]]
    done: set[str] = set()
    out = {}
    for k, step in enumerate(STEPS, start=1):
        new = {p.name for p in drone_pieces if _in_step(p, step)}
        shown = [
            p
            for p in drone_pieces
            if (p.name in done or p.name in new) and p.module in ("base", step.module)
        ]
        if not new:
            continue
        polygons, colors = [], []
        for p in shown:
            base = np.array(style.rgb("accent" if p.name in new else "muted")) / 255
            dim = 1.0 if p.name in new else 0.8
            for tri, shade in zip(cache[p.name], shades[p.name], strict=True):
                polygons.append(tri)
                colors.append(np.clip(base * shade * dim, 0, 1))
        canvas = charts.Canvas(
            f"Step {k}: {step.title}",
            "The drone so far; this step's parts in spearmint",
            made_up=False,
            size="wide",
        )
        flat = canvas.axes[0]
        rect = (0.0, 0.04, 1.0, 0.76)  # no headline here: the drone gets everything under the title
        canvas.fig.delaxes(flat)
        ax = canvas.fig.add_axes(rect, projection="3d", facecolor=charts._c("background"))
        ax.add_collection3d(Poly3DCollection(polygons, facecolors=colors, edgecolors="none"))
        every = np.concatenate([t for p in drone_pieces for t in cache[p.name]])
        low, high = every.min(axis=0), every.max(axis=0)
        middle, half = (low + high) / 2, (high - low).max() / 2
        for setter, m in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), middle, strict=True):
            setter(m - half, m + half)
        ax.set_box_aspect((1, 1, 1), zoom=1.5)
        ax.set_proj_type("ortho")
        ax.view_init(*views.VIEWS["three-quarter"])
        ax.set_axis_off()
        name = f"step-{k:02d}-wide.png"
        canvas.save(folder / name)
        out[step.title] = f"stills/{name}"
        done |= new
    return out


def _in_step(piece, step: Step) -> bool:
    if piece.part_id is not None:
        return piece.part_id in step.parts and piece.module == step.module
    # the wires: with their module's wiring step
    wiring = WIRING_PARTS.get(piece.module)
    return piece.kind == "wire" and wiring in step.parts


def _shade(tri) -> float:
    import numpy as np

    from pcs14.cad.views import LIGHT

    normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
    length = np.linalg.norm(normal)
    return 0.35 + 0.65 * max(0.0, float(np.dot(normal / length, LIGHT))) if length else 0.35
