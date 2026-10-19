# 2026-10-19: The electrical report, and what the wiring really weighs

*PC, Windows side. Step 3c's last task and the numbers half of step 3d.*

## One command for all of it

`pcs14 electrical` now does the whole electrical layer in about 26 seconds: the rules in all eight module combinations, the currents in four flight cases each, 438 checks, the six switch sims in ngspice, heat through the burst, twelve harness diagrams, the KiCad schematic with KiCad's own rules check, three stills and a Rerun recording. It all lands in [the electrical report](../reports/electrical/README.md), with `electrical.json` next to it for the project site later. `--quick` skips the outside tools when I just want the checks.

The report leads with the verdict, which is a fail, and that's the honest answer: 430 checks pass and 8 don't. They're the same open findings as before (the parachute's release servo voltage, the Pi's 5 V ceiling, the XT60 in the burst), now in one table with what each rests on.

The hero still is the safety monitor taking over an ESC line mid-frame:

![The safety monitor takes over](../reports/electrical/stills/takeover-portrait.png)

Making it found a modeling bug. In the sim, the flight controller let go of its line whenever any reply was due, including replies to the Teensy's frames, so the flight controller's frame at 200 µs was cut to a stub. A real flight controller lets go only after its own frames. The fix changed no results (by then the switch had isolated it), but I'd have posted a picture of something the hardware doesn't do.

## The wiring, weighed

Until now the wiring was a 45 g guess. The connection list knows every wire's gauge and every route's length, so now it gets weighed:

| | Wire | Weight |
|---|---|---|
| Base | 6.49 m | 59.7 g |
| V | 0.71 m | 2.3 g |
| P | 0.73 m | 3.1 g |
| C | 0.51 m | 2.7 g |

Base's 59.7 g is 52.0 g of copper and insulation, 4.1 g of plugs (the battery XT60's half, and the wire's half of every JST plug), 3.4 g of heat shrink on 114 soldered ends, and half a gram of sleeving on the battery leads. The grams per meter, the heat shrink and the sleeving are estimates, and they say so in the catalog. The old 45 g also covered a battery strap and screws. The straps come with the frame, but the screws and standoffs for the board stacks aren't weighed anywhere now, so that goes on the open list.

The main path, from the pack's terminals through the leads and the XT60 to the ESC and back, measures 3.8 mΩ against the 3 mΩ I'd guessed. Working that out turned up a second bug: the sizing model's "pack voltage" is already after the wiring, and the electrical solve then took the leads' drop off again. Now each case starts at the pack's own terminals.

## A CAD bug the new parts brought in

Rerunning the CAD stopped dead: the fused body for the wind tunnel wasn't watertight. It came down to C's module socket and the two fuse holders, which I'd placed flush against the frame's back edge. Each touched the frame along exactly one line. Fused, that edge belongs to four faces instead of two, and the skin isn't closed anymore. That's also a lousy way to mount something. The socket now sits 6 mm onto the bottom plate, and the fuse holders, too tall for the 7 mm gap between the plates, sit on top of the second plate behind the stack's standoff. Nothing tested the real body for the wind tunnel or that the real layout passes every check, so now two tests do.

## The targets, rechecked

With the wiring and the printed parts' new weights in (the rail lost 1.6 g to its pockets, P's holder gained 2.0 g for its lip):

| Setup | Before | After | Pessimistic hover | Target |
|---|---|---|---|---|
| Mission | 2320 g | 2340 g | 21.19 to 20.92 min | 21 min |
| Max | 2526 g | 2549 g | 18.49 min | under 2500 g |

Mission is now marginal: five seconds short of 21 minutes on the pessimistic model, with the 200 g growth margin still on top. Max was already over its limit and is 49 g over now. Each gram costs Mission about 0.8 s of pessimistic hover, so it needs about 6 g back to reach 21 minutes.

## Next

The open findings and the weight are decisions, not code, so they're the rest of step 3d: what to trim or accept on weight, the release servo's voltage, the Pi's ceiling, and the XT60 in the burst.
