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
| Setup | WSL2 on the PC, with all checks passing | Up next | |
| 1. Sizing and parts | Real, orderable parts that hit the targets | Done, 2026-10-17 | Emax 2814 850KV motors, Gemfan 10x5 props, a 6S2P Molicel P42A pack and a Nazgul XL10 frame. Every setup passes, Max included: 25.7 min hover with Mission's loadout at 2254 g ([report](docs/reports/sizing/README.md), [log](docs/log/2026-10-17-first-real-sweep.md)) |
| 2. The virtual drone (CAD) | Every part modeled and connected | Done, 2026-10-18 | Every part modeled and every module combination passing its checks, with the real weights back in the sizing model: Mission 2293 g, still passing ([report](docs/reports/cad/README.md), [log](docs/log/2026-10-18-cad-build.md)) |
| 3. Electrical design | Every wire, pin and connector | Done, 2026-10-19 | One connection list behind every check, diagram and the schematic: 438 checks pass in all eight combinations, and ngspice shows the safety monitor's switch working. Weighing the real wiring and hardware moved the cells to P45B: Mission is 2414 g with a 22.25 min pessimistic hover ([report](docs/reports/electrical/README.md), [log](docs/log/2026-10-19-electrical-report-and-weight.md)) |
| 4. Flight sim (PX4) | Prove the airframe flies, in all eight module combinations | In progress | The talk and the plan are done ([spec](docs/specs/2026-10-19-flight-sim.md), [plan](docs/plans/2026-10-19-flight-sim.md)). Next is the build |
| 5. My firmware | My flight code and the safety monitor, passing the same tests as PX4 | Not started | |
| 6. Modules in sim | Parachute, vision & nav, and claws if they happen | Not started | |
| 7. Smart features in sim | Mapping, safe spots, the LLM, object detection, soar mode, the spiral descent and more | Not started | |
| 8. Build package | Parts list, assembly and wiring guides, test plans, and the unproven list | Not started | |

| Side track | Starts after | Status | Outcome |
|---|---|---|---|
| Structure | Step 2 | Not started | |
| Aero (the wind tunnel) | Step 2 | Not started | |
| Design hunt (v2) | Step 4 | Not started | |
| Project site | Step 1 | Not started | Stays on my machine until the project is done, then joins my portfolio site |

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
| 4c. Build | Test-first: the targets, the motor fit, the drag math, the generator, power, the triggers, grading and the report, then the setup, the runner and every scenario | In progress | Tasks 1 to 10 done ([log](docs/log/2026-10-19-flight-sim-build.md), [first flight](docs/log/2026-10-19-first-flight.md)). Task 11 mostly done: all twelve scenarios fly; most pass, and three misses are real findings (no chute means a dead motor crashes, no GPS means a blind descent, cruise endurance disagrees with the sizing model) ([log](docs/log/2026-10-20-flight-sim-scenarios.md)). Next: finish the 78-run batch, then the report |
| 4d. Close the loop | The sim's results against the sizing model, the false-trigger counts against the thresholds | Not started | |

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
