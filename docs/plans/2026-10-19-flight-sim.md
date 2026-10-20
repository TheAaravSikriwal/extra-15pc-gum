# Implementation plan: flight sim

*Written 2026-10-19, from the [flight sim spec](../specs/2026-10-19-flight-sim.md). Test-first, like every step.*

## What it builds

`pcs14 flight-sim`: it generates a Gazebo model and PX4 parameters for each of the eight module combinations, flies PX4 v1.17.0 through every scenario in Gazebo Harmonic, grades each flight against the `flight_sim` targets, and writes the report, `flight-sim.json`, a Rerun recording and stills. It also includes a drag plugin of our own (body drag, wind and the parachute) and a Python reference version of the safety monitor's triggers.

## Where things go

| What | Where |
|---|---|
| The pass/fail numbers and trigger thresholds | `design/targets.yaml`, a `flight_sim` section |
| The Python side | `src/pcs14/flight/`: `motor.py` (the motor model fit), `generate.py` (models, world, PX4 parameters), `drag.py` (the plugin's math, mirrored), `power.py` (rotor speeds to current to the battery), `grade.py`, `report.py`, `run.py` (launching Gazebo, PX4 and the scenarios) and `scenarios/` |
| The safety monitor's reference triggers | `src/pcs14/safety/triggers.py` |
| The Gazebo plugin | `sim/plugins/pcs14_drag/` (C++ and CMake, built inside WSL2) |
| Generated models and worlds | `outputs/flight-sim/models/`, not committed (build outputs) |
| Flight logs | `outputs/flight-sim/logs/`, never committed |
| The report | `docs/reports/flight-sim/` |
| Setup | `scripts/setup-ubuntu.sh`, its first half |

## The tasks

| # | Task | What the tests check |
|---|---|---|
| 1 | **The `flight_sim` targets:** the spec's pass/fail table and the trigger thresholds in `design/targets.yaml`, with their schema | They load; a missing or nonsense number fails with a clear message |
| 2 | **The motor model:** Gazebo's multicopter motor constants fitted to Emax's thrust table (thrust against rotor speed squared, torque from the power), the top speed at the worst case (the reserve, the 90 A cap) from the sizing model, and the flagged estimates (the prop's drag, rolling moment and spin-up times, from the x500's, scaled) | A fit worked by hand on a made-up table; on the real build, four motors at the sizing model's hover speed lift Mission's weight |
| 3 | **The drag and parachute math, in Python:** drag = ½ ρ v² × the drag area against the wind, and the chute's ejection delay and opening, exactly what the C++ plugin will do | Forces worked by hand at a few speeds and winds; the canopy's area over time; the canopy's size from Fruity Chutes' rating gives 4.6 m/s at 2.5 kg |
| 4 | **The generator:** per combination, an SDF model (the CAD's mesh, a collision body and feet, the CAD's mass, center of gravity and inertia, the four rotors, the drag plugin with its numbers, the chute in P, the detachable payload in C), the world (empty, with wind), and PX4's parameters (the rotor geometry, the hover thrust, the battery, the capability limits) | The SDF is valid XML; the inertia matches the CAD's and is physically possible; the rotors sit on the frame's motor mounts; a made-up build's output matches a known-good copy |
| 5 | **Power afterwards:** logged rotor speeds to each motor's current (from Emax's table), plus the avionics, to the pack, through the sizing model's battery model | A steady synthetic hover gives the sizing model's hover time within 1% |
| 6 | **The safety monitor's reference triggers:** free fall and tumbling, from IMU samples | Synthetic traces: a drop triggers, a tumble triggers, a hard punch-out and a fast yaw don't |
| 7 | **Grading:** each scenario's checks from a flight log (the hover hold, step settling and overshoot, top speed, the wind hold and motor headroom, endurance against the sizing model, the failsafe sequences, the chute's order of events and height lost, the payload hold, false triggers) | Each check on a short synthetic log with a hand-worked answer, including ones that fail |
| 8 | **The report and data file:** `docs/reports/flight-sim/README.md` and `flight-sim.json`, every scenario in every combination, every estimate, Rerun (the CAD drone flying its logged path) and stills in the post sizes | The report matches a known-good copy for made-up results; the recording writes without a viewer |
| 9 | **Setup in WSL2:** Gazebo Harmonic, PX4 v1.17.0 at its tag, MAVSDK-Python and pyulog, pinned in `scripts/setup-ubuntu.sh`; the drag plugin built; the machine check rerun | The script runs twice cleanly; `scripts/check-machine.sh pc` finds every tool at its pinned version |
| 10 | **The runner:** `pcs14 flight-sim run` starts Gazebo (headless) with a generated world and model, PX4 in standalone mode with its parameters, and a scenario script, and collects the log | A smoke flight (take off, hover 10 s, land) in the base combination passes on the PC. Marked so it skips anywhere without PX4 |
| 11 | **Every scenario, every combination:** the scenario scripts, run in all eight combinations, with PX4 tuned where its defaults don't fly this airframe (each change recorded) | The scenarios themselves, graded by task 7 |
| 12 | **Close the loop:** the sim's endurance against the sizing model's, the false-trigger counts against the thresholds, anything the scenarios found, written up | The baseline passes every scenario in all eight combinations, or the report says exactly what doesn't |

Tasks 1 to 8 need only Windows and CI; 9 to 12 need Ubuntu in WSL2 on the PC.

**Done in the build (2026-10-19):** tasks 1 to 8. The stills wait for the first real flights, which are what's worth a post; the report and the Rerun replay are in.

**Done when:** the baseline passes every scenario in all eight module combinations on PX4, and the report shows every run.
