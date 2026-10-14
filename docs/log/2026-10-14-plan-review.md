# 2026-10-14: A second opinion, and rules as settings

*PC, Windows side. No code, just a review and a few decisions.*

Before building anything, I had Claude read the entire repo and poke holes in the plan. Here's what came back, what I decided, and what's still up for grabs.

## What I decided today

**Government rules are settings, not caps.** I want this drone to be able to do everything its hardware can do, and then I tune it down. So the FAA's 400 ft ceiling, Remote ID, and FCC radio power limits all get taken into account, but they live in a limits profile I switch from the ground station instead of being baked into the firmware. There's a `us-recreational` profile and a `max` profile, and whichever one is on gets written into every flight log. The safety rules (my kill switch always wins, the LLM never touches the motors) aren't government rules, so they don't change.

**HaLow for video.** I watched a YouTube build where someone strapped a $6 ESP32 board with a camera and a Wi-Fi HaLow radio onto a DJI Mini and streamed video into ATAK, the map app the military uses. It got pitched as a $40,000 defense drone for $120, which it really isn't: it was 2 frames per second at 60 feet. But HaLow itself is a great fit for my open video link. It's Wi-Fi on 900 MHz, with a lot more range than normal Wi-Fi, and it carries normal internet traffic, so telemetry and real video can share one link. It's now the lead option.

**A Meshtastic relay (#30).** The best idea in that video was putting a mesh node in the air. Radios like these need line of sight, and trees and hills break up a ground mesh. A node on the drone acts like a temporary cell tower and stitches it back together. It doesn't need to talk to the flight controller at all, and with its own GPS and battery it doubles as a lost-drone finder.

**2.4 GHz for control.** HaLow and Meshtastic both live in the 902–928 MHz band in the US, and so does 900 MHz ExpressLRS. The control link is the one thing that can never get drowned out, so it goes on 2.4 GHz.

## What the review flagged (not decided yet)

These go into the full plan revision next.

1. **The kill switch isn't independent when it matters most.** The Teensy that can cut the motors without my firmware lives in the parachute module, which doesn't get built until Phase 5. So the first flights of brand-new firmware would have a kill switch running inside the firmware it's supposed to stop. The suggestion: move the Teensy and its motor cut into Base, cut the ESC signal lines instead of the main power, and run the automatic triggers in log-only mode for a while first.
2. **The thrust-to-weight targets fight the battery.** Max's 3:1 at 2.5 kg means 7.5 kg of thrust. At full throttle that's something like 80–150 A from a Li-ion pack rated around 90 A, and Li-ion sags a lot near the end of a flight. Base's 4:1 never actually limits anything. The suggestion: one rule, at least 2.5:1 at the 20% reserve point, under load.
3. **Base's cruise time can't be measured on Base.** GPS lives in module V, so without it I can't hold or log a known speed. The suggestion: add hover-time targets, define cruise as one fixed speed, and count the battery reserve in mAh instead of volts.
4. **Phase 1 holds up too much.** Learning CFD, a CFD pipeline, an optimizer and a render pipeline all come before I can buy a $30 dev board. The CFD mostly refines drag, which moves flight time by a few percent, while manufacturer thrust data can be off by 15–20%. The suggestion: shrink the Phase 1 gate to sizing, CAD and PX4 in Gazebo, buy one motor and prop for the thrust stand now, and fly the plain X before the design hunt.

Smaller ones: the Remote ID module isn't in any weight estimate yet, Max could land anywhere from about 2.25 to 2.7 kg, the flight controller board needs SWD pads for debugging, meshes should be regenerated from the CAD code instead of committed through Git LFS, and it's worth deciding whether Part 107 makes more sense than flying under the recreational rules.

## Also

The PC turns out to have a Ryzen 7 9800X3D, not an i7. I'd written it down wrong. Fixed everywhere.

## Next

The full plan revision. Everything above gets folded into one plan, I read it start to finish and confirm it, and then building starts.
