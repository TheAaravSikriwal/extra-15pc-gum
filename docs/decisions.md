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
  - making the CAD and sim produce stuff worth showing
  - checking the FAA's Part 107 rules if I ever monetize it
- **What I know going in:** soldering, embedded programming, and flying RC.

### Simulate first, then buy

Nothing gets bought until it has flown in simulation. The loop is: pick parts, run the sizing model, put them in CAD, fly them in Gazebo, check against the targets, swap parts, repeat. It only gets priced once it passes.

All four layers are happening:

1. Sizing model (my own Python tool)
2. CAD mock-up (Onshape, public documents)
3. Physics sim: Gazebo Harmonic + PX4, flown by proven firmware first
4. My own firmware flying the same Gazebo sim

This is partly about money and partly about my career, because simulation is a skill I want. I'll test two ways:
- **Software-in-the-loop:** the flight code is compiled for the PC and flies in the sim.
- **Hardware-in-the-loop:** the real chip runs the code while the sim feeds it fake sensor data.

Both only work if the flight logic stays separate from the hardware drivers, so the same code runs everywhere.

The simulator is Gazebo Harmonic + PX4 on Ubuntu 24.04: native on the PC, WSL2 on the laptop. It's what the industry actually uses.

### My machines

- **Laptop:** Lenovo, Core Ultra 7 155U, 16 GB, Intel integrated graphics, WSL2 Ubuntu 24.04 (capped at about 7.6 GB of RAM). Gazebo runs, but scenes have to stay simple. No NVIDIA GPU, so no Isaac Sim and no decent local LLM.
- **PC:** dual boot, i7, 32 GB DDR5, RTX 3060. The sim lives on its Ubuntu 24.04 side.

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
- A separate monitor can fire it as well as the main flight controller. That's my spare Teensy 4.1 with its own IMU, so if my firmware crashes, the parachute still works.
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
- A plain, deterministic checker validates every plan: geofence, 400 ft ceiling, battery reserve, speed limits.
- I approve the plan before it goes to the drone. Simple stuff like "land" or "come back" maps straight onto the landing modes.
- The flight controller flies the plan and can override it at any time. My transmitter and kill switch always win.
- If the companion computer crashes or freezes, the flight controller notices the missing heartbeat and holds position or comes home.

### Safety basics

- Pre-arm checks: sensors healthy, battery OK, GPS lock when it's needed
- A kill switch on the radio
- A geofence

### Modular design (locked 2026-10-13)

The frame, motors, ESC and battery are sized for the heaviest setup, but the drone flies bare first. Modules go on and off depending on what I'm doing that day.

Base is always on: frame, motors, ESC, battery, flight controller, receiver, rangefinder. It flies by itself.

| Module | What's in it | Notes |
|---|---|---|
| **V: Vision & nav** | GPS + compass, camera(s), companion computer, video link | GPS and camera go together, because mapping, safe-spot landing and GPS-free flight all need both |
| **P: Parachute** | The chute + the independent Teensy 4.1 monitor | See the parachute rule below |
| **C: Claws** | Claws + servos | Works without V, but you'll want the camera to see what you're grabbing |

