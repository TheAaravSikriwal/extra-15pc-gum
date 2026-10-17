"""The flight stepper: fly at a steady airspeed until the reserve, a few seconds at a time.

Each step, the drone asks the pack for the power it needs at that speed; the battery model
turns it into a current, sag included; the current drains the charge; and the step records
voltage, current, charge used and thrust headroom (full-throttle thrust over the thrust it
needs). The flight ends at the reserve, or earlier if the pack can't deliver the power, the
voltage drops below the cells' minimum, or full throttle can no longer hold the speed.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pcs14 import units
from pcs14.design import Build, SetupTargets
from pcs14.sizing.battery import Pack
from pcs14.sizing.drag import drag_area
from pcs14.sizing.mass import mass_budget
from pcs14.sizing.rotor import MOTORS, PowerModel, Rotor


@dataclass(frozen=True)
class Sample:
    time: float  # s
    soc: float
    voltage: float  # V at the pack, under load
    current: float  # A
    power: float  # W
    mah_used: float
    thrust_headroom: float  # full-throttle thrust over the thrust needed right now


@dataclass(frozen=True)
class Flight:
    speed: float  # m/s
    samples: tuple[Sample, ...]
    ended: str  # reserve, power, voltage, thrust, or stopped (by a stopping rule)

    @property
    def duration(self) -> float:
        return self.samples[-1].time

    @property
    def minutes(self) -> float:
        return units.seconds_to_minutes(self.duration)


def avionics_power(build: Build, setup: SetupTargets) -> float:
    return sum(part.power for part in build.carried(setup.modules))


def power_model(
    build: Build, setup: SetupTargets, growth_margin: float = 0.0, pessimistic: bool = False
) -> PowerModel:
    """The power model for one setup: its weight, drag and avionics, on this build's rotor."""
    return PowerModel(
        rotor=Rotor.from_build(build, pessimistic=pessimistic),
        weight=mass_budget(build, setup, growth_margin).weight,
        drag_area=drag_area(build, setup),
        avionics_power=avionics_power(build, setup),
    )


def thrust_to_weight(model: PowerModel, pack: Pack, soc: float) -> float:
    """Full-throttle thrust over weight, with the pack sagging under the load."""
    return MOTORS * model.rotor.full_throttle(pack, soc).thrust / model.weight


def fly(
    model: PowerModel,
    pack: Pack,
    speed: float,
    reserve_fraction: float,
    dt: float = 5.0,
    stop: Callable[[Sample], bool] | None = None,
) -> Flight:
    """`stop` is an extra rule for ending the flight, like landing at a set voltage."""
    power = model.power(speed)
    needed = model.thrust_per_motor(speed)
    reserve = pack.soc_at_reserve(reserve_fraction)
    soc, time, samples = 1.0, 0.0, []

    def record(current: float) -> Sample:
        full = model.rotor.full_throttle(pack, soc)
        sample = Sample(
            time=time,
            soc=soc,
            voltage=pack.terminal_voltage(soc, current),
            current=current,
            power=power,
            mah_used=pack.mah_used(soc),
            thrust_headroom=model.available_thrust_per_motor(speed, full) / needed,
        )
        samples.append(sample)
        return sample

    while True:
        current = pack.current_for_power(soc, power)
        if current is None:
            ended = "power"
            break
        sample = record(current)
        if sample.voltage < pack.min_voltage:
            ended = "voltage"
            break
        if sample.thrust_headroom < 1:
            ended = "thrust"
            break
        if soc <= reserve + 1e-12:
            ended = "reserve"
            break
        if stop is not None and stop(sample):
            ended = "stopped"
            break
        step = dt
        after = pack.drain(soc, current, step)
        if after < reserve:  # land exactly on the reserve instead of overshooting it
            step = (soc - reserve) * pack.capacity / current
            after = reserve
        soc, time = after, time + step
    if not samples:
        samples.append(Sample(0.0, soc, pack.ocv(soc), 0.0, power, pack.mah_used(soc), 0.0))
    return Flight(speed=speed, samples=tuple(samples), ended=ended)
