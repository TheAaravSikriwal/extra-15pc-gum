# Status

**Last updated:** 2026-10-14, on the PC's Windows side (docs only; the Ubuntu side still isn't set up)
**Phase:** 1, simulating the baseline
**Main machine from now on:** the PC (Ubuntu 24.04)

## Right now

Planning is done, and the full plan revision is confirmed (2026-10-14). The live plan is the [roadmap](docs/roadmap.md) and [docs/decisions.md](docs/decisions.md). What changed and why, tagged R1 to R7, is in [docs/specs/2026-10-14-plan-revision.md](docs/specs/2026-10-14-plan-revision.md). The Phase 1 design is in [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md). It covers:
- the sizing model
- a thrust stand, bought as soon as the sizing model has a shortlist
- CAD written as code (by Claude)
- Gazebo + PX4
- visuals for every layer
- running alongside, without blocking anything: the CFD wind tunnel and the design hunt (for v2)

The look is locked in [docs/style.md](docs/style.md).

**Nothing has been built yet.** The repo has its folders, Python tooling, CI and two small test files (12 tests), and they pass on GitHub. The clean starting point is tagged `phase-1-start`.

**Moving to the PC:** [docs/setup-pc.md](docs/setup-pc.md) walks through it. `scripts/check-machine.sh` and `scripts/setup-dev.sh` rerun on the PC the same checks that were run on the laptop. The laptop's results are logged in [docs/machines/](docs/machines/).

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Set up the PC's Ubuntu side** with [docs/setup-pc.md](docs/setup-pc.md). Commit `docs/machines/pc.md`.
2. **Talk through the sizing model.** That discussion hasn't happened yet. The questions to settle are in the spec, under "To settle before building it":
   - the hover power, cruise power and battery math, and what to validate them against
   - how to find the least-power speed that replaces the 10 m/s cruise placeholder
   - how to model voltage sag well enough to get thrust-to-weight at the reserve right
   - the catalog format, which real parts to seed it with, and where measured thrust data goes
   - what the report looks like
   - how the code is packaged
3. **Update the spec** with the answers, then **write the implementation plan** for the sizing model.
4. **Build it**, test-first. Its first job is the mass budget: does Max fit under 2.5 kg?
5. **Buy the thrust-stand parts** once the sizing model has a shortlist, and build the stand.
6. **Write the first half of `scripts/setup-ubuntu.sh`:** Gazebo, PX4 and the Python tools, with pinned versions. Test it on the PC.

## Still open

- Prop size, cell type, and 6S2P vs 6S3P. The sizing model gets to decide.
- Cruise speed: 10 m/s until the sizing model says otherwise
- How modules talk to the flight controller: plain serial or DroneCAN
- Which H743 flight controller board. It has to be one PX4 supports, with SWD pads.
- Which OpenFOAM: the Foundation release or ESI's. Decided when writing the CFD half of the setup script.
- Companion computer and camera (not until Phase 6). HaLow is the lead option for the video link.
- Where the Meshtastic relay (#30) lives: V, Base, or its own little module
- Exactly what goes in the `us-recreational` limits profile, and whether to get Part 107 (before Phase 3)
- How many clean shadow-mode flights before the safety monitor's automatic triggers go live
- What "unique" is allowed to mean in the design hunt
- Passive ways to save power in flight, without wings: under discussion, nothing decided yet

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Dual boot. **Ubuntu 24.04**, Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060 | Main machine: building, sim, CFD, renders | Ubuntu side not set up yet. Follow [docs/setup-pc.md](docs/setup-pc.md). |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station in the field | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now. |

## Switching machines

Pull when you sit down, push when you get up. Update this file and the log before you push.
