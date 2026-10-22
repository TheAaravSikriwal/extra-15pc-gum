"""The flight sim's runs as playback files for the project site: each run's ground truth at up
to 20 Hz (the drone's path and attitude, the motors), its events and its findings, for both
firmwares, and an index of every run, with what each scenario tests. Every flown scenario from
steps 4 to 7 is there: step 4's matrix flown by PX4 and by my firmware (step 5), and steps 6
and 7's, flown by mine.

The logs aren't in the repo (*.ulg is gitignored), so these are made on the machine that flew
them, from outputs/flight-sim.
"""

import re
from collections.abc import Callable
from pathlib import Path

import numpy as np

from pcs14.flight.report import SCENARIOS
from pcs14.flight.scenarios import modules, smart
from pcs14.site import schema

RATE_HZ = 20.0
MAX_SAMPLES = 3000  # a 30 min low battery run comes down to about 1.7 Hz, a few hundred kB


# every scenario the site plays, in the order the steps flew them
ALL_SCENARIOS = (
    *SCENARIOS,
    *(c.name for c in modules.SCENARIOS),
    *(c.name for c in smart.SCENARIOS),
)

# what each one tests, in a line, for the site's scenario list
ABOUT = {
    "hover": (
        4,
        "Ten meters up, held for a minute. The baseline everything else is measured against.",
    ),
    "steps": (
        4,
        "Sudden roll and pitch stick inputs, each held 2 s, to see how quickly and cleanly it "
        "answers.",
    ),
    "top speed": (
        4,
        "Thirty meters up, flat out to the north for 30 s, until drag and the tilt limit stop it "
        "gaining.",
    ),
    "wind": (
        4,
        "A wind builds to the combination's target over 10 s and blows for 30, and it has to hold "
        "its spot.",
    ),
    "endurance": (
        4,
        "A minute of hover, then cruise legs out and back, to check the flight time against the "
        "sizing model.",
    ),
    "lost link": (
        4,
        "Twenty meters up and 50 out, the uplink cut. It waits 10 s, then flies home and lands on "
        "its own.",
    ),
    "low battery": (
        4,
        "Holding 50 m out while the pack drains until it's time to come home, landing above the "
        "reserve.",
    ),
    "parachute drop": (
        4,
        "Forty meters up, flight termination from the ground: the motors stop and the chute fires.",
    ),
    "dead motor": (
        4,
        "Forty meters up, one motor stops. With the chute it comes down under the canopy; without "
        "it, a quad can't fly on three.",
    ),
    "failed sensor": (
        4,
        "Twenty meters up and 30 out, the GPS goes away, and it has to come down without flying "
        "off.",
    ),
    "sagging pack": (
        4,
        "The pack sags the way a cold or worn one does, and it has to land where it is.",
    ),
    "payload grab": (
        4,
        "Picks a 250 g box off a shelf, carries it for 20 s, sets it down and lands at home.",
    ),
    "hung flight controller": (
        6,
        "Forty meters up, my flight controller frozen. The safety monitor cuts the motors and the "
        "chute brings it down.",
    ),
    "drop from": (
        6,
        "Flight termination in Max, the heaviest, to find how low the chute still saves it.",
    ),
    "chute rule": (
        6,
        "No chute on board, asked to climb to 40 m: my firmware's rule holds it at 30.",
    ),
    "camera": (6, "The camera on, 60 m out at 5 m/s past a shed, some trees and a box, and back."),
    "halow range": (
        6,
        "Seven kilometers out and back at 15 m/s while the HaLow link to the laptop fades, and it "
        "flies on.",
    ),
    "land now": (7, "Fifteen meters up and 30 out, then straight down where it is."),
    "back to start": (7, "Fifteen meters up and 30 out, then home first and down there."),
    "land here": (
        7,
        "Fifteen meters up and 30 out, then over to a point it's given and down there.",
    ),
    "turn back": (
        7,
        "Six hundred meters out with a 6 m/s wind behind it, then home into it, checking the "
        "energy the warning predicted.",
    ),
    "planned mission": (
        7,
        "A plan written from plain English by the local model, passed by the checker, approved and"
        " flown.",
    ),
    "spiral descent": (
        7,
        "Down from 40 m on a helix 8 m across, the way down meant to stay out of its own downwash."
        " The sim has the path only.",
    ),
    "lift": (7, "Into a column of air rising at 4 m/s, found by the thrust it saves."),
    "roll doublet": (
        7,
        "Three quick roll doublets on the stick, and self-tuning works out the roll inertia from "
        "them.",
    ),
    "mapping run": (
        7,
        "The camera straight down on a lawnmower grid 30 m up, and a map stitched from the frames.",
    ),
    "mapping run, box moved": (
        7,
        "The same grid with the box moved 22 m, and the two maps compared to find what changed.",
    ),
    "safe landing": (
        7,
        "Asked to land on the shed, it picks the nearest safe spot instead and lands there.",
    ),
    "flow run": (
        7,
        "Six meters up over a textured field, around a rectangle, its position from the camera "
        "alone.",
    ),
}


def about(name: str) -> schema.ScenarioAbout:
    key = "drop from" if re.fullmatch(r"drop from [\d.]+ m", name) else name
    step, what = ABOUT[key]
    if key == "drop from":
        what = f"From {name.removeprefix('drop from ')} up. " + what
    return schema.ScenarioAbout(name=name, step=step, what=what)


def _round(rows, digits: int) -> list[list[float]]:
    return np.round(np.asarray(rows, dtype=float), digits).tolist()


