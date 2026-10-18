# 2026-10-18: Wiring it up, on paper first

*PC, Windows side. Step 3a, the electrical talk.*

Step 2 gave the drone a body. Step 3 gives it a nervous system: every wire, pin and connector, with the numbers to show nothing melts. Before any code, the usual talk, one question at a time. It was going to be seven questions, and power split into two once the currents came in, so it ended up eight. Everything is in the [electrical spec](../specs/2026-10-18-electrical.md).

## One list, everything else generated

The CAD worked because every part lived in code and everything else came out of it. Same idea here. One file, `design/electrical.yaml`, lists every board, pin, connector and wire, and which route in the CAD each wire follows. The harness diagrams (WireViz), the pin map tables, a KiCad schematic, every check, and the 3D wires colored by current all get generated from it. A schematic made of blocks and net labels looks plainer than a hand-drawn one. I can live with that.

## A new flight controller

The CAD started with a Holybro Kakute H7. Laying out the connections showed it was out of room: it has four full serial ports and PX4 already uses all of them, so the safety monitor's link would have had to take over the debug console. It also has no CAN at all. The ARK FPV has five full serial ports, a CAN port, bidirectional DShot on every motor output, and a proper debug plug for when my own firmware goes on. It costs $195 against $85, and it's on backorder, which matters less when nothing gets bought by default.

## How the modules talk

DroneCAN, the standard bus for drone add-ons. Each module announces itself on the bus, so the flight controller knows what's fitted. The chute's release servo and the claws' servos sit on small DroneCAN servo nodes, and the GPS gets swapped for a DroneCAN one (the current one is end of life anyway). The Pi talks to the flight controller over one serial line, the normal PX4 way. The module connector is an XT30 for 5 V plus one JST-GH for the signals.

## Power, with real numbers

I pulled the battery currents out of the sizing model before picking anything:

| Setup | Hovering | Cruising at 10 m/s | Flat out |
|---|---|---|---|
| Base | 9 to 11 A | 7 to 8 A | 90 A (capped from 127 A) |
| Mission | 14 to 17 A | 11 to 14 A | 90 A |
| Max | 16 to 20 A | 13 to 16 A | 90 A |

The main lead carries under 20 A almost the whole flight, and 90 A only in short bursts, which is what my firmware's current cap allows. No common connector is rated for 90 A continuous, and none needs to be. So the frame's XT60 stays, judged on its real duty: 20 A against its 35 A rating, plus a heat check on the bursts. There's no main fuse. A fuse in the 90 A line is one more way to drop a healthy drone, and the 7 g of weight margin couldn't pay for it anyway. Instead the pack gets a fuse link on each cell, the way e-bike packs are built, so a crushed lead in a crash blows the links instead of starting a fire. Whether there's room between "survives 45 A per cell for 10 seconds" and "melts on a dead short" is something the checks have to prove.

The 5 V scare from step 2 mostly went away. The Pi's supply is rated for exactly the 5 A the Pi 5 asks for, which looked tight. But the Pi asks for 5 A so it can pass 1.6 A on to USB devices. By itself it measured under 2 A flat out, and nothing in V uses USB. The whole module rail comes to about 2.5 A in Max. Only stalled claw servos push it past 5 A, and the claws are still a placeholder.

## The half second

This was the best find of the talk. The old plan for the safety monitor was a switch that disconnects the four ESC signal lines when it wants the motors stopped, on the assumption that an ESC stops when its signal disappears. I went and read AM32's source (the ESC's firmware). It does stop, after half a second. Until then it holds the last throttle it was given. The comment in the code says "half second timeout when armed".

Half a second at hover throttle after hitting the kill switch is not a kill switch. So the switch became a multiplexer. Normally the flight controller drives the ESC, and that's what happens whenever the Teensy is off, unpowered or dead. To cut, the Teensy takes the lines and sends DShot stop frames itself, and the motors stop within a millisecond. Its code can only ever send stop. Every line the Teensy listens to goes through a buffer that floats when it loses power, so a dead Teensy can't drag the flight controller's signals down with it. It also fires the parachute over two wires of its own, never through the bus, and it takes power from two supplies, so it can still fire the chute if the flight controller goes dark.

The circuit sim (ngspice) now has a clear job: show DShot passing cleanly through all of that with the Teensy on, off and cutting, and show the handover costs at most one broken frame.

## The check numbers

Every wire, connector and supply at no more than 80% of its continuous rating, the same rule electricians use. A 10 second burst at the 90 A cap for heat. Every part 20 °C under its temperature rating on a 40 °C day. No more than 2% voltage lost between the pack and the ESC. And any part with no published rating gets a conservative guess that the report lists, so nothing passes on a number I made up without saying so.

## What worries me

Weight. The new parts all add some: a DroneCAN GPS is likely heavier than the little Matek one, the servo nodes and the safety monitor's extra chips weigh something, and Max is 7 g under its 2500 g limit. Step 3d puts the real weights back into the sizing model, and something may have to give. Also, ARK doesn't publish how much its 5 V supply can deliver. The flight-critical parts on it draw under half an amp, but that's a number I want before calling the design done.

## Next

Step 3b: research the new parts (the DroneCAN GPS, servo nodes, multiplexers, connectors and fuses) and write the implementation plan.
