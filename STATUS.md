# Status

**Last updated:** 2026-10-20, on the PC (Windows and WSL2 Ubuntu)
**Step:** step 4, the flight sim, finishing: the final batch of all 78 runs is flying. Step 5, my firmware, has started alongside it: the spec and plan are written and tasks 1 to 3 are done (2026-10-20).
**Main machine:** the PC, with WSL2 Ubuntu 24.04 for the Linux tools

## Right now

**It's a research project now (2026-10-17).** Instead of buying parts and building the drone, I'm designing the whole thing in simulation: every real part modeled and connected, the wiring worked out, and my firmware flying it in the sim. The goal is a build package complete enough to build from one day, plus an honest list of what the simulations can't prove. Nothing gets bought by default. The thrust stand and a Nucleo board are optional extras.

Where to look:
- **The live plan:** the [README](README.md#the-plan), with each step's outcome filled in as it finishes
- **The steps in detail:** the [roadmap](docs/roadmap.md)
- **Every decision and why:** [docs/decisions.md](docs/decisions.md)
- **Steps 1, 2 and 4 in depth:** [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md)
- **The earlier revision (R1 to R7):** [docs/specs/2026-10-14-plan-revision.md](docs/specs/2026-10-14-plan-revision.md)

**The PC runs the Linux tools in WSL2 now** (decided 2026-10-17), so there's no rebooting into the Ubuntu side, and it matches the laptop. The native Ubuntu side is a fallback. WSL isn't installed on the PC yet; [docs/setup-pc.md](docs/setup-pc.md) walks through it.

**Step 1a is done (2026-10-17).** The sizing model talk settled eight questions, all in the spec under "Settled in the sizing model talk": the power model, the battery model, the catalog format, which parts go in first, the outputs (a Markdown report, Rerun replays of every test, and the project site), the code as one package called 14 pcs left (`pcs14` in the code), and Mission plus a 200 g growth margin as the setup that sizes the drone. The [log](docs/log/2026-10-17-sizing-model-talk.md) has the story.

**Step 1c is done (2026-10-17).** The sizing model (`pcs14`) works end to end: `pcs14 size`, `sweep`, `report` and `validate`, with every flight playable in Rerun. The honesty check says the battery model is good and the cruise numbers run optimistic, maybe up to 2x, so hover is the number to trust for now.

**The first real sweep (2026-10-17).** Six real motors, seven props, four cells, two frames: 192 builds. At first, the rule that full throttle has to fit the pack's continuous rating forced a third parallel cell (and 400 g) on everything. So my firmware caps the battery current at the rating now, and 76 builds pass. The most robust is a Hobbywing 3115 on HQ 10x5 props with a 6S3P P45B pack (35.1 min hover with Mission's loadout, 2914 g); the lightest that passes every setup, Max included, is an Emax 2814 on Gemfan 1050 props with a 6S2P P42A pack (2254 g). The [report](docs/reports/sizing/README.md), the [log](docs/log/2026-10-17-first-real-sweep.md), and [decisions](docs/decisions.md) have the details.

**Step 1 is done (2026-10-17).** I picked the lightest build that passes every setup, Max included: Emax E3 2814 850KV motors, Gemfan 1050 tri-blades, a 6S2P Molicel P42A pack, the Tekko32 F4 50A ESC and the Nazgul XL10 frame, with my firmware capping the current at 90 A. Mission hovers 25.7 min (22.2 pessimistic) at 2254 g, and Max weighs 2454 g. The growth margin stays 200 g. "The parts" in [decisions](docs/decisions.md) has the full picture, including the catch: thin margins, and cruise numbers that are probably optimistic.

**Step 2 is done (2026-10-18).** `pcs14 cad` builds the whole drone, checks all eight module combinations (collisions, prop clearance, the parachute's cone, the rail, balance with the pack trimmed, the compass and Remote ID rules, the lidar's view), compares parts with existing CAD models, exports STEP, meshes, a GLB and print files, renders stills, and plays it all in Rerun. The first checks failed every combination; the fixed layout passes all eight. The printed parts' real weights went back into the catalog: Mission is 2293 g and still passes, with almost no margin left. The [CAD report](docs/reports/cad/README.md) and the [log](docs/log/2026-10-18-cad-build.md) have the details.

