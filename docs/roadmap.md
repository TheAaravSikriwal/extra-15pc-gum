# Roadmap

This plan is going to change. It's the route I'm following today, not a promise. Sim results, test flights, broken parts and new ideas will all reshape it, and that's fine. I can't plan for everything, but I can be prepared. When something changes, I update this file and write down why in [decisions.md](decisions.md).

**Last revised:** 2026-10-13

## The short version

| Phase | What it's for | Done when | What I buy |
|---|---|---|---|
| **0. Planning** (done) | Figure out what I'm building | Decisions written down | Nothing |
| **1. Simulate the design** | Prove the parts can hit the targets | Every module combination passes in sim, and the parts list has a price | Nothing |
| **2. My firmware in sim** | Write the flight code and prove it | My firmware flies Base through every test, in sim and on the real chip | Nucleo-H743 (~$30), an IMU breakout (~$10) |
| **3. Bench build** | Build the Base drone, props off | Every bench check passes on my firmware | Base parts (most of the money) |
| **4. First flights** | Fly Base for real | Stable hover and altitude hold, flight time confirmed, sim matches reality | Props, spares |
| **5. Module P** | Parachute and its independent monitor | The chute deploys reliably and the firmware enforces the rule | P parts |
| **6. Module V** | GPS, camera, companion computer | GPS hold, every landing mode, and video on the laptop | V parts |
| **7. Smart features** | Mapping, safe spots, the LLM, self-tuning and friends | Each one proven in sim, then for real | Not much |
| **8. Module C** | Claws | Grabs and carries 250 g, and perches | C parts |
| **9. Extras** | Wristband and whatever else makes the cut | Decided when I get there | Per extra |

Spending is spread out: nothing until Phase 1 passes, and each module only gets bought when its phase comes up.

Why P before V: under the parachute rule, autonomous GPS missions and anything above about 30 m need the parachute fitted, so it has to exist first.

## Phase 1: Simulate the design

Mostly on the PC. The sizing and CAD work runs fine on the laptop too. The detailed design is in [specs/2026-10-13-phase-1-simulation.md](specs/2026-10-13-phase-1-simulation.md).

1. **Setup script:** one command that installs Gazebo Harmonic, PX4 and the Python tools on Ubuntu 24.04, on both the PC and the laptop's WSL.
2. **Sizing model:** the parts files plus the calculator. Iterate motors, props and batteries until Base, Mission and Max all pass on paper.
3. **CAD mock-up in Onshape:**
   - Model the frame, every part, the module mount, and modules V, P and C.
   - Check it all fits and see where the center of gravity ends up.
   - Export the mass and inertia numbers.
4. **Gazebo model, flown by PX4:** every module combination goes through the same tests:
   - hover, and how it reacts to sudden stick inputs
   - a top-speed run
   - 10 m/s wind
   - full endurance on a battery model
   - failsafes (lost link, low battery)
   - a parachute drop
   - a payload grab (sudden mass change)
5. **Iterate:** swap parts and rerun until everything passes.
6. **Price it:** if it's over budget, swap parts and simulate again.

**Done when:** I have a priced parts list that passes everything. I'll order the Base parts here so they show up during Phase 2.

## Phase 2: My firmware in simulation

1. **Architecture:** flight logic kept separate from the hardware drivers, so the same code runs on the PC and on the H743.
2. **Warm-up (optional):** dRehmFlight on the Teensy with an IMU breakout, so I can watch a working flight controller before writing my own.
3. **Flight modes, in order:** rate mode, then self-level, then altitude hold. Each one runs the same tests as PX4 so I can compare them directly.
4. **Arming and failsafes:** pre-arm checks, the kill switch, and lost-link and low-battery behavior.
5. **Ground station v1** on the laptop: live telemetry and live PID tuning. It speaks MAVLink, so QGroundControl works from day one.
6. **Hardware-in-the-loop:** the same firmware running on the real Nucleo chip, with the sim feeding it sensor data.

**Done when:** my firmware flies Base in sim and on the real chip.

## Phase 3: Bench build

Props stay off the whole time.

1. **Thrust stand:** the Teensy measures real thrust and efficiency, and I feed the numbers back into the sizing model and Gazebo. Then I recheck the targets with real data.
2. **Build Base:** solder the ESC, motors, flight controller, receiver, rangefinder and power wiring, and fit the module mount.
3. **Bench checks:** motor order and direction, sensor readings, ESC telemetry, failsafes, and the kill switch.
4. **Legal stuff:**
   - FAA registration
   - TRUST certificate
   - a Remote ID plan
   - find a field, and check the airspace and LAANC

**Done when:** Base passes every bench check on my firmware.

## Phase 4: First flights

1. **Baseline (optional):** fly the real airframe once on PX4. That means picking an H743 board PX4 supports. If my firmware misbehaves later, I'll know the hardware is fine.
2. **My firmware, tethered:** first flights tied to a test rig.
3. **Free flight:** low, in an open field. Self-level first, then altitude hold, then rate mode.
4. **Match the sim to reality:** compare real flight logs against the sim, and adjust the sim until they agree. That makes every later phase's sim more believable.
5. **Endurance test:** with ballast standing in for V, P and C.

**Done when:** it flies stably and the flight time is confirmed.

## Phase 5: Module P (parachute)

1. **Sim:** free-fall detection, the motor cut, and how the chute deploys.
2. **Build:** the chute, the Teensy monitor with its own IMU, and the motor-cut circuit.
3. **Drop tests:** with a dummy weight, long before it goes anywhere near the drone.
4. **Enforce the rule:** no autonomous missions or flights above about 30 m without P fitted.

**Done when:** the chute deploys reliably and the firmware enforces the rule.

## Phase 6: Module V (vision & nav)

1. **Sim first:** GPS position hold, back to start, land here, and waypoints, all on my firmware.
2. **Pick the hardware:** the companion computer (Pi 5 or Jetson), camera and video link, based on what the sim says.
3. **Build V** onto the mount, with module detection.
4. **Real flights, in order:** position hold, then the landing modes, then waypoints.
5. **Ground station v2:** map, mission planning, video.

**Done when:** GPS hold, every landing mode, and video on the laptop all work.

## Phase 7: Smart features

Each one goes sim first, then real.

1. Mapping runs (#7), processed in OpenDroneMap
2. Safe-spot detection and the "nearest safe spot" landing mode
3. Change detection (#11)
4. Wind sensing (#10) and the "turn back now" battery warning
5. Self-tuning (#21), with a profile for each module combination
6. GPS-free flight (#24)
7. The LLM mission assistant (#26): plan, checker, my approval, then flight

## Phase 8: Module C (claws)

1. **Sim:** grab and release, a sudden mass change, perching.
2. **Make them:** design and print the claws.
3. **Tests, in order:** grip tests on the bench, then flying with empty claws, then grabbing 250 g, then perching.

**Done when:** it grabs and carries 250 g, and perches.

## Phase 9: Extras

Wrist gesture control (#2) first, then whatever else from the ideas pool in [decisions.md](decisions.md) still sounds fun.

## The whole way through

- Every phase gets build-log entries in [log/](log/) for the posts.
- [STATUS.md](../STATUS.md) always shows the current phase and what's next.
- When the plan changes, update the "Last revised" date up top and write the reason in [decisions.md](decisions.md).
