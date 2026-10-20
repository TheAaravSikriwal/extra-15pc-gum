"""The flight sim in Rerun: the CAD drone flying its logged path, with its plots."""

import numpy as np
import rerun.blueprint as rrb

from pcs14.flight.grade import FlightLog


def synthetic_flight():
    t = np.arange(0, 10, 0.02)
    climb = np.minimum(t, 5.0) * 2
    position = np.column_stack([0.5 * t, 0 * t, climb])
    velocity = np.gradient(position, t, axis=0)
    attitude = np.tile([0.0, 0.0, 0.0, 1.0], (len(t), 1))
    rotors = np.full((len(t), 4), 620.0)
    return FlightLog(t, position, velocity, rotors, [(9.0, "landed")], attitude)


def test_writes_a_flight_recording_without_a_viewer(tmp_path):
    from build123d import Box

    from pcs14.cad.assembly import Piece
    from pcs14.viz.flight_log import FlightRecorder

    path = tmp_path / "flight.rrd"
    recorder = FlightRecorder(path)
    recorder.log_drone([Piece("frame", Box(0.3, 0.03, 0.035), "frame", "base", 0.3, 0.3)])
    recorder.log_flight("hover, mission", synthetic_flight(), max_rot_velocity=930.0)
    recorder.log_summary("all good")
    recorder.close()
    assert path.stat().st_size > 0


def test_every_plot_opens_on_the_whole_flight():
    from pcs14.viz.flight_log import flight_blueprint
    from pcs14.viz.rerun_log import WHOLE_RUN

    def views(container):
        for item in getattr(container, "contents", []):
            yield item
            yield from views(item)

    plots = [
        v for v in views(flight_blueprint().root_container) if isinstance(v, rrb.TimeSeriesView)
    ]
    assert len(plots) == 3
    for plot in plots:
        assert repr(plot.properties.get("TimeAxis")) == repr(WHOLE_RUN), plot.name
