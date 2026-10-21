# The build package (step 8)

*Written 2026-10-21. I asked for the open items to keep moving without stopping to ask, so I made these calls myself and wrote down why. The ones that are mine to make stay open below.*

## What it has to do

From the [roadmap](../roadmap.md#step-8-the-build-package): everything someone needs to build the drone from the docs alone. Seven parts:

| # | Part | Where it comes from |
|---|---|---|
| 1 | The parts list: part numbers, supplier links, prices, a fallback for each | the catalog and the build, the CAD report's hardware and printed parts, the electrical report's wires |
| 2 | The assembly guide, with renders from the CAD | the CAD, in build order |
| 3 | The wiring guide | the connection list (`design/electrical.yaml`) and the electrical report |
| 4 | The firmware: build steps and configuration | the firmware's CMake, PX4's targets, the generated airframe files |
| 5 | Test plans: bench checks with the props off, then first flights, tethered first | the safety rules, the failsafes, the unproven list |
| 6 | The legal checklist | decisions.md's "Government rules are settings, not caps", the FAA's and FCC's own pages |
| 7 | The unproven list, each item with the first thing to measure | decisions.md's table and each report's list |

**Done when:** someone could build it from the docs alone.

## Calls

- **It's generated, like every report.** `pcs14 package` writes `docs/build/`: a README that walks the build in order, the parts list as Markdown and CSV, the assembly and wiring guides, the firmware guide, the test plans, the legal checklist and the unproven list. It reads the catalog and the reports' own data files, never the CAD or the sims directly, so the package says exactly what the reports say, and a part swapped in the catalog shows up everywhere at once.
- **Every bought part gets a buy link, a price, the date it was checked, and a fallback.** The link goes in the catalog's `link` (the product page, not a datasheet), and the fallback in a new `fallback` field: the maker, the model, a link and why it's second choice. A fallback that changes the design (a different board, a different size) says what has to change. A part with no fallback says why. Prices are what the shop showed on the day, in US dollars, and they'll drift.
- **Researched links get checked, not guessed.** Each one is opened before it goes in. Where a shop page couldn't be confirmed, the maker's own page goes in instead, and the price stays empty rather than made up.
- **The parts list counts what each combination needs.** Base, then V, P and C on their own, and a total for each of the eight combinations. Wire is listed by type and gauge with the length the connection list adds up to plus 30% for mistakes and trimming. Screws and nuts come from the CAD's hardware list, rolled up by size. Printed parts list their material and grams, and come out of `pcs14 cad` as 3MF files.
- **The assembly guide is a fixed build order with renders from the CAD.** Each step names its parts and the hardware that holds them, and shows the drone built up to that step with the new parts in the project's spearmint. The order is mine: frame, stack, power, the Base boards, the safety monitor, the legs and tray, then each module.
- **The wiring guide goes harness by harness,** each wire's two ends, gauge, type and cut length, the harness drawing, and the checks to make with a meter before anything gets power: continuity end to end, no short between the pack's leads, and every rail at its voltage.
- **The firmware guide puts PX4 first.** The ARK FPV runs PX4 out of the box, so the first flights are PX4's, tuned from the flight sim's parameters, and my firmware flies only after PX4 has. My firmware's image builds in CI, but its register-level drivers wait for a bench board, and the safety monitor's Teensy image needs PJRC's Teensy core, which is a download I haven't made. The guide says so.
- **Test plans have pass criteria,** written the way the sims' graders are. Bench checks first with the props off (a smoke stopper on first power, then each rail, the receiver, the motors' order and direction, the safety monitor's cut through both boards, the failsafes), then tethered hovers, then free flights in the `us-recreational` profile. Each unproven item's first measurement sits in the plan where it fits.
- **The legal checklist points at the source for each rule** (FAA and FCC pages) and says which limits profile setting it maps to. The rules stay settings, not caps.
- **The unproven list carries its measurements in the reports themselves.** Each report's items become (what, the first thing to measure) pairs, so the site's unproven page and the package show the same thing, written once.

## Not settled yet

- PJRC's Teensy core, for the safety monitor's image: a download, mine to approve.
- The camera's mapping position or a tilt servo (step 7): a weight call for me. The package builds V as designed, tipped 30 degrees.
- P in every combination, and optical flow in Base: still my calls from step 4. The package builds what's designed.
- Fruity Chutes' release servo and canopy timing: still to ask them. The Harrier's release servo stays the stand-in.
