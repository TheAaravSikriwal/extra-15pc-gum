# Status

**Last updated:** 2026-10-14, on the laptop (handing off to the PC)
**Phase:** 1, simulating the design
**Main machine from now on:** the PC (Ubuntu 24.04)

## Right now

Planning is done and locked in. The modules, the targets, the parachute rule and the [roadmap](docs/roadmap.md) are all in [docs/decisions.md](docs/decisions.md). The Phase 1 design is in [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md), and I've approved it. It covers:
- the sizing model
- CAD written as code (by Claude)
- a CFD wind tunnel layer
- Gazebo + PX4
- a design hunt once the plain X quad works
- visuals for every layer

The look is locked in [docs/style.md](docs/style.md).

**Nothing has been built yet.** The repo has its folders, Python tooling, CI and two small test files (8 tests), and they pass on the laptop and on GitHub. The clean starting point is tagged `phase-1-start`.

**Moving to the PC:** [docs/setup-pc.md](docs/setup-pc.md) walks through it. `scripts/check-machine.sh` and `scripts/setup-dev.sh` rerun on the PC the same checks that were run on the laptop. The laptop's results are logged in [docs/machines/](docs/machines/).

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Set up the PC** with [docs/setup-pc.md](docs/setup-pc.md). Commit `docs/machines/pc.md`.
2. **Talk through the sizing model.** That discussion hasn't happened yet. The questions to settle are in the spec, under "To settle before building it":
   - the cruise power and battery math, and what to validate them against
   - what cruise speed "flight time" means
   - the catalog format and which real parts to seed it with
   - what the report looks like
   - how the code is packaged
3. **Update the spec** with the answers, then **write the implementation plan** for the sizing model.
4. **Build it**, test-first.
5. **Write `scripts/setup-ubuntu.sh`:** Gazebo, PX4, OpenFOAM, ParaView, Blender, with pinned versions. Test it on the PC.

## Still open

- Prop size: 8, 9 or 10". The sizing model gets to decide.
- How modules talk to the flight controller: plain serial or DroneCAN
- Which H743 flight controller board. It has to be one PX4 supports, for the baseline flight.
- Which OpenFOAM: the Foundation release or ESI's. Decided when writing the setup script.
- Companion computer, camera and video link (not until Phase 6)
- What "unique" is allowed to mean in the design hunt (after the baseline works)

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Dual boot. **Ubuntu 24.04**, i7, 32 GB DDR5, RTX 3060 | Main machine: building, sim, CFD, renders | Not set up yet. Follow [docs/setup-pc.md](docs/setup-pc.md). |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station in the field | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now. |

## Switching machines

Pull when you sit down, push when you get up. Update this file and the log before you push.
