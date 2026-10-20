# Flight sim (step 4)

*Started 2026-10-19 with the flight sim talk. Like everything else here, it will change once real numbers show up.*

## What this step has to produce

From the [roadmap](../roadmap.md) and layer 4 of the [simulation spec](2026-10-13-phase-1-simulation.md#layer-4-gazebo--px4-sim): PX4 flying a Gazebo model of this exact drone in all eight module combinations, through the same scenarios every time. A generator turns `build.yaml`, the sizing output, the CAD's mass properties and the drag numbers into a Gazebo model and PX4 settings for each combination, modeled on PX4's stock x500. The scenarios: hover and sudden stick inputs, a top-speed run, 10 m/s wind, hover and cruise endurance, lost link and low battery, a parachute drop, a payload grab, and failure injection (a dead motor, a failed sensor, a sagging battery). Gazebo doesn't model electricity, so the rotor speeds get turned into current afterwards and run through the sizing model's battery model. Every scenario's IMU data is replayed through the safety monitor's trigger logic to count false triggers. Results come out as pass/fail reports, Rerun recordings and clips.

**Done when:** the baseline passes every scenario in all eight module combinations on PX4.

## Settled in the flight sim talk

**The versions (2026-10-19): PX4 v1.17.0 and Gazebo Harmonic, pinned.** v1.17.0 has been PX4's stable release since May 2026; v1.18 was at its first release candidate when this was decided. Harmonic is PX4's default simulator and a long-term Gazebo release, and Ubuntu 24.04 supports it. Both get pinned to exact tags in `scripts/setup-ubuntu.sh`, so both machines match. **Why:** the most-tested pair, so the bugs I hit are more likely mine than the tools'. **Cost:** v1.18's changes wait. Moving to it once it's stable is its own small decision, with the scenarios rerun.

**Drag and wind (2026-10-19): a small Gazebo plugin of our own.** Out of the box, Gazebo's multicopter motor model adds only a little drag from the spinning props, and nothing pushes on the body, so the top-speed run would be limited only by PX4's tilt limit and the wind scenario would barely do anything. Gazebo's own wind system pushes each part in proportion to its mass and its speed through the air, which isn't how drag works. So a plugin of about 100 lines of C++ applies drag = ½ ρ v² × the drag area, against Gazebo's wind, using the same drag area the sizing model uses for that combination. The aero track's tables replace that one number later, direction by direction. The props' own drag stays the motor plugin's, from an estimate that's flagged as one. **Why:** the sim and the sizing model agree on drag. **Cost:** a plugin to build and keep working against Gazebo's API (Apache 2.0, fine next to GPL-3.0).

**The battery and my 90 A cap (2026-10-19): the motors top out at the worst case.** Each motor's top speed in the model is where the sizing model's full throttle lands: the pack at its 20% reserve, held to the 90 A cap. Every scenario flies on that, the same worst case the sizing model judges capability on. Flight time still comes from the logged rotor speeds, turned into current and run through the battery model afterwards. **Why:** simple, and it can't disagree with the sizing model. **Cost:** early in a flight the real drone has more thrust than the sim gives it, and the XT60's heat limit (a firmware job for step 5) isn't in the PX4 baseline at all.

**Pass and fail (2026-10-19): a `flight_sim` section in `design/targets.yaml`.**

| Scenario | Passes when | Number from |
|---|---|---|
| Hover, still air | holds within 0.5 m sideways and 0.3 m in height for 60 s | my pick |
| Stick inputs | each step settles within 0.5 s, overshooting under 20% | a control rule of thumb |
| Top speed | Mission reaches 80 km/h | the targets |
| 10 m/s wind | Mission holds within 1 m, its motors under 90% of their top speed | the targets, plus my picks |
| Endurance | hover and cruise times within 10% of the sizing model's | the layers agreeing |
| Lost link, low battery | returns and lands; low battery lands with at least 20% left | the targets' reserve |
| Parachute drop | the motors stop before the chute fires; the height lost before it holds is reported | the safety rules |
| Dead motor, failed sensor, sagging pack | a controlled landing or under the chute, never a fly-away | behavior |
| Payload grab (C only) | stays within 1 m after picking up the 250 g | the targets' payload |
| False triggers | none from the safety monitor in any healthy scenario | the safety rules |

The chute's drag comes from Fruity Chutes' rating (2.5 kg at 4.6 m/s), so the sim's descent rate would only repeat it; that's why the drop checks the order of events and reports the height lost. Max, at 2.62 kg, is a little over that rating and would come down at about 4.7 m/s.

**Flying the scenarios (2026-10-19): MAVSDK-Python, headless, in lockstep.** PX4's own SDK in Python drives PX4 and Gazebo with no window open, in lockstep so a run repeats exactly. Each scenario is one script; failures go in through MAVSDK's failure injection, and wind through Gazebo's own transport. Each flight's log goes through pyulog into the report, into Rerun (the CAD drone flying its logged path, next to the plots) and into the data files the project site reads. **Why:** the shortest path from a scenario to a graded result, in the same Python as the rest of pcs14. **Cost:** MAVSDK hides some of MAVLink; anything it can't do falls back to pymavlink for that one message.

From here on I made the calls myself and wrote down why (I asked to be asked only about drastic changes).

**The safety monitor's triggers (2026-10-19): a Python reference version now, ported to the Teensy in step 5.** The false-trigger replay needs trigger logic before the Teensy firmware exists, so `pcs14` gets one: free fall (the IMU's total acceleration under 0.3 g for 0.3 s) and tumbling (a body rate over 400 °/s for 0.3 s, or a tilt past 75° for 0.5 s). Those are starting numbers, set loose enough for a punch-out and tight enough to catch a dead motor, and tuned against the replays. They live in `design/targets.yaml` next to the pass/fail table. Step 5's Teensy firmware has to give the same answers on the same recorded IMU data. **Why:** the shadow-mode rule (triggers only log until they've shown zero false triggers) needs something to count with, and one reference keeps the sim and the firmware honest with each other.

