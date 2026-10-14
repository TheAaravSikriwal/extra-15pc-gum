# Roadmap

This plan is going to change. It's the route I'm following today, not a promise. Sim results, test flights, broken parts and new ideas will all reshape it, and that's fine. I can't plan for everything, but I can be prepared. When something changes, I update this file and write down why in [decisions.md](decisions.md).

**Last revised:** 2026-10-14, the full plan revision. What changed and why is in [specs/2026-10-14-plan-revision.md](specs/2026-10-14-plan-revision.md).

## The short version

| Phase | What it's for | Done when | What I buy |
|---|---|---|---|
| **0. Planning** (done) | Figure out what I'm building | Decisions written down | Nothing |
| **1. Simulate the baseline** | Prove the plain X works, with real thrust data | The baseline passes sizing, CAD and Gazebo for all eight combinations, and has a price | Thrust-stand parts, most of which end up on the drone |
| **2. My firmware in sim** | Write the flight code and the safety monitor, and prove them | My firmware flies Base in sim and on the real chip, and the safety monitor works in hardware-in-the-loop | Nucleo-H743 (~$30), an IMU breakout (~$10), a second Teensy 4.1 (~$30) |
| **3. Bench build** | Build Base, props off | Every bench check passes on my firmware, and it boots and arms on PX4 | Base parts (most of the money), a Remote ID module |
| **4. First flights** | Fly Base for real | Stable on my firmware, hover times measured | Props, spares |
| **5. Module P** | Parachute | The chute deploys reliably, the automatic triggers are live, and the rule is enforced | P parts |
| **6. Module V** | GPS, camera, companion computer, HaLow | GPS hold, every landing mode, video on the laptop, cruise times measured | V parts |
| **7. Smart features** | Mapping, safe spots, the LLM, self-tuning, the Meshtastic relay | Each one proven in sim, then for real | Not much |
| **8. Module C** | Claws | Grabs and carries 250 g, and perches | C parts |
| **9. Extras** | Wristband and whatever else makes the cut | Decided when I get there | Per extra |
| **10. v2** | Build what the design hunt found, if it's worth building | Decided when there's a winner | Per design |

Spending is spread out. Before Phase 1 passes, the only purchases are thrust-stand parts, because they make the simulation more accurate. Each module only gets bought when its phase comes up.

**Running alongside, never blocking a phase:** the CFD wind tunnel, the design hunt, the FluidX3D showcase runs and the Blender renders. Whenever they produce numbers, those go back into the sizing model and Gazebo, and the targets get rechecked.

Why P before V: under the parachute rule, autonomous GPS missions and anything above about 30 m need the parachute fitted, so it has to exist first.

## Phase 1: Simulate the baseline

Mostly on the PC. The sizing and CAD work runs fine on the laptop too. The detailed design is in [specs/2026-10-13-phase-1-simulation.md](specs/2026-10-13-phase-1-simulation.md).

1. **Setup script, first half:** Gazebo Harmonic, PX4 and the Python tools on Ubuntu 24.04. OpenFOAM, ParaView and Blender come in the second half, when the CFD work starts.
2. **Sizing model:**
   - the parts catalog
   - the targets and the mass budget
   - a battery model with sag
   - thrust-to-weight at full charge and at the reserve
   - the current check
   - a sweep over motors, props and batteries, including 6S3P packs in case the extra cells earn their weight
3. **Thrust stand:** once the sizing model has a shortlist, I buy one motor, two or three props, the 4-in-1 ESC, a load cell with an HX711 amplifier, and a current sensor.
   - The Teensy logs thrust, current, voltage and RPM across the throttle range.
   - It runs off a real 6S pack, so the sag gets measured, not guessed.
   - The measured data replaces the manufacturer's in the catalog.
   - The stand gets bolted down, and nobody stands in line with the prop.
4. **CAD in code (baseline X):** Claude builds the drone in build123d, straight from the parts files. That covers:
   - every part, the module mount, the safety monitor, the Remote ID mount, and modules V, P and C
   - clearance checks, including every antenna (ExpressLRS, HaLow, GPS, Meshtastic)
   - real center of gravity and inertia
   - meshes, STEP files, and renders
