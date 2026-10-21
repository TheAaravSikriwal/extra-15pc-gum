"""The flight sim's report and data file: docs/reports/flight-sim/README.md and flight-sim.json.

The run holds plain results, so the report can be written (and tested) without PX4 or Gazebo.
Until the scenarios have flown, it shows each one as not flown yet, next to the generated
models' numbers and every estimate they rest on.
"""

from dataclasses import dataclass

from pcs14 import __version__

# every scenario, in the order the report lists them
SCENARIOS = (
    "hover",
    "steps",
    "top speed",
    "wind",
    "endurance",
    "lost link",
    "low battery",
    "parachute drop",
    "dead motor",
    "failed sensor",
    "sagging pack",
    "payload grab",
)
UNPROVEN = (
    "The parachute's descent rate. Its drag comes from Fruity Chutes' own rating, so the sim "
    "only repeats it; the drop checks the order of events and the height lost.",
    "The payload grab. Gazebo's attach joint stands in for the claws, which are a placeholder "
    "anyway.",
    "My firmware's current cap and the XT60's heat limit. This is PX4, which has neither, so "
    "the motors are held at their worst-case top speed instead.",
    "The props' in-plane drag, their rolling moment and the motors' spin-up times, which are "
    "PX4's x500 values.",
    "Body drag beyond a frontal-area estimate, until the wind tunnel side track has real tables.",
    "Vibration, and anything else a real IMU sees that clean Gaussian noise doesn't.",
)


# why a miss misses, for the misses that have been looked into: (scenario, check) to the reason
EXPLAINED = {
    ("dead motor", "touchdown"): (
        "There's no chute without P, and a quad can't fly on three motors: PX4 drops the dead "
        "one from the mix and tries, but it tumbles and falls. Every combination without P "
        "loses the drone to a dead motor."
    ),
    ("failed sensor", "no fly-away"): (
        "Without GPS this drone has nothing to hold its position with: the TF-Luna only "
        "measures height, and there's no optical flow sensor. PX4 comes down blind, level by "
        "its own attitude estimate, and that estimate's small tilt error carries it off at up "
        "to a few m/s. In wind it would drift farther."
    ),
    ("endurance", "cruise endurance"): (
        "The sizing model says forward flight is cheaper than a hover, the way it is for a real "
        "prop moving through fresh air. Gazebo's rotors make the same thrust at any airspeed, so "
        "in the sim a cruise costs about what a hover does. The truth is somewhere between, and "
        "pinning it down takes the rotor's forward-flight data the aero side track will "
        "measure."
    ),
}


def applies(scenario: str, setup) -> bool:
    """Which scenarios a combination flies: top speed and wind where the targets set them, the
    drop with P, the grab with C, the rest everywhere."""
    if scenario == "top speed":
        return setup.min_top_speed is not None
    if scenario == "wind":
        return setup.hold_position_in_wind is not None
    if scenario == "parachute drop":
        return "P" in setup.modules
    if scenario == "payload grab":
        return "C" in setup.modules
    # step 6's: the hung flight controller where there's a chute, the drop heights in the
    # heaviest, the parachute rule where there's none
    if scenario == "hung flight controller":
        return "P" in setup.modules
    if scenario.startswith("drop from "):
        return setup.name == "max"
    if scenario == "chute rule":
        return "P" not in setup.modules
    if scenario in ("halow range", "camera", "turn back", "mapping run", "safe landing"):
        return "V" in setup.modules
    # step 7's: the landing modes are the firmware's, not a module's, so base flies them
    if scenario in ("land now", "back to start", "land here", "spiral descent", "lift"):
        return setup.name == "base"
    if scenario == "planned mission":
        return setup.name == "mission"
    return True


@dataclass(frozen=True)
class ModelSummary:
    setup: str
    mass_g: float
    hover_throttle: float
    top_rpm: float
    motor_constant: float
    moment_constant: float
    drag_area_cm2: float
    chute: bool
    payload_g: float


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    setup: str
    flown: bool
    findings: tuple = ()  # pcs14.flight.grade.Finding
    note: str = ""

    @property
    def passed(self) -> bool:
        return self.flown and all(f.passed for f in self.findings)


@dataclass(frozen=True)
class FlightSimRun:
    build_label: str
    px4: str
    gazebo: str
    combinations: tuple  # the setups, in order (pcs14.design.SetupTargets)
    models: tuple[ModelSummary, ...]
    results: tuple[ScenarioResult, ...]
    estimates: tuple[str, ...]
    files: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    mine: tuple[ScenarioResult, ...] = ()  # the same scenarios flown by my firmware (step 5)

    def result(self, scenario: str, setup: str) -> ScenarioResult | None:
        return next((r for r in self.results if r.scenario == scenario and r.setup == setup), None)

    def expected(self) -> list[tuple[str, str]]:
        return [(sc, s.name) for s in self.combinations for sc in SCENARIOS if applies(sc, s)]

    @property
    def verdict(self) -> str:
        found = [self.result(sc, s) for sc, s in self.expected()]
        if not any(r is not None and r.flown for r in found):
            return "not flown yet"
        if all(r is not None and r.passed for r in found):
            return "pass"
        return "fail"


