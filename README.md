# Extra 15pc Gum

I'm designing a long-range quadcopter from scratch, as a research project. Every real part gets modeled and connected, the wiring gets worked out, and my own flight firmware flies it in simulation. Nothing gets bought. The goal is a design complete enough that I could build it one day, plus an honest list of what the simulations can't prove. This repo is all of it. The plan, the code, the mistakes, out in the open.

Yes, it's named after a pack of gum. It made sense at the time.

**Where it's at:** planning is done, and the first step (sizing and parts) is up next. [The plan](#the-plan) below shows every step and what came out of it. [STATUS.md](STATUS.md) has today's details, and the [roadmap](docs/roadmap.md) has the rest. It will change.

## What it's designed to do

- **Fly for a long time.** 8–10" props, low-KV motors and a Li-ion pack, aiming for 25–40 minutes of cruising.
- **Run on my code.** A flight controller I'm writing myself, for an STM32H743.
- **Land where I tell it.** Back where it took off, a spot I click on the map, right where it is, or the nearest safe spot it found on a 3D map of the area.
- **Not fall out of the sky.** Failsafes for lost signal, low battery and lost GPS, plus a parachute fired by a separate little computer that doesn't trust my main firmware either.
- **See and find its way.** Camera and GPS, mapping runs, objects spotted and labeled on my laptop, and getting home on the camera alone if GPS drops.
- **Use the air.** While it waits, it parks in rising air and breezes, like a kestrel hanging over a hillside.
- **Get smarter.** It tunes itself, and takes missions in plain English from an LLM on my laptop. The LLM makes the plan. It never touches the motors.

## The plan

This is the live version. When a step finishes, its outcome goes here, with a link to the details. The reasons behind each step are in the [roadmap](docs/roadmap.md) and [decisions.md](docs/decisions.md).

**Done means** someone could order the parts, follow the assembly and wiring guides, flash my firmware and run the test plans, with an honest list of what the simulations couldn't prove. Nothing gets bought by default.