5. **Gazebo model, flown by PX4:** every module combination goes through the same tests:
   - hover, and how it reacts to sudden stick inputs
   - a top-speed run
   - 10 m/s wind
   - hover and cruise endurance on a battery model
   - failsafes (lost link, low battery)
   - a parachute drop
   - a payload grab (sudden mass change)
   - every scenario's IMU data replayed through the safety monitor's trigger logic, counting false triggers
6. **The baseline passes.** Tag it, price it, and order the Base parts.

Every step exports visuals in the project's look, sized for LinkedIn and Instagram.

My firmware doesn't have to wait for step 6. Phase 2 can start as soon as Gazebo works, flying PX4's stock x500, and switches to my design once it passes.

**Done when:** I have a priced parts list for the plain X that passes sizing (with measured thrust data), CAD and Gazebo, across all eight module combinations.

## Running alongside: the wind tunnel and the design hunt

These start whenever there's time, and never hold up a phase.

1. **Aerodynamics:**
   - Prove OpenFOAM on a sphere and a cylinder first.
   - Then run the drone with its props as disks: drag at speed and tilt, prop wash on the modules, ground effect, crosswind.
   - Feed the results back into the sizing model and Gazebo, and recheck the targets.
2. **The design hunt:** an automated loop builds, tests and improves designs, looking for one that's actually unique and beats the baseline. The fast layers filter thousands of candidates, and the best go through CFD and Gazebo. Whatever it finds becomes v2 (Phase 10).
3. **Showcase visuals:** spinning-prop runs in FluidX3D and Blender hero renders.

## Phase 2: My firmware in simulation

