# Decisions

Every call I've made on this project, and why. Started 2026-10-13. When something changes, it changes here first.

## The idea

I want a fairly big, fairly fast quadcopter with a camera and GPS, running flight firmware I wrote myself. The point is to learn by building it.

- **Hardware:** parts I can order. Dev boards, breakout boards, ESCs, motors, a receiver. No custom PCB, because I don't want to sit around waiting on fab and shipping.
- **Firmware:** mine. Starting from open-source flight code and adapting it is fine. I'll pick up PID and control theory as I go.
- **Airframe:** a quad on 8–10" props with low-KV motors and a Li-ion pack, built to fly long (roughly 25–40 minutes cruising). I looked at a VTOL quadplane and dropped it. Way too much complexity for a first build.
- **Budget:** around $1,000, but parked for now. Pricing happens after the simulation work, not before.
- **Name and home:** Extra 15pc Gum, in a public GitHub repo (`extra-15pc-gum`) under GPL-3.0. The repo is how I move between machines, and [STATUS.md](../STATUS.md) always says where I am.
- **Building in public:** I'm posting the whole process. That means:
  - respecting the licenses of any code I reuse (a lot of flight code is GPL)
  - scrubbing home and launch GPS coordinates from anything I post
  - making the CAD and sim produce stuff worth showing, for the repo and then my portfolio
- **Not monetizing any of it.** This is purely for learning, and because it's a really cool project. That keeps me under the FAA's recreational rules.
- **What I know going in:** soldering, embedded programming, and flying RC.

### Simulate first, then buy

Nothing big gets bought until it has flown in simulation. The one exception (revised 2026-10-14) is small test parts that make the simulation more accurate, like a motor, a few props and the ESC for the thrust stand. Most of those end up on the drone anyway. The loop is:
1. pick parts and a shape
2. run the sizing model, with measured thrust data as soon as the thrust stand has some
3. build it in CAD
4. fly it in Gazebo
5. check it against the targets
6. improve it and go again

It only gets priced once it passes. The virtual wind tunnel runs alongside the loop instead of inside it: its numbers sharpen the sizing model and Gazebo whenever they arrive, but the baseline doesn't wait for them.

Five layers:

1. Sizing model (my own Python tool)
2. CAD, written as code (build123d), by Claude
3. Aerodynamics: CFD, the digital version of a wind tunnel (runs alongside, see below)
4. Flight sim: Gazebo Harmonic + PX4, flown by proven firmware first
5. My own firmware flying the same Gazebo sim

This is partly about money and partly about my career, because simulation is a skill I want. I'll test two ways:
- **Software-in-the-loop:** the flight code is compiled for the PC and flies in the sim.
- **Hardware-in-the-loop:** the real chip runs the code while the sim feeds it fake sensor data.

Both only work if the flight logic stays separate from the hardware drivers, so the same code runs everywhere.

The simulator is Gazebo Harmonic + PX4 on Ubuntu 24.04: native on the PC, WSL2 on the laptop. It's what the industry actually uses.

### CAD in code, then hunt for a unique design (decided 2026-10-13)

Claude writes all the CAD as Python code with build123d, reading from the parts files. Change a part and the model rebuilds itself. It spits out:
- the center of gravity and inertia
- meshes for the sim and for CFD
- STEP files
- renders

It happens in two steps:

1. **Baseline first.** A plain, simple X quad, run through sizing, CAD and Gazebo until the pipeline works end to end. This is the one I buy, build and fly (decided 2026-10-14).
2. **Then the automation.** Build a design, test it, read the results, improve it, repeat, hunting for a drone design that's actually unique. The fast sizing model filters thousands of candidates; only the promising ones get the slow CFD and Gazebo runs. It runs alongside everything else, and whatever it finds becomes v2.

What counts as "unique" (stay a quad, or open it up to other layouts) gets decided once the baseline works, since leaving the quad layout would change the firmware too. One knock-on effect: a unique layout probably means a custom frame, either CNC-cut carbon plates from my own files or carbon tubes with printed joints, instead of a bought one.

### Aerodynamics (decided 2026-10-13)