def mine_view(run: FlightSimRun) -> FlightSimRun:
    """The run as my firmware flew it: its results in place of PX4's."""
    from dataclasses import replace

    return replace(run, results=run.mine, mine=())


def closing(run: FlightSimRun) -> dict:
    """The sim against the other layers: flight times against the sizing model's, the safety
    monitor's false triggers in the healthy runs, and how soon it would catch the real
    failures."""
    flight_time = []
    for setup in run.combinations:
        r = run.result("endurance", setup.name)
        if r is None or not r.flown:
            continue
        row = {"setup": setup.name}
        for f in r.findings:
            if f.extra and f.check in ("hover endurance", "cruise endurance"):
                kind = f.check.split()[0]
                row[f"{kind}_sim_min"] = f.extra["sim_min"]
                row[f"{kind}_sizing_min"] = f.extra["sizing_min"]
        flight_time.append(row)
    false, healthy = [], 0
    caught = []
    for r in run.results:
        for f in r.findings:
            if f.check == "false triggers":
                healthy += 1
                if f.value:
                    false.append({"scenario": r.scenario, "setup": r.setup, "detail": f.detail})
            elif f.check == "safety monitor":
                caught.append({"scenario": r.scenario, "setup": r.setup, "delay_s": f.value,
                               "detail": f.detail})  # fmt: skip
    return {"flight_time": flight_time, "healthy_runs": healthy, "false_triggers": false,
            "caught": caught}  # fmt: skip


def _minutes(value) -> str:
    return f"{value:.1f} min" if value is not None else ""


def _closing_lines(run: FlightSimRun) -> list[str]:
    found = closing(run)
    if not (found["flight_time"] or found["healthy_runs"] or found["caught"]):
        return []
    lines = ["## Closing the loop", ""]
    if found["flight_time"]:
        lines += [
            "Flight times from the sim's logged rotors, through my battery model, against the "
            "sizing model's at the same weight (no growth margin, no payload).",
            "",
            "| Setup | Hover, sim | Hover, sizing model | Cruise, sim | Cruise, sizing model |",
            "|---|---|---|---|---|",
        ]
        keys = ("hover_sim_min", "hover_sizing_min", "cruise_sim_min", "cruise_sizing_min")
        for row in found["flight_time"]:
            cells = [_minutes(row.get(k)) for k in keys]
            lines.append(f"| {row['setup']} | " + " | ".join(cells) + " |")
        lines.append("")
    if found["healthy_runs"]:
        count = len(found["false_triggers"])
        lines.append(
            f"The safety monitor's triggers, replayed over the {found['healthy_runs']} runs where "
            "nothing fails on purpose: "
            + ("no false triggers." if not count else f"{count} false triggers:")
        )
        lines += [
            f"- {f['scenario']} in {f['setup']}: {f['detail']}" for f in found["false_triggers"]
        ]
        lines.append("")
    if found["caught"]:
        lines += ["And where something really fails:", ""]
        lines += [f"- {c['scenario']} in {c['setup']}: {c['detail']}" for c in found["caught"]]
        lines.append("")
    return lines


def _misses_lines(run: FlightSimRun) -> list[str]:
    misses: dict[tuple, list[str]] = {}
    unexplained = []
    for r in run.results:
        if not r.flown:
            continue
        for f in r.findings:
            if f.passed:
                continue
            key = (r.scenario, f.check)
            if key in EXPLAINED:
                misses.setdefault(key, []).append(r.setup)
            else:
                unexplained.append(f"{f.check} in {r.setup}")
    if not misses and not unexplained:
        return []
    lines = ["## Why the misses miss", ""]
    for (scenario, check), setups in misses.items():
        lines += [
            f"**{scenario}, {check}** ({', '.join(setups)}). {EXPLAINED[scenario, check]}",
            "",
        ]
    for item in unexplained:
        lines.append(f"- {item}: not looked into yet")
    if unexplained:
        lines.append("")
    return lines


def _cell(run: FlightSimRun, scenario: str, setup) -> str:
    if not applies(scenario, setup):
        return ""
    r = run.result(scenario, setup.name)
    if r is None or not r.flown:
        return "not yet"
    return "pass" if r.passed else "**fail**"


