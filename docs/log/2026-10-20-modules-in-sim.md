# 2026-10-20: The modules in sim, starting with the chute

*PC, WSL2 Ubuntu and Windows. Step 6: the [spec](../specs/2026-10-20-modules-in-sim.md), the [plan](../plans/2026-10-20-modules-in-sim.md) and the build. The [report](../reports/modules/README.md) has every number.*

Step 6 is where the modules (P the parachute, V the camera and the radio, C the claws) get their own tests. Steps 4 and 5 had already done more of it than the roadmap expected: the chute drops in every combination with P, the safety monitor's triggers had been replayed over dozens of healthy runs, and my firmware's parachute rule had its tests. So the spec started with a table of what was already done, and the plan only covered what wasn't.

## The safety monitor fires the chute

The safety rules say the parachute can be fired by the flight controller or the safety monitor. The flight controller could. The monitor, it turned out, couldn't. The electrical design gives the Teensy a release line of its own, and the right to take the release servo's line away from P's node, but nothing in its firmware used them.

Now it does. The pilot's chute switch reaches the monitor too, and when it flips, the monitor cuts the motors and then lets the chute go, in that order, every time. Two cases where it does nothing: on the ground, disarmed, and on a drone without P. That second one matters more than it sounds. Cutting the motors to fire a chute that isn't there drops the drone, so the switch has to know P is fitted. The release latches like the cut does, clearing only on the ground. The monitor's own triggers stay in shadow mode, logging only, so in the air it's the pilot who fires the chute from the monitor.

## A flight controller that hangs

This is the scenario the monitor exists for: 40 m up with the chute on, my flight controller's process frozen, the way a hung processor would be. The monitor sees its heartbeat stop and cuts the motors. A second later the pilot flips the chute switch.

The first run failed, and the bug was mine. A frozen flight controller stops logging, and it also stops the clock every other scenario waits on, so this one times itself on Gazebo's clock and records Gazebo's ground truth itself. My ground-truth reader hadn't heard a single pose when the script read the time, so it said -1 s. Every wait after that ended at once, the flight controller was unfrozen straight away, and the run was over before the canopy could open. Waiting for the first real pose fixed it.

| | P | mission | P+C | max |
|---|---|---|---|---|
| The monitor cut, after the hang | 0.29 s | 0.28 s | 0.28 s | 0.28 s |
| The motors stopped before the canopy left | 0.98 s | 1.21 s | 1.01 s | 1.02 s |
| Height lost before it steadied | 9.7 m | 11.1 m | 9.7 m | 10.3 m |
| Coming down at | 4.1 m/s | 4.3 m/s | 4.3 m/s | 4.4 m/s |
| Height to spare | 27.2 m | 24.0 m | 27.1 m | 26.2 m |

The cut comes 0.28 to 0.29 s after the hang against the monitor's 0.25 s timeout; the rest is how I time the hang itself, off Gazebo's ground truth sampled every 20 ms of wall time. It loses twice the height of a plain drop because the drone free-falls for the second the pilot takes to react before the chute even fires. The monitor's own free-fall trigger, in shadow mode, saw the fall 0.6 s after the hang every time.

## How low the chute saves it

Decisions.md says the chute needs about 10 m to open. So I dropped Max, the heaviest, from 10, 15, 20 and 30 m. All four were saved, losing about 5 m before settling at 4.4 m/s. Even from 10 m it had nearly 6 m to spare.

That's less of a result than it looks. The sim's canopy takes 0.2 s to leave the tube and 1.0 s to fill, and both numbers are my guesses: Fruity Chutes doesn't publish them. A one-dimensional version of the same canopy, which agrees with the sim at 1 s (5.1 m lost against the sim's 4.4 to 5.2), shows how much rides on that guess:

| Opening time | Height lost |
|---|---|
| 0.5 s | 2.1 m |
| 1.0 s | 5.1 m |
| 1.5 s | 8.1 m |
| 2.0 s | 11.4 m |
| 3.0 s | 18.3 m |

Every extra second costs about 6 m. The "about 10 m" in my decisions is a canopy that takes nearly 2 s. That's a question for Fruity Chutes, next to the one about the release servo.

## The opening jolt

For the structure track, which will need to know what the chute's mount has to hold: how hard does the canopy pull when it opens? Two numbers. The sim's, from Gazebo's ground truth during the opening: 38 to 46 N, about 2 g. That's low, because the sim's canopy grows its area in a straight line and real ones overshoot as they fill. And the textbook bound, the opening force coefficient times the dynamic pressure times the canopy's drag area, with the coefficient from Knacke's Parachute Recovery Systems Design Manual for a solid canopy at "infinite mass": 171 to 254 N, 8 to 12 g, at the 9 to 11 m/s the drone was falling when its canopy started to fill. Infinite mass is the worst case, and a 2 kg drone under a 1.9 m^2 canopy is nowhere near it, so the truth is somewhere between. The mount gets designed to the bound.

