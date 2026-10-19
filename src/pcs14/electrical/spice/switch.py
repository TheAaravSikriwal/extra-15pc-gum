"""The safety monitor's motor cut switch in ngspice: one DShot channel, end to end.

The flight controller drives inverted DShot600 through its wire to the switch's NC side; the
switch's common goes on to the ESC, which answers each frame with its motor's period on the
same wire 30 us later, while the flight controller lets go of the line. The Teensy's own DShot
pin sits on the switch's NO side, and its listening buffer hangs off the flight controller's
end of the line. The switch is powered from the flight controller's side, so it works whether
the Teensy is on or not. An unpowered Teensy is its pins' protection diodes into a dead 3.3 V
rail (10 uF, and 33 Ohm for the chip's own draw); an unpowered buffer is its specified Ioff,
10 uA at most, so 330 kOhm.

The numbers, and where they come from:
- The TS3A5018 switch: 10 Ohm on at 3 V (its datasheet's maximum), 16 pF on; 5 pF off is a guess.
- Microcontroller pins (the flight controller's, the ESC's, the Teensy's): a 40 Ohm driver and
  5 pF, guesses from their datasheets' output levels; 40 kOhm internal pull-ups, typical.
- The SN74LVC1G125 buffer's input: 4 pF, a guess; its Ioff is TI's.
- The wires: resistance from the wire table, lengths from the CAD's routes; 0.8 uH and 40 pF a
  meter are guesses for a loose wire.
- Logic thresholds: 0.7 and 0.3 of the supply, the usual CMOS figures.
"""

from dataclasses import dataclass, field
from pathlib import Path

from pcs14.electrical import dshot
from pcs14.electrical.checks import Finding
from pcs14.electrical.spice import signals
from pcs14.electrical.spice.run import run

THROTTLE = 1046
RATE = 600_000
REPLY_RATE = 750_000  # 5/4 of DShot600
BIT = 1 / RATE
FRAME = 16 * BIT
REPLY_GAP = 30e-6
PERIOD_US = 1234  # the motor period the ESC reports
VDD = 3.3
EDGE = 2e-9
DRIVER_OHMS = 40.0
PIN_F = 5e-12
PULLUP_OHMS = 40e3
SWITCH_ON_OHMS = 10.0
SWITCH_ON_F = 16e-12
SWITCH_OFF_F = 5e-12
BUFFER_F = 4e-12
BUFFER_OFF_OHMS = 330e3
WIRE_H_PER_M = 0.8e-6
WIRE_F_PER_M = 40e-12
DEAD_RAIL_F = 10e-6
DEAD_RAIL_OHMS = 33.0
VIH, VIL = 0.7 * VDD, 0.3 * VDD
UART_BAUD = 420_000  # CRSF


def reply_period() -> int:
    return dshot.quantized_period(PERIOD_US)


@dataclass(frozen=True)
class Wiring:
    fc_to_switch: float  # m
    switch_to_esc: float
    fc_to_tap: float
    teensy_to_switch: float
    rx_to_fc: float
    rx_to_tap: float
    ohms_28: float  # per meter
    ohms_26: float
    rise_share: float
    margin_share: float

    @classmethod
    def from_design(cls, root: Path) -> "Wiring":
        from pcs14.cad.settings import load_settings
        from pcs14.catalog import load_catalog
        from pcs14.electrical.model import load_connection_list

        root = Path(root)
        design = load_connection_list(root / "design" / "electrical.yaml")
        settings = load_settings(root / "design" / "cad.yaml")
        catalog = load_catalog(root / "design" / "catalog")
        return cls.from_loaded(design, catalog, settings)

    @classmethod
    def from_loaded(cls, design, catalog, settings) -> "Wiring":
        """The same, from a connection list, catalog and CAD settings already loaded."""
        from pcs14.cad.assembly import wire_length

        routes = {w.name: wire_length(w) for w in settings.wires}
        runs = {run.label: run for run in design.wires}

        def length(label):
            run = runs[label]
            return run.length if run.length is not None else routes[run.route]

        lead = catalog.wire("thin-signal-lead")
        return cls(
            fc_to_switch=length("fc.ESC.CH1 to cut.J1.NC1"),
            switch_to_esc=length("cut.J1.CM1 to esc.FC.M1"),
            fc_to_tap=length("fc.ESC.CH1 to taps.B2.A"),
            teensy_to_switch=length("teensy.pins.22 to cut.J1.NO1"),
            rx_to_fc=length("rx.pads.TX to fc.RC.USART6_RX"),
            rx_to_tap=length("rx.pads.TX to taps.B1.A"),
            ohms_28=lead.gauge(28).resistance_per_m,
            ohms_26=lead.gauge(26).resistance_per_m,
            rise_share=design.checks.rise_share,
            margin_share=design.checks.threshold_margin_share,
        )


