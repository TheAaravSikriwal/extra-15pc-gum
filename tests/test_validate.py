"""The honesty check: run the model on published builds and see how far off it is."""

from pathlib import Path

import pytest

from pcs14.catalog import Cell
from pcs14.sizing.validate import compare_case, discharge_check, load_cases

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cases(catalog):
    return load_cases(FIXTURES / "validation", catalog)


def test_cases_load_with_their_parts(cases):
    assert [c.name for c in cases] == ["Testco hover test"]
    case = cases[0]
    assert case.motor.id == "testco-m2810-900kv"
    assert case.pack.series == 6
    assert case.weight == pytest.approx(1.8 * 9.80665)


def test_comparison_flies_the_build_until_the_stated_point(cases):
    result = compare_case(cases[0])
    assert result.measured_minutes == 36.0
    # Flown to 80% used, like the made-up measurement says
    assert result.flight.samples[-1].soc == pytest.approx(0.2, abs=0.01)
    assert 20 < result.predicted_minutes < 60
    assert result.predicted_pessimistic < result.predicted_minutes
    expected = (result.predicted_minutes - 36.0) / 36.0
    assert result.error == pytest.approx(expected)


def test_stopping_on_a_loaded_voltage(cases, tmp_path):
    case = cases[0].model_copy(
        update={
            "measured": cases[0].measured.model_copy(
                update={"until": {"loaded_voltage_per_cell_v": 3.3}}
            )
        }
    )
    result = compare_case(case)
    assert result.flight.samples[-1].voltage <= 6 * 3.3 + 0.05


def _cell_with_test(points):
    return Cell.model_validate(
        {
            "type": "cell",
            "id": "testco-curve",
            "maker": "Testco",
            "model": "curve",
            "source": {"kind": "made_up", "note": "test"},
            "mass_g": 70,
            "capacity_mah": 4000,
            "max_continuous_a": 30,
            "min_voltage_v": 2.5,
            "max_voltage_v": 4.2,
            "internal_resistance_mohm": 20,
            "resistance_source": {"kind": "made_up", "note": "test"},
            "ocv_source": {"kind": "made_up", "note": "test"},
            "ocv_curve": [
                {"soc": 0.0, "voltage_v": 3.0},
                {"soc": 0.5, "voltage_v": 3.7},
                {"soc": 1.0, "voltage_v": 4.2},
            ],
            "discharge_tests": [
                {"current_a": 10, "source": {"kind": "made_up", "note": "test"}, "points": points}
            ],
        }
    )


def test_a_discharge_curve_that_matches_the_model_exactly():
    # At 10 A and 20 milliohms the model sits 0.2 V under the resting curve
    cell = _cell_with_test(
        [
            {"capacity_mah": 0, "voltage_v": 4.0},
            {"capacity_mah": 2000, "voltage_v": 3.5},
            {"capacity_mah": 4000, "voltage_v": 2.8},
        ]
    )
    (check,) = discharge_check(cell)
    assert check.current == 10
    assert check.rms_error == pytest.approx(0.0, abs=1e-9)


def test_a_discharge_curve_that_sags_more_than_the_model():
    cell = _cell_with_test(
        [
            {"capacity_mah": 0, "voltage_v": 3.9},
            {"capacity_mah": 2000, "voltage_v": 3.4},
            {"capacity_mah": 4000, "voltage_v": 2.7},
        ]
    )
    (check,) = discharge_check(cell)
    assert check.rms_error == pytest.approx(0.1)
    assert check.mean_error == pytest.approx(-0.1)  # the real cell sits 0.1 V lower


def test_the_validation_report(cases, catalog, tmp_path):
    from pcs14.report.validation import write_validation

    comparisons = [compare_case(c) for c in cases]
    checks = [check for cell in catalog.cells.values() for check in discharge_check(cell)]
    out = write_validation(
        tmp_path / "v", comparisons, checks, made_up=True, generated="2026-10-17"
    )
    text = (out / "validation.md").read_text(encoding="utf-8")
    assert "Testco hover test" in text
    assert "made-up test parts" in text
    assert (out / "charts" / "validation.png").stat().st_size > 1000


def test_a_made_up_validation_cant_go_in_docs_reports(cases):
    from pcs14.report.validation import write_validation

    root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="made-up"):
        write_validation(root / "docs" / "reports" / "sizing", [], [], made_up=True)


def test_the_drag_area_it_would_take_to_match(cases):
    from pcs14.sizing.validate import drag_area_to_match

    hover = cases[0]
    assert drag_area_to_match(hover) is None  # drag doesn't matter in a hover

    cruise_measured = hover.measured.model_copy(update={"kind": "cruise", "speed_ms": 12.0})
    cruise = hover.model_copy(update={"measured": cruise_measured})
    shorter = 0.8 * compare_case(cruise).predicted_minutes
    case = cruise.model_copy(
        update={"measured": cruise_measured.model_copy(update={"minutes": shorter})}
    )
    needed = drag_area_to_match(case)
    assert needed > case.drag_area_cm2
    matched = compare_case(case.model_copy(update={"drag_area_cm2": needed}))
    assert matched.predicted_minutes == pytest.approx(shorter, abs=0.1)
