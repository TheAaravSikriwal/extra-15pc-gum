# Status

**Last updated:** 2026-10-13, on the laptop
**Phase:** 1, simulating the design

## Right now

Planning is done and locked in. The modules, the targets, the parachute rule and the [roadmap](docs/roadmap.md) are all in [docs/decisions.md](docs/decisions.md). The detailed Phase 1 design is in [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md).

The repo has its folders, Python tooling and CI in place, but nothing has been built yet. This is the clean starting point, tagged `phase-1-start`.

## Up next

1. Talk through the sizing model and nail down how it works (the open questions are listed in the spec).
2. Write the implementation plan for it.
3. Build it.
4. Write the Ubuntu setup script for Gazebo + PX4, and test it in the laptop's WSL.
5. Set up the PC (Linux side) and clone the repo there.

## Still open

- Prop size: 8, 9 or 10". The sizing model gets to decide.
- How modules talk to the flight controller: plain serial or DroneCAN
- Which H743 flight controller board. It has to be one PX4 supports, for the baseline flight.
- Companion computer, camera and video link (not until Phase 6)

## Machines

| Machine | What it is | What it's for | Setup state |
|---|---|---|---|
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Planning, docs, sizing model, CAD, ground station in the field | Repo in OneDrive. Python venv at `%USERPROFILE%\.venvs\extra-15pc-gum`. Sim toolchain not installed. Pushes need `env -u GH_TOKEN git push` for now. |
| PC | Dual boot, i7, 32 GB DDR5, RTX 3060. **Ubuntu 24.04 for the sim** | Main simulation machine | Not set up yet |

## Switching machines

Pull when you sit down, push when you get up. Update this file and the log before you push.