@dataclass
class Run:
    name: str
    description: str
    expected_to_pass: bool
    findings: list = field(default_factory=list)
    esc_frames: list = field(default_factory=list)
    fc_replies: list = field(default_factory=list)
    waves: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(f.passed for f in self.findings)


def _pwl(points) -> str:
    cleaned, last = [], -1.0
    for t, v in points:
        t = max(t, last + 1e-13)
        cleaned.append(f"{t:.10e} {v:.4f}")
        last = t
    return "PWL(" + " ".join(cleaned) + ")"


def _wire(name, a, b, length, ohms_per_m) -> str:
    half_c = WIRE_F_PER_M * length / 2
    return (
        f"C{name}a {a} 0 {half_c:.4e}\n"
        f"R{name} {a} {name}m {max(ohms_per_m * length, 1e-4):.4e}\n"
        f"L{name} {name}m {b} {WIRE_H_PER_M * length:.4e}\n"
        f"C{name}b {b} 0 {half_c:.4e}\n"
    )


def _driver(name, node, points, enable) -> str:
    return (
        f"V{name} {name}s 0 {_pwl(points)}\n"
        f"R{name} {name}s {name}o {DRIVER_OHMS}\n"
        f"S{name} {name}o {node} {name}e 0 swdrv\n"
        f"V{name}e {name}e 0 {_pwl(enable)}\n"
    )


def _frames(starts, throttle) -> list:
    points = [(0.0, VDD)]
    for start in starts:
        bits = dshot.frame_bits(throttle, bidirectional=True)
        points += dshot.waveform(bits, RATE, VDD, start, EDGE, inverted=True)
    return points


def _reply(start) -> list:
    slot = 1 / REPLY_RATE
    points = [(start - EDGE, VDD)]
    for i, level in enumerate(dshot.reply_bits(PERIOD_US)):
        t = start + i * slot
        points += [(t, points[-1][1]), (t + EDGE, VDD * level)]
    end = start + 21 * slot
    return points + [(end, points[-1][1]), (end + EDGE, VDD)]


def _windows_on(windows, stop) -> list:
    """An enable signal, high inside the windows."""
    points = [(0.0, 0.0)]
    for a, b in windows:
        points += [(a, 0.0), (a + EDGE, VDD), (b, VDD), (b + EDGE, 0.0)]
    return points + [(stop, 0.0)]


