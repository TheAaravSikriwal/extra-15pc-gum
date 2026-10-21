# Modules in sim (step 6)

*Written 2026-10-20. I asked for the open items to keep moving without stopping to ask, so I made these calls myself and wrote down why. The calls that are mine to make stay open below: P in every combination, optical flow in Base, the HaLow card, the claws, and the latched cut.*

## What it has to do

From the [roadmap](../roadmap.md#step-6-modules-in-sim): each module passes its tests in every combination it's part of.

- **P (parachute):** deployment with a drag model, the opening jolt for the structure track, the motor-cut timing, the false-trigger replay, and the parachute rule in the firmware.
- **V (vision and nav):** a simulated camera and GPS, HaLow as a link with range against bitrate and its dropouts, video to the laptop, and the companion computer's jobs, which settle the Pi 5 against a Jetson.
- **C (claws):** only if a unique claw on an actual arm comes up. Until then the claws are a placeholder.

## What's already done

Steps 4 and 5 covered more of this than the roadmap expected.

| Module | Already done | Where |
|---|---|---|
| P | The canopy as a drag model, sized from Fruity Chutes' rating; the 40 m drop in all four P combinations, graded on the motors stopping before the canopy leaves and the height lost | step 4's drop scenario |
| P | A dead motor with P fires the chute | step 4 |
| P | No false triggers from the safety monitor's reference triggers in 66 healthy PX4 runs | step 4d |
| P | The parachute rule in my firmware, with its own tests | step 5, task 9 |
| V | The GPS, its failure, and the lost link | steps 4 and 5 |
| C | The payload grab with the placeholder claws | step 4 |

## What's left, and how I'll do it

**P: the safety monitor fires the chute.** The safety rules say the flight controller or the safety monitor can fire it, and the electrical design gives the Teensy its own release line (pin 37) and the right to take the release servo's line from P's node (pin 31). The monitor's firmware has neither yet. It gets a chute command from the pilot's switch (a CRSF channel it already hears), and in the sim it drives the chute the way the flight controller does. The order is fixed: it cuts the motors first, every time, and the release goes high only once the stop frames are going out. Its automatic triggers stay in shadow mode, so in the air only the pilot fires it from the monitor.

**P: the flight controller is dead and the pilot fires the chute.** The scenario I care about most: the flight controller freezes at 40 m, the monitor sees its heartbeat stop and cuts the motors, and the pilot flips the chute switch. Graded the same way as the drop: the motors stop before the canopy leaves, and the height lost.

**P: how low a chute still saves it.** Drops from 10, 15, 20, 30 and 40 m in Max, the heaviest, to find the lowest height where the canopy settles before the ground. That's the "about 10 m" in decisions.md, measured.

**P: the opening jolt.** The sim's canopy opens over its opening time with its drag area growing in a straight line, so Gazebo's acceleration during the opening gives one number for the peak force on the drone. That's optimistic: real canopies overshoot as they fill. So the report also gives the textbook bound, the opening-force coefficient times the dynamic pressure times the drag area, with the coefficient from Knacke's *Parachute Recovery Systems Design Manual*. The structure track gets both, in newtons and in g, at the speed the drone is falling when the canopy opens.

**P: the false-trigger replay on my firmware.** The same count as step 4d, over my firmware's 78 runs.

**V: HaLow as a link.** A model of the link from the radio's own numbers: 802.11ah's rates at each modulation and coding scheme on a 2 MHz channel, the card's transmit power (21 dBm), the receiver sensitivity at each rate, the antennas' gain, and the path loss at 915 MHz with the ground's reflection. Out of it comes the rate the link can hold at each distance and height, and where it starts to drop packets. In the sim it becomes a relay between the ground station and the drone that delays and drops packets the way the model says at the drone's distance, so a flight past the link's range shows what my firmware does when the data link fades out. The control link (ExpressLRS at 2.4 GHz) is separate and stays as the sim has it.

**V: the camera and the video.** A camera on V's model in Gazebo, the Camera Module 3's field of view and frame rate, its frames recorded through a scenario. Then the video the laptop would see: the frames encoded at the bitrate the HaLow model allows at each distance, so the picture's quality against range is something to look at, not just a number. Whether Gazebo's camera renders in WSL without a GPU is the first thing to find out; if it doesn't, the camera moves to Windows' Gazebo or waits.

**V: the companion computer's jobs.** The jobs that have to stay on board (the video encode, GPS-free flight, photos for mapping) against what a Pi 5 and a Jetson Orin Nano can do, from published benchmarks, with a note on what each costs in grams and watts. Decisions.md already leans to the Pi 5 because the LLM and the object detector run on the laptop; this puts numbers on it. One thing already known: the Pi 5 has no hardware video encoder, so the encode is on its CPU.

**C: waits.** The claws stay the placeholder until the claw conversation, which is mine to have. The payload grab keeps running in every C combination.

## Settled here

- **The monitor fires the chute only on the pilot's command, for now.** Its automatic triggers have shown no false triggers in 66 PX4 runs, but the rule says they stay in shadow mode until they've shown zero, and "shown" is a call I want to make on real flights, not on a sim's clean IMU.
- **The opening jolt gets two numbers, the sim's and the textbook bound,** and the structure track designs to the bound.
- **HaLow is modeled from the chip maker's numbers,** since Heltec publishes no sensitivity for its card: Morse Micro's for the MM6108 module (21 dBm out, -103 dBm at the slowest rate on a 2 MHz channel), marked as estimates for Heltec's card. The card swap (mine to decide) changes a couple of numbers in the model, not the model.

## Not settled yet

- Whether Gazebo's camera renders headless in WSL.
