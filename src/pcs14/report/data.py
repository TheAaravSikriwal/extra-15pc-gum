"""The data file (sizing.json): every result in one place, for the CAD, electrical and Gazebo
steps and for the project site. Timelines are thinned to at most 200 points each."""

import math

from pcs14 import __version__, units
from pcs14.catalog import Part
from pcs14.sizing import checks as checks_module
from pcs14.sizing import rotor
from pcs14.sizing.battery import Pack
from pcs14.sizing.checks import DesignResult
from pcs14.sizing.drag import AIR_DENSITY
from pcs14.sizing.flight import Flight

MAX_POINTS = 200


def r(value: float | None, places: int = 6) -> float | None:
    return None if value is None else round(value, places)


def part_info(part: Part) -> dict:
    return {
        "id": part.id,
        "maker": part.maker,
        "model": part.model,
        "mass_g": r(part.mass_g),
        "price_usd": part.price_usd,
        "link": str(part.link) if part.link else None,
        "source": part.source.kind.value,
        "source_url": str(part.source.url) if part.source.url else None,
    }


def flight_series(flight: Flight) -> dict:
    samples = list(flight.samples)
    step = max(1, math.ceil(len(samples) / MAX_POINTS))
    thinned = samples[::step]
    if thinned[-1] is not samples[-1]:
        thinned = thinned[:-1] + [samples[-1]]
    return {
        "minutes": r(flight.minutes),
        "ended": flight.ended,
        "speed_ms": r(flight.speed),
        "time_s": [r(s.time, 2) for s in thinned],
        "voltage_v": [r(s.voltage, 4) for s in thinned],
        "charge_mah": [r(s.mah_used, 2) for s in thinned],
        "current_a": [r(s.current, 3) for s in thinned],
        "headroom": [r(s.thrust_headroom, 4) for s in thinned],
    }


def to_data(design: DesignResult, sweep=None, margin=None, made_up=False, generated=None) -> dict:
    build, targets = design.build, design.targets
    pack = Pack(build.pack)
    table = build.thrust_table
    data = {
        "generated": generated,
        "pcs14_version": __version__,
        "made_up": made_up,
        "verdict": design.verdict,
        "sizing_case": targets.sizing_case,
        "growth_margin_g": r(units.kg_to_g(targets.growth_margin)),
        "targets": {
            "reserve_fraction": targets.reserve_fraction,
            "cruise_speed_ms": targets.cruise_speed,
            "min_thrust_to_weight": targets.min_thrust_to_weight,
        },
        "build": {
            "motor": part_info(build.motor),
            "prop": {
                **part_info(build.prop),
                "diameter_in": build.prop.diameter_in,
                "pitch_in": build.prop.pitch_in,
            },
            "esc": part_info(build.esc),
            "frame": part_info(build.frame),
            "pack": {
                "cell": part_info(build.pack.cell),
                "series": build.pack.series,
                "parallel": build.pack.parallel,
                "capacity_mah": r(pack.capacity_mah),
                "resistance_mohm": r(pack.resistance * 1000),
                "mass_g": r(units.kg_to_g(build.pack.mass)),
            },
            "thrust_table": {
                "voltage_v": table.voltage,
                "source": table.source.kind.value,
                "source_url": str(table.source.url) if table.source.url else None,
            },
            "current_cap_a": r(build.current_cap),
            "components": [part_info(c) for c in build.base],
            "modules": {m: [part_info(c) for c in parts] for m, parts in build.modules.items()},
        },
        "model": {
            "induced_factor": rotor.INDUCED_FACTOR,
            "profile_share": rotor.PROFILE_SHARE,
            "profile_growth": rotor.PROFILE_GROWTH,
            "max_tilt_deg": r(math.degrees(rotor.MAX_TILT)),
            "derate": {kind.value: value for kind, value in rotor.DERATE.items()},
            "gust_headroom": checks_module.GUST_HEADROOM,
            "top_speed_soc": checks_module.TOP_SPEED_SOC,
            "air_density": AIR_DENSITY,
        },
        "setups": [
            {
                "name": result.setup.name,
                "modules": sorted(result.setup.modules),
                "required": result.setup.required,
                "verdict": result.verdict,
                "mass_g": r(units.kg_to_g(result.mass.total)),
                "growth_margin_g": r(units.kg_to_g(result.growth_margin)),
                "mass_lines": [
                    {"name": line.name, "grams": r(units.kg_to_g(line.mass)), "group": line.group}
                    for line in result.mass.lines
                ],
                "checks": [
                    {
                        "name": check.name,
                        "unit": check.unit,
                        "nominal": r(check.nominal),
                        "pessimistic": r(check.pessimistic),
                        "limit": r(check.limit),
                        "higher_is_better": check.higher_is_better,
                        "verdict": check.verdict,
                        "margin": r(check.margin),
                        "note": check.note,
                    }
                    for check in result.checks
                ],
                "flights": {key: flight_series(f) for key, f in result.flights.items()},
                "least_power_speed_ms": r(result.least_power_speed),
                "least_power_minutes": r(result.least_power_minutes),
                "top_speed_kmh": {k: r(v, 2) for k, v in result.top_speeds_kmh.items()},
            }
            for result in design.setups
        ],
        "sweep": None,
        "margin_curve": None,
    }
    if sweep is not None:
        data["sweep"] = {
            "ranked": [
                {
                    "rank": rank,
                    "label": c.build.label,
                    "motor": c.build.motor.id,
                    "prop": c.build.prop.id,
                    "cell": c.build.pack.cell.id,
                    "layout": f"{c.build.pack.series}S{c.build.pack.parallel}P",
                    "frame": c.build.frame.id,
                    "verdict": c.verdict,
                    "tightest_margin": r(c.tightest_margin),
                    "sizing_cruise_minutes": r(c.sizing_cruise_minutes),
                    "sizing_mass_g": r(units.kg_to_g(c.result.sizing.mass.total)),
                }
                for rank, c in enumerate(sweep.ranked, start=1)
            ],
            "skipped": [{"label": label, "reason": reason} for label, reason in sweep.skipped],
        }
    if margin is not None:
        data["margin_curve"] = {
            name: [
                {
                    "grams": p.grams,
                    "hover_minutes": r(p.hover_minutes),
                    "cruise_minutes": r(p.cruise_minutes),
                }
                for p in points
            ]
            for name, points in margin.items()
        }
    return data
