"""Heat: wire and connector temperatures, steady and through a burst, checked by hand and against
a wire maker's published table."""

import math

import pytest

from pcs14.electrical import thermal
from pcs14.electrical.checks import awg_area

# UL3135 silicone: 20 C resistance in ohms per meter and outer diameter in meters
SILICONE = {12: (5.64e-3, 3.95e-3), 18: (23.2e-3, 2.70e-3), 22: (59.4e-3, 2.32e-3)}


def silicone(awg):
    ohms, outer = SILICONE[awg]
    return thermal.WireModel(ohms, awg_area(awg), outer, thermal.SILICONE)


def test_the_steady_state_balances():
    wire = silicone(18)
    hot = wire.steady(20.0, air_c=40.0)
    # every watt the copper makes leaves the surface, after crossing the insulation
    heat = 20.0**2 * wire.ohms_per_m * (1 + thermal.ALPHA * (hot.conductor_c - 20))
    out = wire.cooling(hot.surface_c, 40.0) * math.pi * wire.outer * (hot.surface_c - 40.0)
    assert out == pytest.approx(heat, rel=1e-3)
    across = (
        heat * math.log(wire.outer / wire.conductor) / (2 * math.pi * thermal.SILICONE.conductivity)
    )
    assert hot.conductor_c - hot.surface_c == pytest.approx(across, rel=1e-3)


@pytest.mark.parametrize("awg, published", [(12, 68), (18, 28), (22, 16)])
def test_free_air_ampacity_matches_remingtons_table(awg, published):
    # Remington: a single conductor in free air, 30 C ambient, up to a 200 C insulation rating
    assert silicone(awg).ampacity(200, air_c=30) == pytest.approx(published, rel=0.05)


def test_a_burst_with_no_cooling_heats_the_copper_by_hand():
    # 18 AWG at 50 A for one second, copper only, no cooling, resistance held at 20 C
    wire = thermal.WireModel(23.2e-3, awg_area(18), 2.7e-3, thermal.SILICONE)
    end = wire.burst(
        start_c=40, amps=50, seconds=1.0, air_c=40, cooling=False, insulation_mass=False, alpha=0
    )
    copper = awg_area(18) * thermal.COPPER_DENSITY * thermal.COPPER_HEAT
    assert end - 40 == pytest.approx(50**2 * 23.2e-3 * 1.0 / copper, rel=1e-3)


def test_a_burst_never_passes_the_steady_temperature_at_its_current():
    wire = silicone(12)
    start = wire.steady(23, air_c=40).conductor_c
    end = wire.burst(start_c=start, amps=90, seconds=10, air_c=40)
    assert start < end < wire.steady(90, air_c=40).conductor_c


def test_a_connector_at_its_rated_current_lands_at_its_published_rise():
    # Amass: 35 A with under 85 K of rise, contacts at 1.0 mOhm
    xt60 = thermal.ConnectorModel(rated_a=35, rise_c=85, contact_ohms=1.0e-3, heat_capacity=2.0)
    assert xt60.steady_rise(35) == pytest.approx(85)
    assert xt60.steady_rise(17.5) == pytest.approx(85 / 4)


def test_a_connector_burst_follows_its_time_constant():
    xt60 = thermal.ConnectorModel(rated_a=35, rise_c=85, contact_ohms=1.0e-3, heat_capacity=2.0)
    tau = (85 / 35**2) / 1.0e-3 * 2.0  # thermal resistance times heat capacity
    start = xt60.steady_rise(20)
    end = xt60.burst_rise(start_rise=start, amps=90, seconds=10)
    final = xt60.steady_rise(90)
    assert end == pytest.approx(final + (start - final) * math.exp(-10 / tau))


def test_a_bursts_trajectory_ends_where_the_burst_does():
    wire = silicone(12)
    start = wire.steady(23, air_c=40).conductor_c
    curve = wire.trajectory(start_c=start, amps=90, seconds=10, air_c=40, points=11)
    assert len(curve) == 11 and curve[0] == (0.0, pytest.approx(start))
    assert curve[-1][0] == pytest.approx(10)
    assert curve[-1][1] == pytest.approx(wire.burst(start, 90, 10, 40), abs=0.01)
    assert all(b[1] >= a[1] for a, b in zip(curve, curve[1:], strict=False))


def test_a_connectors_trajectory_follows_its_time_constant():
    xt60 = thermal.ConnectorModel(rated_a=35, rise_c=85, contact_ohms=1.0e-3, heat_capacity=2.0)
    curve = xt60.trajectory(start_rise=10, amps=90, seconds=10, points=5)
    assert curve[-1][1] == pytest.approx(xt60.burst_rise(10, 90, 10))


def _hot_wire_case():
    """A 24 V load on a made-up silicone 18 AWG pair, hovering at 2 A and bursting at 3 A."""
    from pcs14.catalog.schema import Wire
    from test_electrical_checks import context, solutions_for
    from test_electrical_loads import ALL, ALL_LISTED, wire

    table = ALL["t-wire"].model_dump(mode="json")
    table.update(id="t-silicone", insulation="silicone")
    parts = {**ALL, "t-silicone": Wire.model_validate(table)}
    data = {
        "boards": {"load": {"part": "t-24v-load"}},
        "wires": [
            {**wire("pack.XT60.+", "load.J.IN", 300), "wire": "t-silicone"},
            wire("pack.XT60.-", "load.J.GND", 300),
        ],
    }
    from pcs14.electrical.loads import Case

    cases = [
        Case("hover", pack_volts=25.0, draw="typical"),
        Case("burst", pack_volts=25.0, draw="worst"),
    ]
    design, solutions = solutions_for(data, cases, parts, ALL_LISTED)
    return context(design, parts, ALL_LISTED), solutions


def test_how_hard_a_wire_works_is_its_share_of_the_allowed_heating():
    ctx, solutions = _hot_wire_case()
    working = thermal.wire_working(ctx, solutions)
    label = "pack.XT60.+ to load.J.IN"
    model = silicone(18)
    model = thermal.WireModel(21e-3, model.area, 2.7e-3, thermal.SILICONE)
    air, limit = 40, 200 - 20
    hover = model.steady(2.0, air).conductor_c
    assert working[("test", "hover")][label] == pytest.approx((hover - air) / (limit - air), 1e-3)
    burst = model.burst(hover, 3.0, 10, air)
    assert working[("test", "burst")][label] == pytest.approx((burst - air) / (limit - air), 1e-3)
    # the ground wire's table has no insulation rating, so there's nothing to share out
    assert "pack.XT60.- to load.J.GND" not in working[("test", "hover")]


def test_burst_curves_start_hot_and_carry_their_limits():
    ctx, solutions = _hot_wire_case()
    curves = thermal.burst_curves(ctx, solutions)
    name, curve, limit_c = curves[0]
    assert name == "pack.XT60.+ to load.J.IN"
    assert limit_c == 180
    assert curve[0][0] == 0 and curve[-1][0] == pytest.approx(10)
    assert curve[0][1] > 40 and curve[-1][1] > curve[0][1]
