"""The KiCad schematic: every board a block with its pins, joined by net labels, and KiCad's own
electrical rules check run on it."""

from pathlib import Path

import pytest

from pcs14.electrical import kicad, tools

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def project():
    from pcs14.catalog import load_catalog
    from pcs14.design import load_build
    from pcs14.electrical.model import load_connection_list

    catalog = load_catalog(ROOT / "design" / "catalog")
    build = load_build(ROOT / "design" / "build.yaml", catalog)
    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    return kicad.Schematic.make(design, catalog, build)


def balanced(text):
    depth = 0
    quoted = False
    for i, ch in enumerate(text):
        if ch == '"' and text[i - 1] != "\\":
            quoted = not quoted
        elif not quoted and ch == "(":
            depth += 1
        elif not quoted and ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def test_the_file_is_well_formed_and_the_same_every_time(project):
    text = project.text()
    assert text.startswith("(kicad_sch") and balanced(text)
    assert project.text() == text  # IDs come from names, so nothing moves between runs


def test_every_board_is_placed_once(project):
    text = project.text()
    for name in project.design.boards:
        assert text.count(f'(property "Board" "{name}"') == 1, name


def test_every_shared_net_labels_every_pin_on_it(project):
    text = project.text()
    for net, refs in project.nets().items():
        assert text.count(f'(label "{net}" ') == len(refs), net


def test_unused_pins_get_no_connect_flags(project):
    flagged = project.text().count("(no_connect ")
    assert flagged == len(project.unused_pins()) > 0


def test_one_supply_drives_from_one_pin(project):
    # the ARK FPV's 5 V comes out on five plugs; only one of them is the power output
    types = project.pin_types("fc")
    fives = [types[p] for p in ("RC.5V", "CAN.5V", "GPS.5V", "TELEM.5V", "SPI.5V")]
    assert fives.count("power_out") == 1


@pytest.mark.kicad
@pytest.mark.skipif(tools.find("kicad-cli") is None, reason="KiCad isn't installed")
def test_kicads_rules_check_comes_back_clean(project, tmp_path):
    folder = project.write(tmp_path)
    violations = kicad.erc(folder / "electrical.kicad_sch")
    assert violations == []
