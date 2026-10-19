"""DShot, the flight controller's digital protocol to the ESC, enough to drive and read the
circuit sims.

A frame is 16 bits: an 11-bit throttle (0 is stop, 1 to 47 are commands, 48 to 2047 throttle),
a telemetry bit, and a 4-bit checksum, the low nibble of the 12-bit value XORed with itself
shifted by 4 and by 8. Bidirectional DShot inverts the checksum and the line (idle high), and
after each frame the ESC answers on the same wire with its motor's period: a 9-bit mantissa
and 3-bit shift, a checksum, GCR-coded into 20 bits and sent as 21 line levels at 5/4 of the
command rate. In DShot600 a bit is 1.67 us; a one is active for 75% of it, a zero for 37.5%.
The source is Betaflight's DShot page (https://betaflight.com/docs/development/API/Dshot).
"""

STOP = 0
ONE_DUTY = 0.75
ZERO_DUTY = 0.375
GCR = {
    0x0: 0x19, 0x1: 0x1B, 0x2: 0x12, 0x3: 0x13, 0x4: 0x1D, 0x5: 0x15, 0x6: 0x16, 0x7: 0x17,
    0x8: 0x1A, 0x9: 0x09, 0xA: 0x0A, 0xB: 0x0B, 0xC: 0x1E, 0xD: 0x0D, 0xE: 0x0E, 0xF: 0x0F,
}  # fmt: skip
UNGCR = {code: nibble for nibble, code in GCR.items()}


def _checksum(value12: int, inverted: bool) -> int:
    crc = (value12 ^ (value12 >> 4) ^ (value12 >> 8)) & 0xF
    return (~crc & 0xF) if inverted else crc


def frame_value(throttle: int, telemetry: bool = False, bidirectional: bool = False) -> int:
    value12 = (throttle << 1) | int(telemetry)
    return (value12 << 4) | _checksum(value12, bidirectional)


def frame_bits(throttle: int, telemetry: bool = False, bidirectional: bool = False) -> list[int]:
    return [int(b) for b in f"{frame_value(throttle, telemetry, bidirectional):016b}"]


def decode_frame(bits, bidirectional: bool = False) -> int | None:
    """The throttle in a frame, or None if it's broken or its checksum is wrong."""
    if len(bits) != 16:
        return None
    value = int("".join(str(b) for b in bits), 2)
    value12 = value >> 4
    if value & 0xF != _checksum(value12, bidirectional):
        return None
    return value12 >> 1


def waveform(bits, rate, high, start, edge, inverted=False, low=0.0):
    """A piecewise-linear waveform for these bits: (seconds, volts) points."""
    period = 1 / rate
    idle, active = (high, low) if inverted else (low, high)
    points = [(0.0, idle)] if start > 0 else []
    for i, bit in enumerate(bits):
        t0 = start + i * period
        width = (ONE_DUTY if bit else ZERO_DUTY) * period
        points += [(t0, idle), (t0 + edge, active), (t0 + width, active), (t0 + width + edge, idle)]
    return points


def crossings(samples, threshold):
    """Times a sampled waveform crosses the threshold, with which way it went (+1 up, -1 down)."""
    out = []
    for (t0, v0), (t1, v1) in zip(samples, samples[1:], strict=False):
        if (
            (v0 - threshold) * (v1 - threshold) < 0
            or (v0 < threshold <= v1)
            or (v0 >= threshold > v1)
        ):
            if v1 == v0:
                continue
            t = t0 + (threshold - v0) * (t1 - t0) / (v1 - v0)
            out.append((t, 1 if v1 > v0 else -1))
    return out


def pulse_bits(samples, threshold, rate, inverted=False):
    """The bits in a DShot waveform, from how long each pulse stays active."""
    period = 1 / rate
    cut = (ONE_DUTY + ZERO_DUTY) / 2 * period
    starts, bits = None, []
    begin, finish = (-1, 1) if inverted else (1, -1)
    for t, way in crossings(samples, threshold):
        if way == begin:
            starts = t
        elif way == finish and starts is not None:
            bits.append(1 if t - starts > cut else 0)
            starts = None
    return bits


def quantized_period(period_us: int) -> int:
    """The motor period as the reply can carry it: a 9-bit mantissa shifted by up to 7."""
    shift = 0
    while (period_us >> shift) > 0x1FF and shift < 7:
        shift += 1
    return (period_us >> shift) << shift


def _reply_value(period_us: int) -> int:
    shift = 0
    while (period_us >> shift) > 0x1FF and shift < 7:
        shift += 1
    value12 = (shift << 9) | (period_us >> shift)
    return (value12 << 4) | _checksum(value12, True)


def reply_bits(period_us: int) -> list[int]:
    """The ESC's answer as 21 line levels: GCR-coded, then each one in the code flips the line."""
    value = _reply_value(period_us)
    gcr = 0
    for shift in (12, 8, 4, 0):
        gcr = (gcr << 5) | GCR[(value >> shift) & 0xF]
    code = [int(b) for b in f"{gcr:020b}"]
    levels = [0]
    for bit in code:
        levels.append(levels[-1] ^ bit)
    return levels


def decode_reply(levels) -> int | None:
    """The period in an answer, or None if it doesn't decode."""
    if len(levels) != 21:
        return None
    code = [levels[i + 1] ^ levels[i] for i in range(20)]
    value = 0
    for i in range(4):
        quintet = int("".join(str(b) for b in code[5 * i : 5 * i + 5]), 2)
        if quintet not in UNGCR:
            return None
        value = (value << 4) | UNGCR[quintet]
    value12 = value >> 4
    if value & 0xF != _checksum(value12, True):
        return None
    shift, mantissa = value12 >> 9, value12 & 0x1FF
    return mantissa << shift
