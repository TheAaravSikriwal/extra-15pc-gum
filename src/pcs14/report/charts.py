"""The report's charts, in the project's wind-tunnel look and at the 4:5 post size.

Every chart follows the layout in docs/style.md: the project name small at the top, the
visual in the middle, one big number in spearmint with a caption under it, and the credit
line at the bottom. A chart made from made-up test parts says so in magenta.
"""

import logging
import math
from functools import cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from pcs14 import style, units  # noqa: E402
from pcs14.sizing.battery import Pack  # noqa: E402
from pcs14.sizing.checks import DesignResult, SetupResult  # noqa: E402
from pcs14.sizing.flight import power_model, thrust_to_weight  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

DPI = 100


@cache
def _fonts() -> dict[str, str]:
    available = {font.name for font in font_manager.fontManager.ttflist}
    wanted = style.load()["fonts"]
    fallback = {"headline": "DejaVu Sans", "body": "DejaVu Sans", "numbers": "DejaVu Sans Mono"}
    return {kind: name if name in available else fallback[kind] for kind, name in wanted.items()}


def _c(name: str) -> str:
    return style.color(name)


class Canvas:
    """One post-sized figure with the project's header, footer and plot area."""

    def __init__(self, title: str, subtitle: str, made_up: bool, rows: int = 1):
        width, height = style.load()["sizes"]["portrait"]
        self.width, self.height = width, height
        self.fig = plt.figure(
            figsize=(width / DPI, height / DPI), dpi=DPI, facecolor=_c("background")
        )
        margin = style.load()["layout"]["margin_px"]
        x = margin / width
        fonts = _fonts()
        self._text(x, 1 - 70 / height, "EXTRA 15PC GUM", 14, "text", fonts["body"], weight="bold")
        if made_up:
            self._text(
                1 - x,
                1 - 70 / height,
                "MADE-UP TEST PARTS",
                14,
                "pop",
                fonts["body"],
                weight="bold",
                ha="right",
            )
        self._text(x, 1 - 140 / height, title, 36, "text", fonts["headline"], weight="medium")
        self._text(x, 1 - 188 / height, subtitle, 17, "muted", fonts["body"])
        self._text(x, 52 / height, style.load()["layout"]["credit"], 12, "muted", fonts["body"])
        top, bottom = 1 - 250 / height, 330 / height
        gap = 60 / height
        span = (top - bottom - gap * (rows - 1)) / rows
        self.axes = []
        for row in range(rows):
            low = top - (row + 1) * span - row * gap
            ax = self.fig.add_axes((130 / width, low, 1 - 130 / width - x, span))
            _style_axes(ax)
            self.axes.append(ax)

    def _text(self, x, y, text, size, color, family, **kw):
        self.fig.text(x, y, text, fontsize=size, color=_c(color), family=family, va="center", **kw)

    def headline(self, number: str, caption: str, color: str = "accent") -> None:
        x = style.load()["layout"]["margin_px"] / self.width
        fonts = _fonts()
        self._text(x, 215 / self.height, number, 44, color, fonts["numbers"], weight="bold")
        self.fig.text(
            x,
            150 / self.height,
            caption,
            fontsize=15,
            color=_c("muted"),
            family=fonts["body"],
            va="top",
            wrap=True,
        )

    def save(self, path: Path) -> None:
        self.fig.savefig(path, dpi=DPI, facecolor=_c("background"))
        plt.close(self.fig)


