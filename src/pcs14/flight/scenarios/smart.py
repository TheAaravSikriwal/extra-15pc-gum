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
- spiral descent (base): from 40 m down a helix (8 m across, 1.5 m/s down, 4 m/s around), its
  setpoints streamed the way the companion computer would, then straight down for the last
  4 m. The path only: Gazebo has no vortex ring state for the helix to avoid
- lift (base): 20 m up, a hover in still air, then 30 m north into a column of air rising at
  4 m/s (the script turns the wind's upward part on while the drone is in it) and a hover
  there. The detector finds the column by the thrust it saves. In Gazebo that's only the push
  on the body; on a real drone the rotors gain more, which is the momentum-theory number
- mapping run (V): V's camera pointed straight down (the bracket would need a mapping position),
  a lawnmower grid 30 m up over the scenery step 6 put out, every third frame kept, and the
  orthomosaic built from the frames and the log's poses (pcs14.smart.ortho)
- mapping run, box moved (V): the same grid with the box moved 22 m, and the two orthomosaics
  differenced (pcs14.smart.change): it has to be flagged where it was and where it went, and
  nowhere else
- safe landing (V): asked to land on the shed, it picks the nearest safe spot on the world's
  height map (pcs14.smart.safespots), flies there and lands. The grade also asks what the
  mapping run's orthomosaic would have picked, and whether that spot is truly clear
- flow run (V): V's camera pointed straight down, 6 m up over a textured field (Gazebo's own
  ground is one flat color), around three sides of a 40 by 20 m rectangle at 3 m/s. The
  position comes from the frames alone (pcs14.smart.flow), with the true attitude tilted by an
  estimate's error and the true height given the TF-Luna's, and it has to stay within 5% of
  the distance flown of Gazebo's truth
- planned mission (mission): the plan `pcs14 smart` wrote from plain English (a local model,
  then the checker), approved here by the test script, which says so in the log, since on the
  drone the approving is mine. A plan the checker refused never gets approved, so never flies
