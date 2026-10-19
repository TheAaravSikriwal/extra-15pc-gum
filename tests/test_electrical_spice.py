"""Running ngspice and reading what it writes back."""

import math

import pytest

from pcs14.electrical import tools
from pcs14.electrical.spice import run as spice

needs_ngspice = pytest.mark.skipif(tools.find("ngspice") is None, reason="ngspice isn't installed")

RAW = """Title: rc
Date: today
Plotname: Transient Analysis
Flags: real
No. Variables: 3
No. Points: 2
Variables:
\t0\ttime\ttime
\t1\tv(out)\tvoltage
\t2\tv(in)\tvoltage
Values:
 0\t0.000000000000000e+00
\t0.000000000000000e+00
\t0.000000000000000e+00
 1\t1.000000000000000e-06
\t6.321205588285577e-01
\t1.000000000000000e+00
"""


def test_the_ascii_raw_file_reads_back():
    waves = spice.read_raw(RAW)
    assert list(waves) == ["time", "v(out)", "v(in)"]
    assert waves["time"][1] == pytest.approx(1e-6)
    assert waves["v(out)"][1] == pytest.approx(1 - math.exp(-1))


@needs_ngspice
def test_an_rc_circuit_by_hand(tmp_path):
    # a 1 V step into 1 kOhm and 1 nF: one time constant is 1 us, where it's at 63.2%
    netlist = "V1 in 0 PWL(0 0 1p 1)\nR1 in out 1k\nC1 out 0 1n\n"
    waves = spice.run(netlist, ["v(out)"], tmp_path, step=1e-9, stop=5e-6)
    at = spice.value_at(waves, "v(out)", 1e-6)
    assert at == pytest.approx(1 - math.exp(-1), abs=0.005)


@needs_ngspice
def test_a_broken_netlist_says_so(tmp_path):
    with pytest.raises(spice.SpiceError):
        spice.run("R1 a\n", ["v(a)"], tmp_path, step=1e-9, stop=1e-6)
