"""The CAD run and its report: every module combination built, trimmed and checked, plus the
printed parts, the wires, what's estimated and the existing CAD models, written up as
docs/reports/cad/README.md and cad.json (for the Gazebo generator and the project site).
"""

import json
from dataclasses import dataclass
from pathlib import Path

from pcs14 import __version__
from pcs14.cad import existing as existing_cad
from pcs14.cad.assembly import Drone
from pcs14.cad.checks import CombinationResult, check_combination, trim
from pcs14.cad.mass import mass_properties
from pcs14.cad.parts import build_part
from pcs14.cad.printed import PrintedPart, build_printed

MM = 0.001
BIGGEST_TO_COMPARE = 40_000_000  # bytes; bigger existing models take minutes to load
MODULE_ORDER = {"base": 0, "V": 1, "P": 2, "C": 3}
KIND_ORDER = {"frame": 0, "motor": 1, "prop": 2, "pack": 3, "bought": 4, "printed": 5, "wire": 6}


@dataclass(frozen=True)
class Estimate:
    part_id: str
    dimensions: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class ExistingRow:
    part_id: str
    found: str
    terms: str | None
    compared: str | None  # what the comparison found, if the model is in the cache


@dataclass(frozen=True)
class HardwareRow:
    holds: str
    what: str  # e.g. "M3 x 12 screw"
    count: int
    material: str
    each_g: float


@dataclass(frozen=True)
class PieceRow:
    """One piece of the full drone, named as the GLB names its node (the project site's
    explorer matches them up)."""

    name: str
    kind: str  # frame, motor, prop, pack, bought, printed or wire
    module: str  # base, V, P or C
    mass_g: float
    part_id: str | None
    moving: bool


@dataclass(frozen=True)
class CadRun:
    build_label: str
    results: tuple[CombinationResult, ...]
    printed: tuple[PrintedPart, ...]
    catalog_masses: dict[str, float]  # kg, the catalog's guess for each printed part's entry
    wire_lengths: dict[str, float]  # m
    estimates: tuple[Estimate, ...]
    existing: tuple[ExistingRow, ...]
    exports: tuple[str, ...]
    hardware: tuple[HardwareRow, ...] = ()
    pieces: tuple[PieceRow, ...] = ()  # the full drone's, as the GLB has them

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)


def _parts(build):
    """Every distinct catalog part in the build (catalog parts can't be hashed, so by id)."""
    every = [build.motor, build.prop, build.esc, build.frame, build.pack.cell, *build.base]
    for module in build.modules.values():
        every += module
    return list({part.id: part for part in every}.values())


def _compare(part, cache: Path) -> str | None:
    path = existing_cad.cached_model(cache, part.id)
    if path is None:
        return None
    if path.stat().st_size > BIGGEST_TO_COMPARE:
        size = path.stat().st_size // 1_000_000
        return f"in the cache, but {size} MB is too big to compare on every run"
    if part.cad.shape not in ("board", "box", "cylinder", "motor", "cell"):
        return None
    holes = getattr(part.cad, "holes", [])
    diameter = holes[0].diameter if holes else None
    result = existing_cad.compare(build_part(part), existing_cad.load_model(path), diameter)
    return result.note


def run_cad(drone: Drone, setups, cache: Path = existing_cad.CACHE, recorder=None) -> CadRun:
    results = tuple(check_combination(drone, s.name, s.modules) for s in setups)
    build = drone.build
    printed = tuple(build_printed(build, drone.settings, drone.frame))
    catalog = {part.id: part.mass for part in _parts(build)}
    estimates = tuple(
        Estimate(part.id, tuple(part.cad.estimates), part.cad.estimate_note or "")
        for part in _parts(build)
        if part.cad is not None and part.cad.estimates
    )
    rows = []
    for part in _parts(build):
        found = part.cad.existing
        rows.append(ExistingRow(part.id, found.found, found.terms, _compare(part, cache)))
    full = drone.combination({"V", "P", "C"})
    from pcs14.cad import hardware as fasteners

    hardware = tuple(
        HardwareRow(
            item.holds,
            " ".join(
                x
                for x in (
                    item.size,
                    f"x {item.length_mm:g}" if item.length_mm else None,
                    item.what,
                )
                if x
            ),
            item.count,
            item.material or "",
            fasteners.item_mass(item, drone.settings.materials) * 1000,
        )
        for item in drone.settings.hardware
    )
    run = CadRun(
        build_label=build.label,
        results=results,
        printed=printed,
        catalog_masses={
            p.catalog_id: catalog[p.catalog_id] for p in printed if p.catalog_id in catalog
        },
        wire_lengths=dict(full.wire_lengths),
        estimates=estimates,
        existing=tuple(rows),
        exports=(),
        hardware=hardware,
        pieces=tuple(
            PieceRow(p.name, p.kind, p.module, round(p.mass * 1000, 3), p.part_id, p.moving)
            for p in full.pieces
        ),
    )
    if recorder is not None:
        _record(drone, setups, results, recorder)
    return run


