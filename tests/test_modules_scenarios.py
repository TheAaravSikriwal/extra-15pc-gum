"""Step 6's scenarios without Gazebo: which combinations fly them, and their graders on made-up
flights."""

from types import SimpleNamespace as NS

import numpy as np

from pcs14.flight import report
from pcs14.flight.scenarios import modules as m
from pcs14.flight.scenarios import scenarios


def setup(name, modules):
    return NS(name=name, modules=modules, min_top_speed=None, hold_position_in_wind=None)


def test_each_new_scenario_flies_where_it_means_something():
    found = scenarios()
    for name in ("hung flight controller", "drop from 10 m", "chute rule"):
        assert name in found
        assert name not in report.SCENARIOS  # not in step 4's matrix
    assert report.applies("hung flight controller", setup("P", ("P",)))
    assert not report.applies("hung flight controller", setup("base", ()))
    assert report.applies("drop from 10 m", setup("max", ("V", "P", "C")))
    assert not report.applies("drop from 10 m", setup("P", ("P",)))  # the heaviest only
    assert report.applies("chute rule", setup("V", ("V",)))
    assert report.applies("halow range", setup("V", ("V",)))
    assert not report.applies("halow range", setup("P", ("P",)))  # no HaLow without V
    assert report.applies("camera", setup("V", ("V",)))
    assert not report.applies("camera", setup("C", ("C",)))
    assert scenarios()["camera"].camera and not scenarios()["hover"].camera
    assert not report.applies("chute rule", setup("mission", ("V", "P")))


def falling(fired=1.0, from_m=40.0, fall_s=1.5, descent=4.6, end_s=20.0, dt=0.02):
    """A made-up drop: still at `from_m`, free fall from `fired` for `fall_s`, then the canopy's
    steady `descent` to the ground."""
    t = np.arange(0.0, end_s, dt)
    z = np.full_like(t, from_m)
    for k, s in enumerate(t):
        if s < fired:
            continue
        if s < fired + fall_s:
            z[k] = from_m - 0.5 * 9.81 * (s - fired) ** 2
        else:
            drop = 0.5 * 9.81 * fall_s**2
            z[k] = max(from_m - drop - descent * (s - fired - fall_s), 0.07)
    return [(float(a), float(b), 0.0) for a, b in zip(t, z, strict=True)]


def test_a_drop_from_high_enough_settles_under_the_canopy():
    found = m.settled_under_canopy(falling(), fired=1.0)
    assert found.passed
    assert 10.0 < found.value < 13.0  # about the 11 m of the free fall


def test_a_drop_from_too_low_hits_the_ground_first():
    found = m.settled_under_canopy(falling(from_m=10.0), fired=1.0)
    assert not found.passed


def test_the_hung_flight_controller_grade_reads_the_monitors_own_log():
    notes = {
        "hung at": 100.0,
        "monitor": ["trigger tumble rate at 50.000 since 49.700",  # a shadow one, long before
                    "cut flight controller silent at 100.260", "chute released at 101.010",
                    "trigger free fall at 100.560 since 100.260"],
        "truth": falling(fired=101.01, end_s=130.0),
    }  # fmt: skip
    log = NS(when=lambda name: 101.03 if name == "chute fired" else None)
    c = NS(notes=notes, model={"chute": {"ejection_s": 0.2}})
    found = {f.check: f for f in m.grade_hung(log, None, c)}
    assert found["monitor cut"].passed and abs(found["monitor cut"].value - 0.26) < 1e-9
    assert found["chute order"].passed
    assert found["settled under the canopy"].passed
    # the monitor's own free-fall trigger, in shadow mode, saw the fall the cut started
    assert found["monitor's own trigger"].passed
    assert abs(found["monitor's own trigger"].value - 0.56) < 1e-9


def test_the_hang_waits_for_gazebos_first_pose():
    import asyncio

    class Truth:
        def __init__(self):
            self.calls = 0

        def now(self):
            self.calls += 1
            return (-1.0, 0.0, 0.0) if self.calls < 4 else (41.2, 40.0, 0.0)

    assert asyncio.run(m.first_pose(Truth(), timeout_s=1.0)) == 41.2


def test_the_link_fades_where_the_model_says():
    from pcs14.modules.halow import Link

    model = Link()
    edge = m.half_lost_m(m.HALOW_HEIGHT_M)
    assert edge > model.reach_m(0, m.HALOW_HEIGHT_M, margin_db=0.0)  # just past the rated edge
    seconds, d = [], 0.0
    import random

    rng = random.Random(3)
    for t in range(600):  # out at 15 m/s, 40 datagrams a second
        loss = model.packet_loss(max(d, 1.0), m.HALOW_HEIGHT_M)
        got = sum(rng.random() >= loss for _ in range(40))
        seconds.append((t, d, 40, got))
        d += 15.0
    found = {f.check: f for f in m.grade_link(seconds)}
    assert found["link fades where the model says"].passed
    assert abs(found["link fades where the model says"].value - edge) / edge < 0.03


def test_the_camera_grade_wants_frames_at_the_rate_asked_for(tmp_path):
    times = [10.0 + 0.1 * k for k in range(120)]
    found = {f.check: f for f in m.grade_frames(times, every=3)}
    assert found["camera frames"].passed and found["camera frames"].value == 120
    assert abs(found["camera rate"].value - 10.0) < 0.01
    assert not m.grade_frames(times[:10], every=3)[0].passed  # too few to be a recording


def test_the_scenery_is_static_models_along_the_path():
    sdf = m.scenery_sdf("shed", (30.0, 2.0, 1.5), size=(4.0, 3.0, 3.0), color=(0.5, 0.45, 0.4))
    assert "<static>true</static>" in sdf and "<box>" in sdf and "shed" in sdf


def test_a_monitor_that_never_cut_fails():
    c = NS(notes={"hung at": 100.0, "monitor": []}, model={})
    found = m.grade_hung(NS(when=lambda name: None), None, c)
    assert [f.check for f in found] == ["monitor cut"] and not found[0].passed