## The parachute rule, in the sim

My firmware won't fly above 30 m without P. Every scenario run on my firmware switches the rule off, since they compare it with PX4, which has no such rule, and a scenario couldn't switch it back on: the runner's override always won. It can now. Asked for a 40 m take-off without P, it stopped at 30.3 to 30.4 m in all four combinations without a chute.

## The false-trigger replay

The safety monitor's reference triggers, replayed over the 72 healthy runs my firmware flew (nothing failing on purpose): none fired. One thing the hung flight controller runs showed that the replay can't: under the canopy, the monitor's own tumble-tilt trigger fires, logged only, because the drone hangs at an angle from the chute's mount. The motors are already cut by then, so it changes nothing, but it's the kind of thing the shadow mode is there to catch before a trigger ever acts.

## HaLow, as a link

Module V's radio to the laptop is Wi-Fi HaLow. Heltec publishes no receive sensitivity for its card, so the model uses Morse Micro's numbers for the chip on it: -103 dBm at the slowest rate on a 2 MHz channel, -84 dBm at the fastest (7.2 Mbps), 21 dBm out. Line of sight over flat ground at 915 MHz, the ground's reflection taking over past a few hundred meters to a couple of kilometers depending on height, and a 10 dB margin for everything that leaves out.

| | 10 m up | 30 m up | 120 m up |
|---|---|---|---|
| 7.2 Mbps holds to | 0.8 km | 1.2 km | 1.2 km |
| the slowest rate holds to | 3.1 km | 5.3 km | 10.7 km |

That's more than Heltec's own "1 to 2 km", which I'd guess is measured near the ground with things in the way. Trees and hills aren't in my model at all.

Then into the sim. On the real drone, HaLow carries the laptop's ground station link and the video. The pilot's link is ExpressLRS at 2.4 GHz, and the companion computer talks to the flight controller over a wire. So the sim's ground station link went through the model: every datagram my firmware sends to the laptop dropped with the model's packet loss at the drone's distance. The drone flew 7 km out at 10 m and back, in all four combinations with V. Under half the datagrams got through from 5.86 to 5.95 km, within 1.5% of where the model loses half of them (about 5.94 km), which says the relay does what the model says and not much more. (My first grader compared that with the model's rated edge, where a tenth are lost; the runs were fine, the grader wasn't.) And the drone flew on regardless, and landed within 2 m of where it started, as it should, since nothing it depends on is HaLow.

## The companion computer

The roadmap left the Pi 5 against a Jetson Orin Nano for step 6. Decisions.md already leaned to the Pi, since the LLM and the object detector run on the laptop. The numbers back it. Neither board has a hardware video encoder (the Pi 5 dropped its, and NVIDIA's own docs say the Orin Nano has no NVENC), so the live video is a CPU encode on either: Raspberry Pi says its CPU does 1080p30 on as little as 60% of one core. GPS-free flight needs visual-inertial odometry, which a published benchmark ran on embedded ARM boards a generation older than the Pi 5's. The Orin Nano would add watts (7 to 25 W against the Pi's 8 W budget) without a job to spend its GPU on.

## The camera

V's camera is the Raspberry Pi Camera Module 3, 66 degrees across, and the question was whether Gazebo would render it at all inside WSL with no GPU of its own. It does: 30 frames of 720p in about 1.3 s of wall time, on the CPU. The camera goes on V's models only when a scenario asks for it, because PX4's server config loads Gazebo's rendering system for every run, and a camera on every model would render in every batch.

Two bugs before the first useful frame. The camera spent its first flight looking at plain ground, because Gazebo spawns the model facing east and the scenario flew it north, sideways. And once it faced the right way, the shed, the trees and the box I'd put along the path were nowhere: the spawn's own pose overrides the pose inside the model, and the spawn's was zero, so all seven of them were standing at home, around the spot the drone took off from. It flew up through them without noticing, since they have no collision.

Then the video the laptop would get. What's left of HaLow's rate for video at each distance (about 60% of the rate on the air carries data, less the telemetry) carries 720p at 30 frames a second out to about 2 km at 30 m up, 480p at 3 km, and 240p at 10 frames a second at 5 km. I encoded the camera's own frames at those rates. The three look almost the same, and that's the sim flattering the link: Gazebo's world is flat colors with no texture, which compresses to almost nothing. Real video with grass and leaves moving would need far more bits for the same picture, so the table is the honest part and the still isn't.

## What's next

Step 6 is done, except C. The claws are still a placeholder, and the roadmap holds C until a unique claw on an actual arm comes up, which is my conversation to have. The payload grab keeps passing in every C combination meanwhile.

The questions for Fruity Chutes grow by one: besides the release servo's voltage and draw, how long the Harrier takes to fill.

Up next is step 7, the smart features. The camera working in WSL means the mapping runs, the safe spots, change detection, GPS-free flight and the object detector can all happen in the sim, not just the ones that don't need a picture.
