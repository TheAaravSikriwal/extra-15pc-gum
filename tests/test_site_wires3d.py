"""Every wire in 3D for the site (pcs14.site.wires3d), from the real design: each wire's two pins
in the drone's frame, the route between them, and the pieces its ends ride with."""

import math
from pathlib import Path

import pytest

from pcs14.site import schema, wires3d

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data():
    return wires3d.wires3d(ROOT / "design")


def test_a_point_turns_about_x_then_y_then_z_and_then_moves():
    # a quarter turn about z takes +x to +y; about x first, +y goes to +z
    assert wires3d.placed((10, 0, 0), (0, 0, 0), (0, 0, 90)) == pytest.approx((0, 10, 0), abs=1e-9)
    assert wires3d.placed((0, 10, 0), (5, 0, 0), (90, 0, 90)) == pytest.approx((5, 0, 10), abs=1e-9)


def test_it_turns_the_way_the_cad_does():
    locate = pytest.importorskip("pcs14.cad.locate")
    from pcs14.cad.settings import Placement

    spot = Placement(at_mm=(38, 39.1, 59), turn_deg=(90, 0, 0))
    cad = locate.place_point((0.0126, -0.0045, 0.013), spot)
    ours = wires3d.placed((12.6, -4.5, 13), (38, 39.1, 59), (90, 0, 0))
    assert [v * 1000 for v in cad] == pytest.approx(ours, abs=1e-6)


def test_every_wire_once_with_both_ends_placed(data):
    from pcs14.electrical.model import load_connection_list

    connections = load_connection_list(ROOT / "design" / "electrical.yaml")
    assert [w.label for w in data.wires] == [w.label for w in connections.wires]
    for w in data.wires:
        assert len(w.ends) == 2 and all(len(e.at_mm) == 3 for e in w.ends), w.label


def test_each_end_sits_on_its_part_where_the_cad_put_it(data):
    # the flight controller sits on the ESC at 20.4 mm, centered: its ESC plug on its +x edge
    ch1 = next(e for w in data.wires for e in w.ends if e.pin == "fc.ESC.CH1")
    assert ch1.piece == "ark-fpv"
    assert ch1.at_mm == pytest.approx([16.3, -5.15, 22.0], abs=0.01)
    # the BEC is turned a quarter turn about z, so its pads' +x edge faces +y on the drone
    out = next(e for w in data.wires for e in w.ends if e.pin == "bec.pads.OUT")
    assert out.at_mm[1] == pytest.approx(15.85, abs=0.01)
    # a motor's leads at its corner, and the second fuse at its own spot
    lead = next(e for w in data.wires for e in w.ends if e.pin == "m3.leads.A")
    assert lead.piece == "motor front left" and lead.at_mm[0] > 100 and lead.at_mm[1] > 100
    fuse = next(e for w in data.wires for e in w.ends if e.pin.startswith("fuses.F2"))
    assert fuse.piece == "branch-fuses 2"


def test_a_plug_in_a_socket_sits_at_the_socket(data):
    # the module bus harness's 4-pin plug sits in the flight controller's CAN port
    end = next(e for w in data.wires for e in w.ends if e.pin.startswith("sockets.FC_CAN"))
    assert end.piece == "ark-fpv"


def test_a_routed_wire_follows_its_route_from_the_end_nearest_its_first_pin(data):
    leads = next(w for w in data.wires if w.ends[0].pin == "lead.XT60.+")
    assert leads.route == "battery leads" and leads.route_piece == "wire battery leads"
    first, last = leads.path_mm[0], leads.path_mm[-1]
    a, b = leads.ends[0].at_mm, leads.ends[1].at_mm
    assert math.dist(a, first) + math.dist(b, last) <= math.dist(a, last) + math.dist(b, first)
    assert leads.awg == 12 and leads.role == "power"
    assert leads.length_mm == pytest.approx(
        sum(map(math.dist, leads.path_mm, leads.path_mm[1:])), rel=0.01
    )
    # a short jumper has no route, only its own length
    jumper = next(w for w in data.wires if w.route is None)
    assert jumper.path_mm == [] and jumper.length_mm > 0


def test_every_connector_says_where_its_pins_came_from(data):
    sources = {c.connector: c for c in data.connectors}
    assert not sources["fc.ESC"].estimate and "arkelectron" in sources["fc.ESC"].url
    assert sources["cut.J1"].estimate and sources["cut.J1"].note
    ends = {e.pin.rsplit(".", 1)[0] for w in data.wires for e in w.ends}
    assert {c.connector for c in data.connectors} >= {
        e for e in ends if not e.startswith("sockets.FC")
    }


def test_it_validates_as_the_site_reads_it(data):
    again = schema.Wires3d.model_validate_json(data.model_dump_json())
    assert again.wires[0].label == data.wires[0].label
