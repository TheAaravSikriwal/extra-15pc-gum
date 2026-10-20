"""The plain flights: the smoke flight that proves the runner works, and the moves every other
scenario is built from."""

from pcs14.flight import grade
from pcs14.flight.scenarios import Aborted, Scenario

SMOKE_HEIGHT = 2.5  # m
SMOKE_HOLD_S = 10.0
SETTLE_S = 3.0  # after reaching a height, before a hold counts
HOME_RADIUS = 1.0  # m: a flight that should come back lands within this of where it started


async def take_off(s, height: float, timeout: float = 40.0):
    """Arms, climbs to `height` with PX4's takeoff mode, and lets it settle."""
    await s.drone.action.set_takeoff_altitude(height)
    await s.drone.action.arm()
    s.mark("arm")
    await s.drone.action.takeoff()
    if not await s.clock.until(lambda: s.state.height >= height - 0.2, timeout):
        raise Aborted(f"it never climbed to {height:g} m (got to {s.state.height:.1f} m)")
    await s.clock.sleep(SETTLE_S)


async def hold(s, seconds: float, name: str = "hold"):
    """Holds where it is for `seconds`, marked "<name> start" and "<name> end" (not just the
    name, which could be one of PX4's modes)."""
    s.mark(f"{name} start")
    await s.clock.sleep(seconds)
    s.mark(f"{name} end")


async def land(s, timeout: float = 90.0):
    """Lands where it is and waits for PX4 to disarm."""
    await s.drone.action.land()
    s.mark("land sent")
    if not await s.clock.until(lambda: not s.state.armed, timeout):
        raise Aborted(f"it didn't land and disarm within {timeout:g} s")


async def smoke(s):
    await take_off(s, SMOKE_HEIGHT)
    await hold(s, SMOKE_HOLD_S)
    await land(s)


def hold_window(log, name: str = "hold"):
    start, end = log.when(f"{name} start"), log.when(f"{name} end")
    if start is None or end is None:
        return None
    return start, end


def height_at(log, t: float) -> float:
    k = min(int(log.t.searchsorted(t)), len(log.t) - 1)
    return float(log.position[k, 2])


def grade_smoke(log, imu, context) -> list:
    hover = context.targets.flight_sim.hover
    window = hold_window(log)
    if window is None:
        return [grade.Finding("hover", False, None, None, "", "it never got to the hold")]
    start, end = window
    found = grade.hover_hold(
        log, start, end, height_at(log, start), hover.max_drift_m, hover.max_height_error_m
    )
    found.append(
        grade.sequence(log.events, ["took off", "landed", "disarmed"], "take-off and landing")
    )
    found.append(grade.ends_safely(log, HOME_RADIUS))
    return found


SCENARIOS = (Scenario("smoke", smoke, grade_smoke, budget_s=120.0),)
