# The virtual drone (CAD)

*Generated on 2026-10-18 by pcs14 0.1.0, the CAD layer in `src/pcs14/cad/`. Every module combination gets built, its pack slid to where it balances best, and checked: collisions, prop clearance, the parachute's cone, the module rail, balance, and the makers' placement rules.*

![The drone, three-quarter view](views/three-quarter.png)

## The verdict

**Fail.** 1 of 2 combinations misses a check: mission (balance, compass distance).

Built from Testco M2810 / P10x4.5 / 6S2P.

## Every module combination

| Setup | Modules | Weight | Pack at | Center of gravity (x, y, z) | Busiest motor | Verdict |
|---|---|---|---|---|---|---|
| base | none | 1776 g | -11 mm | 0.1, 0.0, -2.5 mm | +0.1% | pass |
| mission | V+P | 2091 g | -14 mm | 9.2, 0.2, 12.0 mm | +6.2% | fail |

The pack's position is along x from the motors' center; it slides to balance each combination. The busiest motor column says how much harder the busiest motor works than the average in a hover (the limit is +5%).

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | the busiest motor works 0.1% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk | pass |

</details>

<details>
<summary>mission: fail</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | the busiest motor works 6.2% harder | fail |
| compass distance | the compass is 28 mm from the BEC | fail |
| collisions | nothing overlaps | pass |

</details>

## Mass properties

Each part's weight spread over its solid, with the pack at its trim. Inertia is about the center of gravity.

| Setup | Weight | Ixx | Iyy | Izz |
|---|---|---|---|---|
| base | 1776 g | 16.0 g m² | 19.0 g m² | 26.0 g m² |
| mission | 2091 g | 16.0 g m² | 19.0 g m² | 26.0 g m² |

## My printed parts

Weighed from their geometry and material, next to what the catalog says for each one's entry (pcs14 cad --update-catalog writes the CAD's numbers in).

| Part | Material | Weight | Its catalog entry |
|---|---|---|---|
| module rail | petg_cf | 13.4 g | 30 g, a guess the CAD replaces (module-mount) |
| leg front left | tpu | 6.6 g | not in the catalog yet (landing-legs) |

Together they weigh 20 g.

## Wires

Rough routes, until the electrical step picks gauges and connectors.

| Wire | Length |
|---|---|
| battery leads | 123 mm |
| receiver | 47 mm |

## What's estimated

- testco-frame: arm_width_mm. traced from a render

## Existing CAD models

Checked for every part before modeling it. They stay in a local cache that never gets committed, and get compared with my parts by size and hole spacing.

| Part | Found | Terms | Compared with mine |
|---|---|---|---|
| testco-fc | official | No license; don't commit | holes line up |
| testco-gps | none |  |  |

## Files

Generated on every run, and not committed (they're build outputs):

- `outputs/cad/drone.step`
- `outputs/cad/drone.glb`

## Views

![Front](views/front.png) ![Side](views/side.png) ![Top](views/top.png) ![Exploded](views/exploded.png)
