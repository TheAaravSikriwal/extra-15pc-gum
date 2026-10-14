# Roadmap

> **This plan will change.** It's the route we're following today, not a promise. Simulation results, test flights, broken parts and new ideas will all reshape it, and that's expected. We can't plan for everything, but we can be prepared. When something changes, it's recorded here and in [decisions.md](decisions.md) along with the reason.

**Last revised:** 2026-10-13

## At a glance

| Phase | Goal | Done when | What gets bought |
|---|---|---|---|
| **0. Planning** ✅ | Decide what we're building | Decisions log written | Nothing |
| **1. Simulate the design** | Prove the parts can hit the targets | Every module combination passes in sim, and the parts list is priced | Nothing |
| **2. My firmware in sim** | Write the flight code and prove it in sim | My firmware flies Base through every test, in sim and on the real chip | Nucleo-H743 (~$30), IMU breakout (~$10) |
| **3. Bench build** | Build the Base drone, props off | Every bench check passes on my firmware | Base parts (the bulk of the cost) |
| **4. First flights** | Fly Base for real | Stable hover and altitude hold, flight time confirmed, sim matches reality | Props, spares |
| **5. Module P** | Parachute and independent monitor | Chute deploys reliably, firmware enforces the rule | P parts |
| **6. Module V** | GPS, camera, companion computer | GPS hold, all landing modes and video to the laptop working | V parts |
| **7. Smart features** | Mapping, safe spots, LLM, self-tuning and the rest | Each feature proven in sim, then for real | Little or nothing |
| **8. Module C** | Claws | Grabs and carries 250 g, perches | C parts |
| **9. Extras** | Wristband and other shortlist ideas | Decided at the time | Per extra |

Spending is spread out: nothing until Phase 1 passes, and each module is bought only when its phase arrives.

**Why P comes before V:** under the parachute rule, autonomous GPS missions and flights above ~30 m need P fitted, so it has to exist first.

## Phase 1: Simulate the design

Mostly on the PC; the sizing and CAD work runs on the laptop too.

1. **Setup script:** one command installs Gazebo Harmonic, PX4 and Python on Ubuntu 24.04, on both the PC and the laptop's WSL.
2. **Sizing model:** the parts file plus the calculator. Iterate motors, props and batteries until Base, Mission and Max all pass on paper.
3. **CAD mock-up in Onshape:** frame, every part, the module mount and modules V, P and C. Check that everything fits and where the centre of gravity lands, and export the mass and inertia numbers.
4. **Gazebo model, flown by PX4:** every module combination goes through the same test scenarios:
   - hover, and how it responds to sudden stick inputs
   - top-speed run
   - 10 m/s wind
   - full endurance on a battery model
   - failsafes (lost link, low battery)
   - a parachute drop
   - a payload grab (sudden mass change)
5. **Iterate:** swap parts and re-run until everything passes.
6. **Price it:** if it's over budget, swap parts and re-simulate.

**Exit:** a priced parts list that passes everything. Order the Base parts here, so they arrive during Phase 2.

## Phase 2: My firmware in simulation

1. **Architecture:** keep the flight logic separate from the hardware drivers, so the same code runs on the PC and on the H743.
2. **Optional warm-up:** dRehmFlight on the Teensy 4.1 with an IMU breakout, to see a working flight controller before writing my own.
3. **Flight modes, in order:** rate mode, then self-level, then altitude hold. Each is tested in the same scenarios as PX4 and compared against it.
4. **Arming and failsafes:** pre-arm checks, kill switch, lost-link and low-battery behaviour.
5. **Ground station v1** on the laptop: live telemetry and live PID tuning. It speaks MAVLink, so QGroundControl works from day one.
6. **Hardware-in-the-loop:** the same firmware runs on the real Nucleo chip, with the simulator feeding it sensor data.

**Exit:** my firmware flies Base in sim and on the real chip.

## Phase 3: Bench build (props off throughout)

1. **Thrust stand** run by the Teensy: measure real thrust and efficiency, and feed the numbers back into the sizing model and Gazebo. Re-check the targets with real data.
2. **Build Base:** solder the ESC, motors, flight controller, receiver, rangefinder and power wiring, and fit the module mount.
3. **Bench checks:** motor order and direction, sensor readings, ESC telemetry, failsafes and the kill switch.
4. **Legal prep:**
   - FAA registration
   - TRUST certificate
   - a Remote ID plan
   - a flying field, with an airspace and LAANC check

**Exit:** the Base drone passes every bench check on my firmware.

## Phase 4: First flights (Base)

1. **Optional baseline:** fly the real airframe once on PX4. Choose an H743 board that PX4 supports so this is possible. If my firmware later misbehaves, I'll know the hardware is fine.
2. **My firmware, tethered:** first flights tied to a test rig.
3. **Free flight:** low and in an open field. Self-level first, then altitude hold, then rate mode.
4. **Match the sim to reality:** compare real flight logs with the sim and adjust the sim until they agree.
5. **Endurance test** with ballast standing in for V, P and C.

**Exit:** stable flight, flight time confirmed, sim matches reality.

## Phase 5: Module P (parachute)

1. **Sim:** free-fall detection, motor cut, and how the chute deploys.
2. **Build:** the chute, the Teensy monitor with its own IMU, and the motor-cut circuit.
3. **Drop tests** with a dummy weight before it ever goes on the drone.
4. **The rule:** no autonomous missions or flights above about 30 m without P fitted.

**Exit:** the chute deploys reliably and the firmware enforces the rule.

## Phase 6: Module V (vision & nav)

1. **Sim first:** GPS position hold, back to start, land here, and waypoints, all on my firmware.
2. **Choose the companion computer** (Pi 5 or Jetson), the camera and the video link, guided by the sim results.
3. **Build** V onto the mount, with module detection.
4. **Real flights:** position hold, then the landing modes, then waypoints.
5. **Ground station v2:** map, mission planning and video.

**Exit:** GPS hold, all landing modes and video to the laptop working.

## Phase 7: Smart features

Each one sim first, then for real.

1. **Mapping runs** (#7), processed in OpenDroneMap
2. **Safe-spot detection**, and the "nearest safe spot" landing mode
3. **Change detection** (#11)
4. **Wind sensing** (#10) and the "turn back now" battery warning
5. **Self-tuning** (#21), with a profile for each module combination
6. **GPS-free flight** (#24)
7. **The LLM mission assistant** (#26): plan, then checker, then my approval, then flight

## Phase 8: Module C (claws)

1. **Sim:** grab and release, a sudden mass change, and perching.
2. **Design and print** the claws.
3. **Tests, in order:** grip tests on the bench, then flying with empty claws, then grabbing 250 g, then perching.

**Exit:** it grabs and carries 250 g, and perches.

## Phase 9: Extras

Wrist gesture control (#2), then anything else from the ideas pool in [decisions.md](decisions.md).

## Throughout

- Every phase gets a build-log entry in [log/](log/) for the online posts.
- [STATUS.md](../STATUS.md) always shows the current phase and next steps.
- When the plan changes, update this file's "Last revised" date and note why in [decisions.md](decisions.md).
