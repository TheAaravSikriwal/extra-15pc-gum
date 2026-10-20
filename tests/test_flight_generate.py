"""The generator: each combination's Gazebo model, the world and PX4's parameters."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from pcs14.flight.drag import Chute
from pcs14.flight.generate import FlightModel, RotorSpot, world_sdf
from pcs14.flight.motor import MotorModel

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).parent / "fixtures" / "flight_sim" / "model.sdf"


def made_up_model(**changes):
    from dataclasses import replace

    motor = MotorModel(1.5e-5, 0.016, 930.0, 620.0, 0.0125, 0.025, 8.06428e-05, 1e-06,
                       ("time_constant_up",), "x500")  # fmt: skip
    corners = ((1, -1, "ccw"), (-1, 1, "ccw"), (1, 1, "cw"), (-1, -1, "cw"))
    rotors = tuple(
        RotorSpot(n, (sx * 0.15, sy * 0.15, 0.04), d, 0.0168, 0.127)
        for n, (sx, sy, d) in enumerate(corners)
    )
    model = FlightModel(
        name="pcs14_test",
        setup="test",
        modules=frozenset({"P"}),
        mass=2.0,
        center=(0.001, 0.0, 0.01),
        inertia=((0.02, 0.0, 0.0), (0.0, 0.03, 0.0), (0.0, 0.0, 0.045)),
        rotors=rotors,
        body_center=(0.0, 0.0, 0.017),
        body_size=(0.2, 0.04, 0.035),
        feet=((0.1, 0.1, -0.08), (-0.1, 0.1, -0.08), (0.1, -0.1, -0.08), (-0.1, -0.1, -0.08)),
        motor=motor,
        drag_area=0.015,
        chute=Chute(1.9, 0.2, 1.0),
        mesh="meshes/body.stl",
    )
    return replace(model, **changes)


def test_the_model_matches_a_known_good_copy():
    assert made_up_model().sdf() == GOLDEN.read_text(encoding="utf-8")


def test_it_rests_on_its_feet():
    model = made_up_model()
    assert model.lift_off == pytest.approx(0.08 + 0.008)  # the feet's spheres touch the ground


def test_the_model_is_valid_sdf_with_everything_px4_needs():
    root = ET.fromstring(made_up_model().sdf())
    assert root.tag == "sdf" and root.get("version") == "1.9"
    sensors = {s.get("type") for s in root.iter("sensor")}
    assert sensors == {"air_pressure", "magnetometer", "imu", "navsat"}
    motors = [p for p in root.iter("plugin") if "multicopter-motor" in p.get("filename")]
    assert [m.findtext("motorNumber") for m in motors] == ["0", "1", "2", "3"]
    drag = next(p for p in root.iter("plugin") if p.get("filename") == "pcs14-drag")
    assert drag.find("chute") is not None


def test_no_chute_and_no_payload_unless_the_module_is_there():
    root = ET.fromstring(made_up_model(chute=None).sdf())
    drag = next(p for p in root.iter("plugin") if p.get("filename") == "pcs14-drag")
    assert drag.find("chute") is None
    assert not [p for p in root.iter("plugin") if "detachable" in p.get("filename")]
    with_payload = ET.fromstring(made_up_model(payload=0.25).sdf())
    assert [p for p in with_payload.iter("plugin") if "detachable" in p.get("filename")]


def test_the_world_has_wind_and_px4s_origin():
    root = ET.fromstring(world_sdf(wind=(-10.0, 0.0, 0.0)))
    assert root.find("world/wind/linear_velocity").text == "-10 0 0"
    assert root.find("world/spherical_coordinates/latitude_deg").text == "47.397971057728974"


# --- the real drone ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def real():
    from pcs14.cad.assembly import Drone
    from pcs14.cad.settings import load_settings
    from pcs14.catalog import load_catalog
    from pcs14.design import load_build, load_targets
    from pcs14.flight.generate import flight_model

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    targets = load_targets(ROOT / "design" / "targets.yaml")
    drone = Drone(build, load_settings(ROOT / "design" / "cad.yaml"))
    setups = {s.name: s for s in targets.combinations()}
    models = {
        name: flight_model(drone, build, targets, setups[name]) for name in ("mission", "max")
    }
    return build, targets, drone, setups, models


def test_its_weight_is_the_cads(real):
    from pcs14.cad.checks import trim
    from pcs14.cad.mass import mass_properties

    _, _, drone, setups, models = real
    cad = mass_properties(trim(drone, setups["mission"].modules).pieces)
    assert models["mission"].total_mass == pytest.approx(cad.mass, rel=1e-6)


def test_its_inertia_is_physically_possible(real):
    _, _, _, _, models = real
    for model in models.values():
        i = np.array(model.inertia)
        assert np.allclose(i, i.T)
        principal = np.linalg.eigvalsh(i)
        assert (principal > 0).all()
        a, b, c = sorted(principal)
        assert c <= a + b + 1e-12  # the triangle rule every real body obeys


def test_the_rotors_sit_on_the_motor_mounts_in_px4s_order(real):
    _, _, drone, _, models = real
    rotors = models["mission"].rotors
    mounts = drone.frame.motor_mounts
    for rotor in rotors:
        x, y, _ = rotor.position
        assert min(math.dist((x, y), (m[0], m[1])) for m in mounts) < 1e-9
    corners = [(r.position[0] > 0, r.position[1] > 0, r.direction) for r in rotors]
    assert corners == [(True, False, "ccw"), (False, True, "ccw"), (True, True, "cw"),
                       (False, False, "cw")]  # fmt: skip


def test_the_chute_only_comes_with_p_and_the_payload_with_c(real):
    _, _, _, _, models = real
    assert models["mission"].chute is not None and models["mission"].payload == 0
    assert models["max"].chute is not None and models["max"].payload == pytest.approx(0.25)


def test_the_drag_area_is_the_sizing_models(real):
    from pcs14.sizing.drag import drag_area

    build, _, _, setups, models = real
    assert models["mission"].drag_area == pytest.approx(drag_area(build, setups["mission"]))


def test_px4s_parameters_match_the_model(real):
    build, targets, _, _, models = real
    model = models["mission"]
    p = model.params
    cx, cy, cz = model.center
    front_right = model.rotors[0]
    assert p["CA_ROTOR0_PX"] == pytest.approx(front_right.position[0] - cx, abs=1e-4)
    assert p["CA_ROTOR0_PY"] == pytest.approx(-(front_right.position[1] - cy), abs=1e-4)
    assert p["CA_ROTOR0_PY"] > 0  # front right is +y in PX4's frame
    assert p["CA_ROTOR0_KM"] > 0 > p["CA_ROTOR2_KM"]  # counterclockwise positive
    assert p["SIM_GZ_EC_MAX1"] == round(model.motor.max_rot_velocity)
    assert p["MPC_TILTMAX_AIR"] == pytest.approx(45.0)
    assert p["MPC_XY_VEL_MAX"] > targets.setups["mission"].min_top_speed
    assert 0.1 <= p["MPC_THR_HOVER"] <= 0.8
    assert p["BAT1_N_CELLS"] == build.pack.series


def test_px4_fires_the_chute_by_termination_only_with_p(real):
    _, _, _, _, models = real
    p = models["mission"].params
    assert p["SIM_GZ_SV_FUNC1"] == 400  # PX4's parachute output, on the first servo
    assert p["CBRK_FLIGHTTERM"] == 0  # flight termination allowed, which fires it
    root = ET.fromstring(models["mission"].sdf())
    chute = next(p for p in root.iter("plugin") if p.get("filename") == "pcs14-drag").find("chute")
    # the output sits at -45 degrees in flight and goes to +45 on termination
    assert float(chute.findtext("fire_above")) == pytest.approx(math.radians(22.5))
    from pcs14.flight.generate import px4_params

    build, targets, _, _, _ = real
    without = px4_params(made_up_model(chute=None), build, targets)
    assert "SIM_GZ_SV_FUNC1" not in without and "CBRK_FLIGHTTERM" not in without


def test_it_writes_every_models_folder_and_the_world(real, tmp_path):
    import json

    from pcs14.flight.generate import write_models

    build, targets, drone, setups, _ = real
    models = write_models(tmp_path, drone, build, targets, [setups["max"]], meshes=False)
    home = tmp_path / "models" / models[0].name
    for name in ("model.config", "model.sdf", "params.json"):
        assert (home / name).is_file(), name
    ET.parse(home / "model.sdf")
    assert json.loads((home / "params.json").read_text())["CA_ROTOR_COUNT"] == 4
    assert (tmp_path / "models" / "pcs14_payload" / "model.sdf").is_file()  # Max carries one
    ET.parse(tmp_path / "worlds" / "pcs14.sdf")
