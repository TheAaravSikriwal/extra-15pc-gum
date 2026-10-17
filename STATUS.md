# Status

**Last updated:** 2026-10-17, on the PC's Windows side
**Step:** 1c, building the sizing model ([the plan](docs/plans/2026-10-17-sizing-model.md)): task 12 of 15 done, the sweep and the margin chart; next is task 13, the report
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

**Step 1a is done (2026-10-17).** The sizing model talk settled eight questions, all in the spec under "Settled in the sizing model talk": the power model, the battery model, the catalog format, which parts go in first, the outputs (a Markdown report, Rerun replays of every test, and the project site), the code as one package called 14 pcs left (`pcs14` in the code), and Mission plus a 200 g growth margin as the setup that sizes the drone. The [log](docs/log/2026-10-17-sizing-model-talk.md) has the story.

**Nothing has been built yet.** The repo has its folders, Python tooling, CI and two small test files (14 tests), and they pass on GitHub. The clean starting point is tagged `phase-1-start`.

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Set up WSL2 on the PC** with [docs/setup-pc.md](docs/setup-pc.md). The `wsl --install` step needs an admin PowerShell and one reboot. Then commit `docs/machines/pc.md`.
2. **Step 1c: build the sizing model**, test-first, following [the plan](docs/plans/2026-10-17-sizing-model.md) (OK'd 2026-10-17). It doesn't need WSL: it's plain Python, and CI checks it on Linux. From task 10 on, every test flight plays in Rerun.
3. **Step 1d: research and add the real parts**, run the sweep, and pick the parts and the final growth margin, with uncertainty bands.
4. **The project site's spec** (what it's built with), so its first pages can come with the sizing model.
5. **Write the first half of `scripts/setup-ubuntu.sh`** (inside WSL2): Gazebo, PX4 and the Python tools, with pinned versions.

## Still open

- Prop size, cell type, and 6S2P vs 6S3P. The sizing model gets to decide.
- Cruise speed: 10 m/s until the sizing model says otherwise
- The final growth margin (step 1d)
- How modules talk to the flight controller: plain serial or DroneCAN (step 3)
- Which H743 flight controller board. It has to be one PX4 supports, with SWD pads.
- Which OpenFOAM: the Foundation release or ESI's. Decided when writing the CFD half of the setup script.
- Companion computer and camera (step 6). HaLow is the lead option for the video link.
- Where the Meshtastic relay (#30) lives: V, Base, or its own little module
- Exactly what goes in the `us-recreational` limits profile, and whether to get Part 107 (for the build package)
- What "unique" is allowed to mean in the design hunt
- What the project site is built with (it stays on my machine until the project is done, then joins my portfolio at wearechintu.com)

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Windows 11 + **WSL2 Ubuntu 24.04** (dual boot, native Ubuntu as a fallback), Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060 | Main machine: sim, CFD, CAD, renders | WSL not installed yet. Follow [docs/setup-pc.md](docs/setup-pc.md). The repo is at `C:\dr\extra-15pc-gum`. |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station, object detection | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now. |

## Switching machines

Pull when you sit down, push when you get up. Update this file, the README's plan and the log before you push.
