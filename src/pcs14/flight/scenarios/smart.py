"""Step 7's scenarios, the smart features in sim, on my firmware. None of them is in step 4's
matrix: each runs when it's named.

- land now, back to start, land here (base): 15 m up and 30 m north, then each of the three
  ways down. Land now comes down where it is, back to start flies home first, and land here
  flies to a point it's given (20 m east, 20 m north of home) and comes down there
- turn back (V): 30 m up in a 6 m/s wind blowing north, a hover to sense it, 600 m out with the
  wind behind it, then home into it. The grade: the energy home the warning predicted at the
  turn (pcs14.smart.wind, the sizing model's power at the airspeed home takes) against what my
  firmware's own gauge measured on the way home. My firmware's simulated pack drains on a
  clock, not by power, so the pack itself can't run out early; the gauge's current, from the
  motors' thrust, is what the prediction is checked against
- planned mission (mission): the plan `pcs14 smart` wrote from plain English (a local model,
  then the checker), approved here by the test script, which says so in the log, since on the
  drone the approving is mine. A plan the checker refused never gets approved, so never flies
"""

import asyncio
import math

from pcs14.flight import grade
from pcs14.flight.scenarios import Scenario
from pcs14.flight.scenarios.basic import go_to, leave_offboard, offboard_here, take_off

LANDING_HEIGHT_M = 15.0
OUT_NORTH_M = 30.0
HERE = (20.0, 20.0)  # east, north of home: where "land here" is asked to land
LANDED_RADIUS_M = 1.5
LANDING = ("land now", "back to start", "land here")


async def _out(s):
    await take_off(s, LANDING_HEIGHT_M)
    await offboard_here(s)
    await go_to(s, OUT_NORTH_M, 0.0, LANDING_HEIGHT_M, tolerance=1.0)


async def _down(s, timeout: float = 120.0):
    await s.clock.until(lambda: not s.state.in_air, timeout)
    await s.clock.sleep(2.0)


async def land_now(s):
    await _out(s)
    await leave_offboard(s)
    s.mark("land now")
    await s.drone.action.land()
    await _down(s)


async def back_to_start(s):
    await _out(s)
    await leave_offboard(s)
    s.mark("back to start")
    await s.drone.action.return_to_launch()
    await _down(s)


async def land_here(s):
    await _out(s)
    s.mark("land here")
    east, north = HERE
    await go_to(s, north, east, LANDING_HEIGHT_M, tolerance=1.0)
    await leave_offboard(s)
    await s.drone.action.land()
    await _down(s)


def grade_landed_at(log, c, where) -> list:
    """On the ground within LANDED_RADIUS_M of `where` (east, north of home), and gently."""
    end = log.position[-1]
    off = math.hypot(end[0] - where[0], end[1] - where[1])
    down = log.when("landed") is not None or end[2] <= grade.ON_GROUND_M
    ok = down and off <= LANDED_RADIUS_M
    words = (f"down {off:.1f} m from where it was asked to land" if down
             else f"still {end[2]:.0f} m up")  # fmt: skip
    return [grade.Finding("landed where asked", ok, off, LANDED_RADIUS_M, "m", words),
            grade.touchdown(log, c.sim.failures.max_touchdown_ms)]  # fmt: skip


def grade_land_now(log, imu, c) -> list:
    return grade_landed_at(log, c, (0.0, OUT_NORTH_M))


def grade_back_to_start(log, imu, c) -> list:
    return grade_landed_at(log, c, (0.0, 0.0))


def grade_land_here(log, imu, c) -> list:
    return grade_landed_at(log, c, HERE)


# --- the turn-back warning ------------------------------------------------------------------

TURN_HEIGHT_M = 30.0
TURN_WIND_MS = 6.0  # blowing north
TURN_GROUND_MS = 10.0
TURN_OUT_S = 60.0
TURN_HOVER_S = 12.0
PREDICTION_TOLERANCE = 0.25


def rotate(q, v):
    """v turned by the unit quaternion q (x, y, z, w)."""
    import numpy as np

    x, y, z, w = q
    u, v = np.array([x, y, z]), np.asarray(v, dtype=float)
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)


