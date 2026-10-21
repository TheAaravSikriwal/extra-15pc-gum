"""Step 6's scenarios, the modules in sim. They fly my firmware, since the safety monitor in the
loop is mine. None of them is in step 4's matrix: each runs when it's named.

- hung flight controller (P only): 40 m up, my firmware's process frozen (SIGSTOP), the way a
  hung processor would be. The safety monitor sees its heartbeat stop and cuts the motors; a
  second later the pilot flips the chute switch, which reaches the chute through the monitor.
  My firmware's own log stops while it's frozen, and so does the clock the other scripts wait
  on, so this one times itself on Gazebo's clock and keeps Gazebo's ground truth itself
- drop from N m (Max, the heaviest): flight termination at 10, 15, 20 and 30 m, to find how
  low the chute still saves it (40 m is step 4's parachute drop)
- chute rule (no P): a take-off asked for 40 m; my firmware's parachute rule holds it at 30 m
"""

import asyncio
import os
import signal

from pcs14.flight import grade
from pcs14.flight.scenarios import Scenario
from pcs14.flight.scenarios.basic import hold, take_off
from pcs14.flight.scenarios.failures import COME_DOWN_S, DROP_HEIGHT, grade_drop

PILOT_REACTION_S = 1.0  # from the hang to the pilot's chute switch
SAMPLE_S = 0.02  # wall time between ground-truth samples while the flight controller is frozen
DROP_HEIGHTS = (10.0, 15.0, 20.0, 30.0)
RULE_ASKED_M = 40.0
RULE_CEILING_M = 30.0


# --- hung flight controller --------------------------------------------------------------


async def _until_gz(truth, t_end: float, samples: list):
    """Waits, on Gazebo's clock, until `t_end`, keeping a ground-truth sample every step."""
    while True:
        t, height, tilt = truth.now()
        if not samples or t > samples[-1][0]:
            samples.append((t, height, tilt))
        if t >= t_end:
            return
        await asyncio.sleep(SAMPLE_S)


async def first_pose(truth, timeout_s: float = 10.0) -> float:
    """Gazebo's time at the first pose the ground truth hears (it says -1 before then)."""
    waited = 0.0
    while (t := truth.now()[0]) < 0:
        if waited > timeout_s:
            from pcs14.flight.run import SimError

            raise SimError("Gazebo's ground truth never came in")
        await asyncio.sleep(SAMPLE_S)
        waited += SAMPLE_S
    return t


async def hung_flight_controller(s):
    from pcs14.flight import firmware, run

    await take_off(s, DROP_HEIGHT)
    await hold(s, 3.0, "before")
    truth = firmware.GroundTruth(run.gz_bindings(), s.partition, s.entity)
    samples: list = []
    await first_pose(truth)
    sitl = next(p for name, p in s._processes if name == "sitl")
    t0 = truth.now()[0]
    s.result.notes["hung at"] = t0
    os.kill(sitl.pid, signal.SIGSTOP)  # the flight controller hangs
    try:
        await _until_gz(truth, t0 + PILOT_REACTION_S, samples)
        await s.gz_publish(f"/{s.entity}/chute", "gz.msgs.Boolean", "data: true")
        s.result.notes["chute switch at"] = truth.now()[0]
        await _until_gz(truth, t0 + COME_DOWN_S, samples)
    finally:
        os.kill(sitl.pid, signal.SIGCONT)
    s.result.notes["truth"] = samples


def grade_hung(log, imu, c) -> list:
    """From the monitor's own log, the drag plugin's "chute fired" and Gazebo's ground truth:
    the monitor cut within its timeout, the motors stopped before the canopy left, and the drone
    settled under the canopy before the ground."""
    notes = c.notes
    hung = notes.get("hung at")
    said = notes.get("monitor", [])

    def at(line: str) -> float:
        return float(line.split(" at ")[1].split()[0])

    cut = next((at(x) for x in said if x.startswith("cut flight controller silent")), None)
    released = next((at(x) for x in said if x.startswith("chute released")), None)
    fired = log.when("chute fired") if log is not None else None
    out = []
    if hung is None or cut is None:
        return [grade.Finding("monitor cut", False, None, None, "s", "the monitor never cut")]
    # the monitor's 0.25 s timeout, and 0.1 s for the hang's own moment: it's read off Gazebo's
    # ground truth, sampled every 20 ms of wall time (40 ms of the sim's at 2x)
    late, limit = cut - hung, 0.25 + 0.1
    out.append(grade.Finding("monitor cut", late <= limit, late, limit, "s",
                             f"cut {late:.2f} s after the hang"))  # fmt: skip
    ejection = c.model.get("chute", {}).get("ejection_s", 0.0)
    order = released is not None and fired is not None and cut <= fired + ejection
    out.append(grade.Finding(
        "chute order", order, None, None, "",
        f"the motors stopped {fired + ejection - cut:.2f} s before the canopy left" if order
        else "the chute never fired" if fired is None else "the canopy left before the cut",
    ))  # fmt: skip
    out.append(settled_under_canopy(notes.get("truth", []), fired))
    # the flight controller's log has no IMU while it's frozen, so the free-fall check is the
    # monitor's own: its shadow-mode triggers, on its own IMU
    seen = [at(x) - hung for x in said if x.startswith("trigger free fall") and at(x) >= hung]
    out.append(grade.Finding(
        "monitor's own trigger", bool(seen), seen[0] if seen else None, None, "s",
        f"its free-fall trigger fired {seen[0]:.2f} s after the hang (shadow mode: logged only)"
        if seen else "its free-fall trigger never fired",
    ))  # fmt: skip
    return out


