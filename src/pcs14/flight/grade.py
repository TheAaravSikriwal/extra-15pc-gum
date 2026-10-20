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
- no fly-away: the flight ends on the ground within the given radius of where it started
"""

from dataclasses import dataclass, field

import numpy as np

SETTLE_BAND = 0.05  # a share of the step
STEADY_BAND = 0.10  # a share of the steady descent rate
HOLD_S = 1.0  # what top speed has to be held for
ON_GROUND_M = 0.5


@dataclass(frozen=True)
class Finding:
    check: str
    passed: bool
    value: float | None
    limit: float | None
    unit: str
    detail: str


@dataclass
class FlightLog:
    t: np.ndarray  # s
    position: np.ndarray  # m, (n, 3), z up
    velocity: np.ndarray  # m/s, (n, 3)
    rotor_speed: np.ndarray  # rad/s, (n, 4)
    events: list = field(default_factory=list)  # (s, name)

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
                   f"{sizing_s / 60:.1f}")  # fmt: skip


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


def chute(log: FlightLog) -> list[Finding]:
    stopped, fired = log.when("motors stopped"), log.when("chute fired")
    order = stopped is not None and fired is not None and stopped <= fired
    order_finding = Finding(
        "chute order",
        order,
        None,
        None,
        "",
        "the motors stopped before the chute fired" if order else "the chute fired first",
    )
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


def ends_safely(log: FlightLog, radius: float) -> Finding:
    end = log.position[-1]
    distance = float(np.hypot(end[0] - log.position[0, 0], end[1] - log.position[0, 1]))
    down = end[2] <= ON_GROUND_M or log.when("landed") is not None
    passed = down and distance <= radius
    where = "on the ground" if down else f"still {end[2]:.0f} m up"
    return Finding("no fly-away", passed, distance, radius, "m",
                   f"ended {where}, {distance:.0f} m from where it started")  # fmt: skip


def false_triggers(imu, limits, allowed: int) -> Finding:
    from pcs14.safety.triggers import triggers

    fired = triggers(imu, limits)
    kinds = ", ".join(f"{t.kind} at {t.at:.1f} s" for t in fired) or "none"
    return Finding("false triggers", len(fired) <= allowed, len(fired), allowed, "",
                   f"the safety monitor's triggers fired: {kinds}")  # fmt: skip
