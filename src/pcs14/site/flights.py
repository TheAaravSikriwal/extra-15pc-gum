"""The flight sim's runs as playback files for the project site: each run's ground truth at up
to 20 Hz (the drone's path and attitude, the motors), its events and its findings, for both
firmwares, and an index of every run for the matrices.

The logs aren't in the repo (*.ulg is gitignored), so these are made on the machine that flew
them, from outputs/flight-sim.
"""

from collections.abc import Callable
from pathlib import Path

import numpy as np

from pcs14.flight.report import SCENARIOS
from pcs14.site import schema

RATE_HZ = 20.0
MAX_SAMPLES = 3000  # a 30 min low battery run comes down to about 1.7 Hz, a few hundred kB


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
    events = sorted([*log.events, *marks], key=lambda e: e[0])
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


def file_name(setup: str, scenario: str, firmware: str) -> str:
    return f"flights/{setup.lower().replace('+', '_')}-{scenario.replace(' ', '-')}-{firmware}.json"


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
            if r.scenario not in SCENARIOS:
                continue
            if r.setup not in setups:
                setups.append(r.setup)
            run = logs(firmware, r.setup, r.scenario) if r.flown else None
            name = file_name(r.setup, r.scenario, firmware) if run is not None else None
            if run is not None:
                log, marks, _ = run
                written.append(_write(out / name, name, playback(log, marks, r, firmware)))
            runs.append(schema.Run(scenario=r.scenario, setup=r.setup, firmware=firmware,
                                   flown=r.flown, passed=r.passed, file=name))  # fmt: skip
    index = schema.Flights(schema_version=schema.SCHEMA_VERSION, scenarios=list(SCENARIOS),
                           setups=setups, runs=runs)  # fmt: skip
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
