"""The honesty check's report: how far off the model is on published builds and cells."""

from pathlib import Path

from pcs14 import __version__
from pcs14.report import charts
from pcs14.report.markdown import SOURCE_WORDS
from pcs14.report.write import REAL_REPORTS

UNTIL_WORDS = {
    "charge_used_fraction": "until {:.0%} of the charge was used",
    "charge_used_mah": "until {:.0f} mAh was used",
    "loaded_voltage_per_cell_v": "down to {:.2f} V per cell under load",
    "resting_voltage_per_cell_v": "down to {:.2f} V per cell at rest",
}


def _source(source) -> str:
    words = SOURCE_WORDS[source.kind.value]
    return f"[{words}]({source.url})" if source.url else words


def _what(case) -> str:
    ((kind, value),) = case.measured.until.items()
    flown = (
        "hovering"
        if case.measured.kind == "hover"
        else f"cruising at {case.measured.speed_ms:g} m/s"
    )
    return f"{flown}, {UNTIL_WORDS[kind].format(value)}"


def render(comparisons, discharge_checks, made_up=False, generated=None) -> str:
    lines = ["# How far off is the model?", ""]
    if made_up:
        lines += [
            "> **Made from made-up test parts.** These cases are invented, so this only shows "
            "what the honesty check looks like.",
            "",
        ]
    when = f" on {generated}" if generated else ""
    lines += [
        f"*Generated{when} by pcs14 {__version__}. Each published build gets flown by the model "
        "with its own parts, weight and stopping point, and the model's flight time goes next "
        "to the measured one. The model gives a range: the published thrust data at the top, "
        "the pessimistic version at the bottom.*",
        "",
        "![How far off is the model?](charts/validation.png)",
        "",
        "## Published builds",
        "",
        "| Build | What was measured | Measured | Model (published / pessimistic) | Off by | "
        "Inside the range? | Measured by |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in comparisons:
        if c.flight is None:
            lines.append(
                f"| {c.case.name} | {_what(c.case)} | {c.measured_minutes:.1f} min | "
                f"can't hover: {c.note} | | | {c.case.measured.label} |"
            )
            continue
        lines.append(
            f"| {c.case.name} | {_what(c.case)} | {c.measured_minutes:.1f} min | "
            f"{c.predicted_minutes:.1f} / {c.predicted_pessimistic:.1f} min | "
            f"{c.error * 100:+.0f}% | "
            f"{'yes' if c.inside_the_band else 'no'} | {c.case.measured.label}, "
            f"{_source(c.case.source)} |"
        )
    if comparisons:
        usable = [c for c in comparisons if c.flight is not None]
        if usable:
            mean = sum(c.error for c in usable) / len(usable)
            inside = sum(c.inside_the_band for c in usable)
            lines += [
                "",
                f"On average the model's published-data prediction is {abs(mean) * 100:.0f}% "
                f"{'long' if mean > 0 else 'short'}, and {inside} of {len(usable)} measurements "
                "land inside its range.",
            ]
        lines += ["", "What had to be estimated, build by build:", ""]
        lines += [f"- {c.case.name}: {c.case.estimate_note}" for c in comparisons]
    lines += [
        "",
        "## The battery model against real discharge curves",
        "",
        "The model's voltage under a steady current is the cell's resting curve minus current "
        "times internal resistance. Here it is against measured discharges. A negative mean "
        "means the real cell sags more than the model says.",
        "",
        "| Cell | Current | RMS error | Mean error | Measured by |",
        "|---|---|---|---|---|",
    ]
    for check in discharge_checks:
        lines.append(
            f"| {check.cell.maker} {check.cell.model} | {check.current:g} A | "
            f"{check.rms_error:.3f} V | {check.mean_error:+.3f} V | {_source(check.source)} |"
        )
    if not discharge_checks:
        lines.append("| none yet | | | | |")
    lines.append("")
    return "\n".join(lines)


def chart(comparisons, path: Path, made_up: bool) -> None:
    canvas = charts.Canvas(
        "How far off is the model?", "Measured flight time against the model's range", made_up
    )
    ax = canvas.axes[0]
    usable = [c for c in comparisons if c.flight is not None]
    for i, c in enumerate(usable):
        ax.barh(
            i,
            c.predicted_minutes - c.predicted_pessimistic,
            left=c.predicted_pessimistic,
            height=0.5,
            color=charts._c("accent"),
            alpha=0.35,
        )
        ax.plot([c.measured_minutes] * 2, [i - 0.3, i + 0.3], color=charts._c("text"), linewidth=3)
    ax.set_yticks(range(len(usable)))
    ax.set_yticklabels([c.case.name for c in usable], color=charts._c("text"), fontsize=12)
    charts._label(ax, "minutes (band: the model's range, white: measured)", "")
    if usable:
        mean = sum(c.error for c in usable) / len(usable)
        canvas.headline(
            f"{mean * 100:+.0f}%",
            "How far the model's published-data prediction "
            "lands from the measured flight time, on average.",
        )
    canvas.save(path)


def write_validation(out: Path, comparisons, discharge_checks, made_up=False, generated=None):
    out = Path(out).resolve()
    if made_up and (out == REAL_REPORTS or REAL_REPORTS in out.parents):
        raise ValueError(
            "a made-up validation can't go in docs/reports/, which is only for real "
            "parts. Write it somewhere like outputs/ instead."
        )
    out.mkdir(parents=True, exist_ok=True)
    text = render(comparisons, discharge_checks, made_up=made_up, generated=generated)
    (out / "validation.md").write_bytes(text.encode("utf-8"))
    (out / "charts").mkdir(exist_ok=True)
    chart(comparisons, out / "charts" / "validation.png", made_up)
    return out
