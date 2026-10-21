"""`pcs14 package`: the build package, docs/build/, from the catalog and the build, the
connection list and the CAD's settings, and the reports' own data files.
"""

import json
from pathlib import Path

from pcs14.package import assembly, firmware, legal, parts, testplans, wiring

OPEN = (
    "P in every combination, and an optical flow sensor in Base (step 4's findings): the "
    "package builds what's designed today.",
    "The HaLow card: Heltec's SPI card has no working Pi 5 report yet, and its swap waits for "
    "me. The ground side's HaLow radio waits with it.",
    "V's camera: its bracket tips it 30 degrees for the live video, too oblique for mapping. "
    "A mapping position or a tilt servo is a weight call for me.",
    "The claws (C): a placeholder until the claw conversation.",
    "Fruity Chutes' release servo (Hitec's HS-55 stands in) and the canopy's opening time.",
    "The safety monitor's Teensy image: it needs PJRC's Teensy core, a download for me to approve.",
)


def readme(sums, generated: str) -> str:
    out = [
        "# The build package",
        "",
        f"*Generated {generated} by `pcs14 package`. Everything someone needs to build Extra "
        "15pc Gum from these docs: what to buy and print, how to wire it and put it "
        "together, the firmware, the tests before and after the first flight, and the rules. "
        "It reads the catalog, the build, the connection list and the reports, so it says "
        "exactly what they say.*",
        "",
        "Nothing here has been built yet. The drone exists in simulation, every part a real "
        "one, and these docs are the plan for the first real one. What the sims can't prove "
        "is in the test plans, with the first thing to measure for each.",
        "",
        "## What it costs",
        "",
        "| Combination | Bought parts, wire and plugs | Not priced yet |",
        "|---|---|---|",
    ]
    for t in sums:
        if t.setup != "once":
            out.append(f"| {t.setup} | ${t.usd:,.2f} | {t.unpriced} |")
    once = next((t for t in sums if t.setup == "once"), None)
    if once is not None:
        out += ["", f"Plus what's bought once (the transmitter, a charger, supplies and "
                f"tools): ${once.usd:,.2f} priced so far, {once.unpriced} not yet."]  # fmt: skip
    out += [
        "",
        "## In order",
        "",
        "1. **Read the [test plans](tests.md)** first, the safety checks especially. They say "
        "what has to pass before the props go on.",
        "2. **Buy** from the [parts list](parts.md) ([as a spreadsheet](parts.csv)). Each "
        "part has a second choice, and what changes if it's used.",
        "3. **Print** the printed parts: `pcs14 cad` writes their 3MF files to "
        "`outputs/cad/print/`. TPU where a part should flex (the legs, the GPS mast's "
        "foot and cradle, the Remote ID mount), carbon-filled PETG for the rest.",
        "4. **Wire** each harness from the [wiring guide](wiring.md), with its meter checks.",
        "5. **Assemble** in the order of the [assembly guide](assembly.md).",
        "6. **Flash** PX4 first, from the [firmware guide](firmware.md), with this "
        "combination's parameters.",
        "7. **Test** on the bench, props off, then fly tethered, from the [test plans](tests.md).",
        "8. **Before the first outdoor flight,** the [legal checklist](legal.md).",
        "",
        "## Still open",
        "",
    ]
    out += [f"- {o}" for o in OPEN]
    out += [""]
    return "\n".join(out)


def to_data(lines, sums, generated: str) -> dict:
    return {
        "generated": generated,
        "totals": [{"setup": t.setup, "usd": round(t.usd, 2), "unpriced": t.unpriced,
                    "printed": t.printed, "printed_g": round(t.printed_g, 1)} for t in sums],
        "lines": [{"module": x.module, "group": x.group, "name": x.name, "qty": x.qty,
                   "unit": x.unit, "maker": x.maker, "model": x.model, "link": x.link,
                   "price_each_usd": x.price_each, "total_usd": x.total, "checked": x.checked,
                   "fallback": x.fallback, "note": x.note} for x in lines],
        "open": list(OPEN),
    }  # fmt: skip


def write(out, generated: str, catalog, build, targets, design, settings, docs, exports,
          extras_path=None, renders: bool = True) -> list[Path]:  # fmt: skip
    from pcs14.cad.assembly import wire_length
    from pcs14.site.unproven import unproven_data
    from pcs14.unproven import Unproven

    out, docs = Path(out), Path(docs)
    out.mkdir(parents=True, exist_ok=True)
    cad_report = json.loads((docs / "reports" / "cad" / "cad.json").read_text("utf-8"))
    electrical = json.loads(
        (docs / "reports" / "electrical" / "electrical.json").read_text("utf-8")
    )
    lines = parts.drone_lines(catalog, build, design, settings, cad_report)
    if extras_path is not None and Path(extras_path).is_file():
        lines += parts.extra_lines(parts.load_extras(extras_path))
    combos = [(s.name, tuple(s.modules)) for s in targets.combinations()]
    sums = parts.totals(lines, combos)
    written = []

    def put(name: str, text: str):
        path = out / name
        path.write_bytes(text.encode("utf-8"))
        written.append(path)

    put("parts.md", parts.render(lines, sums, generated))
    put("parts.csv", parts.to_csv(lines))
    # without new renders, the ones already there (step k's picture is stills/step-kk-wide.png)
    stills = {}
    for k, step in enumerate(assembly.STEPS, start=1):
        if (out / "stills" / f"step-{k:02d}-wide.png").is_file():
            stills[step.title] = f"stills/step-{k:02d}-wide.png"
    if renders:
        from pcs14.cad.assembly import Drone

        pieces = Drone(build, settings).combination(frozenset({"V", "P", "C"})).pieces
        stills = assembly.render_stills(pieces, out / "stills")
        written += [out / p for p in stills.values()]
    put("assembly.md", assembly.render(settings.hardware, generated, stills))
    parts_by_id = {p.id: p for p in catalog.all_parts()}
    routes = {w.name: (w.module, wire_length(w)) for w in settings.wires}
    put("wiring.md", wiring.render(wiring.rows(design, routes, parts_by_id), generated))
    files = firmware.write_setup_files(exports, out)
    written += files
    put("firmware.md", firmware.render(build, files, generated))
    groups = [(g.name, [Unproven(what=i.what, measure=i.measure) for i in g.items])
              for g in unproven_data(docs).groups]  # fmt: skip
    put("tests.md", testplans.render(electrical, groups, generated))
    put("legal.md", legal.render(generated))
    put("README.md", readme(sums, generated))
    put("package.json", json.dumps(to_data(lines, sums, generated), indent=1) + "\n")
    return written
