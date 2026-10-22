"""The `pcs14` command.

    pcs14 size     evaluate one build: every setup, every check, every flight
    pcs14 sweep    try every build the catalog allows, and rank them
    pcs14 report   write the full sizing report: Markdown, charts and the data file
    pcs14 validate the honesty check: the model against published builds and cell curves
    pcs14 cad      build the drone in CAD, check every module combination, export it
    pcs14 electrical  every wire, pin and connector, checked in every combination
    pcs14 flight-sim  Gazebo models of every combination for PX4, and the flight sim report
    pcs14 tunnel   the wind tunnel's visuals: FluidX3D runs of the drone and their stills
    pcs14 modules  step 6's report: the modules in sim, from the flight sim's runs of them
    pcs14 smart    step 7: plan a mission from plain English (a local model), checked

Every run saves a Rerun recording to outputs/rerun/ (or wherever --record says), and --live
opens the viewer and streams into it as the run happens.
"""

import argparse
import sys
from dataclasses import replace
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
    electrical.add_argument(
        "--snap-routes",
        action="store_true",
        help="redraw each wire route in the CAD settings from the plugs its wires leave, then stop",
    )
    electrical.add_argument(
        "--update-cad",
        action="store_true",
        help="write each wire route's thickness, from the wires in it, into the CAD settings",
    )
    electrical.add_argument(
        "--out", type=Path, default=Path("docs/reports/electrical"), help="report folder"
    )
    electrical.add_argument(
        "--exports",
        type=Path,
        default=Path("outputs/electrical"),
        help="where the sims work and the build outputs too big to commit go",
    )
    electrical.add_argument(
        "--update-catalog",
        action="store_true",
        help="write the wiring's weight and the main path's resistance into the catalog and build",
    )
    electrical.add_argument(
        "--quick",
        action="store_true",
        help="just the checks and the report: no sims, diagrams, schematic or stills",
    )
    flight = add(
        "flight-sim",
        "The flight sim: a Gazebo model of every combination for PX4, and the report.",
    )
    flight.add_argument(
        "action",
        nargs="?",
        choices=("generate", "report", "run", "regrade"),
        default="generate",
        help="generate the models and the report (the default); report: just the report, "
        "stills and replays, leaving the model files alone (safe while flying); run: fly the "
        "scenarios (inside WSL2, where PX4 and Gazebo are); regrade: grade the flown runs "
        "again from their logs",
    )
    flight.add_argument(
        "--setup",
        action="append",
        help="with run: a combination to fly (repeat for more; default: all eight)",
    )
    flight.add_argument(
        "--scenario",
        action="append",
        help="with run: a scenario to fly (repeat for more; default: all of them)",
    )
    flight.add_argument("--jobs", type=int, default=1, help="with run: flights at once")
    flight.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="with run: a PX4 parameter over the generated ones, for an experiment",
    )
    flight.add_argument(
        "--tag",
        help="with run: a name for an experiment's runs, kept apart from the real ones and "
        "out of the report",
    )
    flight.add_argument(
        "--speed", type=float, default=1.0, help="with run: the sim's speed, against real time"
    )
    flight.add_argument(
        "--instance",
        type=int,
        default=0,
        help="with run: the first PX4 instance (each moves the ports), to fly beside another batch",
    )
    flight.add_argument(
        "--firmware",
        choices=("px4", "mine"),
        default="px4",
        help="with run: what flies, PX4 or my own (firmware/, built by scripts/build-firmware.sh); "
        "my firmware's runs are kept apart, tagged mine",
    )
    flight.add_argument("--cad", type=Path, default=Path("design/cad.yaml"))
    flight.add_argument(
        "--out", type=Path, default=Path("docs/reports/flight-sim"), help="report folder"
    )
    flight.add_argument(
        "--exports",
        type=Path,
        default=Path("outputs/flight-sim"),
        help="where the generated models, worlds and flight logs go",
    )
    flight.add_argument(
        "--no-meshes", action="store_true", help="skip the CAD meshes (the models still fly)"
    )
    flight.add_argument(
        "--replays",
        action="store_true",
        help="also write a Rerun recording of every flown run to outputs/flight-sim/rerun/",
    )
    tunnel = add(
        "tunnel",
        "The wind tunnel's visuals: FluidX3D runs of the drone (on the PC's GPU) and their stills.",
    )
    tunnel.add_argument("--cad", type=Path, default=Path("design/cad.yaml"))
    tunnel.add_argument("--setup", default="max", help="the module combination (default: max)")
    tunnel.add_argument(
        "--case",
        action="append",
        choices=("cruise", "back", "crosswind", "left", "above", "below", "hover"),
        help="a case to run (repeat for more; default: all seven)",
    )
    tunnel.add_argument(
        "--out", type=Path, default=Path("outputs/tunnel"), help="frames, meshes and stills"
    )
    tunnel.add_argument(
        "--stills-only", action="store_true", help="don't run FluidX3D, just redraw the stills"
    )
    ground = add(
        "ground",
        "The ground station: live telemetry, live tuning and the limits profile, on a web page.",
    )
    ground.add_argument(
        "--connect",
        default="udpin://0.0.0.0:14550",
        help="where the drone's ground station MAVLink comes in (default: PX4's port, 14550)",
    )
    ground.add_argument("--host", default="127.0.0.1", help="the page's address")
    ground.add_argument("--port", type=int, default=8714, help="the page's port")
    ground.add_argument("--grpc-port", type=int, default=50060, help="MAVSDK's own server")
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
    site = commands.add_parser(
        "site",
        help="The project site's data: every report into the files the site reads.",
        description="The project site's data: every report into the files the site reads.",
    )
    site.add_argument("--reports", type=Path, default=Path("docs/reports"))
    site.add_argument("--out", type=Path, default=Path("site/public/data"))
    site.add_argument(
        "--flights",
        type=Path,
        nargs="?",
        const=Path("outputs/flight-sim"),
        help="also every flight's playback file, from the flight sim's logs (default folder: "
        "outputs/flight-sim; the logs are only on the machine that flew them)",
    )
    site.add_argument(
        "--tunnel",
        type=Path,
        nargs="?",
        const=Path("outputs/tunnel"),
        help="also the wind tunnel's stills and frames (default folder: outputs/tunnel; they "
        "stay on this machine until the FluidX3D fork is public)",
    )
    site.add_argument(
        "--schema",
        type=Path,
        nargs="?",
        const=Path("site/schema"),
        help="also export the data's shapes as JSON Schema (default folder: site/schema)",
    )
    structure = commands.add_parser(
        "structure",
        help="The structure side track's first pass: the arms and the chute's mount, as beams.",
        description="The structure side track's first pass: the arms under full thrust and "
        "their bending modes against the props' speeds, and the chute mount's joints against "
        "step 6's jolt bound, as textbook beams. Written to docs/reports/structure/.",
    )
    for name, default in (("--catalog", "design/catalog"), ("--build", "design/build.yaml"),
                          ("--targets", "design/targets.yaml"), ("--docs", "docs"),
                          ("--exports", "outputs/flight-sim"),
                          ("--out", "docs/reports/structure")):  # fmt: skip
        structure.add_argument(name, type=Path, default=Path(default))
    structure.add_argument("--allow-made-up", action="store_true", help=argparse.SUPPRESS)
    package = commands.add_parser(
        "package",
        help="Step 8: the build package, docs/build/, from the catalog, the build and the reports.",
        description="Step 8: the build package. The parts list with prices and fallbacks, the "
        "assembly and wiring guides, the firmware, the test plans and the legal checklist, "
        "written to docs/build/ from the catalog, the build, the connection list and the "
        "reports' data files.",
    )
    for name, default in (("--catalog", "design/catalog"), ("--build", "design/build.yaml"),
                          ("--targets", "design/targets.yaml"), ("--cad", "design/cad.yaml"),
                          ("--electrical", "design/electrical.yaml"),
                          ("--extras", "design/package.yaml"), ("--docs", "docs"),
                          ("--exports", "outputs/flight-sim"),
                          ("--out", "docs/build")):  # fmt: skip
        package.add_argument(name, type=Path, default=Path(default))
    package.add_argument("--no-renders", action="store_true", help="skip the assembly renders")
    package.add_argument("--allow-made-up", action="store_true", help=argparse.SUPPRESS)
    modules = commands.add_parser(
        "modules",
        help="Step 6's report: the modules in sim, from the flight sim's runs of them.",
        description="Step 6's report: the modules in sim, from the flight sim's runs of them "
        "(fly them with pcs14 flight-sim run --firmware mine --scenario ...).",
    )
    modules.add_argument("--exports", type=Path, default=Path("outputs/flight-sim"))
    modules.add_argument("--out", type=Path, default=Path("docs/reports/modules"))
    smart = commands.add_parser(
        "smart",
        help="Step 7: its report, or a mission from plain English through a local model.",
        description="Step 7. With no words: the report, docs/reports/smart/, from the flight "
        "sim's runs of step 7's scenarios. With words: a mission from plain English. A local "
        "model (Ollama) writes the plan, the deterministic checker checks it against the "
        "limits profile and the drone, and the plan is saved for approval. The model never "
        "commands the motors.",
    )
    smart.add_argument("words", nargs="?", help="what to do, in plain English")
    smart.add_argument("--exports", type=Path, default=Path("outputs/flight-sim"))
    smart.add_argument("--report", type=Path, default=Path("docs/reports/smart"))
    smart.add_argument("--setup", default="mission", help="the module combination")
    smart.add_argument("--profile", default="us-recreational", choices=("max", "us-recreational"))
    smart.add_argument("--model", default="qwen2.5:7b-instruct", help="Ollama's model")
    smart.add_argument("--out", type=Path, default=Path("outputs/smart/plan.json"))
    for name, default in (("--catalog", "design/catalog"), ("--build", "design/build.yaml"),
                          ("--targets", "design/targets.yaml")):  # fmt: skip
        smart.add_argument(name, type=Path, default=Path(default))
    smart.add_argument("--allow-made-up", action="store_true", help=argparse.SUPPRESS)
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
        from pcs14.cad import hardware
        from pcs14.cad.catalog_update import update_catalog, update_hardware

        changed = update_catalog(result.printed, args.catalog, args.build)
        print(f"\nThe catalog took {len(changed)} printed weights:")
        for path in changed:
            print(f"  {path}")
        settings = drone.settings
        masses = hardware.by_module(settings, hardware.module_of_parts(build))
        counts = {}
        for item in settings.hardware:
            module = item.module or hardware.module_of_parts(build)[item.holds]
            counts[module] = counts.get(module, 0) + item.count
        changed = update_hardware(masses, args.catalog, args.build, counts)
        grams = ", ".join(f"{m} {kg * 1000:.1f} g" for m, kg in masses.items() if kg)
        print(f"The hardware ({grams}) went in too: {len(changed)} files changed.")
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
    if args.snap_routes:
        from pcs14.electrical.routes import update_cad_paths
        from pcs14.site.wires3d import snapped_routes

        changed = update_cad_paths(args.cad, snapped_routes(Path(args.cad).parent))
        print(f"{args.cad} took {len(changed)} routes redrawn from their plugs:")
        for name in changed:
            print(f"  {name}")
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
    if args.update_cad:
        from pcs14.electrical.routes import route_diameters, update_cad_routes

        parts = {part.id: part for part in catalog.all_parts()}
        changed = update_cad_routes(args.cad, route_diameters(design, parts))
        print(f"\n{args.cad} took {len(changed)} wire route thicknesses from the list.")
    from pcs14.electrical import pipeline, report
    from pcs14.viz.electrical_log import ElectricalRecorder, record

    settings = load_settings(args.cad)
    sims = None if args.quick else Path(args.exports) / "spice"
    analysis = pipeline.analyze(design, catalog, build, targets, settings, sims)
    run = pipeline.to_run(analysis)
    if not args.quick:
        run = pipeline.make_files(args.out, analysis, run, exports=args.exports)
    pipeline.write(args.out, run, date.today().isoformat())
    text = report.summary(run)
    print("\n" + text)
    print(f"\nReport written to {Path(args.out).resolve()}")
    if args.update_catalog:
        from pcs14.electrical import mass
        from pcs14.electrical.checks import design_context, main_path_ohms

        masses = mass.masses_for(design, catalog, build, settings)
        ohms = main_path_ohms(design_context(design, catalog, build, settings), analysis.solutions)
        changed = mass.update_catalog(masses, args.catalog, args.build, ohms)
        print("\nThe wiring, from the connection list:")
        for module, m in masses.items():
            print(f"  {module:5s}{m.meters:6.2f} m  {m.total * 1000:6.1f} g")
        print(f"  the main path: {ohms * 1000:.1f} mOhm out and back")
        print(f"The catalog and build took them ({len(changed)} files). Rerun pcs14 cad, report.")
    recorder = _recorder(args, ElectricalRecorder)
    if recorder is not None:
        from pcs14.cad.assembly import Drone

        pieces = Drone(build, settings).combination(pipeline.EVERYTHING).pieces
        record(
            recorder,
            pieces,
            settings.wires,
            design,
            analysis.setups,
            analysis.working,
            analysis.connectors,
            analysis.curves,
            analysis.sims,
            f"```\n{text}\n```",
        )
        recorder.close()
    return 0


