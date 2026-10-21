# 2026-10-20: My firmware flies the whole flight sim

*PC, WSL2 Ubuntu and Windows. Step 5, tasks 6 to 13: from speaking MAVLink to every scenario in every combination, the first real drivers for the board, and the ground station.*

The [first firmware entry](2026-10-20-firmware-start.md) ended with rate mode flying in Gazebo and a log the graders could read. This one ends with my firmware flying the same 78 runs PX4 flew in step 4, graded by the same code. Getting there took most of the plan's tasks and a handful of bugs, a few of them in Gazebo rather than in my code.

## Speaking PX4's language

The flight sim's scripts fly through MAVSDK, which expects PX4. So my firmware pretends to be PX4 on the wire: the same heartbeat, PX4's way of numbering modes, the telemetry MAVSDK listens for, acked commands, and a parameter store with PX4's odd habit of packing integers into floats byte for byte. I read MAVSDK's source to find exactly what it checks before it calls a drone healthy. It connected, saw a healthy drone with a home position, and armed it the first time it ran, which almost never happens.

## Holding still

Self-level is an angle loop around the rate loop. The height comes from a barometer and the accelerometer blended in a small filter that also learns the accelerometer's bias. Position is the same idea with the GPS.

My PC's model of the drone caught the classic weakness of an accelerometer-only attitude filter before Gazebo did. In a long lean the drone speeds up sideways, the accelerometer feels mostly thrust, and the filter slowly decides "this is level". It drifted until the drone was at 47 degrees. The fix takes the drone's own acceleration, from the GPS's velocity, out of the accelerometer first.

## Gazebo's compass is left-handed

The first hover in Gazebo spiralled out and tumbled. The heading was a quarter turn off: Gazebo Harmonic's magnetometer lays the Earth's field out in a left-handed frame. PX4's bridge undoes that with a fixed swap of the axes, and I copied it. That held level, and then went wrong in a 45 degree dash.

So I measured it. I put static models in Gazebo, level, pitched 30 degrees and rolled 30 degrees, and read the magnetometer. The readings are the swapped field turned by the model's attitude, to four digits. The swap doesn't commute with a tilt, so no fixed mapping is right once the drone leans. It does commute with a turn about the vertical, though, so undoing it needs only the tilt, and the tilt comes from the accelerometer. My sim layer does that now. (Gazebo fixed this upstream in gz-sim pull request 2460, in a release after the one I run.)

## Tuning

My rate loops ask for an angular acceleration and multiply by the drone's inertia, so the gains mean something physical and don't carry PX4's names. A sweep on my PC's model picked rate P 20, I 70, D 0.5 and a self-level gain of 6.5, and the accelerometer's pull on the attitude drops to 0.3 in the air. A 15 degree stick step settles in 0.26 s on my PC's model. More integral holds an off-center weight better but leaves a slow tail on every step: at 100 the same step took 0.62 s.

Gazebo disagreed with 6.5 in one place. In the steps scenario the overshoot came out at 4 to 6% in some combinations, right on the grader's 5% band, so P+C took 0.61 s to settle while it wandered in and out of the band. I moved the self-level gain to 5.5 and flew the eight step runs again: 0.27 to 0.33 s, under 2% overshoot. Then I flew the whole matrix again with it, which is the batch below.

## Failsafes, limits and the safety monitor

