"""The parts list: what to buy, print and cut for each module, what it costs, and a second
choice for each bought part.

- Bought parts come from the build and the catalog: four motors and props, the ESC, the frame,
  the pack's cells, then each module's parts. A catalog part that bundles small parts (the
  safety monitor's buffers on their adapters) is one line, priced as the set.
- Wire comes from the connection list: each wire's route length in the CAD (or its own length
  for a short jumper), added up by type and gauge, with SLACK on top for mistakes and trimming.
- Plugs come from the connection list too: the wire's half of each plug it lands in, the way
  the wiring's weight counts them. The module plugs and sockets are parts of their own.
- Screws, nuts and spacers come from the CAD report's hardware list, rolled up by size.
- Printed parts come from the CAD report, with their material and grams; `pcs14 cad` writes
  their 3MF files.
- What isn't on the drone (the transmitter, a charger, the pack's supplies, tools, spares) comes
  from design/package.yaml.

A part without a price counts as unpriced, never as free: the totals say how many are missing.
"""

import csv
import io
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml
from pydantic import Field, HttpUrl

from pcs14.catalog.schema import Fallback
from pcs14.catalog.source import Strict

SLACK = 1.3  # wire bought against wire needed
MATERIALS = {"tpu": "TPU", "petg_cf": "PETG-CF", "petg": "PETG"}
MODULES = ("V", "P", "C")
GROUPS = ("bought", "wire", "plug", "hardware", "printed")
ONCE = ("ground", "supplies", "tools", "spares")  # bought once, whatever's fitted
BUNDLES = ("-wiring", "-hardware")  # catalog parts that only carry weight; listed as their pieces


@dataclass(frozen=True)
class Line:
    group: str  # bought, wire, plug, hardware, printed, or one of ONCE
    module: str  # base, V, P, C, or "once"
    name: str  # what it is, in words
    qty: float
    unit: str = ""  # "" for a count, "m" for wire
    maker: str = ""
    model: str = ""
    link: str | None = None
    price_each: float | None = None  # USD per unit
    checked: str | None = None
    fallback: str = ""
    note: str = ""
    part_id: str | None = None

    @property
    def total(self) -> float | None:
        return None if self.price_each is None else self.price_each * self.qty


def fallback_text(fallback: Fallback | None) -> str:
    if fallback is None:
        return ""
    if fallback.none:
        return f"none: {fallback.note}"
    name = f"{fallback.maker} {fallback.model}"
    if fallback.link is not None:
        name = f"[{name}]({fallback.link})"
    return f"{name}: {fallback.note}"


def _line(
    part, module: str, qty: float, group: str = "bought", name: str | None = None, note: str = ""
) -> Line:
    return Line(
        group=group,
        module=module,
        name=name or part.model,
        qty=qty,
        maker=part.maker,
        model=part.model,
        link=str(part.link) if part.link else None,
        price_each=part.price_usd,
        checked=part.checked.isoformat() if part.checked else None,
        fallback=fallback_text(part.fallback),
        note="; ".join(x for x in (note, part.buy_note) if x),
        part_id=part.id,
    )


def bought_lines(build, printed_ids=frozenset()) -> list[Line]:
    """The bought parts, Base's then each module's. Printed parts and the catalog's weight-only
    bundles (wiring, hardware) are left to their own lists."""
    cells = build.pack.series * build.pack.parallel
    lines = [
        _line(build.motor, "base", 4, name="Motor"),
        _line(build.prop, "base", 4, name="Prop", note="two turn each way"),
        _line(build.esc, "base", 1, name="4-in-1 ESC"),
        _line(build.frame, "base", 1, name="Frame"),
        _line(
            build.pack.cell,
            "base",
            cells,
            name="Cell",
            note=f"for the {build.pack.series}S{build.pack.parallel}P pack",
        ),
    ]
    sections = [("base", build.base)] + [(m, build.modules.get(m, ())) for m in MODULES]
    for module, parts in sections:
        seen: dict[str, int] = {}
        for part in parts:
            if part.id in printed_ids or part.id.endswith(BUNDLES):
                continue
            seen[part.id] = seen.get(part.id, 0) + 1
        for part in parts:
            if part.id in seen:
                lines.append(_line(part, module, seen.pop(part.id)))
    return lines


