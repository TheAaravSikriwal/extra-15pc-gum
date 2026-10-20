"""My firmware flying the generated base model in Gazebo Harmonic, through its sim layer. Like
the PX4 flights, these only run where the tools are (WSL2 Ubuntu on the PC, after
scripts/setup-ubuntu.sh and scripts/build-firmware.sh); everywhere else they skip."""

import asyncio
from pathlib import Path

import pytest

from pcs14.flight import firmware, run

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "outputs" / "flight-sim"
TOOLS = run.toolchain()
MISSING = TOOLS.missing()
if not firmware.sitl_binary().exists():
    MISSING.append("no pcs14_sitl (scripts/build-firmware.sh)")

pytestmark = [
    pytest.mark.sitl,
    pytest.mark.skipif(bool(MISSING), reason="; ".join(MISSING) or "everything is here"),
    pytest.mark.skipif(
        not (EXPORTS / "models" / "pcs14_base" / "firmware.txt").exists(),
        reason="no generated models with firmware.txt",
    ),
]


def test_rate_mode_holds_the_drone_level_for_10_s():
    """Arm, climb, then hover on the throttle with the sticks centered: rate mode holds the
    rates at zero, so the drone stays level-ish (step 5, task 4)."""
    check = asyncio.run(firmware.rate_check(TOOLS, EXPORTS, "pcs14_base", instance=6))
    assert check.seconds >= 12.9
    assert check.end_height_m > 1.0, check.lines[-5:]
    assert check.worst_tilt_deg < 5.0, check.lines[-5:]


def test_its_log_reads_like_px4s():
    """The same flight's ULog, through the graders' own reader (step 5, task 5)."""
    from pcs14.flight import ulog

    check = asyncio.run(firmware.rate_check(TOOLS, EXPORTS, "pcs14_base", hold_s=3.0,
                                            instance=6))  # fmt: skip
    assert check.log is not None and check.log.exists()
    flight = ulog.flight_log(ulog.read(check.log))
    names = [name for _, name in flight.events]
    assert "armed" in names and "took off" in names, flight.events
    assert flight.position[:, 2].max() > 1.0  # it climbed, by Gazebo's own account
    assert flight.rotor_speed.max() > 400
    assert ulog.tilt_of(flight.attitude).max() < 0.1  # rad


def test_mavsdk_connects_reads_health_and_arms():
    """The flight sim's own runner, with my firmware in PX4's place: MAVSDK connects through the
    relay, sees a healthy vehicle with a home, sets its rates and a parameter, and arms it
    (step 5, task 6)."""

    async def fly():
        s = run.Session(TOOLS, "pcs14_base", {"MC_ROLL_P": 9.0}, EXPORTS, "mavlink-check",
                        instance=6, firmware="mine")  # fmt: skip
        try:
            await s.start()  # waits for the health and the home position, as with PX4
            await s.drone.action.arm()
            armed = await s.clock.until(lambda: s.state.armed, 5.0)
            mode = s.state.mode
            await s.drone.action.disarm()
            return armed, mode
        finally:
            await s.stop()

    armed, mode = asyncio.run(fly())
    assert armed
    assert mode == "ACRO"


