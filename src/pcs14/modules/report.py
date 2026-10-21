"""Step 6's report, the modules in sim: what each module's scenarios found on my firmware, the
parachute's opening jolt and how its timing moves the height it needs, HaLow's range, and the
companion computer. Written to docs/reports/modules/ by `pcs14 modules`, like every other step.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pcs14.flight import grade
from pcs14.flight.drag import Chute
from pcs14.modules import chute as chute_math
from pcs14.modules import companion, halow

HUNG = "hung flight controller"
RULE = "chute rule"
RANGE = "halow range"
OWN_TRIGGER = "monitor's own trigger"
DROP_PREFIX = "drop from "
OPENING_TIMES_S = (0.5, 1.0, 1.5, 2.0, 3.0)
HALOW_HEIGHTS_M = (10.0, 30.0, 120.0)
HALOW_DISTANCES_M = (100, 500, 1000, 2000, 3000, 5000, 8000)
SETUP_ORDER = ("base", "V", "P", "C", "mission", "V+C", "P+C", "max")

UNPROVEN = (
    "The canopy's timing. Fruity Chutes publishes no ejection or opening time, so the 0.2 s and "
    "1.0 s the sim uses are my guesses, and the lowest height the chute saves the drone from "
    "rests on them (the table under the drop heights).",
    "The opening jolt. The sim's canopy grows in a straight line and never overshoots, which "
    "real canopies do as they fill, so its number is low. The bound uses Knacke's infinite-mass "
    "opening coefficient, which is high for a drone this light under a canopy this big. The "
    "real number is between them.",
    "A hung flight controller here is a frozen process. A real one could hang with its DShot "
    "outputs in any state, which the safety monitor's takeover of the lines has to win against; "
    "that's tested on the host, not on a board.",
    "HaLow's range: line of sight over flat ground, with a 10 dB margin standing in for the "
    "drone's body, multipath and a laptop held low. No trees, hills or buildings. And the "
    "radio's numbers are Morse Micro's for its own module, not Heltec's for its card.",
    "The companion computer's comparison is from published numbers, not measured on a board.",
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


def _model(exports: Path, setup: str) -> dict:
    path = exports / "models" / f"pcs14_{setup.lower().replace('+', '_')}" / "model.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _is_step6(name: str) -> bool:
    return name in (HUNG, RULE, RANGE) or name.startswith(DROP_PREFIX)


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
    return ModulesRun(tuple(runs), jolts, opening, mass, area)


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
    lines += [f"- {u}" for u in UNPROVEN]
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
    out += ["", "### The camera and the video", "",
            "Live video at the rate HaLow holds: about 2 Mbps carries 720p at 30 frames a "
            "second, so the live view holds to the distance where the table drops under that, "
            "and full-resolution stills go when the link allows.", "",
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
        "unproven": list(UNPROVEN),
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
    (out / "README.md").write_bytes(render(run, generated).encode("utf-8"))
    (out / "modules.json").write_bytes(
        (json.dumps(to_data(run, generated), indent=1, default=float) + "\n").encode()
    )
    return [out / "README.md", out / "modules.json", *drawn]
