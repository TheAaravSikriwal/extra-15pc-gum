# 2026-10-18: The electrical build, part 1

*PC, Windows side. Step 3c, tasks 1 to 3 and the first half of task 8.*

The plan got its OK this afternoon and the build started straight away, test-first like the CAD.

## Tools

Three programs went onto the PC: Graphviz (WireViz draws harness diagrams with it), ngspice 47 for the circuit sims, and KiCad 10 for the schematic's rules check. None of them is a Python package, so `pcs14` looks for each one in a set order (an environment variable, then the PATH, then where its Windows installer puts it), and `pcs14 electrical --tools` says what it found. CI installs Graphviz and ngspice for every run, and KiCad gets its own job because it's a big install. The first CI run caught a test of mine that only worked on Windows.

## Every part's pins

The catalog learned a new block. Each part now lists its connectors and pins, the current it draws and through which pin, any supply it provides, and its ratings if it's a connector, fuse or diode. Every number has a source, and the guesses are named, so the report can list every check that rests on one. Wire got its own small catalog type, a table of gauges.

Filling it in turned up a few things:

| Finding | What it means |
|---|---|
| The HaLow card's Pi HAT feeds it through a linear regulator from 5 V | The drone pays 5 V times its current, not 3.3 V: 1.06 W instead of the 0.69 W the sizing model had |
| Emax weighs its motor without its leads | 270 mm of 18 AWG on each phase. Cut to length, the four motors' leads come to roughly 28 g, and I don't think the 45 g wiring guess counted them. Step 3d will tell |
| Nobody sells a usable ICM-42688-P breakout | One is out of stock, one discontinued, one $88 with no specs. The safety monitor's IMU is now ST's LSM6DSOX on Adafruit's board, which is in stock, documented and 1.7 g |
| Nobody publishes the mass of an inline fuse holder | They're guessed at 3 g each, which makes the two branch fuses 7.1 g. A wire-leaded fuse soldered inline would drop the holders if the weight matters |
| The motor cut switch's board has two 1 kOhm resistors nobody documents | If they pull its control pins up instead of down, the board would hand the motors to the Teensy by default. The build package will say to check them with a meter, and the design adds its own pull-downs |

## Fitting the new parts into the drone

The new parts went into the build and the CAD together, because the CAD's tests run on the real build. Two changes to how the CAD works came with them. A part can now sit in more than one module (the servo node is in P and in C), and one part can sit at several spots (three module sockets, two fuse holders), sharing its weight between them.

The module plugs needed room. V's plug can only go under the Pi, so the whole Pi stack rose 6 mm (the V housing had 16 mm spare). P's plug goes under the parachute tube, so the tube now stands on a printed lip 6 mm above the rail. V's and P's sockets sink into pockets in the rail. C's socket and the two fuse holders hang off the frame's back edge, clear of the claws and the rear props. The safety monitor's switch board, buffers and 3.3 V regulator stack on top of the Teensy, under the top plate.

The first check run found the switch board and buffers overlapping the Teensy by a few cubic millimeters: its top is at 22.14 mm, not the 22.1 I'd used. With that fixed, all eight module combinations pass every check.

## The weight

| | Before | Now | Target |
|---|---|---|---|
| Mission | 2293 g | 2320 g | |
| Mission's hover, pessimistic | 21.6 min | 21.2 min | 21 |
| Max | 2493 g | 2526 g | 2500 g (reported, doesn't have to pass) |

Mission still passes, by 1%. The wiring is still a 45 g guess, and if the motor leads aren't in it, the real number will be higher. Step 3d replaces the guess with every wire's real gauge and length, and that's where this gets decided. The fuse holders are the obvious first thing to trim.

## Next

Task 4: the connection list itself, `design/electrical.yaml`, and the rules it has to follow.