def _channel(wiring: Wiring, case: dict):
    stop = case["stop"]
    fc_starts, teensy_starts = case["fc_frames"], case.get("teensy_frames", [])
    answered = case["replies_after"]
    replies = [s + FRAME + REPLY_GAP for s in answered]

    def released(starts):
        """Where a sender lets go of the line: while an answer to each of its own frames is
        due, whether or not one comes."""
        due = [s + FRAME + REPLY_GAP for s in starts]
        return [(r - 5e-6, min(r + 21 / REPLY_RATE + 5e-6, stop)) for r in due if r < stop]

    fc_enable = [(0.0, stop)]
    for a, b in sorted(released(fc_starts)):  # the flight controller waits for its answers
        last = fc_enable.pop()
        fc_enable += [(last[0], a), (b, last[1])]
    lines = [
        ".model swdrv sw(vt=1.65 vh=0.1 ron=0.01 roff=1e12)",
        f".model swchip sw(vt=1.65 vh=0.2 ron={SWITCH_ON_OHMS} roff=1e9)",
        ".model esd d(is=1e-12 n=1.5 rs=10)",
        f"Vdd vdd 0 {VDD}",
    ]
    if case["teensy_on"]:
        lines.append(f"Vtrail trail 0 {VDD}")
    else:
        lines += [f"Rtrail trail 0 {DEAD_RAIL_OHMS}", f"Ctrail trail 0 {DEAD_RAIL_F}"]
    lines += [f"Cfc fc 0 {PIN_F}", f"Rpfc fc vdd {PULLUP_OHMS}"]
    text = "\n".join(lines) + "\n"
    text += _driver("fc", "fc", _frames(fc_starts, THROTTLE), _windows_on(fc_enable, stop))
    text += _wire("w1", "fc", "nc", wiring.fc_to_switch, wiring.ohms_28)
    text += _wire("w2", "fc", "tap", wiring.fc_to_tap, wiring.ohms_28)
    if case["buffers"]:
        text += f"Ctap tap 0 {BUFFER_F}\n"
        if not case["teensy_on"]:
            text += f"Rtap tap 0 {BUFFER_OFF_OHMS}\n"
    else:  # the Teensy's pin itself, straight on the line
        text += f"Ctap tap 0 {PIN_F}\nDtap1 tap trail esd\nDtap2 0 tap esd\n"
    text += (
        f"Vctl ctl 0 {_pwl(case['control'])}\n"
        f"Bnot nctl 0 V={VDD}-V(ctl)\n"
        "Snc nc com nctl 0 swchip\n"
        "Sno no com ctl 0 swchip\n"
        f"Ccom com 0 {SWITCH_ON_F}\nCnc nc 0 {SWITCH_OFF_F}\nCno no 0 {SWITCH_OFF_F}\n"
    )
    text += _wire("w4", "tpin", "no", wiring.teensy_to_switch, wiring.ohms_28)
    text += f"Ctpin tpin 0 {PIN_F}\nRtpin tpin 0 1e6\nDtp1 tpin trail esd\nDtp2 0 tpin esd\n"
    if case["teensy_on"] and teensy_starts:
        # once it takes over, the Teensy holds the line high between its frames and lets go
        # only while the ESC answers, the way a flight controller does
        windows = [(case.get("teensy_from", 0.0), stop)]
        for a, b in sorted(released(teensy_starts)):
            last = windows.pop()
            windows += [(last[0], a), (b, last[1])] if a > last[0] else [(b, last[1])]
        text += _driver(
            "te", "tpin", _frames(teensy_starts, dshot.STOP), _windows_on(windows, stop)
        )
    text += _wire("w3", "com", "esc", wiring.switch_to_esc, wiring.ohms_28)
    text += f"Cesc esc 0 {PIN_F}\nRpesc esc vdd {PULLUP_OHMS}\n"
    if replies:
        points = [(0.0, VDD)]
        for r in replies:
            points += _reply(r)
        windows = [(r - 1e-6, r + 21 / REPLY_RATE + 1e-6) for r in replies]
        text += _driver("esc", "esc", points, _windows_on(windows, stop))

    # the frames meant for the ESC: the flight controller's while the switch passes, the
    # Teensy's once it has taken over
    def held(t):
        return [v for when, v in case["control"] if when <= t][-1] >= VDD / 2

    starts = sorted(
        {*(s for s in fc_starts if not held(s)), *(s for s in teensy_starts if held(s))}
    )
    frame_windows = [(s - 2e-7, s + FRAME + 5e-7) for s in starts]
    reply_windows = [(r - 15e-6, r + 40e-6) for r in replies]
    return text, frame_windows, reply_windows