def run_flight_sim(args) -> int:
    from pcs14.cad.assembly import Drone
    from pcs14.cad.settings import load_settings
    from pcs14.flight import report
    from pcs14.flight.batch import load_results
    from pcs14.flight.generate import flight_model, write_models

    _, build, targets = _load(args)
    if targets.flight_sim is None:
        raise ValueError("the targets have no flight_sim section, so nothing can be graded")
    if args.action == "run":
        return fly_flight_sim(args, build, targets)
    if args.action == "regrade":
        return regrade_flight_sim(args, build, targets)
    drone = Drone(build, load_settings(args.cad))
    setups = targets.combinations()
    exports = Path(args.exports)
    if args.action == "report":  # the models as they'd be, without touching their files
        models = [flight_model(drone, build, targets, s) for s in setups]
    else:
        models = write_models(exports, drone, build, targets, setups, meshes=not args.no_meshes)
    names = {s.name for s in setups}

    def graded_runs(firmware):
        found = load_results(exports, firmware=firmware)
        return tuple(r for r in found if r.scenario in report.SCENARIOS and r.setup in names)

    flown, mine = graded_runs("px4"), graded_runs("mine")
    skipped = []
    if not flown:
        skipped.append("flying the scenarios: PX4 and Gazebo run in WSL2 on the PC "
                       "(pcs14 flight-sim run)")  # fmt: skip
    files = sorted(p.relative_to(exports.parent).as_posix() for p in exports.rglob("*.sdf"))
    run = report.FlightSimRun(
        build_label=build.label,
        px4="v1.17.0",
        gazebo="Harmonic",
        combinations=tuple(setups),
        models=tuple(report.summary_of(m) for m in models),
        results=flown,
        estimates=report.estimates_for(models, build),
        files=tuple(files),
        skipped=tuple(skipped),
        mine=mine,
    )
    stills = []
    if flown:
        from pcs14.flight import stills as drawing

        chute = next((m.chute for m in models if m.chute is not None), None)
        timing = (chute.ejection_s, chute.opening_s) if chute is not None else None
        out_dir = Path(args.out)
        stills = [p.relative_to(out_dir).as_posix()
                  for p in drawing.draw_all(out_dir / "stills", run, exports, timing)]  # fmt: skip
    replays = []
    if flown and args.replays:
        replays = flight_replays(drone, models, flown, exports)
    run = replace(run, files=tuple(stills) + run.files + tuple(replays))
    out = report.write(args.out, run, date.today().isoformat())
    print(_made_up_line(args) + report.summary(run))
    if args.action != "report":
        print(f"\nModels written to {exports.resolve()}")
    print(f"Report written to {out.resolve()}")
    return 0


