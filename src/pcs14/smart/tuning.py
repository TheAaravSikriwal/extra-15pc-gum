"""Self-tuning (#21): the drone works out its own inertia from a short, small excitation in the
air, and its rate loops use that instead of the one they were given.

My rate loops ask for an angular acceleration and multiply it by the inertia they believe to
get the torque (step 5's tuning), so the gains mean something physical. If the drone's real
inertia is bigger (a payload, a module the profile didn't expect), it turns slower than asked,
by exactly the ratio. A doublet (a few degrees each way, a fraction of a second) and a least
squares fit of the measured angular acceleration against the asked one give that ratio. The
gains stay as they are; the inertia they multiply by changes.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Found:
    inertia: float  # kg m^2
    fit: float  # r^2 of the measured acceleration against the asked one


def identify_inertia(t, rate, asked, believed: float) -> Found:
    """From the body rate (rad/s) over time and the angular acceleration the loop asked for
    (rad/s^2): the inertia, given the one the loop believed."""
    t, rate, asked = (np.asarray(x, dtype=float) for x in (t, rate, asked))
    # the rate against the integral of what was asked, not its derivative against the asked:
    # integrating keeps the gyro's noise and the doublet's sharp edges from smearing the fit
    dt = np.diff(t, prepend=t[0])
    integral = np.cumsum(asked * dt)
    design = np.column_stack([integral, np.ones_like(integral)])
    (ratio, start), *_ = np.linalg.lstsq(design, rate, rcond=None)
    residual = rate - (ratio * integral + start)
    spread = rate - rate.mean()
    fit = 1.0 - float(np.dot(residual, residual) / np.dot(spread, spread))
    return Found(inertia=believed / float(ratio), fit=fit)


def torque_scale(found: float, believed: float) -> float:
    """How much more torque the same gains ask for with the found inertia."""
    return found / believed


def lagged(t, asked, lag_s: float) -> np.ndarray:
    """What motors with a first-order lag of `lag_s` do with the speeds they're asked for."""
    asked = np.asarray(asked, dtype=float)
    if lag_s <= 0:
        return asked
    out = np.empty_like(asked)
    out[0] = asked[0]
    dt = np.diff(np.asarray(t, dtype=float), prepend=t[0])
    for k in range(1, len(out)):
        out[k] = out[k - 1] + (asked[k] - out[k - 1]) * min(dt[k] / lag_s, 1.0)
    return out


def identify_roll(t, roll_rate, rotor_speed, motor_constant: float, rotor_y,
                  lag_s: float = 0.0, pad_s: float = 0.3) -> Found:  # fmt: skip
    """The roll inertia from a flight log: the roll torque the rotors' thrusts make (k w^2 at
    each rotor's arm across, after the motors' lag), against the gyro's roll rate. Each stretch
    where the torque moves is fitted on its own, the rate against the torque's integral with a
    starting rate of its own, so slow drift between them doesn't count."""
    t = np.asarray(t, dtype=float)
    speeds = lagged(t, rotor_speed, lag_s)
    torque = motor_constant * (speeds**2 * np.asarray(rotor_y, dtype=float)).sum(axis=1)
    torque = torque - np.median(torque)  # the steady part holds a center of gravity off-center
    busy = np.abs(torque) > 0.2 * np.abs(torque).max()
    if busy.sum() < 5:
        raise ValueError("nothing in this flight moves the roll enough to tell")
    # the busy stretches, padded and merged
    dt = float(np.median(np.diff(t)))
    pad = int(pad_s / dt)
    marked = np.convolve(busy.astype(float), np.ones(2 * pad + 1), mode="same") > 0
    edges = np.flatnonzero(np.diff(np.concatenate([[0], marked.astype(int), [0]])))
    stretches = list(zip(edges[::2], edges[1::2], strict=True))
    rows, rates, columns = [], [], len(stretches)
    for n, (a, b) in enumerate(stretches):
        integral = np.cumsum(torque[a:b]) * dt
        for k in range(b - a):
            row = np.zeros(1 + columns)
            row[0], row[1 + n] = integral[k], 1.0
            rows.append(row)
        rates.extend(np.asarray(roll_rate, dtype=float)[a:b])
    design, rates = np.array(rows), np.array(rates)
    solution = np.linalg.lstsq(design, rates, rcond=None)[0]
    residual = rates - design @ solution
    spread = rates - rates.mean()
    fit = 1.0 - float(np.dot(residual, residual) / np.dot(spread, spread))
    return Found(inertia=float(1.0 / solution[0]), fit=fit)
