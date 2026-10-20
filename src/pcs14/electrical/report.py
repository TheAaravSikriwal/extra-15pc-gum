"""The electrical run and its report: the connection list checked in every module combination and
flight case, the switch sims, heat through the burst, the pin maps, the power tree, the harness
diagrams and the schematic, written up as docs/reports/electrical/README.md and electrical.json.

The run holds plain results, so the report can be written (and tested) without any of the
outside tools; the files that need them are made separately and listed in the run.
"""

from dataclasses import dataclass, field

from pcs14 import __version__
from pcs14.electrical.checks import Finding

PIN_MAPS = ("fc", "teensy")  # the boards whose every pin gets a table
CASES = ("hover", "cruise", "burst", "worst")
IDLE = 0.01  # routes that never work harder than this get one line in the report
STILLS = {
    "hero": "stills/takeover-portrait.png",
    "heat": "stills/burst-heat.png",
    "work": "stills/wire-work.png",
}


@dataclass(frozen=True)
class CaseRow:
    setup: str
    case: str
    pack_volts: float
    battery_amps: float | None


@dataclass(frozen=True)
class HeatRow:
    name: str
    start_c: float
    end_c: float
    limit_c: float


@dataclass(frozen=True)
class SwitchRow:
    name: str
    description: str
    expected_to_pass: bool
    passed: bool
    esc_frames: tuple
    fc_replies: tuple
    details: tuple[str, ...]

    @property
    def as_meant(self) -> bool:
        return self.passed == self.expected_to_pass


@dataclass(frozen=True)
class Estimate:
    part_id: str
    boards: tuple[str, ...]
    items: tuple[str, ...]  # the block's estimated fields; empty when the whole block is one
    note: str


@dataclass(frozen=True)
class ElectricalRun:
    build_label: str
    boards: int
    wires: int
    safety_paths: int
    combinations: tuple[str, ...]
    problems: tuple[str, ...]
    cases: tuple[CaseRow, ...]
    findings: tuple[Finding, ...]
    heat: tuple[HeatRow, ...]
    switch: tuple[SwitchRow, ...] | None  # None when the sims didn't run
    route_shares: dict  # {(setup, case): {route: share of its heating limit}}
    wire_amps: dict  # {(setup, case): {wire: amps}}
    power_tree: str
    pin_maps: tuple[tuple[str, str, str], ...]  # (board, part, Markdown table)
    estimates: tuple[Estimate, ...]
    unproven: tuple[str, ...]
    files: tuple[str, ...] = ()  # generated next to the report, relative to it
    erc: int | None = None  # KiCad's rules check: violations, or None when it didn't run
    skipped: tuple[str, ...] = ()  # what didn't run, and why
    harnesses: tuple[str, ...] = field(default=())  # harness diagrams, relative to the report
    exports: tuple[str, ...] = ()  # build outputs elsewhere, not committed
    routes: dict = field(default_factory=dict)  # {CAD route: (wire labels, "a to b")}
    full: str = "max"  # the combination with every module in
    continuous_share: float = 0.8  # the check numbers, from the connection list
    air_c: float = 40.0
    burst_s: float = 10.0
    temp_margin_c: float = 20.0

    @property
    def failing(self) -> list[Finding]:
        return [f for f in self.findings if not f.passed]

    @property
    def passed(self) -> bool:
        switch_ok = self.switch is None or all(row.as_meant for row in self.switch)
        return not self.problems and not self.failing and switch_ok and not self.erc


def _many(count: int, word: str) -> str:
    return f"{count} {word if count == 1 else word + 's'}"


def _all(count: int) -> str:
    return "both" if count == 2 else f"all {count}"


def _closeness(f: Finding, air_c: float) -> float:
    """How near a finding sits to its limit, smaller being tighter: a share of the limit, or for
    a temperature, a share of the rise the air leaves it."""
    if f.value is None or f.limit is None or f.limit == 0:
        return float("inf")
    if f.unit == "C" and f.limit > air_c:
        return (f.limit - f.value) / (f.limit - air_c)
    return abs(f.limit - f.value) / abs(f.limit)


def _rests(f: Finding) -> str:
    return "; ".join(f.rests_on)


def _frames(frames, other=()) -> str:
    """Decoded frames, or "nothing" when none came; blank for a line that isn't DShot."""
    if not frames and not other:
        return ""
    return ", ".join("broken" if f is None else str(f) for f in frames) or "nothing"


