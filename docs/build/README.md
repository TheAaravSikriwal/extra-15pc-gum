# The build package

*Generated 2026-10-21 by `pcs14 package`. Everything someone needs to build Extra 15pc Gum from these docs: what to buy and print, how to wire it and put it together, the firmware, the tests before and after the first flight, and the rules. It reads the catalog, the build, the connection list and the reports, so it says exactly what they say.*

Nothing here has been built yet. The drone exists in simulation, every part a real one, and these docs are the plan for the first real one. What the sims can't prove is in the test plans, with the first thing to measure for each.

## What it costs

| Combination | Bought parts, wire and plugs | Not priced yet |
|---|---|---|
| base | $876.78 | 0 |
| V | $1,321.67 | 1 |
| P | $1,569.26 | 0 |
| C | $1,034.93 | 1 |
| mission | $2,014.15 | 1 |
| V+C | $1,479.81 | 2 |
| P+C | $1,727.40 | 1 |
| max | $2,172.29 | 2 |

Plus what's bought once (the transmitter, a charger, supplies and tools): $361.99 priced so far, 5 not yet.

## In order

1. **Read the [test plans](tests.md)** first, the safety checks especially. They say what has to pass before the props go on.
2. **Buy** from the [parts list](parts.md) ([as a spreadsheet](parts.csv)). Each part has a second choice, and what changes if it's used.
3. **Print** the printed parts: `pcs14 cad` writes their 3MF files to `outputs/cad/print/`. TPU where a part should flex (the legs, the GPS mast's foot and cradle, the Remote ID mount), carbon-filled PETG for the rest.
4. **Wire** each harness from the [wiring guide](wiring.md), with its meter checks.
5. **Assemble** in the order of the [assembly guide](assembly.md).
6. **Flash** PX4 first, from the [firmware guide](firmware.md), with this combination's parameters.
7. **Test** on the bench, props off, then fly tethered, from the [test plans](tests.md).
8. **Before the first outdoor flight,** the [legal checklist](legal.md).

## Still open

- P in every combination, and an optical flow sensor in Base (step 4's findings): the package builds what's designed today.
- The HaLow card: Heltec's SPI card has no working Pi 5 report yet, and its swap waits for me. The ground side's HaLow radio waits with it.
- V's camera: its bracket tips it 30 degrees for the live video, too oblique for mapping. A mapping position or a tilt servo is a weight call for me.
- The claws (C): a placeholder until the claw conversation.
- Fruity Chutes' release servo (Hitec's HS-55 stands in) and the canopy's opening time.
- The safety monitor's Teensy image: it needs PJRC's Teensy core, a download for me to approve.
