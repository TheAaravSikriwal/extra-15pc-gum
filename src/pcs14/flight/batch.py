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
    if scenario.healthy:
        sim = targets.flight_sim
        findings.append(grade.false_triggers(imu, sim.triggers, sim.max_false_triggers))
    note = f"{outcome.wall_s:.0f} s of real time"
    return ScenarioResult(scenario.name, setup.name, True, tuple(findings), note)


def save(exports: Path, model: str, result: ScenarioResult) -> Path:
    folder = Path(exports) / RESULTS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{model}-{result.scenario.replace(' ', '-')}.json"
    data = asdict(result)
    data["findings"] = [asdict(f) for f in result.findings]
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
        findings = tuple(grade.Finding(**f) for f in data.pop("findings"))
        out.append(ScenarioResult(findings=findings, **data))
    return out


async def run_one(tools, exports, setup, scenario: Scenario, targets, build, instance=0, speed=1.0):
    """Flies one scenario in one combination, grades it and saves the result."""
    model = model_name(setup.name)
    params = load_params(exports, model)
    context = Context(targets, setup, params, build=build, model=load_model(exports, model))
    if scenario.params is not None:
        params = {**params, **scenario.params(context)}
        context = replace(context, params=params)
    name = scenario.name.replace(" ", "-")
    session = Session(tools, model, params, exports, name, instance, speed)
    session.context = context
    outcome = await fly(session, scenario.fly, scenario.budget_s, scenario.prepare)
    result = graded(scenario, outcome, context)
    save(exports, model, result)
    return result, outcome


async def run_many(
    tools, exports, pairs, targets, build, jobs: int = 1, speed: float = 1.0, report=print
):
    """Every (setup, scenario) in `pairs`, `jobs` at a time, each on its own PX4 instance."""
    queue: asyncio.Queue = asyncio.Queue()
    for pair in pairs:
        queue.put_nowait(pair)
    results = []

    async def worker(instance: int):
        while not queue.empty():
            setup, scenario = queue.get_nowait()
            result, outcome = await run_one(
                tools, exports, setup, scenario, targets, build, instance, speed
            )
            results.append(result)
            verdict = "pass" if result.passed else ("FAIL" if result.flown else "not flown")
            report(f"{scenario.name} in {setup.name}: {verdict} ({result.note})")
            for f in result.findings:
                if not f.passed:
                    report(f"    {f.check}: {f.detail}")
            if outcome.log is not None:
                report(f"    log: {outcome.log}")

    await asyncio.gather(*(worker(k) for k in range(max(1, jobs))))
    return results
