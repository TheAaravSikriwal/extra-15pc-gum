"""The flight sim's stills, in the project's look and the post sizes.

- drop: the hero. A parachute drop: the height from the moment PX4 terminates, through the
  free fall, the canopy leaving and filling, to the steady descent. In every post size.
- steps: a 15 degree stick step on PX4's x500 attitude gains against the tuned ones, when
  the experiment's log is there (pcs14 flight-sim run --scenario steps --tag x500-gains
  --param MC_ROLL_P=6.5 --param MC_PITCH_P=6.5)
- matrix: every scenario in every combination, pass or fail
"""

import math
from pathlib import Path

import numpy as np

from pcs14.flight import grade, ulog
from pcs14.report import charts

SIZES = ("portrait", "square", "vertical", "wide")
DROP_BEFORE_S = 2.0  # of the hover before the termination, on the drop's chart
STEP_BEFORE_S = 0.3
STEP_AFTER_S = 1.5


SETTLE_TARGET_S = 0.5  # s, the steps scenario's target


def _c(name: str) -> str:
    return charts._c(name)


def drop(log, path: Path, setup: str, ejection_s: float, opening_s: float,
         size: str = "portrait") -> Path:  # fmt: skip
    """`log` is a parachute drop's FlightLog, with "terminate" and "chute fired" among its
    events."""
    start = log.when("terminate") or log.when("motors stopped")
    fired = log.when("chute fired")
    order, lost = grade.chute(log, ejection_s)
    t = log.t - start
    shown = (t >= -DROP_BEFORE_S) & (log.position[:, 2] > -1)
    ground = np.flatnonzero((t > 0) & (log.position[:, 2] <= grade.CONTACT_M))
    end = float(t[ground[0]]) + 1.0 if len(ground) else float(t[-1])
    shown &= t <= end
    canvas = charts.Canvas(
        "The parachute",
        f"PX4 cuts the flight 40 m up, in {setup}, and the chute does the rest",
        made_up=False,
        size=size,
    )
    (ax,) = canvas.axes
    ax.plot(t[shown], log.position[shown, 2], color=_c("accent"), linewidth=2.2)
    fonts = charts._fonts()
    top = float(log.position[shown, 2].max())
    stopped = log.when("motors stopped")
    marks = [(stopped - start if stopped is not None else 0.0, "PX4 stops the motors", "muted")]
    if fired is not None:
        leaves = fired - start + ejection_s
        marks += [(leaves, "the canopy leaves", "muted"),
                  (leaves + opening_s, "it's open", "pop")]  # fmt: skip
    # the labels sit in the empty top right, each pointing at its moment on the curve
    for k, (x, words, color) in enumerate(marks):
        ax.axvline(x, color=_c(color), linewidth=1.6 if color == "pop" else 1.0, zorder=0)
        y = float(np.interp(x, t[shown], log.position[shown, 2]))
        ax.annotate(words, xy=(x, y), xytext=(0.42, 0.94 - 0.09 * k), textcoords="axes fraction",
                    fontsize=13, color=_c("text"), family=fonts["body"], va="center",
                    arrowprops={"arrowstyle": "-", "color": _c("muted"), "linewidth": 0.8,
                                "shrinkA": 4, "shrinkB": 2})  # fmt: skip
    ax.set_xlim(-DROP_BEFORE_S, end)
    ax.set_ylim(0, top * 1.08)
    charts._label(ax, "seconds from the termination", "height (m)")
    detail = lost.detail if lost.value is not None else ""
    rate = detail.split("settling at ")[-1] if "settling at" in detail else "its steady rate"
    gap = ""
    if fired is not None and stopped is not None:
        gap = f" The motors stopped {fired + ejection_s - stopped:.2f} s before the canopy left."
    canvas.headline(
        f"{lost.value:.1f} m" if lost.value is not None else "no chute",
        f"lost before the canopy holds it, then down at {rate}.{gap}",
    )
    canvas.save(path)
    return path


def _step_response(log, marks):
    """Roll through the first stick step: (s from the step, degrees)."""
    start = next(t for t, name in marks if name == "step 0 start")
    inside = (log.t >= start - STEP_BEFORE_S) & (log.t <= start + STEP_AFTER_S)
    roll = np.degrees(ulog.px4_euler(log.attitude[inside])[:, 0])
    return log.t[inside] - start, roll


