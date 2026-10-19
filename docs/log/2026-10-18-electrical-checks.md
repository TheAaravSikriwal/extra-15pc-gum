# 2026-10-18: The checks find their first problems

*PC, Windows side. Step 3c, tasks 4 to 7.*

The drone's wiring now exists as one file, `design/electrical.yaml`: 33 boards and 128 wires, from the battery's XT60 to the parachute's release servo. Everything after this gets generated from it. Today was about making the computer check it the way I'd want an electrical engineer to.

## Rules first

Before any current gets worked out, the connection list has to make sense on its own. For each of the eight module combinations, the code joins every pin into nets through the wires, the plugs and anything soldered together, then checks:

- every pin and route exists
- each module connects through its connector only
- no line has two drivers
- no two supplies are tied together without diodes
- no pin sees more volts than it takes, with the motor cut switch checked in both positions
- every board is powered and grounded
- every fuse has a rating
- the CAN bus has exactly two terminators

The real list passed on the first try, which made me suspicious. So I broke it on purpose four ways. Three got caught. The fourth, pulling the wire that lets the safety monitor take over the parachute, passed every rule. Electrically nothing was wrong: the pull-down keeps that switch in a safe state. The design had just quietly lost a safety feature. So the safety design's 27 paths are now written into the list as requirements, and losing any of them fails the check.

## Currents

Every net gets solved as a small resistor network. Each wire is a resistor from its gauge and length, each plug contact from its maker's contact resistance. The solve runs from the battery outward through fuses, regulators and diodes, and finishes on the ground net, so parallel grounds split the way they really would. The sizing model supplies the battery current for hovering, cruising and flat out.

The first run gave the battery lead 4441 A. Every net downstream of a fuse started at 0 V, so a regulator worked out its input current as its output power divided by almost nothing. With a no-load start, the battery lead now carries exactly what the sizing model says, all 32 solves take two and a half seconds, and the Pi sees 5.18 V.

It also caught one of my own numbers. In the talk I wrote that Max hovers at about 20 A. That was the nominal power model. The pessimistic model at the reserve, which is what the checks use, says 23 A. The XT60 still sits at two thirds of its rating, and the spec now says 23.

## What the checks found

| Finding | Number | Limit |
|---|---|---|
| The parachute's release servo, through its diode | 4.79 to 4.88 V | 4.9 V (a stand-in servo's 4.8 V, plus the margin) |
| The same servo, with the module supply dead | 4.55 V | 4.9 V |
| The Pi's 5 V | 5.19 V | 5.15 V (a guessed 5.25 V ceiling, less the margin) |
| The XT60 after 10 s at 90 A | 128 °C | 100 °C (120 °C less the margin) |

Every wire runs cool. The 12 AWG battery leads reach 61 °C hovering and 80 °C after the burst, against 180 °C. The motor leads reach 59 °C. The heat model, by the way, ran about 10% optimistic against Remington's published wire table, so it's scaled to match that table within 3%.

## The fuse links that couldn't work

In the talk I picked no main fuse, with a fuse link on each cell to stop a dead short in the battery leads. The fuse check took that apart:

| Cell link | Opens a dead short in | At the 90 A cap |
|---|---|---|
| 18 AWG | 0.95 s | the solder joint passes 163 °C after 6.4 s |
| 16 AWG | 2.4 s | survives |

The leads' insulation reaches 200 °C after 1.1 s of that short, so a link has to open within a second. The ones that do cook during flat-out flight. A main fuse that never trips at 90 A is slower still: Littelfuse's own curve gives 3 to 100 seconds at three times its rating. The root problem is the pack's own resistance, which limits a dead short to about five times the cap. No fuse can tell "five times flat out" from "flat out" quickly without also tripping on flat out. That's probably why drone packs don't fuse their cells.

So the links are out. The battery leads get short runs, sleeving and routing away from crush points, and a dead short in them goes on a new unproven list that the report will carry.

## Next

The rest of the build: the CAD's new wire routes, then DShot and the ngspice runs for the safety monitor's switch, which is the one I most want to see. The open findings above go into step 3d, along with the weight.
