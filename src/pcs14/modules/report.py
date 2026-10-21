"""Step 6's report, the modules in sim: what each module's scenarios found on my firmware, the
parachute's opening jolt and how its timing moves the height it needs, HaLow's range, and the
companion computer. Written to docs/reports/modules/ by `pcs14 modules`, like every other step.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pcs14 import unproven
from pcs14.flight import grade
from pcs14.flight.batch import load_results
from pcs14.flight.drag import Chute
from pcs14.modules import chute as chute_math
from pcs14.modules import companion, halow, video
from pcs14.unproven import Unproven

HUNG = "hung flight controller"
RULE = "chute rule"
RANGE = "halow range"
CAMERA = "camera"
OWN_TRIGGER = "monitor's own trigger"
DROP_PREFIX = "drop from "
OPENING_TIMES_S = (0.5, 1.0, 1.5, 2.0, 3.0)
HALOW_HEIGHTS_M = (10.0, 30.0, 120.0)
HALOW_DISTANCES_M = (100, 500, 1000, 2000, 3000, 5000, 8000)
SETUP_ORDER = ("base", "V", "P", "C", "mission", "V+C", "P+C", "max")

UNPROVEN = (
    Unproven(
        what=(
            "The canopy's timing. Fruity Chutes publishes no ejection or opening time, so the 0.2"
            " s and 1.0 s the sim uses are my guesses, and the lowest height the chute saves the "
            "drone from rests on them (the table under the drop heights)."
        ),
        measure=(
            "Fruity Chutes' own numbers, asked for; then a drop of the canopy with a dummy "
            "weight, filmed, to time its opening."
        ),
    ),
    Unproven(
        what=(
            "The opening jolt. The sim's canopy grows in a straight line and never overshoots, "
            "which real canopies do as they fill, so its number is low. The bound uses Knacke's "
            "infinite-mass opening coefficient, which is high for a drone this light under a "
            "canopy this big. The real number is between them."
        ),
        measure=("A load cell inline on the riser, in the same drop."),
    ),
    Unproven(
        what=(
            "A hung flight controller here is a frozen process. A real one could hang with its "
            "DShot outputs in any state, which the safety monitor's takeover of the lines has to "
            "win against; that's tested on the host, not on a board."
        ),
        measure=(
            "On the bench, props off: the ARK FPV halted in a debugger, and the safety monitor "
            "taking the ESC lines and stopping the motors."
        ),
    ),
    Unproven(
        what=(
            "HaLow's range: line of sight over flat ground, with a 10 dB margin standing in for "
            "the drone's body, multipath and a laptop held low. No trees, hills or buildings. And"
            " the radio's numbers are Morse Micro's for its own module, not Heltec's for its "
            "card."
        ),
        measure=(
            "A walk-out range test with the drone on a 10 m mast, logging the link's rate against"
            " the distance."
        ),
    ),
    Unproven(
        what=(
            "The companion computer's comparison is from published numbers, not measured on a "
            "board."
        ),
        measure=(
            "The Pi 5 running the video encode and the flow estimate, its CPU load and "
            "temperature logged."
        ),
    ),
)


@dataclass(frozen=True)
class Run:
    scenario: str
    setup: str
    flown: bool
    findings: tuple
    notes: dict
    marks: tuple

    @property
    def passed(self) -> bool:
        return self.flown and all(f.passed for f in self.findings)

    def finding(self, check: str):
        return next((f for f in self.findings if f.check == check), None)


@dataclass(frozen=True)
class Jolt:
    setup: str
    mass_kg: float
    speed_ms: float  # falling, as the canopy started to fill
    sim_n: float  # the sim's peak pull
    bound_n: float  # the textbook bound at that speed

    @property
    def sim_g(self) -> float:
        return self.sim_n / (self.mass_kg * 9.80665)

    @property
    def bound_g(self) -> float:
        return self.bound_n / (self.mass_kg * 9.80665)


@dataclass(frozen=True)
class ModulesRun:
    runs: tuple[Run, ...]
    jolts: tuple[Jolt, ...]
    opening: tuple  # (opening_s, chute_math.Drop) for Max under the Harrier
    max_mass_kg: float
    canopy_area_m2: float
    healthy_runs: int = 0  # my firmware's, where nothing fails on purpose
    video: bool = False  # the camera's frames got encoded for the side-by-side still
    false_triggers: tuple = ()  # (scenario, setup, detail) where the triggers fired anyway


def _model(exports: Path, setup: str) -> dict:
    path = exports / "models" / f"pcs14_{setup.lower().replace('+', '_')}" / "model.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _is_step6(name: str) -> bool:
    return name in (HUNG, RULE, RANGE, CAMERA) or name.startswith(DROP_PREFIX)


def collect(exports) -> ModulesRun:
    exports = Path(exports)
    runs = []
    for path in sorted((exports / "results").glob("*-mine.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data["scenario"].removesuffix(" (mine)")
        if not _is_step6(name):
            continue
        run = data.get("run") or {}
        runs.append(Run(name, data["setup"], data["flown"],
                        tuple(grade.Finding(**f) for f in data["findings"]),
                        run.get("notes", {}),
                        tuple(tuple(m) for m in run.get("marks", []))))  # fmt: skip
    runs.sort(
        key=lambda r: (r.scenario, SETUP_ORDER.index(r.setup) if r.setup in SETUP_ORDER else 9)
    )
    jolts = tuple(
        j for r in runs if r.scenario == HUNG and (j := _jolt(r, _model(exports, r.setup)))
    )
    heaviest = _model(exports, "max")
    mass = heaviest.get("mass_kg", 2.37)
    area = heaviest.get("chute", {}).get("canopy_area_m2", 1.93)
    ejection = heaviest.get("chute", {}).get("ejection_s", 0.2)
    opening = tuple((s, chute_math.drop(Chute(area, ejection, s), mass)) for s in OPENING_TIMES_S)
    healthy, fired = 0, []
    for r in load_results(exports, firmware="mine"):
        for f in r.findings:
            if f.check == "false triggers":
                healthy += 1
                if f.value:
                    fired.append((r.scenario, r.setup, f.detail))
    return ModulesRun(tuple(runs), jolts, opening, mass, area, healthy, tuple(fired))


def _jolt(run: Run, model: dict) -> Jolt | None:
    truth = run.notes.get("truth") or []
    fired = next((t for t, name in run.marks if name == "chute fired"), None)
    if len(truth) < 10 or fired is None or "chute" not in model:
        return None
    c = model["chute"]
    t = np.array([p[0] for p in truth])
    z = np.array([p[1] for p in truth])
    vz = np.gradient(z, t)
    start = fired + c["ejection_s"]
    pull = chute_math.peak_pull(t, vz, model["mass_kg"], since=start,
                                until=start + c["opening_s"] + 1.0)  # fmt: skip
    speed = float(-np.interp(start, t, vz))
    bound = chute_math.opening_force_bound(speed, c["canopy_area_m2"])
    return Jolt(run.setup, model["mass_kg"], speed, pull.force_n, bound)


def verdict(run: ModulesRun) -> str:
    if not run.runs:
        return "not run"
    return "pass" if all(r.passed for r in run.runs) else "fail"


def _cell(f) -> str:
    return f.detail if f is not None else ""


def render(run: ModulesRun, generated: str) -> str:
    lines = [
        "# Modules in sim (step 6)",
        "",
        f"*Generated {generated} by `pcs14 modules`, from the flight sim's runs of step 6's "
        "scenarios on my firmware. The spec is [docs/specs/2026-10-20-modules-in-sim.md]"
        "(../../specs/2026-10-20-modules-in-sim.md).*",
        "",
        "## The verdict",
        "",
        f"**{verdict(run)}.** {sum(r.passed for r in run.runs)} of {len(run.runs)} runs pass.",
        "",
    ]
    lines += _parachute(run)
    lines += _vision(run)
    lines += [
        "## C: the claws",
        "",
        "The claws are still a placeholder: the roadmap holds C until a unique claw on an actual "
        "arm comes up, and that's my conversation to have. The payload grab (step 4) keeps "
        "flying in every C combination, and passes on both firmwares.",
        "",
        "## What it can't prove",
        "",
    ]
    lines += unproven.bullets(UNPROVEN)
    lines += [""]
    return "\n".join(lines)


def _parachute(run: ModulesRun) -> list[str]:
    out = ["## P: the parachute", ""]
    out += [
        "The safety monitor can fire the chute now, as the flight controller can: on the "
        "pilot's chute switch, only with P fitted, and always cutting the motors first. Its "
        "automatic triggers stay in shadow mode, logging only. Its host tests cover the order, "
        "nothing on the ground, nothing without P, the release latching like the cut, and the "
        "chute still going with the flight controller hung.",
        "",
        "### A hung flight controller",
        "",
        "40 m up, my firmware's process frozen the way a hung processor would be. The monitor "
        "sees its heartbeat stop and cuts the motors; a second after the hang the pilot flips "
        "the chute switch, which reaches the chute through the monitor.",
        "",
        "| Combination | The cut | The order | Under the canopy | The monitor's own trigger |",
        "|---|---|---|---|---|",
    ]
    for r in (r for r in run.runs if r.scenario == HUNG):
        out.append(f"| {r.setup} | {_cell(r.finding('monitor cut'))} | "
                   f"{_cell(r.finding('chute order'))} | "
                   f"{_cell(r.finding('settled under the canopy'))} | "
                   f"{_cell(r.finding(OWN_TRIGGER))} |")  # fmt: skip
    drops = [r for r in run.runs if r.scenario.startswith(DROP_PREFIX)]
    if drops:
        out += ["", "### How low the chute saves it", "",
                "Flight termination in Max, the heaviest, from each height (40 m is step 4's "
                "parachute drop).", "", "| From | The order | Under the canopy |",
                "|---|---|---|"]  # fmt: skip
        for r in sorted(drops, key=lambda r: float(r.scenario.split()[2])):
            out.append(f"| {r.scenario.removeprefix(DROP_PREFIX)} | "
                       f"{_cell(r.finding('chute order'))} | "
                       f"{_cell(r.finding('settled under the canopy'))} |")  # fmt: skip
    out += ["", "The height it takes rests on how fast the canopy fills, which Fruity Chutes "
            "doesn't publish. The same canopy in one dimension (the sim's model, the drone's "
            f"own drag left out), Max at {run.max_mass_kg:.2f} kg, falling from still air:", "",
            "| Opening time | Height lost | Falling as it opens |", "|---|---|---|"]  # fmt: skip
    for s, d in run.opening:
        out.append(f"| {s:g} s | {d.height_lost_m:.1f} m | {d.speed_at_open_ms:.1f} m/s |")
    out += ["", "The sim uses 1.0 s. The \"about 10 m to open\" in decisions.md is a canopy "
            "that takes nearly 2 s.", "", "![How low the chute saves it](stills/opening-wide.png)",
            ""]  # fmt: skip
    if run.jolts:
        out += ["### The opening jolt", "",
                "The canopy's peak pull on the drone, for the structure track: the sim's, from "
                "Gazebo's ground truth during the opening, and the textbook bound at the speed "
                "the drone fell as the canopy began to fill (Cx q CdS, Cx 1.7, Knacke). The "
                "structure track designs to the bound.", "",
                "| Combination | Falling at | The sim's peak | The bound |",
                "|---|---|---|---|"]  # fmt: skip
        for j in run.jolts:
            out.append(f"| {j.setup} | {j.speed_ms:.1f} m/s | {j.sim_n:.0f} N ({j.sim_g:.1f} g) | "
                       f"{j.bound_n:.0f} N ({j.bound_g:.1f} g) |")  # fmt: skip
        out += [""]
    out += ["### The false-trigger replay on my firmware", ""]
    if run.false_triggers:
        out += [f"The safety monitor's triggers fired in {len(run.false_triggers)} of the "
                f"{run.healthy_runs} healthy runs:", ""]  # fmt: skip
        out += [f"- {s} in {c}: {d}" for s, c, d in run.false_triggers]
    else:
        out += [f"The safety monitor's reference triggers, replayed over the {run.healthy_runs} "
                "healthy runs my firmware flew, where nothing fails on purpose: none fired. "
                "They stay in shadow mode anyway, until real flights show the same."]  # fmt: skip
    out += ["", "Under the canopy the monitor's own tumble-tilt trigger fires too, logged only: "
            "the drone hangs at an angle from the chute's mount. By then the motors are already "
            "cut, so it changes nothing, but it's one more reason the triggers stay in shadow "
            "mode until real flights show what they see.", ""]  # fmt: skip
    rule = [r for r in run.runs if r.scenario == RULE]
    if rule:
        out += ["### The parachute rule", "",
                "Without P, my firmware won't go above 30 m. A take-off asked for 40 m:", "",
                "| Combination | Found |", "|---|---|"]  # fmt: skip
        out += [f"| {r.setup} | {_cell(r.finding('chute rule ceiling'))} |" for r in rule]
        out += [""]
    return out


def _vision(run: ModulesRun) -> list[str]:
    link = halow.Link()
    out = ["## V: vision and nav", "", "### HaLow's range", "",
           "The rate the link holds, by distance and the drone's height, over flat ground with "
           "the laptop's antenna 1.5 m up and a 10 dB fade margin (pcs14.modules.halow, from "
           "Morse Micro's numbers for the MM6108):", "",
           "| Distance | " + " | ".join(f"{h:g} m up" for h in HALOW_HEIGHTS_M) + " |",
           "|---|" + "---|" * len(HALOW_HEIGHTS_M)]  # fmt: skip
    for d in HALOW_DISTANCES_M:
        cells = [f"{link.rate_mbps(d, h):.2f} Mbps" if link.rate_mbps(d, h) else "none"
                 for h in HALOW_HEIGHTS_M]  # fmt: skip
        out.append(f"| {d / 1000:g} km | " + " | ".join(cells) + " |")
    out += ["", "![HaLow's range](stills/halow-wide.png)"]
    flown = [r for r in run.runs if r.scenario == RANGE]
    if flown:
        out += ["", "In the sim, the ground station's link went through the model at the drone's "
                "distance while it flew 7 km out at 10 m and back. Its pilot's link and its "
                "companion computer's aren't HaLow, so it should fly on regardless:", "",
                "| Combination | Where the link faded | The flight |", "|---|---|---|"]  # fmt: skip
        for r in flown:
            out.append(f"| {r.setup} | {_cell(r.finding('link fades where the model says'))} | "
                       f"{_cell(r.finding('no fly-away'))} |")  # fmt: skip
    out += ["", "### The live video", "",
            "What's left of the link for video at each distance, 30 m up: about 60% of the "
            "rate on the air carries data, less 0.1 Mbps of telemetry, encoded as H.264 in "
            "software the way the Pi 5 would (pcs14.modules.video). Full-resolution stills for "
            "mapping go when the link allows.", "",
            "| Distance | On the air | For video | Carries |", "|---|---|---|---|"]  # fmt: skip
    for row in video.at_distances(HALOW_DISTANCES_M, 30.0):
        out.append(f"| {row.distance_m / 1000:g} km | {row.phy_mbps:.2f} Mbps | "
                   f"{row.kbps:.0f} kbps | {row.carries} |")  # fmt: skip
    shot = [r for r in run.runs if r.scenario == CAMERA]
    if shot:
        out += ["", "### The camera", "",
                "V's camera (the Camera Module 3, 720p at 30 frames a second) on the model, "
                "flown 20 m up over a shed, some trees and a box, every third frame saved:", "",
                "| Combination | Frames | Rate | The flight |", "|---|---|---|---|"]  # fmt: skip
        for r in shot:
            cells = [_cell(r.finding(k)) for k in ("camera frames", "camera rate", "no fly-away")]
            out.append(f"| {r.setup} | " + " | ".join(cells) + " |")
    if run.video:
        out += ["", "The camera scenario's own frames (V's Camera Module 3 in Gazebo, 20 m up "
                "over a shed, some trees and a box), encoded at those budgets. The frames were "
                "saved at 10 a second, so each clip gives every frame the bits it would get at "
                "30. The clips stay out of the repo, like every video. The three look alike, "
                "and that's the sim flattering the link: Gazebo's world here is flat colors "
                "with no texture, which compresses to almost nothing. Real video, with grass "
                "and leaves moving, would need far more bits for the same picture, so the "
                "table's resolutions are the honest part, not the still.", "",
                "![What the laptop sees](stills/video-wide.png)"]  # fmt: skip
    out += ["",
            "### The companion computer", "", companion.verdict().why, "",
            "| Board | What | Found | Source |", "|---|---|---|---|"]  # fmt: skip
    for b in companion.BOARDS:
        out += [f"| {b.name} | {f.what} | {f.value} | [link]({f.source}) |" for f in b.facts]
    out += [""]
    return out


def to_data(run: ModulesRun, generated: str) -> dict:
    return {
        "generated": generated,
        "verdict": verdict(run),
        "runs": [{"scenario": r.scenario, "setup": r.setup, "passed": r.passed,
                  "findings": [f.__dict__ for f in r.findings]} for r in run.runs],
        "jolts": [{"setup": j.setup, "speed_ms": j.speed_ms, "sim_n": j.sim_n, "sim_g": j.sim_g,
                   "bound_n": j.bound_n, "bound_g": j.bound_g} for j in run.jolts],
        "opening": [{"opening_s": s, "height_lost_m": d.height_lost_m,
                     "speed_at_open_ms": d.speed_at_open_ms} for s, d in run.opening],
        "halow": {f"{h:g}": {f"{d}": halow.Link().rate_mbps(d, h) for d in HALOW_DISTANCES_M}
                  for h in HALOW_HEIGHTS_M},
        "companion": companion.verdict().pick,
        "healthy_runs": run.healthy_runs,
        "false_triggers": [list(x) for x in run.false_triggers],
        "unproven": unproven.data(UNPROVEN),
    }  # fmt: skip


STILL_SIZES = ("wide", "portrait")


def opening_still(run: ModulesRun, path: Path, size: str = "wide") -> Path:
    """The height the chute needs against how fast the canopy fills."""
    from pcs14.report import charts

    canvas = charts.Canvas("How low the chute saves it",
                           f"Max, {run.max_mass_kg:.2f} kg, dropped from a hover under the Harrier",
                           made_up=False, size=size)  # fmt: skip
    (ax,) = canvas.axes
    xs = [s for s, _ in run.opening]
    ys = [d.height_lost_m for _, d in run.opening]
    ax.plot(xs, ys, color=charts._c("accent"), linewidth=2.4, marker="o")
    sim = next((d.height_lost_m for s, d in run.opening if s == 1.0), None)
    if sim is not None:
        ax.axvline(1.0, color=charts._c("muted"), linewidth=1.0, zorder=0)
    ax.set_ylim(0, max(ys) * 1.1)
    charts._label(ax, "seconds for the canopy to fill", "height lost (m)")
    canvas.headline(f"{sim:.0f} m" if sim is not None else "",
                    "lost at the 1 s the sim assumes. Fruity Chutes doesn't publish the real "
                    "time, and every extra second costs about 6 m more.")  # fmt: skip
    canvas.save(path)
    return path


def halow_still(path: Path, size: str = "wide") -> Path:
    """HaLow's rate against distance, at three heights."""
    from pcs14.report import charts

    link = halow.Link()
    subtitle = (
        "The rate the link holds over flat ground, with a 10 dB margin, by the drone's height"
    )
    canvas = charts.Canvas("HaLow's range", subtitle, made_up=False, size=size)
    (ax,) = canvas.axes
    distances = np.linspace(50, 10000, 400)
    shades = ("muted", "text", "accent")
    for h, shade in zip(HALOW_HEIGHTS_M, shades, strict=True):
        ax.plot(distances / 1000, [link.rate_mbps(d, h) for d in distances],
                color=charts._c(shade), linewidth=2.2, label=f"{h:g} m up")  # fmt: skip
    ax.legend(frameon=False, labelcolor=charts._c("text"), fontsize=13)
    charts._label(ax, "km from the laptop", "Mbps")
    reach = link.reach_m(0, 30.0)
    canvas.headline(f"{reach / 1000:.1f} km", "where the slowest rate gives out, 30 m up. "
                    "Trees, hills and buildings aren't in it.")  # fmt: skip
    canvas.save(path)
    return path


