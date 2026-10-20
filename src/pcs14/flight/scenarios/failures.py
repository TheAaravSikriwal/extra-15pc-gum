"""Things going wrong: the parachute drop, a dead motor, a failed sensor and a sagging pack.
None of them may end in a fly-away; each has to end in a controlled landing or under the chute.

- parachute drop (P only): 40 m up, flight termination from the ground. PX4 stops the motors
  and its parachute output fires the chute in the same step; the canopy leaves after its
  ejection delay
- dead motor: 40 m up, PX4's failure injection stops motor 1. PX4 only acts on that with
  CA_FAILURE_MODE set (the x500 ignores motor failures), and its "remove the failed motor"
  setting is what I'd want anyway: it gives up yaw to keep the attitude. A quad still can't
  fly on three motors. With P, PX4's failure detector sees the attitude go and terminates,
  which fires the chute; without P there's nothing to save it, and the run shows how it comes
  down
- failed sensor: the GPS, 20 m up and 30 m north. It's the sensor PX4 leans on most for
  holding position, and losing it leaves the barometer and the IMU to come down on. PX4's
  Gazebo bridge doesn't do sensor failure injection (only Gazebo Classic's does), so the
  GPS fails on PX4's side: its estimator stops using it (EKF2_GPS_CTRL to 0) mid-flight
- sagging pack: 20 m up, the pack sags the way a cold or worn one does, three times its
  internal resistance. The motors' top speed drops to what that pack gives at the reserve,
  and PX4's battery reading drops to empty, so it lands where it is
"""

import math
from dataclasses import replace

from pcs14.flight import grade
from pcs14.flight.scenarios import Scenario
from pcs14.flight.scenarios.basic import (
    disarmed,
    go_to,
    hold,
    leave_offboard,
    offboard_here,
    take_off,
)

DROP_HEIGHT = 40.0  # m
SENSOR_NORTH = 30.0
FAILURE_HEIGHT = 20.0
SAG_RESISTANCE = 3.0  # times the cells' internal resistance: a cold or worn pack
# s to wait after a termination or a dead motor: down from 40 m even under the canopy (about
# 10 s at 4.6 m/s), with room to spare. PX4's own estimate can't be trusted to say it's down
# after a tumble, so the script just waits, and the grader looks at Gazebo's ground truth
COME_DOWN_S = 25.0


def _chute(log, c) -> list:
    ejection = c.model.get("chute", {}).get("ejection_s", 0.0)
    return grade.chute(log, ejection_s=ejection)


def _after_failure(log, c, mark: str) -> list:
    """No fly-away from where the failure hit, and, without a chute, a controlled landing."""
    since = log.when(mark)
    out = [grade.ends_safely(log, c.sim.failures.max_distance_m, since=since)]
    if log.when("chute fired") is not None:
        out += _chute(log, c)
    else:
        out.append(grade.touchdown(log, c.sim.failures.max_touchdown_ms))
    return out


# --- parachute drop ----------------------------------------------------------------------


async def parachute_drop(s):
    await take_off(s, DROP_HEIGHT)
    await hold(s, 3.0, "before")
    s.mark("terminate")
    await s.drone.action.terminate()
    await s.clock.sleep(COME_DOWN_S)


def grade_drop(log, imu, c) -> list:
    return _chute(log, c) + [
        grade.ends_safely(log, c.sim.failures.max_distance_m, since=log.when("terminate"))
    ]


# --- dead motor --------------------------------------------------------------------------


async def dead_motor(s):
    from mavsdk.failure import FailureType, FailureUnit

    await take_off(s, DROP_HEIGHT)
    await hold(s, 3.0, "before")
    s.mark("motor failed")
    await s.drone.failure.inject(FailureUnit.SYSTEM_MOTOR, FailureType.OFF, 1)
    await s.clock.sleep(COME_DOWN_S)


def dead_motor_params(c) -> dict:
    return {"CA_FAILURE_MODE": 1}  # act on a failed motor: drop it from the mix


def grade_dead_motor(log, imu, c) -> list:
    return _after_failure(log, c, "motor failed")


# --- failed sensor -----------------------------------------------------------------------


async def failed_sensor(s):
    await take_off(s, FAILURE_HEIGHT)
    await offboard_here(s)
    await go_to(s, SENSOR_NORTH, 0.0, FAILURE_HEIGHT)
    await leave_offboard(s)
    await s.clock.sleep(3.0)
    s.mark("gps failed")
    await s.drone.param.set_param_int("EKF2_GPS_CTRL", 0)
    await disarmed(s, 300.0)


def grade_failed_sensor(log, imu, c) -> list:
    return [grade.sequence(log.events, ["gps failed", "landed"], "the landing")] + _after_failure(
        log, c, "gps failed"
    )


# --- sagging pack ------------------------------------------------------------------------


def sagged_top_speed(c) -> float:
    """rad/s: the motors' top speed on a sagging pack (SAG_RESISTANCE times the cells'
    resistance) at the reserve, scaled from the model's own by the square root of the
    full-throttle thrust, since thrust goes as the speed squared."""
    from pcs14.sizing.battery import Pack
    from pcs14.sizing.rotor import Rotor

    spec = c.build.pack
    cell = spec.cell.model_copy(
        update={"internal_resistance_mohm": spec.cell.internal_resistance_mohm * SAG_RESISTANCE}
    )
    rotor = Rotor.from_build(c.build, pessimistic=True)
    soc = c.targets.reserve_fraction
    healthy = rotor.full_throttle(Pack(spec), soc).thrust
    sagging = rotor.full_throttle(Pack(replace(spec, cell=cell)), soc).thrust
    return c.top_rot_velocity * math.sqrt(sagging / healthy)


async def sagging_pack(s):
    from mavsdk.failure import FailureType, FailureUnit

    top = round(sagged_top_speed(s.context))
    s.result.notes["sagged_top_rot_velocity"] = top
    await take_off(s, FAILURE_HEIGHT)
    await hold(s, 3.0, "before")
    s.mark("pack sagged")
    for n in range(1, 5):
        await s.drone.param.set_param_int(f"SIM_GZ_EC_MAX{n}", top)
    await s.drone.failure.inject(FailureUnit.SYSTEM_BATTERY, FailureType.OFF, 0)
    await disarmed(s, 180.0)


def grade_sagging_pack(log, imu, c) -> list:
    out = [grade.sequence(log.events, ["pack sagged", "low battery", "landed"], "the landing")]
    top = c.notes.get("sagged_top_rot_velocity")
    if top:
        share = top / c.top_rot_velocity
        out.append(grade.Finding("sagged top speed", True, share, None, "",
                                 f"the motors topped out at {share:.0%} of their usual top "
                                 "speed"))  # fmt: skip
    return out + _after_failure(log, c, "pack sagged")


SCENARIOS = (
    Scenario(
        "parachute drop",
        parachute_drop,
        grade_drop,
        budget_s=180.0,
        healthy=False,
        failure="terminate",
    ),
    Scenario(
        "dead motor",
        dead_motor,
        grade_dead_motor,
        budget_s=180.0,
        healthy=False,
        params=dead_motor_params,
        failure="motor failed",
        world="pcs14-fine",
    ),
    Scenario("failed sensor", failed_sensor, grade_failed_sensor, budget_s=420.0),
    Scenario("sagging pack", sagging_pack, grade_sagging_pack, budget_s=300.0),
)