| Step | What it's for | Status | Outcome |
|---|---|---|---|
| 0. Planning | Figure out what I'm designing | Done, 2026-10-17 | Decisions, targets and roadmap written, reviewed and revised ([log](docs/log/2026-10-14-plan-revision.md)), then turned into a research plan ([log](docs/log/2026-10-17-research-project.md)) |
| Setup | WSL2 on the PC, with all checks passing | Done, 2026-10-19 | WSL2 Ubuntu 24.04 with PX4 v1.17.0, Gazebo Harmonic and the flight sim's tools ([machine check](docs/machines/pc.md), [log](docs/log/2026-10-19-first-flight.md)) |
| 1. Sizing and parts | Real, orderable parts that hit the targets | Done, 2026-10-17 | Emax 2814 850KV motors, Gemfan 10x5 props, a 6S2P Molicel pack (P42A then, P45B since step 3) and a Nazgul XL10 frame. Every setup passed, Max included: 25.7 min hover with Mission's loadout at 2254 g ([report](docs/reports/sizing/README.md), [log](docs/log/2026-10-17-first-real-sweep.md)) |
| 2. The virtual drone (CAD) | Every part modeled and connected | Done, 2026-10-18 | Every part modeled and every module combination passing its checks, with the real weights back in the sizing model: Mission 2293 g, still passing ([report](docs/reports/cad/README.md), [log](docs/log/2026-10-18-cad-build.md)) |
| 3. Electrical design | Every wire, pin and connector | Done, 2026-10-19 | One connection list behind every check, diagram and the schematic: 438 checks pass in all eight combinations (437 since the wire routes were redrawn from the plugs on 2026-10-21, when a ground pin's tiny share of a ground loop fell under the 1 mA the check counts from), and ngspice shows the safety monitor's switch working. Weighing the real wiring and hardware moved the cells to P45B: Mission is 2414 g with a 22.25 min pessimistic hover ([report](docs/reports/electrical/README.md), [log](docs/log/2026-10-19-electrical-report-and-weight.md)) |
| 4. Flight sim (PX4) | Prove the airframe flies, in all eight module combinations | Done, 2026-10-20 | 62 of 78 runs pass; the 16 misses are three real findings: a dead motor without the chute crashes, losing GPS means a blind descent that can drift past 30 m, and cruise endurance runs 25% under the sizing model. The hover times agree with the sizing model to 0.1 min ([report](docs/reports/flight-sim/README.md), [log](docs/log/2026-10-20-flight-sim-final.md)) |
| 5. My firmware | My flight code and the safety monitor, passing the same tests as PX4 | Done, 2026-10-20 | C++17, one core library with thin layers for the sim, the ARK FPV and the safety monitor, speaking PX4's MAVLink and ULog so the same scenarios grade it. 66 of 78 runs pass against PX4's 62: everything PX4 passes, plus the four GPS failures PX4 drifted too far in. The other twelve miss for the same reasons as PX4's ([report](docs/reports/flight-sim/README.md#my-firmware-the-same-scenarios), [log](docs/log/2026-10-20-firmware-flies.md)) |
| 6. Modules in sim | Parachute, vision & nav, and claws if they happen | Done, 2026-10-20, except C | The safety monitor fires the chute now, motors first, only with P. A hung flight controller at 40 m with the chute on: cut in 0.28 s, down at 4.1 to 4.4 m/s with 24 m to spare, in every P combination. Drops from 10 m up all saved, but the height it needs rests on the canopy's unpublished opening time (11 m lost at 2 s). HaLow faded in the sim within 1.5% of its model, about 6 km out 10 m up, and the drone flew on. V's camera renders in Gazebo. The companion computer stays the Pi 5. C waits on the claw conversation ([report](docs/reports/modules/README.md), [log](docs/log/2026-10-20-modules-in-sim.md)) |
| 7. Smart features in sim | Mapping, safe spots, the LLM, object detection, soar mode, the spiral descent and more | Done, 2026-10-21 | All twelve work in the sim, 22 of 22 runs. Self-tuning finds the inertia within 0.3% in all eight combinations from three stick doublets. The GPS-free estimate (the camera and the rangefinder) ended 0.17 m off after 103 m, at 3 m/s; at 15 m/s it lost the ground. The local model's plans fly, but it misread "60 m west" into a safe, wrong plan, so I approve plans on a map. The vision model boxed 14 of 20 things: a describer, not a detector to land by. Maps, change detection and the safe-spot landing work over flat-colored scenery ([report](docs/reports/smart/README.md), [log](docs/log/2026-10-21-smart-features.md)) |
| 8. Build package | Parts list, assembly and wiring guides, test plans, and the unproven list | Done, 2026-10-21 | `pcs14 package` writes it all to docs/build: every bought part with a buy link, a price and a fallback ($875 for Base to $2,171 for Max, plus $362 bought once), a 16-step assembly guide rendered from the CAD, every wire harness by harness, PX4 first with each combination's parameters, bench checks for every safety rule, the legal checklist, and every unproven item with the first thing to measure. Two supply problems to decide: the chute switch's chip is gone until 2027, and the HaLow card isn't proven on a Pi 5 ([package](docs/build/README.md), [log](docs/log/2026-10-21-build-package.md)) |

| Side track | Starts after | Status | Outcome |
|---|---|---|---|
| Structure | Step 2 | First pass done, 2026-10-21 | Beam math, since CalculiX isn't installed: the arms are about seven times as strong as full thrust needs, but they ring sideways at 80 to 144 Hz, right where an unbalanced prop shakes them in a hover (88 to 103 Hz), so the props get balanced and the first gyro log gets checked. The chute's mount rests on heat-set inserts and nylon screws with thin margins: steel screws suggested and a hang test added ([report](docs/reports/structure/README.md), [log](docs/log/2026-10-21-structure-first-pass.md)). Up next: CalculiX for the cradle, rail and legs |
| Aero (the wind tunnel) | Step 2 | In progress | The visual half: FluidX3D on the RTX 3060, the drone's drag lines and wake at 10 m/s, the crosswind, and the hover's downwash, with the props as actuator disks because at 3.4 mm cells the blades' pitch is one cell and they pushed no air down ([spec](docs/specs/2026-10-20-wind-tunnel-visuals.md), [log](docs/log/2026-10-20-first-wind-tunnel.md), [hover log](docs/log/2026-10-20-wind-tunnel-hover.md)). The stills wait for the FluidX3D fork to go public. Up next: OpenFOAM for the numbers |
| Design hunt (v2) | Step 4 | Not started | |
| Project site | Step 1 | Done, 2026-10-20 | A static site that opens from a folder: the drone in 3D (click any of its 86 pieces, switch modules off, pull it apart, the wires colored by how hard they work), the spec sheet, the wiring with every board's pin map, a page per step built from this plan, every flight played back with PX4's run and mine on one clock, the wind tunnel's flow on the same clock, and what the sims can't prove, one click from the home page ([spec](docs/specs/2026-10-20-project-site.md), [plan](docs/plans/2026-10-20-project-site.md), [log](docs/log/2026-10-20-project-site.md)). The first load is 267 kB. It grows with each step, stays on my machine until the project is done, and the tunnel's pictures wait for the FluidX3D fork to go public Since 2026-10-21 it holds everything: Build it (the parts and their prices), the library (every doc in the repo, rendered), the catalog (every part, every field and source), the data (every report's own data file) and the math (how each number is worked out, in the code's own words). Its home is now the drone view: one 3D drone always on screen, Inside it over a blueprint (every wire drawn pin to pin from the researched pins, a board lighting its wires, the camera flying in to a picked wire's pin) and Fly it in white space (all 198 recorded runs as looping animations, each with a drawing of its run, its route in the air, and a strip of what's happening as it plays), with detailed parts drawn as looks inside the CAD's envelopes ([spec](docs/specs/2026-10-21-the-drone-view.md), [plan](docs/plans/2026-10-21-the-drone-view.md), [log](docs/log/2026-10-21-the-drone-view.md)). |

### Step 1, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 1a. Talk | Settle the power and battery math, the sag model, the parts catalog and the report | Done, 2026-10-17 | Eight questions settled, from the power model to which setup sizes the drone ([log](docs/log/2026-10-17-sizing-model-talk.md), [spec](docs/specs/2026-10-13-phase-1-simulation.md#settled-in-the-sizing-model-talk)) |
| 1b. Plan | Update the spec, then write the implementation plan | Done, 2026-10-17 | 15 test-first tasks, with every flight streaming into Rerun from task 10 on ([plan](docs/plans/2026-10-17-sizing-model.md)) |
| 1c. Build | Test-first, in Python. The first answer: the mass budget for every setup | Done, 2026-10-17 | All 15 tasks, 163 tests. The honesty check trusts the battery model and says cruise runs optimistic, maybe up to 2x ([log](docs/log/2026-10-17-first-real-sweep.md), [honesty check](docs/reports/sizing/validation.md)) |
| 1d. Pick the parts | Research and add the real parts, run the sweep, choose the parts and the growth margin, with uncertainty bands | Done, 2026-10-17 | 192 real builds, 76 pass with my firmware's current cap. I picked the lightest that passes every setup over the most robust (660 g heavier, Max over its limit). Growth margin stays 200 g ([decisions](docs/decisions.md), [report](docs/reports/sizing/README.md)) |
| Thrust stand | One motor and prop on a load cell, to replace the manufacturer's numbers | Optional | |

### Step 2, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 2a. Talk | Settle how the parts get modeled, the layout, the checks and what comes out | Done, 2026-10-17 | Seven questions settled, from where the shapes come from to the wires. Battery underneath, modules on top ([log](docs/log/2026-10-17-cad-talk.md), [spec](docs/specs/2026-10-13-phase-1-simulation.md#settled-in-the-cad-talk)) |
| 2b. Plan | Every part's dimensions and existing CAD checked, then the implementation plan | Done, 2026-10-17 | Six of the build's parts have official 3D files; the frame has no drawing at all, so it gets traced from iFlight's renders ([plan](docs/plans/2026-10-17-cad.md)) |
| 2c. Build | Test-first, in build123d: every part, the assembly, the checks, Rerun and the exports | Done, 2026-10-18 | The frame traced from iFlight's render; the first checks failed every combination and the fixed layout passes all eight ([log](docs/log/2026-10-18-cad-build.md)) |
| 2d. Close the loop | The CAD's weights back into the sizing model, and the targets rechecked | Done, 2026-10-18 | The printed parts went into the catalog. Mission's pessimistic hover is 21.6 min against 21, and Max is 2493 g against 2500: everything passes, with almost no room left |

### Step 3, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 3a. Talk | Settle where the design lives, the flight controller, the module bus, power, the motor cut, the checks and watching it | Done, 2026-10-18 | Eight questions settled. The surprise: the ESC firmware holds the last throttle for half a second when its signal disappears, so the safety monitor now sends stop frames instead of just disconnecting the lines ([log](docs/log/2026-10-18-electrical-talk.md), [spec](docs/specs/2026-10-18-electrical.md#settled-in-the-electrical-talk)) |
| 3b. Plan | The new parts researched (a DroneCAN GPS, servo nodes, the multiplexers, connectors and fuses), then the implementation plan | Done, 2026-10-18 | 14 test-first tasks. The lightest DroneCAN GPS is 8 g over the old one, and with the servo nodes Max will land around 2514 g, over its limit ([plan](docs/plans/2026-10-18-electrical.md)) |
| 3c. Build | Test-first: the connection list, the ARK FPV swap, the checks, the generators (WireViz, pin maps, KiCad), ngspice, Rerun and the report | Done | The connection list passes every rule in all eight combinations, and the checks found real problems: the cell fuse links can't work at 90 A (they're out), the release servo sits under its range, and the XT60 overheats through a long burst ([log](docs/log/2026-10-18-electrical-checks.md)). Tasks 8 to 12: ngspice shows the safety monitor's switch passing DShot with the Teensy on, off and cutting; the harness diagrams, pin maps and a clean KiCad schematic come from the list; Rerun shows every wire by how hard it works ([log](docs/log/2026-10-18-electrical-sims.md)). Task 13: `pcs14 electrical` runs all of it and writes [the report](docs/reports/electrical/README.md) ([log](docs/log/2026-10-19-electrical-report-and-weight.md)) |
| 3d. Close the loop | The new parts' weights back into the CAD and the sizing model, with Max only 7 g under its limit | Done, 2026-10-19 | The wiring weighs 59.7 g in Base (the guess was 45) and the screws 37 g, so the fuses are soldered inline and the cells are Molicel P45B: Mission is 2414 g and passes at 22.25 min pessimistic hover. The release servo runs through an ideal-diode OR, the Pi's 5 V is checked against USB's 5.25 V, and my firmware gets a heat limit for the XT60, so the report passes ([log](docs/log/2026-10-19-electrical-report-and-weight.md)) |

