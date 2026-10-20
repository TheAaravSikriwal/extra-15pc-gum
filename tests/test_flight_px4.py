"""Real flights: PX4 v1.17.0 flying the generated base model in Gazebo Harmonic. These only run
where scripts/setup-ubuntu.sh has set things up (WSL2 Ubuntu on the PC); everywhere else, CI
included, they skip. They need the models generated first: pcs14 flight-sim."""

import asyncio
from pathlib import Path

import pytest

from pcs14.flight import batch, run
from pcs14.flight.scenarios import scenarios

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "outputs" / "flight-sim"
TOOLS = run.toolchain()
MISSING = TOOLS.missing()

pytestmark = [
    pytest.mark.px4,
    pytest.mark.skipif(bool(MISSING), reason="; ".join(MISSING) or "PX4 is here"),
    pytest.mark.skipif(
        not (EXPORTS / "models" / "pcs14_base").exists(), reason="no generated models"
    ),
]


def test_a_smoke_flight_in_the_base_combination(targets, setups):
    """Take off, hover 10 s, land: the runner works end to end."""
    from pcs14.catalog import load_catalog
    from pcs14.design import load_build

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    smoke = scenarios()["smoke"]
    result, outcome = asyncio.run(
        batch.run_one(TOOLS, EXPORTS, setups["base"], smoke, targets, build, instance=7)
    )
    assert outcome.error is None, outcome.error
    assert outcome.log is not None and outcome.log.exists()
    failed = [f"{f.check}: {f.detail}" for f in result.findings if not f.passed]
    assert result.flown and not failed, failed
