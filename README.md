# Extra 15pc Gum

A long-range quadcopter built from scratch and in public. It runs **my own flight firmware** on off-the-shelf parts, and every part choice is proven in simulation before anything is bought.

> **Status:** Phase 1, simulating the design. See [STATUS.md](STATUS.md) for where things stand right now, and the [roadmap](docs/roadmap.md) for where it's heading (a living plan that will change as we go).

## What it will do

- **Fly long:** 8–10" props, low-KV motors and a Li-ion pack, aiming for roughly 25–40 minutes cruising
- **Fly on my own code:** a custom flight controller running on an STM32H743
- **Land smart:** return to start, land at a spot I pick on the map, land in place, or go to the nearest safe spot found from a 3D map of the area
- **Fail safe:** failsafes for lost link, low battery and lost GPS, plus a parachute fired by an independent safety monitor
- **See:** a camera for video and for 3D mapping runs
- **Navigate without GPS:** camera-based navigation, so it can get home if GPS drops
- **Tune itself:** a self-tuning controller that re-tunes when the payload changes
- **Take plain-English missions:** an LLM on the laptop turns commands into flight plans, which are checked and approved before they fly. The LLM never controls the motors.

**Modular:** the airframe is built for the full load but flies bare first. Modules attach and detach depending on the day's job:
- **V:** vision & nav (GPS + camera)
- **P:** parachute
- **C:** claws

Shortlisted extras: wrist-gesture control, wind sensing, and change detection between mapping runs.

## How it's being built

**Simulate first, then buy.** Pick candidate parts → sizing model → CAD mock-up → physics sim → check against the target specs → swap parts → repeat. Parts are priced only once the specs are met.

| Layer | What it answers | Tools |
|---|---|---|
| 1. Sizing model | Will it lift? How long will it fly? | Python |
| 2. CAD mock-up | Does it fit? Where's the centre of gravity? | Onshape |
| 3. Physics sim | Can the airframe fly? Proven with PX4 | Gazebo Harmonic + PX4 |
| 4. My firmware in the sim | Does my code fly it? | Gazebo + custom firmware |

Then the hardware is built in stages:
1. It flies on my firmware.
2. Add the camera.
3. Add GPS and autonomy.

## Architecture

```
LAPTOP              map · telemetry · LLM assistant · approve missions · 3D maps
   │  data + video link
COMPANION COMPUTER  cameras · GPS-free navigation
   │
FLIGHT CONTROLLER   sensors · PID · motors · failsafes · self-tuning
   │                (the RC radio connects here directly, and always wins)
4-in-1 ESC → 4 motors          + independent parachute monitor
```

## Repo guide

- [STATUS.md](STATUS.md): current phase, next steps, open questions
- [docs/roadmap.md](docs/roadmap.md): the phases from simulation to the last module
- [docs/decisions.md](docs/decisions.md): every decision so far, and why
- [docs/log/](docs/log/): dated build-log entries

## License

[GPL-3.0](LICENSE)