"""

import asyncio
import math
from pathlib import Path

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


# --- the spiral descent -------------------------------------------------------------------

SPIRAL_START_M = 40.0
SPIRAL_STEP_S = 0.1  # between setpoints, on the sim's clock
SPIRAL_RADIUS_TOLERANCE_M = 1.5
SPIRAL_SINK_TOLERANCE_MS = 0.3


async def spiral_descent(s):
    from mavsdk.offboard import PositionNedYaw

    from pcs14.smart.spiral import Spiral

    await take_off(s, SPIRAL_START_M)
    await offboard_here(s)
    path = Spiral(start_m=SPIRAL_START_M, start_north=s.state.north, start_east=s.state.east)
    s.result.notes["spiral"] = {"start_m": path.start_m, "start_north": path.start_north,
                                "start_east": path.start_east}  # fmt: skip
    s.mark("spiral")
    start = s.clock.now
    while (t := s.clock.now - start) <= path.turning_s:
        north, east, height = path.at(t)
        await s.drone.offboard.set_position_ned(PositionNedYaw(north, east, -height, 0.0))
        await s.clock.sleep(SPIRAL_STEP_S)
    s.mark("straight")
    await leave_offboard(s)
    await s.drone.action.land()
    await _down(s)


def grade_spiral(log, imu, c) -> list:
    from pcs14.smart.spiral import Spiral, followed

    notes = c.notes.get("spiral", {})
    begin = log.when("spiral")
    if begin is None or not notes:
        return [grade.Finding("the spiral", False, None, None, "", "it never started")]
    path = Spiral(**notes)
    inside = log.window(begin, begin + path.turning_s)
    t = log.t[inside] - begin
    east, north, height = log.position[inside].T
    found = followed(t, north, east, height, path)
    return [
        grade.Finding("the helix", found.radius_error_m <= SPIRAL_RADIUS_TOLERANCE_M,
                      found.radius_error_m, SPIRAL_RADIUS_TOLERANCE_M, "m",
                      f"at most {found.radius_error_m:.1f} m off the circle"),
        grade.Finding("the sink rate",
                      abs(found.sink_ms - path.sink_ms) <= SPIRAL_SINK_TOLERANCE_MS,
                      found.sink_ms, path.sink_ms, "m/s",
                      f"sank at {found.sink_ms:.2f} m/s, asked for {path.sink_ms:g}"),
        grade.touchdown(log, c.sim.failures.max_touchdown_ms),
    ]  # fmt: skip


# --- soar mode's lift detector -------------------------------------------------------------

LIFT_HEIGHT_M = 20.0
LIFT_NORTH_M = 30.0
LIFT_UPDRAFT_MS = 4.0
LIFT_HOLD_S = 60.0  # soar mode is for waiting, so it can average a minute: a tenth of a newton


async def lift(s):
    from pcs14.flight.generate import WIND_TOPIC
    from pcs14.flight.scenarios.basic import hold

    await take_off(s, LIFT_HEIGHT_M)
    await offboard_here(s)
    await s.clock.sleep(4.0)
    await hold(s, LIFT_HOLD_S, "still")
    await go_to(s, LIFT_NORTH_M, 0.0, LIFT_HEIGHT_M, tolerance=1.0)
    await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", f"z: {LIFT_UPDRAFT_MS}")
    await s.clock.sleep(6.0)
    await hold(s, LIFT_HOLD_S, "lifted")
    await s.gz_publish(WIND_TOPIC, "gz.msgs.Vector3d", "z: 0")
    await go_to(s, 0.0, 0.0, LIFT_HEIGHT_M, tolerance=1.0)
    await leave_offboard(s)
    await s.drone.action.land()
    await _down(s)


def grade_lift(log, imu, c) -> list:
    import numpy as np

    from pcs14.smart import lift as detector

    def thrusts(name):
        inside = log.window(log.when(f"{name} start"), log.when(f"{name} end"))
        return np.array([detector.thrust_n(w, c.model["motor_constant"])
                         for w in log.rotor_speed[inside]])  # fmt: skip

    still, lifted = thrusts("still"), thrusts("lifted")
    deficit = float(still.mean() - lifted.mean())
    error = detector.standard_error(still, lifted)
    found = detector.is_lift(deficit, error)
    updraft = detector.updraft_in_sim(deficit, c.model["drag_area_m2"])
    saving = detector.power_saving_w(float(still.mean()), updraft)
    return [
        grade.Finding("lift found", found, deficit, None, "N",
                      f"{deficit:.2f} N less thrust in the column, {deficit / error:.1f} "
                      "standard errors past zero"),
        grade.Finding("the updraft", abs(updraft - LIFT_UPDRAFT_MS) <= 0.25 * LIFT_UPDRAFT_MS,
                      updraft, LIFT_UPDRAFT_MS, "m/s",
                      f"{updraft:.1f} m/s rising, by the push on the body (the sim's "
                      f"{LIFT_UPDRAFT_MS:g}); a real rotor would save about {saving:.0f} W "
                      "in it"),
    ]  # fmt: skip


# --- the mapping run ----------------------------------------------------------------------

MAP_HEIGHT_M = 30.0
MAP_LINES_EAST = (-14.0, -2.0, 10.0)  # m: the grid's lines, flown north and south in turn
MAP_NORTH = (5.0, 70.0)
MAP_AREA = ((-25.0, 25.0), (0.0, 75.0))  # east, north: the map's edges
MAP_M_PER_PX = 0.1


def moved_scenery():
    """Step 6's scenery with the box moved, for the second mapping run."""
    from pcs14.flight.scenarios.modules import SCENERY

    return tuple((n, BOX_MOVED_TO if n == "box" else p, size, color)
                 for n, p, size, color in SCENERY)  # fmt: skip


BOX_MOVED_TO = (8.0, 58.0, 0.6)  # from (-5, 40)