def _record(drone: Drone, setups, results, recorder) -> None:
    full = drone.combination({"V", "P", "C"})
    pieces = sorted(full.pieces, key=lambda p: (MODULE_ORDER[p.module], KIND_ORDER[p.kind]))
    names = [p.name for p in pieces]
    recorder.log_pieces(pieces)
    recorder.log_build_up(names)
    step = len(names) + 1
    recorder.log_prop_disks(full.prop_disks, step)
    thrust = (0.0, 0.0, full.prop_disks[0].bounding_box().min.Z)
    for setup, result in zip(setups, results, strict=True):
        assembly = drone.combination(setup.modules, pack_x=result.trim_x)
        trouble = {name for f in result.findings if not f.passed for name in f.parts}
        for _ in range(4):  # hold each combination for a moment
            recorder.log_combination(
                step=step,
                label=setup.name,
                shown={p.name for p in assembly.pieces},
                all_names=names,
                pack_shift=result.trim_x - drone.home_x,
                center=result.mass.center,
                thrust=thrust,
                problems=[p for p in assembly.pieces if p.name in trouble],
                passed=result.passed,
            )
            step += 1
    chute_id = "fruity-chutes-harrier-40-42"
    chutes = [p for p in drone.build.modules.get("P", ()) if p.id == chute_id]
    if chutes:
        x, y, z = drone.settings.place[chute_id].at
        checks = drone.settings.checks
        recorder.log_cone(
            (x, y, z + chutes[0].cad.size("length_mm")),
            chutes[0].cad.size("diameter_mm") / 2,
            checks.chute_cone_half_angle_deg,
            checks.chute_cone_height,
            step,
        )
    recorder.log_explode(step + 1, pieces)
    recorder.log_summary(_combination_table(results))


def _mm(value: float) -> str:
    return f"{value / MM:.0f}"


def _modules(result) -> str:
    return "+".join(m for m in "VPC" if m in result.modules) or "none"


def _verdict(result) -> str:
    return "pass" if result.passed else "fail"


