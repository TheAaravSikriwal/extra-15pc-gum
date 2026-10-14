# Extra 15pc Gum

I'm building a long-range quadcopter from scratch: my own flight firmware, parts I can actually order, and nothing gets bought until it has flown in simulation first. This repo is all of it. The plan, the code, the mistakes, out in the open.

Yes, it's named after a pack of gum. It made sense at the time.

**Where it's at:** planning is done, and Phase 1 (simulating the baseline) is starting. [The plan](#the-plan) below shows every step and what came out of it. [STATUS.md](STATUS.md) has today's details, and the [roadmap](docs/roadmap.md) has the rest. It will change.

## What it's going to do

- **Fly for a long time.** 8–10" props, low-KV motors and a Li-ion pack, aiming for 25–40 minutes of cruising.
- **Run on my code.** A flight controller I'm writing myself, on an STM32H743.
- **Land where I tell it.** Back where it took off, a spot I click on the map, right where it is, or the nearest safe spot it found on a 3D map of the area.
- **Not fall out of the sky.** Failsafes for lost signal, low battery and lost GPS, plus a parachute fired by a separate little computer that doesn't trust my main firmware either.
- **See and find its way.** Camera and GPS, mapping runs, and getting home on the camera alone if GPS drops.
- **Get smarter.** It tunes itself, and takes missions in plain English from an LLM on my laptop. The LLM makes the plan. It never touches the motors.

## The plan

This is the live version. When a step finishes, its outcome goes here, with a link to the details. The reasons behind each phase are in the [roadmap](docs/roadmap.md) and [decisions.md](docs/decisions.md).

| Phase | What it's for | Status | Outcome |
|---|---|---|---|
| 0. Planning | Figure out what I'm building | Done, 2026-10-14 | Decisions, targets and roadmap written, reviewed and revised ([log](docs/log/2026-10-14-plan-revision.md)) |
| 1. Simulate the baseline | Prove the plain X works, with real thrust data | In progress | |
| 2. My firmware in sim | The flight code and the safety monitor, in sim and on the real chip | Not started | |
| 3. Bench build | Build the bare drone, props off | Not started | |
| 4. First flights | PX4 flies it first, then my firmware | Not started | |
| 5. Module P | Parachute | Not started | |
| 6. Module V | GPS, camera, companion computer, HaLow video | Not started | |
| 7. Smart features | Mapping, safe spots, the LLM, self-tuning, soar mode, the spiral descent and more | Not started | |
| 8. Module C | Claws, if I come up with a unique claw on an arm | Not started | |
| 9. Extras | A wristband, and whatever else makes the cut | Not started | |
| 10. v2 | Whatever the design hunt finds, if it's worth building | Not started | |

### Phase 1, step by step

| Step | What happens | Status | Outcome |
|---|---|---|---|
| 1. PC setup | The PC's Ubuntu side, from nothing to all checks passing | Up next | |
| 2. Sizing model: talk | Settle the power and battery math, the sag model, the parts catalog and the report | Up next | |
| 3. Sizing model: plan | Update the spec, then write the implementation plan | Not started | |
| 4. Sizing model: build | Test-first, in Python. The first answer: does the fully loaded drone fit under 2.5 kg? | Not started | |
| 5. Thrust stand | One motor, a few props and the ESC on a load cell, running off a real 6S pack | Not started | |
| 6. Setup script | Gazebo, PX4 and the Python tools, at pinned versions | Not started | |
| 7. CAD | The plain X in build123d: does it fit, where does it balance, plus meshes and renders | Not started | |
| 8. Gazebo + PX4 | The model generator and every test scenario | Not started | |
| 9. Baseline passes | Tag it, price it, order the parts | Not started | |

Running alongside, without blocking anything: the CFD wind tunnel and the design hunt. Their outcomes show up here too once they have some.

## Modules

The frame is built to carry everything, but it flies bare first. After that I bolt on whatever the day needs.

| | Module | What's in it |
|---|---|---|
| **V** | Vision & nav | GPS, camera, companion computer, long-range video link |
| **P** | Parachute | The chute and its ejector |
| **C** | Claws | Grabby bits. Coming eventually. |

## How I'm building it

Simulate first, buy later. Five layers:

1. **Sizing model.** Will it lift, and for how long? (Python, with real numbers from a thrust stand)
2. **CAD, as code.** Does it all fit, and where does it balance? (build123d)
3. **Virtual wind tunnel.** What does the air actually do around it? (OpenFOAM, plus FluidX3D for the pretty spinning-prop runs)
4. **Flight sim.** Can the airframe fly? PX4 flies it in Gazebo to find out.
5. **My firmware in the sim.** Can *my* code fly it?

The first design is a plain X quad. It has to pass the sizing model, the CAD and the flight sim before any real money changes hands, and then it's the one I build and fly. The wind tunnel runs alongside and keeps sharpening the numbers. So does an automated loop that builds, tests and improves designs, hunting for one that's actually unique. Whatever it finds becomes v2.

## How it fits together

```
LAPTOP              map · telemetry · LLM assistant · mission approval · 3D maps
   │  data + video link
COMPANION COMPUTER  cameras · GPS-free navigation
   │
FLIGHT CONTROLLER   sensors · PID · motors · failsafes · self-tuning
   │                (my RC transmitter plugs in here and always wins)
4-in-1 ESC → 4 motors          + independent safety monitor (kill switch, parachute)
```

Each layer has to stay safe if the one above it dies.

## Finding your way around

- [STATUS.md](STATUS.md): what I'm doing right now
- [docs/roadmap.md](docs/roadmap.md): the plan, phase by phase
- [docs/decisions.md](docs/decisions.md): every decision so far, and why
- [docs/learning.md](docs/learning.md): everything I'm learning along the way, with the resources I'm using
- [docs/style.md](docs/style.md): how everything is supposed to look
- [docs/specs/](docs/specs/): detailed designs, written before I build things
- [docs/setup-pc.md](docs/setup-pc.md) and [docs/machines/](docs/machines/): setting up a machine, and what each one has
- [docs/log/](docs/log/): the build log, roughly one entry per session

## License

[GPL-3.0](LICENSE). Take it, build on it, share what you make.