async def mapping_run(s, scenery=None, suffix: str = "mapping"):
    from pcs14.flight.scenarios.modules import CAMERA_EVERY, SCENERY, scenery_sdf

    for name, position, size, color in scenery or SCENERY:
        await s.spawn_sdf(scenery_sdf(name, (0, 0, 0), size, color).replace("'", '"'), name,
                          position)  # fmt: skip
    folder = s.exports / "camera" / f"{s.model}-{suffix}"
    recorder = s.record_camera(folder, CAMERA_EVERY)
    try:
        await take_off(s, MAP_HEIGHT_M)
        await offboard_here(s)
        s.mark("grid start")
        for k, east in enumerate(MAP_LINES_EAST):
            a, b = MAP_NORTH if k % 2 == 0 else MAP_NORTH[::-1]
            await go_to(s, a, east, MAP_HEIGHT_M, tolerance=1.0)
            await go_to(s, b, east, MAP_HEIGHT_M, tolerance=1.0)
        s.mark("grid end")
        await go_to(s, 0.0, 0.0, MAP_HEIGHT_M, tolerance=1.0)
        await leave_offboard(s)
        await s.drone.action.land()
        await _down(s)
    finally:
        recorder.close()
        s.result.notes["frames"] = list(recorder.saved)
        s.result.notes["frames folder"] = folder.as_posix()


def build_map(log, frames_folder, times, pitch_deg: float = 90.0, every: int = 1):
    """The orthomosaic from a run's saved frames (and their sim times) and its log's poses."""
    import numpy as np
    from PIL import Image

    from pcs14.flight.generate import CAMERA
    from pcs14.smart import ortho

    camera = ortho.Camera(width=1280, height=720, hfov_rad=1.15192)
    assert "<horizontal_fov>1.15192</horizontal_fov>" in CAMERA  # the same camera
    offset = (0.18, 0.0, 0.0)
    frames = []
    start, end = log.when("grid start"), log.when("grid end")
    for k, t in enumerate(times):
        if k % every or not (start <= t <= end):
            continue
        i = min(int(np.searchsorted(log.t, t)), len(log.t) - 1)
        pose = ortho.Pose.on_drone(log.position[i], log.attitude[i], offset,
                                   np.radians(pitch_deg))  # fmt: skip
        picture = np.asarray(Image.open(Path(frames_folder) / f"frame-{k:04d}.png").convert("RGB"))
        frames.append((picture, pose))
    return ortho.mosaic(frames, camera, *MAP_AREA, m_per_px=MAP_M_PER_PX)


def grade_mapping(log, imu, c) -> list:
    import numpy as np

    from pcs14.flight.scenarios.modules import SCENERY

    folder, times = c.notes.get("frames folder"), c.notes.get("frames", [])
    if not folder or not times:
        return [grade.Finding("the map", False, None, None, "", "no frames")]
    found = build_map(log, folder, times, every=2)
    out = [grade.Finding("the map", found.covered > 0.9, found.covered, 0.9, "",
                         f"{found.covered:.0%} of the area seen")]  # fmt: skip
    ground = found.color_at(east=20.0, north=5.0).astype(float)
    for name, (x, y, _), _size, color in SCENERY:
        want = np.array(color) * 255
        # the map's pixel nearest its own color within a meter of where it stands, nearer that
        # color than the ground's: it's on the map, and within a meter of the right place
        seen = found.nearest_color(east=x, north=y, color=want, within_m=1.0).astype(float)
        ok = np.linalg.norm(seen - want) < np.linalg.norm(seen - ground)
        words = f"at {x:g} m east, {y:g} m north: {tuple(int(v) for v in seen)}"
        out.append(grade.Finding(f"{name} on the map", ok, None, None, "", words))
    from PIL import Image

    Image.fromarray(found.image).save(Path(folder).parent / f"{Path(folder).name}.png")
    return out


# --- the nearest-safe-spot landing --------------------------------------------------------

SAFE_ASKED = (6.0, 25.0)  # east, north: on the shed
SAFE_HEIGHT_M = 20.0
SAFE_AREA = ((-25.0, 25.0), (0.0, 75.0))
MAP_ERROR_M = 1.0  # how far off the orthomosaic can put things