def _combination_table(results) -> str:
    lines = [
        "| Setup | Modules | Weight | Pack at | Center of gravity (x, y, z) | Busiest motor "
        "| Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        x, y, z = (v / MM for v in r.mass.center)
        lines.append(
            f"| {r.setup} | {_modules(r)} | {r.mass.mass * 1000:.0f} g | {_mm(r.trim_x)} mm | "
            f"{x:.1f}, {y:.1f}, {z:.1f} mm | +{r.overload * 100:.1f}% | {_verdict(r)} |"
        )
    return "\n".join(lines)


def render(run: CadRun, generated: str | None = None) -> str:
    when = f" on {generated}" if generated else ""
    lines = [
        "# The virtual drone (CAD)",
        "",
        f"*Generated{when} by pcs14 {__version__}, the CAD layer in `src/pcs14/cad/`. Every "
        "module combination gets built, its pack slid to where it balances best, and checked: "
        "collisions, prop clearance, the parachute's cone, the module rail, balance, and the "
        "makers' placement rules.*",
        "",
        "![The drone, three-quarter view](views/three-quarter.png)",
        "",
        "## The verdict",
        "",
    ]
    failing = [r for r in run.results if not r.passed]
    if not failing:
        lines.append(f"**Pass.** All {len(run.results)} combinations pass every check.")
    else:
        which = "; ".join(
            f"{r.setup} ({', '.join(dict.fromkeys(f.check for f in r.findings if not f.passed))})"
            for r in failing
        )
        verb = "misses" if len(failing) == 1 else "miss"
        lines.append(
            f"**Fail.** {len(failing)} of {len(run.results)} combinations {verb} a check: {which}."
        )
    lines += [
        "",
        f"Built from {run.build_label}.",
        "",
        "## Every module combination",
        "",
        _combination_table(run.results),
        "",
        "The pack's position is along x from the motors' center; it slides to balance each "
        "combination. The busiest motor column says how much harder the busiest motor works "
        "than the average in a hover (the limit is +5%).",
        "",
        "Every check, setup by setup:",
        "",
    ]
    for r in run.results:
        lines += [
            "<details>",
            f"<summary>{r.setup}: {_verdict(r)}</summary>",
            "",
            "| Check | Result | Verdict |",
            "|---|---|---|",
        ]
        ordered = sorted(r.findings, key=lambda f: f.passed)
        lines += [f"| {f.check} | {f.detail} | {'pass' if f.passed else 'fail'} |" for f in ordered]
        lines += ["", "</details>", ""]
    lines += [
        "## Mass properties",
        "",
        "Each part's weight spread over its solid, with the pack at its trim. Inertia is about "
        "the center of gravity.",
        "",
        "| Setup | Weight | Ixx | Iyy | Izz |",
        "|---|---|---|---|---|",
    ]
    for r in run.results:
        i = r.mass.inertia
        lines.append(
            f"| {r.setup} | {r.mass.mass * 1000:.0f} g | {i[0][0] * 1000:.1f} g m² | "
            f"{i[1][1] * 1000:.1f} g m² | {i[2][2] * 1000:.1f} g m² |"
        )
    lines += [
        "",
        "## My printed parts",
        "",
        "Weighed from their geometry and material, next to what the catalog says for each one's "
        "entry (pcs14 cad --update-catalog writes the CAD's numbers in).",
        "",
        "| Part | Material | Weight | Its catalog entry |",
        "|---|---|---|---|",
    ]
    groups: dict[str, list[PrintedPart]] = {}
    for part in run.printed:
        groups.setdefault(part.catalog_id, []).append(part)
    for part in run.printed:
        group = groups[part.catalog_id]
        entry = run.catalog_masses.get(part.catalog_id)
        cad_total = sum(p.mass for p in group)
        if entry is None:
            listed = f"not in the catalog yet ({part.catalog_id})"
        elif abs(entry - cad_total) < 0.00015:
            shared = f" for all {len(group)}" if len(group) > 1 else ""
            listed = f"{entry * 1000:.1f} g{shared}, from the CAD ({part.catalog_id})"
        else:
            listed = f"{entry * 1000:.0f} g, a guess the CAD replaces ({part.catalog_id})"
        lines.append(f"| {part.name} | {part.material} | {part.mass * 1000:.1f} g | {listed} |")
    total = sum(p.mass for p in run.printed)
    lines += [
        "",
        f"Together they weigh {total * 1000:.0f} g.",
        "",
        "## Wires",
        "",
        "Each route's length. The wires in them, their gauges and their weight come from the "
        "electrical connection list (docs/reports/electrical).",
        "",
        "| Wire | Length |",
        "|---|---|",
    ]
    lines += [f"| {name} | {length / MM:.0f} mm |" for name, length in run.wire_lengths.items()]
    lines += ["", "## Hardware", ""]
    if run.hardware:
        lines += [
            "The screws, nuts and spacers, counted from the CAD's holes and weighed from their "
            "standard sizes. Each one's weight sits on the part it holds.",
            "",
            "| Holds | What | How many | Material | Each | All of them |",
            "|---|---|---|---|---|---|",
        ]
        lines += [
            f"| {h.holds} | {h.what} | {h.count} | {h.material} | {h.each_g:.2f} g | "
            f"{h.count * h.each_g:.1f} g |"
            for h in run.hardware
        ]
        total = sum(h.count * h.each_g for h in run.hardware)
        lines += ["", f"Together they weigh {total:.0f} g."]
    else:
        lines.append("None listed.")
    lines += ["", "## What's estimated", ""]
    if run.estimates:
        lines += [f"- {e.part_id}: {', '.join(e.dimensions)}. {e.note}" for e in run.estimates]
    else:
        lines.append("Nothing.")
    lines += [
        "",
        "## Existing CAD models",
        "",
        "Checked for every part before modeling it. They stay in a local cache that never gets "
        "committed, and get compared with my parts by size and hole spacing.",
        "",
        "| Part | Found | Terms | Compared with mine |",
        "|---|---|---|---|",
    ]
    for row in run.existing:
        compared = row.compared or ("not downloaded" if row.found != "none" else "")
        lines.append(f"| {row.part_id} | {row.found} | {row.terms or ''} | {compared} |")
    lines += ["", "## Files", ""]
    if run.exports:
        lines.append("Generated on every run, and not committed (they're build outputs):")
        lines.append("")
        lines += [f"- `{path}`" for path in run.exports]
    else:
        lines.append("Not exported on this run.")
    lines += [
        "",
        "## Views",
        "",
        "![Front](views/front.png) ![Side](views/side.png) ![Top](views/top.png) "
        "![Exploded](views/exploded.png)",
        "",
    ]
    return "\n".join(lines)


def to_data(run: CadRun, generated: str | None = None) -> dict:
    def finding(f):
        return {
            "check": f.check,
            "passed": f.passed,
            "value": f.value,
            "limit": f.limit,
            "detail": f.detail,
            "parts": list(f.parts),
        }

    return {
        "generated": generated,
        "pcs14_version": __version__,
        "build": run.build_label,
        "verdict": "pass" if run.passed else "fail",
        "combinations": [
            {
                "setup": r.setup,
                "modules": sorted(r.modules),
                "passed": r.passed,
                "trim_x_mm": round(r.trim_x / MM, 3),
                "mass_g": round(r.mass.mass * 1000, 3),
                "center_of_gravity_mm": [round(v / MM, 3) for v in r.mass.center],
                "inertia_kg_m2": [list(row) for row in r.mass.inertia],
                "busiest_motor_extra": round(r.overload, 6),
                "findings": [finding(f) for f in r.findings],
            }
            for r in run.results
        ],
        "pieces": [vars(p) for p in run.pieces],
        "printed_parts": [
            {
                "name": p.name,
                "material": p.material,
                "mass_g": round(p.mass * 1000, 3),
                "module": p.module,
                "catalog_id": p.catalog_id,
            }
            for p in run.printed
        ],
        "wire_lengths_mm": {
            name: round(length / MM, 3) for name, length in run.wire_lengths.items()
        },
        "estimates": [
            {"part": e.part_id, "dimensions": list(e.dimensions), "note": e.note}
            for e in run.estimates
        ],
        "existing_cad": [
            {"part": r.part_id, "found": r.found, "terms": r.terms, "compared": r.compared}
            for r in run.existing
        ],
        "exports": list(run.exports),
        "hardware": [
            {
                "holds": h.holds,
                "what": h.what,
                "count": h.count,
                "material": h.material,
                "each_g": round(h.each_g, 3),
            }
            for h in run.hardware
        ],
    }


def write_cad_report(
    out: Path,
    run: CadRun,
    drone: Drone,
    generated: str | None = None,
    exports: Path | None = None,
) -> CadRun:
    """README.md and cad.json in `out`; with `exports`, also the files and the stills."""
    from dataclasses import replace

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if exports is not None:
        from pcs14.cad import export
        from pcs14.cad.views import render_stills

        exports = Path(exports)
        full = trim(drone, {"V", "P", "C"})
        files = [
            export.export_step_file(full.pieces, exports / "drone.step"),
            export.export_gazebo(full.pieces, exports / "drone-gazebo.stl"),
            export.export_cfd(full.pieces, exports / "drone-cfd.stl"),
            export.export_glb(full.pieces, exports / "drone.glb"),
        ]
        for part in run.printed:
            files += export.export_print_files(part, exports / "print")
        render_stills(full.pieces, out / "views", title="Extra 15pc Gum, in CAD")
        run = replace(run, exports=tuple(path.as_posix() for path in files))
    (out / "README.md").write_bytes(render(run, generated).encode("utf-8"))
    (out / "cad.json").write_bytes(
        (json.dumps(to_data(run, generated), indent=1) + "\n").encode("utf-8")
    )
    return run


def summary(run: CadRun) -> str:
    """The short version for the terminal."""
    verdict = "pass" if run.passed else "fail"
    return (
        f"CAD: {len(run.results)} module combinations, verdict: {verdict}\n\n"
        + _combination_table(run.results)
    )


def mass_of(run: CadRun, setup: str):
    result = next(r for r in run.results if r.setup == setup)
    return result.mass


__all__ = ["CadRun", "mass_properties", "run_cad", "render", "to_data", "write_cad_report"]
