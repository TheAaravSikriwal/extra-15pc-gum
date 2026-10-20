"""What the drone can do: hover, answer the sticks, run flat out, hold in wind, last, and pick
up its payload.

- hover: 10 m up, held for the targets' 60 s
- steps: sudden stick inputs in PX4's altitude mode, the way a pilot flies: roll right, back
  to center, pitch forward, back to center, each held 2 s. Each step is judged against where
  the attitude settles, not the stick's nominal angle, because PX4 turns the stick into an
  acceleration first. Yaw isn't stepped: a yaw stick commands a rate, not an angle
- top speed: 30 m up, an offboard velocity of PX4's 25 m/s limit to the north for 30 s, so the
  drag plugin and the tilt limit decide where it tops out
- wind: 10 m up, the wind ramps from still to the setup's speed over 10 s (a real wind builds;
  a step from nothing is a harder test than the target means), then blows for 30 s
- endurance: 60 s of hover, then two 30 s legs at the cruise speed, there and back. Each
  stretch's power comes from the logged rotor speeds, and the battery model turns it into a
  flight time to compare with the sizing model's at the same weight
- payload grab: a 250 g box on a 1 m shelf 4 m north of home. The drone hovers 0.4 m above it,
  the box goes up to just under its feet, where the claws would hold it, and Gazebo's attach
  joint stands in for the claws. It climbs to 3 m and carries it for 20 s, then lets go of it
  1.5 m up, 2 m east of home, and lands at home
"""

import contextlib
import math
from dataclasses import replace

import numpy as np

from pcs14.flight import grade, ulog
from pcs14.flight.generate import PAYLOAD_TOPICS, PREFIX, TOP_SPEED_LIMIT, WIND_TOPIC
from pcs14.flight.scenarios import Aborted, Scenario
from pcs14.flight.scenarios.basic import (
    Sticks,
    go_to,
    height_at,
    hold,
    land,
    leave_offboard,
    missing,
    offboard_here,
    take_off,
    window,
)

HOVER_HEIGHT = 10.0
STEP_STICK = 0.4  # of full stick
STEP_S = 2.0
# (axis, its index in PX4's (roll, pitch, yaw), the stick)
STEPS = (("roll", 0, STEP_STICK), ("roll", 0, 0.0), ("pitch", 1, STEP_STICK), ("pitch", 1, 0.0))
STEP_BEFORE_S = 0.2  # the level before a step: the average over this long before it
STEP_FINAL_S = 0.5  # where it settles: the average over the end of the step
DASH_HEIGHT = 30.0
DASH_S = 30.0
WIND_RAMP_S = 10.0
WIND_RAMP_STEPS = 20
WIND_HOLD_S = 30.0
ENDURANCE_HOVER_S = 60.0
CRUISE_LEG_S = 30.0
CRUISE_SETTLE_S = 8.0  # each leg's start, to get up to speed, isn't counted
SHELF_NORTH = 4.0  # m north of home
SHELF_HEIGHT = 1.0
SHELF_SIDE = 0.3
PAYLOAD_SIZE = 0.08  # the payload model's box, pcs14.flight.generate.payload_sdf
GRAB_CLEARANCE = 0.4  # m between the drone's feet and the payload's top
CLAW_GAP = 0.01  # m between the feet and the box's top once the claws have it
SETTLE_STEPS_S = 0.01  # s of sim for Gazebo to move the box before the joint takes it
CARRY_HEIGHT = 3.0
DROP_EAST = 2.0  # m east of home, where the box gets set down, clear of the landing spot
RELEASE_HEIGHT = 1.5  # m: the box drops about a meter when it's let go. Lower, PX4's height
# estimate isn't good to 20 cm, and with the box resting on the ground it calls itself landed
CARRY_S = 20.0
LIFT_BAND = 0.05  # the rotors' thrust has to grow by the payload's share, within this much
G = 9.80665


# --- hover -------------------------------------------------------------------------------