def scenery_boxes():
    from pcs14.flight.scenarios.modules import SCENERY

    return [(position, size) for _, position, size, _ in SCENERY]


def true_safe():
    from pcs14.smart import safespots

    return safespots.safe(safespots.height_map(scenery_boxes(), SAFE_AREA, 0.25))


async def safe_landing(s):
    from pcs14.flight.scenarios.modules import SCENERY, scenery_sdf
    from pcs14.smart import safespots

    for name, position, size, color in SCENERY:
        await s.spawn_sdf(scenery_sdf(name, (0, 0, 0), size, color).replace("'", '"'), name,
                          position)  # fmt: skip
    east, north = safespots.nearest(true_safe(), *SAFE_ASKED)
    s.result.notes["chosen"] = [east, north]
    await take_off(s, SAFE_HEIGHT_M)
    await offboard_here(s)
    s.mark("to the spot")
    await go_to(s, north, east, SAFE_HEIGHT_M, tolerance=1.0)
    await leave_offboard(s)
    await s.drone.action.land()
    await _down(s)


def grade_safe_landing(log, imu, c) -> list:
    import numpy as np

    from pcs14.smart import safespots

    chosen = c.notes.get("chosen")
    if not chosen:
        return [grade.Finding("the spot", False, None, None, "", "no spot was chosen")]
    end = log.position[-1]
    off = float(np.hypot(end[0] - chosen[0], end[1] - chosen[1]))
    truth = true_safe()
    out = [
        grade.Finding("landed on the spot", off <= LANDED_RADIUS_M, off, LANDED_RADIUS_M, "m",
                      f"{off:.1f} m from the spot it chose, {chosen[0]:.1f} m east and "
                      f"{chosen[1]:.1f} m north, "
                      f"{np.hypot(chosen[0] - SAFE_ASKED[0], chosen[1] - SAFE_ASKED[1]):.1f} m "
                      "from the shed it was asked to land on"),
        grade.Finding("clear where it landed", bool(truth.at(end[0], end[1])), None, None, "",
                      "clear of everything by the clearance" if truth.at(end[0], end[1])
                      else "too near something"),
        grade.touchdown(log, c.sim.failures.max_touchdown_ms),
    ]  # fmt: skip
    # what the mapping run's picture would have chosen, if there's one
    picture = Path(c.notes.get("map", "")) if c.notes.get("map") else None
    if picture is None:
        from pcs14.flight.scenarios.modules import SCENERY  # noqa: F401 (the same scenery)

        found = sorted(Path("outputs/flight-sim/camera").glob("*-mapping.png"))
        picture = found[0] if found else None
    if picture is not None and picture.is_file():
        from PIL import Image

        image = np.asarray(Image.open(picture).convert("RGB"))
        ground = image[-20:, -20:].reshape(-1, 3).mean(axis=0)  # the south-east corner: open
        blocked = safespots.obstacles_from_picture(image, ground)
        grid = safespots.Grid(blocked.astype(float), MAP_AREA[0][0], MAP_AREA[1][1], MAP_M_PER_PX)
        # the map places things to within about a meter (the mapping run's grade), so safe
        # spots read off it get that meter on top of the clearance
        from_map = safespots.safe(grid, clearance_m=3.0 + MAP_ERROR_M, step_m=0.5)
        spot = safespots.nearest(from_map, *SAFE_ASKED)
        clear = bool(truth.at(*spot))
        share = float(from_map.values.mean())
        out.append(grade.Finding("the map's choice", clear, None, None, "",
                                 f"the orthomosaic would have picked {spot[0]:.1f} m east, "
                                 f"{spot[1]:.1f} m north, which is "
                                 f"{'clear' if clear else 'not clear'} in truth; it calls "
                                 f"{share:.0%} of the area safe, the true map "
                                 f"{float(truth.values.mean()):.0%}"))  # fmt: skip
    return out


# --- change detection ---------------------------------------------------------------------

CHANGE_RADIUS_M = 1.5


async def mapping_run_moved(s):
    await mapping_run(s, moved_scenery(), "mapping-moved")


