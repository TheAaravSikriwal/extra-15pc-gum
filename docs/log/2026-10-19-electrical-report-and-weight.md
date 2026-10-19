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

## Deciding the weight

The first fix was the cheap one. The two branch fuses sat in inline holders, a 7.1 g guess, and soldering the same MINI fuses straight into their wires under heat shrink saves about 5 g. A blown one takes a soldering iron, but these only blow on a fault. I'd first estimated 5.8 g and then realized a sleeve over a whole fuse weighs more like half a gram, not the 0.03 g of a wire joint. That left Mission at 20.98 minutes: 1.2 seconds short.

Then the screws. The old 45 g wiring guess had quietly included them, so once the wiring was weighed properly they weren't counted anywhere. The CAD knows where every screw hole is, so the drone now has a hardware list in `design/cad.yaml`: 26 lines, from the eight M3 screws through the landing legs to the three 4-40s in the parachute's base, each weighed from its standard size. What they weigh depends almost entirely on the material:

| Fasteners | What Mission gains |
|---|---|
| All steel | 52 g |
| Steel where it carries load, nylon elsewhere | 30 g |
| Titanium where it carries load, nylon elsewhere | 19 g |

Even the light choice would have cost Mission about 14 seconds, far more than any trim. So the real lever was the cells. In step 1 I picked the P42A because it was the only way to keep Max under 2500 g. Max has since become report-only, and it's over anyway. Molicel's P45B is the same 21700 size with the same 45 A rating, so the 90 A cap, the pack in the CAD and every electrical number stay where they are. It costs 42 g and buys about 1.7 minutes.

With the P45B and the hardware in (steel where it carries load, nylon elsewhere, 37 g in all):

| Setup | Weight | Pessimistic hover | Target |
|---|---|---|---|
| Mission | 2414 g | 22.25 min | 21 min |
| Max | 2623 g | 19.77 min | 17 min, and under 2500 g (report-only) |

Every required setup passes again. One caveat I found while comparing cells: the catalog rates the P45B's capacity to 2.5 V but the P42A's, measured by HKJ, to 2.8 V. On equal terms the P45B's lead is about 2% smaller, which still leaves Mission well clear. The heavier drone hovers on more current, so the XT60's burst got a little worse: 94 K over the air at the end, against 88.

## The release servo

The parachute's release servo got 4.79 to 4.88 V through its Schottky diode, and 4.54 V on its backup feed, against the 4.9 V it needs (a stand-in servo's 4.8 V rating plus the margin). I couldn't find the Harrier's real servo: Fruity Chutes only calls it a "patent pending servo release". So the fix had to work on the stand-in's numbers.

The diodes are now an ideal-diode OR: TI's LM66200, which passes whichever of its two inputs is higher through a MOSFET instead of a diode junction, on Adafruit's half-gram breakout. On TI's worst-case on-resistance (60 mOhm, hot), a stalled servo loses 27 mV instead of about 0.4 V. The servo now sees 5.16 to 5.20 V, and 4.92 V on the backup. That's two of the eight findings gone, and 0.3 g lighter than the diodes. I still want the real servo's range, so asking Fruity Chutes is on my list.

## Next

The last two findings: the Pi's 5 V ceiling and the XT60 in the burst.