def steps(tuned, stock, path: Path, size: str = "portrait") -> Path:
    """`tuned` and `stock` are (FlightLog, marks, settle_s) for the steps scenario with the
    tuned and the x500's attitude gains."""
    canvas = charts.Canvas(
        "Tuning PX4 for this airframe",
        "A 15 degree roll stick, flown in PX4's altitude mode",
        made_up=False,
        size=size,
    )
    (ax,) = canvas.axes
    fonts = charts._fonts()
    overshoot = 0.0
    for (log, marks, settle), color, words in (
        (stock, "muted", "the x500's gain, 6.5"),
        (tuned, "accent", "tuned, 9"),
    ):
        t, roll = _step_response(log, marks)
        ax.plot(t, roll, color=_c(color), linewidth=2.2)
        k = np.searchsorted(t, 0.62)
        # inside the plot, above the tuned line and below the stock one
        ax.text(0.62, roll[min(k, len(roll) - 1)] + (0.9 if color == "accent" else -1.6),
                f"{words}: settles in {settle:.2f} s", fontsize=12, color=_c("text"),
                family=fonts["body"])  # fmt: skip
        if color == "accent":
            final = float(np.mean(roll[t > t[-1] - 0.3]))
            overshoot = max(0.0, float(np.max(roll)) / final - 1) if final else 0.0
    ax.axvline(SETTLE_TARGET_S, color=_c("pop"), linewidth=1.4, zorder=0)
    ax.text(0.52, 1.0, "the 0.5 s target", fontsize=12, color=_c("text"), family=fonts["body"])
    ax.set_xlim(-STEP_BEFORE_S, STEP_AFTER_S)
    charts._label(ax, "seconds from the stick moving", "roll (degrees)")
    # the words follow the numbers: in the first runs the stock gains missed the target, and in
    # the final batch they don't
    if stock[2] > SETTLE_TARGET_S:
        why = (f"PX4's stock x500 gains were too gentle for this drone; raising the attitude "
               f"gain from 6.5 to 9 fixed it with {overshoot:.0%} overshoot.")  # fmt: skip
    else:
        why = (f"Both make the {SETTLE_TARGET_S:g} s target; raising the attitude gain from "
               f"the x500's 6.5 to 9 settles {stock[2] / tuned[2]:.1f} times faster, with "
               f"{overshoot:.0%} overshoot.")  # fmt: skip
    canvas.headline(
        f"{stock[2]:.2f} s to {tuned[2]:.2f} s", "to settle within 5% of the step. " + why
    )
    canvas.save(path)
    return path


def matrix(run, path: Path, size: str = "wide") -> Path:
    """Every scenario in every combination: `run` is a pcs14.flight.report.FlightSimRun."""
    from pcs14.flight.report import SCENARIOS, applies

    canvas = charts.Canvas(
        "Every scenario, every combination",
        f"PX4 {run.px4} in Gazebo {run.gazebo}, flying a model of each module combination",
        made_up=False,
        size=size,
    )
    (ax,) = canvas.axes
    # room on the left for the scenarios' names ("parachute drop" ran off the edge)
    box = ax.get_position()
    ax.set_position((box.x0 + 0.06, box.y0, box.width - 0.06, box.height))
    fonts = charts._fonts()
    combos = run.combinations
    ax.set_xlim(-0.5, len(combos) - 0.5)
    ax.set_ylim(len(SCENARIOS) - 0.5, -0.5)
    ax.grid(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_xticks(range(len(combos)), [s.name for s in combos])
    ax.set_yticks(range(len(SCENARIOS)), SCENARIOS)
    ax.tick_params(length=0, labelsize=13, colors=_c("text"))
    ax.xaxis.tick_top()
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_family(fonts["body"])
    passed = flown = 0
    for row, scenario in enumerate(SCENARIOS):
        for col, setup in enumerate(combos):
            if not applies(scenario, setup):
                continue
            r = run.result(scenario, setup.name)
            if r is None or not r.flown:
                color, words = _c("lines"), "not yet"
            elif r.passed:
                color, words = _c("accent"), "pass"
            else:
                color, words = _c("pop"), "fail"
            flown += r is not None and r.flown
            passed += r is not None and r.passed
            ax.add_patch(_cell(col, row, color))
            ax.text(col, row, words, ha="center", va="center", fontsize=11,
                    color=_c("background") if words != "not yet" else _c("muted"),
                    family=fonts["body"], weight="bold")  # fmt: skip
    total = len(run.expected())
    canvas.headline(
        f"{passed} of {total}",
        f"runs pass. {flown - passed} fail, and the report says exactly why: "
        "docs/reports/flight-sim.",
    )
    canvas.save(path)
    return path


def _cell(col, row, color):
    from matplotlib.patches import FancyBboxPatch

    return FancyBboxPatch((col - 0.44, row - 0.38), 0.88, 0.76,
                          boxstyle="round,pad=0,rounding_size=0.08", color=color,
                          linewidth=0)  # fmt: skip


def settle_of(result) -> float | None:
    """The first step's settling time, from a steps result."""
    for f in result.findings:
        if f.check.startswith("roll to") and f.check.endswith("settling"):
            return f.value
    return None


def draw_all(folder: Path, run, exports: Path, chute=None) -> list[Path]:
    """Whichever stills the flown runs allow. `chute` is (ejection_s, opening_s)."""
    from pcs14.flight.batch import flown_log

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = [matrix(run, folder / "matrix.png")]
    for setup in ("mission", "P", "max", "P+C"):
        found = flown_log(exports, setup, "parachute-drop")
        if found is not None and chute is not None:
            log, _, _ = found
            for size in SIZES:
                paths.append(drop(log, folder / f"drop-{size}.png", setup, *chute, size=size))
            break
    tuned = flown_log(exports, "base", "steps")
    stock = flown_log(exports, "base", "steps-x500-gains")
    if tuned is not None and stock is not None:
        both = []
        for log, marks, result in (tuned, stock):
            both.append((log, marks, settle_of(result) or math.nan))
        paths.append(steps(both[0], both[1], folder / "steps.png"))
    return paths
