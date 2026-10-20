# 2026-10-20: Every scenario, and what they found

*PC, Windows and WSL2 Ubuntu. Step 4c, task 11, in progress, plus the start of task 12.*

All twelve scenarios are written and have each flown at least once: hover, stick steps, top speed, wind, endurance, lost link, low battery, the parachute drop, a dead motor, a failed sensor, a sagging pack and the payload grab. A clean batch of all 78 runs is flying as I write this.

## What passes

| Scenario | What it showed |
|---|---|
| Hover | 0.07 to 0.09 m of drift in 60 s, height within 0.05 to 0.07 m |
| Stick steps | a 15° roll or pitch step settles in 0.16 to 0.25 s, 2 to 4% overshoot (after tuning) |
| Top speed | Mission held 88 km/h against the 80 km/h target, leaning 45° |
| Wind | 10 m/s: 0.11 m of drift, leaning 3.3° into it, busiest motor at 64% |
| Lost link | uplink cut, PX4 waited its 10 s, returned and landed where it took off |
| Low battery | warned at 35%, returned at 30%, landed home with 29% left by my battery model |
| Parachute drop | the motors stop 0.14 s before the canopy leaves, 4.5 m lost, then 4.1 m/s |
| Dead motor, with P | PX4's failure detector terminates 0.6 s after the motor dies, and the chute brings it down at 4.2 m/s |
| Sagging pack | motors capped at 79% of their top speed, PX4 lands it at 0.7 m/s |
| Payload grab | stays within 5 cm, and the rotors' thrust grows 12%, exactly the 250 g |

## What doesn't, and why

**A dead motor without P is a crash.** A quad can't fly on three motors. PX4 drops the dead one from the mix and tries, but it tumbles and hits the ground at about 25 m/s from 40 m. So every combination without P (base, V, C, V+C) loses the drone to a dead motor. That's physics, not a bug, and it's the biggest thing the flight sim has said so far.

**Losing GPS means coming down blind.** This drone's only other position-ish sensor is the TF-Luna, which measures height. Without GPS, PX4 descends level by its own attitude estimate, and that estimate's small tilt error carried it 34 to 38 m away in calm air. In wind it would go farther. A small optical flow sensor is the obvious fix, and it's a parts-list change, so it's a decision for later.

**Cruise endurance disagrees by about 25%.** Hover agrees almost exactly (33.3 min in the sim, 33.2 in the sizing model). Cruise doesn't: the sizing model says forward flight is cheaper than a hover, and Gazebo's rotors make the same thrust at any airspeed, so in the sim a cruise costs what a hover does. Neither is the truth. It's the forward-flight rotor gap that's been on the open list since step 1, now with a number on it.

## What broke on the way

- **The chute fired on take-off.** I gave PX4's parachute output function 400, which is the landing gear. The "gear" retracted after take-off, the servo swung over, and my plugin opened the canopy 4 m up. Mission then crawled along at 4 m/s at a 45° lean, and the wind blew it over. Function 401 is the parachute.
- **The stick steps were too slow.** PX4's x500 attitude gain (6.5) settled a step in 0.6 s against the 0.5 s target. At 9 it settles in 0.25 s with 3 to 4% overshoot. That's the one PX4 tuning change so far, written next to its reason in the generator.
- **Altitude mode didn't always take.** Once, PX4 refused the switch, and the first stick movement dropped it from Hold into Position mode, where a stick means a speed. The script now waits until PX4 really is in altitude mode.
- **The dead motor kept spinning.** PX4 ignores injected motor failures unless CA_FAILURE_MODE is set. Its "drop the failed motor" setting is what I'd want on the real drone anyway.
- **The GPS failure did nothing.** PX4's sensor failure injection only works with Gazebo Classic. The GPS now fails on PX4's side: its estimator stops using it mid-flight.
- **Power was read the wrong way.** The sim's one-number motor fit runs 3% slow at hover, which is 9% in power if you read the table by speed. Reading it by the thrust the rotor actually made fixed hover endurance.
- **Four runs at once was too many.** At 4x sim speed with four runs side by side, the PC hit a load of 18.6 on 16 threads, and the results got worse (0.81 m of hover height error instead of 0.05). Two at a time at 4x matches the real-time runs.

## Also new

Stills in the post sizes (the parachute drop as the hero, the stick steps before and after tuning, the pass/fail matrix), a Rerun replay of any flown run, a `report` action that writes the report without touching the model files, a `regrade` action, and the start of closing the loop: flight times side by side with the sizing model, the false-trigger counts, and how soon the safety monitor's triggers would catch a real failure.

## Next

Finish the batch, rerun anything the sim itself spoiled, write the report, stills and replays, and fly the stick steps once more on the x500's gains for the before-and-after still. Then task 12 and the write-up.