**Step 3a, the electrical talk, is done (2026-10-18).** Eight answers, all in the [electrical spec](docs/specs/2026-10-18-electrical.md): one connection list in code generates every diagram and check; the ARK FPV replaces the Kakute H7; DroneCAN plus a serial line for the modules; the frame's XT60 with no main fuse (fused branches, a fuse link on each cell); one BEC for the Pi and the modules; the safety monitor takes over the ESC lines and sends stop frames, because AM32 holds the last throttle for half a second when its signal just disappears; 80% of every rating, with a 10 s burst at the 90 A cap for heat; and Rerun with the wires colored by current. The [log](docs/log/2026-10-18-electrical-talk.md) has the story.

**Step 3b, the electrical plan, is done (2026-10-18).** The research picked the parts (the ARK GPS on DroneCAN, ARK CANnodes in P and C, a TI TS3A5018 board for the motor cut, single-gate buffers that stay quiet when the Teensy is off) and the 14 tasks. The catch: the lightest DroneCAN GPS is 8 g over the old one, so with the servo nodes Max lands around 2514 g, over its limit. The [log](docs/log/2026-10-18-electrical-plan.md) has the story.

**Step 3c is done (2026-10-18 to 19).** All 13 tasks. Since the checks: every wire has a CAD route sized from its bundle; ngspice shows the safety monitor's switch passing DShot with the Teensy on and unpowered, handing the ESC stop frames when cutting, and losing one frame in a mid-frame takeover; WireViz harnesses, pin maps, the power tree and a KiCad schematic (rules check clean) all come from the connection list; and Rerun shows every wire by how hard it works. The sims added a firmware requirement: after a takeover the Teensy holds the line high between frames. The [log](docs/log/2026-10-18-electrical-sims.md) has the story. The connection list (`design/electrical.yaml`, 33 boards, 128 wires, 27 safety paths) passes every rule in all eight combinations; every wire's current comes from a DC solve; and the checks cover connectors, supplies, voltages, fuses, heat, the ESC and motors, and a backup case with the module supply dead. The cell fuse links came out (none can work at 90 A). Open findings: the release servo sits under its range through its diode, the Pi's 5.2 V crowds a guessed ceiling, and the XT60 overheats through a 10 s burst on a guessed contact mass. The logs: [part 1](docs/log/2026-10-18-electrical-build.md), [the checks](docs/log/2026-10-18-electrical-checks.md). Task 13 made `pcs14 electrical` run all of it in about 26 s and write [the electrical report](docs/reports/electrical/README.md): 438 checks, 8 of them the open findings.

**Step 3d is done (2026-10-19).** `pcs14 electrical --update-catalog` weighs the wiring from the connection list (59.7 g in Base against the 45 g guess), and the main path is 3.8 mOhm. The branch fuses are now soldered inline (5 g off). The screws, nuts and spacers are a list in `design/cad.yaml`, counted from the CAD's holes: 37 g with steel where it carries load and nylon elsewhere. That's more than any trim could absorb, so the cells are Molicel P45B now (same size and rating, 42 g heavier). Mission is 2414 g with a pessimistic hover of 22.25 min against 21, and passes; Max is 2623 g (report-only). The release servo's diodes are now an ideal-diode OR (an LM66200), which lifts it to 5.16 V, and 4.92 V on its backup. The Pi's 5.185 V is checked against USB's 5.25 V without the margin, since Raspberry Pi publishes no maximum. And my firmware's current cap gets a heat limit on the XT60 (full current for 3.1 s from Max's hover, then easing toward the 29 A it holds forever), so **the electrical report passes: 438 checks, nothing missing. Step 3 is done.** C's socket and the fuses also moved onto the frame's plates, because touching along a bare edge broke the CAD's body for the wind tunnel. The [log](docs/log/2026-10-19-electrical-report-and-weight.md) has the story.

**The parts research added two missing parts (2026-10-17).** The camera needs a 22-pin cable for the Pi 5, and the HaLow card comes with no antenna, so both went into module V (14 g together). Mission is now 2268 g and hovers 25.5 min (21.9 pessimistic, against 21), and Max is 2468 g. Everything still passes, with a thinner margin.

**The CAD talk is done (2026-10-17).** Seven answers, all in the spec under "Settled in the CAD talk": I model every part myself from published dimensions, after checking whether a CAD model of it already exists; battery underneath and modules on top, so the chute fires straight up; real printable designs for our own brackets, legs, tray and rail; check limits based on what each one costs; Rerun and styled stills for watching; STEP, meshes, a GLB for the site and print files on every run, with `cad.json` committed; and rough wire routes now. The [log](docs/log/2026-10-17-cad-talk.md) has the story.

**Step 4a and 4b, the flight sim talk and plan, are done (2026-10-19).** PX4 v1.17.0 on Gazebo Harmonic, pinned; a small drag plugin of our own for body drag, wind and the parachute; each motor topping out at the sizing model's worst case (the reserve, the 90 A cap); a pass/fail table in the targets; MAVSDK-Python flying the scenarios headless; a Python reference for the safety monitor's triggers; PX4 unmodified. The [spec](docs/specs/2026-10-19-flight-sim.md), the [plan](docs/plans/2026-10-19-flight-sim.md) (12 tasks, the first eight Windows-only) and the [log](docs/log/2026-10-19-flight-sim-talk.md). From here on, routine choices get made and written down, and only drastic ones get asked.

**Step 4c, tasks 1 to 8, are done (2026-10-19).** The targets, the motor model fit, the drag and parachute math, the generator, power from logged rotor speeds, the safety monitor's reference triggers, grading, and the report. `pcs14 flight-sim` writes all eight Gazebo models and the [flight sim report](docs/reports/flight-sim/README.md): 78 scenario runs planned, none flown until PX4 is installed. Mission flies at 2213 g (the CAD's weight, without the growth margin) and should hover at 58% throttle. The [log](docs/log/2026-10-19-flight-sim-build.md).

