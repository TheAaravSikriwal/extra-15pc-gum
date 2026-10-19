"""The electrical layer in Rerun: the drone's wires colored by how hard they work, the switch sims
as scope traces, and temperatures through the burst."""

from types import SimpleNamespace

import numpy as np
import pytest
import rerun.blueprint as rrb

from electrical_parts import good
from pcs14 import style
from pcs14.electrical.model import ConnectionList


def test_a_share_of_the_limit_gets_a_color():
    from pcs14.viz.electrical_log import share_color

    assert share_color(0.0) != share_color(0.8)
    assert share_color(1.2) == style.rgb("pop")  # past its limit: magenta
    assert max(share_color(0.0)) > 150  # an idle wire still shows on the black background


def test_a_scope_trace_keeps_its_edges_and_drops_its_flat_stretches():
    from pcs14.viz.electrical_log import thin

    times = np.arange(1000) * 1e-9
    volts = np.where(times < 500e-9, 0.0, 3.3) + 1e-4 * np.sin(times * 1e8)  # one edge, a ripple
    t, v = thin(times, volts, step=0.033)
    assert len(t) < 10
    assert t[0] == times[0] and t[-1] == times[-1]
    edge = int(np.argmin(abs(t - 500e-9)))
    assert t[edge] == pytest.approx(500e-9)
    assert t[edge - 1] == pytest.approx(499e-9) and v[edge] == pytest.approx(volts[500])


def _cad_wires():
    return [
        SimpleNamespace(
            name="main", module="base", path=[(0, 0, -0.01), (0.1, 0, 0.02)], diameter=0.004
        ),
        SimpleNamespace(
            name="signal", module="P", path=[(0, 0, 0.02), (0, 0.1, 0.02)], diameter=0.001
        ),
    ]


def test_a_route_works_as_hard_as_its_hardest_wire():
    from pcs14.viz.electrical_log import route_shares

    design = ConnectionList.model_validate(good())
    working = {("base", "hover"): {"pack.XT60.+ to reg.J.VIN": 0.3, "reg.J.VOUT to load.J.5V": 0.1}}
    assert route_shares(design, working)[("base", "hover")]["main"] == pytest.approx(0.3)


def test_a_connector_sits_at_the_end_of_its_route_nearest_the_pack():
    from pcs14.viz.electrical_log import connector_points

    design = ConnectionList.model_validate(good())
    points = connector_points(design, _cad_wires(), near=(0, 0, -0.05))
    assert points["pack.XT60.+"] == (0, 0, -0.01)


def test_writes_an_electrical_recording_without_a_viewer(tmp_path):
    from build123d import Box

    from pcs14.cad.assembly import Piece
    from pcs14.viz.electrical_log import ElectricalRecorder, record

    design = ConnectionList.model_validate(good())
    pieces = [
        Piece("frame", Box(0.3, 0.03, 0.035), "frame", "base", 0.3, 0.3),
        Piece("pack", Box(0.1, 0.05, 0.03), "pack", "base", 0.5, 0.5),
        Piece("servo", Box(0.02, 0.01, 0.02), "bought", "P", 0.01, 0.01),
    ]
    setups = {"base": frozenset(), "P": frozenset({"P"})}
    label = "pack.XT60.+ to reg.J.VIN"
    working = {
        (s, c): {label: 0.4 if c == "hover" else 1.1} for s in setups for c in ("hover", "burst")
    }
    connectors = {key: {"pack.XT60.+": 0.5} for key in working}
    curves = [(label, [(0.0, 61.0), (10.0, 80.0)], 180.0)]
    times = np.linspace(0, 50e-6, 200)
    sims = {
        "Teensy off": SimpleNamespace(
            waves={"time": times, "v(esc)": np.sin(times * 1e6), "v(tap)": times}
        )
    }
    path = tmp_path / "electrical.rrd"
    recorder = ElectricalRecorder(path)
    record(
        recorder,
        pieces,
        _cad_wires(),
        design,
        setups,
        working,
        connectors,
        curves,
        sims,
        "all good",
    )
    recorder.close()
    assert path.stat().st_size > 0


def _views(container):
    for item in getattr(container, "contents", []):
        yield item
        yield from _views(item)


def test_every_plot_opens_on_the_whole_run():
    from pcs14.viz.electrical_log import SCOPES, electrical_blueprint
    from pcs14.viz.rerun_log import WHOLE_RUN

    blueprint = electrical_blueprint()
    plots = [v for v in _views(blueprint.root_container) if isinstance(v, rrb.TimeSeriesView)]
    assert len(plots) == len(SCOPES) + 1  # a scope plot for each switch case, and the heat
    for plot in plots:
        assert repr(plot.properties.get("TimeAxis")) == repr(WHOLE_RUN), plot.name


def test_it_opens_on_the_wires_and_their_timeline():
    from pcs14.viz.electrical_log import electrical_blueprint

    blueprint = electrical_blueprint()
    tabs = blueprint.root_container
    assert isinstance(tabs, rrb.Tabs) and tabs.contents[0].name == "Wires"
    assert blueprint.time_panel.timeline == "step"