def video_still(frames: Path, clips: Path, path: Path, at_s: float = 44.0,
                size: str = "wide") -> Path | None:  # fmt: skip
    """The camera scenario's frames encoded at what HaLow holds at 1, 3 and 5 km, and the same
    moment from each, side by side. The clips go to `clips` (not the repo: no videos there)."""
    import bisect
    import subprocess

    from PIL import Image

    from pcs14.report import charts

    listed = frames / "frames.txt"
    if video.ffmpeg() is None or not listed.is_file():
        return None
    times = [float(x) for x in listed.read_text(encoding="utf-8").split()]
    # the clip's own time of the moment at `at_s` s of the sim's clock: frames at 10 a second
    offset = min(bisect.bisect_left(times, at_s), max(len(times) - 1, 0)) / video.SAVED_FPS
    clips.mkdir(parents=True, exist_ok=True)
    panels = []
    for c in video.comparison():
        name = f"halow-{c.distance_m / 1000:g}km"
        clip = video.encode(frames, clips / f"{name}.mp4", kbps=max(c.kbps_at_10, 50),
                            fps=video.SAVED_FPS, height=c.lines)  # fmt: skip
        grab = clips / f"{name}.png"
        subprocess.run([video.ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{offset:.2f}",
                        "-i", str(clip), "-frames:v", "1", str(grab)], check=True)  # fmt: skip
        panels.append((c, Image.open(grab).convert("RGB")))
    canvas = charts.Canvas("What the laptop sees", "The live video at the rate HaLow holds, "
                           "30 m up over flat ground", made_up=False, size=size)  # fmt: skip
    (ax,) = canvas.axes
    ax.set_axis_off()
    width = 640
    sheet = Image.new("RGB", (width * len(panels) + 20 * (len(panels) - 1), 360), (11, 11, 11))
    for k, (_, im) in enumerate(panels):
        sheet.paste(im.resize((width, 360), Image.Resampling.NEAREST), (k * (width + 20), 0))
    ax.imshow(sheet)
    fonts = charts._fonts()
    for k, (c, _) in enumerate(panels):
        ax.text((k + 0.5) * (width + 20), 395, f"{c.distance_m / 1000:g} km: {c.row.carries}, "
                f"{c.row.kbps:.0f} kbps", ha="center", va="top", fontsize=13,
                color=charts._c("text"), family=fonts["body"])  # fmt: skip
    canvas.headline(f"{panels[-1][0].row.kbps:.0f} kbps",
                    "at 5 km, and it holds up here because the sim's world is flat colors. "
                    "Real video, grass and leaves moving, needs far more bits for the same "
                    "picture.")  # fmt: skip
    canvas.save(path)
    return path


def write(exports, out, generated: str) -> list[Path]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    run = collect(exports)
    stills = out / "stills"
    stills.mkdir(exist_ok=True)
    drawn = []
    for size in STILL_SIZES:
        drawn.append(opening_still(run, stills / f"opening-{size}.png", size))
        drawn.append(halow_still(stills / f"halow-{size}.png", size))
    frames = Path(exports) / "camera" / "pcs14_v"
    clips = Path(exports).parent / "modules" / "video"
    seen = video_still(frames, clips, stills / "video-wide.png")
    if seen is not None:
        drawn.append(seen)
        from dataclasses import replace

        run = replace(run, video=True)
    (out / "README.md").write_bytes(render(run, generated).encode("utf-8"))
    (out / "modules.json").write_bytes(
        (json.dumps(to_data(run, generated), indent=1, default=float) + "\n").encode()
    )
    return [out / "README.md", out / "modules.json", *drawn]
