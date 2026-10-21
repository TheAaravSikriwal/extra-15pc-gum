"""The structure side track's first report: docs/reports/structure/, by `pcs14 structure`.

The arms under the motors' full thrust, their first bending modes against the props' speeds,
the chute mount's joints against step 6's opening-jolt bound, and a rough drop number. Every
number the laminate gives is swept across its range, since iFlight publishes none.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path

from pcs14 import unproven
from pcs14.structure import beams
from pcs14.unproven import Unproven

G = 9.80665
MODULUS_GPA = (40.0, 70.0)  # woven carbon plate, an estimate: iFlight publishes nothing
STRENGTH_MPA = 400.0  # the low end for woven carbon plate in bending, an estimate
SCREW_G = 4.0  # a motor's four M3 screws, about 1 g each
NYLON_MPA = (60.0, 80.0)  # nylon 6/6's tensile strength, a typical range
STEEL_MPA = (800.0, 1200.0)  # class 8.8 to 12.9 screws' tensile strength
M3_AREA_MM2 = 5.03  # ISO 898-1's tensile stress area for M3
UNC_4_40_AREA_MM2 = 3.90  # ASME B1.1's tensile stress area for #4-40 UNC
INSERT_N = (300.0, 800.0)  # an M3 heat-set insert's pull-out in printed PETG: a guess
NEAR = 0.15  # a mode within this share of an excitation is near it
DROP_M = 1.0  # a motor cut at 1 m, the worst landing short of a crash

UNPROVEN = (
    Unproven(
        what="The laminate: iFlight publishes nothing about the Nazgul's carbon, so its "
        "stiffness runs 40 to 70 GPa and its strength from 400 MPa, typical woven plate.",
        measure="A tap test on a spare arm, clamped as on the frame, with a phone's "
        "accelerometer or a microphone: its ring frequency gives the stiffness.",
    ),
    Unproven(
        what="The clamp: where the arm's free length starts depends on how tightly the plates "
        "hold it, swept 10% either way here.",
        measure="The same tap test on the built frame.",
    ),
    Unproven(
        what="The heat-set inserts' pull-out and the printed cradle and rail: guesses, and the "
        "weakest links between the chute's riser and the frame.",
        measure="A hang test before P flies: 26 kg (the jolt's bound) from the riser's point on "
        "the mounted cradle for a minute, then 39 kg (one and a half times); nothing cracks, "
        "creeps or pulls out.",
    ),
    Unproven(
        what="Crashes, and the legs' TPU under a hard landing: no FE model without CalculiX.",
        measure="Drop tests of the legs with a dummy weight, from 0.25 m up to 1 m.",
    ),
)


@dataclass(frozen=True)
class Mode:
    name: str
    hz: tuple[float, float]  # (low, high) across the laminate's and the clamp's ranges


def arm_for(build, frame_cad, length_scale: float = 1.0) -> beams.Arm:
    """The arm from the frame's published size: motors on a `wheelbase` diagonal, leaving the
    body plates at their half-width on a 45 degree line."""
    radius = build.frame.wheelbase_mm / 2 / 1000
    clamp = frame_cad["body_width_mm"] / 2 / 1000 * math.sqrt(2)
    return beams.Arm(
        length_m=(radius - clamp) * length_scale,
        width_m=frame_cad["arm_width_mm"] / 1000,
        thickness_m=frame_cad["arm_thickness_mm"] / 1000,
        density_kg_m3=1600.0,  # design/cad.yaml's carbon
        tip_mass_kg=(build.motor.mass_g + build.prop.mass_g + SCREW_G) / 1000,
    )


def modes(build, frame_cad) -> list[Mode]:
    out = []
    for name, vertical in (("vertical", True), ("in the frame's plane", False)):
        found = [arm_for(build, frame_cad, s).first_mode_hz(e * 1e9, vertical)
                 for s in (0.9, 1.1) for e in MODULUS_GPA]  # fmt: skip
        out.append(Mode(name, (min(found), max(found))))
    return out


def _models(exports) -> list[Path]:
    """The generated models with their numbers (the payload's model has none)."""
    return [
        m for m in sorted(Path(exports, "models").glob("pcs14_*")) if (m / "model.json").is_file()
    ]


def collect(build, docs, exports) -> dict:
    frame_cad = build.frame.cad.model_dump()
    arm = arm_for(build, frame_cad)
    top_n = max(r.thrust_g for r in build.thrust_table.rows) / 1000 * G
    stress = arm.root_stress(top_n)
    sag = [arm.tip_deflection(top_n, e * 1e9) for e in MODULUS_GPA]
    hovers = {}
    for model in _models(exports):
        info = json.loads((model / "model.json").read_text(encoding="utf-8"))
        hovers[info["setup"]] = info["hover_rot_velocity"]
        top_rad_s = info["top_rot_velocity"]
    blades = build.prop.blades
    found_modes = modes(build, frame_cad)
    near = []
    for mode in found_modes:
        for setup, rad_s in hovers.items():
            for per, hz in zip((1, blades), beams.excitations_hz(rad_s, blades), strict=True):
                low, high = mode.hz
                if low * (1 - NEAR) <= hz <= high * (1 + NEAR):
                    near.append((mode.name, setup, per, hz))
    modules = json.loads((Path(docs) / "reports" / "modules" / "modules.json").read_text("utf-8"))
    bound = max(j["bound_n"] for j in modules.get("jolts", []))
    joints = [
        beams.Joint("the Harrier's base: three 4-40 steel screws", 3,
                    tuple(beams.screw_tension_n(UNC_4_40_AREA_MM2, s) for s in STEEL_MPA),
                    "the screws themselves; their threads in the Harrier's base are unknown"),
        beams.Joint("the cradle's rail locks: two M3 steel screws in heat-set inserts", 2,
                    INSERT_N, "an insert's pull-out in printed PETG, a guess"),
        beams.Joint("the rail on the top plate: four M3 nylon screws", 4,
                    tuple(beams.screw_tension_n(M3_AREA_MM2, s) for s in NYLON_MPA),
                    "nylon 6/6 in tension"),
    ]  # fmt: skip
    mass = max(json.loads((m / "model.json").read_text("utf-8"))["mass_kg"]
               for m in _models(exports))  # fmt: skip
    return {
        "arm": arm, "top_n": top_n, "stress_pa": stress, "sag_m": sag, "modes": found_modes,
        "hovers": hovers, "top_rad_s": top_rad_s, "blades": blades, "near": near,
        "bound_n": bound, "joints": joints, "drop_j": mass * G * DROP_M, "mass_kg": mass,
    }  # fmt: skip


def verdict(run: dict) -> str:
    strong = STRENGTH_MPA * 1e6 / run["stress_pa"] >= 2
    joints = all(j.margin(run["bound_n"])[0] >= 1.5 for j in run["joints"])
    if strong and joints and not run["near"]:
        return "pass"
    return "open" if strong else "fail"


def render(run: dict, generated: str) -> str:
    arm = run["arm"]
    margin = STRENGTH_MPA * 1e6 / run["stress_pa"]
    lines = [
        "# Structure, first pass: beam math",
        "",
        f"*Generated {generated} by `pcs14 structure`: textbook beams and joints in Python, "
        "since FreeCAD and CalculiX aren't installed here. The spec is "
        "[docs/specs/2026-10-21-structure-beams.md](../../specs/2026-10-21-structure-beams.md). "
        "iFlight publishes nothing about the Nazgul's carbon, so its stiffness is swept from "
        f"{MODULUS_GPA[0]:g} to {MODULUS_GPA[1]:g} GPa and the arm's free length 10% either "
        "way.*",
        "",
        "## The verdict",
        "",
        f"**{verdict(run)}.** The arms are strong enough by a wide margin. One of their "
        "bending modes sits near what the props shake them at in a hover, and the chute's "
        "mount rests on joints whose strength is a guess. Both go to the test plans.",
        "",
        "## The arms under full thrust",
        "",
        f"Each arm is a {arm.width_m * 1000:g} by {arm.thickness_m * 1000:g} mm carbon "
        f"cantilever, {arm.length_m * 1000:.0f} mm from where it leaves the plates to the "
        f"motor, carrying {arm.tip_mass_kg * 1000:.0f} g of motor and prop. At the top of the "
        f"thrust table, {run['top_n']:.1f} N a motor (more than my firmware's 90 A current cap "
        "lets it make):",
        "",
        "| | Found | Against |",
        "|---|---|---|",
        f"| Bending stress at the root | {run['stress_pa'] / 1e6:.0f} MPa | at least "
        f"{STRENGTH_MPA:g} MPa: {margin:.1f} times |",
        f"| The tip's sag | {min(run['sag_m']) * 1000:.1f} to {max(run['sag_m']) * 1000:.1f} mm "
        "| a degree or two of the motor's tilt |",
        "",
        "## The arms' vibration",
        "",
        "A spinning prop shakes its arm once a turn (any imbalance in the prop or the motor) "
        f"and once a blade ({run['blades']} a turn). The arm's first two bending modes, across "
        "the laminate's and the clamp's ranges:",
        "",
        "| Mode | Frequency | The motor speed that shakes it once a turn |",
        "|---|---|---|",
    ]
    for m in run["modes"]:
        lo, hi = m.hz
        lines.append(f"| {m.name} | {lo:.0f} to {hi:.0f} Hz | {beams.crossing_rad_s(lo):.0f} to "
                     f"{beams.crossing_rad_s(hi):.0f} rad/s |")  # fmt: skip
    hov = run["hovers"]
    lines += ["", f"The hover's motor speed runs {min(hov.values()):.0f} to "
              f"{max(hov.values()):.0f} rad/s across the combinations, "
              f"{min(hov.values()) / (2 * math.pi):.0f} to {max(hov.values()) / (2 * math.pi):.0f} "
              "turns a second. Excitations within 15% of a mode at the hover:", ""]  # fmt: skip
    if run["near"]:
        lines += ["| Mode | Combination | Excitation | At |", "|---|---|---|---|"]
        for name, setup, per, hz in run["near"]:
            what = "once a turn" if per == 1 else f"{per} a turn (the blades)"
            lines.append(f"| {name} | {setup} | {what} | {hz:.0f} Hz |")
        lines += ["", "The in-plane mode is the one that matters: an unbalanced prop at a "
                  "hover shakes the arm sideways close to where it rings, so the gyro sees "
                  "it. The vertical mode only gets passed through on the way up and down. "
                  "The fix, if a gyro log shows it, is balancing the props first, then the "
                  "flight controller's notch filter on that frequency; stiffer arms would "
                  "move the mode up and away.", ""]  # fmt: skip
    else:
        lines += ["None.", ""]
    lines += [
        "![The arms' modes against the props' speeds](stills/campbell-wide.png)",
        "",
        "## The chute's mount",
        "",
        f"Step 6's textbook bound on the canopy's opening jolt: {run['bound_n']:.0f} N, the "
        "most of any combination. Each joint between the riser and the frame, with only half "
        "of its fasteners carrying it (prying and uneven fits):",
        "",
        "| Joint | What one holds | Margin over the bound | Note |",
        "|---|---|---|---|",
    ]
    for j in run["joints"]:
        lo, hi = j.margin(run["bound_n"])
        lines.append(f"| {j.name} | {j.each_n[0]:.0f} to {j.each_n[1]:.0f} N | {lo:.1f} to "
                     f"{hi:.1f} | {j.note} |")  # fmt: skip
    lines += [
        "",
        "The screws into the Harrier are far stronger than they need to be. The rail locks' "
        "heat-set inserts are the weak link, on numbers that are guesses, and the rail's four "
        "nylon screws are thin margin for something that carries the chute. Two changes "
        "suggest themselves: steel for those four (about 3 g more), and a hang test before P "
        "ever flies, which the test plans carry.",
        "",
        "## A hard landing",
        "",
        f"Dropped {DROP_M:g} m (the motors cut at 1 m), the heaviest combination, "
        f"{run['mass_kg']:.2f} kg, lands with {run['drop_j']:.0f} J for the TPU legs to "
        "take. The firmware's own landings touch down at 0.7 to 0.8 m/s, under 1 J. Without "
        "an FE model the legs' strength is a test, not a number.",
        "",
        "## What it can't prove",
        "",
    ]
    lines += unproven.bullets(UNPROVEN)
    lines += [""]
    return "\n".join(lines)


def to_data(run: dict, generated: str) -> dict:
    return {
        "generated": generated,
        "verdict": verdict(run),
        "arm": {"length_m": run["arm"].length_m, "tip_mass_kg": run["arm"].tip_mass_kg},
        "top_thrust_n": run["top_n"],
        "root_stress_mpa": run["stress_pa"] / 1e6,
        "modes": [{"name": m.name, "low_hz": m.hz[0], "high_hz": m.hz[1]} for m in run["modes"]],
        "near": [{"mode": n, "setup": s, "per_turn": p, "hz": h} for n, s, p, h in run["near"]],
        "joints": [{"name": j.name, "margin_low": j.margin(run["bound_n"])[0],
                    "margin_high": j.margin(run["bound_n"])[1]} for j in run["joints"]],
        "unproven": unproven.data(UNPROVEN),
    }  # fmt: skip


def campbell_still(run: dict, path: Path, size: str = "wide") -> Path:
    """The arm's modes as bands against the motors' speed, with the excitations as lines and
    the hovers marked."""
    import numpy as np

    from pcs14.report import charts

    canvas = charts.Canvas("What shakes the arms", "The arm's bending modes against what the "
                           "props shake it at, from idle to full speed", made_up=False,
                           size=size)  # fmt: skip
    (ax,) = canvas.axes
    top = run["top_rad_s"]
    speeds = np.linspace(0, top, 200)
    for m, shade in zip(run["modes"], ("muted", "accent"), strict=True):
        ax.axhspan(*m.hz, color=charts._c(shade), alpha=0.25, lw=0)
        ax.text(top * 0.99, m.hz[1], f"  the arm, {m.name}", ha="right", va="bottom",
                color=charts._c(shade), fontsize=12)  # fmt: skip
    for per, style in ((1, "-"), (run["blades"], "--")):
        ax.plot(speeds, speeds * per / (2 * np.pi), color=charts._c("text"), lw=1.6, ls=style,
                label="once a turn" if per == 1 else f"{per} a turn (the blades)")  # fmt: skip
    lo, hi = min(run["hovers"].values()), max(run["hovers"].values())
    ax.axvspan(lo, hi, color=charts._c("pop"), alpha=0.18, lw=0)
    ax.text((lo + hi) / 2, 5, "hover", ha="center", color=charts._c("pop"), fontsize=12)
    ax.set_xlim(0, top)
    ax.set_ylim(0, max(m.hz[1] for m in run["modes"]) * 1.6)
    ax.legend(frameon=False, labelcolor=charts._c("text"), fontsize=12, loc="upper left")
    charts._label(ax, "the motors' speed (rad/s)", "Hz")
    mode = run["modes"][1]
    canvas.headline(f"{mode.hz[0]:.0f} to {mode.hz[1]:.0f} Hz",
                    "where the arms ring sideways, and an unbalanced prop at a hover shakes "
                    f"them at {lo / (2 * np.pi):.0f} to {hi / (2 * np.pi):.0f} Hz. Balance the "
                    "props, and check a gyro log.")  # fmt: skip
    canvas.save(path)
    return path


def write(build, docs, exports, out, generated: str) -> list[Path]:
    out = Path(out)
    (out / "stills").mkdir(parents=True, exist_ok=True)
    run = collect(build, docs, exports)
    drawn = [campbell_still(run, out / "stills" / "campbell-wide.png"),
             campbell_still(run, out / "stills" / "campbell-portrait.png", "portrait")]  # fmt: skip
    (out / "README.md").write_bytes(render(run, generated).encode("utf-8"))
    (out / "structure.json").write_bytes(
        (json.dumps(to_data(run, generated), indent=1) + "\n").encode("utf-8")
    )
    return [out / "README.md", out / "structure.json", *drawn]