def flight_replays(drone, models, results, exports) -> list[str]:
    """A Rerun recording of every flown run, in outputs/flight-sim/rerun/."""
    from pcs14.cad.checks import trim
    from pcs14.flight.batch import flown_log
    from pcs14.viz.flight_log import drone_meshes, record_run

    by_setup = {m.setup: m for m in models}
    meshes = {}
    out = []
    for r in results:
        model = by_setup[r.setup]
        name = r.scenario.replace(" ", "-")
        found = flown_log(exports, r.setup, name)
        if found is None:
            continue
        if r.setup not in meshes:
            pieces = [p for p in trim(drone, model.modules).pieces if p.kind != "prop"]
            meshes[r.setup] = drone_meshes(pieces)
        log, _, result = found
        rows = [f"| {f.check} | {f.detail} | {'pass' if f.passed else 'fail'} |"
                for f in result.findings]  # fmt: skip
        summary = "\n".join(
            [f"## {r.scenario}, {r.setup}", "", "| Check | Found | Verdict |", "|---|---|---|"]
            + rows
        )
        path = exports / "rerun" / f"{model.name}-{name}.rrd"
        record_run(path, meshes[r.setup], f"{r.scenario}, {r.setup}", log,
                   model.motor.max_rot_velocity, summary)  # fmt: skip
        out.append(path.relative_to(exports.parent).as_posix())
    return out


