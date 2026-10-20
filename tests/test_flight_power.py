"""Power afterwards: a flight's logged rotor speeds turned into current, through the sizing
model's battery model."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets
from pcs14.flight import power

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real():
    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    targets = load_targets(ROOT / "design" / "targets.yaml")
    setup = next(s for s in targets.combinations() if s.name == "mission")
    return build, targets, setup


def test_a_motors_power_follows_its_table_and_the_cube_below_it(real):
    build, _, _ = real
    table = build.thrust_table
    first = table.rows[0]
    assert power.motor_power(table, first.rpm) == pytest.approx(first.power)
    assert power.motor_power(table, first.rpm / 2) == pytest.approx(first.power / 8)
    middle = (table.rows[2].rpm + table.rows[3].rpm) / 2
    assert power.motor_power(table, middle) == pytest.approx(
        (table.rows[2].power + table.rows[3].power) / 2
    )


def test_a_steady_hover_lasts_as_long_as_the_sizing_model_says(real):
    from pcs14.sizing.battery import Pack
    from pcs14.sizing.flight import avionics_power, fly, power_model

    build, targets, setup = real
    model = power_model(build, setup, targets.growth_margin, pessimistic=True)
    pack = Pack(build.pack)
    sizing = fly(model, pack, 0.0, targets.reserve_fraction).samples[-1].time
    rpm = model.rotor.rpm_for_thrust(model.hover_thrust)
    watts = power.electrical_power(build.thrust_table, [rpm] * 4, avionics_power(build, setup))
    assert power.endurance(pack, watts, targets.reserve_fraction) == pytest.approx(sizing, rel=0.01)


def test_a_logged_flight_drains_the_pack_sample_by_sample(real):
    from pcs14.sizing.battery import Pack

    build, _, _ = real
    pack = Pack(build.pack)
    times = [0.0, 30.0, 60.0]
    drained = power.drain(pack, times, [400.0, 400.0, 400.0])
    current = pack.current_for_power(1.0, 400.0)
    assert drained.mah_used[-1] == pytest.approx(current * 60 / 3.6, rel=0.01)
    assert drained.soc[0] == 1.0 and drained.soc[-1] < 1.0
    assert drained.voltage[-1] < drained.voltage[0]
