"""The whole electrical run, from the connection list to the report's files.

analyze() solves and checks every combination and case, works out the heat, and runs the
switch sims when ngspice is there. to_run() turns that into the plain results the report
needs. make_files() draws what needs the outside tools (the harness diagrams, the KiCad
schematic and its rules check) and the stills, and says what it had to skip.
"""

from dataclasses import dataclass, replace
from pathlib import Path

from pcs14.electrical import report, thermal, tools
from pcs14.electrical.checks import check_design, design_context
from pcs14.electrical.diagrams import Sources, pin_map_markdown, power_tree_markdown
from pcs14.electrical.loads import solve_all
from pcs14.electrical.routes import route_shares

EVERYTHING = frozenset({"V", "P", "C"})


@dataclass
class Analysis:
    design: object
    catalog: object
    build: object
    targets: object
    settings: object  # the CAD settings
    setups: dict  # name -> modules, in order
    solutions: dict
    findings: list
    working: dict  # thermal.wire_working
    connectors: dict  # thermal.connector_working
    curves: list  # thermal.burst_curves
    sims: dict | None  # the switch runs, or None when they didn't run
    sources: Sources
    skipped: tuple[str, ...] = ()

    @property
    def full(self) -> str:
        """The combination with every module in."""
        return next(name for name, modules in self.setups.items() if modules == EVERYTHING)


def _missing(key: str, what: str) -> str:
    tool = tools.TOOLS[key]
    return f"{what}: {tool.name} isn't installed ({tool.install})"


def analyze(design, catalog, build, targets, settings, sims_dir: Path | None = None) -> Analysis:
    """Everything but the files. `sims_dir` is where ngspice works; None skips the sims."""
    from pcs14.cad.assembly import wire_length

    solutions = solve_all(design, catalog, build, targets, settings)
    findings = check_design(design, catalog, build, targets, settings, solutions)
    ctx = design_context(design, catalog, build, settings)
    skipped = []
    sims = None
    if sims_dir is None:
        skipped.append("the switch sims: asked to skip them")
    elif tools.find("ngspice") is None:
        skipped.append(_missing("ngspice", "the switch sims"))
    else:
        from pcs14.electrical.spice import switch

        wiring = switch.Wiring.from_loaded(design, catalog, settings)
        sims = switch.run_all(wiring, Path(sims_dir))
    lengths = {wire.name: wire_length(wire) for wire in settings.wires}
    return Analysis(
        design=design,
        catalog=catalog,
        build=build,
        targets=targets,
        settings=settings,
        setups={s.name: s.modules for s in targets.combinations()},
        solutions=solutions,
        findings=findings,
        working=thermal.wire_working(ctx, solutions),
        connectors=thermal.connector_working(ctx, solutions),
        curves=thermal.burst_curves(ctx, solutions),
        sims=sims,
        sources=Sources.make(design, catalog, build, lengths),
        skipped=tuple(skipped),
    )


def _estimates(design, parts) -> tuple[report.Estimate, ...]:
    boards: dict[str, list[str]] = {}
    for name, board in design.boards.items():
        boards.setdefault(board.part, []).append(name)
    out = []
    for part_id, names in boards.items():
        block = getattr(parts.get(part_id), "electrical", None)
        if block is None:
            continue
        if block.source.kind.value == "estimate":
            out.append(report.Estimate(part_id, tuple(names), (), block.source.note or ""))
        elif block.estimates:
            items = tuple(block.estimates)
            out.append(report.Estimate(part_id, tuple(names), items, block.estimate_note or ""))
    return tuple(out)


def to_run(a: Analysis) -> report.ElectricalRun:
    design, build = a.design, a.build
    parts = a.sources.parts
    cases = tuple(
        report.CaseRow(setup, case, s.case.pack_volts, s.case.battery_amps)
        for (setup, case), s in a.solutions.items()
    )
    heat = tuple(report.HeatRow(n, c[0][1], c[-1][1], limit) for n, c, limit in a.curves)
    switch = None
    if a.sims is not None:
        switch = tuple(
            report.SwitchRow(
                name,
                run.description,
                run.expected_to_pass,
                run.passed,
                tuple(run.esc_frames),
                tuple(run.fc_replies),
                tuple(f"{f.check}: {f.detail}" for f in run.findings),
            )
            for name, run in a.sims.items()
        )
    full = a.full
    tree = power_tree_markdown(
        a.sources, typical=a.solutions[(full, "hover")], worst=a.solutions[(full, "worst")]
    )
    pin_maps = tuple(
        (board, design.boards[board].part, pin_map_markdown(a.sources, board))
        for board in report.PIN_MAPS
        if board in design.boards
    )
    return report.ElectricalRun(
        build_label=build.label,
        boards=len(design.boards),
        wires=len(design.wires),
        safety_paths=len(design.requires),
        combinations=tuple(a.setups),
        problems=(),
        cases=cases,
        findings=tuple(a.findings),
        heat=heat,
        switch=switch,
        route_shares=route_shares(design, a.working),
        wire_amps={key: dict(s.wires) for key, s in a.solutions.items()},
        power_tree=tree,
        pin_maps=pin_maps,
        estimates=_estimates(design, parts),
        unproven=tuple(design.unproven),
        skipped=a.skipped,
        full=full,
        continuous_share=design.checks.continuous_share,
        air_c=design.checks.air_c,
        burst_s=design.checks.burst_s,
        temp_margin_c=design.checks.temp_margin_c,
    )


def make_files(
    out: Path,
    a: Analysis,
    run: report.ElectricalRun,
    exports: Path | None = None,
    stills: bool = True,
):
    """The harness diagrams, the schematic (with KiCad's rules check) and the stills, next to
    the report; the schematic's SVG, too big to commit, in `exports`. Returns the run with its
    files filled in."""
    out = Path(out)
    files, harnesses, outside, skipped = [], [], [], list(run.skipped)
    erc = None
    if tools.find("dot") is not None:
        from pcs14.electrical.diagrams import draw_harnesses

        drawn = draw_harnesses(a.sources, out / "harnesses")
        harnesses = [p.relative_to(out).as_posix() for p in drawn]
        files += harnesses
    else:
        skipped.append(_missing("dot", "the harness diagrams"))
    from pcs14.electrical import kicad

    folder = kicad.Schematic.make(a.design, a.catalog, a.build).write(out / "kicad")
    if tools.find("kicad-cli") is not None:
        sheet = folder / "electrical.kicad_sch"
        erc = len(kicad.erc(sheet))
        if exports is not None:
            outside += [p.as_posix() for p in kicad.export_svg(sheet, Path(exports))]
        # KiCad leaves its per-user settings next to the project; they aren't the design
        for local in folder.glob("*.kicad_prl"):
            local.unlink()
    else:
        skipped.append(_missing("kicad-cli", "the schematic's rules check"))
    files += [p.relative_to(out).as_posix() for p in sorted(folder.iterdir()) if p.is_file()]
    if stills:
        from pcs14.electrical import stills as drawing

        files += [p.relative_to(out).as_posix() for p in drawing.draw_all(out / "stills", a)]
    return replace(
        run,
        files=tuple(sorted(dict.fromkeys(files))),
        harnesses=tuple(harnesses),
        exports=tuple(outside),
        erc=erc,
        skipped=tuple(skipped),
    )


def write(out: Path, run: report.ElectricalRun, generated: str | None = None) -> Path:
    import json

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_bytes(report.render(run, generated).encode("utf-8"))
    data = json.dumps(report.to_data(run, generated), indent=1) + "\n"
    (out / "electrical.json").write_bytes(data.encode("utf-8"))
    return out