def run_tunnel(args) -> int:
    import math

    from pcs14.aero import stills, tunnel
    from pcs14.cad.assembly import Drone
    from pcs14.cad.settings import load_settings

    _, build, targets = _load(args)
    setup = _pick([args.setup], {s.name: s for s in targets.combinations()}, "combination")[0]
    drone = Drone(build, load_settings(args.cad))
    out = Path(args.out)
    meshes = out / "meshes"
    found = tunnel.case_for(drone, build, targets, setup, meshes)
    wanted = set(args.case or ("cruise", "back", "crosswind", "left", "above", "below", "hover"))
    chosen = [c for c in found if c.name.rsplit("-", 1)[1] in wanted]
    home = tunnel.fluidx3d_dir()
    if not args.stills_only and not (home / "bin" / "FluidX3D.exe").exists():
        print(f"No FluidX3D build in {home} (set FLUIDX3D_DIR); --stills-only redraws stills.")
        return 2
    drawn = []
    for case in chosen:
        if not args.stills_only:
            print(f"{case.name}: running FluidX3D ({case.time_s:g} s of air)")
            tunnel.run(case, home, out, meshes)
        rpm = case.omega * 60 / (2 * math.pi) if case.omega else None
        drawn += stills.draw(case, out / case.name, out / "stills", rpm)
    print(f"{len(drawn)} stills in {(out / 'stills').resolve()}")
    print("They stay out of the repo until the FluidX3D fork is public.")
    return 0