### Step 4, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 4a. Talk | Settle the versions, the air, the battery, what passing means, the runner and where it runs | Done, 2026-10-19 | PX4 v1.17.0 on Gazebo Harmonic, a drag plugin of our own, motors topping out at the sizing model's worst case, and a pass/fail table ([log](docs/log/2026-10-19-flight-sim-talk.md), [spec](docs/specs/2026-10-19-flight-sim.md#settled-in-the-flight-sim-talk)) |
| 4b. Plan | The implementation plan | Done, 2026-10-19 | 12 test-first tasks; the first eight need only Windows ([plan](docs/plans/2026-10-19-flight-sim.md)) |
| 4c. Build | Test-first: the targets, the motor fit, the drag math, the generator, power, the triggers, grading and the report, then the setup, the runner and every scenario | Done, 2026-10-20 | All twelve scenarios fly in all eight combinations, 78 runs ([scenarios](docs/log/2026-10-20-flight-sim-scenarios.md), [the last batch](docs/log/2026-10-20-flight-sim-final.md)). Runs spoiled by the PC's load at 4x were flown again alone, and passed |
| 4d. Close the loop | The sim's results against the sizing model, the false-trigger counts against the thresholds | Done, 2026-10-20 | Hover times agree with the sizing model to 0.1 min in all eight; cruise runs 25% shorter (Gazebo's rotors don't gain from forward flight). No false triggers in 66 runs; the free-fall trigger catches a real failure in about half a second ([log](docs/log/2026-10-20-flight-sim-final.md)) |

