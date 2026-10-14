# Extra 15pc Gum

I'm building a long-range quadcopter from scratch: my own flight firmware, parts I can actually order, and nothing gets bought until it has flown in simulation first. This repo is all of it. The plan, the code, the mistakes, out in the open.

Yes, it's named after a pack of gum. It made sense at the time.

**Where it's at:** Phase 1, simulating the design. [STATUS.md](STATUS.md) is always the current version. The [roadmap](docs/roadmap.md) has the rest, and it will change.

## What it's going to do

- **Fly for a long time.** 8–10" props, low-KV motors and a Li-ion pack, aiming for 25–40 minutes of cruising.
- **Run on my code.** A flight controller I'm writing myself, on an STM32H743.
- **Land where I tell it.** Back where it took off, a spot I click on the map, right where it is, or the nearest safe spot it found on a 3D map of the area.
- **Not fall out of the sky.** Failsafes for lost signal, low battery and lost GPS, plus a parachute fired by a separate little computer that doesn't trust my main firmware either.
- **See and find its way.** Camera and GPS, mapping runs, and getting home on the camera alone if GPS drops.
- **Get smarter.** It tunes itself, and takes missions in plain English from an LLM on my laptop. The LLM makes the plan. It never touches the motors.

## Modules

The frame is built to carry everything, but it flies bare first. After that I bolt on whatever the day needs.

| | Module | What's in it |
|---|---|---|
| **V** | Vision & nav | GPS, camera, companion computer |
| **P** | Parachute | The chute, plus the independent monitor that fires it |
| **C** | Claws | Grabby bits. Coming eventually. |

## How I'm building it

Simulate first, buy later. Every design has to get through five layers before any money changes hands:

1. **Sizing model.** Will it lift, and for how long? (Python)
2. **CAD, as code.** Does it all fit, and where does it balance? (build123d)
3. **Virtual wind tunnel.** What does the air actually do around it? (OpenFOAM, plus FluidX3D for the pretty spinning-prop runs)
4. **Flight sim.** Can the airframe fly? PX4 flies it in Gazebo to find out.
5. **My firmware in the sim.** Can *my* code fly it?

The first design is a plain X quad, just to prove the pipeline works. After that, an automated loop builds, tests and improves designs, hunting for one that's actually unique. Whatever wins gets priced, and then it gets bought.

## How it fits together

```
LAPTOP              map · telemetry · LLM assistant · mission approval · 3D maps
   │  data + video link
COMPANION COMPUTER  cameras · GPS-free navigation
   │
FLIGHT CONTROLLER   sensors · PID · motors · failsafes · self-tuning
   │                (my RC transmitter plugs in here and always wins)
4-in-1 ESC → 4 motors          + independent parachute monitor
```

Each layer has to stay safe if the one above it dies.

## Finding your way around

- [STATUS.md](STATUS.md): what I'm doing right now
- [docs/roadmap.md](docs/roadmap.md): the plan, phase by phase
- [docs/decisions.md](docs/decisions.md): every decision so far, and why
- [docs/learning.md](docs/learning.md): everything I'm learning along the way, with the resources I'm using
- [docs/style.md](docs/style.md): how everything is supposed to look
- [docs/specs/](docs/specs/): detailed designs, written before I build things
- [docs/log/](docs/log/): the build log, roughly one entry per session

## License

[GPL-3.0](LICENSE). Take it, build on it, share what you make.