def _pick(wanted, available: dict, what: str) -> list:
    if not wanted or wanted == ["all"]:
        return list(available.values())
    folded = {k.lower(): v for k, v in available.items()}
    missing = [w for w in wanted if w.lower() not in folded]
    if missing:
        raise ValueError(f"no {what} called {', '.join(missing)}: there's {', '.join(available)}")
    return [folded[w.lower()] for w in wanted]


def fly_flight_sim(args, build, targets) -> int:
    import asyncio

    from pcs14.flight import batch, report, run
    from pcs14.flight.scenarios import scenarios

    tools = run.toolchain()
    missing = tools.missing()
    if missing:
        print("Can't fly here: " + "; ".join(missing) + ".")
        print("The flights run inside WSL2 Ubuntu, set up by scripts/setup-ubuntu.sh.")
        return 2
    setups = _pick(args.setup, {s.name: s for s in targets.combinations()}, "combination")
    found = scenarios()
    if not args.scenario:  # every report scenario; the smoke flight only when it's named
        found = {name: sc for name, sc in found.items() if name in report.SCENARIOS}
    chosen = _pick(args.scenario, found, "scenario")
    pairs = [
        (s, sc) for s in setups for sc in chosen if sc.name == "smoke" or report.applies(sc.name, s)
    ]
    overrides = {}
    for item in args.param:
        name, _, value = item.partition("=")
        if not value:
            raise ValueError(f"--param wants NAME=VALUE, not {item!r}")
        overrides[name.strip()] = float(value) if "." in value or "e" in value else int(value)
    print(f"Flying {len(pairs)} runs, {args.jobs} at a time, at {args.speed:g}x real time")
    results = asyncio.run(
        batch.run_many(
            tools,
            Path(args.exports),
            pairs,
            targets,
            build,
            args.jobs,
            args.speed,
            overrides=overrides,
            tag=args.tag,
            firmware=args.firmware,
            first_instance=args.instance,
        )  # fmt: skip
    )
    passed = sum(r.passed for r in results)
    print(f"\n{passed} of {len(results)} runs passed")
    return 0 if passed == len(results) else 1


def regrade_flight_sim(args, build, targets) -> int:
    from pcs14.flight import batch
    from pcs14.flight.scenarios import scenarios

    setups = _pick(args.setup, {s.name: s for s in targets.combinations()}, "combination")
    chosen = _pick(args.scenario, scenarios(), "scenario")
    done = 0
    for setup in setups:
        for scenario in chosen:
            result = batch.regrade(Path(args.exports), setup, scenario, targets, build,
                                   firmware=args.firmware, tag=args.tag)  # fmt: skip
            if result is None:
                continue
            done += 1
            verdict = "pass" if result.passed else ("FAIL" if result.flown else "not flown")
            print(f"{scenario.name} in {setup.name}: {verdict}")
            for f in result.findings:
                print(f"    {'ok  ' if f.passed else 'FAIL'} {f.check}: {f.detail}")
    print(f"\nRegraded {done} runs")
    return 0


