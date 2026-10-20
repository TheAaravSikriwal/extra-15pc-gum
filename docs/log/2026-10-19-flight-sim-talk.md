# 2026-10-19: Planning the flight sim

*PC, Windows side. Step 4a and 4b: the talk and the plan.*

Step 4 is where the drone flies for the first time, in a simulator: PX4, the open-source flight stack, flying a Gazebo model of this exact drone in all eight module combinations, through the same scenarios every time. Most of what that means was settled back in October's simulation spec. The talk settled the rest.

The versions are PX4 v1.17.0 and Gazebo Harmonic, pinned. v1.17 is PX4's current stable release (v1.18 is at its first release candidate), and Harmonic is the simulator PX4 tests against most. When the bugs show up I'd like them to be mine.

The interesting question was air. Gazebo's multicopter model gives the spinning props a little drag and leaves the body alone, so out of the box the top-speed run is limited only by how far PX4 tilts, and a 10 m/s wind barely registers. Gazebo's own wind system pushes each part in proportion to its mass, which isn't how drag works. So the model gets a small plugin of our own, about a hundred lines of C++: drag from the same drag area the sizing model uses, against Gazebo's wind, plus the parachute, which opens after an ejection delay. When the wind tunnel side track has real drag tables, they replace that one number.

The battery got the same treatment. Gazebo doesn't simulate electricity and PX4 doesn't have my 90 A cap, so each motor tops out where the sizing model's full throttle lands: the pack at its 20% reserve, held to the cap. That's the same worst case the sizing model judges the drone on, so the two can't disagree. Flight time comes from the logged rotor speeds afterwards, through the same battery model.

Then a table of what passing means: holding a hover within half a meter, settling a sudden stick input within half a second, 80 km/h for Mission, holding within a meter in 10 m/s of wind, flight times within 10% of the sizing model's, failsafes that land, a parachute that only fires after the motors stop, and not one false trigger from the safety monitor. One honest catch: the chute's drag comes from Fruity Chutes' own rating, so the sim can't check the descent rate, only the order of events and how much height it loses.

Partway through I decided to stop asking about every choice. From the runner on, the routine calls are mine, written down with their reasons, and only the drastic ones get asked. So:

- the scenarios fly through MAVSDK, PX4's Python SDK, headless and in lockstep
- the safety monitor's free-fall and tumble triggers get a Python reference version now, which step 5's Teensy firmware has to match
- PX4 stays unmodified, running its stock x500 airframe with our parameters
- it all runs in WSL2 on the PC

The plan is 12 test-first tasks ([plan](../plans/2026-10-19-flight-sim.md)). The first eight (the targets, the motor model fit, the drag math, the generator, the power afterwards, the triggers, the grading and the report) need only Windows. The last four need Ubuntu in WSL2 on the PC, which isn't installed yet.

## Next

Building tasks 1 to 8, while Ubuntu gets installed.