def grade_change(log, imu, c) -> list:
    import numpy as np
    from PIL import Image

    from pcs14.smart import change
    from pcs14.smart.ortho import Mosaic

    folder, times = c.notes.get("frames folder"), c.notes.get("frames", [])
    first = Path(folder).parent / Path(folder).name.replace("-mapping-moved", "-mapping.png")
    if not folder or not times or not first.is_file():
        words = "this needs the first mapping run's map, and frames of its own"
        return [grade.Finding("both maps", False, None, None, "", words)]
    after = build_map(log, folder, times, every=2)
    Image.fromarray(after.image).save(Path(folder).parent / f"{Path(folder).name}.png")
    before = Mosaic(np.asarray(Image.open(first).convert("RGB")), MAP_AREA[0][0],
                    MAP_AREA[1][1], MAP_M_PER_PX, 1.0)  # fmt: skip
    blobs = change.changes(before, after)

    def near(east, north):
        # a moved thing brings its shadow along, so everything around the spot is the one change
        return [b for b in blobs if np.hypot(b.east - east, b.north - north) <= CHANGE_RADIUS_M]

    was, went = near(-5.0, 40.0), near(*BOX_MOVED_TO[:2])
    others = [b for b in blobs if b not in was and b not in went]
    out = [
        grade.Finding("where it was", bool(was), None, None, "",
                      "flagged where the box was" if was else "missed where the box was"),
        grade.Finding("where it went", bool(went), None, None, "",
                      "flagged where the box went" if went else "missed where the box went"),
        grade.Finding("nothing else", not others, len(others), 0, "",
                      "nothing else flagged" if not others else
                      "also flagged: " + ", ".join(f"{b.east:.0f} m east, {b.north:.0f} m north "
                                                   f"({b.area_m2:.1f} m^2)" for b in others)),
    ]  # fmt: skip
    return out


# --- GPS-free flight's estimate -----------------------------------------------------------

FLOW_HEIGHT_M = 6.0  # inside the TF-Luna's 8 m, which the estimate needs for its height
FLOW_PATH = ((40.0, 0.0), (40.0, 20.0), (0.0, 20.0))  # (north, east) of each corner, in turn
FLOW_SPEED_MS = 3.0  # slow, the way flow-only flight is: at 15 m/s the frames stopped matching
FLOW_FIELD = (10.0, 20.0, 70.0)  # east and north of the textured field's middle, and its side
FLOW_TEXTURE_PX = 4096
FLOW_HEIGHT_NOISE = 0.02  # the TF-Luna's +-2% from 3 to 8 m, taken as one standard deviation
FLOW_TILT_NOISE_DEG = 0.5  # an attitude estimate's error, added to the sim's true attitude
FLOW_MAX_DRIFT = 0.05  # of the distance flown
FLOW_FROM_M = 10.0  # the worst drift counts from here, once there's a distance to be 5% of
LANDED_HEIGHT_M = 0.074  # the model's middle above the ground when it sits there


def field_texture(path, size_px: int = FLOW_TEXTURE_PX, seed: int = 24):
    """A field for the flow run to look at: noise with detail at every scale (its spectrum
    falls off as one over the frequency), colored from bare soil through grass to dry grass.
    Gazebo's default ground is one flat color, which gives the correlation nothing."""
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(seed)
    k = np.hypot(np.fft.fftfreq(size_px)[:, None], np.fft.rfftfreq(size_px)[None, :])
    spectrum = np.fft.rfft2(rng.standard_normal((size_px, size_px)).astype(np.float32))
    spectrum /= (k + 4.0 / size_px) ** 0.9
    n = np.fft.irfft2(spectrum, s=(size_px, size_px))
    lo, hi = np.percentile(n, (1, 99))
    n = np.clip((n - lo) / (hi - lo), 0.0, 1.0)
    palette = np.array([(58, 48, 34), (82, 104, 52), (160, 146, 98)], float)
    x = n * (len(palette) - 1)
    i = np.minimum(x.astype(int), len(palette) - 2)
    f = (x - i)[..., None]
    Image.fromarray((palette[i] * (1 - f) + palette[i + 1] * f).astype(np.uint8)).save(path)