def run_ground(args) -> int:
    import asyncio

    from pcs14.ground.station import Station
    from pcs14.ground.web import serve

    async def main():
        station = Station(args.connect, args.grpc_port)
        print(f"Waiting for a drone on {args.connect}...")
        await station.start()
        server = serve(station, args.host, args.port)
        host, port = server.server_address[:2]
        print(f"Ground station at http://{host}:{port}/ (Ctrl-C to stop)")
        try:
            while True:
                await asyncio.sleep(5.0)
                await station.refresh_params()
        finally:
            server.shutdown()
            await station.stop()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    return 0


def run_smart(args) -> int:
    from pcs14.smart import missions

    if args.words is None:
        from datetime import date

        from pcs14.smart import report

        written = report.write(args.exports, args.report, date.today().isoformat())
        runs = report.collect_runs(args.exports)
        detection = report.load_detection(args.exports, run_model=False)
        print(f"Smart features in sim: {len(runs)} runs, verdict "
              f"{report.verdict(runs, detection)}")  # fmt: skip
        print(f"Report written to {Path(args.report).resolve()} ({len(written)} files)")
        return 0

    _, build, targets = _load(args)
    setup = _pick([args.setup], {s.name: s for s in targets.combinations()}, "combination")[0]
    plan = missions.plan_from_words(args.words, missions.ollama(args.model))
    checked = missions.check(plan, missions.drone_for(build, targets, setup),
                             missions.PROFILES[args.profile])  # fmt: skip
    path = missions.save(args.out, args.words, plan, checked, approved_by=None,
                         profile=args.profile)  # fmt: skip
    print(plan.model_dump_json(indent=1))
    if checked.ok:
        print(f"The checker passes it ({checked.energy_wh:.1f} Wh). It needs approving before "
              f"it flies: {path}")  # fmt: skip
    else:
        print("The checker refuses it:")
        for problem in checked.problems:
            print(f"  - {problem}")
    return 0 if checked.ok else 1


def run_structure(args) -> int:
    from datetime import date

    from pcs14.structure import report

    _, build, _ = _load(args)
    written = report.write(build, args.docs, args.exports, args.out, date.today().isoformat())
    data = report.collect(build, args.docs, args.exports)
    print(f"Structure, first pass: verdict {report.verdict(data)}")
    print(f"Report written to {Path(args.out).resolve()} ({len(written)} files)")
    return 0


def run_package(args) -> int:
    from datetime import date

    from pcs14.cad.settings import load_settings
    from pcs14.electrical.model import load_connection_list
    from pcs14.package import write

    catalog, build, targets = _load(args)
    written = write.write(args.out, date.today().isoformat(), catalog, build, targets,
                          load_connection_list(args.electrical), load_settings(args.cad),
                          args.docs, args.exports, args.extras,
                          renders=not args.no_renders)  # fmt: skip
    print(f"Build package written to {Path(args.out).resolve()} ({len(written)} files)")
    return 0


def run_modules(args) -> int:
    from datetime import date

    from pcs14.modules import report

    written = report.write(args.exports, args.out, date.today().isoformat())
    run = report.collect(args.exports)
    print(f"Modules in sim: {len(run.runs)} runs, verdict {report.verdict(run)}")
    print(f"Report written to {Path(args.out).resolve()} ({len(written)} files)")
    return 0


def run_site(args) -> int:
    import subprocess

    from pcs14.site import data

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                text=True, check=True).stdout.strip() or None  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        commit = None
    written = data.write_all(args.out, args.reports, commit)
    if args.schema is not None:
        written += data.write_schema(args.schema)
    if args.flights is not None:
        from pcs14.site import flights

        results, logs = flights.from_outputs(args.flights)
        written += flights.write_flights(args.out, results, logs)
    if args.tunnel is not None:
        from pcs14.site import tunnel

        written += tunnel.write_tunnel(args.out, args.tunnel)
    index = data.load(Path(args.out) / "index.json", data.schema.Index)
    missing = [name for name, r in index.reports.items() if not r.found]
    print(f"Wrote {len(written)} files to {Path(args.out).resolve()}")
    if missing:
        print("Not there yet: " + ", ".join(missing))
    return 0


COMMANDS = {
    "size": run_size,
    "sweep": run_sweep,
    "report": run_report,
    "validate": run_validate,
    "cad": run_cad,
    "electrical": run_electrical,
    "flight-sim": run_flight_sim,
    "tunnel": run_tunnel,
    "modules": run_modules,
    "package": run_package,
    "structure": run_structure,
    "smart": run_smart,
    "ground": run_ground,
    "site": run_site,
}