async def hover(s):
    await take_off(s, HOVER_HEIGHT)
    await hold(s, s.context.sim.hover.duration_s)
    await land(s)


def grade_hover(log, imu, c) -> list:
    found = window(log, "hold")
    if found is None:
        return missing("hold")
    start, end = found
    h = c.sim.hover
    return grade.hover_hold(
        log, start, end, height_at(log, start), h.max_drift_m, h.max_height_error_m
    )


# --- steps -------------------------------------------------------------------------------


def steps_params(c) -> dict:
    return {"COM_RC_IN_MODE": 1}  # the sticks come over MAVLink, the way a joystick's do


async def steps(s):
    await take_off(s, HOVER_HEIGHT)
    async with Sticks(s) as sticks:
        # PX4 won't take a manual mode until the sticks have been coming in for a moment, and
        # if it never switches, the first stick movement drops it from Hold into Position
        # mode, where a stick means a speed rather than an angle
        await s.clock.sleep(1.0)
        for _ in range(5):
            with contextlib.suppress(Exception):
                await s.drone.manual_control.start_altitude_control()
            if await s.clock.until(lambda: s.state.mode.endswith("ALTCTL"), 2.0):
                break
        else:
            raise Aborted(f"PX4 never went into altitude mode (it stayed in {s.state.mode})")
        await s.clock.sleep(2.0)
        for k, (axis, _, stick) in enumerate(STEPS):
            await sticks.move(**({"y": stick} if axis == "roll" else {"x": stick}))
            s.mark(f"step {k} start")
            await s.clock.sleep(STEP_S)
            s.mark(f"step {k} end")
        await s.drone.action.hold()
        await s.clock.sleep(2.0)
        await land(s)


def grade_steps(log, imu, c) -> list:
    if log.attitude is None:
        return missing("attitude log")
    angles = ulog.px4_euler(log.attitude)
    out = []
    for k, (axis, index, stick) in enumerate(STEPS):
        found = window(log, f"step {k}")
        if found is None:
            return out + missing(f"step {k}")
        start, end = found
        angle = angles[:, index]
        before = (log.t >= start - STEP_BEFORE_S) & (log.t < start)
        final = (log.t >= end - STEP_FINAL_S) & (log.t <= end)
        inside = (log.t >= start) & (log.t <= end)
        level, settled = float(angle[before].mean()), float(angle[final].mean())
        size = settled - level
        name = f"{axis} {'to' if stick else 'back from'} {math.degrees(abs(size)):.0f} degrees"
        if abs(size) < math.radians(1):
            out.append(grade.Finding(name, False, None, None, "", "the stick barely moved it"))
            continue
        response = (angle[inside] - level) / size
        settle, overshoot = grade.step_response(
            log.t[inside], response, start, 1.0, c.sim.steps.max_settle_s, c.sim.steps.max_overshoot
        )
        out += [
            replace(settle, check=f"{name}: settling"),
            replace(overshoot, check=f"{name}: overshoot"),
        ]
    return out


# --- top speed ---------------------------------------------------------------------------


async def top_speed(s):
    from mavsdk.offboard import VelocityNedYaw

    await take_off(s, DASH_HEIGHT)
    await offboard_here(s)
    await s.drone.offboard.set_velocity_ned(VelocityNedYaw(TOP_SPEED_LIMIT, 0.0, 0.0, 0.0))
    await hold(s, DASH_S, "dash")
    await s.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await s.clock.until(lambda: s.state.speed < 0.5, 30.0)
    await leave_offboard(s)
    await land(s)


def grade_top_speed(log, imu, c) -> list:
    found = window(log, "dash")
    if found is None:
        return missing("dash")
    start, end = found
    inside = log.window(start, end)
    dash = grade.FlightLog(log.t[inside], log.position[inside], log.velocity[inside],
                           log.rotor_speed[inside])  # fmt: skip
    out = [grade.top_speed(dash, c.setup.min_top_speed)]
    share = float(log.rotor_speed[inside].max() / c.top_rot_velocity)
    lean = 0.0
    if log.attitude is not None:
        lean = float(np.degrees(ulog.tilt_of(log.attitude[inside])).max())
    out.append(grade.Finding("top speed, flat out", True, share, None, "",
                             f"the busiest motor at {share:.0%} of its top speed, leaning up to "
                             f"{lean:.0f} degrees"))  # fmt: skip
    return out