CASES = {
    "Teensy on": dict(
        description="The flight controller drives the ESC through the switch, and the ESC's RPM "
        "reply comes back, with the Teensy powered and listening",
        teensy_on=True, buffers=True, control=[(0, 0.0)], fc_frames=[2e-6, 100e-6],
        replies_after=[2e-6, 100e-6], stop=200e-6, expect=[THROTTLE, THROTTLE], replies=2,
    ),
    "Teensy off": dict(
        description="The same with the Teensy unpowered: its pins are dead diodes and its buffers "
        "leak their Ioff",
        teensy_on=False, buffers=True, control=[(0, 0.0)], fc_frames=[2e-6, 100e-6],
        replies_after=[2e-6, 100e-6], stop=200e-6, expect=[THROTTLE, THROTTLE], replies=2,
    ),
    "Cutting": dict(
        description="The Teensy holds the switch over and sends stop frames; the flight "
        "controller's frames go nowhere",
        teensy_on=True, buffers=True, control=[(0, VDD)], fc_frames=[2e-6, 100e-6],
        teensy_frames=[2e-6, 100e-6], replies_after=[2e-6, 100e-6], stop=200e-6, expect=[0, 0],
    ),
    "Takeover": dict(
        description="The Teensy takes over in the middle of a frame, then sends stop frames",
        teensy_on=True, buffers=True, control=[(0, 0.0), (110e-6, 0.0), (110e-6 + EDGE, VDD)],
        fc_frames=[2e-6, 100e-6, 200e-6, 300e-6], teensy_frames=[150e-6, 250e-6],
        teensy_from=110e-6, replies_after=[2e-6, 150e-6, 250e-6], stop=360e-6, expect=None,
    ),
    "No buffers, Teensy off": dict(
        description="What happens without the buffers: the dead Teensy's pins sit straight on the "
        "flight controller's line. Meant to fail",
        teensy_on=False, buffers=False, control=[(0, 0.0)], fc_frames=[2e-6, 100e-6],
        replies_after=[2e-6, 100e-6], stop=200e-6, expect=[THROTTLE, THROTTLE], replies=2,
        expected_to_pass=False,
    ),
}  # fmt: skip


def _check_channel(name, case, wiring, waves, frame_windows, reply_windows) -> Run:
    times = waves["time"]
    esc, fc = waves["v(esc)"], waves["v(fc)"]
    result = Run(name, case["description"], case.get("expected_to_pass", True), waves=waves)
    result.esc_frames = signals.frames(times, esc, windows=frame_windows)
    margin = wiring.margin_share * VDD
    where = f"switch sim: {name}"
    expect = case["expect"]
    if expect is None:  # the takeover: only the flight controller's throttle, stop or one loss
        ok = (
            set(result.esc_frames) <= {THROTTLE, dshot.STOP, None}
            and result.esc_frames.count(None) <= 1
            and result.esc_frames[-1] == dshot.STOP
        )
        detail = f"the ESC saw {result.esc_frames}: at most one broken frame, ending on stop"
    else:
        ok = result.esc_frames == expect
        detail = f"the ESC decoded {result.esc_frames}, expecting {expect}"
    result.findings.append(Finding("frames decode", "esc.FC.M1", ok, None, None, "", where, detail))
    if case.get("replies"):
        result.fc_replies = signals.replies(times, fc, reply_windows)
        want = [reply_period()] * case["replies"]
        result.findings.append(
            Finding(
                "reply decodes",
                "fc.ESC.CH1",
                result.fc_replies == want,
                None,
                None,
                "",
                where,
                f"the flight controller read {result.fc_replies}, expecting {want}",
            )
        )
    # edges and levels are measured on the frames that arrived whole
    reached = [
        w for w in frame_windows if signals.frames(times, esc, windows=[w]) not in ([], [None])
    ]
    limit = wiring.rise_share * BIT
    if reached:
        slowest = signals.edge_times(times, esc, reached, VDD)
        result.findings.append(
            Finding(
                "signal edges",
                "esc.FC.M1",
                slowest <= limit,
                slowest * 1e9,
                limit * 1e9,
                "ns",
                where,
                f"the slowest edge at the ESC takes {slowest * 1e9:.1f} ns, against "
                f"{wiring.rise_share:.0%} of a bit",
            )
        )
    low, high = signals.frame_levels(times, esc, [w[0] + 2e-7 for w in reached])
    if low is not None:
        ok = low <= VIL - margin and high >= VIH + margin
        result.findings.append(
            Finding(
                "signal levels",
                "esc.FC.M1",
                ok,
                high,
                VIH + margin,
                "V",
                where,
                f"lows settle at {low:.2f} V or under (limit {VIL - margin:.2f}), highs at "
                f"{high:.2f} V or over (limit {VIH + margin:.2f})",
            )
        )
    return result


