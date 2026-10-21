# Structure, first pass: beam math (side track)

*Written 2026-10-21. I asked for the open items to keep moving without stopping to ask, so I made these calls myself and wrote down why.*

## What it has to do

From the [roadmap](../roadmap.md#side-tracks): the arms under full thrust, the arms' vibration frequencies against the props' speeds, a rough drop check, the parachute's opening jolt on its mount, and the module mounts' loads. The roadmap planned FreeCAD with CalculiX for it, and neither is installed here (installing them is `sudo`, mine). So the first pass is the textbook version, in Python: each arm a cantilever, each joint its screws and inserts, with the numbers it rests on written down and swept across their ranges.

## Calls

- **An arm is a cantilever,** clamped where it leaves the body plates and carrying its motor and prop at the tip. Its stress and deflection under the motor's full thrust, and its first bending modes, vertical and in the plane of the frame, from the standard formulas (Euler-Bernoulli, with 24% of the arm's own mass added at the tip, Rayleigh's usual share for a cantilever).
- **The laminate's numbers are a range, not a value.** iFlight publishes nothing about the Nazgul's carbon, so the modulus runs 40 to 70 GPa and the strength from 400 MPa, typical of woven carbon plate, and every result is shown across that range. That's what CalculiX would need too.
- **The vibration check is a Campbell diagram:** the arm's modes against the motors' rotation (one per turn, an unbalanced prop) and the blades' passing (three per turn), from idle to full speed, with the hover marked. A mode near the hover's speed is a finding, and the first thing to measure is a gyro log with the props spinning.
- **The chute's mount is checked against the textbook bound,** step 6's 8 to 12 g (up to 254 N in Max), at each joint between the canopy's riser and the frame: the Harrier's three 4-40 screws, the cradle's two rail locks in their heat-set inserts, the rail's four nylon screws. The printed cradle itself needs a real load test, which goes in the test plans.
- **The drop check is energy into the legs,** a rough number for the TPU legs' job, not a crash model.

## Not settled yet

- FreeCAD and CalculiX, for a real FE model of the cradle, the rail and the legs: installs that are mine.