The failsafes follow PX4's by name and default, so the failsafe scenarios mean the same thing for both: lost link returns home, low battery returns then lands, a lost position comes down on the barometer alone, and a drone tilted past 60 degrees for 0.3 s is out of control and, where there's a chute, terminated. Then the things PX4 doesn't have: the current cap with the XT60's heat limit (90 A for 3.1 s from Max's hover, then easing toward 29 A, as the electrical report has it), the limits profiles, and my parachute rule.

The safety monitor is its own program on its own simulated IMU, sitting between my flight controller and the motors. When I froze the flight controller mid-hover, the monitor cut the motors 0.26 s later (its timeout is 0.25 s) and the drone came down, instead of hovering on at its last motor speeds. The last two pieces went in today: a geofence by PX4's names and defaults, and pre-arm checks. It won't arm without live sensors, a position where the mode needs one, a battery above critical, the kill switch off, and a safety monitor that's alive and not cutting. The monitor sends its own heartbeat for that now.

## The whole matrix

All 78 runs, the same twelve scenarios in the same eight combinations PX4 flew in step 4, graded by the same code, one at a time at 4x sim speed. My firmware passes 66 of 78. PX4 passed 62. Every run PX4 passes, mine passes too.

| Scenario | PX4 | Mine |
|---|---|---|
| hover | 8 of 8 | 8 of 8 |
| steps | 8 of 8 | 8 of 8 |
| top speed | 3 of 3 | 3 of 3 |
| wind | 3 of 3 | 3 of 3 |
| endurance | 0 of 8 | 0 of 8 |
| lost link | 8 of 8 | 8 of 8 |
| low battery | 8 of 8 | 8 of 8 |
| parachute drop | 4 of 4 | 4 of 4 |
| dead motor | 4 of 8 | 4 of 8 |
| failed sensor | 4 of 8 | 8 of 8 |
| sagging pack | 8 of 8 | 8 of 8 |
| payload grab | 4 of 4 | 4 of 4 |
| **all** | **62 of 78** | **66 of 78** |

The misses are the same ones, for the same reasons. Cruise endurance misses everywhere on both, because Gazebo's rotors don't get cheaper in forward flight the way real ones do. A dead motor without the chute is a crash on both: a quad can't fly on three motors, and without P nothing catches it.

A few differences are worth a closer look.

**A failed GPS.** PX4's blind descents ended 22 to 36 m from where the GPS failed, and four of them missed the 30 m limit. That was one of step 4's three findings, and it raised the question of an optical flow sensor in Base. Mine ended 4 to 6 m away in every combination. It isn't that my firmware is clever. With no position it does what PX4 does, levels on its own attitude estimate and comes down on the barometer, and the drift comes from how wrong that "level" is. Today's fixes to my attitude estimate (the compass at a tilt, the drone's own acceleration taken out of the accelerometer) leave it closer to true than PX4's is in this sim. That doesn't settle the optical flow question. A real IMU has bias and vibration that Gazebo's clean noise doesn't, and a real drone would drift more than either of these. But part of step 4's finding was PX4's estimator in this particular sim, not the drone.

**Holding height.** My hovers wander 0.12 to 0.25 m in height, against PX4's 0.06 to 0.20 m, inside the 0.3 m limit but not by much. Sideways it's the other way round: mine drift under a centimeter over the minute, PX4's 6 to 10 cm. My height estimate is the barometer and the accelerometer, and my filter lets the barometer's noise through at about 6 cm. PX4 leans on the GPS's height, which in Gazebo has no noise at all, so the sim flatters it there. A real GPS's height is noisy and slow, so this goes on the open list rather than getting tuned away for the sim's sake.

**The steps.** A 14 degree roll step settles inside 5% in 0.27 to 0.32 s on mine, with 1 to 2% overshoot, in every combination. PX4's 15 degree step settles in 0.14 to 0.36 s with 2 to 4%. Mine is a touch slower and calmer, which is the gain change above doing its job.

## Four bugs the matrix found

**The ground was 0.7 m off.** Top speed takes off to 30 m first, and on my firmware it stopped at 29.2 m by its own reckoning while Gazebo said 29.8. My firmware set its height's zero on the barometer's very first sample, and the sim's barometer has 3 Pa of noise, about a quarter meter. One unlucky first sample put the ground 0.7 m below where it was. The zero is now the average of the first second.

**The payload hung on a boom.** In the payload grab, my firmware went into a slow roll wobble that grew every cycle until it was swinging 55 degrees. PX4 carried the same box without a problem. The cause was in the scenario: Gazebo's attach joint holds the box at whatever offset it finds, and the drone grabbed it from 0.4 m above, so the box rode rigidly half a meter below the drone. That's five times the drone's roll inertia, on a boom real claws don't have. My rate loop only knows the drone's own inertia, so its gain dropped to a fifth, its bandwidth fell below the self-level loop's, and the two loops started fighting. On my PC's model my loops ride out about four times the inertia they're told; Gazebo with the position loop on top wanted five.

The fix is in the scenario. At the grab, the box moves to just under the feet, where the claws would hold it, and then the joint closes. PX4's four payload runs flew again that way, and all pass. Both firmwares' thrust grew 11 to 13% with the 250 g box, against 11 to 12% expected.

**The take-off hand-over held a "close enough" height.** P+C's hover held its height within 0.34 m, over the 0.3 m limit. At the end of a take-off my firmware handed over to hold at whatever height the estimate said at that moment, which was the take-off's target minus however far short the climb was when it called itself done. Now hold takes over at the take-off's own height, and the hovers came in under the limit.

**The grader counted a touchdown on the drone's side as a landing.** V+C's dead motor passed once, which a quad on three motors shouldn't. It had crashed and come to rest on its side, with its origin about 0.26 m up, so the grader's "on the ground" test, written for a drone on its feet, never saw the moment it hit. Touchdown is now the first contact on any side, 0.4 m being the farthest the origin sits from the ground however the drone lies, and that run fails like the other three without a chute.

## The board

The ARK FPV layer got the pieces that don't need a scope to trust:

- **The clock tree,** PX4's for this board, as numbers with tests. That caught a real bug: my image timed DShot off a 240 MHz clock, a 480 MHz part's number, but this board runs its core at 320 MHz and its timers at 160. The motors would have been sent DShot400 while expecting DShot600. (PX4's own file says 480 in a comment and 320 in its numbers.)
- **The hardware watchdog** at 20 ms, twenty missed passes of the loop. A hung CPU resets, its heartbeat stops, and the monitor takes the motor lines.
- **The compass and the barometer,** started the way PX4's drivers start them and tested against fake chips. The barometer's math is the datasheet's floating-point form, and the test checks it against Bosch's integer form, the one PX4 runs: they agree to a hundredth of a pascal, about a millimeter of height. Its calibration check is a CRC, and the test uses the CRC catalogue's published check value, so that one isn't just my code agreeing with itself.
- **DroneCAN,** through libcanard (the DroneCAN project's C library, MIT). The board sends its node status the way every DroneCAN node does, and it decodes the GPS's position message. The decoder's test feeds it frames that pydronecan, the DroneCAN project's own Python library, built from the message definitions, so the check isn't my encoder agreeing with my decoder.
- **The SD card's log,** on FatFs (ChaN's FAT file system, a one-clause BSD license). The same ULog writer the sim uses writes to a FAT volume on a fake block device in the test, and the file reads back byte for byte.
- **The fuel gauge:** the battery's used charge, counted from the current, on PX4's battery message, so the ground station shows mAh used, not just volts.

None of this has run on a real chip. The register-level parts (DMA for the IMU and the motors, the I2C and CAN peripherals, the SD card) wait for a bench board.

## The ground station, for real

The last task's own test was the ground station talking to my firmware while it flies in the sim. I flew a hover on base at real speed with `pcs14 ground` listening on PX4's ground station port: it showed the drone in HOLD at 10.07 m, 24.5 V, 13.8 A and the limits profile, and when I set the heading gain from 2.8 to 2.75 on the page, the drone took it and the page read 2.75 back from it.

## What's next

Step 5 is done by its own test: my firmware and the safety monitor pass every scenario PX4 passes. The board's register-level drivers (the DMA for the IMU and the motors, the I2C and CAN peripherals, the SD card's bus) wait for a bench board, if I ever buy one.

Up next is step 6, the modules in sim. Some of it is already here from steps 4 and 5 (the parachute drop, the false-trigger count, the parachute rule). What isn't: the safety monitor firing the chute itself, a flight controller that hangs with the chute on, how low a chute still saves the drone, how hard the canopy pulls when it opens, HaLow as a link with a range, and the camera.

Open from this entry: the height estimate's 6 cm of barometer noise, and the safety monitor's latched cut, which is built and still mine to confirm.
