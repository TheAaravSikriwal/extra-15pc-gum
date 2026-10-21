# The wiring (electrical)

*Generated on 2026-10-19 by pcs14 0.1.0, the electrical layer in `src/pcs14/electrical/`. One connection list, `design/electrical.yaml`, holds every board, connector and wire. Everything here comes from it, checked in every module combination and flight case.*

![The safety monitor takes over an ESC line, in ngspice](stills/takeover-portrait.png)

## The verdict

**Fail.** 1 of 4 checks miss.

| Check | Where | In | What it found | Rests on |
|---|---|---|---|---|
| load voltage | load.J.5V | P, worst | 4.620 to 4.700 V across the cases, inside 4.75 to 5.15 V | t-load: draws[J.5V] |

Built from Testco M2810 / P10x4.5 / 6S2P. The connection list has 3 boards, 7 wires and 1 safety path.
It passes every rule in both module combinations: every pin exists, one driver per line, no supplies tied together, no pin over its voltage, every board powered and grounded, two CAN terminators, and every safety path there.

## The flight cases

Each combination gets four. Hover and cruise use the pessimistic power model at the reserve, where the pack is lowest and the current highest. The burst is full throttle at the reserve, which the firmware caps. The worst case is a hover with every 5 V part at its worst: servos stalled, the Pi flat out. These are the battery's currents.

| Setup | Hover | Cruise | Burst | The pack in the burst |
|---|---|---|---|---|
| base | 12.0 A | 14.5 A | 40.0 A | 19.8 V |
| P | 12.6 A | 15.1 A | 40.0 A | 19.7 V |

## Every check

Every rating gets 80% at most, steady. Heat is checked in 40 °C air, steady and through the 10 s burst, against each insulation's or connector's limit less 20 °C. A check that rests on an estimate says so in the verdict and in "What it rests on".

| Check | How many | Passed | Tightest |
|---|---|---|---|
| wire current | 2 | 2 | pack.XT60.+ to reg.J.VIN, P, burst: 2.10 A in 18 AWG silicone, which carries 27.5 A to its 200 C limit |
| load voltage | 1 | 0 | load.J.5V, P, worst: 4.620 to 4.700 V across the cases, inside 4.75 to 5.15 V |
| connector burst | 1 | 1 | pack.XT60.+, P, burst: 40 A for 10 s ends 51 K over the air |

Every check, one by one:

<details>
<summary>wire current: 2 checked</summary>

| What | In | Found | Verdict |
|---|---|---|---|
| pack.XT60.+ to reg.J.VIN | P, burst | 2.10 A in 18 AWG silicone, which carries 27.5 A to its 200 C limit | pass |
| reg.J.VOUT to load.J.5V | base, hover | 0.90 A in 18 AWG silicone, which carries 27.5 A to its 200 C limit | pass |

</details>

<details>
<summary>load voltage: 1 checked, 1 miss</summary>

| What | In | Found | Verdict |
|---|---|---|---|
| load.J.5V | P, worst | 4.620 to 4.700 V across the cases, inside 4.75 to 5.15 V | fail |

</details>

<details>
<summary>connector burst: 1 checked</summary>

| What | In | Found | Verdict |
|---|---|---|---|
| pack.XT60.+ | P, burst | 40 A for 10 s ends 51 K over the air | pass |

</details>

## Heat through the burst

Each starts from its hottest steady temperature and takes the burst's current for its whole length. A connector my firmware protects (`heat_limited`) stops at its limit, where the firmware eases the current cap.

| Part | Before | At the end | Limit |
|---|---|---|---|
| pack.XT60.+ | 61 °C | 91 °C | 100 °C |
| pack.XT60.+ to reg.J.VIN | 48 °C | 60 °C | 180 °C |

![Temperatures through the burst](stills/burst-heat.png)

## How hard every wire works

Each route at its hardest working wire, as a share of that wire's heating limit (its rise over the air, against the rise to its limit), in its hardest combination.

| Route | Hover | Cruise | Burst | Worst case |
|---|---|---|---|---|
| main | 13% |  | 33% |  |

One more route never passes 1%.

![How hard every wire works, flat out](stills/wire-work.png)

## The safety monitor's switch

One DShot channel in ngspice: the flight controller's pin, the wires at their real lengths, the analog switch, the Teensy's listening buffer and the ESC, which answers with its RPM reply. Every case is decoded from the simulated voltages by the project's own DShot decoder.

| Case | What happens | The ESC got | The flight controller read | Meant to | Result |
|---|---|---|---|---|---|
| Teensy off | The flight controller drives the ESC through the switch | 1046, 1046 | 1232, 1232 | pass | as meant |
| No buffers | A dead Teensy straight on the line. Meant to fail | broken, broken | broken | fail | as meant |

<details>
<summary>What each run measured</summary>

- **Teensy off:** frames decode: the ESC decoded [1046]
- **No buffers:** frames decode: the ESC decoded [None, None]

</details>

## Where the power goes

From the pack down, with every module in (max): typical while hovering, and the worst case.

- pack.XT60.+
  - reg.5V, a switching 5 V supply rated 3 A

## Pin maps

### mcu (t-mcu)

| Pin | What it is | Called | Goes to |
|---|---|---|---|

## Harness diagrams

### power

![The power harness](harnesses/power.svg)

## The schematic

Every board a block with its pins, joined by net labels, in [`kicad/electrical.kicad_sch`](kicad/electrical.kicad_sch). It opens in KiCad 8 or later. KiCad's electrical rules check finds 0 violations.

An SVG of it, too big to commit, is at `outputs/electrical/electrical.svg` after a run.

## What it rests on

Every number comes from a maker's datasheet or a measurement, except these estimates.

- **t-load** (load): draws[J.5V]. From a similar board.
- **t-servo** (servo): its whole electrical block. A stand-in until the real one is picked.

## What it can't prove

- A dead short in the battery leads. *First to measure:* Look.
- The switch sims use generic models built from datasheet numbers, with no ground bounce or noise from the motor current. A clean sim isn't a scope on the real thing.

## Files

Generated on every run, next to this report:

- `harnesses/power.svg`
- `kicad/electrical.kicad_sch`
- `stills/burst-heat.png`
- `stills/takeover-portrait.png`
- `stills/wire-work.png`

And outside it, not committed (they're build outputs):

- `outputs/electrical/electrical.svg`