def playback(log, marks, result, firmware: str) -> schema.Playback:
    """One run: its FlightLog (pcs14.flight.grade), the script's marks, and its result."""
    t = np.asarray(log.t, dtype=float)
    duration = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    rate = min(RATE_HZ, MAX_SAMPLES / duration) if duration > 0 else RATE_HZ
    times = np.arange(t[0], t[-1] + 1e-9, 1.0 / rate)[:MAX_SAMPLES]
    k = np.clip(np.searchsorted(t, times), 0, len(t) - 1)
    attitude = (log.attitude[k] if log.attitude is not None
                else np.tile([0.0, 0.0, 0.0, 1.0], (len(k), 1)))  # fmt: skip
    # the log's events already carry the script's marks (pcs14.flight.ulog.flight_log); the
    # marks come in again only for logs read without them. Each once, none before the log
    seen, events = set(), []
    for at, name in sorted([*log.events, *marks], key=lambda e: e[0]):
        key = (round(float(at), 2), name)
        if key not in seen:
            seen.add(key)
            events.append((max(float(at), float(t[0])), name))
    return schema.Playback(
        schema_version=schema.SCHEMA_VERSION,
        scenario=result.scenario,
        setup=result.setup,
        firmware=firmware,
        passed=result.passed,
        findings=[
            schema.FindingRow(check=f.check, passed=f.passed, detail=f.detail)
            for f in result.findings
        ],  # fmt: skip
        t=np.round(times - t[0], 3).tolist(),
        position=_round(log.position[k], 3),
        attitude=_round(attitude, 4),
        motors=_round(log.rotor_speed[k], 0),
        events=[
            schema.Event(at=round(float(at) - float(t[0]), 3), name=name) for at, name in events
        ],  # fmt: skip
    )


GLYPH_POINTS = 40
GOES_SOMEWHERE_M = 4.0  # farther than this across the ground, and its picture is its path
NARROW = 0.25  # a path this narrow for its length is a line from above; its height says more


def glyph(p: schema.Playback) -> schema.Glyph:
    """The run's picture for the scenario list: where it went, seen from above, if it went more
    than a few meters and not just along a line; otherwise its height over time (the climb,
    whatever it did up there, the way down). Evenly spaced in time, scaled to fill a square
    without stretching a path."""
    t = np.asarray(p.t, dtype=float)
    pos = np.asarray(p.position, dtype=float)
    at = np.linspace(t[0], t[-1], GLYPH_POINTS)
    xs, ys, zs = (np.interp(at, t, pos[:, k]) for k in range(3))
    extent = max(np.ptp(xs), np.ptp(ys))
    # how wide the path is against how long, along its own axes, so a diagonal line is a line too
    narrow, wide = np.sqrt(np.clip(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]))), 0, None))
    if extent > GOES_SOMEWHERE_M and narrow > NARROW * wide:
        cx, cy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
        points = np.column_stack([(xs - cx) / extent + 0.5, (ys - cy) / extent + 0.5])
        kind = "plan"
    else:
        low, high = zs.min(), zs.max()
        points = np.column_stack(
            [(at - at[0]) / ((at[-1] - at[0]) or 1), (zs - low) / ((high - low) or 1)]
        )
        kind = "profile"
    return schema.Glyph(kind=kind, points=np.round(points, 3).tolist())


def file_name(setup: str, scenario: str, firmware: str) -> str:
    scenario = scenario.replace(",", "").replace(" ", "-")
    return f"flights/{setup.lower().replace('+', '_')}-{scenario}-{firmware}.json"


def _write(path: Path, key: str, model) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = model.model_dump_json()
    path.write_bytes((text + "\n").encode("utf-8"))
    script = f'(window.pcs14Data = window.pcs14Data || {{}})["{key}"] = {text};\n'
    path.with_suffix(".js").write_bytes(script.encode("utf-8"))
    return path


def write_flights(out, results: dict, logs: Callable) -> list[Path]:
    """Every run's playback file and flights.json. `results` is {firmware: [ScenarioResult]},
    `logs(firmware, setup, scenario)` gives a run's (log, marks, result) or None."""
    out = Path(out)
    written, runs, setups = [], [], []
    for firmware, found in results.items():
        for r in found:
            if r.scenario not in ALL_SCENARIOS:
                continue
            if r.setup not in setups:
                setups.append(r.setup)
            run = logs(firmware, r.setup, r.scenario) if r.flown else None
            name = file_name(r.setup, r.scenario, firmware) if run is not None else None
            shape = None
            if run is not None:
                log, marks, _ = run
                played = playback(log, marks, r, firmware)
                shape = glyph(played)
                written.append(_write(out / name, name, played))
            runs.append(schema.Run(scenario=r.scenario, setup=r.setup, firmware=firmware,
                                   flown=r.flown, passed=r.passed, file=name,
                                   glyph=shape))  # fmt: skip
    index = schema.Flights(schema_version=schema.SCHEMA_VERSION, scenarios=list(ALL_SCENARIOS),
                           about=[about(name) for name in ALL_SCENARIOS], setups=setups,
                           runs=runs)  # fmt: skip
    written.append(_write(out / "flights.json", "flights.json", index))
    return written


def from_outputs(exports) -> tuple[dict, Callable]:
    """The results and logs the flight sim left in `exports` (outputs/flight-sim)."""
    from pcs14.flight.batch import flown_log, load_results

    exports = Path(exports)
    results = {fw: load_results(exports, firmware=fw) for fw in ("px4", "mine")}

    def logs(firmware, setup, scenario):
        name = scenario.replace(" ", "-") + ("-mine" if firmware == "mine" else "")
        return flown_log(exports, setup, name)

    return results, logs
