# The flight sim

*Generated on 2026-10-20 by pcs14 0.1.0, the flight sim in `src/pcs14/flight/`. PX4 v1.17.0 flies a Gazebo Harmonic model of this drone, generated from the build, the sizing model and the CAD, in every module combination.*

## The verdict

**Fail.** 13 of 78 runs flown, and 4 miss: endurance in base; dead motor in base; failed sensor in base; failed sensor in P.

Built from E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P45B.

## Every scenario, every combination

| Scenario | base | V | P | C | mission | V+C | P+C | max |
|---|---|---|---|---|---|---|---|---|
| hover | pass | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| steps | pass | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| top speed |  | not yet | not yet |  | pass |  |  |  |
| wind |  | not yet | not yet |  | pass |  |  |  |
| endurance | **fail** | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| lost link | pass | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| low battery | not yet | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| parachute drop |  |  | pass |  | not yet |  | not yet | not yet |
| dead motor | **fail** | not yet | pass | not yet | not yet | not yet | not yet | not yet |
| failed sensor | **fail** | not yet | **fail** | not yet | not yet | not yet | not yet | not yet |
| sagging pack | pass | not yet | not yet | not yet | not yet | not yet | not yet | not yet |
| payload grab |  |  |  | pass |  | not yet | not yet | not yet |

A blank cell is a scenario that combination doesn't fly: top speed and wind only where the targets set them, the parachute drop with P, the payload grab with C.

<details>
<summary>dead motor, base: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 2 m from where it was then | pass |
| touchdown | came down at 24.8 m/s at the end, too fast for a controlled landing | fail |

</details>

<details>
<summary>endurance, base: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 33.3 min in the sim against the sizing model's 33.2, at 287 W | pass |
| cruise endurance | 33.5 min in the sim against the sizing model's 44.9, at 285 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, base: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 38 m from where it was then | fail |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.09 m sideways over 60 s | pass |
| hover height | held its height within 0.07 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 79% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.25 s | pass |
| roll to 15 degrees: overshoot | overshot by 3% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.25 s | pass |
| roll back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.23 s | pass |
| pitch to 15 degrees: overshoot | overshot by 3% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.23 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 4% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>payload grab, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| payload drift | stayed within 0.05 m after picking it up | pass |
| payload lifted | the rotors' thrust grew 12%, against 12% for 250 g | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>top speed, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| top speed | held 88 km/h for 1 s, against 80 | pass |
| top speed, flat out | the busiest motor at 100% of its top speed, leaning up to 47 degrees | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>wind, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| wind drift | drifted 0.11 m in the wind | pass |
| motor headroom | the busiest motor reached 64% of its top speed | pass |
| leaning into the wind | leaned 3.3 degrees into a 10 m/s wind | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 1 m from where it was then | pass |
| chute order | the motors stopped 0.15 s before the canopy left | pass |
| chute height lost | lost 8.9 m before settling at 4.2 m/s | pass |

</details>

<details>
<summary>failed sensor, P: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 37 m from where it was then | fail |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>parachute drop, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| chute order | the motors stopped 0.14 s before the canopy left | pass |
| chute height lost | lost 4.5 m before settling at 4.1 m/s | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |

</details>

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
