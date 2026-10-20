"""The plain flights: the smoke flight that proves the runner works, and the moves every other
scenario is built from.

PX4 holds its position by itself after taking off (its Hold mode). Moving to a point uses
offboard position setpoints, which MAVSDK keeps resending; leaving offboard goes back to Hold.
A script's marks come in pairs, "<name> start" and "<name> end", never a bare name that could
be one of PX4's modes.
"""

import asyncio
import contextlib
import math

from pcs14.flight import grade
from pcs14.flight.scenarios import Aborted, Scenario

SMOKE_HEIGHT = 2.5  # m
SMOKE_HOLD_S = 10.0
SETTLE_S = 3.0  # after reaching a height or a point, before a hold counts
GROUNDED_M = 0.3  # m: under this after a take-off, it never left the ground
STILL_MS = 0.3  # m/s: slower than this counts as stopped


async def take_off(s, height: float, timeout: float = 60.0):
    """Arms, climbs to `height` with PX4's takeoff mode, and lets it settle."""
    await s.drone.action.set_takeoff_altitude(height)
    await s.drone.action.arm()
    s.mark("arm")
    await s.drone.action.takeoff()
    if not await s.clock.until(lambda: s.state.height >= height - 0.2, timeout):
        if s.state.in_air and s.state.height < GROUNDED_M:
            # PX4 thinks it's flying, with the motors run up, and the model never moved: in
            # the batch of 2026-10-20 this happened only with two runs at once, when Gazebo
            # never got PX4's motor commands. That's the sim failing, not the drone
            from pcs14.flight.run import SimError

            raise SimError("PX4 ran the motors up for take-off and the model never moved")
        raise Aborted(f"it never climbed to {height:g} m (got to {s.state.height:.1f} m)")
    await s.clock.sleep(SETTLE_S)


async def hold(s, seconds: float, name: str = "hold"):
    """Waits `seconds` where it is, marked "<name> start" and "<name> end"."""
    s.mark(f"{name} start")
    await s.clock.sleep(seconds)
    s.mark(f"{name} end")


async def offboard_here(s):
    """Switches to offboard, holding the current position and heading."""
    from mavsdk.offboard import PositionNedYaw

    from pcs14.flight.run import read_heading

    heading = await read_heading(s.drone, s.state)
    st = s.state
    await s.drone.offboard.set_position_ned(PositionNedYaw(st.north, st.east, st.down, heading))
    await s.drone.offboard.start()


async def go_to(s, north: float, east: float, height: float, tolerance=0.5, timeout=90.0):
    """Flies (in offboard) to a point north and east of home, `height` m up, and settles."""
    from mavsdk.offboard import PositionNedYaw

    await s.drone.offboard.set_position_ned(PositionNedYaw(north, east, -height, s.state.heading))

    def there():
        st = s.state
        off = math.dist((st.north, st.east, st.height), (north, east, height))
        return off <= tolerance and st.speed <= STILL_MS

    if not await s.clock.until(there, timeout):
        raise Aborted(f"it never got to {north:g} m north, {east:g} m east, {height:g} m up")
    await s.clock.sleep(SETTLE_S)


async def leave_offboard(s):
    """Back to PX4's Hold."""
    await s.drone.action.hold()
    await s.clock.until(lambda: s.state.mode.endswith("HOLD"), 5.0)


async def land(s, timeout: float = 120.0):
    """Lands where it is and waits for PX4 to disarm."""
    await s.drone.action.land()
    s.mark("land sent")
    await disarmed(s, timeout)


async def disarmed(s, timeout: float):
    if not await s.clock.until(lambda: not s.state.armed, timeout):
        raise Aborted(f"it didn't land and disarm within {timeout:g} s")


async def down(s, timeout: float = 90.0, after_s: float = 3.0):
    """Waits for it to be on the ground by PX4's estimate, however it got there."""
    if not await s.clock.until(lambda: s.state.height < 0.5 and not s.state.in_air, timeout):
        raise Aborted(f"it was still in the air {timeout:g} s later")
    await s.clock.sleep(after_s)


class Sticks:
    """A pilot's sticks over MAVLink, resent 20 times a second like a real transmitter's: x
    forward, y right, z throttle (0.5 holds height in altitude mode), r yaw."""

    def __init__(self, s):
        self.s = s
        self.x = self.y = self.r = 0.0
        self.z = 0.5
        self._task = None

    async def send(self):
        await self.s.drone.manual_control.set_manual_control_input(self.x, self.y, self.z, self.r)

    async def move(self, **sticks):
        """Moves sticks (x, y, z or r) and sends them at once, not at the next resend: at a
        faster sim speed the resend's real-time gap is a longer stretch of sim time."""
        for name, value in sticks.items():
            setattr(self, name, value)
        await self.send()

    async def _send(self):
        while True:
            await self.send()
            await asyncio.sleep(0.05)

    async def __aenter__(self):
        self._task = asyncio.create_task(self._send())
        await asyncio.sleep(0.2)
        return self

    async def __aexit__(self, *exc):
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task


async def smoke(s):
    await take_off(s, SMOKE_HEIGHT)
    await hold(s, SMOKE_HOLD_S)
    await land(s)


def window(log, name: str):
    """The (start, end) of a marked stretch, or None."""
    start, end = log.when(f"{name} start"), log.when(f"{name} end")
    if start is None or end is None:
        return None
    return start, end


def hold_window(log, name: str = "hold"):
    return window(log, name)


def height_at(log, t: float) -> float:
    k = min(int(log.t.searchsorted(t)), len(log.t) - 1)
    return float(log.position[k, 2])


def missing(what: str) -> list:
    return [grade.Finding(what, False, None, None, "", f"the flight never got to the {what}")]


def grade_smoke(log, imu, context) -> list:
    hover = context.sim.hover
    found = window(log, "hold")
    if found is None:
        return missing("hold")
    start, end = found
    out = grade.hover_hold(
        log, start, end, height_at(log, start), hover.max_drift_m, hover.max_height_error_m
    )
    out.append(
        grade.sequence(log.events, ["took off", "landed", "disarmed"], "take-off and landing")
    )
    out.append(grade.ends_safely(log, context.sim.returns.max_landing_distance_m))
    return out


SCENARIOS = (Scenario("smoke", smoke, grade_smoke, budget_s=120.0),)