**PX4 stays unmodified (2026-10-19).** PX4 runs its stock x500 airframe in Gazebo's standalone mode, with our generated parameters loaded at start, and `pcs14` starts Gazebo itself with our generated world and model. Nothing is added to PX4's source tree. **Why:** a clean pin to v1.17.0, nothing to carry between PX4 versions, and no PX4 code in this repo. The parameters include the hardware's real limits for the capability tests (a tilt limit and top speed high enough for the 80 km/h run); the legal limits are a separate limits profile, as always.

**The model (2026-10-19).** One Gazebo model per module combination, generated:
- the looks from the CAD's mesh of that combination, and a simple collision shape (the body and the four feet), because contacts on a full mesh are slow and jittery
- the mass, center of gravity and inertia from the CAD's mass properties, with the pack at its trim
- the rotors from the frame's geometry, with Gazebo's multicopter motor model fitted to Emax's thrust table: thrust against rotor speed squared, torque from the power, and the top speed at the worst case above. The prop's own drag, its rolling moment and the motors' spin-up times start from the x500's values, scaled, and are flagged as estimates
- our drag plugin, carrying the combination's drag area and, in P, the parachute: when the scenario fires it, the plugin waits out an ejection delay and then opens a canopy over an opening time, both estimates, with the canopy sized from Fruity Chutes' rating
- in C, Gazebo's detachable joint for the payload grab

**Where it runs (2026-10-19).** The PC's WSL2 Ubuntu 24.04, with PX4's source and builds in the Ubuntu home folder (the setup guide's rule). CI doesn't install PX4 or Gazebo, which are gigabytes and a long build. It checks everything around them instead: the generator's output, the drag and parachute math, the pass/fail grading and the battery post-processing, all on made-up data and short synthetic logs. Real flight logs stay out of the repo as always; the sim's logs live under `outputs/`.

**What comes out (2026-10-19).** `pcs14 flight-sim` generates the models, flies any or all scenarios in any or all combinations, and writes `docs/reports/flight-sim/` (the report and `flight-sim.json`, like the other steps), a Rerun recording, and stills in the post sizes. Gazebo clips for the posts get recorded on request and stay out of the repo.
