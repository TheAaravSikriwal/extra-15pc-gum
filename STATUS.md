# Status

**Last updated:** 2026-10-14, on the PC's Windows side (docs only; the Ubuntu side still isn't set up)
**Phase:** 1, simulating the design
**Main machine from now on:** the PC (Ubuntu 24.04)

## Right now

Planning is done, but it's getting one more full revision before anything gets built. The modules, the targets, the parachute rule and the [roadmap](docs/roadmap.md) are all in [docs/decisions.md](docs/decisions.md). The Phase 1 design is in [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md), and I've approved it. It covers:
- the sizing model
- CAD written as code (by Claude)
- a CFD wind tunnel layer
- Gazebo + PX4
- a design hunt once the plain X quad works
- visuals for every layer

The look is locked in [docs/style.md](docs/style.md).

**Plan review (2026-10-14):** Claude reviewed the whole repo. A few things got decided on the spot and are in [docs/decisions.md](docs/decisions.md):
- government rules are settings in a limits profile, not hard caps
- Wi-Fi HaLow is the lead option for the video link
- a Meshtastic relay node is on the shortlist (#30)
- the control link goes on 2.4 GHz to stay out of HaLow and Meshtastic's band

The rest are suggestions, not decisions yet. They're written up in [today's log](docs/log/2026-10-14-plan-review.md).

**Nothing has been built yet.** The repo has its folders, Python tooling, CI and two small test files (8 tests), and they pass on the laptop and on GitHub. The clean starting point is tagged `phase-1-start`.

**Moving to the PC:** [docs/setup-pc.md](docs/setup-pc.md) walks through it. `scripts/check-machine.sh` and `scripts/setup-dev.sh` rerun on the PC the same checks that were run on the laptop. The laptop's results are logged in [docs/machines/](docs/machines/).

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Full plan revision.** Fold the review's suggestions into one revised plan (roadmap, targets, spec). I read it start to finish and confirm it before anything else happens. It may change the targets and the order of the phases.
2. **Set up the PC's Ubuntu side** with [docs/setup-pc.md](docs/setup-pc.md). Commit `docs/machines/pc.md`.
3. **Talk through the sizing model.** That discussion hasn't happened yet. The questions to settle are in the spec, under "To settle before building it" (the plan revision may add some):
   - the cruise power and battery math, and what to validate them against
   - what cruise speed "flight time" means
   - the catalog format and which real parts to seed it with
   - what the report looks like
   - how the code is packaged
4. **Update the spec** with the answers, then **write the implementation plan** for the sizing model.
5. **Build it**, test-first.
6. **Write `scripts/setup-ubuntu.sh`:** Gazebo, PX4, OpenFOAM, ParaView, Blender, with pinned versions. Test it on the PC.

## Still open

- Prop size: 8, 9 or 10". The sizing model gets to decide.
- How modules talk to the flight controller: plain serial or DroneCAN
- Which H743 flight controller board. It has to be one PX4 supports, for the baseline flight.
- Which OpenFOAM: the Foundation release or ESI's. Decided when writing the setup script.
- Companion computer and camera (not until Phase 6). HaLow is the lead option for the video link.
- Where the Meshtastic relay (#30) lives: V, Base, or its own little module
- Exactly what goes in the `us-recreational` limits profile (before Phase 3)
- What "unique" is allowed to mean in the design hunt (after the baseline works)

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Dual boot. **Ubuntu 24.04**, Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060 | Main machine: building, sim, CFD, renders | Ubuntu side not set up yet. Follow [docs/setup-pc.md](docs/setup-pc.md). |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station in the field | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now. |

## Switching machines

Pull when you sit down, push when you get up. Update this file and the log before you push.
