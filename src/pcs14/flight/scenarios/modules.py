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
- halow range (V): 10 m up, out 7 km north at 15 m/s and back, with the ground station's link
  through the HaLow model (pcs14.flight.run.HalowLink): what reaches the laptop fades with
  distance as the model says, and the drone flies on regardless, because its pilot's link and
  its companion computer's aren't HaLow
- camera (V): V's camera on the model (the Camera Module 3, 720p at 30 frames a second), a few
  simple things along the way (a shed, some trees, a box), 20 m up and 60 m north at 5 m/s and
  back, every third frame saved for the live video's encodes
"""

import asyncio
import math
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
# low enough that the link's edge comes inside a battery's flight: 10 m up, the model's slowest
# rate gives out about 5.5 km away over flat ground
HALOW_HEIGHT_M = 10.0
HALOW_OUT_M = 7000.0
HALOW_SPEED_MS = 15.0


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


# --- HaLow's range ------------------------------------------------------------------------


async def halow_range(s):
    from mavsdk.offboard import PositionNedYaw, VelocityNedYaw

    from pcs14.flight.run import GCS_PORT, HalowLink
    from pcs14.flight.scenarios.basic import leave_offboard, offboard_here
    from pcs14.modules.halow import Link

    model = Link()

    def distance() -> float:
        return math.hypot(s.state.north, s.state.east)

    def loss() -> float:
        return model.packet_loss(max(distance(), 1.0), max(s.state.height, 1.0))

    link = HalowLink(GCS_PORT + s.instance, loss=loss, now=lambda: s.clock.now, distance=distance)
    await link.start()
    try:
        await take_off(s, HALOW_HEIGHT_M)
        await offboard_here(s)
        heading = s.state.heading
        s.mark("out")
        await s.drone.offboard.set_velocity_ned(VelocityNedYaw(HALOW_SPEED_MS, 0, 0, heading))
        await s.clock.until(lambda: s.state.north >= HALOW_OUT_M, 2 * HALOW_OUT_M / HALOW_SPEED_MS)
        s.mark("back")
        await s.drone.offboard.set_velocity_ned(VelocityNedYaw(-HALOW_SPEED_MS, 0, 0, heading))
        await s.clock.until(lambda: s.state.north <= 30.0, 2 * HALOW_OUT_M / HALOW_SPEED_MS)
        await s.drone.offboard.set_position_ned(PositionNedYaw(0, 0, -HALOW_HEIGHT_M, heading))
        await s.clock.until(lambda: distance() < 2.0 and s.state.speed < 0.5, 60.0)
        await leave_offboard(s)
        await s.drone.action.land()
        await s.clock.until(lambda: not s.state.in_air, 90.0)
    finally:
        link.close()
        s.result.notes["link"] = [(b.t, b.distance_m, b.sent, b.delivered) for b in link.seconds]


def half_lost_m(height_m: float) -> float:
    """Where the model loses half the packets on its slowest rate: 2 log10(5), 1.4 dB, under
    its rated sensitivity (where it loses a tenth)."""
    from pcs14.modules.halow import Link

    return Link().reach_m(0, height_m, margin_db=-2 * math.log10(5))


def grade_link(seconds, height_m: float = HALOW_HEIGHT_M) -> list:
    """Where the share of the drone's datagrams reaching the laptop first falls under half,
    against where the model loses half of them."""
    edge = half_lost_m(height_m)
    out = [(d, got / sent) for _, d, sent, got in seconds if sent >= 5]
    faded = next((d for d, share in out if share < 0.5), None)
    if faded is None:
        return [grade.Finding("link fades where the model says", False, None, edge, "m",
                              "the link never faded")]  # fmt: skip
    ok = abs(faded - edge) / edge < 0.1
    return [grade.Finding("link fades where the model says", ok, faded, edge, "m",
                          f"under half got through from {faded:.0f} m, against the model's "
                          f"{edge:.0f} m")]  # fmt: skip


def grade_halow_range(log, imu, c) -> list:
    import numpy as np

    # the height it actually flew out at, for the model
    out_at, back_at = log.when("out"), log.when("back")
    height = HALOW_HEIGHT_M
    if out_at is not None and back_at is not None:
        leg = (log.t > out_at) & (log.t < back_at)
        if leg.any():
            height = float(np.median(log.position[leg, 2]))
    out = grade_link(c.notes.get("link", []), height)
    out.append(grade.ends_safely(log, 5.0))
    return out


# --- the camera ---------------------------------------------------------------------------

CAMERA_HEIGHT_M = 20.0
CAMERA_OUT_M = 60.0
CAMERA_SPEED_MS = 5.0
CAMERA_EVERY = 3  # of the camera's 30 frames a second: 10 a second saved
# Gazebo's frame: x east, y north, z up; size in m, color as red, green, blue
SCENERY = (
    ("shed", (6.0, 25.0, 1.5), (4.0, 3.0, 3.0), (0.55, 0.45, 0.38)),
    ("box", (-5.0, 40.0, 0.6), (1.2, 1.2, 1.2), (0.9, 0.31, 0.63)),
    *((f"tree_{k}", (x, y, 2.5), (0.8, 0.8, 5.0), (0.2, 0.45, 0.25))
      for k, (x, y) in enumerate(((-8, 15), (9, 50), (-3, 62), (12, 35), (-12, 30)))),
)  # fmt: skip


def scenery_sdf(name: str, position, size, color) -> str:
    """A static box, for the camera to have something to look at."""
    x, y, z = position
    c = " ".join(f"{v:g}" for v in color) + " 1"
    sx, sy, sz = size
    return (f'<sdf version="1.9"><model name="{name}"><static>true</static>'
            f"<pose>{x:g} {y:g} {z:g} 0 0 0</pose><link name='l'><visual name='v'>"
            f"<geometry><box><size>{sx:g} {sy:g} {sz:g}</size></box></geometry>"
            f"<material><ambient>{c}</ambient><diffuse>{c}</diffuse></material>"
            "</visual></link></model></sdf>")  # fmt: skip


async def camera(s):
    from mavsdk.offboard import PositionNedYaw

    from pcs14.flight.scenarios.basic import go_to, leave_offboard, offboard_here

    for name, position, size, color in SCENERY:
        # the spawn's own pose wins over the model's, so it goes in the spawn
        await s.spawn_sdf(scenery_sdf(name, (0, 0, 0), size, color).replace("'", '"'), name,
                          position)  # fmt: skip
    folder = s.exports / "camera" / s.model
    recorder = s.record_camera(folder, CAMERA_EVERY)
    try:
        await take_off(s, CAMERA_HEIGHT_M)
        await offboard_here(s)
        # facing north, the way it flies: Gazebo spawns the model facing east, which would have
        # it fly sideways with the camera looking at empty ground
        await s.drone.offboard.set_position_ned(PositionNedYaw(0, 0, -CAMERA_HEIGHT_M, 0.0))
        await s.clock.until(lambda: abs(((s.state.heading + 180) % 360) - 180) < 3.0, 20.0)
        s.mark("look")
        await s.drone.offboard.set_position_ned(
            PositionNedYaw(CAMERA_OUT_M, 0, -CAMERA_HEIGHT_M, 0.0))  # fmt: skip
        await s.clock.until(lambda: s.state.north >= CAMERA_OUT_M - 1.0, 60.0)
        # (the position setpoint has no speed in it: my firmware flies it at its own pace)
        await s.clock.sleep(2.0)
        await go_to(s, 0.0, 0.0, CAMERA_HEIGHT_M, tolerance=1.0)
        await leave_offboard(s)
        await s.drone.action.land()
        await s.clock.until(lambda: not s.state.in_air, 90.0)
    finally:
        recorder.close()
        s.result.notes["frames"] = list(recorder.saved)


def grade_frames(times, every: int = CAMERA_EVERY, rate_hz: float = 30.0) -> list:
    import numpy as np

    count = len(times)
    out = [grade.Finding("camera frames", count >= 50, count, 50, "",
                         f"{count} frames saved")]  # fmt: skip
    if count < 2:
        return out
    gaps = np.diff(np.asarray(times))
    rate = 1.0 / float(np.median(gaps))
    want = rate_hz / every
    words = f"{rate:.1f} saved a second of the sim's, against {want:g}"
    out.append(grade.Finding("camera rate", abs(rate - want) <= 0.1 * want, rate, want, "Hz",
                             words))  # fmt: skip
    return out


def grade_camera(log, imu, c) -> list:
    return grade_frames(c.notes.get("frames", [])) + [grade.ends_safely(log, 5.0)]


SCENARIOS = (
    # no `failure` mark: the batch's trigger check reads the flight controller's IMU, which is
    # frozen here; grade_hung reads the monitor's own triggers instead
    Scenario("hung flight controller", hung_flight_controller, grade_hung, budget_s=180.0,
             healthy=False),
    *(Scenario(f"drop from {h:g} m", drop_from(h), grade_drop_height, budget_s=180.0,
               healthy=False, failure="terminate") for h in DROP_HEIGHTS),
    Scenario("chute rule", chute_rule, grade_chute_rule, budget_s=240.0,
             params=chute_rule_params),
    Scenario("camera", camera, grade_camera, budget_s=240.0, camera=True),
    Scenario("halow range", halow_range, grade_halow_range,
             budget_s=2 * HALOW_OUT_M / HALOW_SPEED_MS + 300.0),
)  # fmt: skip
