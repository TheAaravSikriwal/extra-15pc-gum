# 2026-10-19: PX4 flies it

*PC, WSL2 Ubuntu 24.04. Step 4c, tasks 9 and 10.*

Until today the flight sim was everything around the flying. Today it flew: PX4 v1.17.0 took off in Gazebo with the generated model of this drone, hovered for 10 seconds, landed, and the grader passed it.

## Setting up

Ubuntu went into WSL2 on the PC, and `scripts/setup-ubuntu.sh` did the rest: PX4's source at its v1.17.0 tag, PX4's own setup script (its toolchain, plus Gazebo Harmonic from OSRF's repository), a PX4 build for the simulator, the Python side (MAVSDK 3.17.4 and pyulog 1.2.4) and our drag plugin.

The first try stalled. PX4's usual instructions clone it with every submodule, which drags in NuttX, Gazebo Classic, jMAVSim and a pile of other things the simulator never touches, gigabytes of them. Partway through, GitHub was handing them over at about 60 kB/s, so the clone would have taken hours. The script now fetches only the nine submodules a simulator build uses, and only their pinned commits. That part took under four minutes, PX4 built in one go (1,141 steps), and Gazebo came in at 8.15.0.

One thing to keep an eye on: MAVSDK 3.17.4 now warns that the `mavsdk` package name is moving to a new native binding, and the API I'm using continues as `mavsdk-grpc`. I pin 3.17.4 exactly, so nothing changes for now.

## The runner

`pcs14 flight-sim run` flies any scenario in any combination. For each run it:

1. starts Gazebo's server with no window, pointed at our generated world and models, PX4's Gazebo plugins and our drag plugin
2. starts PX4 in Gazebo's standalone mode, completely stock: its x500 airframe, with our parameters handed over as environment variables, which PX4 reads at boot. PX4 spawns our model itself.
3. puts a small relay between PX4 and MAVSDK. The lost-link scenario needs to cut the radio, and PX4 v1.17 lists a failure for that but doesn't implement it. So the relay drops everything going up to the drone while still passing everything coming down: PX4 hears silence, the script still sees what PX4 does.
4. flies the scenario's script through MAVSDK, timed on PX4's own clock, so a run means the same thing at any sim speed
5. grades the flight from PX4's log. The grades use Gazebo's ground truth, which PX4 logs next to its own estimates, so a grade says what the drone did, not what PX4 thought it did.

Each run gets its own PX4 instance and Gazebo partition, so several can fly at once.

## The first flight

It flew on the first try and failed the grade anyway. "Held its height within 2.48 m" for a 2.5 m hover is the grader measuring the take-off. My script marked its hover "hold", and PX4's Hold mode is also "hold". PX4 enters Hold when it boots, so the grader started the window there, before take-off. Marks now come in pairs ("hold start", "hold end"), which can't clash with a mode name.

A second fix came out of reading that log. PX4 boots with no ground station and no GPS fix, so "link lost" and "position lost" are already up when the log starts. Those don't count as events anymore, only the moments a flag goes up mid-flight.

Second try: pass. It hovered at 539 rad/s, which is exactly what the motor model predicts for the base combination's 1,875 g, drifted 8 cm sideways, landed within 3 cm of where it took off, and the safety monitor's reference triggers stayed quiet. A 38-second flight takes 41 seconds of real time, start to finish. The same flight runs as a test (`tests/test_flight_px4.py`), which skips on any machine without PX4.

## Getting ready for the rest

Some of the scenario plumbing went in alongside:

- **PX4 fires the chute itself.** In P, PX4's parachute output drives a simulated servo, and our plugin fires the canopy when that output swings over. PX4 only does that on flight termination, which also stops the motors, so the order "motors off, then chute" comes from PX4's own logic, not my script. Termination is turned on only in combinations that have a chute.
- **Two new pass/fail lines in the targets.** A return lands within 2 m of where it took off. After a failure, "a controlled landing" means coming down slower than 2 m/s at the end, and "no fly-away" means ending up within 30 m of where the failure hit.

One thing the machine check turned up: OpenGL inside WSL runs on the CPU (llvmpipe), not the RTX 3060. The flights are headless, so they don't care, but Gazebo's window and any clips for posts will.

## Next

Task 11: every scenario in every combination, 78 runs, tuning PX4 wherever its x500 defaults don't suit this airframe, and writing down every change.
