"""The mass budget: everything a setup carries, line by line."""

from collections import defaultdict
from dataclasses import dataclass

from pcs14.design import MODULES, Build, SetupTargets, Targets
from pcs14.units import G0


@dataclass(frozen=True)
class MassLine:
    name: str
    mass: float  # kg
    group: str  # base, V, P, C, payload or margin


@dataclass(frozen=True)
class MassBudget:
    setup: SetupTargets
    lines: tuple[MassLine, ...]

    @property
    def total(self) -> float:
        return sum(line.mass for line in self.lines)

    @property
    def weight(self) -> float:
        """In newtons."""
        return self.total * G0

    def by_group(self) -> dict[str, float]:
        groups: dict[str, float] = defaultdict(float)
        for line in self.lines:
            groups[line.group] += line.mass
        return dict(groups)


def mass_budget(build: Build, setup: SetupTargets, growth_margin: float = 0.0) -> MassBudget:
    lines = [
        MassLine(f"Frame: {build.frame.maker} {build.frame.model}", build.frame.mass, "base"),
        MassLine(
            f"4 motors: {build.motor.maker} {build.motor.model}", 4 * build.motor.mass, "base"
        ),
        MassLine(f"4 props: {build.prop.maker} {build.prop.model}", 4 * build.prop.mass, "base"),
        MassLine(f"ESC: {build.esc.maker} {build.esc.model}", build.esc.mass, "base"),
        MassLine(f"Pack: {build.pack.label}", build.pack.mass, "base"),
        *(MassLine(c.model, c.mass, "base") for c in build.base),
    ]
    for module in MODULES:
        if module in setup.modules:
            lines += [MassLine(c.model, c.mass, module) for c in build.modules.get(module, ())]
    if setup.payload > 0:
        lines.append(MassLine("Payload in the claws", setup.payload, "payload"))
    if growth_margin > 0:
        lines.append(MassLine("Growth margin", growth_margin, "margin"))
    return MassBudget(setup=setup, lines=tuple(lines))


def design_masses(build: Build, targets: Targets) -> dict[str, MassBudget]:
    """The mass budget for all eight combinations, with the growth margin on the sizing case."""
    return {
        setup.name: mass_budget(
            build,
            setup,
            growth_margin=targets.growth_margin if setup.name == targets.sizing_case else 0.0,
        )
        for setup in targets.combinations()
    }
