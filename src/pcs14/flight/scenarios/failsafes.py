"""PX4's failsafes: losing the link and running low on battery. Both have to bring it home and
land it.

- lost link: 20 m up and 50 m north, holding, the relay cuts the uplink. PX4 hears nothing from
  the ground, waits out its own 10 s, and returns (the x500's NAV_DLL_ACT, kept)
- low battery: PX4's simulated battery, drained at the rate my battery model says a hover
  drains the real pack, so its percentage tracks the real charge. The drone holds 50 m out
  until PX4 calls it critical and returns. PX4 only knows fixed thresholds, so they're set
  where a return from there leaves the reserve: a warning at 35% and the return at 30%. That's
  a stand-in for my firmware's return, which will budget the energy to get home. Whether it
  really landed above the reserve is judged with my battery model, from the logged rotor
  speeds, not PX4's percentage
"""

import numpy as np

from pcs14.flight import grade
from pcs14.flight.scenarios import Aborted, Scenario
from pcs14.flight.scenarios.basic import disarmed, go_to, leave_offboard, offboard_here, take_off

AWAY_NORTH = 50.0  # m
AWAY_HEIGHT = 20.0  # m
LOW_WARNING = 0.35  # PX4's battery thresholds, for the low battery run
LOW_RETURN = 0.30
G = 9.80665


async def fly_out(s):
    await take_off(s, AWAY_HEIGHT)
    await offboard_here(s)
    await go_to(s, AWAY_NORTH, 0.0, AWAY_HEIGHT)
    await leave_offboard(s)
    await s.clock.sleep(3.0)


# --- lost link ---------------------------------------------------------------------------


async def lost_link(s):
    await fly_out(s)
    s.relay.cut = True
    s.mark("link cut")
    await disarmed(s, 240.0)


def grade_lost_link(log, imu, c) -> list:
    return [
        grade.sequence(log.events, ["link cut", "link lost", "return", "landed"], "the return"),
        grade.ends_safely(log, c.sim.returns.max_landing_distance_m),
    ]


# --- low battery -------------------------------------------------------------------------


def _hover_flight(c):
    """The sizing model's hover at the weight the sim flies."""
    from dataclasses import replace

    from pcs14.sizing.battery import Pack
    from pcs14.sizing.flight import fly, power_model

    model = power_model(c.build, c.setup, 0.0, pessimistic=True)
    if c.model.get("mass_kg"):
        model = replace(model, weight=c.model["mass_kg"] * G)
    return fly(model, Pack(c.build.pack), 0.0, c.targets.reserve_fraction)


def full_drain_s(c) -> float:
    """s for a hover to drain a full pack, by my battery model: its time to the reserve,
    stretched over the whole charge."""
    return _hover_flight(c).duration / (1 - c.targets.reserve_fraction)


def low_battery_params(c) -> dict:
    return {
        "SIM_BAT_DRAIN": round(full_drain_s(c), 1),
        "SIM_BAT_MIN_PCT": 0.0,  # PX4's simulated battery stops at 50% unless told otherwise
        "BAT_LOW_THR": LOW_WARNING,
        "BAT_CRIT_THR": LOW_RETURN,
        "COM_LOW_BAT_ACT": 3,  # return at critical, land at emergency (PX4's sim default)
    }


def low_battery_budget(c) -> float:
    return full_drain_s(c) * (1 - LOW_RETURN) + 400.0


async def low_battery(s):
    await fly_out(s)
    s.mark("waiting start")
    limit = low_battery_budget(s.context)
    if not await s.clock.until(lambda: "RETURN" in s.state.mode, limit):
        raise Aborted("PX4 never called the battery low enough to return")
    s.mark("waiting end")
    await disarmed(s, 300.0)


def charge_left(log, c, at: float) -> float:
    """My battery model's state of charge at `at`, from a full pack at arming, every motor's
    power coming from its logged speed."""
    from pcs14.flight.power import drain
    from pcs14.flight.scenarios.capability import logged_power
    from pcs14.sizing.battery import Pack

    start = log.when("armed") or float(log.t[0])
    picked = np.flatnonzero((log.t >= start) & (log.t <= at))[::25]  # every half second
    times = [float(log.t[k] - start) for k in picked]
    powers = [logged_power(log, c, k) for k in picked]
    return drain(Pack(c.build.pack), times, powers).soc[-1]


def grade_low_battery(log, imu, c) -> list:
    out = [
        grade.sequence(log.events, ["low battery", "return", "landed"], "the return"),
        grade.ends_safely(log, c.sim.returns.max_landing_distance_m),
    ]
    landed = log.when("landed")
    if landed is None:
        return out + [grade.Finding("charge at landing", False, None, None, "", "never landed")]
    left = charge_left(log, c, landed)
    reserve = c.targets.reserve_fraction
    out.append(grade.Finding("charge at landing", left >= reserve, left, reserve, "",
                             f"landed with {left:.0%} left by my battery model, against the "
                             f"{reserve:.0%} reserve"))  # fmt: skip
    return out


SCENARIOS = (
    Scenario("lost link", lost_link, grade_lost_link, budget_s=420.0),
    Scenario(
        "low battery",
        low_battery,
        grade_low_battery,
        budget_s=low_battery_budget,
        params=low_battery_params,
    ),
)
