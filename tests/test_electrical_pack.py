"""The pack's insides, worked by hand: copper links, end tabs, welds, its own leads."""

import pytest

from pcs14.electrical import pack


def real_ish():
    # 6S2P of 21.6 mm cells, 0.3 x 10 mm copper strip, 25 mm tabs, 0.1 mOhm welds,
    # 0.05 mOhm solder joints, 80 mm of 12 AWG for each lead
    return pack.insides(6, 2, 0.0216, 0.010, 0.0003, 0.025, 1e-4, 5e-5, 5.64e-3, 38.9e-3,
                        0.080, 0.0195, cap_a=90.0)  # fmt: skip


def test_a_strip_by_hand():
    # 1.72e-8 x 0.0216 / (0.01 x 0.0003) = 0.1238 mOhm
    assert pack.strip_ohms(0.0216, 0.010, 0.0003) == pytest.approx(0.1238e-3, rel=1e-3)


def test_the_insides_add_up():
    found = real_ish()
    per_strip = 0.1238e-3
    assert found.links == pytest.approx(5 * per_strip / 2, rel=1e-3)
    assert found.welds == pytest.approx(6 * 2 * 1e-4 / 2)  # 0.6 mOhm
    assert found.leads == pytest.approx(2 * 0.080 * 5.64e-3)  # 0.9 mOhm
    # the end strips (half a strip each, like a link) and the 25 mm tabs carrying it all
    tab = 1.72e-8 * 0.025 / (0.010 * 0.0003)
    assert found.ends == pytest.approx(2 * (per_strip / 2 + tab), rel=1e-3)
    assert found.ohms == pytest.approx(2.32e-3, rel=0.01)  # 2.3 mOhm in all
    # 14 strips spanning two cells each, and the tabs, in copper; the leads; the rest
    copper = (14 * 2 * 0.0216 + 2 * 0.025) * 0.010 * 0.0003 * 8960
    assert found.copper_kg == pytest.approx(copper, rel=1e-6)
    assert found.kg == pytest.approx(0.0433, abs=0.0005)  # 43 g, against the old 60 g guess


def test_copper_keeps_a_link_cool_where_nickel_wouldnt():
    # 45 A a cell through 0.3 x 10 mm is 15 A/mm^2; 0.15 x 8 mm nickel would be 37.5
    assert real_ish().current_density == pytest.approx(15.0)
    nickel_like = pack.insides(6, 2, 0.0216, 0.008, 0.00015, 0.025, 1e-4, 5e-5, 5.64e-3,
                               38.9e-3, 0.080, 0.0195, cap_a=90.0)  # fmt: skip
    assert nickel_like.current_density == pytest.approx(37.5)
