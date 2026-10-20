# Flight sim (step 4)

*Started 2026-10-19 with the flight sim talk. Like everything else here, it will change once real numbers show up.*

## What this step has to produce

From the [roadmap](../roadmap.md) and layer 4 of the [simulation spec](2026-10-13-phase-1-simulation.md#layer-4-gazebo--px4-sim): PX4 flying a Gazebo model of this exact drone in all eight module combinations, through the same scenarios every time. A generator turns `build.yaml`, the sizing output, the CAD's mass properties and the drag numbers into a Gazebo model and PX4 settings for each combination, modeled on PX4's stock x500. The scenarios: hover and sudden stick inputs, a top-speed run, 10 m/s wind, hover and cruise endurance, lost link and low battery, a parachute drop, a payload grab, and failure injection (a dead motor, a failed sensor, a sagging battery). Gazebo doesn't model electricity, so the rotor speeds get turned into current afterwards and run through the sizing model's battery model. Every scenario's IMU data is replayed through the safety monitor's trigger logic to count false triggers. Results come out as pass/fail reports, Rerun recordings and clips.

**Done when:** the baseline passes every scenario in all eight module combinations on PX4.

## Settled in the flight sim talk

**The versions (2026-10-19): PX4 v1.17.0 and Gazebo Harmonic, pinned.** v1.17.0 has been PX4's stable release since May 2026; v1.18 was at its first release candidate when this was decided. Harmonic is PX4's default simulator and a long-term Gazebo release, and Ubuntu 24.04 supports it. Both get pinned to exact tags in `scripts/setup-ubuntu.sh`, so both machines match. **Why:** the most-tested pair, so the bugs I hit are more likely mine than the tools'. **Cost:** v1.18's changes wait. Moving to it once it's stable is its own small decision, with the scenarios rerun.