I want to see the air moving around the drone, like smoke in a wind tunnel, and I want the numbers that come with it. This is CFD, and it's its own layer between CAD and Gazebo. It tiers by how much detail it needs:

- **Everyday runs: OpenFOAM.**
  - The props are modeled as disks pushing air.
  - The runs cover:
    - drag at different speeds and tilts
    - how much the prop wash pushing down on the frame and modules costs in thrust
    - ground effect
    - crosswind
  - About an hour or two per run on the PC.
  - The results replace the guessed drag in the sizing model and feed Gazebo's wind and drag.
  - It's open source and the industry standard.
- **Showcase runs: FluidX3D on the RTX 3060.**
  - Fully spinning props, for the realistic tip-vortex visuals.
  - Its license allows personal and educational use, but if I publish results from a modified copy, I have to publish the modified source too. That doesn't mix with this repo's GPL, so my FluidX3D setup lives in a separate public fork, clearly marked as modified.
  - The fallback is OpenFOAM with rotating meshes, which is slower but one tool.
- **Visuals:** ParaView renders the streamlines, smoke-style traces and pressure maps.
- **Keeping it honest:** first check OpenFOAM against shapes with known drag, then against published drone data, then against my own flight logs once I have them.
- **Where it runs:** the PC. The laptop only manages coarse test runs.
- **When it runs (decided 2026-10-14):** alongside the phases, never blocking one. At a 10 m/s cruise, drag is roughly 10% of the power, so even a 30% drag error moves flight time by about 3%. That's well inside the uncertainty in manufacturer thrust data. Drag matters more for the 80 km/h top speed, and that number gets rechecked whenever the CFD results arrive.

### Visuals are part of the output (decided 2026-10-13)

I'm posting the whole process, mostly on LinkedIn and sometimes on Instagram, so it has to look good to people scrolling past, not just to me.

- Every layer produces shareable visuals as a normal output:
  - CAD renders
  - CFD flow images and animations
  - sizing charts
  - Gazebo flight clips
- **One consistent look across everything (locked 2026-10-13): "wind tunnel."** The details are in [style.md](style.md).
  - black background, chalk text, spearmint accent, magenta for the one thing that has to pop
  - turbo for CFD color fields
  - Space Grotesk, Inter and JetBrains Mono for type
- **What the CFD images show:**
  - surface pressure, so you can see where the air hits hardest
  - streamlines colored by speed
  - prop wash
  - a "which part costs the most drag" chart, which is also the most useful one for the design hunt
- Exports in the sizes the platforms want:

  | Format | Size |
  |---|---|
  | 4:5 portrait | 1080×1350 (works on both platforms) |
  | 1:1 square | 1080×1080 |
  | 9:16 vertical | 1080×1920 (Reels and Stories) |
  | 16:9 | 1920×1080 (video) |

  Plus PDF carousels for LinkedIn.
- Blender, scripted from Python and rendering on the RTX 3060, does the hero shots and turntables of the CAD model.
- Curated, compressed stills live in the repo. Raw renders and videos stay out of it and go straight to the posts.


### Learning (decided 2026-10-13)

I'm new to a lot of this, CFD especially. Tutorials and studying happen on my own time, offline, and building happens online. They don't get mixed. Everything I should learn, with resources, lives in [learning.md](learning.md), and it grows as new topics come up.

### My machines

- **Laptop:** Lenovo, Core Ultra 7 155U, 16 GB, Intel integrated graphics, WSL2 Ubuntu 24.04 (capped at about 7.6 GB of RAM). Gazebo runs, but scenes have to stay simple. No NVIDIA GPU, so no Isaac Sim and no decent local LLM.
- **PC:** dual boot, Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060. The sim lives on its Ubuntu 24.04 side. **It's the main machine from 2026-10-14**, set up with [setup-pc.md](setup-pc.md). The laptop is for docs, light work and the field.
- Every machine runs the same checks (`scripts/check-machine.sh` and `scripts/setup-dev.sh`), and the results are logged in [machines/](machines/).

### Build stages

1. Get it flying on my firmware: rate mode, then self-level, then altitude hold.
2. Add the camera.
3. Add GPS: position hold, return to launch, waypoints.

The [roadmap](roadmap.md) breaks this down much further.

## What's locked in

### Laptop ground station

