# Status

**Last updated:** 2026-10-13 (laptop)
**Current phase:** 0 — Planning → designing the simulation

## Where we are

Planning is done: the goals, features, safety architecture, flight controller choice and simulation-first approach are all recorded in [docs/decisions.md](docs/decisions.md). We're now designing the simulation, which is four layers: sizing model, CAD, Gazebo + PX4, then my own firmware in the sim. Gazebo + PX4 has been chosen as the simulator.

## Next up

1. **Set the target specs.** These are the pass/fail numbers the simulation checks against: flight time, thrust-to-weight, top speed, wind tolerance, payload, and maximum weight.
2. **Finish the simulation design.** How the layers connect, the parts file, the test scenarios. Write it up as a spec in `docs/`.
3. **Write the implementation plan** for the simulation work.
4. **Set up the PC:** Ubuntu 24.04 (Linux side of the dual boot), clone this repo, install the toolchain.
5. **Build layer 1:** the sizing model.

## Open questions

- Target specs (see item 1 above)
- Exact prop size: 8, 9 or 10"
- Companion computer (Pi 5 or Jetson). Not needed until hardware stage 2.
- Data/video link to the laptop
- Camera type
- Final pick of the shortlisted extras

## Machines

| Machine | Setup | Role | State |
|---|---|---|---|
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Planning, docs, light work, field ground station | Repo created; sim toolchain not installed |
| PC | Dual boot. **Ubuntu 24.04 for the sim**, i7, 32 GB DDR5, RTX 3060 | Main simulation machine | Not set up yet |

## Switching machines

1. Start of a session: `git pull`
2. End of a session: update this file, add a log entry in `docs/log/`, then commit and `git push`
