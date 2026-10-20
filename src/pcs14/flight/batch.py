"""Flying scenarios in combinations, a few at a time, and keeping each one's graded result.

Each run's result is saved as outputs/flight-sim/results/<model>-<scenario>.json the moment it's
graded, so a long batch can stop and pick up again, and the report gathers whatever has flown.
"""

import asyncio
import json
from dataclasses import asdict, replace
from pathlib import Path

from pcs14.flight import grade, ulog
from pcs14.flight.generate import model_name
from pcs14.flight.report import ScenarioResult
from pcs14.flight.run import Session, fly
from pcs14.flight.scenarios import Context, Scenario

RESULTS = "results"


def load_params(exports: Path, model: str) -> dict:
    path = Path(exports) / "models" / model / "params.json"
    if not path.exists():
        raise FileNotFoundError(f"no generated model {model} in {exports}: run pcs14 flight-sim")
    return json.loads(path.read_text(encoding="utf-8"))


def load_model(exports: Path, model: str) -> dict:
    """The generated model's own numbers (its weight, the chute's timing and so on)."""
    path = Path(exports) / "models" / model / "model.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def graded(scenario: Scenario, outcome, context: Context) -> ScenarioResult:
    """A run's ScenarioResult, from its log. A run the sim itself spoiled isn't flown; a run the
    drone spoiled (the script had to stop) is flown and fails."""
    setup, targets = context.setup, context.targets
    if outcome.error:
        return ScenarioResult(scenario.name, setup.name, flown=False, note=outcome.error)
    if outcome.log is None:
        return ScenarioResult(scenario.name, setup.name, flown=False, note="PX4 wrote no log")
    topics = ulog.read(outcome.log)
    log = ulog.flight_log(topics, outcome.marks)
    imu = ulog.imu_samples(topics)
    context = replace(context, notes=outcome.notes)
    findings = list(scenario.grade(log, imu, context)) if not outcome.aborted else []
    if outcome.aborted:
        findings.append(grade.Finding("flown to the end", False, None, None, "", outcome.aborted))
    sim = targets.flight_sim
    if scenario.healthy:
        findings.append(grade.false_triggers(imu, sim.triggers, sim.max_false_triggers))
    elif scenario.failure is not None and log.when(scenario.failure) is not None:
        findings.append(grade.caught(imu, sim.triggers, log.when(scenario.failure)))
    note = f"{outcome.wall_s:.0f} s of real time at {outcome.speed:g}x"
    return ScenarioResult(scenario.name, setup.name, True, tuple(findings), note)


def save(exports: Path, model: str, result: ScenarioResult, outcome=None, name=None) -> Path:
    """The result, plus the run's own record when there is one: the script's marks, its
    notes and how long it took, for looking into a run later."""
    folder = Path(exports) / RESULTS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{model}-{name or result.scenario.replace(' ', '-')}.json"
    data = asdict(result)
    data["findings"] = [asdict(f) for f in result.findings]
    if outcome is not None:
        data["run"] = {
            "marks": [[t, name] for t, name in outcome.marks],
            "notes": outcome.notes,
            "wall_s": outcome.wall_s,
            "speed": outcome.speed,
            "error": outcome.error,
            "aborted": outcome.aborted,
        }
    path.write_text(json.dumps(data, indent=1, default=_plain) + "\n", encoding="utf-8")
    return path


def _plain(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"can't save {type(value).__name__}")


