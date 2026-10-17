"""The sweep, on a small made-up catalog with an obvious winner.

The winner is the light M2810 motor on the 4500 mAh cell in 6S2P. Going 3P adds 420 g and
fails thrust-to-weight at the reserve; the 3000 mAh cell runs out of flight time and current;
the heavier M3115 motor passes but with less to spare; and its 12 inch prop doesn't fit the
10 inch frame, so those builds get skipped with a reason.
"""

import shutil
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.sizing.sweep import margin_curve, sweep
from pcs14.viz import Recorder

FIXTURES = Path(__file__).parent / "fixtures"

MADE_UP = "source: {kind: made_up, note: Invented for the sweep tests}\n"
ROWS = """    rows:
      - {throttle_pct: 20, thrust_g: 220, current_a: 1.2, rpm: 4300}
      - {throttle_pct: 50, thrust_g: 900, current_a: 6.7, rpm: 8600}
      - {throttle_pct: 80, thrust_g: 1650, current_a: 17.0, rpm: 11600}
      - {throttle_pct: 100, thrust_g: 2100, current_a: 26.5, rpm: 13100}
"""
HEAVY_MOTOR = (
    "type: motor\nid: testco-m3115-900kv\nmaker: Testco\nmodel: M3115 900KV\n"
    + MADE_UP
    + "mass_g: 110\nkv: 900\ncells_min: 4\ncells_max: 6\nmax_current_a: 45\nthrust_tables:\n"
    + "  - prop: testco-p10x45\n    voltage_v: 24.0\n    "
    + MADE_UP
    + ROWS
    + "  - prop: testco-p12x6\n    voltage_v: 24.0\n    "
    + MADE_UP
    + ROWS
)
BIG_PROP = (
    "type: prop\nid: testco-p12x6\nmaker: Testco\nmodel: P12x6\n"
    + MADE_UP
    + "mass_g: 20\ndiameter_in: 12\npitch_in: 6\nblades: 2\n"
)
SMALL_CELL = (
    (FIXTURES / "catalog" / "cells" / "testco-c21700-45.yaml")
    .read_text()
    .replace("testco-c21700-45", "testco-c21700-30")
    .replace("model: C21700-45", "model: C21700-30")
    .replace("capacity_mah: 4500", "capacity_mah: 3000")
    .replace("max_continuous_a: 45", "max_continuous_a: 35")
    .replace("mass_g: 70", "mass_g: 65")
)


@pytest.fixture
def sweep_catalog(tmp_path):
    root = tmp_path / "catalog"
    shutil.copytree(FIXTURES / "catalog", root)
    (root / "motors" / "testco-m3115-900kv.yaml").write_text(HEAVY_MOTOR)
    (root / "props" / "testco-p12x6.yaml").write_text(BIG_PROP)
    (root / "cells" / "testco-c21700-30.yaml").write_text(SMALL_CELL)
    return load_catalog(root, allow_made_up=True)


@pytest.fixture
def swept(build, sweep_catalog, targets):
    return sweep(build, sweep_catalog, targets)


def test_the_obvious_winner_comes_first(swept):
    best = swept.ranked[0].build
    assert best.motor.id == "testco-m2810-900kv"
    assert best.pack.cell.id == "testco-c21700-45"
    assert best.pack.parallel == 2


def test_passing_and_marginal_builds_rank_above_failing_ones(swept):
    order = {"pass": 0, "marginal": 1, "fail": 2}
    verdicts = [order[c.verdict] for c in swept.ranked]
    assert verdicts == sorted(verdicts)


def test_every_combination_that_fits_gets_tried(swept):
    # 2 motors x 2 cells x 2 layouts on the 10 inch prop, plus the heavy motor's 12 inch
    # prop, which gets skipped for every cell and layout
    assert len(swept.ranked) == 8
    assert len(swept.skipped) == 4
    assert all("too big" in reason for _, reason in swept.skipped)


def test_the_sweep_fills_in_live(build, sweep_catalog, targets, tmp_path):
    path = tmp_path / "sweep.rrd"
    recorder = Recorder(path=path)
    sweep(build, sweep_catalog, targets, recorder=recorder)
    recorder.close()
    assert path.stat().st_size > 1000


def test_every_extra_100_g_costs_flight_time(build, targets):
    curve = margin_curve(build, targets, grams=range(0, 401, 100))
    mission = curve["mission"]
    assert [point.grams for point in mission] == [0, 100, 200, 300, 400]
    cruise = [point.cruise_minutes for point in mission]
    assert cruise == sorted(cruise, reverse=True)
    assert cruise[0] - cruise[1] > 0.5  # 100 g costs more than half a minute
