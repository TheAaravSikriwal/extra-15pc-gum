"""Reading DShot back out of a simulated waveform: the frames, the ESC's reply, how fast the edges
are, and where the levels settle."""

import numpy as np

from pcs14.electrical import dshot


def _segment(times, volts, window):
    times, volts = np.asarray(times), np.asarray(volts)
    keep = (times >= window[0]) & (times <= window[1])
    return list(zip(times[keep], volts[keep], strict=True))


def frames(times, volts, inverted=True, rate=600_000, threshold=1.65, windows=None):
    """Every frame's throttle (None if it's broken), in order. `windows` limits the search to
    when frames were sent, so the ESC's replies on the same wire don't count; without it, frames
    are split wherever the line goes quiet for 5 us."""
    if windows is None:
        samples = list(zip(times, volts, strict=True))
        edges = dshot.crossings(samples, threshold)
        windows, start, last = [], None, None
        for t, _ in edges:
            if start is None or t - last > 5e-6:
                if start is not None:
                    windows.append((start - 1e-7, last + 1e-7))
                start = t
            last = t
        if start is not None:
            windows.append((start - 1e-7, last + 1e-7))
    out = []
    for window in windows:
        bits = dshot.pulse_bits(_segment(times, volts, window), threshold, rate, inverted)
        if not bits:
            continue  # nothing reached this end in that window
        out.append(dshot.decode_frame(bits, bidirectional=inverted) if len(bits) == 16 else None)
    return out


def replies(times, volts, windows, rate=750_000, threshold=1.65):
    """The ESC's answers, one per window: from the first falling edge, the line's level in the
    middle of each of 21 slots."""
    slot = 1 / rate
    out = []
    for window in windows:
        segment = _segment(times, volts, window)
        falls = [t for t, way in dshot.crossings(segment, threshold) if way < 0]
        if not falls:
            out.append(None)
            continue
        start = falls[0]
        levels = [
            int(np.interp(start + (i + 0.5) * slot, times, volts) > threshold) for i in range(21)
        ]
        out.append(dshot.decode_reply(levels))
    return out


def edge_times(times, volts, windows, vdd):
    """The slowest 10% to 90% edge in the windows, in seconds."""
    times, volts = np.asarray(times), np.asarray(volts)
    low, high, mid = 0.1 * vdd, 0.9 * vdd, 0.5 * vdd
    slowest = 0.0
    for window in windows:
        for t, way in dshot.crossings(_segment(times, volts, window), mid):
            i = int(np.searchsorted(times, t))
            j = i
            a, b = (low, high) if way > 0 else (high, low)
            while j > 0 and (volts[j] > a if way > 0 else volts[j] < a):
                j -= 1
            k = i
            while k < len(volts) - 1 and (volts[k] < b if way > 0 else volts[k] > b):
                k += 1
            start = np.interp(a, *(_ordered(times[j : i + 1], volts[j : i + 1])))
            end = np.interp(b, *(_ordered(times[i - 1 : k + 1], volts[i - 1 : k + 1])))
            slowest = max(slowest, end - start)
    return slowest


def _ordered(t, v):
    order = np.argsort(v)
    return v[order], t[order]


def frame_levels(times, volts, starts, rate=600_000, inverted=True):
    """Where an inverted DShot line settles: the highest it sits while pulled low, the lowest
    while idle high, sampled at each bit's 20% and 95% points."""
    period = 1 / rate
    active, idle = [], []
    for start in starts:
        for i in range(16):
            t0 = start + i * period
            active.append(float(np.interp(t0 + 0.2 * period, times, volts)))
            idle.append(float(np.interp(t0 + 0.95 * period, times, volts)))
    if not active:
        return None, None
    lows, highs = (active, idle) if inverted else (idle, active)
    return max(lows), min(highs)