def _mine_cell(run: FlightSimRun, scenario: str, setup) -> str:
    """My firmware's result, and PX4's where the two disagree."""
    words = _cell(mine_view(run), scenario, setup)
    if words in ("", "not yet"):
        return words
    mine = mine_view(run).result(scenario, setup.name)
    px4 = run.result(scenario, setup.name)
    if px4 is not None and px4.flown and px4.passed != mine.passed:
        words += " (PX4 passes)" if px4.passed else " (PX4 fails)"
    return words


def _mine_lines(run: FlightSimRun) -> list[str]:
    if not any(r.flown for r in run.mine):
        return []
    view = mine_view(run)
    expected = view.expected()
    flown = [r for r in (view.result(sc, s) for sc, s in expected) if r is not None and r.flown]
    failed = [r for r in flown if not r.passed]
    count = (
        ("and both pass" if len(flown) == 2 else "and they all pass")
        if not failed
        else f"and {len(failed)} miss"
    )
    lines = [
        "## My firmware, the same scenarios",
        "",
        "The same models and the same scripts, flown by my own flight firmware (step 5, in "
        "`firmware/`) instead of PX4, through its Gazebo bridge, with the safety monitor's "
        "firmware in the loop. Where it and PX4 disagree, the cell says so.",
        "",
        f"{len(flown)} of {len(expected)} runs flown, {count}.",
        "",
        "| Scenario | " + " | ".join(s.name for s in run.combinations) + " |",
        "|---|" + "---|" * len(run.combinations),
    ]
    for scenario in SCENARIOS:
        cells = [_mine_cell(run, scenario, s) for s in run.combinations]
        lines.append(f"| {scenario} | " + " | ".join(cells) + " |")
    lines.append("")
    if failed:
        lines += ["Where mine misses:", ""]
        for r in failed:
            px4 = run.result(r.scenario, r.setup)
            same = px4 is not None and px4.flown and not px4.passed
            misses = "; ".join(f"{f.check}: {f.detail}" for f in r.findings if not f.passed)
            lines.append(f"- {r.scenario} in {r.setup}: {misses}"
                         + (" (PX4 misses it too)" if same else ""))  # fmt: skip
        lines.append("")
    return lines


