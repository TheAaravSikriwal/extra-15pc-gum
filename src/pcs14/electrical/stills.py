"""The electrical report's stills, in the project's look and the post sizes.

- takeover: the hero. The safety monitor flipping an ESC line over mid-frame in ngspice: the
  flight controller's pin above, the ESC's below, the switch's control in magenta. In every
  post size.
- burst-heat: temperatures through the 10 s burst, against their limits.
- wire-work: how much of its heating limit each wire route uses, flat out, with the hottest
  connector.
"""

from pathlib import Path

import numpy as np

from pcs14.report import charts

SIZES = ("portrait", "square", "vertical", "wide")
HERO = "Takeover"
US = 1e6  # microseconds a second


def _c(name: str) -> str:
    return charts._c(name)


def _nice(name: str) -> str:
    """A pin or wire label as a reader would say it."""
    if name.startswith("pack.XT60"):
        return "the battery's XT60"
    if name.startswith("lead.XT60"):
        return "the battery leads"
    if ".MOTORS." in name:
        return "a motor lead"
    return name


def takeover(sim, path: Path, size: str = "portrait") -> Path:
    """The takeover run: `sim` is its switch.Run. The switch flipping is the one magenta mark;
    each frame on the line gets a plain label."""
    waves = sim.waves
    t = np.asarray(waves["time"]) * US
    window = (t >= 90) & (t <= 300)
    control = np.asarray(waves["v(ctl)"])
    flip = float(t[np.argmax(control > control.max() / 2)])
    canvas = charts.Canvas(
        "The safety monitor takes over",
        "ngspice: one DShot line as the Teensy flips the switch mid-frame",
        made_up=False,
        rows=2,
        size=size,
    )
    top, bottom = canvas.axes
    top.plot(t[window], np.asarray(waves["v(fc)"])[window], color=_c("muted"), linewidth=1.2)
    bottom.plot(t[window], np.asarray(waves["v(esc)"])[window], color=_c("accent"), linewidth=1.2)
    fonts = charts._fonts()
    labels = (
        (top, "the flight controller's pin", ((109.5, "throttle"), (201, "throttle, to nowhere"))),
        (
            bottom,
            "at the ESC",
            ((109.5, "cut short"), (151, "stop"), (205, "the ESC answers"), (251, "stop")),
        ),
    )
    for ax, title, marks in labels:
        ax.set_ylim(-0.4, 4.6)
        ax.set_yticks([0, 3.3])
        ax.set_xlim(90, 300)
        ax.axvline(flip, color=_c("pop"), linewidth=2.0, zorder=0)
        ax.text(0.0, 1.04, title, transform=ax.transAxes, fontsize=13, color=_c("text"),
                family=fonts["body"])  # fmt: skip
        for x, words in marks:
            ax.text(x, 3.75, words, fontsize=11, color=_c("muted"), family=fonts["body"],
                    ha="right" if x < flip else "left")  # fmt: skip
    top.text(flip + 1.5, 4.25, "the switch flips", fontsize=12, color=_c("text"),
             family=fonts["body"])  # fmt: skip
    top.tick_params(labelbottom=False)
    charts._label(bottom, "microseconds", "volts")
    lost = sum(f is None for f in sim.esc_frames)
    canvas.headline(
        f"{lost} frame" if lost == 1 else f"{lost} frames",
        "lost when the Teensy takes over in the middle of one. After that the ESC gets stop "
        "frames from the Teensy, and the flight controller's frames go nowhere.",
    )
    canvas.save(path)
    return path


