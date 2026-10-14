# Status

**Last updated:** 2026-10-13, on the laptop
**Phase:** 1, simulating the design

## Right now

Planning is done and locked in. The modules, the targets, the parachute rule and the [roadmap](docs/roadmap.md) are all in [docs/decisions.md](docs/decisions.md). The detailed Phase 1 design is in [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md).

The repo has its folders, Python tooling and CI in place, but nothing has been built yet. The clean starting point is tagged `phase-1-start`.

Since then, the Phase 1 plan grew. The CAD is now written as code (by Claude), there's an aerodynamics layer (OpenFOAM, plus FluidX3D for showcase runs), and once the baseline X works, an automated design hunt starts. Visuals are a real output of every layer, because this all gets posted on LinkedIn and Instagram.

## Up next

1. Lock in the visual look for posts.
2. Talk through the sizing model and nail down how it works (the open questions are listed in the spec).
3. Write the implementation plan for it.
4. Build it.
5. Write the Ubuntu setup script (Gazebo, PX4, OpenFOAM, ParaView, Blender), and test it in the laptop's WSL.
6. Set up the PC (Linux side) and clone the repo there.

## Still open

- Prop size: 8, 9 or 10". The sizing model gets to decide.
- How modules talk to the flight controller: plain serial or DroneCAN
- Which H743 flight controller board. It has to be one PX4 supports, for the baseline flight.
- Companion computer, camera and video link (not until Phase 6)
- The visual look for posts
- What "unique" is allowed to mean in the design hunt (after the baseline works)

## Machines

| Machine | What it is | What it's for | Setup state |
|---|---|---|---|
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Planning, docs, sizing model, CAD, ground station in the field | Repo in OneDrive. Python venv at `%USERPROFILE%\.venvs\extra-15pc-gum`. Sim toolchain not installed. Pushes need `env -u GH_TOKEN git push` for now. |
| PC | Dual boot, i7, 32 GB DDR5, RTX 3060. **Ubuntu 24.04 for the sim** | Main simulation machine | Not set up yet |

## Switching machines

Pull when you sit down, push when you get up. Update this file and the log before you push.
