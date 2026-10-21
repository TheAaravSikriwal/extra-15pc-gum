"""Grading a flight against the `flight_sim` targets.

A flight log here is plain arrays, so the checks work the same on a real PX4 log (the runner
converts it) and on the short synthetic logs the tests use. Positions are in a local frame with
z up, the height above where the flight started; velocities likewise. Events are (time, name)
pairs: "link lost", "return", "landed", "motors stopped", "chute fired" and so on.

The definitions:
- hover and wind drift: the largest distance sideways from where the hold began, and the
  largest height error from the setpoint
- a step response settles once it stays within 5% of the step for good; the overshoot is how
  far past the step it goes, as a share of the step
- top speed is what it holds for a full second, not a momentary peak
- motor headroom: the fastest any motor spins, as a share of its top speed
- the parachute: the motors have to stop before it fires; the height lost runs from firing
  until the descent first settles within 10% of its steady rate
- no fly-away: the flight ends on the ground within the given radius of where it started, or
  of where it was when something failed
- a controlled landing: the fastest descent over the last 0.3 s before touching the ground
"""

from dataclasses import dataclass, field

import numpy as np

SETTLE_BAND = 0.05  # a share of the step
STEADY_BAND = 0.10  # a share of the steady descent rate
HOLD_S = 1.0  # what top speed has to be held for
ON_GROUND_M = 0.5
CONTACT_M = 0.05  # m above where it started: touching the ground
# m: a tumbled drone lands on its side or upside down with its middle up to about here, so its
# middle can stay above CONTACT_M until it rolls flat, seconds after the impact
SIDE_CONTACT_M = 0.4
TOUCHDOWN_S = 0.3  # how long before touching down the landing speed is measured over


@dataclass(frozen=True)
class Finding:
    check: str
    passed: bool
    value: float | None
    limit: float | None
    unit: str
    detail: str
    extra: dict | None = None  # numbers for the report's tables, when a check has more than one


@dataclass
class FlightLog:
    t: np.ndarray  # s
    position: np.ndarray  # m, (n, 3), z up
    velocity: np.ndarray  # m/s, (n, 3)
    rotor_speed: np.ndarray  # rad/s, (n, 4)
    events: list = field(default_factory=list)  # (s, name)
    attitude: np.ndarray | None = None  # (n, 4) quaternions, x y z w, body to the local frame
    # the motors' commands at their own rate, (t, (m, 4) rad/s): the ground truth can be slower
    # than the motors, and self-tuning needs every command
    esc: tuple | None = None

    def window(self, start: float, end: float) -> np.ndarray:
        return (self.t >= start) & (self.t <= end)

    def when(self, name: str) -> float | None:
        return next((t for t, n in self.events if n == name), None)


def _drift(log: FlightLog, start: float, end: float, height: float):
    inside = log.window(start, end)
    pos = log.position[inside]
    sideways = np.hypot(pos[:, 0] - pos[0, 0], pos[:, 1] - pos[0, 1]).max()
    vertical = np.abs(pos[:, 2] - height).max()
    return float(sideways), float(vertical)


def hover_hold(log, start, end, height, max_drift, max_height) -> list[Finding]:
    sideways, vertical = _drift(log, start, end, height)
    return [
        Finding("hover drift", sideways <= max_drift, sideways, max_drift, "m",
                f"drifted {sideways:.2f} m sideways over {end - start:g} s"),
        Finding("hover height", vertical <= max_height, vertical, max_height, "m",
                f"held its height within {vertical:.2f} m"),
    ]  # fmt: skip


def step_response(t, response, at, size, max_settle, max_overshoot) -> list[Finding]:
    after = t >= at
    times, values = t[after], response[after]
    outside = np.abs(values - size) > SETTLE_BAND * abs(size)
    settle = float(times[outside][-1] - at) if outside.any() else 0.0
    overshoot = max(0.0, float((values.max() - size) / size)) if size else 0.0
    return [
        Finding("step settling", settle <= max_settle, settle, max_settle, "s",
                f"inside {SETTLE_BAND:.0%} of the step after {settle:.2f} s"),
        Finding("step overshoot", overshoot <= max_overshoot, overshoot, max_overshoot, "",
                f"overshot by {overshoot:.0%} of the step"),
    ]  # fmt: skip


def top_speed(log, target, hold_s: float = HOLD_S) -> Finding:
    speed = np.hypot(log.velocity[:, 0], log.velocity[:, 1])
    dt = float(np.median(np.diff(log.t)))
    n = max(1, int(round(hold_s / dt)))
    held = max(float(speed[k : k + n].min()) for k in range(0, len(speed) - n + 1))
    words = f"held {held * 3.6:.0f} km/h for {hold_s:g} s, against {target * 3.6:.0f}"
    return Finding("top speed", held >= target, held, target, "m/s", words)


def wind_hold(log, start, end, height, max_drift, max_motor_share, max_rot_velocity):
    sideways, _ = _drift(log, start, end, height)
    inside = log.window(start, end)
    share = float(log.rotor_speed[inside].max() / max_rot_velocity)
    return [
        Finding("wind drift", sideways <= max_drift, sideways, max_drift, "m",
                f"drifted {sideways:.2f} m in the wind"),
        Finding("motor headroom", share <= max_motor_share, share, max_motor_share, "",
                f"the busiest motor reached {share:.0%} of its top speed"),
    ]  # fmt: skip