def wind_from_log(log, start: float, end: float, mass_kg: float, drag_area_m2: float):
    """The wind from the lean over a steady hover, the thrust axis averaged first."""
    import numpy as np

    from pcs14.smart import wind

    inside = log.window(start, end)
    ups = np.array([rotate(q, (0.0, 0.0, 1.0)) for q in log.attitude[inside]])
    if ups[:, 2].mean() < 0:
        ups = -ups
    up = ups.mean(axis=0)
    up /= np.linalg.norm(up)
    # the log's frame: x east, y north, z up
    return wind.from_lean(lean_north=float(up[1]), lean_east=float(up[0]), mass_kg=mass_kg,
                          drag_area_m2=drag_area_m2)  # fmt: skip


def gauge_wh(samples, start: float, end: float) -> float:
    """Wh from (t, volts, amps) samples between `start` and `end`."""
    inside = [x for x in samples if start <= x[0] <= end]
    return sum((t1 - t0) * v0 * a0 for (t0, v0, a0), (t1, _, _) in
               zip(inside, inside[1:], strict=False)) / 3600.0  # fmt: skip


def grade_prediction(predicted_wh: float, measured_wh: float):
    """The energy the warning predicted for the way home, against what the flight used: within
    PREDICTION_TOLERANCE either way, and with the warning's own margin on top, enough. An
    optimistic warning is the dangerous kind, and the margin is what covers it."""
    from pcs14.smart.wind import MARGIN

    off = (predicted_wh - measured_wh) / measured_wh
    ok = abs(off) <= PREDICTION_TOLERANCE and predicted_wh * MARGIN >= measured_wh
    return grade.Finding("the way home's energy", ok, off, PREDICTION_TOLERANCE, "",
                         f"predicted {predicted_wh:.1f} Wh at the turn, the flight used "
                         f"{measured_wh:.1f} Wh: {off:+.0%}")  # fmt: skip


async def turn_back(s):
    from mavsdk.offboard import VelocityNedYaw

    from pcs14.flight.generate import WIND_TOPIC

    samples: list = []

    async def gauge():
        async for b in s.drone.telemetry.battery():
            if s.clock.now is not None:
                samples.append((s.clock.now, b.voltage_v, b.current_battery_a))

    watch = asyncio.create_task(gauge())
    try:
        await take_off(s, TURN_HEIGHT_M)
        await offboard_here(s)
        await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", f"y: {TURN_WIND_MS}")
        await s.clock.sleep(8.0)  # for the lean to settle
        s.mark("sense start")
        await s.clock.sleep(TURN_HOVER_S)
        s.mark("sense end")
        await s.drone.offboard.set_velocity_ned(VelocityNedYaw(TURN_GROUND_MS, 0, 0, 0.0))
        await s.clock.sleep(TURN_OUT_S)
        s.mark("turn")
        await s.drone.offboard.set_velocity_ned(VelocityNedYaw(-TURN_GROUND_MS, 0, 0, 0.0))
        await s.clock.until(lambda: s.state.north <= 5.0, 3 * TURN_OUT_S)
        s.mark("home")
        await go_to(s, 0.0, 0.0, TURN_HEIGHT_M, tolerance=1.5)
        await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", "y: 0")
        await leave_offboard(s)
        await s.drone.action.land()
        await s.clock.until(lambda: not s.state.in_air, 120.0)
    finally:
        watch.cancel()
        s.result.notes["battery"] = samples


