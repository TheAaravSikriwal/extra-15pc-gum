"""The flight sim's stills draw from made-up flights, in every post size they're made in."""

import math

import numpy as np
import pytest

from pcs14.flight import grade, stills
from pcs14.flight.report import FlightSimRun, ScenarioResult


def made_up_drop():
    """Hovering 40 m up, terminated at 10 s: free fall until the canopy holds, then 4.2 m/s."""
    t = np.arange(0, 22, 0.02)
    fall = np.clip(t - 10, 0, 1.2)
    z = np.where(t < 10, 40.0, np.maximum(40 - 4.9 * fall**2 - 4.2 * np.maximum(t - 11.2, 0), 0))
    vz = np.gradient(z, t)
    events = [(10.0, "terminate"), (10.02, "chute fired"), (10.08, "motors stopped")]
    return grade.FlightLog(t, np.column_stack([0 * t, 0 * t, z]),
                           np.column_stack([0 * t, 0 * t, vz]), np.zeros((len(t), 4)),
                           events)  # fmt: skip


def made_up_steps(tau):
    """A first-order roll response to a 15 degree step at 5 s, with time constant `tau`."""
    t = np.arange(0, 8, 0.004)
    roll = np.where(t < 5, 0.0, math.radians(15) * (1 - np.exp(-(t - 5) / tau)))
    half = roll / 2
    attitude = np.column_stack([np.sin(half), 0 * t, 0 * t, np.cos(half)])  # roll in FLU/ENU
    log = grade.FlightLog(t, np.zeros((len(t), 3)), np.zeros((len(t), 3)),
                          np.zeros((len(t), 4)), [], attitude)  # fmt: skip
    return log, [(5.0, "step 0 start"), (7.0, "step 0 end")], 3 * tau


@pytest.mark.parametrize("size", stills.SIZES)
def test_the_drop_draws_in_every_post_size(tmp_path, size):
    path = stills.drop(made_up_drop(), tmp_path / f"drop-{size}.png", "P", 0.2, 1.0, size=size)
    assert path.stat().st_size > 10_000


def test_the_steps_compare_two_gains(tmp_path):
    path = stills.steps(made_up_steps(0.08), made_up_steps(0.2), tmp_path / "steps.png")
    assert path.stat().st_size > 10_000


def test_the_matrix_shows_every_run(tmp_path, targets):
    setups = tuple(targets.combinations())
    results = (
        ScenarioResult("hover", setups[0].name, True, (grade.Finding("x", True, 0, 1, "", ""),)),
        ScenarioResult("hover", setups[1].name, True, (grade.Finding("x", False, 2, 1, "", ""),)),
    )
    run = FlightSimRun("made up", "v1.17.0", "Harmonic", setups, (), results, ())
    path = stills.matrix(run, tmp_path / "matrix.png")
    assert path.stat().st_size > 10_000


def test_my_firmware_gets_its_own_matrix(tmp_path, targets):
    from dataclasses import replace

    setups = tuple(targets.combinations())
    hover = ScenarioResult("hover", setups[0].name, True, (grade.Finding("x", True, 0, 1, "", ""),))
    run = FlightSimRun("made up", "v1.17.0", "Harmonic", setups, (), (), ())
    paths = stills.draw_all(tmp_path, replace(run, mine=(hover,)), tmp_path / "exports")
    assert [p.name for p in paths] == ["matrix.png", "matrix-mine.png"]
    assert stills.draw_all(tmp_path, run, tmp_path / "exports")[1:] == []  # none until it flies


def test_the_first_steps_settling_comes_from_its_result():
    found = ScenarioResult("steps", "base", True, (
        grade.Finding("roll to 15 degrees: settling", True, 0.25, 0.5, "s", ""),
        grade.Finding("roll to 15 degrees: overshoot", True, 0.03, 0.2, "", ""),
    ))  # fmt: skip
    assert stills.settle_of(found) == 0.25
