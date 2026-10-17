"""Streaming the sizing model's tests into Rerun.

Every simulated flight goes in as a set of time series (pack voltage, charge used, current
and thrust headroom) on a `flight_time` timeline, so it can be scrubbed and replayed. The
sweep goes in candidate by candidate on a `candidate` timeline, so it fills in as it runs.
A recording can stream to a live viewer, save to an .rrd file, or both.
"""

import re
from pathlib import Path

import rerun as rr
import rerun.blueprint as rrb

from pcs14 import style
from pcs14.sizing.flight import Flight

QUANTITIES = {
    "voltage": ("Pack voltage (V)", lambda sample: sample.voltage),
    "charge": ("Charge used (mAh)", lambda sample: sample.mah_used),
    "current": ("Current (A)", lambda sample: sample.current),
    "headroom": (
        "Thrust headroom (full throttle over needed)",
        lambda sample: sample.thrust_headroom,
    ),
}


def _safe(name: str) -> str:
    """Entity paths can't hold characters like the + in 'V+C', so they're dropped."""
    return re.sub(r"[^A-Za-z0-9_-]", "", name)


def blueprint() -> rrb.Blueprint:
    flights = rrb.Grid(
        *(
            rrb.TimeSeriesView(origin=f"/{key}", name=title)
            for key, (title, _) in QUANTITIES.items()
        ),
        name="Flights",
    )
    sweep = rrb.TimeSeriesView(origin="/sweep", name="Sweep: cruise minutes per candidate")
    summary = rrb.TextDocumentView(origin="/summary", name="Summary")
    return rrb.Blueprint(rrb.Tabs(flights, sweep, summary), collapse_panels=True)


class Recorder:
    def __init__(self, path: Path | None = None, live: bool = False, app: str = "pcs14-sizing"):
        sinks = []
        if live:
            rr.spawn(connect=False)
            sinks.append(rr.GrpcSink())
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            sinks.append(rr.FileSink(str(path)))
        if not sinks:
            raise ValueError("a recording needs somewhere to go: a file, a live viewer, or both")
        self.rec = rr.RecordingStream(app)
        self.rec.set_sinks(*sinks, default_blueprint=blueprint())

    def log_flight(self, setup: str, kind: str, case: str, flight: Flight, highlight: bool) -> None:
        """One flight: `kind` is hover or cruise, `case` is nominal or pessimistic."""
        base = style.rgb("accent") if highlight else style.rgb("muted")
        nominal = case == "nominal"
        color = [*base, 255 if nominal else 110]
        times = [sample.time for sample in flight.samples]
        for key, (_, value) in QUANTITIES.items():
            path = f"{key}/{_safe(setup)}/{kind}/{case}"
            rr.log(
                path,
                rr.SeriesLines(
                    colors=[color],
                    widths=[2.5 if highlight and nominal else 1.2],
                    names=[f"{setup}, {kind}, {case}"],
                ),
                static=True,
                recording=self.rec,
            )
            rr.send_columns(
                path,
                indexes=[rr.TimeColumn("flight_time", duration=times)],
                columns=rr.Scalars.columns(scalars=[value(sample) for sample in flight.samples]),
                recording=self.rec,
            )

    def log_reserve(self, reserve_mah: float, longest: float) -> None:
        """The 20% reserve as a line across the charge plot."""
        path = "charge/reserve"
        rr.log(
            path,
            rr.SeriesLines(colors=[[*style.rgb("pop"), 255]], widths=[1.5], names=["reserve"]),
            static=True,
            recording=self.rec,
        )
        rr.send_columns(
            path,
            indexes=[rr.TimeColumn("flight_time", duration=[0.0, longest])],
            columns=rr.Scalars.columns(scalars=[reserve_mah, reserve_mah]),
            recording=self.rec,
        )

    def log_candidate(self, index: int, minutes: float, verdict: str) -> None:
        """One sweep candidate, as a point colored by its verdict."""
        self.rec.set_time("candidate", sequence=index)
        rr.log(
            f"sweep/{verdict}",
            rr.SeriesPoints(colors=[[*style.hex_to_rgb(style.verdict_color(verdict)), 255]]),
            static=True,
            recording=self.rec,
        )
        rr.log(f"sweep/{verdict}", rr.Scalars(minutes), recording=self.rec)

    def log_summary(self, markdown: str) -> None:
        rr.log(
            "summary",
            rr.TextDocument(markdown, media_type=rr.MediaType.MARKDOWN),
            static=True,
            recording=self.rec,
        )

    def close(self) -> None:
        self.rec.flush()
        self.rec.disconnect()