def burst_heat(curves, path: Path, air_c: float) -> Path:
    """`curves` from thermal.burst_curves: (name, [(s, C)], limit)."""
    merged: dict[tuple, list[str]] = {}
    for name, curve, limit in curves:
        key = (round(curve[0][1], 1), round(curve[-1][1], 1), limit)
        merged.setdefault(key, []).append(name)
    shown = []
    for name, curve, limit in curves:
        key = (round(curve[0][1], 1), round(curve[-1][1], 1), limit)
        if merged[key][0] == name:
            shown.append((_nice(name), curve, limit))
    hottest = max(shown, key=lambda c: (c[1][-1][1] - air_c) / (c[2] - air_c))
    canvas = charts.Canvas(
        "Ten seconds flat out",
        "Temperatures through the burst at the 90 A cap, from the hottest hover",
        made_up=False,
    )
    ax = canvas.axes[0]
    fonts = charts._fonts()
    colors = iter([_c("accent"), _c("muted"), _c("text")])
    seconds = max(c[1][-1][0] for c in shown)
    limits = sorted({limit for _, _, limit in shown})
    for limit in limits:
        ax.axhline(limit, color=_c("lines"), linewidth=2, zorder=1)
        ax.text(
            seconds * 0.01,
            limit + 2,
            f"{limit:g} °C limit",
            fontsize=12,
            color=_c("muted"),
            family=fonts["body"],
        )
    for name, curve, limit in shown:
        over = curve[-1][1] > limit
        color = _c("pop") if over else next(colors, _c("muted"))
        xs, ys = zip(*curve, strict=True)
        ax.plot(xs, ys, color=color, linewidth=2.5 if over else 2.0, zorder=3)
        ax.text(
            xs[-1] - seconds * 0.01,
            ys[-1] + 3,
            name,
            fontsize=13,
            color=_c("text"),
            family=fonts["body"],
            ha="right",
        )
    ax.set_xlim(0, seconds)
    ax.set_ylim(air_c - 5, max(max(limits), max(c[1][-1][1] for c in shown)) + 15)
    charts._label(ax, "seconds into the burst", "°C")
    name, curve, limit = hottest
    over = curve[-1][1] > limit
    held = [i for i, (_, c) in enumerate(curve) if c >= limit - 0.01]
    if held and not over:
        # it flattens at its limit: the firmware's heat limit easing the current cap. The
        # samples are coarse, so carry the rise just before it on to the limit
        k = held[0]
        reach = curve[k][0]
        if k >= 2:
            (t0, c0), (t1, c1) = curve[k - 2], curve[k - 1]
            reach = t1 + (limit - c1) * (t1 - t0) / (c1 - c0)
        canvas.headline(
            f"{reach:.1f} s",
            f"of the full current before {name} reaches its {limit:g} °C limit, starting from "
            "the heaviest hover. Then my firmware eases the current cap to hold it there.",
        )
    else:
        canvas.headline(
            f"{curve[-1][1]:.0f} °C",
            f"{name[0].upper()}{name[1:]} after {seconds:g} s at the cap, against its "
            f"{limit:g} °C " + ("limit. It rests on a guessed contact mass." if over else "limit."),
            color="pop" if over else "accent",
        )
    canvas.save(path)
    return path


def wire_work(route_shares: dict, connectors: dict, path: Path, case: str = "burst") -> Path:
    """Each route's share of its heating limit in `case` (its hardest combination), as bars,
    with the hardest working connector."""
    routes: dict[str, float] = {}
    for (_, c), shares in route_shares.items():
        if c == case:
            for route, share in shares.items():
                routes[route] = max(routes.get(route, 0.0), share)
    connector, share = None, 0.0
    for (_, c), shares in connectors.items():
        if c == case:
            for ref, s in shares.items():
                if s > share:
                    connector, share = ref, s
    rows = sorted(((r, s) for r, s in routes.items() if s >= 0.005), key=lambda item: item[1])
    if connector is not None:
        rows.append((_nice(connector), share))
        rows.sort(key=lambda item: item[1])
    canvas = charts.Canvas(
        "How hard every wire works",
        "Flat out: each route's share of its heating limit, in its hardest combination",
        made_up=False,
    )
    ax = canvas.axes[0]
    fonts = charts._fonts()
    names = [r for r, _ in rows]
    values = [s * 100 for _, s in rows]
    colors = [_c("pop") if s > 1 else _c("accent") for _, s in rows]
    ax.barh(range(len(rows)), values, color=colors, height=0.62)
    ax.axvline(100, color=_c("muted"), linewidth=1.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(names, family=fonts["body"], fontsize=12, color=_c("text"))
    for i, v in enumerate(values):
        ax.text(v + 2, i, f"{v:.0f}%", va="center", fontsize=11, color=_c("text"),
                family=fonts["numbers"])  # fmt: skip
    ax.set_xlim(0, max(110, max(values) + 20))
    ax.grid(axis="y", visible=False)
    charts._label(ax, "% of the heating limit", "")
    hardest_route = max(routes.items(), key=lambda item: item[1]) if routes else ("", 0.0)
    text = (
        f"The hardest working route, {hardest_route[0]}, uses {hardest_route[1]:.0%} of its limit."
    )
    who = f"{_nice(connector)[0].upper()}{_nice(connector)[1:]}" if connector else ""
    if connector is not None and share > 1:
        text += f" {who} is the one thing past it."
    elif connector is not None and share >= 0.999:
        text += f" {who} runs right at its limit, where my firmware holds it."
    canvas.headline(f"{hardest_route[1]:.0%}", text)
    # the long route names need more room on the left than the other charts give
    left = 0.30
    box = ax.get_position()
    ax.set_position((left, box.y0, box.x1 - left, box.height))
    canvas.save(path)
    return path


def draw_all(folder: Path, analysis) -> list[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    sims = analysis.sims or {}
    if HERO in sims:
        for size in SIZES:
            paths.append(takeover(sims[HERO], folder / f"takeover-{size}.png", size))
    from pcs14.electrical.routes import route_shares

    paths.append(
        burst_heat(analysis.curves, folder / "burst-heat.png", analysis.design.checks.air_c)
    )
    paths.append(
        wire_work(
            route_shares(analysis.design, analysis.working),
            analysis.connectors,
            folder / "wire-work.png",
        )
    )
    return paths
