"""The build package's parts list, on the made-up catalog and build."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.catalog.schema import Wire
from pcs14.design import load_build
from pcs14.package import parts

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def build():
    catalog = load_catalog(FIXTURES / "catalog", allow_made_up=True)
    return load_build(FIXTURES / "build.yaml", catalog)


def priced(part, usd):
    return part.model_copy(update={"price_usd": usd})


WIRE = Wire.model_validate(
    {
        "type": "wire",
        "id": "testco-silicone",
        "maker": "Testco",
        "model": "Silicone wire",
        "source": {"kind": "made_up", "note": "test"},
        "insulation_max_c": 200,
        "gauges": [
            {
                "awg": 18,
                "resistance_mohm_per_m": 23.2,
                "outer_diameter_mm": 2.7,
                "mass_g_per_m": 12.9,
                "price_usd_per_m": 1.5,
            },
            {
                "awg": 26,
                "resistance_mohm_per_m": 150.0,
                "outer_diameter_mm": 2.05,
                "mass_g_per_m": 4.9,
            },
        ],
    }
)


def test_the_bought_parts_come_from_the_build_by_module(build):
    lines = parts.bought_lines(build)
    by_id = {(x.module, x.part_id): x for x in lines}
    assert by_id[("base", "testco-m2810-900kv")].qty == 4
    assert by_id[("base", "testco-p10x45")].qty == 4
    assert by_id[("base", "testco-c21700-45")].qty == 12  # 6S2P
    assert ("base", "testco-wiring") not in by_id  # weight only: its wire is listed as wire
    assert by_id[("V", "testco-gps")].qty == 1 and by_id[("C", "testco-claws")].qty == 1


def test_printed_parts_are_left_to_their_own_list(build):
    lines = parts.bought_lines(build, printed_ids={"testco-v-housing"})
    assert all(x.part_id != "testco-v-housing" for x in lines)


def test_wire_is_added_up_by_gauge_with_slack_and_rounded_up():
    runs = [
        ("testco-silicone", 18, "base", 0.40),
        ("testco-silicone", 18, "base", 0.37),
        ("testco-silicone", 26, "V", 0.10),
        ("testco-silicone", 18, "V", 0.2),
    ]
    lines = parts.wire_lines(runs, {"testco-silicone": WIRE})
    base = next(x for x in lines if x.module == "base")
    assert base.qty == pytest.approx(1.1)  # 0.77 m x 1.3 = 1.001, up to the next 10 cm
    assert base.unit == "m" and base.total == pytest.approx(1.65)
    thin = next(x for x in lines if x.module == "V" and "26 AWG" in x.name)
    assert thin.price_each is None and thin.total is None  # unpriced, not free
    assert len(lines) == 3


def test_plugs_are_counted_by_family_and_size(build):
    plug = build.motor  # any part stands in for a plug family here
    halves = [("base", "testco-plug", 4), ("base", "testco-plug", 4), ("V", "testco-plug", 8)]
    lines = parts.plug_lines(halves, {"testco-plug": plug})
    assert [(x.module, x.qty, x.name.endswith("4-pin")) for x in lines] == [
        ("V", 1, False),
        ("base", 2, True),
    ]


def test_hardware_rolls_up_by_module_and_size():
    hardware = [
        {"holds": "legs", "what": "M3 x 12 screw", "count": 8, "material": "steel"},
        {"holds": "tray", "what": "M3 x 12 screw", "count": 4, "material": "steel"},
        {"holds": "v-housing", "what": "M3 x 12 screw", "count": 1, "material": "steel"},
        {"holds": "legs", "what": "M3 lock nut", "count": 8, "material": "steel"},
    ]
    lines = parts.hardware_lines(hardware, {"v-housing": "V"})
    counts = {(x.module, x.model): x.qty for x in lines}
    assert counts == {
        ("base", "M3 x 12 screw"): 12,
        ("V", "M3 x 12 screw"): 1,
        ("base", "M3 lock nut"): 8,
    }


def test_each_combination_adds_its_modules_and_counts_what_isnt_priced(build):
    lines = [priced(build.motor, 40.0)]
    lines = parts.bought_lines(build.variant()) + parts.printed_lines(
        [{"name": "leg", "material": "tpu", "mass_g": 6.5, "module": "base"}]
    )
    lines = [
        x if x.part_id != "testco-m2810-900kv" else parts.Line(**{**x.__dict__, "price_each": 40.0})
        for x in lines
    ]
    lines.append(
        parts.Line(group="ground", module="once", name="Transmitter", qty=1, price_each=100.0)
    )
    sums = {t.setup: t for t in parts.totals(lines, [("base", ()), ("V", ("V",))])}
    assert sums["base"].usd == pytest.approx(160.0)  # four motors at $40
    assert sums["V"].unpriced > sums["base"].unpriced  # V's parts have no prices yet
    assert sums["base"].printed == 1 and sums["base"].printed_g == pytest.approx(6.5)
    assert sums["once"].usd == pytest.approx(100.0)


def test_the_csv_has_a_row_a_line(build):
    lines = parts.bought_lines(build)
    text = parts.to_csv(lines)
    rows = text.strip().splitlines()
    assert rows[0].startswith("module,group,name,qty") and len(rows) == len(lines) + 1


def test_an_extra_can_belong_to_a_module(tmp_path):
    path = tmp_path / "package.yaml"
    path.write_text(
        "items:\n"
        "  - {id: servo, module: P, group: ground, name: Servo, why: stand-in, maker: Hitec,\n"
        "     model: HS-55, price_usd: 16.99}\n"
        "  - {id: tx, group: ground, name: Transmitter, why: sticks, maker: Any, model: Any}\n",
        encoding="utf-8",
    )
    lines = parts.extra_lines(parts.load_extras(path))
    assert [(x.module, x.group) for x in lines] == [("P", "bought"), ("once", "ground")]
    sums = {t.setup: t for t in parts.totals(lines, [("P", ("P",))])}
    assert sums["P"].usd == pytest.approx(16.99) and sums["once"].unpriced == 1
