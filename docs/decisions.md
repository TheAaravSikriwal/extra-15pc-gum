# Extra 15pc Gum — Decisions Log

Running record of what's been decided while planning. Started 2026-10-13.

## Project goal

Build a fairly large, fast quadcopter with a camera and GPS, running **my own flight firmware**, to learn by building.

- **Hardware:** off-the-shelf modules and breakout boards (MCU dev board, IMU breakout, ESCs, motors, radio receiver) wired together. **No custom PCB** — too slow to wait on fab/shipping.
- **Firmware:** my own, but starting from open-source flight-controller code and adapting it to this drone is fine. PID and control theory learned along the way.
- **Airframe:** quadcopter with **8–10" props on low-KV motors and a Li-ion pack**, built for long flights (roughly 25–40 min cruising). Quadplane dropped to keep it simpler.
- **Budget:** about $1,000 total, but **set aside for now**. Pricing comes after the simulation work.
- **Public build log:** the whole process will be posted online. So:
  - Respect the licences of any reused code (many flight-control projects are GPL).
  - Strip home and launch GPS coordinates from any logs or maps before posting them.
  - Have the CAD and simulation produce shareable visuals.
  - If the content will be monetised, check the FAA's Part 107 rules.
- **Next step: simulate first, then buy.** Design loop: pick candidate parts → sizing model → CAD mock-up → physics sim → check against the target specs → swap parts → repeat. Price it once the specs are met.
- **Simulation layers (all four chosen):**
  1. Sizing model (my own Python tool)
  2. 3D CAD mock-up (Onshape, public documents)
  3. Physics sim: **Gazebo Harmonic + PX4** (decided), flown by proven firmware
  4. My own firmware in the same Gazebo sim
- **Dev laptop:** Lenovo with an Intel Core Ultra 7 155U, 16 GB RAM and integrated Intel graphics (no NVIDIA GPU), 155 GB free. WSL2 Ubuntu 24.04 with WSLg is already installed (WSL is capped at ~7.6 GB of RAM).
  - No NVIDIA GPU rules out Isaac Sim.
  - Gazebo will run, but scenes need to stay simple.
  - The laptop LLM should be a cloud model; a strong local model won't run on this hardware.
- **Name & repo:** Extra 15pc Gum, a public GitHub repo (`extra-15pc-gum`) under GPL-3.0. The repo is the single source of truth across machines; see `STATUS.md`.
- **Main sim machine (PC):** dual boot. The simulation runs on native Ubuntu 24.04, with an i7, 32 GB DDR5 and an RTX 3060.
- **Experience:** soldering, embedded programming, flown RC aircraft.
- **Staged build:**
  1. Get it flying on my own firmware (rate mode → self-level → altitude hold)
  2. Add the camera
  3. Add GPS (position hold, return-to-launch, waypoints)

## Base spec (decided)

### Laptop ground station
Runs on a laptop, not on the drone. Live telemetry output is required from day one: attitude, motor outputs, battery, GPS, link quality, flight logs, and live PID tuning. Not counted as an "extra" — it's core.

### Smart landing
The pilot chooses where it lands:

