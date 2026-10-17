# Status

**Last updated:** 2026-10-17, on the PC's Windows side
**Step:** setup, then step 1 (sizing and parts)
**Main machine:** the PC, with WSL2 Ubuntu 24.04 for the Linux tools

## Right now

**It's a research project now (2026-10-17).** Instead of buying parts and building the drone, I'm designing the whole thing in simulation: every real part modeled and connected, the wiring worked out, and my firmware flying it in the sim. The goal is a build package complete enough to build from one day, plus an honest list of what the simulations can't prove. Nothing gets bought by default. The thrust stand and a Nucleo board are optional extras.

Where to look:
- **The live plan:** the [README](README.md#the-plan), with each step's outcome filled in as it finishes
- **The steps in detail:** the [roadmap](docs/roadmap.md)
- **Every decision and why:** [docs/decisions.md](docs/decisions.md)
- **Steps 1, 2 and 4 in depth:** [docs/specs/2026-10-13-phase-1-simulation.md](docs/specs/2026-10-13-phase-1-simulation.md)
- **The earlier revision (R1 to R7):** [docs/specs/2026-10-14-plan-revision.md](docs/specs/2026-10-14-plan-revision.md)

**The PC runs the Linux tools in WSL2 now** (decided 2026-10-17), so there's no rebooting into the Ubuntu side, and it matches the laptop. The native Ubuntu side is a fallback. WSL isn't installed on the PC yet; [docs/setup-pc.md](docs/setup-pc.md) walks through it.

**Nothing has been built yet.** The repo has its folders, Python tooling, CI and two small test files (12 tests), and they pass on GitHub. The clean starting point is tagged `phase-1-start`.

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Set up WSL2 on the PC** with [docs/setup-pc.md](docs/setup-pc.md). The `wsl --install` step needs an admin PowerShell and one reboot. Then commit `docs/machines/pc.md`.
2. **Step 1a: talk through the sizing model.** Started 2026-10-17, and it doesn't need WSL. Settled so far: hover and cruise power (the least-power speed falls out of it), the battery model with sag, the catalog format, which parts go in first, and the outputs (a Markdown report, Rerun replays of every test, and the project site), in the spec under "Settled in the sizing model talk". Still to settle:
   - how the code is packaged
3. **Step 1b: update the spec** with the answers, then **write the implementation plan** for the sizing model.
4. **Step 1c: build it**, test-first. Its first job is the mass budget: does Max fit under 2.5 kg?
5. **Step 1d: pick the parts** from the sweep, with uncertainty bands.
6. **Write the first half of `scripts/setup-ubuntu.sh`** (inside WSL2): Gazebo, PX4 and the Python tools, with pinned versions.

## Still open

- Prop size, cell type, and 6S2P vs 6S3P. The sizing model gets to decide.
- Cruise speed: 10 m/s until the sizing model says otherwise
- Whether Max (with the claws) should still size the motors while the claws are uncertain (for the sizing model discussion)
- How modules talk to the flight controller: plain serial or DroneCAN (step 3)
- Which H743 flight controller board. It has to be one PX4 supports, with SWD pads.
- Which OpenFOAM: the Foundation release or ESI's. Decided when writing the CFD half of the setup script.
- Companion computer and camera (step 6). HaLow is the lead option for the video link.
- Where the Meshtastic relay (#30) lives: V, Base, or its own little module
- Exactly what goes in the `us-recreational` limits profile, and whether to get Part 107 (for the build package)
- What "unique" is allowed to mean in the design hunt
- Where the project site is hosted (public or private) and what it's built with

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Windows 11 + **WSL2 Ubuntu 24.04** (dual boot, native Ubuntu as a fallback), Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060 | Main machine: sim, CFD, CAD, renders | WSL not installed yet. Follow [docs/setup-pc.md](docs/setup-pc.md). The repo is at `C:\dr\extra-15pc-gum`. |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station, object detection | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now. |

## Switching machines

Pull when you sit down, push when you get up. Update this file, the README's plan and the log before you push.
