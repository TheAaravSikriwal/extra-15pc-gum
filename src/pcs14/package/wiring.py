"""The wiring guide: harness by harness, every wire in the connection list with its two ends,
its gauge and type, and its cut length (its CAD route, or its own length for a short jumper),
then the meter checks to make before anything gets power.

A wire's end is `board.connector.pin`, the connection list's own name for it, with the board's
part beside it, so the guide and the KiCad schematic and the harness drawings all say the same
thing.
"""

from dataclasses import dataclass

ORDER = ("main power", "battery taps", "motors", "esc cable", "receiver", "lidar",
         "safety monitor", "module power", "module bus", "v", "p", "c")  # fmt: skip
CUT_EXTRA_MM = 20  # cut each wire this much long, then trim it to fit
WORDS = {
    "main power": "The pack's XT60 lead to the ESC's battery pads, 12 AWG. The heaviest "
    "joints on the drone: tin both the pad and the wire, and use an iron that can hold its "
    "heat on a big pad.",
    "battery taps": "The small feeds off the main power: the two fuses inline, the BEC's "
    "feed and the flight controller's battery sense.",
    "motors": "The motors' own leads, cut to their routes along the arms and soldered to "
    "the ESC's motor pads. Any two of a motor's three wires swapped reverses it, which the "
    "bench checks catch.",
    "esc cable": "The ESC's signal cable to the flight controller goes through the motor cut "
    "board: the ESC's side to the switch, the switch to the flight controller. This is the "
    "path the safety monitor takes over.",
    "receiver": "The receiver's CRSF lines to the flight controller, with the safety "
    "monitor's tap on them.",
    "lidar": "The TF-Luna's serial lead along the bottom plate to the flight controller.",
    "safety monitor": "The Teensy's feeds, its listening taps through the buffers, the cut "
    "board's control and its own supply, and the chute lines. The most wires in one place on "
    "the drone, and the ones that matter most: check each against the pin table in the "
    "electrical report before it's soldered.",
    "module power": "The BEC's 5 V and the pack's feed to the module sockets.",
    "module bus": "The CAN bus from the flight controller through V's and P's slots to C's, "
    "with a terminator at each end.",
    "v": "V's own wiring, inside its housing.",
    "p": "P's own wiring: the CANnode, the chute switch, the servo's feed through the "
    "ideal-diode board.",
    "c": "C's own wiring, to the placeholder claws.",
}
CHECKS = {
    "main power": [
        "Between the XT60's two contacts: no dead short. The meter may beep for a moment as the "
        "ESC's capacitors charge, then it must stop.",
        "Each lead end to end: under 0.1 ohm on a meter that can read that low.",
        "The XT60's + to the ESC's VBAT pad, not its GND: the polarity, once more, before the "
        "smoke stopper goes on.",
    ],
    "battery taps": [
        "Through each fuse: continuity. Pull a fuse and the line it feeds goes open.",
    ],
    "module power": [
        "Each socket's 5 V to its GND: no short. Each socket's battery pin to GND: no short.",
    ],
    "safety monitor": [
        "With the Teensy unpowered, each buffered line still reaches its flight controller "
        "pin: the monitor must never load a line it only listens to.",
        "The cut board's control line to the Teensy, and its pull-down to ground: about "
        "10 kOhm. Also measure the board's two undocumented 1 kOhm resistors (the unproven "
        "list).",
    ],
    "module bus": [
        "CAN_H to CAN_L across the whole bus, nothing plugged in: about 60 ohm, the two "
        "terminators in parallel.",
    ],
}
GENERIC = [
    "Every wire end to end: continuity.",
    "Every pin of every plug against its neighbors: no shorts.",
    "Each plug's pin 1 against the board's pinout, before it goes in.",
]


@dataclass(frozen=True)
class Row:
    harness: str
    module: str
    end_a: str
    end_b: str
    awg: int
    wire: str  # the wire's type, in words
    cut_mm: float
    own_lead: bool
    name: str


def rows(design, routes, parts, runs: dict | None = None) -> list[Row]:
    """Every wire, in the connection list's order. `routes` maps each CAD route to (its
    module, its length in m); `parts` is the catalog by id. `runs`, by each wire's label, is its
    whole run in m from one plug to the other (pcs14.site.wires3d): a routed wire is cut to that
    where it's given, since the run from the route to each plug needs wire too."""

    def end(ref: str) -> str:
        board = ref.split(".")[0]
        if board not in design.boards:
            return f"`{ref}`"
        part = parts.get(design.boards[board].part)
        return f"`{ref}` ({part.model})" if part is not None else f"`{ref}`"

    out = []
    for run in design.wires:
        if run.route is not None:
            module, meters = routes[run.route]
            meters = (runs or {}).get(run.label, meters)
        else:
            module, meters = "base", run.length
        out.append(Row(
            harness=run.harness, module=module, end_a=end(run.ends[0]), end_b=end(run.ends[1]),
            awg=run.awg, wire=parts[run.wire].model, cut_mm=meters * 1000,
            own_lead=run.own_lead, name=run.label,
        ))  # fmt: skip
    return out


def render(all_rows, generated: str) -> str:
    out = [
        "# The wiring guide",
        "",
        f"*Generated {generated} by `pcs14 package`, from the connection list "
        "(`design/electrical.yaml`) and the CAD's wire routes. Every wire is here once, under "
        "its harness. The harness drawings and the pin tables are in the "
        "[electrical report](../reports/electrical/README.md), and the KiCad schematic beside "
        f"it. Cut each wire {CUT_EXTRA_MM} mm longer than its length here, then trim it to "
        "fit.*",
        "",
        "Before anything: the pack is in another room, and every check below is made with a "
        "meter, unpowered. Heat shrink goes on every soldered end before it's soldered, "
        "because it can't go on after.",
    ]
    harnesses = list(ORDER) + sorted({r.harness for r in all_rows} - set(ORDER))
    for harness in harnesses:
        picked = [r for r in all_rows if r.harness == harness]
        if not picked:
            continue
        slug = harness.replace(" ", "-")
        total = sum(r.cut_mm for r in picked) / 1000
        out += ["", f"## {harness.capitalize()}", "", WORDS.get(harness, ""), "",
                f"{len(picked)} wires, {total:.2f} m in all. The drawing: "
                f"[{slug}.svg](../reports/electrical/harnesses/{slug}.svg).", "",
                "| From | To | Gauge | Wire | Length |", "|---|---|---|---|---|"]  # fmt: skip
        for r in picked:
            wire = "the motor's own lead" if r.own_lead else r.wire
            out.append(f"| {r.end_a} | {r.end_b} | {r.awg} AWG | {wire} | {r.cut_mm:.0f} mm |")
        out += ["", "Check with a meter:", ""]
        out += [f"- {c}" for c in CHECKS.get(harness, []) + GENERIC]
    out += [""]
    return "\n".join(out)
