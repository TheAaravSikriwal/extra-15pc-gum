# The flight sim

*Generated on 2026-10-19 by pcs14 0.1.0, the flight sim in `src/pcs14/flight/`. PX4 v1.17.0 flies a Gazebo Harmonic model of this drone, generated from the build, the sizing model and the CAD, in every module combination.*

## The verdict

**Fail.** 3 of 19 runs flown, and 1 miss: wind in mission.

Built from Testco M2810 / P10x4.5 / 6S2P.

## Every scenario, every combination

| Scenario | base | mission |
|---|---|---|
| hover | pass | pass |
| steps | not yet | not yet |
| top speed |  | not yet |
| wind |  | **fail** |
| endurance | not yet | not yet |
| lost link | not yet | not yet |
| low battery | not yet | not yet |
| parachute drop |  | not yet |
| dead motor | not yet | not yet |
| failed sensor | not yet | not yet |
| sagging pack | not yet | not yet |
| payload grab |  |  |

A blank cell is a scenario that combination doesn't fly: top speed and wind only where the targets set them, the parachute drop with P, the payload grab with C.

<details>
<summary>hover, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.21 m sideways over 60 s | pass |
| hover height | held its height within 0.08 m | pass |

</details>

<details>
<summary>hover, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.21 m sideways over 60 s | pass |
| hover height | held its height within 0.08 m | pass |

</details>

<details>
<summary>wind, mission: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| wind drift | drifted 1.40 m in the wind | fail |
| motor headroom | the busiest motor reached 81% | pass |

</details>

## Why the misses miss

- wind drift in mission: not looked into yet

## The models

Each combination's model, as generated. The weight is the CAD's, without the sizing model's growth margin; the top speed is where each motor makes the sizing model's full-throttle thrust, at the 20% reserve and the 90 A cap.

| Setup | Weight | Hover throttle | Top speed | Thrust constant | Torque per thrust | Drag area | Chute | Payload |
|---|---|---|---|---|---|---|---|---|
| base | 1675 g | 48% | 8900 rpm | 1.55e-05 N/(rad/s)² | 16.5 mm | 120 cm² |  |  |
| mission | 2214 g | 58% | 8930 rpm | 1.55e-05 N/(rad/s)² | 16.5 mm | 202 cm² | yes |  |

## What it rests on

- the props' drag: PX4's x500 value

## What it can't prove

- The parachute's descent rate. Its drag comes from Fruity Chutes' own rating, so the sim only repeats it; the drop checks the order of events and the height lost. *First to measure:* A drop test of the chute with a dummy weight of the drone's mass, filmed against a tape to time its descent, before the chute ever flies on the drone.
- The payload grab. Gazebo's attach joint stands in for the claws, which are a placeholder anyway. *First to measure:* Waits for the claws' design.
- My firmware's current cap and the XT60's heat limit. This is PX4, which has neither, so the motors are held at their worst-case top speed instead. *First to measure:* On the bench, tethered with the props on: the current at full throttle, logged, and the XT60's temperature after a burst, with a thermocouple.
- The props' in-plane drag, their rolling moment and the motors' spin-up times, which are PX4's x500 values. *First to measure:* One motor and prop on a thrust stand: thrust and current through the throttle, and the spin-up time from a step.
- Body drag beyond a frontal-area estimate, until the wind tunnel side track has real tables. *First to measure:* A GPS-logged cruise at a steady speed in still air, with the current logged.
- Vibration, and anything else a real IMU sees that clean Gaussian noise doesn't. *First to measure:* A gyro log with the props spinning, tethered: its spectrum against the arms' frequencies and the props' speeds.

## Files

Generated on every run, not committed (they're build outputs):

- `outputs/flight-sim/models/pcs14_mission/model.sdf`
