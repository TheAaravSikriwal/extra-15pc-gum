"""The scenarios: each one a script that flies PX4 through MAVSDK, and the grader for its log.

A script gets the run's Session (pcs14.flight.run) and flies, marking what it does as it goes
("hold", "wind on" and so on). Its grader gets the converted log (pcs14.flight.ulog), the IMU
samples and a Context, and returns the findings. Scripts wait on PX4's clock, never the wall's,
so a run means the same at any sim speed.
"""

from collections.abc import Callable
from dataclasses import dataclass, field


class Aborted(RuntimeError):
    """The drone didn't do what the script needed (it never climbed, never landed), so the
    script stopped. The run counts as flown and failed, with this as the reason."""


@dataclass(frozen=True)
class Context:
    targets: object  # pcs14.design.Targets
    setup: object  # pcs14.design.SetupTargets
    params: dict  # PX4's, as generated for this combination, plus the scenario's own
    notes: dict = field(default_factory=dict)  # what the script reported
    build: object = None  # pcs14.design.Build, for the scenarios that need the sizing model
    model: dict = field(default_factory=dict)  # the generated model's numbers (model.json)

    @property
    def sim(self):
        return self.targets.flight_sim

    @property
    def top_rot_velocity(self) -> float:
        """rad/s, the motors' top speed in the model."""
        return float(self.params["SIM_GZ_EC_MAX1"])

    @property
    def has_chute(self) -> bool:
        return "P" in self.setup.modules


@dataclass(frozen=True)
class Scenario:
    name: str
    fly: Callable  # async (Session) -> None
    grade: Callable  # (FlightLog, IMU samples, Context) -> list[Finding]
    budget_s: float | Callable  # s of PX4's clock the script may take, or (Context) -> s
    healthy: bool = True  # nothing fails on purpose, so the safety monitor must stay quiet
    params: Callable | None = None  # (Context) -> PX4 parameters this scenario adds
    prepare: Callable | None = None  # async (Session) -> None: sets up the world before PX4
    failure: str | None = None  # the mark where something fails on purpose, for the monitor
    world: str = "pcs14"  # the world's file; pcs14-fine has a 2 ms physics step
    camera: bool = False  # V's camera on the model (pcs14.flight.generate.with_camera)


def scenarios() -> dict[str, Scenario]:
    from pcs14.flight.scenarios import basic, capability, failsafes, failures, modules

    found = (basic.SCENARIOS + capability.SCENARIOS + failsafes.SCENARIOS + failures.SCENARIOS
             + modules.SCENARIOS)  # fmt: skip
    return {s.name: s for s in found}
