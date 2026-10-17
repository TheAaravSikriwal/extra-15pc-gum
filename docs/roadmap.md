# Roadmap

This plan is going to change. It's the route I'm following today, not a promise. Sim results, new ideas and things I learn along the way will all reshape it, and that's fine. I can't plan for everything, but I can be prepared. When something changes, I update this file and write down why in [decisions.md](decisions.md).

**Last revised:** 2026-10-17. It's a research project now: the goal is a virtual drone complete enough to build one day. The reasons are in [decisions.md](decisions.md), under "A research project, build-ready". The earlier revision (2026-10-14, tagged R1 to R7) is in [specs/2026-10-14-plan-revision.md](specs/2026-10-14-plan-revision.md).

## What done looks like

Someone could order the parts list, follow the assembly and wiring guides, flash my firmware, and run the bench and first-flight test plans. They'd also get an honest list of what the simulations couldn't prove, with the first thing to measure for each.

Nothing gets bought by default, and nothing flies. Two optional purchases are worth knowing about: a thrust stand (roughly $100–200), which is the one measurement that makes the whole simulation more believable, and a Nucleo-H743 (about $30), which runs my firmware on the real chip while the sim feeds it sensor data.

## The short version

**The main line.** Each step feeds the next.

| Step | What it's for | Done when |
|---|---|---|
| **0. Planning** (done) | Figure out what I'm designing | Decisions written down, reviewed and revised |
| **1. Sizing and parts** | Pick real, orderable parts that hit the targets | Every setup passes on paper with real parts, with uncertainty bands |
| **2. The virtual drone (CAD)** | Every part modeled and connected | The full assembly has zero collisions, and its mass properties are back in the sizing model |
| **3. Electrical design** | Every wire, pin and connector | Every connection is specified, and every current, voltage and temperature is inside its rating |
| **4. Flight sim (PX4)** | Prove the airframe flies | The baseline passes every scenario in all eight module combinations |
| **5. My firmware** | My own flight code and the safety monitor | Both pass the same tests as PX4 |
| **6. Modules in sim** | P, V, and C if it happens | Each module passes its tests in every combination it's part of |
| **7. Smart features in sim** | Everything from mapping to soar mode | Each one works in sim, and its limits are written down |
| **8. Build package** | Make it buildable | Someone could build it from the docs alone |

**Side tracks.** They start once their inputs exist and feed their numbers back into the main line, but never hold it up.

| Track | Starts after | What it's for |
|---|---|---|
| **Structure** | Step 2 | Stress and vibration in the frame, arms and module mount |
| **Aero** | Step 2 | The virtual wind tunnel: drag, prop wash, ground effect |
| **Design hunt** | Step 4 | Searching for a better, unique design: the v2 research |
| **Visuals** | Every step | Renders, charts and clips for the posts |

**Setup comes first:** WSL2 on the PC, with [setup-pc.md](setup-pc.md).

## Step 1: Sizing and parts

The detailed design is in [specs/2026-10-13-phase-1-simulation.md](specs/2026-10-13-phase-1-simulation.md).

1. **The parts catalog:** real, orderable parts, each with a part number, a price, dimensions, mass, and the manufacturer's thrust test data for motors and props. It starts with 3–4 candidates for each motor, prop and battery.
2. **The sizing model:**
   - the targets and the mass budget
   - a battery model with sag
   - thrust-to-weight at full charge and at the reserve
   - the current check
   - hover and cruise times, and the speed that uses the least power
   - top speed, and holding position in a 10 m/s wind
   - a sweep over motors, props and batteries, including 6S3P packs
3. **Uncertainty bands:** manufacturer thrust data runs optimistic, so every result carries ±15–20% unless it comes from a thrust stand.
4. **The thrust stand (optional):** one motor, a few props and the ESC on a load cell, logged by my Teensy and running off a real 6S pack. Its data replaces the manufacturer's in the catalog.

**Done when:** every setup passes on paper with real parts, the margins and uncertainty bands are in the report, and the parts are picked.

## Step 2: The virtual drone (CAD)

