"""Shared test setup: the made-up test catalog and build, and the real targets."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog():
    return load_catalog(FIXTURES / "catalog", allow_made_up=True)


@pytest.fixture
def build(catalog):
    return load_build(FIXTURES / "build.yaml", catalog)


@pytest.fixture
def targets():
    return load_targets(ROOT / "design" / "targets.yaml")


@pytest.fixture
def setups(targets):
    return {setup.name: setup for setup in targets.combinations()}
