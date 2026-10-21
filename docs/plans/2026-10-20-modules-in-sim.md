# Implementation plan: modules in sim (step 6)

*Written 2026-10-20, from the [step 6 spec](../specs/2026-10-20-modules-in-sim.md). Test-first, like every step. I asked for the open items to keep moving, so I made the calls below and wrote down why.*

## Where things go

| What | Where |
|---|---|
| The safety monitor's chute | `firmware/monitor/` (its core and its sim program), tests in `firmware/monitor/tests/` |
| The new P scenarios | `src/pcs14/flight/scenarios/modules.py`, graded in `src/pcs14/flight/grade.py` |
| The opening jolt's bound | `src/pcs14/modules/chute.py` |
| The HaLow model | `src/pcs14/modules/halow.py`, its numbers in the catalog's HaLow entry |
| The HaLow relay | the flight sim's existing relay (`src/pcs14/flight/run.py`), given a loss and a delay by distance |
| The camera and the video | the generator puts the camera on V's models; `src/pcs14/modules/video.py` encodes |
| The companion computer's jobs | `docs/reports/modules/`, a table with its sources |
| The report | `pcs14 modules`, writing `docs/reports/modules/` like every other step |

## Calls made for the plan

- **The new scenarios fly my firmware only.** The hung flight controller needs my safety monitor in the loop, and the drop heights and the jolt are about the drone and the chute, not the autopilot. PX4's step 4 runs stay as they are.
- **The pilot's reaction is one second.** In the hung flight controller scenario the pilot flips the chute switch a second after the hang. The monitor has cut the motors at 0.25 s, so the drone is already falling when the switch goes.
- **Drop heights from flight termination,** the same way the 40 m drop fires the chute, in Max (the heaviest, so the worst case), at 10, 15, 20, 30 and 40 m.
- **The jolt from Gazebo's own ground truth,** differentiated twice, against the textbook bound. No new plugin.
- **HaLow's rates come from the standard, its sensitivity from Morse Micro's published figures if they exist, else the standard's minimums,** marked as estimates in the catalog the way every other estimate is.

## The tasks

| # | Task | What the tests check |
|---|---|---|
| 1 | **The monitor fires the chute:** on the pilot's switch where P is fitted, the motors cut first; from its triggers only out of shadow mode; latched like the cut | Host tests: the order, nothing on the ground, nothing without P, still works with the flight controller hung, shadow mode fires nothing |
| 2 | **The hung flight controller:** at 40 m in every P combination, the flight controller frozen, the pilot's switch a second later | The motors stop before the canopy leaves; the drone settles under the canopy before the ground |
| 3 | **How low the chute saves it:** drops in Max from 10 to 40 m | Each height's height lost and touchdown speed; the lowest height that settles before the ground |
| 4 | **The opening jolt:** the peak force from the sim and the textbook bound | The bound against a hand calculation; the sim's number from a made-up trajectory |
| 5 | **The parachute rule in the sim:** a take-off to 40 m in base, without P | My firmware holds at the rule's 30 m |
| 6 | **The false-trigger replay on my firmware** | The count over my firmware's healthy runs, in the report |
| 7 | **The HaLow model:** rates by modulation, the link budget, the range at each rate | Against a hand-worked link budget; the rate falls with distance and never rises |
| 8 | **HaLow in the sim:** the relay drops and delays packets by the model at the drone's distance; a flight out past the range | The data link fades where the model says; my firmware does what its data-link failsafe says |
| 9 | **The camera:** V's models get the Camera Module 3, its frames saved through a scenario | The frames come at the camera's rate; if Gazebo can't render headless in WSL, this task says so and stops |
| 10 | **The video at the link's rate:** the frames encoded at the bitrate HaLow holds at a few distances | The files' bitrates sit under the link's |
| 11 | **The companion computer's jobs:** the Pi 5 and the Jetson Orin Nano against the on-board jobs, from published numbers | Every number has a source |
| 12 | **The report:** `pcs14 modules` and `docs/reports/modules/`, and the project site's step page | It's written, and the site's step 6 page names its verdict |

**Done when:** each module passes its tests in every combination it's part of, and the report says what the sims couldn't settle.

## Where it stands

| Date | Tasks | Notes |
|---|---|---|
| 2026-10-20 | 9 done: all 12 | The camera renders in Gazebo inside WSL on the CPU, 30 frames of 720p in about 1.3 s of wall time. It goes on a model only when a scenario asks for it, a copy of the SDF in the run's folder, since PX4's server config renders for every run. Two bugs first: the drone flew north sideways, facing east the way Gazebo spawns it, and the scenery spawned at home because the spawn's zero pose beat the model's own. The video's encodes look alike at 1, 3 and 5 km, which is the sim's flat-colored world compressing to nothing, not the link being generous |
| 2026-10-20 | 2 to 8, 10 to 12 done | The hung flight controller passes in all four P combinations. The drops from 10, 15, 20 and 30 m in Max all saved it, losing about 5 m, and a one-dimensional model that agrees with the sim shows how much that rests on the canopy's unpublished opening time: 11 m at 2 s, 18 m at 3 s. The jolt: the sim's 2 g against the textbook bound's 8 to 12 g. The parachute rule held 40 m asked down to 30 m in the four combinations without P. No false triggers over my firmware's 72 healthy runs. HaLow's model, in the sim as a relay on the ground station's link, faded within a few percent of where the model loses half the packets, and the drone flew on, its other links not being HaLow. My first grader compared the fade with the model's rated edge (a tenth lost) instead of its half-loss point. The video budget and its encoder, and `pcs14 modules` writing the report. Task 9, the camera, is next |
| 2026-10-20 | 1 done, 2, 4, 7 and 11 started | The monitor fires the chute: 13 host tests, its sim program takes the pilot's chute switch with `--chute`, and the runner gives it that where P is fitted. The hung flight controller passes in P: the monitor cut 0.29 s after the freeze, the motors stopped 0.98 s before the canopy left, and the drone settled at 4.1 m/s with 27 m to spare. Its first run failed on my own scenario: the ground truth hadn't heard a pose yet, so the hang was stamped at -1 s and every wait ended at once. The opening jolt's bound, the HaLow model and the companion computer table have their code and tests. Every run on my firmware forces the parachute rule off; a scenario can now switch it back on for itself |
| 2026-10-20 | none yet | Plan written |