def _verdict_lines(run: ElectricalRun) -> list[str]:
    lines = []
    checks = len(run.findings)
    if run.passed:
        lines.append(
            f"**Pass.** All {checks} checks pass in {_all(len(run.combinations))} module "
            "combinations."
        )
    else:
        misses = []
        if run.failing:
            misses.append(f"{len(run.failing)} of {checks} checks miss")
        if run.problems:
            misses.append(_many(len(run.problems), "rule problem"))
        if run.switch is not None and not all(r.as_meant for r in run.switch):
            misses.append("a switch sim doesn't behave as meant")
        if run.erc:
            misses.append(f"KiCad's rules check finds {_many(run.erc, 'violation')}")
        lines.append(f"**Fail.** {'; '.join(misses).capitalize()}.")
    if run.failing:
        lines += [
            "",
            "| Check | Where | In | What it found | Rests on |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {f.check} | {f.subject} | {f.where} | {f.detail} | {_rests(f)} |"
            for f in run.failing
        ]
    lines += [
        "",
        f"Built from {run.build_label}. The connection list has "
        f"{_many(run.boards, 'board')}, {_many(run.wires, 'wire')} and "
        f"{_many(run.safety_paths, 'safety path')}.",
    ]
    if run.problems:
        lines += ["", "It breaks these rules:", ""] + [f"- {p}" for p in run.problems]
    else:
        lines.append(
            f"It passes every rule in {_all(len(run.combinations))} module combinations: every pin "
            "exists, one driver per line, no supplies tied together, no pin over its voltage, "
            "every board powered and grounded, two CAN terminators, and every safety path there."
        )
    return lines


def _cases_table(run: ElectricalRun) -> list[str]:
    by = {(r.setup, r.case): r for r in run.cases}
    lines = [
        "| Setup | Hover | Cruise | Burst | The pack in the burst |",
        "|---|---|---|---|---|",
    ]
    for setup in run.combinations:
        cells = []
        for case in ("hover", "cruise", "burst"):
            row = by.get((setup, case))
            amps = row.battery_amps if row is not None else None
            cells.append(f"{amps:.1f} A" if amps is not None else "")
        burst = by.get((setup, "burst"))
        pack = f"{burst.pack_volts:.1f} V" if burst is not None else ""
        lines.append(f"| {setup} | {' | '.join(cells)} | {pack} |")
    return lines


def _checks_tables(run: ElectricalRun) -> list[str]:
    groups: dict[str, list[Finding]] = {}
    for f in run.findings:
        groups.setdefault(f.check, []).append(f)
    lines = ["| Check | How many | Passed | Tightest |", "|---|---|---|---|"]
    for check, found in groups.items():
        passed = sum(f.passed for f in found)
        worst = [f for f in found if not f.passed] or sorted(
            found, key=lambda f: _closeness(f, run.air_c)
        )
        tight = worst[0]
        lines.append(
            f"| {check} | {len(found)} | {passed} | {tight.subject}, {tight.where}: "
            f"{tight.detail} |"
        )
    lines += ["", "Every check, one by one:", ""]
    for check, found in groups.items():
        missing = sum(not f.passed for f in found)
        note = f", {missing} miss" if missing else ""
        lines += [
            "<details>",
            f"<summary>{check}: {len(found)} checked{note}</summary>",
            "",
            "| What | In | Found | Verdict |",
            "|---|---|---|---|",
        ]
        ordered = sorted(found, key=lambda f: (f.passed, _closeness(f, run.air_c)))
        lines += [
            f"| {f.subject} | {f.where} | {f.detail} | {'pass' if f.passed else 'fail'} |"
            for f in ordered
        ]
        lines += ["", "</details>", ""]
    return lines


def _work_table(run: ElectricalRun) -> list[str]:
    """Each route's hardest case, over every combination, leaving out the ones that barely
    carry anything."""
    routes = sorted({r for shares in run.route_shares.values() for r in shares})
    lines = ["| Route | Hover | Cruise | Burst | Worst case |", "|---|---|---|---|---|"]
    idle = 0
    for route in routes:
        cells, top = [], 0.0
        for case in CASES:
            shares = [s[route] for (_, c), s in run.route_shares.items() if c == case]
            cells.append(f"{max(shares):.0%}" if shares else "")
            top = max([top, *shares])
        if top < IDLE:
            idle += 1
            continue
        lines.append(f"| {route} | {' | '.join(cells)} |")
    if idle:
        rest = "One more route never passes" if idle == 1 else f"The other {idle} routes never pass"
        lines += ["", f"{rest} {IDLE:.0%}."]
    return lines


