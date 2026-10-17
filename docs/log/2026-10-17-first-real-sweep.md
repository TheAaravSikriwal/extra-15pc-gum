# 2026-10-17: The sizing model meets real parts

*PC, Windows side. Same day as the talk, and a lot happened.*

This morning the sizing model was eight answered questions and no code. Tonight it's a Python package with 163 tests, and it has looked at 192 drones built entirely from parts you can actually buy. Here's how it went.

## Building it

The plan had 15 tasks, each written test-first: the parts catalog, the mass budget, the battery, hover and full throttle from the thrust tables, forward flight, a flight stepper that flies the drone down to the 20% reserve, the checks, the sweep, the report, and every flight streaming into Rerun so I can watch it.

Two bugs are worth telling. The first: the model drew a straight line below a thrust table's first row, and on a light drone that overstated hover power by about 65%. Physics says power goes as thrust to the 1.5, so it scales that way now. The second was dumber. The live Rerun viewer wouldn't open, because Python's Scripts folder isn't on the path on Windows. It looks there itself now.

## Is it honest?

Before trusting it with my parts, I made it fly someone else's drone. The honesty check (`pcs14 validate`) takes a published build, gives the model that build's parts and weight, and compares the model's flight time with the measured one.

The battery side is great. Against four cells' published discharge curves, the model's voltage is within 0.02 to 0.06 V per cell. The cruise side isn't. On Oscar Liang's test of the GEPRC MOZ7 V2, the model said 32 minutes and he measured 16. My best guess is the drag the props themselves make in forward flight, which the model leaves out. I didn't tune the model to match one flight. It's written up in [decisions](../decisions.md), and the report now says plainly that cruise numbers run optimistic and hover is the number to trust.

## Real parts

Three research agents went through more than 50 motors with published 6S thrust tables. Most of the work was throwing tables out: rows that go backwards, prop sizes nobody prints, and one T-Motor page that says a motor pulls 408 A at 60% throttle (its own power column says about 24 A). Six motors made the cut, from Emax, Hobbywing, T-Motor and Flash Hobby, along with seven props whose makers publish their weight. I checked the main tables against the makers' pages by eye, row by row.

## The first real sweep

Every motor, prop, cell and pack layout that fit together: 192 builds. Every target passed easily except one, and that one shaped the whole result.

The rule is that the four motors flat out on a full pack have to stay inside the battery's continuous current rating. A 6S2P pack of Molicel P42A cells is rated for 90 A. All 96 of the 6S2P builds pull more than that flat out, 105 A at the very least, even after the voltage sags under the load. So the winners all have a third cell in parallel (135 A), and that costs about 400 g.

Under today's rules, the pick is:

| | |
|---|---|
| Motors | Flash Hobby Mars M2814 730KV |
| Props | HQ LR10x5x3 |
| Pack | 6S3P Molicel P42A, 12 Ah, 1257 g |
| Frame | iFlight Nazgul XL10 |
| Weight with Mission's loadout | 2678 g (with the 200 g margin) |
| Hover | 32.9 min (28.1 pessimistic), target 21 |
| Thrust-to-weight at 20% charge | 2.35 (2.12 pessimistic), target 2.0 |
| Flat out on a full pack | 118 A, rating 135 A |

It wins because it's the lowest-current motor in the catalog, and that rule rewards low current. Two catches. Its thrust table starts at 50% throttle and this drone hovers below that, so the hover power is a physics estimate that reads a few percent low (I checked against a table that goes lower). And the extra cells push Max to 2878 g, over its 2500 g limit.

Switch the current rule off and 111 builds pass, including lighter 6S2P ones. So the real question isn't which motor. It's whether full throttle has to fit the battery's rating, or whether my firmware caps the current instead. A cap costs some punch on a fresh pack, but at the end of a flight, where the thrust check happens, the sagging pack already keeps the draw near the rating. That's the next thing to decide.

The full report, with every check, the mass budget and charts, is in [docs/reports/sizing](../reports/sizing/README.md).

## Next

Settle the current-limit question, then lock the parts and the growth margin and close step 1. Modeling the props' drag in forward flight is how the cruise numbers get believable.