**Step 4c, tasks 9 and 10, are done (2026-10-19): PX4 flies it.** Ubuntu is in WSL2 on the PC, and `scripts/setup-ubuntu.sh` installed PX4 v1.17.0, Gazebo Harmonic (8.15.0), MAVSDK 3.17.4, pyulog 1.2.4 and our drag plugin. It now fetches only the simulator's submodules, after the full clone crawled at 60 kB/s. `pcs14 flight-sim run` starts Gazebo headless, PX4 standalone and stock with our parameters, a relay that can cut the uplink, and the scenario script on PX4's clock, then grades from Gazebo's ground truth in PX4's log. The smoke flight (take off, hover 10 s, land) in base passes: hovering at 539 rad/s as the motor model predicts, 8 cm of drift, 41 s of real time. In P, PX4's own parachute output fires the chute on flight termination. The [log](docs/log/2026-10-19-first-flight.md).

**Step 4c, task 11, mostly done (2026-10-20).** All twelve scenarios fly. Passing: hover, stick steps (after tuning PX4's attitude gain from 6.5 to 9), top speed (88 km/h), 10 m/s wind, lost link, low battery (home with 29% left), the parachute drop, a dead motor with P, the sagging pack, the payload grab. Not passing, and why: **a dead motor without P is a crash** (a quad can't fly on three motors); **losing GPS means a blind descent** that drifts 34 to 38 m in calm air (no optical flow sensor); **cruise endurance disagrees with the sizing model by about 25%** (Gazebo's rotors don't gain from forward flight; the sizing model's do). Fixed on the way: the chute was on PX4's landing gear output (400, not 401) and opened on take-off. The [log](docs/log/2026-10-20-flight-sim-scenarios.md).

**The first wind tunnel visuals (2026-10-20).** FluidX3D on the RTX 3060: the drone (every module on) at 10 m/s, streamlines and shed vortices, 60 million cells, four minutes a run. FluidX3D lives in `C:\dr\fluidx3d` (altered source, committed locally; it needs its public fork before any picture is posted). Its drag reads about 230 cm² against the sizing model's 202, but that's visual-grade. The [log](docs/log/2026-10-20-first-wind-tunnel.md).

**Step 5 started (2026-10-20).** My firmware is C++17: one core library with no hardware in it, and thin layers for the sim, the ARK FPV and the safety monitor. It speaks PX4's MAVLink dialect and writes ULog, so the flight sim's scenarios and graders work on it unchanged. Tasks 1 to 3 are done: the CMake tree with doctest and a CI job under the sanitizers, the math, Mahony's attitude filter, a PID per axis, and the quad X mixer, which gives up yaw before roll and pitch when the motors run out. 21 host tests pass. The [spec](docs/specs/2026-10-20-firmware.md) and the [plan](docs/plans/2026-10-20-firmware.md).

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Finish task 11** (picking up where I stopped):
   - A clean batch of all 78 runs was flying in WSL (`pcs14 flight-sim run --speed 4 --jobs 2`, two at a time, never four: four overloads the PC and spoils the results). Its results land in `outputs/flight-sim/results/`. If it didn't finish, rerun the missing ones the same way with `--setup` and `--scenario`. Low battery in V hung once ("PX4's clock stopped"), probably starved while the Windows tests ran: rerun it alone.
   - **Look into wind in P first.** In the batch it tumbled about 85 s into the wind (the monitor's tumble trigger at 123.2 s), PX4's failure detector terminated and fired the chute at 123.8 s, and then land was refused. Mission passed the same scenario at 1x. Fly it alone at 1x and at 4x (`--setup P --scenario wind`) to see whether it's P itself or the sped-up sim, and check the wind ramp: its marks show the wind blowing from 38 s to 155 s of sim time, far longer than the 40 s it should.
   - Regrade everything (`pcs14 flight-sim regrade`, inside WSL or on Windows) so the drop and dead-motor runs get the safety monitor's catch time.
   - Fly the before-and-after for the steps still: `pcs14 flight-sim run --setup base --scenario steps --tag x500-gains --param MC_ROLL_P=6.5 --param MC_PITCH_P=6.5 --speed 4`.
   - Then `pcs14 flight-sim report --replays` writes the report, the stills and a Rerun replay of every run. Commit the report and stills.
   - **More batch runs failed only in the batch:** steps in Mission ("never climbed"), low battery in Mission (19.7 of 20 m) and the payload grab in C (tipped over), on top of wind in P. Some overlapped the FluidX3D runs, which also load the PC. Rerun each alone, with nothing else running, before believing any of them.
2. **The wind tunnel, next:** a true side view, post-sized stills (FluidX3D's frame size is a build switch), the props spinning, and the 10 m/s crosswind. Make the public FluidX3D fork (mine to OK) before posting any of it.
3. **Task 12, closing the loop:** the report's new sections do most of it (flight times against the sizing model, false triggers, the monitor's catch times, why each miss misses). Write it up, and decide what the three design findings mean (below).
4. **The project site's spec** (what it's built with). The goal is written down in decisions: a complete blueprint, from the structure to the circuits.
2. **The project site's spec** (what it's built with). The goal is written down in decisions: a complete blueprint, from the structure to the circuits.

