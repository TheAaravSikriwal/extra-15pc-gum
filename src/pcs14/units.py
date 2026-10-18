"""Unit conversions.

Everything inside pcs14 is in meters, kilograms, seconds, newtons, watts, volts, amps, ohms
and coulombs. Grams, millimeters, inches, mAh, km/h and milliohms only exist in the parts files
and the reports, and these functions are the only place they get converted.
"""

G0 = 9.80665  # standard gravity, m/s^2


def g_to_kg(grams: float) -> float:
    return grams / 1000


def kg_to_g(kilograms: float) -> float:
    return kilograms * 1000


def mm_to_m(millimeters: float) -> float:
    return millimeters / 1000


def m_to_mm(meters: float) -> float:
    return meters * 1000


def inch_to_m(inches: float) -> float:
    return inches * 0.0254


def m_to_inch(meters: float) -> float:
    return meters / 0.0254


def mah_to_coulomb(mah: float) -> float:
    return mah * 3.6


def coulomb_to_mah(coulombs: float) -> float:
    return coulombs / 3.6


def kmh_to_ms(kmh: float) -> float:
    return kmh / 3.6


def ms_to_kmh(ms: float) -> float:
    return ms * 3.6


def gram_force_to_newton(grams_force: float) -> float:
    """Thrust tables give thrust in grams; this is the force those grams weigh."""
    return grams_force / 1000 * G0


def newton_to_gram_force(newtons: float) -> float:
    return newtons / G0 * 1000


def mohm_to_ohm(milliohms: float) -> float:
    return milliohms / 1000


def cm2_to_m2(square_cm: float) -> float:
    return square_cm / 1e4


def seconds_to_minutes(seconds: float) -> float:
    return seconds / 60


def minutes_to_seconds(minutes: float) -> float:
    return minutes * 60


def ohm_to_mohm(ohms: float) -> float:
    return ohms * 1000