It lives on the laptop, not the drone, with live telemetry from day one: attitude, motor outputs, battery, GPS, link quality, logs, and PID tuning while it flies. This isn't an extra. It's how I'm going to get the thing flying at all.

### Smart landing

I pick where it lands:

| Mode | What it does | Needs |
|---|---|---|
| Land now | Comes down right where it is | Stage 1 + rangefinder |
| Back to start | Flies back to where it took off and lands | GPS + compass |
| Land here | Lands on a spot I click on the map | GPS + compass |
| Nearest safe spot | Flies to the closest safe landing zone from a 3D map of the area (#7) | GPS + a 3D map of the area |

Finding safe spots happens on the laptop. From the 3D map, look for ground that's flat, smooth, and clear of trees, buildings and wires for a decent radius. Those become a list of GPS points sent to the drone. If I haven't mapped the area, it falls back to back to start.

It also lands on its own when things go wrong:

- Lost radio link: back to start
- Low battery: back to start or the nearest safe spot, whichever it can reach
- Critical battery: land now
- Lost GPS: level itself and land, or hand control back to me
- Out of control or falling: parachute

**Extra hardware this needs:** a downward lidar (TF-Luna or TFmini-S) for the last few meters, because GPS and the barometer aren't precise enough near the ground.

**Maybe later:**
- RTK GPS for landings accurate to the centimeter (normal GPS is good to about 1–3 m).
- A quick camera check before touchdown, in case someone has parked on my safe spot since I mapped it.

### Parachute

- It fires on free fall or loss of control, detected from the accelerometer and attitude. I can also fire it by hand.
- The motors cut before it deploys, or the props eat the lines.
- The safety monitor in Base (below) can fire it as well as the main flight controller, so if my firmware crashes, the parachute still works.
- It needs about 10 m to open, so it won't save a crash from low down.
- It adds roughly 100–150 g.

### The LLM lives on the laptop

I wanted an LLM in the loop, and it makes far more sense on the laptop than on the drone: no extra weight, no power draw, and a much smarter model. It'll probably be a cloud model, since this laptop can't run a good local one.

What it does:
- turns plain-English missions into flight plans (#26)
- looks at photos and 3D maps
- explains what changed between mapping runs
- reads flight logs when something wobbles

If the link drops, I lose the LLM, but nothing depends on it.

The rules that don't bend:

- The LLM never touches the motors. It writes a plan (waypoints and actions), and that's all.
- A plain, deterministic checker validates every plan against the limits profile that's loaded: geofence, altitude ceiling, battery reserve, speed limits.
- I approve the plan before it goes to the drone. Simple stuff like "land" or "come back" maps straight onto the landing modes.
- The flight controller flies the plan and can override it at any time. My transmitter and kill switch always win.
- If the companion computer crashes or freezes, the flight controller notices the missing heartbeat and holds position or comes home.

### Safety basics

- Pre-arm checks: sensors healthy, battery OK, GPS lock when it's needed, and a live safety monitor
- A kill switch on the radio, reaching the motors through two separate boards (see the safety monitor below)
- A geofence: whatever I draw for the day, or none. The flight controller enforces it itself, not just the plan checker.
- A hung CPU means the motors stop, not the motors stuck at the last throttle: a hardware watchdog, and DShot frames sent fresh every loop instead of from a free-running DMA loop that keeps resending the last one.
- The low-battery failsafe counts mAh used, with voltage as a backup. Li-ion's flat curve and sag make voltage a bad fuel gauge.

### The safety monitor (decided 2026-10-14)

The Teensy 4.1 used to live in module P, which wouldn't be built until Phase 5. That meant the first flights of brand-new firmware would have a kill switch running inside that same firmware. So it moved into Base.

- It has its own IMU, and it listens to the same receiver as the flight controller (the receiver's output wire splits to both). The kill switch reaches the motors through two separate boards running separate code. A second receiver would add more independence, but the thing I'm protecting against is my firmware, not the receiver.
- It cuts the motors by blocking the four ESC signal lines with an analog switch, not by switching the main power. A switch in a ~100 A power line is a new way to drop a healthy drone, and ESCs stop the motors when their signal disappears (to be confirmed on the bench). It has to pass signals both ways, because bidirectional DShot sends RPM back on the same wire.
- It fails in the useful direction. If the Teensy loses power, the switch passes signals and the drone keeps flying on the flight controller. The flight controller watches the Teensy's heartbeat, warns me if it goes quiet, and won't arm without it.
- The automatic triggers (free fall, tumbling, the flight controller going quiet) start in shadow mode: they log what they would have done, and do nothing. They go live in Phase 5, after enough flights with zero false triggers. A fast descent at low throttle looks a lot like free fall to an accelerometer, so this matters. The 4.1's SD card handles the logging.
- When P is fitted, it can fire the chute too, after cutting the motors.

### Government rules are settings, not caps (decided 2026-10-14)

I want the drone to be able to do everything its hardware can do, and then I tune it down if I want to. So rules that come from the government (the FAA's 400 ft ceiling, Remote ID, airspace, FCC limits on radio power) get taken into account when planning, but they don't get baked into the design as hard limits.

- **Hardware is sized for what's physically possible.** For a drone this size the law barely touches the hardware anyway. The one exception is Remote ID: Base gets a mount and a 5 V plug for a broadcast module, and I decide whether to fit it. The firmware doesn't refuse to arm without it.
- **The legal numbers live in a limits profile.** Two to start, switched from the ground station:

  | Profile | What it sets |
  |---|---|
  | `us-recreational` | 400 ft ceiling, Remote ID expected, radios on their US (FCC) power and frequency settings |
  | `max` | Only physical limits: what the battery, motors and radios can actually do |

- **The plan checker runs either way.** It's just as strict; it checks against whichever profile is loaded.
- **I always know which one is on.** The active profile shows on the ground station and gets written into every flight log.
- **Radio transmit power is a setting per radio.** The firmware doesn't cap it below what the hardware can do.
- **Planning still names the rule.** When a plan runs into a regulation, the notes say what the rule is and what it means for me, and then the design carries on around what the hardware can do.

What this doesn't touch: the engineering safety rules. My transmitter and kill switch always win, the LLM never commands the motors, and the failsafes stay as designed. The parachute rule (no autonomous missions or flights above about 30 m without P) is my own rule, not the government's, so it stays too.

### Modular design (locked 2026-10-13)

The frame, motors, ESC and battery are sized for the heaviest setup, but the drone flies bare first. Modules go on and off depending on what I'm doing that day.

Base is always on: frame, motors, ESC, battery, flight controller, receiver, rangefinder, the safety monitor, and a mount and plug for a Remote ID module. It flies by itself.

| Module | What's in it | Notes |
|---|---|---|
| **V: Vision & nav** | GPS + compass, camera(s), companion computer, HaLow video link | GPS and camera go together, because mapping, safe-spot landing and GPS-free flight all need both |
| **P: Parachute** | The chute and its ejector | The flight controller or the safety monitor can fire it. See the parachute rule below |
| **C: Claws** | Claws + servos | Works without V, but you'll want the camera to see what you're grabbing |

- **The parachute rule:** the firmware checks whether P is fitted, and won't fly autonomous missions or go above about 30 m without it. The chute needs about 10 m to open anyway, so there's no point carrying it for low hover tests.
- **A standard module mount (#17):** one mechanical interface, and one connector carrying power and a data bus.
  - The firmware sees which modules are on and loads a tuning profile to match. The self-tuning controller (#21) then fine-tunes in flight.
  - The bus is still open: plain serial, or DroneCAN (the industry standard for drone add-ons; the H743 has CAN hardware).
- **Ballast:** until a module exists, I bolt weights to its mount so I can still test at full weight.

### Target specs (locked 2026-10-13, revised 2026-10-14)

The sim checks all eight module combinations. Base and Max are the extremes, and anything in between has to land between them.

| Setup | Modules | Cruise time | Hover time | Other |
|---|---|---|---|---|
| **Base** | none | ≥ 30 min | ≥ 25 min | |
| **Mission** | V + P | ≥ 25 min | ≥ 21 min | Top speed ≥ 80 km/h; holds position in 10 m/s wind |
| **Max** | V + P + C, carrying 250 g | ≥ 20 min | ≥ 17 min | Total weight ≤ 2.5 kg |

For every setup:
- Thrust-to-weight of at least 2:1 at the 20% reserve, at full throttle, under load.
- Full-throttle current stays inside the pack's continuous rating.
- It lands with at least 20% of the battery left, counted in mAh.
- Cruise means 10 m/s for now. The sizing model works out which speed actually uses the least power, and that replaces 10 m/s if it's very different.

What changed on 2026-10-14, and why:
- **Hover times got added.** Base has no GPS, so its cruise time can't be measured until Phase 6. Hover time can be measured in Phase 4. A quad uses a bit less power at a gentle cruise than in a hover, because moving forward keeps feeding the props fresh air, so the hover targets sit about 15% under the cruise ones. The sizing model checks that ratio.
- **One thrust-to-weight rule replaced 4:1 for Base and 3:1 for Max.** The old ones didn't say when they're measured, and Base's 4:1 never limited anything, because the motors are sized for Max. Motor test data is usually measured on a bench supply at full 6S voltage, and full-throttle thrust drops roughly with the square of the voltage. A rough estimate says a Li-ion pack at 20%, under full load, leaves each motor with about 55–60% of its datasheet thrust. So 2:1 at the reserve works out to about 3.5:1 on the datasheet. The sizing model reports both.

If the sim says these numbers are unrealistic, I'll change them and explain why here. The machine-readable version is [design/targets.yaml](../design/targets.yaml).

### Mass budget (2026-10-14)

Rough numbers until the sizing model and the CAD replace them.

| Part | Estimate |
|---|---|
| Battery (6S2P 21700 Li-ion, about 9 Ah) | 850–900 g |
| Frame and module mount | 250–350 g |
| Motors (4) | 240–360 g |
| Props (4) | 40–70 g |
| ESC | 20–35 g |
| Flight controller, receiver, rangefinder, wiring | 60–90 g |
| Safety monitor (Teensy, IMU, signal switch) | 15–30 g |
| Remote ID module, when fitted | 15–40 g |
| **Base** | **about 1.5–1.9 kg** |
| V | 200–300 g |
| P | 120–200 g |
| C, plus the 250 g it's holding | 350–450 g |
| **Max** | **about 2.15–2.8 kg** |

Max only makes 2.5 kg if most parts land at the light end. Checking that is the sizing model's first job. If it doesn't fit, the options are raising the cap (it's my own target, not a law) or a lighter payload.

### Roadmap

The phases live in [roadmap.md](roadmap.md). It's the plan I'm following, and it will change. The full revision on 2026-10-14, with every change tagged R1 to R7 and the reason for each, is in [specs/2026-10-14-plan-revision.md](specs/2026-10-14-plan-revision.md).

## Hardware (draft)

Three layers, plus a safety monitor underneath them all. Each one has to stay safe if the one above it dies:

1. **Flight controller:** the hard real-time stuff. It reads the sensors, runs the PID loops, drives the motors, and handles the failsafes, the parachute and self-tuning (#21). It doesn't depend on anything above it.
2. **Companion computer** (Pi 5 or Jetson Orin Nano): cameras, GPS-free navigation (#24), and photos for mapping. It sends targets down to the flight controller.
3. **Laptop:** telemetry, the map, the LLM (#26), mission approval, 3D map processing, safe spots, and change detection (#11).
4. **Safety monitor:** the Teensy in Base, independent of all three (see above).

Parts so far:

- **Frame:** for the baseline, an 8–10" carbon X frame with the module mount, bought. Printed arms would flex too much at this size. If the design hunt finds something unique, the frame goes custom (see above).
- **Motors:** low-KV, 6S, picked from thrust data once the prop size is settled.
- **ESC:** 4-in-1, 6S, with bidirectional DShot, so I get RPM from every motor. That's great for filtering and for #21. AM32 is open-source ESC firmware, which is a nice bonus.
- **Battery:** 6S2P Li-ion from 21700 high-drain cells, around 9 Ah and 850–900 g. The sizing model also tries 6S3P, in case the extra cells earn their weight.
- **Flight controller (decided):** a Nucleo-H743 on the bench, which gives me a proper debugger, every pin broken out, and hardware-in-the-loop testing. An off-the-shelf STM32H743 flight controller board goes in the drone. Same chip, same firmware. The board has to be one PX4 supports, with SWD pads I can get a debugger onto.
- **Teensy 4.1:** I already have one lying around, and I'm buying a second (about $30) in Phase 2 so each can keep its own job:
  1. Run the thrust stand (from Phase 1): read the load cell, current and voltage, drive the ESC, and log to its SD card.
  2. Desk sandbox: dRehmFlight with a cheap IMU and no motors, so I can watch a complete flight controller work before I write mine.
  3. Be the safety monitor in Base (the second Teensy): its own IMU, listening to the receiver, cutting the motors on the ESC signal lines, and firing the chute when P is fitted.

  It could also be a hardware-in-the-loop bridge, pretending to be the GPS, receiver and rangefinder for the sim. It's no good for the wristband, though: no wireless. That's an ESP32 job.
- **Companion computer:** not needed until stage 2. A Pi 5 is probably enough now that the LLM is on the laptop; a Jetson if #24 needs more.
- **IMU:** ICM-42688-P (it's on most modern flight controller boards anyway).
- **Barometer:** on the flight controller board.
- **GPS + compass:** a u-blox M10 module with compass, up on a mast away from the power wires.
- **Rangefinder:** downward lidar (TF-Luna or TFmini-S).
- **Control link:** an ExpressLRS receiver and a handheld transmitter, on 2.4 GHz. HaLow and Meshtastic (below) both use 902–928 MHz in the US, and so does 900 MHz ExpressLRS, so the control link stays off that band. Its protocol (CRSF) is well documented and easy to parse.
- **Data/video link to the laptop:** the lead option (2026-10-14) is Wi-Fi HaLow (802.11ah), which is Wi-Fi on 900 MHz. It has a lot more range than normal Wi-Fi, with a few Mbps up close dropping to hundreds of kbps far out. It carries normal IP traffic, so MAVLink telemetry and real compressed video can share one link from the companion computer, and existing ground station software works while I build my own. The same video could go into ATAK too (the free civilian version runs on Android). One catch: the Pi 5 has no hardware H.264 encoder, so video encoding runs on its CPU, which counts when picking Pi vs Jetson. Confirmed in Phase 6.
- **Remote ID:** a broadcast module on a mount and 5 V plug in Base. Whether it's fitted is up to me (see the limits profiles).
- **Power:** a dedicated 5 V / 5 A+ supply for the companion computer, and a current sensor (usually on the ESC).
- **First thing I'll build:** a thrust stand (load cell, HX711 amplifier, current sensor) to measure how efficient the motors and props really are, and feed that back into the sim. It happens in Phase 1, as soon as the sizing model has a shortlist, running off a real 6S pack so the voltage sag gets measured too.

## Shortlist (not final)

- **#2 Wrist gesture control:** fly by tilting an ESP32 + IMU wristband.
- **#7 3D mapping runs:** fly a GPS grid taking photos, and turn them into a 3D model with OpenDroneMap. The nearest-safe-spot landing depends on this.
- **#8 Perching claws:** grab a branch or a railing, motors off, camera still rolling. This is module C.
- **#10 Wind sensing:** work out the wind from how hard it leans to hold position. Software only. It feeds a "turn back now" battery warning and smarter landing choices.
- **#11 Change detection:** compare two mapping runs and flag what moved, so the safe spots stay safe.
- **#21 Self-tuning:** tunes its own PID in flight, and re-tunes when the payload changes. Runs on the flight controller.
- **#24 GPS-free flight:** navigates with the camera and IMU, so it can still get home if GPS drops. Runs on the companion computer.
- **#26 Plain-English missions:** the laptop LLM turns what I say into checked plans that I approve.
- **#30 Meshtastic relay:** a small LoRa mesh node riding on the drone. Radios like this need line of sight, so trees and hills break up a ground mesh; a node in the air works like a temporary cell tower and stitches it back together. It doesn't talk to the flight controller at all, just 5 V and an antenna, and with a GPS of its own and a small battery it doubles as a lost-drone finder. LoRa is far too slow for video (a few kbps at most), so video goes over HaLow.

## Ideas pool

Everything that came up while brainstorming, so nothing gets lost.

| # | Idea | Status |
|---|---|---|
| 1 | Tilt-rotor flight (camera stays level without a gimbal) | Not picked |
| 2 | Wrist gesture control | Shortlist |
| 3 | Precision landing on a printed marker | Replaced by smart landing |
| 4 | Web ground station | Locked in (laptop) |
| 5 | Free-fall detection + parachute | Locked in (module P) |
| 6 | Thermal vision overlay | Not picked |
| 7 | 3D mapping runs | Shortlist (needed for safe-spot landing) |
| 8 | Perching claws | Shortlist (module C) |
| 9 | Follow the wristband | Maybe |
| 10 | Wind sensing + "turn back now" battery warning | Shortlist |
| 11 | Change detection between mapping runs | Shortlist |
| 12 | AR overlay on live video | Maybe |
| 13 | Laser "measure anything" | Maybe |
| 14 | Payload winch | Maybe |
| 15 | Amphibious (float landing gear) | Maybe |
| 16 | Repeat-shot time-lapse | Maybe |
| 17 | Modular payload bay | Locked in (the module mount) |
| 18 | VTOL quadplane (adds a wing) | Dropped: too complex, went long-range quad instead |
| 19 | Listening post: microphones locate sounds while perched with motors off | Maybe |
| 20 | Sniffer drone: follows a gas or smoke plume to its source | Maybe |
| 21 | Self-tuning controller | Shortlist |
| 22 | Neural-network controller trained in the sim, run on the real drone | Maybe |
| 23 | Motor-failure survival: spins and lands on 3 motors before the parachute | Maybe |
| 24 | GPS-free flight | Shortlist |
| 25 | Haptic wristband: buzzes for obstacles, battery and direction home | Maybe |
| 26 | Plain-English missions via the laptop LLM | Shortlist |
| 27 | Charging dock: lands on a pad, recharges, takes off again | Maybe |
| 28 | Sensor pucks: drops little sensor beacons, collects them later with the claws | Maybe |
| 29 | Toroidal props: looped propellers that are meant to be quieter | Maybe |
| 30 | Meshtastic relay node: the drone as a temporary cell tower for a ground mesh, plus a lost-drone finder | Shortlist |

## Notes

- **Weight:** see the mass budget above. The modules plus the heavier Li-ion pack are why it's 8–10" props.
- **Making a quad fly longer**, biggest lever first:
  1. bigger, slower props on low-KV motors
  2. Li-ion instead of LiPo
  3. cutting weight ruthlessly
  4. efficient firmware: clean filtering, an eco cruise speed
  5. landing or perching to wait with the motors off

  A 7" on Li-ion might manage 20–30 minutes, and 8–10" more than that.
- **Legal (US):**
  - Over 250 g means FAA registration, Remote ID and the TRUST test. This is recreational flying only.
  - Near airports a lot of the airspace is controlled, so I'll need LAANC authorization there.
  - How these show up in the design: see "Government rules are settings, not caps" above.

## Still open

- Final pick of the extras
- Exact prop size: 8, 9 or 10". The sizing model decides.
- Cell type, and 6S2P vs 6S3P. The sizing model decides.
- Cruise speed: 10 m/s until the sizing model says otherwise
- Which open-source flight code to start from (the chip is decided: STM32H743)
- Which H743 board. It needs PX4 support for the baseline flight, and SWD pads.
- How many clean shadow-mode flights before the safety monitor's automatic triggers go live (picked from the Phase 4 logs)
- Whether to get Part 107 (before Phase 3)
- Data/video link to the laptop: HaLow is the lead option, confirmed in Phase 6 (the control link is decided: 2.4 GHz ExpressLRS)
- Where the Meshtastic relay (#30) lives: in V, in Base, or as its own little module
- Exactly what goes in the `us-recreational` limits profile, checked against the current FAA and FCC rules before Phase 3
- Camera: FPV video, stills for mapping, or both
- Module bus: serial or DroneCAN
- What "unique" is allowed to mean for the design hunt (decided after the baseline works)
- Which OpenFOAM: the Foundation release (openfoam.org) or ESI's (openfoam.com). Both have the tutorials I need. Decided when writing the setup script.