def field_sdf(texture) -> str:
    """The textured field: a flat plane a centimeter over Gazebo's own ground, seen only."""
    side = FLOW_FIELD[2]
    return (
        '<?xml version="1.0"?><sdf version="1.9"><model name="field"><static>true</static>'
        '<link name="l"><visual name="v"><geometry><plane><normal>0 0 1</normal>'
        f"<size>{side:g} {side:g}</size></plane></geometry><material>"
        "<ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse><specular>0 0 0 1</specular>"
        f"<pbr><metal><albedo_map>{Path(texture).as_posix()}</albedo_map>"
        "<roughness>1</roughness><metalness>0</metalness></metal></pbr>"
        "</material></visual></link></model></sdf>"
    )


async def fly_line(s, north: float, east: float, height: float, speed_ms: float):
    """Flies straight to a point at `speed_ms`, its position setpoint carried along the line
    the way the spiral's is, then settles there."""
    from mavsdk.offboard import PositionNedYaw

    heading = s.state.heading
    n0, e0 = s.state.north, s.state.east
    length = math.hypot(north - n0, east - e0)
    start = s.clock.now
    while (gone := (s.clock.now - start) * speed_ms) < length:
        f = gone / length
        await s.drone.offboard.set_position_ned(
            PositionNedYaw(n0 + f * (north - n0), e0 + f * (east - e0), -height, heading)
        )
        await s.clock.sleep(SPIRAL_STEP_S)
    await go_to(s, north, east, height, tolerance=0.5)


async def flow_run(s):
    from pcs14.flight.scenarios.modules import CAMERA_EVERY

    field = s.folder / "field"
    field.mkdir(parents=True, exist_ok=True)
    field_texture(field / "field.png")
    (field / "model.sdf").write_text(field_sdf(field / "field.png"), "utf-8")
    await s.spawn(field / "model.sdf", "field", (FLOW_FIELD[0], FLOW_FIELD[1], 0.01))
    if (pose := s.true_pose(s.entity)) is not None:
        s.result.notes["landed height"] = pose[0][2]
    folder = s.exports / "camera" / f"{s.model}-flow"
    recorder = s.record_camera(folder, CAMERA_EVERY)
    try:
        await take_off(s, FLOW_HEIGHT_M)
        await offboard_here(s)
        s.mark("flow start")
        for north, east in FLOW_PATH:
            await fly_line(s, north, east, FLOW_HEIGHT_M, FLOW_SPEED_MS)
        s.mark("flow end")
        await go_to(s, 0.0, 0.0, FLOW_HEIGHT_M, tolerance=1.0)
        await leave_offboard(s)
        await s.drone.action.land()
        await _down(s)
    finally:
        recorder.close()
        s.result.notes["frames"] = list(recorder.saved)
        s.result.notes["frames folder"] = folder.as_posix()


def _quat_multiply(a, b):
    """Hamilton product of two (x, y, z, w) quaternions."""
    import numpy as np

    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ])  # fmt: skip