| Mode | Behaviour | Needs |
|---|---|---|
| Land now | Descends and lands where it is | Stage 1 + rangefinder |
| Back to start | Returns to the takeoff point and lands | GPS + compass |
| Land here | Pilot clicks a spot on the ground-station map | GPS + compass |
| Nearest safe spot | Flies to the closest safe landing zone found by a 3D mapping run of the area (#7) | GPS + 3D map of the area |

**Safe-spot detection (laptop side):** from the 3D map, find areas that are flat (low slope), smooth, and have a clear radius free of trees, buildings and wires. Upload them to the drone as a list of GPS points. If the area hasn't been mapped, fall back to "Back to start".

**Automatic triggers (failsafes):**
- Radio link lost → Back to start
- Battery low → Back to start or nearest safe spot, whichever it can reach
- Battery critical → Land now
- GPS lost → self-level and land now (or hand control back to the pilot)
- Out of control or in free fall → parachute

**Hardware this adds:**
- Downward lidar rangefinder (e.g. TF-Luna / TFmini-S) for the last few metres and a soft touchdown. GPS and barometer aren't precise enough near the ground.
- Optional: RTK GPS for landings accurate to centimetres. Standard GPS is accurate to about 1–3 m.
- Optional: a downward camera check before the final descent, to abort if the spot is now occupied (the 3D map is only a snapshot).

### Parachute (#5)
- Free-fall or loss-of-control detection from the accelerometer and attitude; can also be triggered manually.
- **Cut the motors before deploying**, so the props don't shred the lines.
- Triggered by an **independent monitor** (the spare Teensy 4.1 with its own IMU) as well as by the main flight controller, so it still works if the main firmware crashes.
- Needs height to open (roughly 10 m or more), so it won't save low-altitude crashes.
- Adds about 100–150 g.

### AI assistant (LLM on the laptop)
The LLM runs **on the laptop, not the drone**. That means no power or weight cost on the drone, and a much more capable model: either a large local model or a cloud model. It handles plain-English missions (#26). It can also read photos and 3D maps, explain change-detection results, and read flight logs to help diagnose wobbles and tuning problems.
- **If the link drops,** the LLM is unavailable, but nothing depends on it: the failsafes and landing modes all run on the drone.
- **Local or cloud model:** leaning cloud, because the laptop has no discrete GPU. Cloud needs internet in the field (e.g. a phone hotspot).
- The drone's companion computer is still needed for GPS-free navigation (#24) and the cameras, but it can be lighter now that it isn't running an LLM.

**Safety architecture (non-negotiable):**
- The LLM never touches the motors. It outputs a structured plan (waypoints and actions).
- A deterministic checker validates every plan: geofence, max 400 ft, battery reserve, speed limits.
- The pilot approves the plan before it's sent to the drone. Simple commands ("land", "come back") map onto the existing landing modes.
- The flight controller executes the plan and can override it at any time. The RC transmitter and the kill switch always win.
- If the companion computer crashes or freezes, the flight controller treats the lost heartbeat as a failsafe and holds position or returns to start.

### Simulation-first testing
Every feature gets tested in a simulator before it flies, for cost and for career reasons.
- **Software-in-the-loop (SITL):** the flight code is compiled for the PC and flown in a physics simulator.
- **Hardware-in-the-loop (HIL):** the real microcontroller runs the flight code while the simulator feeds it fake sensor data.
- **Design consequence:** the flight code must be kept separate from the hardware drivers, so the same control code runs on the PC and on the drone.
- **Simulator (decided): Gazebo Harmonic + PX4** on Ubuntu 24.04 (native on the PC, WSL2 on the laptop). It is the industry standard, which helps the career goal.

### Required safety basics
- Pre-arm checks (sensors healthy, battery OK, GPS lock when needed)
- Kill switch on the radio
- Geofence: a boundary it won't cross

### Modular design: build for the full load, fly it bare first
- The airframe (frame, motors, ESC, battery) is **sized and built for the heaviest configuration**: camera, GPS, parachute, claws, plus a grabbed object.
- The add-ons are **modules**, attached only once the drone flies well and each one is actually needed. Testing starts with the bare drone.
- **A standard module mount (#17):** one mechanical interface, plus a connector carrying power and a data bus. The firmware detects which module is fitted. Bus choice is still open (a simple serial link vs. DroneCAN, the industry standard for drone peripherals; the H743 has CAN hardware).
- **Ballast stand-ins:** before a module exists, weights bolted to its mount point let flights at full weight be tested early.
- **Simulation:** every configuration (bare → camera → GPS + parachute → full with claws) is simulated, and each must meet its targets.

## Hardware architecture (draft)

Three layers. Each layer stays safe if the one above it fails.

1. **Flight controller (microcontroller):** hard real-time work. Reads the sensors, runs the PID loops, drives the motors, runs the failsafes and the parachute, and does the self-tuning (#21). Never depends on the layers above.
2. **Companion computer (Raspberry Pi 5 or Jetson Orin Nano):** cameras, GPS-free navigation (#24), photo capture for mapping. Sends targets to the flight controller.
3. **Laptop ground station:** telemetry, map, the LLM assistant (#26), mission approval, 3D map processing, safe-spot finding, change detection (#11).

**Draft parts list:**
- **Frame:** 8–10" carbon-fibre X frame, bought, with a standard module mount. 3D-printed arms flex too much at this size.
- **Motors:** low-KV, 6S, chosen from thrust tables once the prop size is set.
- **ESC:** 4-in-1, 6S, with bidirectional DShot (per-motor RPM feedback, useful for filtering and #21). AM32 is open-source ESC firmware.
- **Battery:** 6S2P Li-ion from 21700 high-drain cells (~9 Ah, ~850–900 g).
- **Flight controller (decided): the combo.** A Nucleo-H743 dev board on the bench (debugger, every pin, hardware-in-the-loop testing) plus an off-the-shelf STM32H743 flight controller board in the drone. Same chip, so the same firmware runs on both.
- **Teensy 4.1 (already owned).** Uses, in order:
  1. **Thrust-stand controller** (the first build): reads the load cell, current and voltage, drives the ESC, logs to its SD card.
  2. **Desk sandbox:** run dRehmFlight with a cheap IMU breakout and no motors, to see a complete flight controller working before writing one.
  3. **Independent parachute monitor on the drone:** has its own IMU, watches for free fall or tumbling and for a heartbeat from the main flight controller, and fires the parachute and cuts the motors even if the main firmware hangs. The motor-cut circuit is still to be designed.
  - Alternative later role: a hardware-in-the-loop bridge (pretends to be the GPS, receiver and rangefinder for the simulator). A second Teensy (~$30) would let it do both.
  - Not suited to the wristband (#2): it has no wireless. Use an ESP32 there.
- **Companion computer:** not needed until stage 2, so decide then. A Pi 5 is likely enough now that the LLM is on the laptop; go to a Jetson if #24 needs more compute.
- **IMU:** ICM-42688-P (built into most modern flight controller boards; breakout boards exist).
- **Barometer:** usually on the flight controller board.
- **GPS + compass:** u-blox M10 module with compass, on a mast away from power wires.
- **Rangefinder:** downward lidar (TF-Luna or TFmini-S).
- **Control link:** ExpressLRS receiver plus a handheld transmitter. Its protocol (CRSF) is well documented and easy to parse.
- **Data/video link to the laptop:** to decide. Likely a separate high-bandwidth Wi-Fi-based link from the companion computer. Speaking MAVLink lets existing ground-station tools work while the custom one is built.
- **Power:** a separate 5 V / 5 A+ supply for the companion computer, and a current sensor (usually on the ESC).
- **First thing to build:** a thrust stand (load cell + HX711 + current sensor) to measure motor and prop efficiency and feed real data into the simulator.

## Shortlist (not final)

- **#2 Wrist gesture control:** fly by tilting an ESP32 + IMU wristband
- **#7 3D mapping run:** fly a GPS grid taking photos, then build a 3D model with OpenDroneMap. *The "nearest safe spot" landing mode depends on this.*
- **#8 Perching claws:** servo talons grab a branch or rail, the motors stop, and the camera keeps recording
- **#10 Wind sensing:** works out wind from how hard it leans to hold position (software only); powers a live "turn back now" battery warning and smarter landing choices
- **#11 Change detection:** compares two mapping runs and flags what changed, so safe landing spots stay up to date
- **#21 Self-tuning controller:** tunes its own PID in flight and re-tunes when the payload changes (runs on the flight controller)
- **#24 GPS-free flight:** navigates with the camera and IMU, so it gets home if GPS drops (runs on the companion computer)
- **#26 Plain-English missions:** the laptop LLM turns commands into checked, pilot-approved plans

## Ideas pool

| # | Idea | Status |
|---|---|---|
| 1 | Tilt-rotor flight (camera stays level without a gimbal) | Not picked |
| 2 | Wrist gesture control | **Shortlist** |
| 3 | Precision landing on a printed marker | Replaced by smart landing (base spec) |
| 4 | Web ground station | **Base spec** (laptop) |
| 5 | Free-fall detection + parachute | **Base spec** |
| 6 | Thermal vision overlay | Not picked |
| 7 | 3D mapping run | **Shortlist** (needed for safe-spot landing) |
| 8 | Perching claws | **Shortlist** |
| 9 | Follow the wristband | New |
| 10 | Wind sensing + "turn back now" battery warning | **Shortlist** |
| 11 | Change detection between mapping runs | **Shortlist** |
| 12 | AR overlay on live video | New |
| 13 | Laser "measure anything" | New |
| 14 | Payload winch | New |
| 15 | Amphibious (float landing gear) | New |
| 16 | Repeat-shot time-lapse | New |
| 17 | Modular payload bay | **Base spec** (standard module mount; see "Modular design") |
| 18 | VTOL quadplane (adds a wing) | Dropped: too complex; a long-range quad was chosen instead |
| 19 | Listening post: microphones locate sounds while perched with motors off | New |
| 20 | Sniffer drone: follows a gas or smoke plume to its source | New |
| 21 | Self-tuning controller: tunes its own PID in flight and re-tunes when the payload changes | **Shortlist** |
| 22 | Neural-network controller trained in the simulator, run on the real drone | New |
| 23 | Motor-failure survival: spins and lands on 3 motors before resorting to the parachute | New |
| 24 | GPS-free flight: navigates by camera, gets home if GPS drops | **Shortlist** |
| 25 | Haptic wristband: vibrates for obstacles, battery and direction home | New |
| 26 | Plain-English missions via an LLM on the laptop (pilot approves before it flies) | **Shortlist** |
| 27 | Charging dock: lands on a pad, recharges, takes off again | New |
| 28 | Sensor pucks: drops small sensor beacons and collects them later with the claws | New |
| 29 | Toroidal props: looped propellers designed to be quieter | New |

## Early notes

- **Weight:** camera + GPS + parachute + claws + rangefinder + onboard computer probably puts the all-up weight around 1–1.4 kg, plus a heavier Li-ion pack. **Decided: 8–10" props with Li-ion** for flight time.
- **Quad endurance levers (biggest first):** bigger, slower props on low-KV motors; Li-ion packs instead of LiPo; weight discipline; firmware efficiency (clean filtering, an "eco cruise" speed); landing or perching to wait with the motors off. A 7" quad with Li-ion could manage roughly 20–30 min, and an 8–10" more.
- **Legal (US):** over 250 g, so it needs FAA registration and Remote ID, plus the TRUST test. Near airports much of the airspace is controlled, so LAANC authorisation is needed there.

## Still to decide

- Final pick of extra features
- **Target specs** (the pass/fail numbers for the sim): flight time, thrust-to-weight, top speed, wind tolerance, payload, maximum weight. Also the exact prop size (8, 9 or 10").
- Which open-source flight code to start from (the microcontroller is decided: STM32H743)
- Data/video link to the laptop (the control link is decided: ExpressLRS)
- Camera type (FPV video vs. stills for mapping vs. both)