def _style_axes(ax) -> None:
    fonts = _fonts()
    ax.set_facecolor(_c("background"))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_c("lines"))
    ax.tick_params(colors=_c("muted"), labelsize=12)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_family(fonts["numbers"])
    ax.grid(True, color=_c("lines"), linewidth=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(_c("muted"))
    ax.yaxis.label.set_color(_c("muted"))


def _label(ax, x: str, y: str) -> None:
    fonts = _fonts()
    ax.set_xlabel(x, fontsize=13, family=fonts["body"])
    ax.set_ylabel(y, fontsize=13, family=fonts["body"])


def _verdict(name: str) -> str:
    return style.verdict_color(name)


def flight_times(design: DesignResult, path: Path, made_up: bool) -> None:
    canvas = Canvas(
        "Flight time, every setup",
        "Landing with 20% left. Faded: only on the published numbers.",
        made_up,
    )
    ax = canvas.axes[0]
    results = list(reversed(design.setups))
    cruise_name = f"Cruise time at {design.targets.cruise_speed:g} m/s"
    for i, result in enumerate(results):
        for offset, name, height in ((0.18, cruise_name, 0.34), (-0.2, "Hover time", 0.2)):
            if not any(c.name == name for c in result.checks):
                continue
            check = result.check(name)
            color = _verdict(check.verdict)
            ax.barh(i + offset, check.pessimistic, height=height, color=color)
            ax.barh(
                i + offset,
                max(0.0, check.nominal - check.pessimistic),
                height=height,
                left=check.pessimistic,
                color=color,
                alpha=0.35,
            )
            ax.plot(
                [check.limit] * 2,
                [i + offset - height / 2, i + offset + height / 2],
                color=_c("text"),
                linewidth=2,
            )
    ax.set_yticks(range(len(results)))
    names = [f"{r.setup.name}{'' if r.setup.required else ' *'}" for r in results]
    ax.set_yticklabels(names, family=_fonts()["body"], fontsize=13, color=_c("text"))
    _label(ax, "minutes (thick: cruise, thin: hover, white tick: target)", "")
    sizing = design.sizing.check(cruise_name)
    canvas.headline(
        f"{math.floor(sizing.nominal * 10) / 10:.1f} min",
        f"{design.targets.sizing_case.capitalize()} cruising at "
        f"{design.targets.cruise_speed:g} m/s on the published numbers, "
        f"{math.floor(sizing.pessimistic * 10) / 10:.1f} pessimistic. * = optional setup.",
    )
    canvas.save(path)


def battery(design: DesignResult, path: Path, made_up: bool) -> None:
    result = design.sizing
    canvas = Canvas(
        "One flight, start to reserve",
        f"{result.setup.name.capitalize()}, cruising at {design.targets.cruise_speed:g} m/s",
        made_up,
        rows=2,
    )
    volts_ax, tw_ax = canvas.axes
    pack = Pack(design.build.pack)
    for case, color, width in (("nominal", "accent", 3), ("pessimistic", "muted", 2)):
        flight = result.flights.get(f"cruise/{case}")
        if flight is None:
            continue
        minutes = [units.seconds_to_minutes(s.time) for s in flight.samples]
        volts_ax.plot(
            minutes,
            [s.voltage for s in flight.samples],
            color=_c(color),
            linewidth=width,
            label="published data" if case == "nominal" else "pessimistic data",
        )
        model = power_model(
            design.build, result.setup, result.growth_margin, pessimistic=case == "pessimistic"
        )
        tw = [thrust_to_weight(model, pack, s.soc) for s in flight.samples]
        tw_ax.plot(minutes, tw, color=_c(color), linewidth=width)
    tw_ax.axhline(
        design.targets.min_thrust_to_weight, color=_c("text"), linestyle="--", linewidth=1.5
    )
    legend = volts_ax.legend(frameon=False, fontsize=12, loc="upper right")
    for text in legend.get_texts():
        text.set_color(_c("muted"))
    _label(volts_ax, "", "pack voltage under load (V)")
    _label(tw_ax, "minutes", "full-throttle thrust-to-weight")
    check = result.check("Thrust-to-weight at the reserve")
    canvas.headline(
        f"{math.floor(check.nominal * 100) / 100:.2f}:1",
        "Thrust-to-weight left at the 20% reserve, with the pack sagging under full throttle "
        f"({math.floor(check.pessimistic * 100) / 100:.2f}:1 pessimistic, "
        f"{design.targets.min_thrust_to_weight:g}:1 needed).",
    )
    canvas.save(path)


def power(design: DesignResult, path: Path, made_up: bool) -> None:
    result: SetupResult = design.sizing
    canvas = Canvas(
        "Power against airspeed",
        f"{result.setup.name.capitalize()}, all four motors plus the electronics",
        made_up,
    )
    ax = canvas.axes[0]
    speeds = [i * 0.25 for i in range(0, 121)]
    for case, color, width in (("nominal", "accent", 3), ("pessimistic", "muted", 2)):
        model = power_model(
            design.build, result.setup, result.growth_margin, pessimistic=case == "pessimistic"
        )
        ax.plot(speeds, [model.power(v) for v in speeds], color=_c(color), linewidth=width)
    nominal = power_model(design.build, result.setup, result.growth_margin)
    best, watts = nominal.least_power_speed()
    ax.plot([best], [watts], "o", color=_c("pop"), markersize=12)
    ax.axvline(design.targets.cruise_speed, color=_c("text"), linestyle="--", linewidth=1.2)
    _label(ax, "airspeed (m/s)", "electrical power (W)")
    canvas.headline(
        f"{best:.1f} m/s",
        f"The cheapest speed: {watts:.0f} W, against {nominal.power(0):.0f} W to hover. "
        f"Dashed: the {design.targets.cruise_speed:g} m/s the cruise target is checked at.",
    )
    canvas.save(path)


def margin(design: DesignResult, curve: dict, path: Path, made_up: bool) -> None:
    canvas = Canvas("What extra weight costs", "Cruise time as grams go on, every setup", made_up)
    ax = canvas.axes[0]
    sizing = design.targets.sizing_case
    for name, points in curve.items():
        if not points:
            continue
        highlight = name == sizing
        ax.plot(
            [p.grams for p in points],
            [p.cruise_minutes for p in points],
            color=_c("accent" if highlight else "muted"),
            linewidth=3 if highlight else 1.2,
            alpha=1 if highlight else 0.7,
        )
        ax.text(
            points[-1].grams + 8,
            points[-1].cruise_minutes,
            name,
            fontsize=11,
            color=_c("accent" if highlight else "muted"),
            va="center",
            family=_fonts()["body"],
        )
    _label(ax, "extra grams on top of each setup", "cruise minutes")
    points = curve.get(sizing, [])
    today = units.kg_to_g(design.targets.growth_margin)
    marked = [p for p in points if abs(p.grams - today) < 1e-6]
    if marked:
        ax.plot([today], [marked[0].cruise_minutes], "o", color=_c("pop"), markersize=12)
        ax.annotate(
            f"today's {today:.0f} g growth margin",
            (today, marked[0].cruise_minutes),
            xytext=(12, 18),
            textcoords="offset points",
            color=_c("pop"),
            fontsize=12,
            family=_fonts()["body"],
        )
    per_100 = 0.0
    if len(points) > 1:
        per_100 = (points[0].cruise_minutes - points[-1].cruise_minutes) / (
            (points[-1].grams - points[0].grams) / 100
        )
    canvas.headline(
        f"{per_100:.1f} min",
        f"What each extra 100 g costs {sizing} in cruise time, on average across the chart.",
    )
    canvas.save(path)


def sweep_chart(design: DesignResult, sweep, path: Path, made_up: bool) -> None:
    canvas = Canvas(
        "Every build the sweep tried",
        f"{design.targets.sizing_case.capitalize()}'s weight against its cruise time",
        made_up,
    )
    ax = canvas.axes[0]
    for verdict in ("fail", "marginal", "pass"):
        group = [c for c in sweep.ranked if c.verdict == verdict]
        ax.scatter(
            [units.kg_to_g(c.result.sizing.mass.total) for c in group],
            [c.sizing_cruise_minutes for c in group],
            s=120,
            color=_verdict(verdict),
            label=verdict,
            edgecolors="none",
        )
    best = sweep.best
    ax.scatter(
        [units.kg_to_g(best.result.sizing.mass.total)],
        [best.sizing_cruise_minutes],
        s=520,
        facecolors="none",
        edgecolors=_c("text"),
        linewidths=2,
    )
    legend = ax.legend(frameon=False, fontsize=12, loc="lower right")
    for text in legend.get_texts():
        text.set_color(_c("muted"))
    _label(ax, "takeoff weight (g)", "cruise minutes")
    skipped = len(sweep.skipped)
    tail = (
        "Nothing was skipped."
        if not skipped
        else f"{skipped} more were skipped because their parts don't fit together."
    )
    canvas.headline(
        f"{len(sweep.ranked)} builds", f"Ringed: the winner, {best.build.label}. {tail}"
    )
    canvas.save(path)


def draw_all(design: DesignResult, sweep, curve, out: Path, made_up: bool) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    jobs = [
        ("flight-times", lambda p: flight_times(design, p, made_up)),
        ("battery", lambda p: battery(design, p, made_up)),
        ("power", lambda p: power(design, p, made_up)),
    ]
    if curve is not None:
        jobs.append(("margin", lambda p: margin(design, curve, p, made_up)))
    if sweep is not None:
        jobs.append(("sweep", lambda p: sweep_chart(design, sweep, p, made_up)))
    for name, draw in jobs:
        path = out / f"{name}.png"
        draw(path)
        paths.append(path)
    return paths
