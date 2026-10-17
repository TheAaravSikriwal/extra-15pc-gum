"""The Markdown report, written to read well on GitHub."""

from pcs14 import __version__, units
from pcs14.report.formatting import fmt_limit, fmt_value, with_unit
from pcs14.sizing import checks as checks_module
from pcs14.sizing import rotor
from pcs14.sizing.battery import Pack
from pcs14.sizing.checks import DesignResult

SOURCE_WORDS = {
    "manufacturer": "manufacturer",
    "independent_test": "independent test",
    "thrust_stand": "thrust stand",
    "estimate": "estimate",
    "made_up": "made up",
}


def _source(source) -> str:
    words = SOURCE_WORDS[source.kind.value]
    return f"[{words}]({source.url})" if source.url else words


def _value(check, value: float) -> str:
    return with_unit(fmt_value(value, check.unit, check.higher_is_better), check.unit)


def _pair(check) -> str:
    nominal = fmt_value(check.nominal, check.unit, check.higher_is_better)
    if check.nominal == check.pessimistic:
        return with_unit(nominal, check.unit)
    pessimistic = fmt_value(check.pessimistic, check.unit, check.higher_is_better)
    return with_unit(f"{nominal} / {pessimistic}", check.unit)


def _hover_below_the_table(design: DesignResult) -> str | None:
    """A warning when the sizing case hovers below the thrust table's first row, where the
    power gets scaled with momentum theory instead of read from a measured point."""
    first = design.build.thrust_table.rows[0]
    hover = units.kg_to_g(design.sizing.mass.total) / rotor.MOTORS
    if hover >= first.thrust_g:
        return None
    return (
        f"- {design.targets.sizing_case} hovers at {hover:.0f} g per motor, below the thrust "
        f"table's first row ({first.thrust_g:.0f} g at {first.throttle_pct:g}% throttle). Down "
        "there the hover power is scaled from that row with momentum theory instead of read from "
        "a measured point, and that tends to come out a little low on power, so a little long on "
        "flight time."
    )


def _verdict_sentence(design: DesignResult) -> str:
    required = [r for r in design.setups if r.setup.required]
    names = ", ".join(r.setup.name for r in required)
    if design.verdict == "pass":
        return f"Every required setup ({names}) meets every target, even with pessimistic data."

    def listed(verdict: str) -> tuple[str, str]:
        found = [
            f"{c.name.lower()} for {r.setup.name}"
            for r in required
            for c in r.checks
            if c.verdict == verdict
        ]
        count = "one check" if len(found) == 1 else f"{len(found)} checks"
        return count, "; ".join(found)

    if design.verdict == "marginal":
        count, which = listed("marginal")
        verb = "makes" if count == "one check" else "make"
        return (
            f"Every required setup ({names}) meets every target on the published numbers, but "
            f"{count} only {verb} it on the optimistic end: {which}."
        )
    count, which = listed("fail")
    verb = "misses its target" if count == "one check" else "miss their targets"
    return f"{count.capitalize()} {verb} even on the published numbers: {which}."


