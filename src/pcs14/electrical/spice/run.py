"""Running ngspice in batch mode and reading its plain-text raw file back."""

import subprocess
from pathlib import Path

import numpy as np

from pcs14.electrical import tools


class SpiceError(Exception):
    """ngspice couldn't run the circuit."""


def read_raw(text: str) -> dict[str, np.ndarray]:
    """ngspice's ASCII raw file: a header, the variables' names, then each point's values."""
    lines = text.splitlines()
    names, points, start = [], 0, None
    for i, line in enumerate(lines):
        if line.startswith("No. Points:"):
            points = int(line.split(":")[1])
        elif line.startswith("Variables:"):
            j = i + 1
            while not lines[j].startswith("Values:"):
                names.append(lines[j].split()[1])
                j += 1
            start = j + 1
            break
    if start is None:
        raise SpiceError("the raw file has no Values section")
    numbers = []
    for line in lines[start:]:
        parts = line.split()
        if parts:
            numbers.append(float(parts[-1]))
    count = len(names)
    data = np.array(numbers[: points * count]).reshape(points, count)
    return {name: data[:, k] for k, name in enumerate(names)}


def run(netlist: str, probes, workdir: Path, step: float, stop: float, title="pcs14", tmax=None):
    """Run a transient analysis and hand back time and the probed vectors."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    circuit = workdir / "circuit.cir"
    raw = workdir / "out.raw"
    if raw.exists():
        raw.unlink()
    limit = f" 0 {tmax:g}" if tmax else ""  # the longest step ngspice may take
    circuit.write_text(
        f"{title}\n{netlist}\n.tran {step:g} {stop:g}{limit}\n"
        ".control\nset filetype=ascii\nrun\n"
        f"write {raw.name} {' '.join(probes)}\nquit\n.endc\n.end\n",
        encoding="utf-8",
    )
    done = subprocess.run(
        [str(tools.require("ngspice")), "-b", circuit.name],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if done.returncode != 0 or not raw.exists():
        tail = "\n".join((done.stdout + done.stderr).splitlines()[-12:])
        raise SpiceError(f"ngspice couldn't run {circuit}:\n{tail}")
    return read_raw(raw.read_text(encoding="utf-8"))


def value_at(waves, name: str, time: float) -> float:
    return float(np.interp(time, waves["time"], waves[name]))