def render(run: FlightSimRun, generated: str | None = None) -> str:
    when = f" on {generated}" if generated else ""
    lines = [
        "# The flight sim",
        "",
        f"*Generated{when} by pcs14 {__version__}, the flight sim in `src/pcs14/flight/`. "
        f"PX4 {run.px4} flies a Gazebo {run.gazebo} model of this drone, generated from the "
        "build, the sizing model and the CAD, in every module combination.*",
        "",
        "## The verdict",
        "",
    ]
    expected = run.expected()
    flown = [r for r in (run.result(sc, s) for sc, s in expected) if r is not None and r.flown]
    failed = [r for r in flown if not r.passed]
    if run.verdict == "not flown yet":
        lines.append(
            f"**Not flown yet.** {len(expected)} scenario runs are planned across "
            f"{len(run.combinations)} combinations; the models are generated and waiting."
        )
    elif run.verdict == "pass":
        lines.append(f"**Pass.** All {len(expected)} scenario runs pass.")
    else:
        lines.append(
            f"**Fail.** {len(flown)} of {len(expected)} runs flown, and {len(failed)} miss: "
            + "; ".join(f"{r.scenario} in {r.setup}" for r in failed)
            + "."
        )
    lines += ["", f"Built from {run.build_label}.", "", "## Every scenario, every combination", ""]
    header = "| Scenario | " + " | ".join(s.name for s in run.combinations) + " |"
    lines += [header, "|---|" + "---|" * len(run.combinations)]
    for scenario in SCENARIOS:
        cells = [_cell(run, scenario, s) for s in run.combinations]
        lines.append(f"| {scenario} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "A blank cell is a scenario that combination doesn't fly: top speed and wind only where "
        "the targets set them, the parachute drop with P, the payload grab with C.",
        "",
    ]
    for r in run.results:
        if not r.flown or not r.findings:
            continue
        verdict = "pass" if r.passed else "fail"
        lines += [
            "<details>",
            f"<summary>{r.scenario}, {r.setup}: {verdict}</summary>",
            "",
            "| Check | Found | Verdict |",
            "|---|---|---|",
        ]
        lines += [
            f"| {f.check} | {f.detail} | {'pass' if f.passed else 'fail'} |" for f in r.findings
        ]
        lines += ["", "</details>", ""]
    lines += _misses_lines(run)
    lines += _closing_lines(run)
    lines += _mine_lines(run)
    lines += [
        "## The models",
        "",
        "Each combination's model, as generated. The weight is the CAD's, without the sizing "
        "model's growth margin; the top speed is where each motor makes the sizing model's "
        "full-throttle thrust, at the 20% reserve and the 90 A cap.",
        "",
        "| Setup | Weight | Hover throttle | Top speed | Thrust constant | Torque per thrust | "
        "Drag area | Chute | Payload |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in run.models:
        lines.append(
            f"| {m.setup} | {m.mass_g:.0f} g | {m.hover_throttle:.0%} | {m.top_rpm:.0f} rpm | "
            f"{m.motor_constant:.3g} N/(rad/s)² | {m.moment_constant * 1000:.1f} mm | "
            f"{m.drag_area_cm2:.0f} cm² | {'yes' if m.chute else ''} | "
            f"{f'{m.payload_g:.0f} g' if m.payload_g else ''} |"
        )
    lines += ["", "## What it rests on", ""]
    lines += [f"- {e}" for e in run.estimates] or ["Nothing."]
    lines += ["", "## What it can't prove", ""]
    lines += [f"- {u}" for u in UNPROVEN]
    lines += ["", "## Files", ""]
    if run.files:
        lines += ["Generated on every run, not committed (they're build outputs):", ""]
        lines += [f"- `{p}`" for p in run.files]
    else:
        lines.append("Nothing but this report and `flight-sim.json` on this run.")
    if run.skipped:
        lines += ["", "Skipped on this run:", ""] + [f"- {s}" for s in run.skipped]
    lines.append("")
    return "\n".join(lines)


def _result_data(r: ScenarioResult) -> dict:
    return {
        "scenario": r.scenario,
        "setup": r.setup,
        "flown": r.flown,
        "passed": r.passed,
        "note": r.note,
        "findings": [vars(f) for f in r.findings],
    }


def to_data(run: FlightSimRun, generated: str | None = None) -> dict:
    return {
        "generated": generated,
        "pcs14_version": __version__,
        "build": run.build_label,
        "px4": run.px4,
        "gazebo": run.gazebo,
        "verdict": run.verdict,
        "combinations": [s.name for s in run.combinations],
        "models": [vars(m) for m in run.models],
        "results": [_result_data(r) for r in run.results],
        "planned": [{"scenario": sc, "setup": s} for sc, s in run.expected()],
        "closing": closing(run),
        "mine": {
            "verdict": mine_view(run).verdict,
            "results": [_result_data(r) for r in run.mine],
            "closing": closing(mine_view(run)),
        },
        "estimates": list(run.estimates),
        "unproven": list(UNPROVEN),
        "files": list(run.files),
        "skipped": list(run.skipped),
    }


def summary_of(model) -> ModelSummary:
    """A generated pcs14.flight.generate.FlightModel, for the report."""
    import math

    return ModelSummary(
        setup=model.setup,
        mass_g=model.total_mass * 1000,
        hover_throttle=model.params.get("MPC_THR_HOVER", 0.0),
        top_rpm=model.motor.max_rot_velocity * 60 / (2 * math.pi),
        motor_constant=model.motor.motor_constant,
        moment_constant=model.motor.moment_constant,
        drag_area_cm2=model.drag_area * 1e4,
        chute=model.chute is not None,
        payload_g=model.payload * 1000,
    )


def estimates_for(models, build) -> tuple[str, ...]:
    """What the generated models rest on beyond the build's sourced numbers."""
    out = []
    if models:
        motor = models[0].motor
        out.append(
            f"The props' in-plane drag, their rolling moment and the motors' spin-up and "
            f"spin-down times: {motor.estimate_note}"
        )
    for part in build.modules.get("P", ()):
        chute = getattr(part, "parachute", None)
        if chute is not None and chute.estimates:
            out.append(f"{part.id}: {', '.join(chute.estimates)}. {chute.estimate_note}")
    drag = build.frame.drag_source
    if drag is not None and drag.kind.value == "estimate":
        out.append(f"The frame's drag area: {drag.note}")
    out.append(
        "The safety monitor's trigger thresholds are starting numbers, to be tuned against the "
        "false-trigger replays"
    )
    return tuple(out)


def write(out, run: FlightSimRun, generated: str | None = None):
    import json
    from pathlib import Path

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_bytes(render(run, generated).encode("utf-8"))
    data = json.dumps(to_data(run, generated), indent=1) + "\n"
    (out / "flight-sim.json").write_bytes(data.encode("utf-8"))
    return out


def summary(run: FlightSimRun) -> str:
    planned = len(run.expected())
    flown = sum(1 for r in run.results if r.flown)
    lines = [
        f"Flight sim: {len(run.models)} models, {planned} scenario runs planned, {flown} flown. "
        f"Verdict: {run.verdict}"
    ]
    for m in run.models:
        lines.append(
            f"  {m.setup:8s}{m.mass_g:6.0f} g, hovering at {m.hover_throttle:.0%}, top "
            f"{m.top_rpm:.0f} rpm"
        )
    lines += [f"Skipped: {s}" for s in run.skipped]
    return "\n".join(lines)