def grade_turn_back(log, imu, c) -> list:
    import numpy as np

    from pcs14.sizing.flight import power_model
    from pcs14.smart import wind

    sensed = wind_from_log(log, log.when("sense start"), log.when("sense end"),
                           c.model["mass_kg"], c.model["drag_area_m2"])  # fmt: skip
    out = [grade.Finding("wind sensed", abs(sensed.speed_ms - TURN_WIND_MS) < 1.0,
                         sensed.speed_ms, TURN_WIND_MS, "m/s",
                         f"{sensed.speed_ms:.1f} m/s from {sensed.from_deg:.0f} degrees, "
                         f"against the sim's {TURN_WIND_MS:g} from 180")]  # fmt: skip
    turn, home = log.when("turn"), log.when("home")
    k = int(log.t.searchsorted(turn))
    distance = math.hypot(log.position[k, 0], log.position[k, 1])
    # both from the pessimistic rotor: the sizing model's curve for the prediction, the thrust
    # table read by the thrust each rotor made for the flight (step 4's endurance does the same)
    model = power_model(c.build, c.setup, 0.0, pessimistic=True)
    # home at TURN_GROUND_MS over the ground: the airspeed that takes, against the sensed wind
    airspeed = TURN_GROUND_MS - (-sensed.toward_north)
    predicted = wind.energy_home_wh(wind.never_below_hover(model.power), distance,
                                    home_north=-1.0, home_east=0.0,
                                    wind_north=sensed.toward_north,
                                    wind_east=sensed.toward_east, airspeed_ms=airspeed)  # fmt: skip
    from pcs14.flight.scenarios.capability import logged_power

    leg = np.flatnonzero(log.window(turn, home))
    used = sum(logged_power(log, c, k) * (log.t[k + 1] - log.t[k]) for k in leg[:-1]) / 3600
    out.append(grade_prediction(predicted, used))
    gauge = gauge_wh(c.notes.get("battery", []), turn, home)
    words = f"my firmware's own gauge counted {gauge:.1f} Wh on the way home"
    out.append(grade.Finding("my firmware's gauge", True, gauge, None, "Wh", words))
    out.append(grade.ends_safely(log, 5.0))
    return out


# --- a planned mission --------------------------------------------------------------------

WAYPOINT_RADIUS_M = 2.0
SCRIPT_APPROVAL = "the test script, in the sim (on the drone, the approving is mine)"


async def planned_mission(s):
    from pcs14.smart import missions

    path = s.exports.parent / "smart" / "plan.json"
    saved = missions.approve(path, by=SCRIPT_APPROVAL)  # raises if the checker refused it
    s.result.notes["plan"] = saved.model_dump()
    plan = saved.plan
    first = plan.waypoints[0]
    await take_off(s, first.height_m)
    await offboard_here(s)
    for k, w in enumerate(plan.waypoints, start=1):
        s.mark(f"waypoint {k}")
        await go_to(s, w.north_m, w.east_m, w.height_m, tolerance=1.0, timeout=180.0)
        if w.hold_s:
            await s.clock.sleep(w.hold_s)
    await leave_offboard(s)
    if plan.end == "land":
        await s.drone.action.land()
    else:
        await s.drone.action.return_to_launch()
    await s.clock.until(lambda: not s.state.in_air, 240.0)
    await s.clock.sleep(2.0)


def grade_waypoints(log, plan) -> list:
    """Each waypoint: how close the flight came to it (the log is east, north, up)."""
    import numpy as np

    out = []
    for k, w in enumerate(plan.waypoints, start=1):
        target = np.array([w.east_m, w.north_m, w.height_m])
        closest = float(np.min(np.linalg.norm(log.position - target, axis=1)))
        out.append(grade.Finding(f"waypoint {k}", closest <= WAYPOINT_RADIUS_M, closest,
                                 WAYPOINT_RADIUS_M, "m",
                                 f"came within {closest:.1f} m of {w.north_m:g} m north, "
                                 f"{w.east_m:g} m east, {w.height_m:g} m up"))  # fmt: skip
    return out


def grade_planned_mission(log, imu, c) -> list:
    from pcs14.smart.missions import Plan

    saved = c.notes.get("plan")
    if not saved:
        return [grade.Finding("the plan", False, None, None, "", "no approved plan flew")]
    plan = Plan.model_validate(saved["plan"])
    out = [grade.Finding("the plan", True, None, None, "",
                         f"\"{saved['words']}\", approved by {saved['approved_by']}")]  # fmt: skip
    out += grade_waypoints(log, plan)
    if plan.end == "return":
        out.append(grade.ends_safely(log, 3.0))
    return out


SCENARIOS = (
    Scenario("land now", land_now, grade_land_now, budget_s=180.0),
    Scenario("back to start", back_to_start, grade_back_to_start, budget_s=180.0),
    Scenario("land here", land_here, grade_land_here, budget_s=180.0),
    Scenario("turn back", turn_back, grade_turn_back, budget_s=420.0),
    Scenario("planned mission", planned_mission, grade_planned_mission, budget_s=600.0),
)
