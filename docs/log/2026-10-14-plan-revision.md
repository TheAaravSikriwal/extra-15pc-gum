# 2026-10-14: The plan, revised

*PC, Windows side. Still no code. One more round of planning, and then planning is actually done.*

This morning's review turned into a full rewrite of the plan, and I read it start to finish and confirmed it. The short version: fly the boring drone sooner, and make the safety stuff real from the very first flight.

## What changed

**The safety monitor moved into the base drone.** The little Teensy that can stop the motors without trusting my firmware used to live in the parachute module, which I wasn't going to build until Phase 5. Now it's on the drone from day one. My kill switch reaches the motors through two separate boards, and the Teensy cuts them by blocking the signal wires to the motor controllers instead of switching 100 amps of battery power. If the Teensy itself dies, the drone keeps flying. Its automatic triggers (free fall, tumbling) only log what they would have done until they've proven they don't fire on a healthy drone.

**The targets got honest about batteries.** Li-ion packs sag a lot under load, especially near empty. Near the 20% reserve, a motor at full throttle only makes something like 55–60% of the thrust on its spec sheet. So instead of "4:1 thrust-to-weight" with no conditions attached, every setup now needs 2:1 measured at the reserve, under load. That's about 3.5:1 on paper. I also added hover-time targets (25, 21 and 17 minutes) next to the cruise ones, because the bare drone has no GPS and can't measure a cruise speed until Phase 6. Cruise means 10 m/s for now, and the battery reserve is counted in mAh instead of volts.

**Phase 1 got shorter.** The old plan wanted me to learn CFD, build a wind tunnel pipeline, an optimizer and a render pipeline before I could buy a $30 dev board. Now Phase 1 is the sizing model, a thrust stand, CAD and Gazebo. The wind tunnel and the design hunt still happen, but alongside everything else, and whatever the hunt finds becomes v2. The plain X is the drone I build and fly.

**The thrust stand moved up.** One motor, a few props and the ESC get bought as soon as the sizing model has a shortlist, so real measurements replace the manufacturer's optimistic ones early. Most of those parts end up on the drone anyway.

**PX4 flies it first.** Before my own firmware gets anywhere near the real drone, PX4 flies it. If something's wrong with the hardware, I'll know it isn't my code.

**A real weight budget.** The fully loaded drone comes out somewhere between 2.15 and 2.8 kg, and my cap is 2.5 kg. The sizing model's first job is finding out which.

Smaller ones: a flight controller board with debug pads, the geofence enforced on the drone itself, a firmware watchdog, antennas in the CAD clearance checks, generated meshes kept out of git, and a Part 107 decision before Phase 3.

## A small correction along the way

The review's first suggestion for thrust was 2.5:1 at the reserve. Working it through for the plan, battery sag turned out worse than that suggestion assumed. 2.5:1 at the end of a flight would have meant about 4.4:1 on paper, and heavier motors on every flight for margin I only need at the very end. So it's 2:1.

## Next

Set up the PC's Ubuntu side, then the sizing model discussion. I've also started thinking about ways to stay up on less power without adding wings. More on that once it's more than an idea.