def render(design: DesignResult, sweep=None, margin=None, made_up=False, generated=None) -> str:
    build, targets = design.build, design.targets
    pack = Pack(build.pack)
    sizing = design.sizing
    cruise_name = f"Cruise time at {targets.cruise_speed:g} m/s"
    lines = ["# Sizing report", ""]
    if made_up:
        lines += [
            "> **Made from made-up test parts.** Every number here comes from invented parts in "
            "`tests/fixtures/`, so it says nothing about a real drone. It's here to show what the "
            "report looks like.",
            "",
        ]
    when = f" on {generated}" if generated else ""
    lines += [
        f"*Generated{when} by pcs14 {__version__}, the sizing model in `src/pcs14/sizing/`. "
        "Numbers shown as A / B are the published data / the pessimistic version. Rounding "
        "always goes toward failing.*",
        "",
        "## The verdict",
        "",
        f"**{design.verdict.capitalize()}.** {_verdict_sentence(design)}",
        "",
        f"The motors and battery are sized for **{targets.sizing_case}**, carrying an extra "
        f"{units.kg_to_g(targets.growth_margin):.0f} g of growth margin. Setups marked optional "
        "get checked and reported, but don't have to pass.",
        "",
        "![Flight time, every setup](charts/flight-times.png)",
        "",
        "## The build",
        "",
        "| Part | Pick | Mass | Numbers from |",
        "|---|---|---|---|",
        f"| Motors (4) | {build.motor.maker} {build.motor.model} | {build.motor.mass_g:.0f} g each "
        f"| {_source(build.motor.source)} |",
        f"| Props (4) | {build.prop.maker} {build.prop.model} ({build.prop.diameter_in:g} x "
        f"{build.prop.pitch_in:g} in, {build.prop.blades} blades) | {build.prop.mass_g:.0f} g each "
        f"| {_source(build.prop.source)} |",
        f"| Thrust table | {build.thrust_table.voltage:g} V, {len(build.thrust_table.rows)} rows "
        f"| | {_source(build.thrust_table.source)} |",
        f"| Pack | {build.pack.label}: {pack.capacity_mah:.0f} mAh, "
        f"{pack.resistance * 1000:.0f} milliohms, {pack.max_continuous_current:.0f} A continuous "
        f"| {units.kg_to_g(build.pack.mass):.0f} g | {_source(build.pack.cell.source)} |",
        f"| ESC | {build.esc.maker} {build.esc.model} | {build.esc.mass_g:.0f} g "
        f"| {_source(build.esc.source)} |",
        f"| Frame | {build.frame.maker} {build.frame.model} | {build.frame.mass_g:.0f} g "
        f"| {_source(build.frame.source)} |",
        "",
        "## Every setup",
        "",
        f"| Setup | Modules | Required | Weight | Hover | Cruise at {targets.cruise_speed:g} m/s "
        "| Thrust-to-weight at the reserve | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in design.setups:
        setup = result.setup
        cells = []
        for name in ("Hover time", cruise_name, "Thrust-to-weight at the reserve"):
            found = [c for c in result.checks if c.name == name]
            cells.append(_pair(found[0]) if found else "can't hover")
        modules = "+".join(m for m in "VPC" if m in setup.modules) or "none"
        weight = f"{units.kg_to_g(result.mass.total):.0f} g"
        if result.growth_margin:
            weight += f" (with {units.kg_to_g(result.growth_margin):.0f} g margin)"
        lines.append(
            f"| {setup.name} | {modules} | {'yes' if setup.required else 'optional'} | {weight} | "
            f"{' | '.join(cells)} | {result.verdict} |"
        )
    lines += ["", "Every check, setup by setup:", ""]
    for result in design.setups:
        lines += [
            "<details>",
            f"<summary>{result.setup.name}: {result.verdict}</summary>",
            "",
            "| Check | Published / pessimistic | Target | Margin | Verdict |",
            "|---|---|---|---|---|",
        ]
        for check in result.checks:
            target = ("at least " if check.higher_is_better else "at most ") + with_unit(
                fmt_limit(check.limit, check.unit), check.unit
            )
            lines.append(
                f"| {check.name} | {_pair(check)} | {target} | {check.margin * 100:+.0f}% | "
                f"{check.verdict} |"
            )
        notes = [f"- {c.name}: {c.note}" for c in result.checks if c.note]
        if result.least_power_speed is not None:
            notes.append(
                f"- Cheapest speed: {result.least_power_speed:.1f} m/s, for "
                f"{fmt_value(result.least_power_minutes, 'min', True)} min of cruise."
            )
        if result.top_speeds_kmh:
            tops = result.top_speeds_kmh
            notes.append(
                f"- Top speed: {tops['full']:.0f} km/h on a full pack, {tops['half']:.0f} at half "
                f"charge, {tops['reserve']:.0f} at the reserve."
            )
        lines += ["", *notes, "", "</details>", ""]

    lines += [
        f"## Mass budget: {sizing.setup.name}",
        "",
        "| Line | Mass |",
        "|---|---|",
        *(f"| {line.name} | {units.kg_to_g(line.mass):.0f} g |" for line in sizing.mass.lines),
        f"| **Total** | **{units.kg_to_g(sizing.mass.total):.0f} g** |",
        "",
        "## One flight, start to reserve",
        "",
        "![One flight, start to reserve](charts/battery.png)",
        "",
        "## Power and speed",
        "",
        "![Power against airspeed](charts/power.png)",
        "",
    ]
    if sizing.least_power_speed is not None:
        lines += [
            f"The cruise targets are checked at {targets.cruise_speed:g} m/s for now. The speed "
            f"that actually costs {sizing.setup.name} the least is "
            f"{sizing.least_power_speed:.1f} m/s, where it cruises for "
            f"{fmt_value(sizing.least_power_minutes, 'min', True)} min.",
            "",
        ]
    if sweep is not None:
        lines += [
            "## The sweep",
            "",
            f"{len(sweep.ranked)} builds tried, ranked by verdict, then by how far their tightest "
            "required check clears its limit.",
            "",
            "![Every build the sweep tried](charts/sweep.png)",
            "",
            f"| Rank | Build | Frame | Verdict | Tightest margin | {sizing.setup.name} cruise |",
            "|---|---|---|---|---|---|",
        ]
        for rank, c in enumerate(sweep.ranked[:10], start=1):
            lines.append(
                f"| {rank} | {c.build.label} | {c.build.frame.model} | {c.verdict} | "
                f"{c.tightest_margin * 100:+.0f}% | "
                f"{fmt_value(c.sizing_cruise_minutes, 'min', True)} min |"
            )
        if sweep.skipped:
            lines += ["", "Skipped, because the parts don't go together:", ""]
            lines += [f"- {label}: {reason}" for label, reason in sweep.skipped]
        lines.append("")
    if margin is not None:
        required = [r.setup.name for r in design.setups if r.setup.required]
        grams = [p.grams for p in margin.get(targets.sizing_case, [])]
        lines += [
            "## What extra weight costs",
            "",
            "![What extra weight costs](charts/margin.png)",
            "",
            "Cruise minutes as extra grams go on:",
            "",
            "| Setup | " + " | ".join(f"+{g:.0f} g" for g in grams) + " |",
            "|---|" + "---|" * len(grams),
        ]
        for name in required:
            points = margin.get(name, [])
            row = " | ".join(fmt_value(p.cruise_minutes, "min", True) for p in points)
            lines.append(f"| {name} | {row} |")
        lines.append("")
    derate = ", ".join(f"{SOURCE_WORDS[k.value]} {v * 100:.0f}%" for k, v in rotor.DERATE.items())
    lines += [
        "## How the numbers are made",
        "",
        "- **Hover** power comes straight from the thrust table (volts x amps at the table's "
        "voltage). The battery model turns it into current with the pack's sag included.",
        f"- **Forward flight** splits each prop's power into lifting power, blade drag and the "
        f"power to push the drone through the air, fitted to the hover table. Real rotors need "
        f"{(rotor.INDUCED_FACTOR - 1) * 100:.0f}% more lifting power than ideal theory, and blade "
        f"drag takes {rotor.PROFILE_SHARE * 100:.0f}% of a small prop's hover power.",
        "- **The battery** is each cell's resting-voltage curve plus its internal resistance, "
        "scaled to the pack plus the wiring, stepped through the flight a few seconds at a time.",
        f"- **Pessimistic data** cuts every thrust in the table: {derate}.",
        f"- **Holding position in wind** means flying at that airspeed at the 20% reserve with "
        f"{(checks_module.GUST_HEADROOM - 1) * 100:.0f}% more thrust available than needed. "
        f"**Top speed** is checked at {checks_module.TOP_SPEED_SOC * 100:.0f}% charge, and the "
        f"drone won't lean past {rotor.MAX_TILT * 180 / 3.141592653589793:.0f} degrees.",
        "",
        "## What this can't tell you",
        "",
        "- Manufacturer thrust data runs optimistic. The pessimistic numbers allow for that, but "
        "only a thrust stand can say by how much.",
    ]
    below = _hover_below_the_table(design)
    if below:
        lines.append(below)
    lines += [
        "- Cruise is the shakiest number here. The honesty check ([validation.md](validation.md)) "
        "flew a published long-range build through the model, and its cruise time came out much "
        "longer than the measured one, most likely because the drag of the props at speed isn't "
        "modeled yet. Trust the hover numbers more than the cruise ones for now.",
        "- Drag is a guess from frontal area until the wind tunnel side track has real numbers.",
        "- Coming straight down fast (the vortex ring state), cold weather and aging cells aren't "
        "modeled.",
        "- The ESC's limits, wiring losses and heat get checked in the electrical step.",
        "",
    ]
    return "\n".join(lines)