Claude writes the CAD in build123d, reading the catalog and `design/build.yaml`. Change a part and the model rebuilds itself.

1. **Every part from real dimensions:** manufacturer 3D files where they exist, datasheet drawings where they don't.
2. **Everything connected:** mounting holes, bolts and standoffs, the flight controller stack, the module mount and modules V, P and C, every connector, every antenna, and the routes the wires take. The wire lengths feed step 3.
3. **Checks:**
   - nothing collides
   - prop-to-frame, prop-to-prop and prop-to-antenna clearance
   - everything fits on the mount
   - the center of gravity sits close enough to the center of thrust
4. **What comes out:** mass properties for every module combination (replacing the sizing model's estimates), a STEP assembly, meshes for Gazebo and the wind tunnel, exploded views, and renders.

**Done when:** the full assembly has zero collisions, and its mass properties are back in the sizing model.

## Step 3: Electrical design

No custom PCB: everything is off-the-shelf boards and breakouts.

1. **A system schematic** in KiCad, and wiring harness diagrams generated from code with WireViz.
2. **A pin map:**
   - the flight controller: four bidirectional DShot outputs on timers, serial ports for the receiver, GPS, safety monitor and companion computer, SPI for the IMU
   - the Teensy: the receiver feed, its own IMU, the signal switch, the chute trigger, the heartbeat
3. **Power:** the battery connector, the ESC, 5 V supplies for the flight controller and the companion computer, the current sensor, a fuse, wire gauges and connector ratings.
4. **Checks:**
   - voltage drop, using wire lengths from the CAD
   - peak and continuous currents in every setup
   - rough heat in the ESC and motors
   - the power budget for every module combination
5. **Circuit sim (ngspice):** the safety monitor's signal switch passes bidirectional DShot cleanly, and still passes signals with the Teensy unpowered.

**Done when:** every connection is specified, and every current, voltage and temperature is inside its rating with margin.

## Step 4: Flight sim (PX4)

Gazebo Harmonic and PX4, in WSL2.

1. **A generator** turns `build.yaml`, the sizing output, the CAD mass properties and the aero tables (frontal-area guesses until the aero track delivers) into a Gazebo model and PX4 settings for each module combination.
2. **Scenarios**, the same every time:
   - hover, and the response to sudden stick inputs
   - a top-speed run
   - 10 m/s wind
   - hover and cruise endurance on the battery model
   - failsafes: lost link, low battery
   - a parachute drop and a payload grab
   - failure injection: a dead motor, a failed sensor, a sagging battery
   - every scenario's IMU data replayed through the safety monitor's trigger logic, counting false triggers
3. **Results** come out as pass/fail reports, with clips for the posts.

**Done when:** the baseline passes every scenario in all eight module combinations on PX4.

## Step 5: My firmware

1. **Architecture:**
   - flight logic separate from the hardware drivers, so the same code runs in the sim and on the H743
   - a hardware watchdog and fresh DShot frames every loop, so a hung CPU means the motors stop
   - flight modes as separate pieces on top of the same controller, and a landing sequence with a swappable descent part, so later modes like the spiral descent (#34) drop in without rework
2. **Warm-up (optional):** dRehmFlight on my Teensy with a cheap IMU breakout (about $10).
3. **Flight modes, in order:** rate mode, then self-level, then altitude hold, then position modes. Each one runs the same tests as PX4.
4. **Arming, failsafes and limits:**
   - pre-arm checks, including a live safety monitor
   - the kill switch
   - lost link
   - low battery, counted in mAh
   - the geofence, enforced on the flight controller
   - the limits profiles
5. **Safety monitor firmware:** its own program with its own simulated IMU and the receiver feed. It handles the kill switch and the heartbeat, and runs its automatic triggers in shadow mode.
6. **Ground station v1** on the laptop: live telemetry, live PID tuning, and the active limits profile always on screen. It speaks MAVLink, so QGroundControl works too.
7. **Hardware-in-the-loop (optional):** the same firmware on a Nucleo-H743, fed by the sim.

**Done when:** my firmware and the safety monitor pass the same tests as PX4.

## Step 6: Modules in sim

1. **P (parachute):**
   - deployment, with a simple drag model
   - the opening jolt, which feeds the structure track
   - motor-cut timing
   - the false-trigger replay
   - the parachute rule enforced in the firmware
2. **V (vision & nav):**
   - a simulated camera and GPS
   - HaLow modeled as a link, with range against bitrate and dropouts
   - video to the laptop
   - the companion computer's jobs, which settle Pi 5 vs Jetson
3. **C (claws):** only if a unique claw on an actual arm comes up. Grab and release, a sudden mass change, perching.

**Done when:** each module passes its tests in every combination it's part of.

## Step 7: Smart features in sim

Each one gets proven in sim, and whatever the sim can't show goes on the unproven list.

1. Landing modes: land now, back to start, land here
2. Mapping runs (#7) on simulated camera images, processed in OpenDroneMap
3. Safe-spot detection and the nearest-safe-spot landing
4. Change detection (#11), in a sim world where things move
5. Wind sensing (#10) and the "turn back now" battery warning
6. Self-tuning (#21), with a profile for each module combination
7. GPS-free flight (#24), on the simulated camera
8. Plain-English missions (#26), end to end: the plan, the checker, my approval, then the flight
9. Object detection on the laptop (#39), on the simulated camera and on recorded video
10. The Meshtastic relay (#30), as a link model
11. Soar mode (#31), with a rising-air field added to Gazebo
12. The spiral descent (#34). The sim checks the path only, since Gazebo doesn't model the vortex ring state.

**Done when:** each one works in sim, and its limits are on the unproven list.

## Step 8: The build package

1. **The parts list:** part numbers, supplier links, prices, and a fallback part for each
2. **The assembly guide:** exploded views rendered from the CAD
3. **The wiring guide:** generated from the wiring diagrams
4. **The firmware:** build steps and configuration
5. **Test plans:** bench checks with the props off, then first flights (PX4 first, then my firmware, tethered first)
6. **The legal checklist:** FAA registration, the TRUST certificate, Remote ID, the `us-recreational` profile, and whether to get Part 107
7. **The unproven list,** each item with the first thing to measure (see [decisions.md](decisions.md))

**Done when:** someone could build it from the docs alone.

## Side tracks

1. **Structure** (FreeCAD with CalculiX), once the CAD exists:
   - the arms under full thrust
   - the arms' vibration frequencies against the props' rotation speeds, which matters a lot for gyro noise
   - a rough drop-impact check
   - the parachute's opening jolt on the mount
   - module mount loads
2. **Aero** (OpenFOAM), once the CAD exists:
   - prove it on a sphere and a cylinder first
   - then drag tables, prop wash on the frame and modules, ground effect and crosswind
   - FluidX3D for the spinning-prop showcase visuals
   - the results feed back into the sizing model and Gazebo, and the targets get rechecked
3. **The design hunt,** once the baseline passes in Gazebo: an automated loop builds, tests and improves designs, looking for one that's actually unique and beats the baseline. Whatever it finds becomes the v2 research.
4. **Visuals,** from every step, in the project's look.

## Tools, and where they run

| Where | Tools |
|---|---|
| WSL2 Ubuntu 24.04 (both machines) | The Python code (sizing model, CAD in build123d, WireViz), Gazebo + PX4, OpenFOAM, my firmware in the sim, OpenDroneMap |
| Windows on the PC | KiCad with ngspice, FreeCAD with CalculiX, Blender on the RTX 3060, ParaView, FluidX3D |
| Windows on the laptop | The ground station, and object detection with OpenVINO |

The PC's native Ubuntu side stays as a fallback for really big wind tunnel runs, or if Gazebo's graphics struggle under WSL.

## The whole way through

- The live plan, with each step's outcome, is in the [README](../README.md#the-plan).
- Every step gets build-log entries in [log/](log/) for the posts.
- [STATUS.md](../STATUS.md) always shows the current step and what's next.
- Tutorials and studying aren't in this roadmap. They live in [learning.md](learning.md), on my own time.
- When the plan changes, update the "Last revised" date up top and write the reason in [decisions.md](decisions.md).
