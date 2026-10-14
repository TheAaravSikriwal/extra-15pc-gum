# Status

**Last updated:** 2026-10-13 (laptop)
**Current phase:** 1 — Simulate the design (writing the detailed Phase 1 design)

## Where we are

Planning is done and locked: the modules (Base + V, P, C), the target specs, the parachute rule and the [roadmap](docs/roadmap.md). Everything is in [docs/decisions.md](docs/decisions.md). The roadmap is a living plan and will change as we go.

## Next up

1. **Detailed Phase 1 design:** the parts file, the sizing model, the CAD workflow, Gazebo model generation, and the test scenarios. Written up as a spec in `docs/superpowers/specs/`.
2. **Implementation plan** for Phase 1.
3. **Sizing model** (Phase 1.2): runs on the laptop, no GPU needed.
4. **Ubuntu 24.04 setup script** (Phase 1.1): Gazebo Harmonic + PX4 + Python, tested in the laptop's WSL so the PC setup is one command.
5. **Set up the PC:** Linux side of the dual boot, clone the repo, run the setup script.

## Open questions

- Exact prop size: 8, 9 or 10" (the sizing model will decide)
- Module bus: simple serial vs. DroneCAN
- Companion computer (Pi 5 or Jetson). Decided in Phase 6.
- Data/video link to the laptop
- Camera type
- Which H743 flight controller board (it must be one PX4 supports, for the baseline flight)

## Machines

| Machine | Setup | Role | State |
|---|---|---|---|
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Planning, docs, sizing model, CAD, field ground station | Repo cloned. Sim toolchain not installed. `git push` needs `env -u GH_TOKEN` until the fine-grained token is given access to this repo. |
| PC | Dual boot. **Ubuntu 24.04 for the sim**, i7, 32 GB DDR5, RTX 3060 | Main simulation machine | Not set up yet |

## Switching machines

1. Start of a session: `git pull`
2. End of a session: update this file, add a log entry in `docs/log/`, then commit and `git push`