- **The parachute rule:** the firmware checks whether P is fitted, and won't fly autonomous missions or go above about 30 m without it. The chute needs about 10 m to open anyway, so there's no point carrying it for low hover tests.
- **A standard module mount (#17):** one mechanical interface, and one connector carrying power and a data bus.
  - The firmware sees which modules are on and loads a tuning profile to match. The self-tuning controller (#21) then fine-tunes in flight.
  - The bus is still open: plain serial, or DroneCAN (the industry standard for drone add-ons; the H743 has CAN hardware).
- **Ballast:** until a module exists, I bolt weights to its mount so I can still test at full weight.

### Target specs (locked 2026-10-13)

The sim checks all eight module combinations. Base and Max are the extremes, and anything in between has to land between them.

| Setup | Modules | Flight time | Other targets |
|---|---|---|---|
| **Base** | none | ≥ 30 min | Thrust-to-weight ≥ 4:1 |
| **Mission** | V + P | ≥ 25 min | Top speed ≥ 80 km/h; holds position in 10 m/s wind |
| **Max** | V + P + C, carrying 250 g | ≥ 20 min | Thrust-to-weight ≥ 3:1; total weight ≤ 2.5 kg |

Every setup has to land with at least 20% battery left, and flight times mean cruising, not hovering. If the sim says these numbers are unrealistic, I'll change them and explain why here. The machine-readable version is [design/targets.yaml](../design/targets.yaml).

### Roadmap

The phases live in [roadmap.md](roadmap.md). It's the plan I'm following, and it will change.

## Hardware (draft)

Three layers, and each one has to stay safe if the one above it dies:

1. **Flight controller:** the hard real-time stuff. It reads the sensors, runs the PID loops, drives the motors, and handles the failsafes, the parachute and self-tuning (#21). It doesn't depend on anything above it.
2. **Companion computer** (Pi 5 or Jetson Orin Nano): cameras, GPS-free navigation (#24), and photos for mapping. It sends targets down to the flight controller.
3. **Laptop:** telemetry, the map, the LLM (#26), mission approval, 3D map processing, safe spots, and change detection (#11).

Parts so far:

- **Frame:** an 8–10" carbon X frame, bought, with the module mount. Printed arms would flex too much at this size.
- **Motors:** low-KV, 6S, picked from thrust data once the prop size is settled.
- **ESC:** 4-in-1, 6S, with bidirectional DShot, so I get RPM from every motor. That's great for filtering and for #21. AM32 is open-source ESC firmware, which is a nice bonus.
- **Battery:** 6S2P Li-ion from 21700 high-drain cells, around 9 Ah and 850–900 g.
- **Flight controller (decided):** a Nucleo-H743 on the bench, which gives me a proper debugger, every pin broken out, and hardware-in-the-loop testing. An off-the-shelf STM32H743 flight controller board goes in the drone. Same chip, same firmware.
- **Teensy 4.1:** I already have one lying around. Its jobs, in order:
  1. Run the thrust stand: read the load cell, current and voltage, drive the ESC, and log to its SD card.
  2. Desk sandbox: dRehmFlight with a cheap IMU and no motors, so I can watch a complete flight controller work before I write mine.
  3. Be the independent parachute monitor on the drone. It has its own IMU and watches for free fall, tumbling, or the main flight controller going quiet. Then it cuts the motors and fires the chute. The motor-cut circuit still needs designing.

  It could also be a hardware-in-the-loop bridge, pretending to be the GPS, receiver and rangefinder for the sim. A second Teensy is about $30 if I want both. It's no good for the wristband, though: no wireless. That's an ESP32 job.
- **Companion computer:** not needed until stage 2. A Pi 5 is probably enough now that the LLM is on the laptop; a Jetson if #24 needs more.
- **IMU:** ICM-42688-P (it's on most modern flight controller boards anyway).
- **Barometer:** on the flight controller board.
- **GPS + compass:** a u-blox M10 module with compass, up on a mast away from the power wires.
- **Rangefinder:** downward lidar (TF-Luna or TFmini-S).
- **Control link:** an ExpressLRS receiver and a handheld transmitter. Its protocol (CRSF) is well documented and easy to parse.
- **Data/video link to the laptop:** still open. Probably a separate Wi-Fi-based link from the companion computer. If it speaks MAVLink, existing ground station software works while I build my own.
- **Power:** a dedicated 5 V / 5 A+ supply for the companion computer, and a current sensor (usually on the ESC).
- **First thing I'll build:** a thrust stand (load cell, HX711 amplifier, current sensor) to measure how efficient the motors and props really are, and feed that back into the sim.

## Shortlist (not final)

- **#2 Wrist gesture control:** fly by tilting an ESP32 + IMU wristband.
- **#7 3D mapping runs:** fly a GPS grid taking photos, and turn them into a 3D model with OpenDroneMap. The nearest-safe-spot landing depends on this.
- **#8 Perching claws:** grab a branch or a railing, motors off, camera still rolling. This is module C.
- **#10 Wind sensing:** work out the wind from how hard it leans to hold position. Software only. It feeds a "turn back now" battery warning and smarter landing choices.
- **#11 Change detection:** compare two mapping runs and flag what moved, so the safe spots stay safe.
- **#21 Self-tuning:** tunes its own PID in flight, and re-tunes when the payload changes. Runs on the flight controller.
- **#24 GPS-free flight:** navigates with the camera and IMU, so it can still get home if GPS drops. Runs on the companion computer.
- **#26 Plain-English missions:** the laptop LLM turns what I say into checked plans that I approve.

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

## Notes

- **Weight:** camera, GPS, parachute, claws, rangefinder and companion computer probably add up to 1–1.4 kg before the heavier Li-ion pack goes on. That's why it's 8–10" props.
- **Making a quad fly longer**, biggest lever first:
  1. bigger, slower props on low-KV motors
  2. Li-ion instead of LiPo
  3. cutting weight ruthlessly
  4. efficient firmware: clean filtering, an eco cruise speed
  5. landing or perching to wait with the motors off

  A 7" on Li-ion might manage 20–30 minutes, and 8–10" more than that.
- **Legal (US):**
  - Over 250 g means FAA registration, Remote ID and the TRUST test.
  - Near airports a lot of the airspace is controlled, so I'll need LAANC authorization there.

## Still open

- Final pick of the extras
- Exact prop size: 8, 9 or 10". The sizing model decides.
- Which open-source flight code to start from (the chip is decided: STM32H743)
- Which H743 board. It needs PX4 support for the baseline flight.
- Data/video link to the laptop (the control link is decided: ExpressLRS)
- Camera: FPV video, stills for mapping, or both
- Module bus: serial or DroneCAN