def render(run: ElectricalRun, generated: str | None = None) -> str:
    when = f" on {generated}" if generated else ""
    files = set(run.files)
    lines = [
        "# The wiring (electrical)",
        "",
        f"*Generated{when} by pcs14 {__version__}, the electrical layer in "
        "`src/pcs14/electrical/`. One connection list, `design/electrical.yaml`, holds every "
        "board, connector and wire. Everything here comes from it, checked in every module "
        "combination and flight case.*",
        "",
    ]
    if STILLS["hero"] in files:
        lines += [f"![The safety monitor takes over an ESC line, in ngspice]({STILLS['hero']})", ""]
    lines += ["## The verdict", "", *_verdict_lines(run), ""]
    lines += [
        "## The flight cases",
        "",
        "Each combination gets four. Hover and cruise use the pessimistic power model at the "
        "reserve, where the pack is lowest and the current highest. The burst is full throttle "
        "at the reserve, which the firmware caps. The worst case is a hover with every 5 V part "
        "at its worst: servos stalled, the Pi flat out. These are the battery's currents.",
        "",
        *_cases_table(run),
        "",
        "## Every check",
        "",
        f"Every rating gets {run.continuous_share:.0%} at most, steady. Heat is checked in "
        f"{run.air_c:g} °C air, steady and through the {run.burst_s:g} s burst, against each "
        f"insulation's or connector's limit less {run.temp_margin_c:g} °C. A check that rests "
        'on an estimate says so in the verdict and in "What it rests on".',
        "",
        *_checks_tables(run),
        "## Heat through the burst",
        "",
        "Each starts from its hottest steady temperature and takes the burst's current for "
        "its whole length. A connector my firmware protects (`heat_limited`) stops at its limit, "
        "where the firmware eases the current cap.",
        "",
        "| Part | Before | At the end | Limit |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| {h.name} | {h.start_c:.0f} °C | {h.end_c:.0f} °C | {h.limit_c:.0f} °C |"
        for h in run.heat
    ]
    if STILLS["heat"] in files:
        lines += ["", f"![Temperatures through the burst]({STILLS['heat']})"]
    lines += [
        "",
        "## How hard every wire works",
        "",
        "Each route at its hardest working wire, as a share of that wire's heating limit (its "
        "rise over the air, against the rise to its limit), in its hardest combination.",
        "",
        *_work_table(run),
    ]
    if STILLS["work"] in files:
        lines += ["", f"![How hard every wire works, flat out]({STILLS['work']})"]
    lines += [
        "",
        "## The safety monitor's switch",
        "",
    ]
    if run.switch is None:
        lines.append("Not simulated on this run.")
    else:
        lines += [
            "One DShot channel in ngspice: the flight controller's pin, the wires at their real "
            "lengths, the analog switch, the Teensy's listening buffer and the ESC, which "
            "answers with its RPM reply. Every case is decoded from the simulated voltages by "
            "the project's own DShot decoder.",
            "",
            "| Case | What happens | The ESC got | The flight controller read | Meant to | "
            "Result |",
            "|---|---|---|---|---|---|",
        ]
        for row in run.switch:
            meant = "pass" if row.expected_to_pass else "fail"
            result = "as meant" if row.as_meant else "**not as meant**"
            lines.append(
                f"| {row.name} | {row.description} | "
                f"{_frames(row.esc_frames, row.fc_replies)} | "
                f"{_frames(row.fc_replies, row.esc_frames)} | {meant} | {result} |"
            )
        lines += ["", "<details>", "<summary>What each run measured</summary>", ""]
        for row in run.switch:
            lines.append(f"- **{row.name}:** " + "; ".join(row.details))
        lines += ["", "</details>"]
    lines += [
        "",
        "## Where the power goes",
        "",
        f"From the pack down, with every module in ({run.full}): typical while hovering, and "
        "the worst case.",
        "",
        run.power_tree,
        "",
        "## Pin maps",
        "",
    ]
    for board, part, table in run.pin_maps:
        lines += [f"### {board} ({part})", "", table, ""]
    lines += ["## Harness diagrams", ""]
    if run.harnesses:
        for path in run.harnesses:
            name = path.rsplit("/", 1)[-1].removesuffix(".svg").replace("-", " ")
            lines += [f"### {name}", "", f"![The {name} harness]({path})", ""]
    else:
        lines += ["Not drawn on this run.", ""]
    lines += ["## The schematic", ""]
    if "kicad/electrical.kicad_sch" in files:
        verdict = (
            "KiCad's electrical rules check wasn't run."
            if run.erc is None
            else f"KiCad's electrical rules check finds {_many(run.erc, 'violation')}."
        )
        lines += [
            "Every board a block with its pins, joined by net labels, in "
            "[`kicad/electrical.kicad_sch`](kicad/electrical.kicad_sch). It opens in KiCad 8 "
            f"or later. {verdict}",
            "",
        ]
        svgs = [p for p in run.exports if p.endswith(".svg")]
        if svgs:
            lines += [
                f"An SVG of it, too big to commit, is at `{svgs[0]}` after a run.",
                "",
            ]
    else:
        lines += ["Not written on this run.", ""]
    lines += [
        "## What it rests on",
        "",
        "Every number comes from a maker's datasheet or a measurement, except these estimates.",
        "",
    ]
    for e in run.estimates:
        what = ", ".join(e.items) if e.items else "its whole electrical block"
        lines.append(f"- **{e.part_id}** ({', '.join(e.boards)}): {what}. {e.note}")
    if not run.estimates:
        lines.append("Nothing.")
    lines += ["", "## What it can't prove", ""]
    lines += [f"- {item}" for item in run.unproven] or ["Nothing listed."]
    if run.switch is not None:
        lines.append(
            "- The switch sims use generic models built from datasheet numbers, with no ground "
            "bounce or noise from the motor current. A clean sim isn't a scope on the real thing."
        )
    lines += ["", "## Files", ""]
    if run.files:
        lines.append("Generated on every run, next to this report:")
        lines.append("")
        lines += [f"- `{path}`" for path in run.files]
    else:
        lines.append("Nothing but this report and `electrical.json` on this run.")
    if run.exports:
        lines += ["", "And outside it, not committed (they're build outputs):", ""]
        lines += [f"- `{path}`" for path in run.exports]
    if run.skipped:
        lines += ["", "Skipped on this run:", ""] + [f"- {s}" for s in run.skipped]
    lines.append("")
    return "\n".join(lines)