def wire_lines(runs, wires, slack: float = SLACK) -> list[Line]:
    """`runs`: (wire id, gauge, module, meters) for every wire. One line per module, type and
    gauge, rounded up to the next 10 cm after the slack."""
    totals: dict[tuple[str, str, int], float] = {}
    for wire_id, awg, module, meters in runs:
        key = (module, wire_id, awg)
        totals[key] = totals.get(key, 0.0) + meters
    lines = []
    for (module, wire_id, awg), meters in sorted(totals.items(), key=lambda kv: kv[0]):
        part = wires[wire_id]
        gauge = next((g for g in part.gauges if g.awg == awg), None)
        buy = math.ceil(meters * slack * 10) / 10
        link = getattr(gauge, "link", None) or part.link
        per_m = getattr(gauge, "price_usd_per_m", None)
        lines.append(
            Line(
                group="wire",
                module=module,
                name=f"{part.model}, {awg} AWG",
                qty=buy,
                unit="m",
                maker=part.maker,
                model=part.model,
                link=str(link) if link else None,
                price_each=per_m,
                checked=part.checked.isoformat() if part.checked else None,
                fallback=fallback_text(part.fallback),
                note=f"{meters:.2f} m in the connection list, plus {slack - 1:.0%}",
                part_id=wire_id,
            )
        )
    return lines


def plug_lines(halves, parts) -> list[Line]:
    """`halves`: (module, family, pins) for each plug half the wires need. One line per module,
    family and size."""
    counts: dict[tuple[str, str, int], int] = {}
    for module, family, pins in halves:
        counts[(module, family, pins)] = counts.get((module, family, pins), 0) + 1
    lines = []
    for (module, family, pins), count in sorted(counts.items()):
        part = parts[family]
        size = f", {pins}-pin" if pins > 2 else ""
        lines.append(
            _line(
                part,
                module,
                count,
                group="plug",
                name=f"{part.model}{size}",
                note="the wire's half",
            )
        )
    return lines


def hardware_lines(hardware, module_of) -> list[Line]:
    """The CAD report's hardware (holds, what, count, material), rolled up by module, size and
    material."""
    counts: dict[tuple[str, str, str], int] = {}
    for item in hardware:
        module = module_of.get(item["holds"], "base")
        key = (module, item["what"], item.get("material") or "")
        counts[key] = counts.get(key, 0) + int(item["count"])
    return [
        Line(
            group="hardware",
            module=module,
            name=f"{what}" + (f", {material}" if material else ""),
            qty=count,
            maker="Any",
            model=what,
            note="standard size; any good supplier",
        )
        for (module, what, material), count in sorted(counts.items())
    ]


def printed_lines(printed) -> list[Line]:
    """The CAD report's printed parts: one line each, with its material and grams."""
    return [
        Line(
            group="printed",
            module=p["module"] if p["module"] in MODULES else "base",
            name=p["name"],
            qty=1,
            maker="Printed",
            model=MATERIALS.get(p["material"], p["material"]),
            note=f"{p['mass_g']:.1f} g of {p['material'].upper()}; "
            f"outputs/cad/print/{p['name'].replace(' ', '-')}.3mf from pcs14 cad",
            part_id=p.get("catalog_id"),
        )
        for p in printed
    ]


# --- what isn't on the drone ---------------------------------------------------------------


class Extra(Strict):
    id: str
    module: str = Field(default="once", pattern="^(once|base|V|P|C)$")  # where it's needed
    group: str = Field(pattern="^(ground|supplies|tools|spares)$")
    name: str
    why: str
    maker: str
    model: str
    qty: float = Field(default=1, gt=0)
    link: HttpUrl | None = None
    price_usd: float | None = Field(default=None, ge=0)
    checked: date | None = None
    fallback: Fallback | None = None


class Extras(Strict):
    items: list[Extra]


def load_extras(path) -> list[Extra]:
    return Extras.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8"))).items


