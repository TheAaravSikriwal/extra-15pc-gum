"""The mass budget, checked against sums worked out by hand from the made-up test parts.

Base: frame 300 + 4 motors 280 + 4 props 56 + ESC 25 + pack (12 cells x 70 + 60) 900
      + flight controller 12, receiver 3, lidar 5, safety monitor 20, Remote ID 25, wiring 45
      = 1671 g
V: 20 + 30 + 60 + 15 + 60 = 185 g     P: 120 + 40 = 160 g     C: 150 g, plus a 250 g payload
"""

import pytest

from pcs14.sizing.mass import design_masses, mass_budget


def test_base(build, setups):
    assert mass_budget(build, setups["base"]).total == pytest.approx(1.671)


def test_mission_without_and_with_the_growth_margin(build, setups):
    assert mass_budget(build, setups["mission"]).total == pytest.approx(2.016)
    assert mass_budget(build, setups["mission"], growth_margin=0.2).total == pytest.approx(2.216)


def test_max_carries_the_payload(build, setups):
    assert mass_budget(build, setups["max"]).total == pytest.approx(2.416)


def test_claws_alone_carry_the_payload_too(build, setups):
    assert mass_budget(build, setups["C"]).total == pytest.approx(2.071)


def test_groups_add_up(build, setups):
    groups = mass_budget(build, setups["max"], growth_margin=0.2).by_group()
    assert groups == pytest.approx(
        {"base": 1.671, "V": 0.185, "P": 0.160, "C": 0.150, "payload": 0.250, "margin": 0.200}
    )


def test_lines_name_what_they_are(build, setups):
    names = [line.name for line in mass_budget(build, setups["base"]).lines]
    assert "4 motors: Testco M2810 900KV" in names
    assert "Pack: 6S2P Testco C21700-45" in names


def test_only_the_sizing_case_carries_the_growth_margin(build, targets):
    budgets = design_masses(build, targets)
    assert len(budgets) == 8
    assert budgets["mission"].total == pytest.approx(2.216)
    assert budgets["max"].total == pytest.approx(2.416)
    assert budgets["V"].total == pytest.approx(1.856)