# --- wind --------------------------------------------------------------------------------


async def wind(s):
    speed = s.context.setup.hold_position_in_wind
    await take_off(s, HOVER_HEIGHT)
    s.mark("wind start")
    # the ramp follows PX4's clock: each publish takes real time, which at a faster sim speed
    # is more sim time, so stepping a fixed count would stretch the ramp
    start = s.clock.now
    while (elapsed := s.clock.now - start) < WIND_RAMP_S:
        share = min(elapsed / WIND_RAMP_S + 1 / WIND_RAMP_STEPS, 1.0)
        await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", f"x: {speed * share}")
        await s.clock.sleep(WIND_RAMP_S / WIND_RAMP_STEPS)
    await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", f"x: {speed}")
    await s.clock.sleep(WIND_HOLD_S)
    s.mark("wind end")
    await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", "x: 0")
    await land(s)


def grade_wind(log, imu, c) -> list:
    found = window(log, "wind")
    if found is None:
        return missing("wind")
    start, end = found
    w = c.sim.wind
    out = grade.wind_hold(log, start, end, height_at(log, start), w.max_drift_m,
                          w.max_motor_share, c.top_rot_velocity)  # fmt: skip
    if log.attitude is not None:
        steady = log.window(end - WIND_HOLD_S / 2, end)
        lean = float(np.degrees(ulog.tilt_of(log.attitude[steady])).mean())
        out.append(grade.Finding("leaning into the wind", lean > 0.5, lean, 0.5, "degrees",
                                 f"leaned {lean:.1f} degrees into a "
                                 f"{c.setup.hold_position_in_wind:g} m/s wind"))  # fmt: skip
    return out


# --- endurance ---------------------------------------------------------------------------


async def endurance(s):
    from mavsdk.offboard import VelocityNedYaw

    cruise = s.context.targets.cruise_speed
    await take_off(s, HOVER_HEIGHT)
    await hold(s, ENDURANCE_HOVER_S, "hover")
    await offboard_here(s)
    for k, direction in enumerate((1.0, -1.0)):
        await s.drone.offboard.set_velocity_ned(
            VelocityNedYaw(direction * cruise, 0.0, 0.0, 0.0 if direction > 0 else 180.0)
        )
        await s.clock.sleep(CRUISE_SETTLE_S)
        await hold(s, CRUISE_LEG_S - CRUISE_SETTLE_S, f"cruise {k}")
    await s.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await s.clock.until(lambda: s.state.speed < 0.5, 20.0)
    await leave_offboard(s)
    await land(s)


def logged_power(log, c, k: int) -> float:
    """W from the pack at log sample `k`: every motor's power for the thrust it made, from the
    thrust table, plus the avionics (pcs14.flight.power)."""
    from pcs14.flight.power import electrical_power_from_thrust
    from pcs14.sizing.flight import avionics_power
    from pcs14.sizing.rotor import Rotor

    rotor = Rotor.from_build(c.build, pessimistic=True)
    thrusts = c.model["motor_constant"] * log.rotor_speed[k] ** 2
    return electrical_power_from_thrust(rotor, thrusts, avionics_power(c.build, c.setup))


def mean_power(log, windows, c) -> float:
    """W from the pack, on average over the marked stretches."""
    picked = [k for start, end in windows for k in np.flatnonzero(log.window(start, end))]
    return float(np.mean([logged_power(log, c, k) for k in picked]))