def extra_lines(extras) -> list[Line]:
    return [
        Line(
            group=e.group if e.module == "once" else "bought",
            module=e.module,
            name=e.name,
            qty=e.qty,
            maker=e.maker,
            model=e.model,
            link=str(e.link) if e.link else None,
            price_each=e.price_usd,
            checked=e.checked.isoformat() if e.checked else None,
            fallback=fallback_text(e.fallback),
            note=e.why,
            part_id=e.id,
        )
        for e in extras
    ]


# --- totals -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Total:
    setup: str
    usd: float  # of the priced lines
    unpriced: int  # lines with no price, which aren't in usd
    lines: int
    printed: int = 0
    printed_g: float = 0.0
    missing: list = field(default_factory=list)  # the unpriced lines' names


def totals(lines, combinations) -> list[Total]:
    """For each combination (name, modules): the drone's bought parts, wire and plugs. Printed
    parts are counted in grams of filament; hardware is cheap and unpriced, so it's left out of
    the missing count; what's bought once is its own total, "once"."""
    out = []
    for name, modules in list(combinations) + [("once", None)]:
        if modules is None:
            picked = [x for x in lines if x.module == "once"]
        else:
            fitted = {"base", *modules}
            picked = [x for x in lines if x.module in fitted and x.module != "once"]
        priced = [
            x
            for x in picked
            if x.group in GROUPS + ONCE and x.group != "printed" and x.group != "hardware"
        ]
        missing = [x.name for x in priced if x.total is None]
        out.append(
            Total(
                setup=name,
                usd=sum(x.total for x in priced if x.total is not None),
                unpriced=len(missing),
                lines=len(picked),
                printed=sum(1 for x in picked if x.group == "printed"),
                printed_g=sum(
                    float(x.note.split(" g ")[0]) for x in picked if x.group == "printed"
                ),
                missing=missing,
            )
        )
    return out


# --- writing ------------------------------------------------------------------------------

CSV_FIELDS = (
    "module",
    "group",
    "name",
    "qty",
    "unit",
    "maker",
    "model",
    "price_each_usd",
    "total_usd",
    "link",
    "checked",
    "fallback",
    "note",
    "part_id",
)


def to_csv(lines) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(CSV_FIELDS)
    for x in lines:
        writer.writerow(
            [
                x.module,
                x.group,
                x.name,
                f"{x.qty:g}",
                x.unit,
                x.maker,
                x.model,
                "" if x.price_each is None else f"{x.price_each:.2f}",
                "" if x.total is None else f"{x.total:.2f}",
                x.link or "",
                x.checked or "",
                x.fallback,
                x.note,
                x.part_id or "",
            ]
        )
    return out.getvalue()


def _money(v: float | None) -> str:
    return "?" if v is None else f"${v:,.2f}"


def _made_by(x: Line) -> str:
    """The maker, and the model where the name doesn't already say it."""
    return x.maker if x.model in x.name else f"{x.maker} {x.model}"


def _name(x: Line) -> str:
    return f"[{x.name}]({x.link})" if x.link else x.name


SECTION_NAMES = {
    "base": "Base",
    "V": "V: vision and nav",
    "P": "P: the parachute",
    "C": "C: the claws",
    "once": "Bought once",
}
GROUP_NAMES = {
    "bought": "Parts",
    "wire": "Wire",
    "plug": "Plugs",
    "hardware": "Screws, nuts and spacers",
    "printed": "Printed",
    "ground": "On the ground",
    "supplies": "Supplies",
    "tools": "Tools",
    "spares": "Spares",
}


