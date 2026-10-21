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
    delay_s: float = 0.0  # how late the motors got their commands, where that was looked for


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


DELAYS_S = tuple(round(0.004 * k, 3) for k in range(21))  # 0 to 80 ms, a loop step apart


def identify_roll_with_delay(t, roll_rate, rotor_speed, motor_constant: float, rotor_y,
                             lag_s: float = 0.0, delays=DELAYS_S) -> Found:  # fmt: skip
    """identify_roll, with the commands' dead time found too: the log has each command when
    the loop sent it, and the motors get it later (in the sim, a few of Gazebo's steps), which
    reads as a bigger inertia if it's left out. The dead time that fits best wins."""
    t = np.asarray(t, dtype=float)
    speeds = np.asarray(rotor_speed, dtype=float)
    best = None
    for delay in delays:
        late = np.column_stack([np.interp(t - delay, t, speeds[:, k])
                                for k in range(speeds.shape[1])])  # fmt: skip
        found = identify_roll(t, roll_rate, late, motor_constant, rotor_y, lag_s)
        if best is None or found.fit > best.fit:
            best = Found(found.inertia, found.fit, float(delay))
    return best


def lagged_asymmetric(t, asked, up_s: float, down_s: float) -> np.ndarray:
    """What motors do with the speeds they're asked for when they speed up faster than they
    slow down (Gazebo's motor model: 12.5 ms up, 25 ms down), each column on its own."""
    asked = np.asarray(asked, dtype=float)
    out = np.empty_like(asked)
    out[0] = asked[0]
    dt = np.diff(np.asarray(t, dtype=float), prepend=t[0])
    for k in range(1, len(out)):
        step = asked[k] - out[k - 1]
        tau = np.where(step > 0, up_s, down_s)
        out[k] = out[k - 1] + step * (1.0 - np.exp(-dt[k] / tau))
    return out


def identify_roll_doublets(t, roll_rate, rotor_speed, motor_constant: float, rotor_y, windows,
                           up_s: float, down_s: float, delays=DELAYS_S) -> Found:  # fmt: skip
    """The roll inertia from the doublets the firmware flew for it: in each doublet's own
    window (start, end), the gyro's roll rate against the integral of the rotors' roll torque
    (their commanded speeds, late by the dead time, through the motors' lags), with an offset
    and a trend of its own, so a trim that wanders between and during them (the drone drifting
    sideways, rotor drag above the center of gravity) doesn't count as inertia. The dead time
    that fits best wins.

    Step 7 found this the hard way: fitted over stretches picked out by how busy the torque
    was, with one trim for the whole flight, the same doublets read 12% low in base."""
    t = np.asarray(t, dtype=float)
    rate = np.asarray(roll_rate, dtype=float)
    speeds = np.asarray(rotor_speed, dtype=float)
    arms = np.asarray(rotor_y, dtype=float)
    masks = [(t >= a) & (t <= b) for a, b in windows]
    n = len(masks)
    best = None
    for delay in delays:
        late = np.column_stack([np.interp(t - delay, t, speeds[:, k])
                                for k in range(speeds.shape[1])])  # fmt: skip
        actual = lagged_asymmetric(t, late, up_s, down_s)
        torque = motor_constant * (actual**2 * arms).sum(axis=1)
        rows, ys = [], []
        for j, m in enumerate(masks):
            tt, tq = t[m], torque[m]
            integral = np.concatenate([[0.0], np.cumsum(0.5 * (tq[1:] + tq[:-1]) * np.diff(tt))])
            block = np.zeros((m.sum(), 1 + 2 * n))
            block[:, 0] = integral
            block[:, 1 + j] = 1.0
            block[:, 1 + n + j] = tt - tt[0]
            rows.append(block)
            ys.append(rate[m])
        design, ys = np.vstack(rows), np.concatenate(ys)
        solution = np.linalg.lstsq(design, ys, rcond=None)[0]
        residual = ys - design @ solution
        spread = ys - ys.mean()
        fit = 1.0 - float(np.dot(residual, residual) / np.dot(spread, spread))
        if best is None or fit > best.fit:
            best = Found(float(1.0 / solution[0]), fit, float(delay))
    return best
