"""The pack's own insides: the links between its cell groups, its end tabs, its welds, its own
leads and plug, the balance lead and the wrap. Their resistance adds to the drone's side of the
main path (the connection list's 3.8 mOhm), and their weight is the pack's overhead.

The links are nickel-plated copper strip, not nickel (decided 2026-10-20). A series link
carries each cell's share of the current: at the 90 A cap that's 45 A a cell. In the usual
0.15 x 8 mm nickel strip that's 37 A per square millimeter and about 0.6 mOhm a link, so the
pack runs hot; in 0.3 x 10 mm copper it's 15 A per square millimeter and about 0.06 mOhm,
with the cells as heat sinks.

Each link's current crosses one cell pitch (a cell's diameter) to the next group, split over
the group's parallel cells. Each cell has a weld at both ends, in series with it. The end
strips gather the end groups' cells to the tabs, and the tabs carry the whole current to the
leads, soldered on. All of it is worked out, not measured: the welds' resistance especially is
a guess, and it's on the unproven list.
"""

from dataclasses import dataclass

COPPER_OHM_M = 1.72e-8  # ohm meters, annealed copper at 20 C
COPPER_KG_M3 = 8960.0


@dataclass(frozen=True)
class Insides:
    links: float  # ohms, all the series links
    ends: float  # ohms, the end strips and tabs
    welds: float  # ohms
    solder: float  # ohms, the tabs to the leads
    leads: float  # ohms, the pack's own two leads
    copper_kg: float
    leads_kg: float
    other_kg: float  # the balance lead, the pack's plug half and the wrap
    current_density: float  # A/mm^2 in a link strip at `cap_a`

    @property
    def ohms(self) -> float:
        return self.links + self.ends + self.welds + self.solder + self.leads

    @property
    def kg(self) -> float:
        return self.copper_kg + self.leads_kg + self.other_kg


def strip_ohms(length_m: float, width_m: float, thickness_m: float) -> float:
    return COPPER_OHM_M * length_m / (width_m * thickness_m)


def insides(
    series: int,
    parallel: int,
    cell_diameter_m: float,
    strip_width_m: float,
    strip_thickness_m: float,
    tab_length_m: float,
    weld_ohms: float,
    solder_ohms: float,
    lead_ohm_per_m: float,
    lead_kg_per_m: float,
    lead_length_m: float,
    other_kg: float,
    cap_a: float,
) -> Insides:
    """The pack's insides, worked out from its layout and its strip."""
    pitch = cell_diameter_m
    # one strip per parallel cell in each link, each carrying its cell's share across a pitch
    per_strip = strip_ohms(pitch, strip_width_m, strip_thickness_m)
    links = (series - 1) * per_strip / parallel
    # the end strips gather each end group the same way, then a tab carries the whole current
    ends = 2 * (per_strip / parallel + strip_ohms(tab_length_m, strip_width_m, strip_thickness_m))
    # two welds per cell, in series with it; a group's cells sit in parallel
    welds = series * 2 * weld_ohms / parallel
    solder = 2 * solder_ohms
    leads = 2 * lead_length_m * lead_ohm_per_m
    # each strip spans two cells' ends (one from each group) across the pack's width
    strip_area = strip_width_m * strip_thickness_m
    strips = (series - 1) * parallel + 2 * parallel  # the links' strips and the end strips
    copper = (strips * 2 * pitch + 2 * tab_length_m) * strip_area * COPPER_KG_M3
    density = cap_a / parallel / (strip_area * 1e6)
    return Insides(links, ends, welds, solder, leads, copper,
                   2 * lead_length_m * lead_kg_per_m, other_kg, density)  # fmt: skip