## Still open

- **Decisions the flight sim raised (mine to make):** should P (the chute) be in every combination, since a dead motor without it loses the drone? Should Base get an optical flow sensor, so a GPS failure isn't a blind descent? Both change the parts list and the weight.

- Rotor drag in forward flight, so the cruise numbers get believable (the honesty check's big miss)
- The weight: Mission passes at 22.25 min pessimistic hover with 1.25 min to spare; Max is 2623 g against its own 2500 g target (report-only)
- Not counted yet: how the ARK GPS fixes to its plate and how the modules lock onto the rail
- The sizing model's capped full-throttle point scales from the thrust table's top row with a power law, which lands its rpm about 4% off the table itself; the flight sim matches thrust instead
- **Mine to do:** ask Fruity Chutes for the Harrier release servo's voltage range and draw. The design runs on a stand-in (Hitec's HS-55, 4.8 to 6 V)
- The XT60's contact mass (a 2.5 g guess): the firmware's heat limit and the burst check both rest on it
- The pack's own nickel strip and leads aren't in its 3.8 mOhm wiring number
- What the motor cut board's two undocumented 1 kOhm resistors do (pull-ups would make the board fail the wrong way)
- Whether a safety monitor cut can be undone in the air (step 5), and the delay between cutting the motors and firing the chute (step 6)
- Whether the HaLow HAT works on a Pi 5 (Heltec lists Pi 1 to 4), and which 915 MHz antenna to use
- Cruise speed: 10 m/s until the sizing model says otherwise
- Which OpenFOAM: the Foundation release or ESI's. Decided when writing the CFD half of the setup script.
- Companion computer and camera (step 6). HaLow is the lead option for the video link.
- Where the Meshtastic relay (#30) lives: V, Base, or its own little module
- Exactly what goes in the `us-recreational` limits profile, and whether to get Part 107 (for the build package)
- What "unique" is allowed to mean in the design hunt
- OpenGL inside WSL runs on the CPU (llvmpipe), not the RTX 3060. Headless flights don't care; Gazebo's window and clips for posts will
- MAVSDK-Python 3.17.4 warns that its package name now belongs to a new native binding; the API I use continues as `mavsdk-grpc`. Pinned for now, and a move is its own small decision
- What the project site is built with (it stays on my machine until the project is done, then joins my portfolio at wearechintu.com)

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Windows 11 + **WSL2 Ubuntu 24.04** (dual boot, native Ubuntu as a fallback), Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060 | Main machine: sim, CFD, CAD, renders | WSL2 Ubuntu 24.04 with the flight sim's tools ([pc.md](docs/machines/pc.md)). The repo is at `C:\dr\extra-15pc-gum`. |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station, object detection | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now. |

## Switching machines

Pull when you sit down, push when you get up. Update this file, the README's plan and the log before you push.
