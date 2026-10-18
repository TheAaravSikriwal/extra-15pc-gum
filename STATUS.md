# Status

**Last updated:** 2026-10-18, on the PC's Windows side
**Step:** step 2 is done (2026-10-18): the whole drone is modeled, every module combination passes its checks, and the real weights are back in the sizing model. Next is step 3, electrical design.
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

**Step 1c is done (2026-10-17).** The sizing model (`pcs14`) works end to end: `pcs14 size`, `sweep`, `report` and `validate`, with every flight playable in Rerun. The honesty check says the battery model is good and the cruise numbers run optimistic, maybe up to 2x, so hover is the number to trust for now.

**The first real sweep (2026-10-17).** Six real motors, seven props, four cells, two frames: 192 builds. At first, the rule that full throttle has to fit the pack's continuous rating forced a third parallel cell (and 400 g) on everything. So my firmware caps the battery current at the rating now, and 76 builds pass. The most robust is a Hobbywing 3115 on HQ 10x5 props with a 6S3P P45B pack (35.1 min hover with Mission's loadout, 2914 g); the lightest that passes every setup, Max included, is an Emax 2814 on Gemfan 1050 props with a 6S2P P42A pack (2254 g). The [report](docs/reports/sizing/README.md), the [log](docs/log/2026-10-17-first-real-sweep.md), and [decisions](docs/decisions.md) have the details.

**Step 1 is done (2026-10-17).** I picked the lightest build that passes every setup, Max included: Emax E3 2814 850KV motors, Gemfan 1050 tri-blades, a 6S2P Molicel P42A pack, the Tekko32 F4 50A ESC and the Nazgul XL10 frame, with my firmware capping the current at 90 A. Mission hovers 25.7 min (22.2 pessimistic) at 2254 g, and Max weighs 2454 g. The growth margin stays 200 g. "The parts" in [decisions](docs/decisions.md) has the full picture, including the catch: thin margins, and cruise numbers that are probably optimistic.

**Step 2 is done (2026-10-18).** `pcs14 cad` builds the whole drone, checks all eight module combinations (collisions, prop clearance, the parachute's cone, the rail, balance with the pack trimmed, the compass and Remote ID rules, the lidar's view), compares parts with existing CAD models, exports STEP, meshes, a GLB and print files, renders stills, and plays it all in Rerun. The first checks failed every combination; the fixed layout passes all eight. The printed parts' real weights went back into the catalog: Mission is 2293 g and still passes, with almost no margin left. The [CAD report](docs/reports/cad/README.md) and the [log](docs/log/2026-10-18-cad-build.md) have the details.

**The parts research added two missing parts (2026-10-17).** The camera needs a 22-pin cable for the Pi 5, and the HaLow card comes with no antenna, so both went into module V (14 g together). Mission is now 2268 g and hovers 25.5 min (21.9 pessimistic, against 21), and Max is 2468 g. Everything still passes, with a thinner margin.

**The CAD talk is done (2026-10-17).** Seven answers, all in the spec under "Settled in the CAD talk": I model every part myself from published dimensions, after checking whether a CAD model of it already exists; battery underneath and modules on top, so the chute fires straight up; real printable designs for our own brackets, legs, tray and rail; check limits based on what each one costs; Rerun and styled stills for watching; STEP, meshes, a GLB for the site and print files on every run, with `cad.json` committed; and rough wire routes now. The [log](docs/log/2026-10-17-cad-talk.md) has the story.

**Offline?** Study from [docs/learning.md](docs/learning.md). Topics 1 and 2 (how quads fly; props, motors and batteries) are what the sizing model needs.

## Up next

1. **Set up WSL2 on the PC** with [docs/setup-pc.md](docs/setup-pc.md). The `wsl --install` step needs an admin PowerShell and one reboot. Then commit `docs/machines/pc.md`.
2. **Step 3a: the electrical talk.** Gauges, connectors and pinouts from the CAD's wire lengths (in `docs/reports/cad/cad.json`), the power budget for the Pi's 5 V rail (the BEC is rated right at the Pi's 5 A), and how modules talk to the flight controller.
3. **The project site's spec** (what it's built with), so its first pages can come with the sizing model.
4. **Write the first half of `scripts/setup-ubuntu.sh`** (inside WSL2): Gazebo, PX4 and the Python tools, with pinned versions.

## Still open

- Rotor drag in forward flight, so the cruise numbers get believable (the honesty check's big miss)
- Almost no weight margin left: Mission's pessimistic hover is 21.6 min against 21, and Max is 7 g under its 2500 g limit. The next grams need a decision.
- Whether the HaLow HAT works on a Pi 5 (Heltec lists Pi 1 to 4), and which 915 MHz antenna to use
- Cruise speed: 10 m/s until the sizing model says otherwise
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