1. **Architecture:** flight logic kept separate from the hardware drivers, so the same code runs on the PC and on the H743. A hardware watchdog and fresh DShot frames every loop from day one, so a hung CPU means the motors stop. Flight modes are separate pieces on top of the same controller, and the landing sequence has a swappable descent part, so later modes like the spiral descent (#34) drop in without rework.
2. **Warm-up (optional):** dRehmFlight on the Teensy with an IMU breakout, so I can watch a working flight controller before writing my own.
3. **Flight modes, in order:** rate mode, then self-level, then altitude hold. Each one runs the same tests as PX4 so I can compare them directly.
4. **Arming, failsafes and limits:**
   - pre-arm checks, including a live safety monitor
   - the kill switch
   - lost link
   - low battery, counted in mAh
   - the geofence, enforced on the flight controller
   - the limits profiles (see [decisions.md](decisions.md))
5. **Safety monitor firmware:** on a second Teensy 4.1, so the first one can stay on the thrust stand.
   - the kill switch from the receiver
   - the flight controller's heartbeat
   - the automatic triggers, in shadow mode
   - tested in hardware-in-the-loop with sim IMU data and a simulated kill switch
6. **Ground station v1** on the laptop: live telemetry, live PID tuning, and the active limits profile always on screen. It speaks MAVLink, so QGroundControl works from day one.
7. **Hardware-in-the-loop:** the same firmware running on the real Nucleo chip, with the sim feeding it sensor data.

**Done when:** my firmware flies Base in sim and on the real chip, and the safety monitor's kill path works in hardware-in-the-loop.

## Phase 3: Bench build

Props stay off the whole time.

1. **Thrust-stand the other three motors,** so I know all four match.
2. **Build Base:**
   - the ESC, motors, flight controller, receiver and rangefinder
   - the power wiring and the module mount
   - the safety monitor and its signal switch
   - the Remote ID mount
3. **Bench checks:** motor order and direction, sensor readings, ESC telemetry and failsafes, plus:
   - the kill switch through both paths
   - what the ESC does when its signal disappears, and how fast
   - that the signal switch passes signals with the Teensy unpowered
   - that the receiver feeds both boards cleanly
4. **Rules, taken into account (they're settings, not caps):**
   - FAA registration and the TRUST certificate
   - the Remote ID module
   - fill in the `us-recreational` limits profile from the current FAA and FCC rules
   - decide on Part 107 (the project is partly for my career, and the recreational rules cover flying strictly for fun)
   - find a field, and check the airspace and LAANC

**Done when:** Base passes every bench check on my firmware, and boots and arms on PX4.

## Phase 4: First flights

1. **PX4 first:** fly the real airframe on PX4. Hover, simple maneuvers, and a first hover-endurance run. If something's wrong with the hardware, I find out before my firmware is in the picture.
2. **Match the sim to reality** using the PX4 logs. It's the cleanest comparison, since the sim flies PX4 too. That makes every later phase's sim more believable.
3. **My firmware, tethered:** first flights tied to a test rig.
4. **Free flight:** low, in an open field. Self-level first, then altitude hold, then rate mode. The kill switch works through both paths, and the automatic triggers stay in shadow mode, logging.
5. **Hover endurance:** with ballast standing in for V, P and C, checked against the hover targets.

**Done when:** it flies stably on my firmware and the hover times are measured. If they miss, the targets change here, with the reason written down.

## Phase 5: Module P (parachute)

1. **Sim:** free-fall detection, the motor cut, and how the chute deploys.
2. **Build:** the chute and its ejector. The safety monitor is already on the drone.
3. **Drop tests:** with a dummy weight, long before it goes anywhere near the drone.
4. **Automatic triggers go live,** once the shadow-mode logs show enough flights with zero false triggers. The exact number gets picked from the Phase 4 logs.
5. **Enforce the rule:** no autonomous missions or flights above about 30 m without P fitted.

**Done when:** the chute deploys reliably, the automatic triggers are live, and the firmware enforces the rule.

## Phase 6: Module V (vision & nav)

1. **Sim first:** GPS position hold, back to start, land here, and waypoints, all on my firmware.
2. **Pick the hardware:** the companion computer (Pi 5 or Jetson), camera and video link (HaLow is the lead option), based on what the sim says.
3. **Build V** onto the mount, with module detection.
4. **Real flights, in order:** position hold, then the landing modes, then waypoints.
5. **Cruise endurance** at 10 m/s, now that GPS can hold the speed, checked against the cruise targets.
6. **Ground station v2:** map, mission planning, and video over HaLow. ATAK can show the same video if I want it.

**Done when:** GPS hold, every landing mode, and video on the laptop all work, and the cruise times are measured.

## Phase 7: Smart features

Each one goes sim first, then real.

1. Mapping runs (#7), processed in OpenDroneMap
2. Safe-spot detection and the "nearest safe spot" landing mode
3. Change detection (#11)
4. Wind sensing (#10) and the "turn back now" battery warning
5. Self-tuning (#21), with a profile for each module combination
6. GPS-free flight (#24)
7. The LLM mission assistant (#26): plan, checker, my approval, then flight
8. The Meshtastic relay (#30), with a range test against a ground mesh
9. Soar mode (#31): parking in rising air, holding position in a breeze, and riding the wind on routes. Sim first, with a rising-air field added to Gazebo.
10. Spiral descent (#34): coming down from height in a GPS-centered helix on low throttle. The sim checks the path; real flights check whether it beats a straight descent.

## Phase 8: Module C (claws)

This only happens if we come up with a unique claw on an actual arm. That gets talked through when the time comes.

1. **Sim:** grab and release, a sudden mass change, perching.
2. **Make them:** design and print the claws.
3. **Tests, in order:** grip tests on the bench, then flying with empty claws, then grabbing 250 g, then perching.

**Done when:** it grabs and carries 250 g, and perches.

## Phase 9: Extras

Wrist gesture control (#2) first, then whatever else from the ideas pool in [decisions.md](decisions.md) still sounds fun.

## Phase 10: v2

If the design hunt finds something that's actually better and actually unique, it gets its own build: priced, simulated against the same targets, and flown on the same firmware. If leaving the quad layout means changing the firmware, that work is part of this phase.

## The whole way through

- Every phase gets build-log entries in [log/](log/) for the posts.
- [STATUS.md](../STATUS.md) always shows the current phase and what's next.
- Tutorials and studying aren't in this roadmap. They live in [learning.md](learning.md), on my own time.
- When the plan changes, update the "Last revised" date up top and write the reason in [decisions.md](decisions.md).
