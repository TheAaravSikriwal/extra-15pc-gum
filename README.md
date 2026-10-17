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
| 1. Sizing and parts | Real, orderable parts that hit the targets | Up next | |
| 2. The virtual drone (CAD) | Every part modeled and connected | Not started | |
| 3. Electrical design | Every wire, pin and connector | Not started | |
| 4. Flight sim (PX4) | Prove the airframe flies, in all eight module combinations | Not started | |
| 5. My firmware | My flight code and the safety monitor, passing the same tests as PX4 | Not started | |
| 6. Modules in sim | Parachute, vision & nav, and claws if they happen | Not started | |
| 7. Smart features in sim | Mapping, safe spots, the LLM, object detection, soar mode, the spiral descent and more | Not started | |
| 8. Build package | Parts list, assembly and wiring guides, test plans, and the unproven list | Not started | |

| Side track | Starts after | Status | Outcome |
|---|---|---|---|
| Structure | Step 2 | Not started | |
| Aero (the wind tunnel) | Step 2 | Not started | |
| Design hunt (v2) | Step 4 | Not started | |

### Step 1, in detail

| Part | What happens | Status | Outcome |
|---|---|---|---|
| 1a. Talk | Settle the power and battery math, the sag model, the parts catalog and the report | In progress | Settled so far: real thrust tables for hover, a fitted forward-flight model for cruise, and a battery model with sag ([spec](docs/specs/2026-10-13-phase-1-simulation.md#settled-in-the-sizing-model-talk)) |
| 1b. Plan | Update the spec, then write the implementation plan | Not started | |
| 1c. Build | Test-first, in Python. The first answer: does the fully loaded drone fit under 2.5 kg? | Not started | |
| 1d. Pick the parts | Run the sweep and choose real parts, with uncertainty bands | Not started | |
| Thrust stand | One motor and prop on a load cell, to replace the manufacturer's numbers | Optional | |

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
- [docs/setup-pc.md](docs/setup-pc.md) and [docs/machines/](docs/machines/): setting up a machine, and what each one has
- [docs/log/](docs/log/): the build log, roughly one entry per session

## License

[GPL-3.0](LICENSE). Take it, build on it, share what you make.
