"""The `pcs14` command.

    pcs14 size     evaluate one build: every setup, every check, every flight
    pcs14 sweep    try every build the catalog allows, and rank them
    pcs14 report   write the full sizing report: Markdown, charts and the data file
    pcs14 validate the honesty check: the model against published builds and cell curves
    pcs14 cad      build the drone in CAD, check every module combination, export it
    pcs14 electrical  every wire, pin and connector, checked in every combination

Every run saves a Rerun recording to outputs/rerun/ (or wherever --record says), and --live
opens the viewer and streams into it as the run happens.
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from pcs14 import __version__, units
from pcs14.catalog import CatalogError, load_catalog
from pcs14.design import DesignError, load_build, load_targets
from pcs14.report.formatting import fmt_value

RECORDINGS = Path("outputs") / "rerun"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcs14",
        description="14 pcs left: design and simulation tools for the Extra 15pc Gum drone.",
    )
    parser.add_argument("--version", action="version", version=f"pcs14 {__version__}")
    commands = parser.add_subparsers(dest="command")

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text, description=help_text)
        sub.add_argument("--catalog", type=Path, default=Path("design/catalog"))
        sub.add_argument("--build", type=Path, default=Path("design/build.yaml"))
        sub.add_argument("--targets", type=Path, default=Path("design/targets.yaml"))
        sub.add_argument(
            "--allow-made-up",
            action="store_true",
            help="let the made-up test parts in (their results are stamped as made up)",
        )
        sub.add_argument("--live", action="store_true", help="open the Rerun viewer and stream")
        sub.add_argument("--record", type=Path, help="where to save the Rerun recording")
        sub.add_argument("--no-record", action="store_true", help="don't save a recording")
        return sub

    add("size", "Evaluate one build: every setup, every check, every flight.")
    add("sweep", "Try every build the catalog allows, and rank them.")
    cad = add(
        "cad", "Build the drone in CAD: every part, every module combination, and the checks."
    )
    cad.add_argument("--cad", type=Path, default=Path("design/cad.yaml"), help="the CAD settings")
    cad.add_argument("--out", type=Path, default=Path("docs/reports/cad"), help="report folder")
    cad.add_argument(
        "--exports",
        type=Path,
        default=Path("outputs/cad"),
        help="where STEP, meshes and print files go",
    )
    cad.add_argument(
        "--skip-exports",
        action="store_true",
        help="just the checks and the report, no files or stills",
    )
    cad.add_argument(
        "--update-catalog",
        action="store_true",
        help="write the printed parts' weights into the catalog (then rerun pcs14 report)",
    )
    electrical = add(
        "electrical",
        "The electrical design: every wire, pin and connector, checked in every combination.",
    )
    electrical.add_argument(
        "--tools", action="store_true", help="say where the outside tools are, then stop"
    )
    electrical.add_argument(
        "--electrical",
        type=Path,
        default=Path("design/electrical.yaml"),
        help="the connection list",
    )
    electrical.add_argument("--cad", type=Path, default=Path("design/cad.yaml"))
    report = add("report", "Write the sizing report: Markdown, charts and the data file.")
    report.add_argument("--out", type=Path, help="report folder (default: docs/reports/sizing)")
    report.add_argument(
        "--grams",
        type=int,
        nargs=3,
        metavar=("FROM", "TO", "STEP"),
        default=(0, 600, 100),
        help="extra grams for the margin chart",
    )
    report.add_argument(
        "--sweep-best",
        action="store_true",
        help="write up the sweep's top pick instead of the build file's build",
    )
    validate = commands.add_parser(
        "validate",
        help="The honesty check: the model against published builds and cell curves.",
    )
    validate.add_argument("--catalog", type=Path, default=Path("design/validation/catalog"))
    validate.add_argument("--cases", type=Path, default=Path("design/validation/cases"))
    validate.add_argument(
        "--cells",
        type=Path,
        default=Path("design/catalog"),
        help="catalog whose cells get checked against their discharge tests",
    )
    validate.add_argument("--out", type=Path, default=Path("docs/reports/sizing"))
    validate.add_argument("--allow-made-up", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return COMMANDS[args.command](args)
    except (CatalogError, DesignError, ValueError, OSError) as error:
        print(f"pcs14 {args.command}: {error}", file=sys.stderr)
        return 2


def _load(args):
    catalog = load_catalog(args.catalog, allow_made_up=args.allow_made_up)
    build = load_build(args.build, catalog)
    targets = load_targets(args.targets)
    return catalog, build, targets


def _recorder(args, kind=None):
    if args.no_record and not args.live:
        return None
    from pcs14.viz import Recorder

    kind = kind or Recorder

    path = None
    if not args.no_record:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = args.record or RECORDINGS / f"{args.command}-{stamp}.rrd"
    recorder = kind(path=path, live=args.live)
    if path is not None:
        print(f"Recording to {path}")
    return recorder


def _made_up_line(args) -> str:
    return (
        "MADE-UP TEST PARTS: these numbers say nothing about a real drone.\n"
        if (args.allow_made_up)
        else ""
    )


def _summary(design, made_up: str) -> str:
    targets = design.targets
    cruise = f"Cruise time at {targets.cruise_speed:g} m/s"
    lines = [
        made_up + f"Build: {design.build.label}",
        "",
        f"{'setup':<10}{'weight':>9}{'hover':>10}{'cruise':>10}{'T/W at reserve':>16}  verdict",
    ]
    for result in design.setups:

        def shown(name, unit, result=result):
            return _shown(result, name, unit)

        optional = "" if result.setup.required else " (optional)"
        lines.append(
            f" {result.setup.name:<9}{units.kg_to_g(result.mass.total):>7.0f} g"
            f"{shown('Hover time', 'min'):>7} min{shown(cruise, 'min'):>7} min"
            f"{shown('Thrust-to-weight at the reserve', ':1'):>14}:1  {result.verdict}{optional}"
        )
    lines += ["", f"Verdict: {design.verdict} (sized for {targets.sizing_case})"]
    return "\n".join(lines)


def _shown(result, name: str, unit: str) -> str:
    found = [c for c in result.checks if c.name == name]
    if not found:
        return "-"
    return fmt_value(found[0].nominal, unit, found[0].higher_is_better)


def run_size(args) -> int:
    from pcs14.sizing.checks import evaluate

    _, build, targets = _load(args)
    recorder = _recorder(args)
    design = evaluate(build, targets, recorder=recorder)
    text = _summary(design, _made_up_line(args))
    print(text)
    if recorder is not None:
        recorder.log_summary(f"```\n{text}\n```")
        recorder.close()
    return 0


def run_sweep(args) -> int:
    from pcs14.sizing.sweep import sweep

    catalog, build, targets = _load(args)
    recorder = _recorder(args)
    result = sweep(build, catalog, targets, recorder=recorder)
    lines = [
        _made_up_line(args) + f"{len(result.ranked)} builds tried, {len(result.skipped)} skipped",
        "",
        f"{'rank':>4}  {'verdict':<9}{'margin':>8}{'cruise':>10}  build",
    ]
    for rank, candidate in enumerate(result.ranked, start=1):
        lines.append(
            f"{rank:>4}  {candidate.verdict:<9}{candidate.tightest_margin * 100:>+7.0f}%"
            f"{fmt_value(candidate.sizing_cruise_minutes, 'min', True):>6} min  "
            f"{candidate.build.label}, {candidate.build.frame.model}"
        )
    for label, reason in result.skipped:
        lines.append(f"   skipped  {label}: {reason}")
    text = "\n".join(lines)
    print(text)
    if recorder is not None:
        recorder.log_summary(f"```\n{text}\n```")
        recorder.close()
    return 0


def run_report(args) -> int:
    from pcs14.report import write_report
    from pcs14.sizing.checks import evaluate
    from pcs14.sizing.sweep import margin_curve, sweep

    catalog, build, targets = _load(args)
    out = args.out or Path("docs/reports/sizing")
    start, stop, step = args.grams
    recorder = _recorder(args)
    swept = sweep(build, catalog, targets, recorder=recorder)
    chosen = swept.best.build if args.sweep_best and swept.ranked else build
    design = evaluate(chosen, targets, recorder=recorder)
    margin = margin_curve(chosen, targets, grams=range(start, stop + 1, step))
    written = write_report(
        out,
        design,
        swept,
        margin,
        made_up=args.allow_made_up,
        generated=date.today().isoformat(),
    )
    text = _summary(design, _made_up_line(args))
    print(text)
    print(f"\nReport written to {written}")
    if recorder is not None:
        recorder.log_summary(f"```\n{text}\n```")
        recorder.close()
    return 0


def run_validate(args) -> int:
    from pcs14.report.validation import write_validation
    from pcs14.sizing.validate import compare_case, discharge_check, load_cases

    catalog = load_catalog(args.catalog, allow_made_up=args.allow_made_up)
    cases = load_cases(args.cases, catalog)
    comparisons = [compare_case(case) for case in cases]
    cells = load_catalog(args.cells, allow_made_up=args.allow_made_up).cells.values()
    checks = [check for cell in cells for check in discharge_check(cell)]
    for c in comparisons:
        print(
            f"{c.case.name}: measured {c.measured_minutes:.1f} min, model "
            f"{c.predicted_minutes:.1f} / {c.predicted_pessimistic:.1f} min ({c.error * 100:+.0f}%)"
        )
    for check in checks:
        print(
            f"{check.cell.model} at {check.current:g} A: RMS {check.rms_error:.3f} V, "
            f"mean {check.mean_error:+.3f} V"
        )
    out = write_validation(
        args.out,
        comparisons,
        checks,
        made_up=args.allow_made_up,
        generated=date.today().isoformat(),
    )
    print(f"\nValidation written to {out / 'validation.md'}")
    return 0


def run_cad(args) -> int:
    from pcs14.cad.assembly import Drone
    from pcs14.cad.report import run_cad as run
    from pcs14.cad.report import summary, write_cad_report
    from pcs14.cad.settings import load_settings
    from pcs14.viz.cad_log import CadRecorder

    catalog, build, targets = _load(args)
    missing = [p.id for p in [build.motor, build.prop, build.esc, build.frame] if p.cad is None]
    if missing:
        raise ValueError(
            f"these parts have no cad block, so they can't be modeled: {', '.join(missing)}"
        )
    drone = Drone(build, load_settings(args.cad))
    recorder = _recorder(args, CadRecorder)
    result = run(drone, targets.combinations(), recorder=recorder)
    exports = None if args.skip_exports else args.exports
    result = write_cad_report(args.out, result, drone, date.today().isoformat(), exports)
    print(_made_up_line(args) + summary(result))
    print(f"\nReport written to {Path(args.out).resolve()}")
    if args.update_catalog:
        from pcs14.cad.catalog_update import update_catalog

        changed = update_catalog(result.printed, args.catalog, args.build)
        print(f"\nThe catalog took {len(changed)} printed weights:")
        for path in changed:
            print(f"  {path}")
    if recorder is not None:
        recorder.close()
    return 0


def run_electrical(args) -> int:
    from pcs14.cad.settings import load_settings
    from pcs14.electrical import tools
    from pcs14.electrical.model import load_connection_list
    from pcs14.electrical.validate import validate_design

    if args.tools:
        print("Outside tools:")
        for line in tools.describe():
            print(f"  {line}")
        return 0
    catalog, build, targets = _load(args)
    design = load_connection_list(args.electrical)
    combinations = targets.combinations()
    problems = validate_design(
        design, catalog, build, load_settings(args.cad), [s.modules for s in combinations]
    )
    print(
        _made_up_line(args) + f"The connection list: {len(design.boards)} boards, "
        f"{len(design.wires)} wires, {len(design.requires)} safety paths"
    )
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"It passes every rule in all {len(combinations)} module combinations.")
    return 0


COMMANDS = {
    "size": run_size,
    "sweep": run_sweep,
    "report": run_report,
    "validate": run_validate,
    "cad": run_cad,
    "electrical": run_electrical,
}
