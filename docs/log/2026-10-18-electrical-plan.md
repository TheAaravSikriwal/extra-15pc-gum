# 2026-10-18: Shopping for parts I'm not buying

*PC, Windows side. Step 3b, the electrical plan.*

The talk decided how the wiring works. The plan has to name real parts for it, so I sent four research passes out at once (the flight controller and ESC pinouts, the DroneCAN parts, the small logic chips and fuses, and the tools), on top of notes from earlier in the day on connectors, wire and fuses. The whole plan is [here](../plans/2026-10-18-electrical.md): 14 test-first tasks, like the CAD build.

## The good news

ARK publishes its flight controller's 5 V supply rating after all: 2 A, with 1.5 A free once the board itself is fed. That was the talk's last open question, and the flight-critical parts on it draw under half an amp.

There's an off-the-shelf board for the safety monitor's switch. TI's TS3A5018 is four two-way switches with one control pin, and with the control pins pulled low it connects the flight controller side, which is exactly TI's own reference wiring. It comes on a small breakout board that costs a couple of dollars. No custom PCB needed.

## Two of my assumptions were wrong

I'd planned to isolate the Teensy's listening lines with a quad buffer chip, the SN74LVC125A. Its current datasheet doesn't promise anything about what its pins do when it's unpowered, which was the whole point of the buffer. The single-gate version, the SN74LVC1G125, does promise it: under 10 µA of leakage with its supply off. So it's six tiny chips on six adapter boards instead of one.

And the one-channel switch I'd named for the parachute module, a TI SN74LVC1G157, doesn't exist. TI's product page is a 404. Nexperia makes the 74LVC1G157, with the same unpowered-leakage promise, so that's the pick.

## The weight problem got real

The talk swapped the GPS for a DroneCAN one, because the old Matek M10Q is end of life and the modules talk DroneCAN now. The lightest DroneCAN GPS with a compass that's still sold weighs 16 g. The M10Q weighed 8. The servo nodes for the parachute and the claws add 5 g each.

| | Before | After the new parts (rough) |
|---|---|---|
| Mission | 2293 g | about 2309 g, still passing |
| Mission's pessimistic hover (target 21 min) | 21.6 min | about 21.4 min |
| Max (limit 2500 g) | 2493 g | about 2514 g |

A serial GPS from the same maker weighs 8 g, but Max would still land around 2506 g, and its six wires would have pushed the module connector from 8 pins to 12. So I kept the DroneCAN GPS: ARK's, which PX4 documents down to how you switch its terminator on. Max going over 2500 g doesn't fail anything (Max only has to be reported, since Mission is what sizes the drone), but it's the first time since picking the parts that it's over. The wiring is still a 45 g guess in the mass budget, and step 3d replaces that guess with each wire's real gauge and length, so the final number could move either way.

## Small things that would have bitten later

- The flight controller's ESC plug and the ESC's plug have the same eight signals in different orders, on different pitches. Holybro's pin map doesn't say which end is pin 1, so the cable is an educated guess until someone checks one with a meter.
- The ESC's current sensor scale changes with its board revision. My firmware's 90 A cap trusts that sensor, so the build package has to say "check the revision".
- A CAN bus needs a terminator at each end, and the GPS can't be one of the ends because it leaves when V comes off. The bus will end at a fixed terminator in the module mount instead.
- The only public DShot library for the Teensy can't do the inverted DShot the ESC locks onto at power-up, so the safety monitor's stop frames are mine to write in step 5.

## Next

Step 3c, task 1: getting Graphviz, ngspice and KiCad onto the PC and into CI.
