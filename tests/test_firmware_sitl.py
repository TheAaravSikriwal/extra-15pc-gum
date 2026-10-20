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