### Step 5, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 5a. Talk | The language, the shape of the code, how it talks to the flight sim, the estimator, the safety monitor | Done, 2026-10-20 | C++17, a hardware-free core, PX4's MAVLink dialect and ULog, Mahony's filter first ([spec](docs/specs/2026-10-20-firmware.md)) |
| 5b. Plan | The implementation plan | Done, 2026-10-20 | 13 test-first tasks, from the build to a ground station ([plan](docs/plans/2026-10-20-firmware.md)) |
| 5c. Build | Test-first, task by task | Done, 2026-10-20 | All 13 tasks: the core (Mahony's filter, the PIDs, the mixer, the height and position filters, the modes, PX4's failsafes, the geofence, pre-arm checks that include the safety monitor, the fuel gauge), the sim layer, the safety monitor on its own IMU, the ARK FPV's drivers as far as host tests go (the clock tree, the watchdog, the compass and barometer, DroneCAN, the SD card), and the ground station, which talked to the firmware flying in the sim. Every scenario in every combination: 66 of 78, against PX4's 62 ([log](docs/log/2026-10-20-firmware-flies.md)). The register-level drivers wait for a bench board |

### Step 6, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 6a. Spec | What steps 4 and 5 already covered, and what's left for each module | Done, 2026-10-20 | The monitor fires the chute only on the pilot's switch while its triggers stay in shadow mode; the opening jolt gets the sim's number and the textbook bound; HaLow from the chip maker's numbers ([spec](docs/specs/2026-10-20-modules-in-sim.md)) |
| 6b. Plan | The implementation plan | Done, 2026-10-20 | 12 test-first tasks, the new scenarios on my firmware only ([plan](docs/plans/2026-10-20-modules-in-sim.md)) |
| 6c. Build | Test-first, task by task | Done, 2026-10-20 | All 12 tasks: the monitor's chute, the hung flight controller, the drop heights, the opening jolt (the sim's 2 g, the textbook's 8 to 12 g), the parachute rule holding at 30 m, no false triggers in 72 healthy runs, HaLow's model and its relay, the camera, the video at the link's rate, the companion computer, and `pcs14 modules` writing the report ([log](docs/log/2026-10-20-modules-in-sim.md)) |