def test_altitude_mode_climbs_holds_and_comes_down():
    """Altitude mode on the sticks over MAVLink, the way the steps scenario flies PX4: climb on
    the stick, hold the height with it centered, then come down, land and disarm itself
    (step 5, task 7). Graded from Gazebo's ground truth in my firmware's own log."""
    import numpy as np

    from pcs14.flight import ulog
    from pcs14.flight.scenarios.basic import Sticks, window

    async def fly():
        s = run.Session(TOOLS, "pcs14_base", {}, EXPORTS, "altitude-check", instance=6,
                        firmware="mine")  # fmt: skip
        try:
            await s.start()
            async with Sticks(s) as sticks:
                await s.drone.manual_control.start_altitude_control()
                await s.drone.action.arm()
                await sticks.move(z=0.8)
                climbed = await s.clock.until(lambda: s.state.height > 5.0, 20.0)
                await sticks.move(z=0.5)
                await s.clock.sleep(3.0)
                s.mark("hold start")
                await s.clock.sleep(10.0)
                s.mark("hold end")
                await sticks.move(z=0.0)
                disarmed = await s.clock.until(lambda: not s.state.armed, 40.0)
            return climbed, disarmed, s
        finally:
            await s.stop()

    climbed, disarmed, s = asyncio.run(fly())
    assert climbed and disarmed
    flight = ulog.flight_log(ulog.read(s.result.log), s.result.marks)
    start, end = window(flight, "hold")
    inside = (flight.t >= start) & (flight.t <= end)
    heights = flight.position[inside, 2]
    assert heights.max() - heights.min() < 0.6, (heights.min(), heights.max())
    assert np.degrees(ulog.tilt_of(flight.attitude[inside])).max() < 2.0
    assert flight.position[-1, 2] < 0.2  # back on the ground


def test_the_safety_monitor_cuts_a_hung_flight_controller():
    """Hovering at 5 m, my firmware's process freezes (SIGSTOP: a hung flight controller). The
    safety monitor, on its own IMU, sees the heartbeat stop and cuts within its 0.25 s
    timeout, and the drone falls instead of hovering on at its last motor speeds (step 5,
    task 10)."""
    import os
    import signal
    import time

    async def fly():
        s = run.Session(TOOLS, "pcs14_base", {}, EXPORTS, "hang-check", instance=6,
                        firmware="mine")  # fmt: skip
        try:
            await s.start()
            truth = firmware.GroundTruth(run.gz_bindings(), s.partition, s.entity)
            await s.drone.action.set_takeoff_altitude(5.0)
            await s.drone.action.arm()
            await s.drone.action.takeoff()
            await s.clock.until(lambda: s.state.height > 4.8, 30.0)
            await s.clock.sleep(3.0)
            t0, h0, _ = truth.now()
            sitl = next(p for name, p in s._processes if name == "sitl")
            os.kill(sitl.pid, signal.SIGSTOP)
            time.sleep(1.5)  # wall time: the flight controller's clock is frozen with it
            _, h1, _ = truth.now()
            os.kill(sitl.pid, signal.SIGCONT)
        finally:
            await s.stop()
        return t0, h0, h1, s.result.notes.get("monitor", [])

    t0, h0, h1, said = asyncio.run(fly())
    cuts = [line for line in said if line.startswith("cut flight controller silent")]
    assert cuts, said
    cut_at = float(cuts[0].rsplit(" ", 1)[1])
    assert 0 < cut_at - t0 < 0.4
    assert h0 > 4.5 and h1 < 1.0  # it came down


def test_the_ground_station_sees_my_firmware_and_tunes_it_live():
    """The ground station on my firmware's ground station link (PX4's port, 14550 plus the
    instance), next to the runner's own MAVSDK: it gets the telemetry and the limits profile,
    and a gain it sets reaches the firmware (step 5, task 13)."""
    from pcs14.ground.station import Station

    async def fly():
        s = run.Session(TOOLS, "pcs14_base", {}, EXPORTS, "ground-check", instance=6,
                        firmware="mine")  # fmt: skip
        station = Station("udpin://0.0.0.0:14556", grpc_port=50076)
        try:
            await s.start()
            await station.start(timeout_s=30.0)
            await s.clock.sleep(2.0)
            seen = station.snapshot()
            echoed = await station.set_param("MC_ROLL_P", 7.5)
            runner_reads = await s.drone.param.get_param_float("MC_ROLL_P")
        finally:
            await station.stop()
            await s.stop()
        return seen, echoed, runner_reads

    seen, echoed, runner_reads = asyncio.run(fly())
    assert seen["connected"] and seen["limits"] == "max"
    assert "height_m" in seen and seen["armed"] is False
    assert echoed == 7.5 and runner_reads == 7.5