def flow_sensors(log, times, landed_m: float, seed: int = 24):
    """At each frame's time: the drone's true (east, north), and what its own sensors would
    say, its attitude (the truth, tilted by an estimate's error) and the rangefinder's height
    (the truth above the ground, with the TF-Luna's error)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    truth, attitudes, heights = [], [], []
    sigma = np.radians(FLOW_TILT_NOISE_DEG)
    for t in times:
        i = int(np.clip(np.searchsorted(log.t, t), 1, len(log.t) - 1))
        f = float(np.clip((t - log.t[i - 1]) / (log.t[i] - log.t[i - 1]), 0.0, 1.0))
        position = log.position[i - 1] * (1 - f) + log.position[i] * f
        q0, q1 = log.attitude[i - 1], log.attitude[i]
        q = q0 * (1 - f) + (q1 if np.dot(q0, q1) >= 0 else -q1) * f
        q = q / np.linalg.norm(q)
        rx, ry = rng.normal(0.0, sigma, 2)
        angle = np.hypot(rx, ry)
        axis = np.array([rx, ry, 0.0]) / angle if angle else np.zeros(3)
        tilt = np.append(axis * np.sin(angle / 2), np.cos(angle / 2))
        truth.append(position[:2])
        attitudes.append(_quat_multiply(q, tilt))
        heights.append((position[2] + landed_m) * (1 + rng.normal(0.0, FLOW_HEIGHT_NOISE)))
    return np.array(truth), attitudes, heights


def grade_flow(log, imu, c) -> list:
    import json

    import numpy as np
    from PIL import Image

    from pcs14.flight.generate import CAMERA
    from pcs14.smart import flow, ortho

    folder, times = c.notes.get("frames folder"), c.notes.get("frames", [])
    start, end = log.when("flow start"), log.when("flow end")
    picked = [(k, t) for k, t in enumerate(times) if start is not None and start <= t <= end]
    if len(picked) < 20:
        words = "too few frames between the start and the end of the path"
        return [grade.Finding("frames", False, len(picked), 20, "", words)]
    camera = ortho.Camera(width=1280, height=720, hfov_rad=1.15192)
    assert "<horizontal_fov>1.15192</horizontal_fov>" in CAMERA  # the same camera
    landed = float(c.notes.get("landed height", LANDED_HEIGHT_M))
    truth, attitudes, heights = flow_sensors(log, [t for _, t in picked], landed)
    pictures = (np.asarray(Image.open(Path(folder) / f"frame-{k:04d}.png").convert("RGB"))
                for k, _ in picked)  # fmt: skip
    found = flow.track(pictures, attitudes, heights, camera, np.radians(90.0),
                       offset=(0.18, 0.0, 0.0))  # fmt: skip
    truth = truth - truth[0]
    flown = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(truth, axis=0).T))])
    off = np.hypot(*(found - truth).T)
    far = flown >= FLOW_FROM_M
    worst = float((off[far] / flown[far]).max()) if far.any() else float("nan")
    drift = float(off[-1] / flown[-1])
    (Path(folder).parent / f"{Path(folder).name}-track.json").write_text(json.dumps({
        "t": [t for _, t in picked], "truth": truth.round(3).tolist(),
        "found": found.round(3).tolist(), "flown_m": flown.round(3).tolist(),
    }), "utf-8")  # fmt: skip
    return [
        grade.Finding("drift at the end", drift < FLOW_MAX_DRIFT, drift, FLOW_MAX_DRIFT, "",
                      f"{off[-1]:.2f} m off after {flown[-1]:.0f} m flown ({drift:.1%})"),
        grade.Finding("worst drift", worst < FLOW_MAX_DRIFT, worst, FLOW_MAX_DRIFT, "",
                      f"at worst {worst:.1%} of the distance flown, past the first "
                      f"{FLOW_FROM_M:g} m"),
    ]  # fmt: skip


SCENARIOS = (
    Scenario("land now", land_now, grade_land_now, budget_s=180.0),
    Scenario("back to start", back_to_start, grade_back_to_start, budget_s=180.0),
    Scenario("land here", land_here, grade_land_here, budget_s=180.0),
    Scenario("turn back", turn_back, grade_turn_back, budget_s=420.0),
    Scenario("planned mission", planned_mission, grade_planned_mission, budget_s=600.0),
    Scenario("spiral descent", spiral_descent, grade_spiral, budget_s=240.0),
    Scenario("lift", lift, grade_lift, budget_s=240.0),
    Scenario(
        "mapping run, box moved",
        mapping_run_moved,
        grade_change,
        budget_s=600.0,
        camera=True,
        camera_pitch_deg=90.0,
    ),
    Scenario("safe landing", safe_landing, grade_safe_landing, budget_s=240.0),
    Scenario("flow run", flow_run, grade_flow, budget_s=420.0, camera=True, camera_pitch_deg=90.0),
    Scenario(
        "mapping run",
        mapping_run,
        grade_mapping,
        budget_s=600.0,
        camera=True,
        camera_pitch_deg=90.0,
    ),
)