def grade_endurance(log, imu, c) -> list:
    from pcs14.flight.power import endurance as flight_time
    from pcs14.sizing.battery import Pack
    from pcs14.sizing.flight import fly, power_model

    pack = Pack(c.build.pack)
    reserve = c.targets.reserve_fraction
    sizing = power_model(c.build, c.setup, 0.0, pessimistic=True)
    if c.model.get("mass_kg"):  # the sizing model at the weight the sim flies (no payload)
        sizing = replace(sizing, weight=c.model["mass_kg"] * G)
    out = []
    stretches = {
        "hover": ([window(log, "hover")], 0.0),
        "cruise": ([window(log, "cruise 0"), window(log, "cruise 1")], c.targets.cruise_speed),
    }
    for name, (windows, speed) in stretches.items():
        if any(w is None for w in windows):
            out += missing(name)
            continue
        watts = mean_power(log, windows, c)
        sim_s = flight_time(pack, watts, reserve)
        sizing_s = fly(sizing, pack, speed, reserve).duration
        found = grade.endurance(sim_s, sizing_s, c.sim.endurance.max_difference)
        out.append(replace(found, check=f"{name} endurance",
                           detail=f"{found.detail}, at {watts:.0f} W"))  # fmt: skip
    return out


# --- payload grab ------------------------------------------------------------------------

_BOX = f"<geometry><box><size>{SHELF_SIDE} {SHELF_SIDE} {SHELF_HEIGHT}</size></box></geometry>"
SHELF_SDF = (
    f'<sdf version="1.9"><model name="{PREFIX}shelf"><static>true</static><link name="link">'
    f'<collision name="c">{_BOX}</collision><visual name="v">{_BOX}</visual></link></model></sdf>'
)


async def place_payload(s):
    """The shelf and the payload on it, before PX4 spawns the drone (whose attach joint looks
    for the payload when it loads). Gazebo's frame is east-north-up."""
    await s.spawn_sdf(SHELF_SDF, f"{PREFIX}shelf", (0.0, SHELF_NORTH, SHELF_HEIGHT / 2))
    payload = s.exports / "models" / f"{PREFIX}payload" / "model.sdf"
    top = SHELF_HEIGHT + PAYLOAD_SIZE / 2 + 0.002
    await s.spawn(payload, f"{PREFIX}payload", (0.0, SHELF_NORTH, top))


def claws_position(drone, lift_off: float) -> tuple[float, float, float]:
    """Where the box's center goes for the claws to hold it: just under the feet of a drone
    whose origin is at `drone` (Gazebo's frame, z up) and `lift_off` m above its feet."""
    x, y, z = drone
    return x, y, z - lift_off - CLAW_GAP - PAYLOAD_SIZE / 2


async def to_the_claws(s, attach_topic: str):
    """Moves the box from the shelf to just under the feet. Gazebo's attach joint keeps
    whatever offset it finds, and holding the box rigidly 0.4 m below the feet is a boom real
    claws don't have: it put five times the roll inertia on the drone, and my firmware's roll
    loop, which only knows the drone's own, swung itself over on it (2026-10-20)."""
    from pcs14.flight.run import WORLD, SimError

    topics = s.gz()
    if topics is None:
        raise SimError("the payload grab needs Gazebo's Python bindings (python3-gz-transport13)")
    await topics.ready(attach_topic, "gz.msgs.Empty")  # so the joint closes right after the move
    pose = s.true_pose(s.entity)
    if pose is None:
        raise SimError("Gazebo hasn't sent the drone's pose")
    (x, y, z), (qw, qx, qy, qz) = claws_position(pose[0], s.context.model["lift_off_m"]), pose[1]
    reply = await s.gz_service(
        f"/world/{WORLD}/set_pose", "gz.msgs.Pose", "gz.msgs.Boolean",
        f'name: "{PREFIX}payload", position: {{x: {x}, y: {y}, z: {z}}}, '
        f"orientation: {{w: {qw}, x: {qx}, y: {qy}, z: {qz}}}",
        fast=True,
    )  # fmt: skip
    if "true" not in reply:
        raise SimError(f"Gazebo wouldn't move the payload: {reply.strip()}")
    await s.clock.sleep(SETTLE_STEPS_S)