### Step 7, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 7a. Spec | What each of the twelve features can be in the sim with the tools the PC has | Done, 2026-10-20 | A local model for the missions, orthomosaics from known poses, safe spots on a height map, optical flow and the rangefinder for GPS-free flight, a local vision model for detection ([spec](docs/specs/2026-10-20-smart-features.md)) |
| 7b. Plan | The implementation plan | Done, 2026-10-20 | 13 test-first tasks, the new scenarios on my firmware only ([plan](docs/plans/2026-10-20-smart-features.md)) |
| 7c. Build | Test-first, task by task | Done, 2026-10-21 | All 13 tasks: the landing modes, the wind and the turn-back warning, self-tuning (from doublets, after the steps failed), a plain-English mission flown, the spiral, the lift detector, the mapping run, the safe-spot landing, change detection, the GPS-free estimate, object detection, and `pcs14 smart` writing the report ([log](docs/log/2026-10-21-smart-features.md)) |


### Step 8, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 8a. Spec | What a build package needs and where each part of it comes from | Done, 2026-10-21 | Generated from the catalog and the reports, every bought part with a link, a price and a fallback, PX4 first, test plans with pass criteria, the unproven list carrying its measurements ([spec](docs/specs/2026-10-21-build-package.md)) |
| 8b. Plan | The implementation plan | Done, 2026-10-21 | 9 test-first tasks ([plan](docs/plans/2026-10-21-build-package.md)) |
| 8c. Build | Test-first, task by task | Done, 2026-10-21 | All 9: the catalog's fallbacks and the parts research, the parts list, the assembly and wiring guides, the firmware guide, the test plans, the legal checklist, the unproven measurements, and `pcs14 package` with the site's Build it page ([log](docs/log/2026-10-21-build-package.md)) |
## Modules

