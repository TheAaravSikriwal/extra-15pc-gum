"""The safety monitor's automatic triggers, the reference version.

The Teensy has its own IMU, and two things it watches for:

- free fall: the total acceleration it feels drops under `free_fall_g` (an IMU feels about 1 g
  hovering and close to nothing falling) and stays there for `free_fall_s`
- tumbling: its body rate passes `tumble_rate_dps` for `tumble_rate_s`, or its tilt passes
  `tumble_tilt_deg` for `tumble_tilt_s`

Each trigger fires once, at the moment its condition has held long enough, and re-arms when the
condition clears. The thresholds live in design/targets.yaml. In the flight sim, every
scenario's IMU data runs through this to count false triggers; while they're in shadow mode the
triggers only log. Step 5's Teensy firmware has to give the same answers on the same data, and
it has to estimate the tilt itself, which this version takes as an input.
"""

import math
from dataclasses import dataclass

G = 9.80665


@dataclass(frozen=True)
class ImuSample:
    t: float  # s
    accel: tuple[float, float, float]  # m/s^2, what the IMU feels: about (0, 0, g) hovering
    gyro: tuple[float, float, float]  # rad/s, body rates
    tilt: float = 0.0  # rad from level


@dataclass(frozen=True)
class Trigger:
    kind: str  # free fall, tumble rate or tumble tilt
    at: float  # s, when it fired
    since: float  # s, when its condition started


def _norm(v) -> float:
    return math.sqrt(sum(c * c for c in v))


def triggers(samples, limits) -> list[Trigger]:
    """Every trigger that fires through `samples`, in order."""
    conditions = {
        "free fall": (
            lambda s: _norm(s.accel) < limits.free_fall_g * G,
            limits.free_fall_s,
        ),
        "tumble rate": (
            lambda s: _norm(s.gyro) > math.radians(limits.tumble_rate_dps),
            limits.tumble_rate_s,
        ),
        "tumble tilt": (
            lambda s: s.tilt > math.radians(limits.tumble_tilt_deg),
            limits.tumble_tilt_s,
        ),
    }
    started: dict[str, float | None] = {kind: None for kind in conditions}
    fired: dict[str, bool] = {kind: False for kind in conditions}
    out = []
    for sample in samples:
        for kind, (holds, hold_s) in conditions.items():
            if not holds(sample):
                started[kind], fired[kind] = None, False
                continue
            if started[kind] is None:
                started[kind] = sample.t
            if not fired[kind] and sample.t - started[kind] >= hold_s - 1e-9:
                out.append(Trigger(kind, sample.t, started[kind]))
                fired[kind] = True
    return out