def render(lines, sums, generated: str) -> str:
    out = [
        "# The parts list",
        "",
        f"*Generated {generated} by `pcs14 package`, from the catalog, the build, the "
        "connection list and the CAD report. The same list is in [parts.csv](parts.csv). "
        "Prices are what the shop showed on the day each part was checked, in US dollars, "
        "and they drift. A ? is a price nobody's checked yet; it isn't counted as free.*",
        "",
        "## What each combination costs",
        "",
        "| Combination | Bought parts, wire and plugs | Not priced yet | Printed |",
        "|---|---|---|---|",
    ]
    for t in sums:
        if t.setup == "once":
            continue
        out.append(
            f"| {t.setup} | {_money(t.usd)} | {t.unpriced} | {t.printed} parts, "
            f"{t.printed_g:.0f} g |"
        )
    once = next((t for t in sums if t.setup == "once"), None)
    if once is not None:
        out += [
            "",
            f"Bought once, whatever's fitted (the transmitter, a charger, supplies, "
            f"tools): {_money(once.usd)}, with {once.unpriced} not priced yet.",
            "Screws, nuts and spacers aren't priced: they're a few dollars from any "
            "hardware supplier.",
        ]
    for module in ("base", *MODULES, "once"):
        picked = [x for x in lines if x.module == module]
        if not picked:
            continue
        out += ["", f"## {SECTION_NAMES[module]}"]
        for group in GROUPS + ONCE:
            rows = [x for x in picked if x.group == group]
            if not rows:
                continue
            out += ["", f"### {GROUP_NAMES[group]}", ""]
            if group in ("hardware",):
                out += ["| Part | How many |", "|---|---|"]
                out += [f"| {x.name} | {x.qty:g} |" for x in rows]
                continue
            if group == "printed":
                out += ["| Part | Material | Note |", "|---|---|---|"]
                out += [f"| {x.name} | {x.model} | {x.note} |" for x in rows]
                continue
            out += [
                "| Part | How many | Each | Total | Checked | If it's gone | Note |",
                "|---|---|---|---|---|---|---|",
            ]
            for x in rows:
                qty = f"{x.qty:g} {x.unit}".strip()
                out.append(
                    f"| {_name(x)}<br>{_made_by(x)} | {qty} | "
                    f"{_money(x.price_each)} | {_money(x.total)} | {x.checked or ''} | "
                    f"{x.fallback} | {x.note} |"
                )
    out += [""]
    return "\n".join(out)


# --- the real drone -----------------------------------------------------------------------


def module_of_parts(build) -> dict[str, str]:
    """Each part id's module: base, or the module whose list has it."""
    out = {p.id: "base" for p in build.base}
    for module in MODULES:
        for p in build.modules.get(module, ()):
            out.setdefault(p.id, module)
    return out


def drone_lines(catalog, build, design, cad_settings, cad_report: dict) -> list[Line]:
    """Every line for the real drone, from the catalog and build, the connection list and the
    CAD's routes, and the CAD report's printed parts and hardware."""
    from pcs14.cad.assembly import wire_length
    from pcs14.electrical.checks import design_context
    from pcs14.electrical.mass import PER_POSITION, SELF_WEIGHED, SOLDERED, _module_of
    from pcs14.electrical.model import PACK

    ctx = design_context(design, catalog, build, cad_settings)
    routes = {w.name: (w.module, wire_length(w)) for w in cad_settings.wires}
    runs, halves, seen = [], [], set()
    for run in design.wires:
        module = _module_of(run, ctx.wiring, routes)
        meters = run.length if run.route is None else routes[run.route][1]
        if not run.own_lead:
            runs.append((run.wire, run.awg, module, meters))
        for ref in run.ends:
            board_name, connector_name, _pin = ref.split(".")
            if board_name == PACK:
                continue
            part_id = design.boards[board_name].part
            connector = ctx.wiring.boards[board_name].block.connector(connector_name)
            family = connector.family
            if family == SOLDERED or part_id in SELF_WEIGHED or family not in ctx.parts:
                continue
            if (board_name, connector_name) in seen:
                continue
            seen.add((board_name, connector_name))
            pins = len(connector.pins) if family in PER_POSITION else 1
            halves.append((module, family, pins))
    printed = cad_report.get("printed_parts", [])
    printed_ids = {p["catalog_id"] for p in printed}
    wires = {p.id: p for p in catalog.all_parts() if p.type == "wire"}
    return (
        bought_lines(build, printed_ids)
        + wire_lines(runs, wires)
        + plug_lines(halves, ctx.parts)
        + hardware_lines(cad_report.get("hardware", []), module_of_parts(build))
        + printed_lines(printed)
    )