def _receiver(wiring: Wiring, workdir: Path) -> Run:
    name = "Receiver, Teensy off"
    bit = 1 / UART_BAUD
    byte = [0] + [int(b) for b in f"{0xC8:08b}"[::-1]] + [1]  # start, CRSF's sync byte, stop
    points, start = [(0.0, VDD)], 5e-6
    for i, level in enumerate(byte * 2):
        t = start + i * bit
        points += [(t, points[-1][1]), (t + EDGE, VDD * level)]
    stop = start + 2 * len(byte) * bit + 10e-6
    text = (
        ".model swdrv sw(vt=1.65 vh=0.1 ron=0.01 roff=1e12)\n"
        f"Vdd vdd 0 {VDD}\n"
        + _driver("rx", "rx", points, [(0.0, VDD), (stop, VDD)])
        + _wire("w1", "rx", "fcrx", wiring.rx_to_fc, wiring.ohms_26)
        + _wire("w2", "rx", "tap", wiring.rx_to_tap, wiring.ohms_26)
        + f"Cfcrx fcrx 0 {PIN_F}\nRfcrx fcrx vdd {PULLUP_OHMS}\n"
        + f"Ctap tap 0 {BUFFER_F}\nRtap tap 0 {BUFFER_OFF_OHMS}\n"
    )
    waves = run(text, ["v(rx)", "v(fcrx)", "v(tap)"], workdir, step=1e-9, stop=stop, tmax=20e-9)
    times, volts = waves["time"], waves["v(fcrx)"]
    result = Run(name, "The receiver's CRSF line into the flight controller, with the Teensy's "
                 "buffer unpowered on it", True, waves=waves)  # fmt: skip
    import numpy as np

    samples = [
        (level, float(np.interp(start + (i + 0.5) * bit, times, volts)))
        for i, level in enumerate(byte * 2)
    ]
    high = min(v for level, v in samples if level)
    low = max(v for level, v in samples if not level)
    margin = wiring.margin_share * VDD
    where = f"switch sim: {name}"
    result.findings.append(
        Finding(
            "signal levels",
            "fc.RC.USART6_RX",
            low <= VIL - margin and high >= VIH + margin,
            high,
            VIH + margin,
            "V",
            where,
            f"lows at {low:.2f} V or under, highs at {high:.2f} V or over",
        )
    )
    slowest = signals.edge_times(times, volts, [(start, stop)], VDD)
    result.findings.append(
        Finding(
            "signal edges",
            "fc.RC.USART6_RX",
            slowest <= wiring.rise_share * bit,
            slowest * 1e9,
            wiring.rise_share * bit * 1e9,
            "ns",
            where,
            f"the slowest edge takes {slowest * 1e9:.1f} ns, against {wiring.rise_share:.0%} "
            "of a CRSF bit",
        )
    )
    return result


def run_all(wiring: Wiring, workdir: Path) -> dict[str, Run]:
    out = {}
    for name, case in CASES.items():
        text, frame_windows, reply_windows = _channel(wiring, case)
        folder = Path(workdir) / name.lower().replace(" ", "-").replace(",", "")
        waves = run(
            text,
            ["v(fc)", "v(nc)", "v(com)", "v(esc)", "v(no)", "v(tap)", "v(ctl)"],
            folder,
            step=1e-9,
            stop=case["stop"],
            tmax=20e-9,
        )
        out[name] = _check_channel(name, case, wiring, waves, frame_windows, reply_windows)
    out["Receiver, Teensy off"] = _receiver(wiring, Path(workdir) / "receiver")
    return out