The frame is designed to carry everything, but it flies bare first. Modules go on depending on the day.

| | Module | What's in it |
|---|---|---|
| **V** | Vision & nav | GPS, camera, companion computer, long-range video link |
| **P** | Parachute | The chute and its ejector |
| **C** | Claws | Grabby bits, if I come up with a unique claw on an actual arm |

## How I'm designing it

Simulate everything, with real parts. The parts catalog and the CAD drive every simulation, so changing a part reruns everything downstream. The layers:

1. **Sizing model.** Will it lift, and for how long? (Python)
2. **CAD, as code.** Does it all fit, how does it connect, and where does it balance? (build123d)
3. **Electrical.** Every wire, pin and connector, and whether the currents, voltages and heat stay inside their ratings. (KiCad, WireViz, ngspice)
4. **Structure.** Will the arms bend, or buzz at the wrong frequency? (FreeCAD with CalculiX)
5. **Virtual wind tunnel.** What does the air actually do around it? (OpenFOAM, plus FluidX3D for the pretty spinning-prop runs)
6. **Flight sim.** Can the airframe fly? PX4 flies it in Gazebo to find out.
7. **My firmware in the sim.** Can *my* code fly it?

The design is a plain X quad, and it's what the build package describes. In the background, an automated loop that builds, tests and improves designs keeps hunting for one that's actually unique. Whatever it finds becomes v2.

## How it fits together

```
LAPTOP              map · telemetry · LLM assistant · object detection · mission approval · 3D maps
   │  data + video link (HaLow)
COMPANION COMPUTER  cameras · GPS-free navigation
   │
FLIGHT CONTROLLER   sensors · PID · motors · failsafes · self-tuning
   │                (my RC transmitter plugs in here and always wins)
4-in-1 ESC → 4 motors          + independent safety monitor (kill switch, parachute)
```

Each layer has to stay safe if the one above it dies.

## Finding your way around

- [STATUS.md](STATUS.md): what I'm doing right now
- [docs/roadmap.md](docs/roadmap.md): the plan, step by step
- [docs/decisions.md](docs/decisions.md): every decision so far, and why
- [docs/learning.md](docs/learning.md): everything I'm learning along the way, with the resources I'm using
- [docs/style.md](docs/style.md): how everything is supposed to look
- [docs/specs/](docs/specs/): detailed designs, written before the work starts
- [docs/plans/](docs/plans/): implementation plans, one per build step, task by task
- [docs/setup-pc.md](docs/setup-pc.md) and [docs/machines/](docs/machines/): setting up a machine, and what each one has
- [docs/log/](docs/log/): the build log, roughly one entry per session

## License

[GPL-3.0](LICENSE). Take it, build on it, share what you make.