def load_results(exports: Path) -> list[ScenarioResult]:
    out = []
    for path in sorted((Path(exports) / RESULTS).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("run", None)
        findings = tuple(grade.Finding(**f) for f in data.pop("findings"))
        out.append(ScenarioResult(findings=findings, **data))
    return out


def run_name(scenario: Scenario, tag: str | None = None) -> str:
    """A run's name in file names: the scenario's, plus an experiment's tag."""
    name = scenario.name.replace(" ", "-")
    return f"{name}-{tag}" if tag else name


def firmware_tag(firmware: str, tag: str | None) -> str | None:
    """The tag a run's files carry: my firmware's runs are tagged "mine", so they never
    overwrite PX4's and stay out of its report."""
    if firmware == "px4":
        return tag
    return f"{firmware}-{tag}" if tag else firmware


async def run_one(
    tools, exports, setup, scenario: Scenario, targets, build, instance=0, speed=1.0,
    overrides=None, tag=None, firmware="px4",
):  # fmt: skip
    """Flies one scenario in one combination, grades it and saves the result. `overrides` are
    PX4 parameters over everything else, `tag` keeps an experiment's run apart, and `firmware`
    is what flies (PX4, or mine)."""
    tag = firmware_tag(firmware, tag)
    model = model_name(setup.name)
    params = load_params(exports, model)
    context = Context(targets, setup, params, build=build, model=load_model(exports, model))
    if scenario.params is not None:
        params = {**params, **scenario.params(context)}
    params = {**params, **(overrides or {})}
    context = replace(context, params=params)
    name = run_name(scenario, tag)
    session = Session(tools, model, params, exports, name, instance, speed, firmware=firmware)
    session.context = context
    session.world_file = scenario.world
    budget = scenario.budget_s(context) if callable(scenario.budget_s) else scenario.budget_s
    outcome = await fly(session, scenario.fly, budget, scenario.prepare)
    result = graded(scenario, outcome, context)
    if tag:
        result = replace(result, scenario=f"{scenario.name} ({tag})")
    save(exports, model, result, outcome, name)
    return result, outcome


def flown_log(exports, setup_name: str, name: str):
    """A flown run's (FlightLog, marks, ScenarioResult), from its saved log and record, or None
    if it hasn't flown. `name` is the run's name in file names (pcs14_mission-parachute-drop
    is "parachute-drop" in mission)."""
    model = model_name(setup_name)
    path = Path(exports) / RESULTS / f"{model}-{name}.json"
    log = Path(exports) / "logs" / f"{model}-{name}.ulg"
    if not path.exists() or not log.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    record = data.pop("run", None) or {"marks": []}
    marks = [(t, n) for t, n in record["marks"]]
    findings = tuple(grade.Finding(**f) for f in data.pop("findings"))
    return ulog.flight_log(ulog.read(log), marks), marks, ScenarioResult(findings=findings, **data)


def regrade(exports, setup, scenario: Scenario, targets, build) -> ScenarioResult | None:
    """Grades a run again from its saved log and record, without flying it: for when a
    grader changes. None if it hasn't flown."""
    from pcs14.flight.run import RunResult

    model = model_name(setup.name)
    name = scenario.name.replace(" ", "-")
    path = Path(exports) / RESULTS / f"{model}-{name}.json"
    log = Path(exports) / "logs" / f"{model}-{name}.ulg"
    if not path.exists() or not log.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8")).get("run")
    if record is None:
        return None
    outcome = RunResult(model, name, Path(), log=log,
                        marks=[(t, n) for t, n in record["marks"]], notes=record["notes"],
                        error=record["error"], aborted=record["aborted"],
                        wall_s=record["wall_s"], speed=record.get("speed", 1.0))  # fmt: skip
    params = load_params(exports, model)
    context = Context(targets, setup, params, build=build, model=load_model(exports, model))
    if scenario.params is not None:
        context = replace(context, params={**params, **scenario.params(context)})
    result = graded(scenario, outcome, context)
    save(exports, model, result, outcome)
    return result


async def run_many(
    tools, exports, pairs, targets, build, jobs: int = 1, speed: float = 1.0, report=print,
    overrides=None, tag=None, firmware="px4", first_instance=0,
):  # fmt: skip
    """Every (setup, scenario) in `pairs`, `jobs` at a time, each on its own PX4 instance,
    numbered from `first_instance` (so two batches can fly side by side)."""
    queue: asyncio.Queue = asyncio.Queue()
    for pair in pairs:
        queue.put_nowait(pair)
    results = []

    async def worker(instance: int):
        while not queue.empty():
            setup, scenario = queue.get_nowait()
            result, outcome = await run_one(
                tools, exports, setup, scenario, targets, build, instance, speed, overrides, tag,
                firmware,
            )  # fmt: skip
            results.append(result)
            verdict = "pass" if result.passed else ("FAIL" if result.flown else "not flown")
            report(f"{scenario.name} in {setup.name}: {verdict} ({result.note})")
            for f in result.findings:
                if not f.passed:
                    report(f"    {f.check}: {f.detail}")
            if outcome.log is not None:
                report(f"    log: {outcome.log}")

    await asyncio.gather(*(worker(first_instance + k) for k in range(max(1, jobs))))
    return results
