"""How numbers show up in the report.

Rounding always goes toward failing: a value that has to stay high rounds down, and one that
has to stay low rounds up. So 1.998:1 against a 2:1 target shows as 1.99, never as a
misleading 2.00 next to a fail.
"""

import math

DECIMALS = {"min": 1, ":1": 2, "A": 1, "km/h": 0, "x": 2, "g": 0, "": 0}


def fmt_value(value: float, unit: str, higher_is_better: bool) -> str:
    places = DECIMALS.get(unit, 2)
    scale = 10**places
    if higher_is_better:
        rounded = math.floor(value * scale + 1e-9) / scale
    else:
        rounded = math.ceil(value * scale - 1e-9) / scale
    return f"{rounded:.{places}f}"


def fmt_limit(value: float, unit: str) -> str:
    return f"{value:.{DECIMALS.get(unit, 2)}f}"


def with_unit(number: str, unit: str) -> str:
    if unit == ":1":
        return f"{number}:1"
    if unit == "x":
        return f"{number}x"
    return f"{number} {unit}".strip()
