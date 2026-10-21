# Implementation plan: smart features in sim (step 7)

*Written 2026-10-20, from the [step 7 spec](../specs/2026-10-20-smart-features.md). Test-first, like every step. I asked for the open items to keep moving, so I made the calls below and wrote down why.*

## Where things go

| What | Where |
|---|---|
| The features' math (wind, the battery warning, self-tuning's identification, the safe spots, the relay's link, lift) | `src/pcs14/smart/`, tests in `tests/test_smart_*.py` |
| The firmware's parts (the landing modes, the spiral descent, the wind estimate, self-tuning) | `firmware/core/`, host tests beside them |
| The scenarios | `src/pcs14/flight/scenarios/smart.py`, flown on my firmware like step 6's |
| The mission planner and its checker | `src/pcs14/smart/missions.py`; the LLM through Ollama's local API |
| The report | `pcs14 smart`, writing `docs/reports/smart/` |

## Calls made for the plan

- **The checker is the contract, not the model.** Tests feed it plans that break each rule (outside the fence, above the ceiling, short on battery, too fast) and plans that don't; the LLM's own tests only check that what it writes parses and gets checked. A model that writes a bad plan is the checker's job to catch.
- **Everything the firmware does new gets a host test before it flies:** the wind estimate against made-up leans, the spiral's path against its geometry, self-tuning's identification against a made-up inertia.
- **The features that need the camera wait on the camera,** and the plan says which in each row.

## The tasks

| # | Task | What the tests check |
|---|---|---|
| 1 | **The math, on its own:** the wind from the lean and the turn-back warning, the Meshtastic relay's link, self-tuning's identification, the mission checker and its planner | Against hand-worked numbers; the checker on plans that break each rule |
| 2 | **The landing modes:** land now, back to start, land here (fly there, then land) | Each ends on the ground where it should |
| 3 | **Wind sensing in the sim:** the estimate from the wind scenario's logs, and the warning on a flight out with the wind behind it | Within 1 m/s of the sim's own wind; the warning fires while home is still in reach |
| 4 | **Self-tuning in the sim:** the inertia from the steps scenario's roll steps (the motors' speeds give the torque, the gyro the acceleration) in every combination | Within 15% of the inertia the CAD says, in all eight |
| 5 | **A plain-English mission, end to end:** the words, the local model's plan, the checker, an approval the script gives and logs as the script's, then my firmware flying it | It flies the plan's points within 2 m and comes home; a plan the checker refuses never flies |
| 6 | **The spiral descent:** a helix on low throttle from height, straightening up for the last few meters on the rangefinder | It follows the helix and its sink rate; the path only (no vortex ring state in Gazebo) |
| 7 | **Soar mode's lift detector:** a column of rising air in the drag plugin's wind, and the thrust a hover in it needs | The thrust drops by what the rising air predicts, and the detector finds the column |
| 8 | **Mapping:** a grid run with the camera, an orthomosaic from the frames and their poses | The scenery lands on the map within a meter of where it is |
| 9 | **Safe spots:** the detection on the world's height map, and a landing at the nearest one | It rejects the shed and the trees, finds open ground, and lands there |
| 10 | **Change detection:** the grid flown twice with the box moved between | The change is flagged where the box was and where it went, nowhere else |
| 11 | **GPS-free flight's estimate:** optical flow and the rangefinder on recorded frames | The position drifts less than 5% of the distance flown, against Gazebo's ground truth |
| 12 | **Object detection:** the local vision model on the camera's frames | It names what's there, and its boxes sit near the truth |
| 13 | **The report:** `pcs14 smart` and `docs/reports/smart/`, and the site's step 7 page | It's written, and the page names its verdict |

**Done when:** each feature works in sim, and its limits are on the unproven list.

## Where it stands

| Date | Tasks | Notes |
|---|---|---|
| 2026-10-21 | 5 done | A plain-English mission end to end: `pcs14 smart "..."` asks the local model (Qwen2.5 7B through Ollama) for a plan, the checker checks it against the limits profile and the drone (its pack, its reserve, never cheaper than a hover), and saves it unapproved. The `planned mission` scenario approves it as the test script, saying so in the log, and my firmware flies it: both waypoints within 0.0 m, home within 0 m. A plan the checker refused can never be approved. The finding worth more than the pass: asked to "fly 60 m west of home", the model wrote a point 20 m north and 40 m east of home, which the checker passed, since it was safe. The checker can't know what I meant; that's what the approval is for, and why the plan has to be shown on a map before I approve it |
| 2026-10-21 | 2 and 3 done | The landing modes in base: land now, back to start and land here, each down within 0.1 m of where it was asked, at 0.7 to 0.8 m/s. Wind sensing reads the sim's wind exactly (10.00 m/s against 10 in the wind scenario, 6.0 against 6 here), which says more about Gazebo using the same drag formula than about the estimate. The turn-back check, in every V combination: hover in a 6 m/s wind to sense it, 600 m out with it behind, then home into it. The warning's first prediction was 39% short, because the sizing model's power curve gets cheaper in forward flight and Gazebo's rotors don't; so the warning now never counts on flying being cheaper than hovering. Against the flight's own power (step 4's thrust-table reading of the rotors) it's within 8%, short by the slow-down at the end, which the warning's 1.25x margin covers. My firmware's gauge reads about 10% higher again, which is on the open list already |
| 2026-10-20 | 4 started, not passing yet | Self-tuning on the steps scenario's logs from my firmware, at their full 250 Hz (the graders' log is resampled to 15 Hz, far too coarse for a roll that settles in 0.3 s). The torque from the ESC speeds against the gyro's roll rate lands 9 to 62% high as is. Shifting the torque about 40 ms earlier, the dead time between a command and the gyro seeing it, gets P to within 3% but leaves C 39% high, and taking Gazebo's thrust falloff with axial speed into account made it worse, so I've stopped guessing. The steps scenario mixes the position loop's own corrections into the roll, which a fit can't untangle; the next try is a dedicated doublet on the rate loop itself |
| 2026-10-20 | 1 done | The wind from the lean, the turn-back warning, the relay's link (a node 100 m up reaches about eight times as far as one on the ground, LongFast), self-tuning's identification (fitting the rate against the integral of what was asked: the derivative smeared the doublet's edges by 2%), and the mission checker with its planner. The local model turned "fly 200 m north at 40 m up, wait 20 s, come home" into a plan in 5.7 s that the checker passed, and turned "go up to 600 feet and fly 2 km east as fast as you can" into one the checker refused twice: over the 400 ft ceiling, and faster than the drone may fly |
| 2026-10-20 | none yet | Plan written |