def settled_under_canopy(samples, fired: float | None, band: float = 0.15) -> grade.Finding:
    """From ground-truth (t, height, tilt) samples: whether the descent steadied under the
    canopy before the ground, and how much height that took."""
    import numpy as np

    if fired is None or len(samples) < 10:
        return grade.Finding("settled under the canopy", False, None, None, "m", "no chute")
    t, z = np.array([p[0] for p in samples]), np.array([p[1] for p in samples])
    after = t >= fired
    rate = np.gradient(z, t)
    ground = float(z.min())
    up = after & (z > ground + 0.4)
    if up.sum() < 5:
        return grade.Finding("settled under the canopy", False, None, None, "m",
                             "it reached the ground before the canopy could slow it")  # fmt: skip
    steady = float(np.median(rate[up][-max(1, up.sum() // 5) :]))
    outside = up & (np.abs(rate - steady) > band * abs(steady))
    k = int(np.flatnonzero(outside)[-1]) + 1 if outside.any() else int(np.flatnonzero(up)[0])
    start = int(np.argmax(after))
    lost = float(z[start] - z[min(k, len(z) - 1)])
    left = float(z[min(k, len(z) - 1)] - ground)
    ok = left > 1.0
    return grade.Finding("settled under the canopy", ok, lost, None, "m",
                         f"lost {lost:.1f} m, then came down at {abs(steady):.1f} m/s with "
                         f"{left:.1f} m to spare")  # fmt: skip


# --- drop heights --------------------------------------------------------------------------


def drop_from(height: float):
    async def fly(s):
        await take_off(s, height)
        await hold(s, 3.0, "before")
        s.mark("terminate")
        await s.drone.action.terminate()
        await s.clock.sleep(COME_DOWN_S)

    return fly


def grade_drop_height(log, imu, c) -> list:
    out = grade_drop(log, imu, c)
    fired = log.when("chute fired")
    samples = list(zip(log.t, log.position[:, 2], [0.0] * len(log.t), strict=True))
    return out + [settled_under_canopy(samples, fired)]


# --- the parachute rule --------------------------------------------------------------------


async def chute_rule(s):
    await s.drone.action.set_takeoff_altitude(RULE_ASKED_M)
    await s.drone.action.arm()
    s.mark("arm")
    await s.drone.action.takeoff()
    await s.clock.until(lambda: s.state.height >= RULE_CEILING_M - 1.0, 60.0)
    await hold(s, 10.0)
    await s.drone.action.land()
    await s.clock.until(lambda: not s.state.in_air, 90.0)


def chute_rule_params(c) -> dict:
    return {"PCS14_CHUTE_RULE": 1}  # on, for once: every other run on my firmware has it off


def grade_chute_rule(log, imu, c) -> list:
    peak = float(log.position[:, 2].max())
    ok = peak <= RULE_CEILING_M + 1.0
    words = f"asked for {RULE_ASKED_M:g} m without P, it went to {peak:.1f} m"
    return [grade.Finding("chute rule ceiling", ok, peak, RULE_CEILING_M + 1.0, "m", words)]


SCENARIOS = (
    # no `failure` mark: the batch's trigger check reads the flight controller's IMU, which is
    # frozen here; grade_hung reads the monitor's own triggers instead
    Scenario("hung flight controller", hung_flight_controller, grade_hung, budget_s=180.0,
             healthy=False),
    *(Scenario(f"drop from {h:g} m", drop_from(h), grade_drop_height, budget_s=180.0,
               healthy=False, failure="terminate") for h in DROP_HEIGHTS),
    Scenario("chute rule", chute_rule, grade_chute_rule, budget_s=240.0,
             params=chute_rule_params),
)  # fmt: skip
