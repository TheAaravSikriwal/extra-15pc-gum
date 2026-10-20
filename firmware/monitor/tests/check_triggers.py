"""check_triggers.py <pcs14_monitor_replay>: the safety monitor's triggers in C++ against the
Python reference (src/pcs14/safety/triggers.py) on the same samples, which must agree exactly.

The samples are made up to cross every threshold: a hover, a free fall, a tumble, a slow roll
past the tilt limit, a flicker that clears before it counts, and noise. The reference is
loaded straight from its file, so this needs nothing installed beyond Python itself.

ctest runs this after the monitor's tests."""

import importlib.util
import math
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "triggers", ROOT / "src" / "pcs14" / "safety" / "triggers.py"
)
triggers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triggers)


class Limits:  # design/targets.yaml's
    free_fall_g, free_fall_s = 0.3, 0.3
    tumble_rate_dps, tumble_rate_s = 400, 0.3
    tumble_tilt_deg, tumble_tilt_s = 75, 0.5


def samples(seed=3):
    rng = random.Random(seed)
    out, t, dt = [], 0.0, 1 / 250
    g = triggers.G

    def add(n, accel, gyro, tilt):
        nonlocal t
        for _ in range(n):
            noise = [rng.gauss(0, 0.05) for _ in range(6)]
            a = tuple(accel[k] + noise[k] for k in range(3))
            w = tuple(gyro[k] + 0.01 * noise[3 + k] for k in range(3))
            out.append(triggers.ImuSample(round(t, 6), a, w, tilt(t)))
            t += dt

    level = lambda _t: 0.0  # noqa: E731
    add(500, (0, 0, g), (0, 0, 0), level)  # hovering
    add(40, (0, 0, 0.1 * g), (0, 0, 0), level)  # a free fall too short to count
    add(250, (0, 0, g), (0, 0, 0), level)
    add(150, (0, 0, 0.05 * g), (0, 0, 0), level)  # a real one
    add(250, (0, 0, g), (0, 0, 0), level)
    add(200, (0, 0, g), (8.0, 0, 0), level)  # tumbling at 460 degrees a second
    start = t
    add(900, (0, 0, g), (0.6, 0, 0), lambda tt: min(1.6, 0.6 * (tt - start)))  # rolling over
    add(250, (0, 0, g), (0, 0, 0), level)
    return out


def main(binary: str) -> int:
    data = samples()
    expected = triggers.triggers(data, Limits)
    text = "\n".join(
        f"{s.t:.6f} {s.accel[0]:.6f} {s.accel[1]:.6f} {s.accel[2]:.6f} "
        f"{s.gyro[0]:.6f} {s.gyro[1]:.6f} {s.gyro[2]:.6f} {s.tilt:.6f}"
        for s in data
    )
    run = subprocess.run([binary], input=text, capture_output=True, text=True, check=True)
    got = []
    for line in run.stdout.splitlines():
        words = line.split()
        got.append((" ".join(words[:-2]), float(words[-2]), float(words[-1])))
    want = [(x.kind, x.at, x.since) for x in expected]
    same = len(got) == len(want) and all(
        a[0] == b[0] and math.isclose(a[1], b[1], abs_tol=1e-6)
        and math.isclose(a[2], b[2], abs_tol=1e-6)
        for a, b in zip(got, want, strict=True)
    )  # fmt: skip
    if not same:
        print("the reference:", want)
        print("the monitor:  ", got)
        return 1
    print(f"the monitor's triggers match the reference: {[w[0] for w in want]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