def endurance(sim_s: float, sizing_s: float, max_difference: float) -> Finding:
    difference = abs(sim_s - sizing_s) / sizing_s
    return Finding("endurance", difference <= max_difference, difference, max_difference, "",
                   f"{sim_s / 60:.1f} min in the sim against the sizing model's "
                   f"{sizing_s / 60:.1f}",
                   extra={"sim_min": sim_s / 60, "sizing_min": sizing_s / 60})  # fmt: skip


def sequence(events, expected, name: str) -> Finding:
    """Whether `expected` happens, in that order."""
    times = sorted(events)
    since, found = -np.inf, []
    for wanted in expected:
        hit = next((t for t, n in times if n == wanted and t >= since), None)
        if hit is None:
            break
        found.append(wanted)
        since = hit
    passed = found == list(expected)
    missing = [e for e in expected if e not in found]
    detail = " then ".join(expected) if passed else f"never got to: {', '.join(missing)}"
    return Finding(name, passed, None, None, "", detail)


def chute(log: FlightLog, ejection_s: float = 0.0) -> list[Finding]:
    """The motors have to stop before the canopy leaves, which is `ejection_s` after the chute
    fires: PX4's flight termination does both in the same step."""
    stopped, fired = log.when("motors stopped"), log.when("chute fired")
    order = stopped is not None and fired is not None and stopped <= fired + ejection_s + 1e-9
    if order:
        words = f"the motors stopped {fired + ejection_s - stopped:.2f} s before the canopy left"
    elif fired is not None and stopped is not None:
        words = "the canopy left while the motors still ran"
    else:
        words = "the chute never fired" if fired is None else "the motors never stopped"
    order_finding = Finding("chute order", order, None, None, "", words)
    if fired is None:
        return [order_finding, Finding("chute height lost", False, None, None, "m", "no chute")]
    after = log.t >= fired
    airborne = after & (log.position[:, 2] > ON_GROUND_M)
    rates = log.velocity[airborne, 2]
    steady = float(np.median(rates[-max(1, len(rates) // 5) :]))
    # settled for good: past the last airborne sample outside the band
    outside = airborne & (np.abs(log.velocity[:, 2] - steady) > STEADY_BAND * abs(steady))
    up = np.flatnonzero(airborne)
    k = min(int(np.flatnonzero(outside)[-1]) + 1, int(up[-1])) if outside.any() else int(up[0])
    start = int(np.argmax(after))
    lost = float(log.position[start, 2] - log.position[k, 2])
    return [
        order_finding,
        Finding("chute height lost", True, lost, None, "m",
                f"lost {lost:.1f} m before settling at {abs(steady):.1f} m/s"),
    ]  # fmt: skip


def ends_safely(log: FlightLog, radius: float, since: float | None = None) -> Finding:
    """On the ground at the end, within `radius` of where it started, or of where it was at
    `since` (the moment a failure hit, say)."""
    k = 0 if since is None else min(int(np.searchsorted(log.t, since)), len(log.t) - 1)
    origin, end = log.position[k], log.position[-1]
    distance = float(np.hypot(end[0] - origin[0], end[1] - origin[1]))
    down = end[2] <= ON_GROUND_M or log.when("landed") is not None
    passed = down and distance <= radius
    where = "on the ground" if down else f"still {end[2]:.0f} m up"
    start = "where it started" if since is None else "where it was then"
    return Finding("no fly-away", passed, distance, radius, "m",
                   f"ended {where}, {distance:.0f} m from {start}")  # fmt: skip


def touchdown(log: FlightLog, max_speed: float) -> Finding:
    """A controlled landing: the fastest it was coming down in the last TOUCHDOWN_S before it
    first got within SIDE_CONTACT_M of the ground after its highest point. That's the moment
    of contact for a drone landing on its feet, its side or its back; a level landing crosses
    it at its landing speed."""
    top = int(np.argmax(log.position[:, 2]))
    down = np.flatnonzero(log.position[top:, 2] <= SIDE_CONTACT_M)
    if not len(down):
        return Finding("touchdown", False, None, max_speed, "m/s", "it never came down")
    k = top + int(down[0])
    before = (log.t >= log.t[k] - TOUCHDOWN_S) & (log.t <= log.t[k])
    speed = max(0.0, float(-log.velocity[before, 2].min()))
    kind = "a controlled landing" if speed <= max_speed else "too fast for a controlled landing"
    return Finding("touchdown", speed <= max_speed, speed, max_speed, "m/s",
                   f"came down at {speed:.1f} m/s at the end, {kind}")  # fmt: skip


def caught(imu, limits, since: float) -> Finding:
    """How soon the safety monitor's triggers would catch a real failure that hit at `since`.
    Not a pass or fail of the drone: its triggers are in shadow mode, and what they'd do about
    it is step 5's and 6's to decide."""
    from pcs14.safety.triggers import triggers

    fired = [t for t in triggers(imu, limits) if t.at >= since]
    if not fired:
        return Finding("safety monitor", False, None, None, "s",
                       "its triggers never fired after the failure")  # fmt: skip
    first = fired[0]
    delay = first.at - since
    words = f"its {first.kind} trigger would fire {delay:.2f} s after the failure"
    return Finding("safety monitor", True, delay, None, "s", words)


def false_triggers(imu, limits, allowed: int) -> Finding:
    from pcs14.safety.triggers import triggers

    fired = triggers(imu, limits)
    kinds = ", ".join(f"{t.kind} at {t.at:.1f} s" for t in fired) or "none"
    return Finding("false triggers", len(fired) <= allowed, len(fired), allowed, "",
                   f"the safety monitor's triggers fired: {kinds}")  # fmt: skip