async def payload_grab(s):
    attach, detach = PAYLOAD_TOPICS
    # Gazebo's attach joint closes as soon as the drone loads, so let go first. A one-off
    # publish from gz's command line can go out before it has found the plugin and be lost,
    # and taking off still joined to a box on a shelf 4 m away tumbles it, so say it a few times
    for _ in range(4):
        await s.gz_publish(detach, "gz.msgs.Empty", "unused: true")
        await s.clock.sleep(0.5)
    await take_off(s, CARRY_HEIGHT)
    await offboard_here(s)
    await go_to(s, SHELF_NORTH, 0.0, CARRY_HEIGHT)
    await hold(s, 5.0, "before")
    grab = SHELF_HEIGHT + PAYLOAD_SIZE + GRAB_CLEARANCE
    await go_to(s, SHELF_NORTH, 0.0, grab, tolerance=0.2)
    await to_the_claws(s, attach)
    s.mark("grab")
    for _ in range(3):
        await s.gz_publish(attach, "gz.msgs.Empty", "unused: true")
        await s.clock.sleep(0.3)
    await go_to(s, SHELF_NORTH, 0.0, CARRY_HEIGHT, timeout=60.0)
    await hold(s, CARRY_S, "carry")
    # set it down away from home before landing, the way the claws would: the stand-in joint
    # holds the box rigidly below the feet, and landing on the box (held or dropped) tips the
    # drone over
    await go_to(s, 0.0, DROP_EAST, CARRY_HEIGHT)
    await go_to(s, 0.0, DROP_EAST, RELEASE_HEIGHT, tolerance=0.35)
    s.mark("release")
    for _ in range(3):
        await s.gz_publish(detach, "gz.msgs.Empty", "unused: true")
        await s.clock.sleep(0.5)
    await s.clock.sleep(1.0)
    await go_to(s, 0.0, 0.0, RELEASE_HEIGHT, tolerance=0.35)
    await leave_offboard(s)
    await land(s)


def grade_payload(log, imu, c) -> list:
    grab, carry = log.when("grab"), window(log, "carry")
    before = window(log, "before")
    if grab is None or carry is None or before is None:
        return missing("payload grab")
    k = int(np.searchsorted(log.t, grab))
    after = log.window(grab, carry[1])
    sideways = float(np.hypot(*(log.position[after, :2] - log.position[k, :2]).T).max())
    limit = c.sim.payload.max_drift_m
    out = [grade.Finding("payload drift", sideways <= limit, sideways, limit, "m",
                         f"stayed within {sideways:.2f} m after picking it up")]  # fmt: skip
    # thrust goes as the speed squared, so the rotors show whether it came along
    lifted = float((log.rotor_speed[log.window(*carry)] ** 2).mean())
    empty = float((log.rotor_speed[log.window(*before)] ** 2).mean())
    mass, payload = c.model.get("mass_kg"), c.model.get("payload_kg")
    if mass and payload:
        expected = (mass + payload) / mass
        ratio = lifted / empty
        passed = abs(ratio - expected) <= LIFT_BAND * expected
        out.append(grade.Finding("payload lifted", passed, ratio, expected, "",
                                 f"the rotors' thrust grew {ratio - 1:.0%}, against "
                                 f"{expected - 1:.0%} for {payload * 1000:.0f} g"))  # fmt: skip
    return out


SCENARIOS = (
    Scenario("hover", hover, grade_hover, budget_s=240.0),
    Scenario("steps", steps, grade_steps, budget_s=180.0, params=steps_params),
    Scenario("top speed", top_speed, grade_top_speed, budget_s=300.0),
    Scenario("wind", wind, grade_wind, budget_s=240.0),
    Scenario("endurance", endurance, grade_endurance, budget_s=300.0),
    Scenario("payload grab", payload_grab, grade_payload, budget_s=360.0, prepare=place_payload),
)
