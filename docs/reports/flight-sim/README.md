# The flight sim

*Generated on 2026-10-19 by pcs14 0.1.0, the flight sim in `src/pcs14/flight/`. PX4 v1.17.0 flies a Gazebo Harmonic model of this drone, generated from the build, the sizing model and the CAD, in every module combination.*

## The verdict

**Not flown yet.** 78 scenario runs are planned across 8 combinations; the models are generated and waiting.

Built from E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P45B.

## Every scenario, every combination

| Scenario | base | V | P | C | mission | V+C | P+C | max |
|---|---|---|---|---|---|---|---|---|
| hover | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| steps | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| top speed |  | not yet | not yet |  | not yet |  |  |  |
| wind |  | not yet | not yet |  | not yet |  |  |  |
| endurance | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| lost link | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| low battery | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| parachute drop |  |  | not yet |  | not yet |  | not yet | not yet |
| dead motor | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| failed sensor | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| sagging pack | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| payload grab |  |  |  | not yet |  | not yet | not yet | not yet |

A blank cell is a scenario that combination doesn't fly: top speed and wind only where the targets set them, the parachute drop with P, the payload grab with C.

## The models

Each combination's model, as generated. The weight is the CAD's, without the sizing model's growth margin; the top speed is where each motor makes the sizing model's full-throttle thrust, at the 20% reserve and the 90 A cap.

| Setup | Weight | Hover throttle | Top speed | Thrust constant | Torque per thrust | Drag area | Chute | Payload |
|---|---|---|---|---|---|---|---|---|
| base | 1875 g | 53% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 120 cm² |  |  |
| V | 2039 g | 56% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 177 cm² |  |  |
| P | 2050 g | 56% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 145 cm² | yes |  |
| C | 2034 g | 60% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.1 mm | 160 cm² |  | 250 g |
| mission | 2213 g | 58% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 202 cm² | yes |  |
| V+C | 2198 g | 62% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.2 mm | 217 cm² |  | 250 g |
| P+C | 2209 g | 62% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.2 mm | 185 cm² | yes | 250 g |
| max | 2372 g | 64% | 8836 rpm | 1.58e-05 N/(rad/s)² | 16.4 mm | 242 cm² | yes | 250 g |

## What it rests on

- The props' in-plane drag, their rolling moment and the motors' spin-up and spin-down times: PX4's x500 model (PX4-gazebo-models b6127f4, pinned by PX4 v1.17.0)
- fruity-chutes-harrier-40-42: ejection_s, opening_s. Fruity Chutes doesn't publish its timing. A spring launcher clears the tube in a fraction of a second, and a canopy this size takes about a second to fill at low speed; both are guesses for the flight sim, which reports the height lost while it opens
- The frame's drag area: Frontal area from the published size, times a drag coefficient of 1.0 for a blunt body: body 35 x 100 mm, arms 7 x 297 mm, four motors about 35 x 25 mm, and a 6S2P 21700 pack end-on about 42 x 70 mm, about 0.012 m2 in all. The battery is counted here. Replaced when the wind tunnel side track has real numbers
- The safety monitor's trigger thresholds are starting numbers, to be tuned against the false-trigger replays

## What it can't prove

- The parachute's descent rate. Its drag comes from Fruity Chutes' own rating, so the sim only repeats it; the drop checks the order of events and the height lost.
- The payload grab. Gazebo's attach joint stands in for the claws, which are a placeholder anyway.
- My firmware's current cap and the XT60's heat limit. This is PX4, which has neither, so the motors are held at their worst-case top speed instead.
- The props' in-plane drag, their rolling moment and the motors' spin-up times, which are PX4's x500 values.
- Body drag beyond a frontal-area estimate, until the wind tunnel side track has real tables.
- Vibration, and anything else a real IMU sees that clean Gaussian noise doesn't.

## Files

Generated on every run, not committed (they're build outputs):

- `flight-sim/models/pcs14_base/model.sdf`
- `flight-sim/models/pcs14_c/model.sdf`
- `flight-sim/models/pcs14_max/model.sdf`
- `flight-sim/models/pcs14_mission/model.sdf`
- `flight-sim/models/pcs14_p/model.sdf`
- `flight-sim/models/pcs14_p_c/model.sdf`
- `flight-sim/models/pcs14_payload/model.sdf`
- `flight-sim/models/pcs14_v/model.sdf`
- `flight-sim/models/pcs14_v_c/model.sdf`
- `flight-sim/worlds/pcs14.sdf`

Skipped on this run:

- flying the scenarios: PX4 and Gazebo run in WSL2 on the PC (task 10)
