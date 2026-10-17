# Decisions

Every call I've made on this project, and why. Started 2026-10-13. When something changes, it changes here first.

## The idea

I want a fairly big, fairly fast quadcopter with a camera and GPS, running flight firmware I wrote myself. The point is to learn by designing it, completely enough that I could build it one day. Since 2026-10-17 it's a research project: every real part modeled, connected and simulated, with nothing bought by default (see "A research project, build-ready" below).

- **Hardware:** parts I can order. Dev boards, breakout boards, ESCs, motors, a receiver. No custom PCB, because I don't want to sit around waiting on fab and shipping.
- **Firmware:** mine. Starting from open-source flight code and adapting it is fine. I'll pick up PID and control theory as I go.
- **Airframe:** a quad on 8–10" props with low-KV motors and a Li-ion pack, built to fly long (roughly 25–40 minutes cruising). I looked at a VTOL quadplane and dropped it. Way too much complexity for a first build.
- **Budget:** the research costs nothing by default. A real build would be around $1,000, and the build package prices it properly.
- **Name and home:** Extra 15pc Gum, in a public GitHub repo (`extra-15pc-gum`) under GPL-3.0. The repo is how I move between machines, and [STATUS.md](../STATUS.md) always says where I am.
- **Building in public:** I'm posting the whole process. That means:
  - respecting the licenses of any code I reuse (a lot of flight code is GPL)
  - scrubbing home and launch GPS coordinates from anything I post
  - making the CAD and sim produce stuff worth showing, for the repo and then my portfolio
- **Not monetizing any of it.** This is purely for learning, and because it's a really cool project. That keeps me under the FAA's recreational rules.
- **What I know going in:** soldering, embedded programming, and flying RC.

### A research project, build-ready (decided 2026-10-17)

Instead of buying parts and building it, I'm designing the whole drone in simulation, in depth: every real part modeled, connected to the parts around it, and tested. It's more of a research project now, but the research has to be good enough that I could build the drone from it one day.

**What done means:** someone could order the parts list, follow the assembly and wiring guides, flash my firmware, and run the bench and first-flight test plans. They'd also get an honest list of what the simulations couldn't prove, with the first thing to measure for each.

**What stays the same:** the targets, the modules, the whole safety design (it gets designed and simulated, just not built), my own firmware, the limits profiles, the posts, and the process (talk it through, spec, plan, test-first).

**What changes:**
- Nothing gets bought by default, and nothing flies. The FAA registration, Remote ID and the Part 107 question move into a checklist in the build package.
- Two new layers: electrical (every wire and pin) and structure (stress and vibration).
- The old bench-build and first-flight phases become written test procedures in the build package.
- The phases became steps: sizing and parts, CAD, electrical, flight sim, my firmware, modules, smart features, and the build package, with structure, aero and the design hunt as side tracks. The details are in [roadmap.md](roadmap.md).

**Two optional purchases:** a thrust stand (roughly $100–200), the one measurement that makes the whole simulation more believable, with parts that carry over to a build; and a Nucleo-H743 (about $30), which runs my firmware on the real chip while the sim feeds it sensor data. Both are off by default.

**The unproven list.** Simulation can't prove everything, so the build package says what's still unknown and what to measure first:

| What sim can't prove | First thing to measure when built |
|---|---|
| Real thrust and efficiency (manufacturer data runs ±15–20%) | One motor and prop on a thrust stand |
| Vibration reaching the IMU, and the filtering it needs | A gyro log with the props spinning |
| Motor and ESC heat in real air | Temperatures after a full hover |
| The vortex ring state (Gazebo doesn't model it) | Careful descent tests |
| Li-ion in the cold, and as it ages | A pack discharge test |
| Real radio range with trees and terrain | A walk-out range test |
| Compass interference from the power wires | Compass readings against throttle |
| Solder joints, connectors and tolerances | The bench checks |

### Simulate everything

The loop is:
1. pick real parts and a shape
2. run the sizing model
3. build it in CAD, with every part connected
4. design the wiring, and check the currents, voltages and heat
5. fly it in Gazebo, on PX4 and then on my firmware
6. check it against the targets
7. improve it and go again

The structure analysis and the virtual wind tunnel run alongside the loop instead of inside it: their numbers sharpen everything else whenever they arrive.

The layers:

1. Sizing model (my own Python tool)
2. CAD, written as code (build123d), by Claude
3. Electrical: wiring diagrams from code (WireViz), schematics (KiCad), circuit simulation (ngspice)
4. Structure: stress and vibration (FreeCAD with CalculiX), alongside
5. Aerodynamics: CFD, the digital version of a wind tunnel (alongside, see below)
6. Flight sim: Gazebo Harmonic + PX4, flown by proven firmware first
7. My own firmware flying the same Gazebo sim

This is partly about money and partly about my career, because simulation is a skill I want. I'll test two ways:
- **Software-in-the-loop:** the flight code is compiled for the PC and flies in the sim.
- **Hardware-in-the-loop (optional, with a $30 Nucleo-H743):** the real chip runs the code while the sim feeds it fake sensor data.

Both only work if the flight logic stays separate from the hardware drivers, so the same code runs everywhere.

The simulator is Gazebo Harmonic + PX4, which is what the industry actually uses. It runs on Ubuntu 24.04 under WSL2 on both machines (decided 2026-10-17), so I never have to reboot to switch. The PC's native Ubuntu side stays as a fallback for really big wind tunnel runs, or if Gazebo's graphics struggle under WSL.

Where everything runs:

| Where | Tools |
|---|---|
| WSL2 Ubuntu 24.04 (both machines) | The Python code (sizing model, CAD in build123d, WireViz), Gazebo + PX4, OpenFOAM, my firmware in the sim, OpenDroneMap |
| Windows on the PC | KiCad with ngspice, FreeCAD with CalculiX, Blender on the RTX 3060, ParaView, FluidX3D, the Rerun viewer |
| Windows on the laptop | The ground station, and object detection with OpenVINO |

### CAD in code, then hunt for a unique design (decided 2026-10-13)

Claude writes all the CAD as Python code with build123d, reading from the parts files. Change a part and the model rebuilds itself. It spits out:
- the center of gravity and inertia
- meshes for the sim and for CFD
- STEP files
- renders

It happens in two steps:

1. **Baseline first.** A plain, simple X quad, run through sizing, CAD and Gazebo until the pipeline works end to end. This is the one the research is built around, and the one the build package describes.
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
- **Keeping it honest:** first check OpenFOAM against shapes with known drag, then against published drone data, and against my own flight logs if I ever build it.
- **Where it runs:** the PC. The laptop only manages coarse test runs.
- **When it runs (decided 2026-10-14, still true for the research):** as a side track, never blocking the main line. At a 10 m/s cruise, drag is roughly 10% of the power, so even a 30% drag error moves flight time by about 3%. That's well inside the uncertainty in manufacturer thrust data. Drag matters more for the 80 km/h top speed, and that number gets rechecked whenever the CFD results arrive.

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

### Every test is visible (decided 2026-10-17)

Visuals matter most while the design is being worked out, not just for posts. So every simulated test, in every step, leaves something to look at, not just a pass/fail line:

| Step | What I get to see |
|---|---|
| Sizing | Every simulated flight on a timeline: voltage, charge, current and thrust headroom, with the reserve line, plus the sweep filling in as it runs |
| CAD | The assembly in 3D, with collisions and tight clearances highlighted |
| Electrical | Current, voltage drop and heat per wire and part, in every setup |
| Structure | Stress maps and the arms' vibration shapes |
| Aero | Streamlines and pressure on the body |
| Flight sim | A clip and telemetry plots for every scenario |
| My firmware | Its plots laid over PX4's on the same test |

Each step has three outputs, all reading the same data files:
- **a Markdown report** with charts, for the repo and the posts
- **Rerun recordings.** Every test streams into the Rerun viewer as it runs, on a timeline I can scrub, and stays there to replay later. Rerun is free, open source and made for robotics, and the same viewer handles plots, the 3D drone and flight replays.
- **pages on the project site** (below)

### The project site (decided 2026-10-17)

One website that pulls from every simulation, for looking at the drone and learning from it. It should feel rich and animated:
- **The drone in 3D,** straight from the CAD. It turns slowly with the props spinning, comes apart into an exploded view and back together, and switches modules V, P and C on and off, with the weight, flight times and verdicts updating as it does. Any part can be clicked for its specs, price and source.
- **A live spec sheet:** weight, flight times, thrust-to-weight and top speed for every setup, colored pass, marginal or fail, always from the latest runs.
- **A page per step:** what the step does, in plain words, linked to the matching topic in learning.md; the results as interactive charts; animated replays of the tests; and links into every individual sim, so nothing hides behind a summary.
- **The unproven list,** front and center.
- **The project's look:** black, spearmint and magenta, with the same fonts as the posts.

It's built from the data files every step writes, so it grows as the steps finish, starting with the sizing model. The individual sims stay available on their own too: the Rerun recordings, the reports in `docs/reports/`, and the clips.

**Where it lives (decided 2026-10-17):** on my machine while the research runs. It doesn't go live until the project is done, and then it joins my portfolio site, wearechintu.com, as another project. So it's built as a self-contained static site with relative links, which can drop into the portfolio wherever it ends up, with no server needed. Its code lives in this repo like everything else, but the built site isn't published anywhere until the end. What it's built with gets settled in its own spec.


### Learning (decided 2026-10-13)

I'm new to a lot of this, CFD especially. Tutorials and studying happen on my own time, offline, and building happens online. They don't get mixed. Everything I should learn, with resources, lives in [learning.md](learning.md), and it grows as new topics come up.

### My machines

- **Laptop:** Lenovo, Core Ultra 7 155U, 16 GB, Intel integrated graphics, WSL2 Ubuntu 24.04 (capped at about 7.6 GB of RAM). Gazebo runs, but scenes have to stay simple. No NVIDIA GPU, so no Isaac Sim and no decent local LLM.
- **PC:** dual boot, Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060. The Linux tools run in WSL2 Ubuntu 24.04 on its Windows side (decided 2026-10-17), and the native Ubuntu side is a fallback. **It's the main machine from 2026-10-14**, set up with [setup-pc.md](setup-pc.md). The laptop is for docs, light work and the ground station.
- Every machine runs the same checks (`scripts/check-machine.sh` and `scripts/setup-dev.sh`), and the results are logged in [machines/](machines/).

### Firmware stages

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
- looks at photos and 3D maps, and works with the object detector (#39)
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

The Teensy 4.1 used to live in module P, which would have come late. That meant the first flights of brand-new firmware would have a kill switch running inside that same firmware. So it moved into Base. In the research it's designed, wired and simulated like everything else.

- It has its own IMU, and it listens to the same receiver as the flight controller (the receiver's output wire splits to both). The kill switch reaches the motors through two separate boards running separate code. A second receiver would add more independence, but the thing I'm protecting against is my firmware, not the receiver.
- It cuts the motors by blocking the four ESC signal lines with an analog switch, not by switching the main power. A switch in a ~100 A power line is a new way to drop a healthy drone, and ESCs stop the motors when their signal disappears (simulated in step 3, and on the bench checklist if it gets built). It has to pass signals both ways, because bidirectional DShot sends RPM back on the same wire.
- It fails in the useful direction. If the Teensy loses power, the switch passes signals and the drone keeps flying on the flight controller. The flight controller watches the Teensy's heartbeat, warns me if it goes quiet, and won't arm without it.
- The automatic triggers (free fall, tumbling, the flight controller going quiet) start in shadow mode: they log what they would have done, and do nothing. In the sim they go live in step 6, once the false-trigger replay shows zero false triggers; on a real drone, only after enough real flights with none. A fast descent at low throttle looks a lot like free fall to an accelerometer, so this matters. The 4.1's SD card handles the logging.
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
| **C: Claws** | Claws + servos | Only if we come up with a unique claw on an actual arm. That conversation waits until the modules step; for now the drone just needs to work. Works without V, but you'll want the camera to see what you're grabbing |

- **The parachute rule:** the firmware checks whether P is fitted, and won't fly autonomous missions or go above about 30 m without it. The chute needs about 10 m to open anyway, so there's no point carrying it for low hover tests.
- **A standard module mount (#17):** one mechanical interface, and one connector carrying power and a data bus.
  - The firmware sees which modules are on and loads a tuning profile to match. The self-tuning controller (#21) then fine-tunes in flight.
  - The bus is still open: plain serial, or DroneCAN (the industry standard for drone add-ons; the H743 has CAN hardware).
- **Ballast:** until a module exists, the sim (and one day the real drone) carries weights on its mount, so it can still be tested at full weight.

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
- **Hover times got added.** Base has no GPS, so on a real build its cruise time can't be measured until V is fitted, but hover time can be measured on the first flights. The sim checks both. A quad uses a bit less power at a gentle cruise than in a hover, because moving forward keeps feeding the props fresh air, so the hover targets sit about 15% under the cruise ones. The sizing model checks that ratio.
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

The steps live in [roadmap.md](roadmap.md), and the live plan with each step's outcome is in the [README](../README.md#the-plan). It's the plan I'm following, and it will change. The full revision on 2026-10-14, with every change tagged R1 to R7 and the reason for each, is in [specs/2026-10-14-plan-revision.md](specs/2026-10-14-plan-revision.md).

## Hardware (draft)

Three layers, plus a safety monitor underneath them all. Each one has to stay safe if the one above it dies:

1. **Flight controller:** the hard real-time stuff. It reads the sensors, runs the PID loops, drives the motors, and handles the failsafes, the parachute and self-tuning (#21). It doesn't depend on anything above it.
2. **Companion computer** (Pi 5 or Jetson Orin Nano): cameras, GPS-free navigation (#24), and photos for mapping. It sends targets down to the flight controller.
3. **Laptop:** telemetry, the map, the LLM (#26), mission approval, 3D map processing, safe spots, and change detection (#11).
4. **Safety monitor:** the Teensy in Base, independent of all three (see above).

Parts so far:

- **Frame:** for the baseline, a real, orderable 8–10" carbon X frame with the module mount. Printed arms would flex too much at this size. If the design hunt finds something unique, the frame goes custom (see above).
- **Motors:** low-KV, 6S, picked from thrust data once the prop size is settled.
- **ESC:** 4-in-1, 6S, with bidirectional DShot, so I get RPM from every motor. That's great for filtering and for #21. AM32 is open-source ESC firmware, which is a nice bonus.
- **Battery:** 6S2P Li-ion from 21700 high-drain cells, around 9 Ah and 850–900 g. The sizing model also tries 6S3P, in case the extra cells earn their weight.
- **Flight controller (decided):** an off-the-shelf STM32H743 flight controller board in the drone, and optionally a Nucleo-H743 on the desk, which gives me a proper debugger, every pin broken out, and hardware-in-the-loop testing. Same chip, same firmware. The board has to be one PX4 supports, with SWD pads I can get a debugger onto.
- **Teensy 4.1:** I already have one lying around. A build would need a second (about $30) so each can keep its own job:
  1. Run the thrust stand (optional, in step 1): read the load cell, current and voltage, drive the ESC, and log to its SD card.
  2. Desk sandbox: dRehmFlight with a cheap IMU and no motors, so I can watch a complete flight controller work before I write mine.
  3. Be the safety monitor in Base (the second Teensy): its own IMU, listening to the receiver, cutting the motors on the ESC signal lines, and firing the chute when P is fitted.

  It could also be a hardware-in-the-loop bridge, pretending to be the GPS, receiver and rangefinder for the sim. It's no good for the wristband, though: no wireless. That's an ESP32 job.
- **Companion computer:** part of module V. A Pi 5 is probably enough now that the LLM and object detection (#39) are on the laptop. The only vision job that has to stay on board is GPS-free flight (#24), because it has to work when the link drops; a Jetson only if #24 needs more. Settled in step 6.
- **IMU:** ICM-42688-P (it's on most modern flight controller boards anyway).
- **Barometer:** on the flight controller board.
- **GPS + compass:** a u-blox M10 module with compass, up on a mast away from the power wires.
- **Rangefinder:** downward lidar (TF-Luna or TFmini-S).
- **Control link:** an ExpressLRS receiver and a handheld transmitter, on 2.4 GHz. HaLow and Meshtastic (below) both use 902–928 MHz in the US, and so does 900 MHz ExpressLRS, so the control link stays off that band. Its protocol (CRSF) is well documented and easy to parse.
- **Data/video link to the laptop:** the lead option (2026-10-14) is Wi-Fi HaLow (802.11ah), which is Wi-Fi on 900 MHz. It has a lot more range than normal Wi-Fi, with a few Mbps up close dropping to hundreds of kbps far out. It carries normal IP traffic, so MAVLink telemetry and real compressed video can share one link from the companion computer, and existing ground station software works while I build my own. The same video could go into ATAK too (the free civilian version runs on Android). One catch: the Pi 5 has no hardware H.264 encoder, so video encoding runs on its CPU, which counts when picking Pi vs Jetson. Confirmed in step 6.
- **Remote ID:** a broadcast module on a mount and 5 V plug in Base. Whether it's fitted is up to me (see the limits profiles).
- **Power:** a dedicated 5 V / 5 A+ supply for the companion computer, and a current sensor (usually on the ESC).
- **Thrust stand (optional):** a load cell, an HX711 amplifier and a current sensor, to measure how efficient the motors and props really are, and feed that back into the sim. If I do it, it happens in step 1, as soon as the sizing model has a shortlist, running off a real 6S pack so the voltage sag gets measured too. It's the single measurement that makes the whole simulation more believable.

## Shortlist (not final)

- **#2 Wrist gesture control:** fly by tilting an ESP32 + IMU wristband.
- **#7 3D mapping runs:** fly a GPS grid taking photos, and turn them into a 3D model with OpenDroneMap. The nearest-safe-spot landing depends on this.
- **#8 Perching:** hanging from or sitting on a surface that isn't a prepared landing spot (a branch, a railing, a ledge, a roof), motors off, camera still rolling. It's the biggest power saver there is, since the motors are off. Hanging needs a grabber, which is module C, and the claws only happen if we come up with a unique claw on an actual arm (talked through in the modules step). Sitting on a flat ledge or roof just needs a good landing.
- **#10 Wind sensing:** work out the wind from how hard it leans to hold position. Software only. It feeds a "turn back now" battery warning and smarter landing choices.
- **#11 Change detection:** compare two mapping runs and flag what moved, so the safe spots stay safe.
- **#21 Self-tuning:** tunes its own PID in flight, and re-tunes when the payload changes. Runs on the flight controller.
- **#24 GPS-free flight:** navigates with the camera and IMU, so it can still get home if GPS drops. Runs on the companion computer.
- **#26 Plain-English missions:** the laptop LLM turns what I say into checked plans that I approve.
- **#30 Meshtastic relay:** a small LoRa mesh node riding on the drone. Radios like this need line of sight, so trees and hills break up a ground mesh; a node in the air works like a temporary cell tower and stitches it back together. It doesn't talk to the flight controller at all, just 5 V and an antenna, and with a GPS of its own and a small battery it doubles as a lost-drone finder. LoRa is far too slow for video (a few kbps at most), so video goes over HaLow.
- **#31 Soar mode:** when the drone is waiting (watching something, or between mapping legs), it uses the air instead of fighting it, like a kestrel hanging still over a hillside. Three parts that work together:
  - **Rising air.** Wind hitting a slope or a building deflects upward, and sunny ground makes thermals. Parking in it cuts the power to hold altitude by very roughly 10–15% per 1 m/s of updraft. Typical slope lift and thermals are 1–3 m/s.
  - **Holding position in a breeze.** Hovering still in a 5–10 m/s breeze costs less than hovering in calm air, for the same reason cruising beats hovering (the props keep getting fresh air). So when it waits, it prefers breezy open air over sheltered calm spots.
  - **Riding the wind on routes.** Upwind legs low, where the wind is weaker, and downwind legs higher.

  It finds lift by comparing the throttle it needs to hold altitude against what its weight predicts, which is the same estimate wind sensing (#10) uses, and the laptop keeps a map of where lift turned up before. One safety limit: it won't sit in rising air faster than about 2 m/s. Holding still in rising air is the same as sinking into your own prop wash, and around 6 m/s for this drone that's the vortex ring state, where quads shake and lose control. It also stays under the loaded profile's altitude ceiling, so a thermal can't carry it past it. Software only.
- **#34 Spiral descent:** comes down from height in a helix on low throttle instead of straight down, then straightens up for the last few meters on the rangefinder. Coming straight down fast is what puts quads into the vortex ring state; moving forward on the way down keeps fresh air going through the props, so the descent is faster and smoother on less power. It's software only, so it can be added after Base is flying without changing anything on the drone:
  - **A rough version** flies a circle from a steady tilt and turn rate. The wind pushes the whole circle sideways, but it works any time after altitude hold does.
  - **The proper version** keeps the spiral centered on the landing spot with GPS, so it comes in step 7, once module V works in the sim.

  The only thing it needs from the start is that the firmware's landing sequence has a swappable descent part, so the spiral drops in later without rework. One honest catch: as far as I know, Gazebo's standard rotor model doesn't simulate the vortex ring state, so the sim can check the path but only real flights will show the benefit.

- **#39 Object detection on the laptop:** boxes and labels on the live video, like a street-camera demo, with all the understanding done on the laptop so the drone carries no AI hardware and spends no power on it. Two parts that work together:
  - **A detector** (a small, fast model like the YOLO family) runs on every frame: it finds, labels and tracks objects, and it works offline in an empty field. The laptop has no NVIDIA GPU, but its integrated graphics and built-in NPU can run one through Intel's OpenVINO, which gets benchmarked first.
  - **The LLM** answers questions about what the detector found, when asked: "is anyone near the landing spot?", "find my red backpack". Some detectors take any object name as text, so the LLM can turn a request into a search and the detector does the looking. The LLM needs internet if it's a cloud model.

  The details that shape it:
  - **The link sets the picture quality.** HaLow gives a few Mbps up close and hundreds of kbps far out, and small, far-away objects get lost in compression. So the drone sends low-bitrate live video for watching, plus full-resolution still frames on request when the laptop wants a closer look.
  - **It's for looking, not steering.** Detections arrive a few hundred milliseconds late and stop when the link drops. Anything that ever steers the drone from detections needs its own safety design, like the LLM's checker.
  - **Drones see the world from above,** and standard detectors are trained on street-level photos. Aerial datasets like VisDrone fix that; retraining happens on the PC's RTX 3060, and the laptop just runs the result.
  - **Licenses:** the popular Ultralytics YOLO is AGPL-3.0, which works with this GPL-3.0 repo, and there are Apache-licensed alternatives. Picked in the spec.
  - **Privacy:** following the limits-profile idea, rules about filming people are settings, not caps. Anything exported for posts gets faces and license plates blurred.

  In the research it runs on the simulated camera and on recorded video (step 7), and the pipeline can be built and benchmarked on the laptop any time.

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
| 8 | Perching (hanging needs claws, module C, and only with a unique claw on an actual arm) | Shortlist |
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
| 31 | Soar mode: park in rising air, hold position in a breeze, ride the wind on routes | Shortlist |
| 32 | Solar panel on top, trickle charging while perched (about 10 W in full sun, roughly 5% of the pack per hour). In flight it about cancels its own weight. | Maybe |
| 33 | Flying-squirrel membrane: unfolds between the arms with the motors off and glides, possibly spiraling down to land, with the props spun up at the last moment | Maybe. Not picked for landing (see the notes); the spiral descent (#34) does that job. It could come back as a gliding demo if v2 has much more glide area. |
| 34 | Spiral descent: comes down in a helix on low throttle instead of straight down, then straightens up for the last few meters | Shortlist (step 7, software only) |
| 35 | Recharging from the props on the way down | Dropped: under 0.5% of the pack from 120 m, and fast descents are the most unstable part of quad flight |
| 36 | Lifting body: shape the body to make lift in forward flight | Left to the design hunt, which already varies body shape and motor tilt. Rough numbers say it's about a wash. |
| 37 | Albatross-style soaring, using the wind gradient | Dropped: needs real wings |
| 38 | Helium assist | Dropped: about 1 m³ of helium per kg of lift, far too much drag for 80 km/h |
| 39 | Object detection on the laptop: boxes and labels on the live video, with the LLM answering questions about them | Shortlist (step 7) |

## Notes

- **Weight:** see the mass budget above. The modules plus the heavier Li-ion pack are why it's 8–10" props.
- **Making a quad fly longer**, biggest lever first:
  1. bigger, slower props on low-KV motors
  2. Li-ion instead of LiPo
  3. cutting weight ruthlessly
  4. efficient firmware: clean filtering, an eco cruise speed
  5. landing or perching to wait with the motors off
  6. soar mode (#31): using rising air and breezes while it waits

  A 7" on Li-ion might manage 20–30 minutes, and 8–10" more than that.
- **Saving power without wings (2026-10-14):** nothing stays up for free unless the air is giving it energy. A wingless quad drops at roughly parachute speed the moment its motors stop. So the passive options are taking energy from the air (soar mode, #31), stopping but staying up high (perching, #8), or trading height for time (gliding), which barely helps. The props already are the wings: a rotor is a spinning wing, and big slow props are an efficient one.
- **The flying-squirrel landing (#33), not picked for now:** glide down in a spiral with the props off, then spin them up at the last moment. The reasons:
  - the frame only fits about 0.1 m² of membrane, so it would glide at about 18 m/s while sinking about 7 m/s, and a banked spiral at that speed is around 90 m across, not a tight funnel
  - the membrane has to fold away before the motors restart (it sits under the props), and then it has to go from a fast glide to a hover in a second or two, close to the ground
  - in the emergencies where a parachute matters (dead motors, dead power, crashed firmware), the restart at the bottom is exactly what can't happen
  - a normal powered descent from 120 m only costs about 1% of the pack, and the membrane and its fold mechanism would cost more than that on every flight

  The spiral descent (#34) gets the same look with the props on low, and it's on the shortlist instead.
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
- How many clean shadow-mode flights a real build would need before the safety monitor's automatic triggers go live
- Whether to get Part 107 (in the build package's legal checklist)
- Whether Max (with C) should still size the motors while the claws are uncertain, or Mission plus a margin (bring up in the sizing model discussion)
- Data/video link to the laptop: HaLow is the lead option, confirmed in step 6 (the control link is decided: 2.4 GHz ExpressLRS)
- Where the Meshtastic relay (#30) lives: in V, in Base, or as its own little module
- Exactly what goes in the `us-recreational` limits profile, checked against the current FAA and FCC rules for the build package
- Camera: FPV video, stills for mapping, or both
- Module bus: serial or DroneCAN
- What "unique" is allowed to mean for the design hunt (decided after the baseline works)
- Which OpenFOAM: the Foundation release (openfoam.org) or ESI's (openfoam.com). Both have the tutorials I need. Decided when writing the setup script.