def _keyed(table: dict, places: int) -> dict:
    out: dict[str, dict] = {}
    for (setup, case), values in table.items():
        out.setdefault(setup, {})[case] = {k: round(v, places) for k, v in values.items()}
    return out


def _plain(value):
    """Numbers out of numpy (the solver and the sims use it) as plain Python, for JSON."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    if hasattr(value, "item") and not isinstance(value, str):
        return value.item()
    return value


def to_data(run: ElectricalRun, generated: str | None = None) -> dict:
    return _plain(_data(run, generated))


def _data(run: ElectricalRun, generated: str | None) -> dict:
    def finding(f: Finding) -> dict:
        return {
            "check": f.check,
            "subject": f.subject,
            "passed": f.passed,
            "value": f.value,
            "limit": f.limit,
            "unit": f.unit,
            "where": f.where,
            "detail": f.detail,
            "rests_on": list(f.rests_on),
        }

    return {
        "generated": generated,
        "pcs14_version": __version__,
        "build": run.build_label,
        "verdict": "pass" if run.passed else "fail",
        "connection_list": {
            "boards": run.boards,
            "wires": run.wires,
            "safety_paths": run.safety_paths,
        },
        "combinations": list(run.combinations),
        "rule_problems": list(run.problems),
        "cases": [
            {
                "setup": c.setup,
                "case": c.case,
                "pack_volts": round(c.pack_volts, 4),
                "battery_amps": None if c.battery_amps is None else round(c.battery_amps, 4),
            }
            for c in run.cases
        ],
        "findings": [finding(f) for f in run.findings],
        "burst_heat": [
            {
                "part": h.name,
                "start_c": round(h.start_c, 2),
                "end_c": round(h.end_c, 2),
                "limit_c": h.limit_c,
            }
            for h in run.heat
        ],  # fmt: skip
        "switch_sims": None
        if run.switch is None
        else [
            {
                "case": s.name,
                "description": s.description,
                "meant_to_pass": s.expected_to_pass,
                "passed": s.passed,
                "esc_frames": list(s.esc_frames),
                "fc_replies": list(s.fc_replies),
                "details": list(s.details),
            }
            for s in run.switch
        ],
        "route_heating_share": _keyed(run.route_shares, 4),
        "wire_amps": _keyed(run.wire_amps, 4),
        "routes": {route: list(labels) for route, labels in run.routes.items()},
        "estimates": [
            {"part": e.part_id, "boards": list(e.boards), "items": list(e.items), "note": e.note}
            for e in run.estimates
        ],
        "unproven": list(run.unproven),
        "kicad_rules_violations": run.erc,
        "files": list(run.files),
        "exports": list(run.exports),
        "skipped": list(run.skipped),
    }


def summary(run: ElectricalRun) -> str:
    """The short version for the terminal."""
    verdict = "pass" if run.passed else "fail"
    lines = [
        f"Electrical: {len(run.findings)} checks in {len(run.combinations)} combinations, "
        f"{len(run.failing)} miss. Verdict: {verdict}"
    ]
    for f in run.failing:
        lines.append(f"  {f.check}, {f.subject} ({f.where}): {f.detail}")
    if run.switch is not None:
        meant = sum(r.as_meant for r in run.switch)
        lines.append(f"Switch sims: {meant} of {len(run.switch)} behave as meant")
    if run.erc is not None:
        lines.append(f"KiCad's rules check: {run.erc} violations")
    lines += [f"Skipped: {s}" for s in run.skipped]
    return "\n".join(lines)
