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
| Forward-flight power, especially the drag the props add at speed (see the honesty check below) | A GPS-logged cruise at a steady speed, with current logged |
| The chute's opening height: Fruity Chutes' chart puts the Harrier's canopy at 52.5 ft (16 m) at least, against the 10 m the sim saved it from on a guessed 1 s opening | Fruity Chutes' own numbers, then a drop test with a dummy weight |

### The first honesty check (2026-10-17)

`pcs14 validate` runs the model against published data. The first results:

- **The battery model holds up.** Against four cells' published 10 A discharge curves (Molicel P42A and P45B, Samsung 40T and 50S), it lands within 0.02 to 0.06 V per cell RMS. Real cells sag a touch more than it says, never less.
- **Cruise is where it misses.** On Oscar Liang's independent test of the GEPRC MOZ7 V2, the model says 31.9 minutes and he measured 16. The hover side agrees with his throttle numbers (about 30% to hover lines up with the table), but to match the cruise, the drone's drag area would have to be about 540 cm2 instead of the 100 cm2 I estimated from its frontal area.
- **Why, probably:** in forward flight the props themselves add drag that grows with speed, which a frontal-area estimate leaves out. The test also had 15-20 mph wind, normal FPV flying instead of a steady cruise, and no published landing voltage. It can't just be a bigger frontal drag area, because that drone reaches 110 km/h, which a 540 cm2 drag area wouldn't allow.
- **What it means:** the cruise numbers in the sizing report are probably optimistic, possibly by up to 2x, and the hover numbers are the ones to trust for now. Fixing it means modeling rotor drag properly and the wind tunnel side track. A thrust stand, and one real GPS-logged flight, would settle it.

### The first real sweep (2026-10-17)

The catalog has real motors and props now. Three researchers went through more than 50 motors with published 6S tables, from Emax, Hobbywing, T-Motor, Flash Hobby, BrotherHobby, iFlight, GEPRC, AxisFlying and RCINPOWER. Six made it in, picked for clean, smooth tables at 6S with an rpm column, on 8 to 10 inch tri-blades whose weight the prop maker publishes:

| Motor | Mass | Props it's tested on |
|---|---|---|
| Emax E3 2814 850KV | 82 g | HQ 9x5x3, Gemfan 1050 |
| Emax E3 3115 900KV | 108 g | HQ 9x5x3, HQ 10x5x3, Gemfan 1050 |
| Hobbywing XRotor 3110 900KV | 89 g | HQ 8x4.5x3, 9x4x3, 9x5x3 |
| Hobbywing XRotor 3115 900KV | 125 g | HQ 9x4x3, 9x5x3, 10x4.5x3, 10x5x3 |
| Flash Hobby Mars M2814 730KV | 87 g | HQ LR10x5x3, Gemfan 1050 |
| T-Motor Velox V3115 900KV | 113.1 g | HQ 9x5x3, HQ 10x5x3 |

I checked the Emax, T-Motor and Flash Hobby tables against the makers' pages by eye. T-Motor's own page has a typo (408.08 A at 60% throttle, next to 582 W at 24 V), so that one row is left out. Many BrotherHobby and iFlight tables are lumpy (currents that jump or go backwards between rows), so they wait, and so does every table whose prop has no published weight.

What the sweep found, trying 192 builds:

- **One rule shapes the whole result: full throttle has to fit the pack's continuous rating.** All 96 of the 6S2P builds fail it: flat out, they pull 105 A or more even after the pack sags, and the best 6S2P pack is rated for 90 A. For 32 of them it's the only check they miss. With 6S3P (135 A), 14 builds pass every required target and 2 more are marginal.
- **Under today's rules, the pick is Flash Hobby Mars M2814 730KV motors, HQ LR10x5x3 props and a 6S3P Molicel P42A pack** on the Nazgul XL10 frame. With Mission's loadout and the 200 g margin: 2678 g, 32.9 min hover (28.1 pessimistic), T/W 2.35 at the reserve, 118 A flat out. It wins because it's the lowest-current motor in the catalog, which is exactly what that rule rewards.
- **The extra cells cost 400 g, and that's what sinks Max.** Max weighs 2878 g against its 2500 g limit. With the current rule switched off, 111 builds pass, and the light 6S2P ones keep Max close to 2500 g.
- **The pick's hover sits below its table.** Flash Hobby's table starts at 50% throttle (1047 g), and Mission hovers at 670 g per motor, so the model scales the power down from that first row. Checked on an Emax table that goes lower, that reads 3 to 10% low on power. The pessimistic numbers cover it, and the report says so.
- **The growth margin stays 200 g for now.** The final pick waits on the question below.

Open question (settled the same day, below): should full throttle have to fit the pack's continuous rating, or should my firmware cap the current at the rating instead?

### My firmware caps the battery current (decided 2026-10-17)

The flight controller caps the total battery current at the pack's continuous rating (100% for now, set in `design/build.yaml` under `firmware`). The target stays the same, full throttle inside the pack's rating, and the cap is how the build meets it.

- **In the model:** when flat out would pull more than the cap, the flight controller throttles back until the pack gives exactly the cap. The pack then sits at its resting voltage minus the cap times its resistance, and thrust follows power to the 2/3, the same law as uncapped full throttle, so the two meet without a jump. Thrust-to-weight, top speed, wind headroom and the flight stepper all see the capped thrust.
- **In the ranking:** the current check still shows in the report, but it doesn't count toward the sweep's ranking when the cap holds it, since it says nothing about the parts.
- **What it changed:** 76 of the 192 builds pass now (15 of them 6S2P), against 14 before. The Samsung 50S makes up most of the fails: its 25 A rating gets capped so hard that thrust-to-weight at the reserve comes up short.
- **For the firmware step:** a battery current limiter joins the flight controller's to-do list. It throttles all four motors together, and it never touches the kill switch or the safety monitor's motor cut.

### What the CAD changed (2026-10-18)

Building the drone in CAD and checking every module combination changed a few things:

- **The 5 V supply for the Pi (the Matek BEC) moved into the frame's bay, and into Base.** Up in the V housing it sat 28 mm under the compass, where Matek asks for 100. In the bay it's 106 mm away, and the module connector carries its 5 V up to the modules, which is what the module mount was always meant to carry.
- **The camera sits in front of the frame on a printed bracket.** Camera Module 3 is 25 mm tall and the XL10's camera bay is 19 mm.
- **The pack's home moved back to 10 mm ahead of the motors' center, sliding 30 mm either way, and the claws hang further back.** That's what it takes to balance every combination within 5% (they all land within 0.2%).
- **Parts moved back from the front props:** the Remote ID module and the camera bracket's tab, to keep 10 mm from the prop disks.
- **The battery tray's strap slots sit just outside the pack,** so the straps wrap around it (the first design had them landing on the pack's edge).
- **The printed parts' weights now come from the CAD,** marked as such in the catalog, and the legs, battery tray and four brackets joined it. Mission went from 2268 g to 2293 g, and its pessimistic hover from 21.9 to 21.6 min against 21. Max is 2493 g against its 2500 g limit.

### The electrical talk (decided 2026-10-18)

Eight questions, all in the [electrical spec](specs/2026-10-18-electrical.md) under "Settled in the electrical talk":

- **One connection list in code** (`design/electrical.yaml`) generates the harness diagrams, pin maps, checks, a KiCad schematic and the 3D wires colored by current.
- **The ARK FPV replaces the Kakute H7:** five full serial ports, CAN and a debug plug.
- **The module bus:** DroneCAN for the modules' parts plus one serial line for the Pi, through an XT30 for 5 V and a JST-GH for signals.
- **The main power path:** the frame's XT60, no main fuse, small fuses on the branches, a fuse link on each cell.
- **The 5 V rail:** one BEC for the Pi and the modules, with checks keeping the Pi's voltage up when servos stall. The Pi's 5 A ask is mostly for USB.
- **The motor cut:** the safety monitor takes over the ESC lines and sends stop frames, because AM32 holds the last throttle for half a second when the signal just disappears. The Teensy fires the chute over its own wires, never through the bus.
- **The check numbers:** 80% of continuous ratings, a 10 s burst at the 90 A cap for heat, 20 °C under every temperature rating at 40 °C air, 2% drop on the main path.
- **Watching it:** Rerun with the wires colored by current and the switch's scope traces, plus stills.

And one from the plan: **the GPS is the ARK GPS on DroneCAN** (16 g, 8 g over the old M10Q). With the servo nodes, Max comes to about 2514 g, over its 2.5 kg limit; the 8 g serial alternative wouldn't have saved it. Max only has to be reported.

### What the flight sim build decided (2026-10-19)

- **The motor model is fitted where the drone flies,** from just under its hover to just over its top speed, because Emax's table isn't exactly speed-squared and a whole-table fit was 6% off at hover.
- **Each motor's top speed matches the sizing model's full-throttle thrust,** not its rpm, because thrust is what the capability checks depend on and the sizing model's capped rpm comes from a power law about 4% off its own table.
- **The sim flies the drone as built:** the CAD's weight, without the 200 g growth margin. Mission is 2213 g there, against 2414 g in the sizing model.
- **The wind reaches the model through our drag plugin,** from the world's starting wind plus a topic of its own, so a scenario can change it mid-flight.
- **The world's origin is PX4's default** (Zurich), never anywhere of mine.

### What the flight sim runner decided (2026-10-19)

- **The setup fetches only the simulator's submodules, at their pinned commits, shallow.** PX4's full recursive clone also pulls NuttX, Gazebo Classic, jMAVSim and more, gigabytes the simulator never uses, and GitHub was serving them at about 60 kB/s. PX4's build fetches anything else it needs on its own.
- **MAVSDK-Python stays pinned at 3.17.4,** though it now warns that the `mavsdk` name is passing to a new native binding. The API I use carries on as `mavsdk-grpc`; moving is its own small decision later.
- **PX4 gets its parameters as PX4_PARAM_* environment variables,** which its startup sets over the x500 airframe's defaults, in a fresh working folder per run, logging from boot until shutdown. Nothing in PX4 changes.
- **Every grade uses Gazebo's ground truth,** which PX4's Gazebo bridge logs next to PX4's own estimates, so a grade says what the drone did, not what PX4 thought it did.
- **Lost link is a relay that cuts the uplink:** it drops everything MAVSDK sends and passes everything PX4 sends. PX4 v1.17 lists a MAVLink-signal failure but doesn't implement it, and a cut uplink is what a dropped radio looks like to PX4, while the script still sees what PX4 does.
- **Scripts keep time on PX4's clock** (from its IMU timestamps), which in the sim is Gazebo's, so a run means the same at any sim speed. A clock that stops for 30 s of real time counts as a hung sim, not a failed drone.
- **In P, PX4 fires the chute itself:** its parachute output (function 401) drives the bridge's first servo, which sits at its low end in flight and swings to its high end on flight termination, and the drag plugin fires the canopy past halfway. Termination also stops the motors, so the order comes from PX4. Flight termination (CBRK_FLIGHTTERM 0) is on only where there's a chute.
- **New pass/fail numbers in the targets,** my picks: a return lands within 2 m of where it took off; after a failure, a controlled landing comes down slower than 2 m/s at the end, and ending more than 30 m from where the failure hit is a fly-away.
- **A script's marks come in pairs,** "hold start" and "hold end", because a bare "hold" collided with PX4's Hold mode in the first flight's grading.

### The first wind tunnel visuals (decided 2026-10-20)

I wanted to see the drag, not just read a number, so the Aero side track's visual half starts now, ahead of its OpenFOAM half.

- **FluidX3D on the PC's RTX 3060, on Windows,** in `C:\dr\fluidx3d`, outside this repo (its license isn't GPL-compatible). My changes are marked as altered source and committed in that clone; it becomes a public fork before any picture from it is posted, since its license requires publishing altered source with results. It did on 2026-10-22: [github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum](https://github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum).
- **The first case:** the CAD's watertight body with every module on (Max), props left out, at the 10 m/s cruise, in a 1.4 by 3.2 by 1.1 m tunnel of 4.3 mm cells (60 million), with the Smagorinsky subgrid model for the high Reynolds number (about 260,000).
- **What it shows:** streamlines in the drone's middle plane and the vortices it sheds, colored by speed in turbo, the project's CFD colormap, swapped in for FluidX3D's rainbow.
- **Pictures, not numbers.** FluidX3D's drag (about 230 cm² of drag area here) is labeled visual-grade: its own docs say it runs 1.3 to 2x high without a wall model. The drag tables still come from OpenFOAM, proven on a sphere first.

### What flying the scenarios changed (2026-10-20)

- **PX4's attitude gains are 9, not the x500's 6.5** (MC_ROLL_P and MC_PITCH_P). At 6.5 a 15° stick step settled in 0.6 s against the 0.5 s target; at 9 it settles in 0.25 s and overshoots 3 to 4%. The tuning lives in one place in the generator, with the reason next to it. *Corrected 2026-10-20:* in the final batch the x500's 6.5 settles in 0.29 s and 9 in 0.17 s, so both make the target; the 0.6 s came from early runs, before the runner's fixes. 9 stays, because it settles 1.7 times faster with 3% overshoot.
- **The chute is PX4's output function 401.** I first used 400, which is PX4's landing gear: the "gear" retracted after take-off, the servo swung over, and the plugin fired the chute 4 m up. Mission then crawled along at 4 m/s with an open canopy, and the wind blew it over. One wrong number, two failed scenarios.
- **Stick inputs are flown in PX4's altitude mode, over MAVLink,** the way a pilot flies it (COM_RC_IN_MODE 1 for that run). The script waits until PX4 really is in altitude mode, because once it wasn't, and the first stick movement dropped PX4 from Hold into Position mode, where a stick means a speed.
- **A dead motor is flown with CA_FAILURE_MODE 1,** PX4's "drop the failed motor from the mix". The x500 ignores motor failures, so without it the injected failure never reached the motor. It's the setting I'd want on the real drone anyway.
- **The GPS fails on PX4's side:** its estimator stops using it (EKF2_GPS_CTRL to 0) mid-flight. PX4's sensor failure injection only works with Gazebo Classic's bridge, not Harmonic's.
- **Power is read off the thrust table by thrust,** the sim rotor's motor constant times its speed squared, not by its speed. The one-number motor fit runs 3% slow at base's hover, which is 9% in power read by speed; by thrust, the sim's hover lasts 33.3 min against the sizing model's 33.2.
- **After a termination or a dead motor the script just waits 25 s** and the grade comes from Gazebo's ground truth: PX4's own estimate can't be trusted to say the drone is down after it has tumbled.
- **pyulog is a main dependency now,** not part of the flight extra: reading PX4's logs is analysis, so Windows can grade, draw and replay flights already flown. MAVSDK stays in the flight extra.
- **The scenarios fly at 4x sim speed, two at a time.** 4x matches real time (hover drift 0.07 against 0.09 m, step overshoot within a percent); four at a time overloaded the PC (load 18.6 on 16 threads) and spoiled the results.
- **The safety monitor's triggers are timed on the real failures too:** for the drop and the dead motor, how soon after the failure its first trigger would fire. Not a pass or fail of the drone: they're in shadow mode.
- **Every miss in the report gets its reason, or says it hasn't been looked into.** The reasons are written once in the report code, next to the unproven list.
- **Low battery runs on PX4's simulated battery, drained at my battery model's hover rate,** with the return called at 30% and a warning at 35%. That's a stand-in for my firmware's energy-based return; whether it landed above the reserve is judged by my battery model from the logged rotors.

### The flight sim's last batch (2026-10-20)

- **Batches fly one at a time at 4x,** with nothing else running. Two at a time kept the PC at a load of about 12 on 16 threads, and about ten runs failed in ways that weren't the drone: a short stall at 4x is four times longer in the sim, and it starves PX4's control loop. Every one of them passed flown alone.
- **A take-off where the model never climbs at all is the sim failing,** not the drone, and the run is "not flown". A drone that climbs and then crashes stays the drone's.
- **Step 4 is done with three findings,** all in [the log](log/2026-10-20-flight-sim-final.md): a dead motor without P is a crash, a GPS failure is a blind descent that can drift past 30 m, and cruise endurance is 25% under the sizing model. The design questions they raise (P in every combination, an optical flow sensor in Base) are mine to decide.

### What finishing the flight sim changed (2026-10-20)

Design changes, from the open list:

- **The pack's insides are worked out, not guessed.** The cells are joined by nickel-plated copper strip (10 by 0.3 mm), spot-welded to the cells and soldered to the leads, with 80 mm of 12 AWG silicone lead, the balance lead, the XT60's half and the wrap. That comes to 2.32 mOhm and 43.3 g, against a 60 g guess, at 15 A/mm² in the copper at the 90 A cap. Plain nickel strip would have been several times the resistance at this current. The sizing model's wiring resistance is 6.12 mOhm now, with the pack's own share in it.
- **The ARK GPS sits in a printed cradle on its mast,** held with four foam tape pads. The cradle is its own printed part, because with it on, the mast no longer printed flat.
- **Each module locks onto the rail with M3 thumb screws into heat-set inserts,** three of them along the rail. The inserts, screws and nuts are in the hardware lists, counted from the CAD.
- **The sizing model reads full throttle off the motor's table at the motor's power,** for both the capped and the uncapped case, extrapolating past the top row as thrust going with power to the 2/3 and rpm to the 1/3. Before, it scaled the top row with a power law, which landed about 4% off the table's own rpm.
- With all of that, Mission is 2408 g in the sizing model (with the 200 g margin) and 2208 g in the CAD, and hovers 25.8 min (22.2 pessimistic). Still a pass, still thin.

The flight sim runner, from flying the batch:

- **The wind ramp follows the sim clock,** not a count of publishes: at 4x, each publish took real time that turned into sim time, and a 10 s ramp stretched to about 110 s.
- **The payload grab lets go 2 m east of the pickup, 1.5 m up, and lands clear of it.** Landing on the dropped box tipped the drone. The detach is sent four times, because once it was lost.
- **Dead-motor runs use a world with a 2 ms physics step,** after Gazebo's physics engine hit an internal assertion in the tumble at the usual 4 ms.
- **Less telemetry, and a longer offboard timeout.** MAVSDK asks for the IMU at 50 Hz, position at 10 Hz and the battery at 1 Hz, with no heading stream. PX4 calls offboard lost after 3 s of real time instead of 1, because the runner's own Python could fall behind for a moment under load and PX4 flew home in the middle of a payload grab. A dropped radio is still tested, by the lost-link scenario's relay.
- **Gazebo messages go out through Gazebo's own Python bindings** (Ubuntu's python3-gz-transport13), with gz's command line as the fallback. Each command-line publish cost about 0.9 s and a quarter of a CPU second; the bindings take 0.04 s. Two runs at 4x already keep the PC at a load of about 12 on 16 threads, and in the wind scenario in P, PX4's IMU went quiet for 44 ms of sim time right as the wind changed, just before it tumbled. Whether that is the whole story gets checked by flying it alone.

Research, closing two open questions as far as reading can:

- **HaLow on the Pi 5:** I found no working report for Heltec's SPI card (the HT-HC01P) on a Pi 5. The SDIO version (HT-HC01) on Heltec's HT-HR01 carrier was reported working once on the Morse Micro forum, with driver 1.12.4, and USB HaLow adapters work through an OpenWrt backport for the Pi 5. The part swap waits for step 6, where the video link gets designed anyway.
- **The motor cut board's two 1 kOhm resistors:** still no schematic for the CJMCU-5018. TI's datasheet wants the TS3A5018's control inputs pulled low, and the design already adds its own 10 kOhm pull-down, plus a meter check of the board before it goes in, so the board fails the safe way whatever those two resistors turn out to be.

### My firmware (decided 2026-10-20)

Step 5's talk, which I asked to run without stopping, so I made the calls and wrote down why. The full reasons are in the [firmware spec](specs/2026-10-20-firmware.md).

- **C++17,** on all three targets: my PC (the sim and the tests), the ARK FPV's STM32H743 and the Teensy 4.1. Host tests run with the address and undefined behavior sanitizers, in CI.
- **One core library with no hardware in it,** and thin layers around it for the sim, the ARK FPV and the safety monitor.
- **It speaks PX4's MAVLink dialect and writes ULog,** so the flight sim's scenarios and graders fly and grade it unchanged. That makes "passing the same tests as PX4" literal.
- **My own code, reading PX4's (BSD) and dRehmFlight's (GPL-3.0),** with anything adapted saying where it came from. This closes "which open-source flight code to start from".
- **Estimators simple first:** Mahony's complementary filter for attitude, small Kalman filters for height and position, and an EKF only if the scenarios show these aren't enough.
- **Control is model-based:** each rate loop asks for an angular acceleration, and the mixer turns that into torque with the CAD's inertia and into motor speeds with the motor model. The mixer gives up yaw first when the motors run out, then collective thrust, and only then roll and pitch.
- **The safety monitor is its own program from day one,** with its own simulated IMU, and its triggers have to match the Python reference from step 4 on the same data.

### What building my firmware decided (2026-10-20)

Calls made while building step 5, in the order they came up.

- **My gains have their own names** (PCS14_ANGLE_P, PCS14_RATE_P, PCS14_RATE_I, PCS14_RATE_D, PCS14_YAW_P, PCS14_YAWRATE_P), not PX4's MC_ ones. My rate loops ask for an angular acceleration, so the numbers mean something different from PX4's and reusing the names would only mislead. The ground station tunes these.
- **The tuning came from a sweep on my PC's model of the drone:** rate P 20, I 70, D 0.5, self-level 6.5, and the accelerometer's pull on the attitude cut to 0.3 in the air. A 15 degree step settles in 0.26 s. A higher I holds an off-center weight better but leaves a slow tail on every step (0.62 s at 100); at 70 a 3 mm offset costs 3.6 degrees, under the test's 5. *Changed the same day:* in Gazebo the 6.5 self-level gain overshot 4 to 6%, right on the 5% band the steps scenario grades with, so a step's settling jumped between 0.2 and 0.6 s and P+C missed once at 0.61. A second sweep moved it to 5.5: 0.6% overshoot on my PC's model, and in Gazebo every step in every combination settles in 0.27 to 0.33 s with at most 2%.
- **The attitude filter takes the drone's own acceleration out of the accelerometer,** from the GPS's velocity. Without it, a long lean fooled the filter into calling the drone level until it was at 47 degrees.
- **The heading locks onto the first compass sample,** as PX4's does, instead of turning toward it slowly.
- **Gazebo's compass is put right in my sim layer, at any tilt.** Gazebo Harmonic lays the Earth's field out left-handed (fixed upstream in gz-sim pull request 2460, in a later release). PX4's bridge undoes that with a fixed swap, which is only right when level. Mine undoes it using the tilt, which is all it needs, because the swap and a turn about the vertical commute. Measured on static models level, pitched and rolled, to four digits.
- **The height's zero is the barometer's average over its first second,** not its first sample. The sim's barometer has 3 Pa of noise, and one unlucky first sample put the ground 0.7 m off, so a take-off to 30 m stopped at 29.2 by the drone's own reckoning.
- **After take-off it holds the take-off height,** as PX4 does, not wherever the "close enough" test caught it (up to 0.3 m away). P+C's hover missed its 0.3 m by 4 cm until this.
- **A touchdown is measured where the drone first gets within 0.4 m of the ground,** not 5 cm. A drone that tumbles and lands on its side or its back keeps its middle up to a quarter meter up, so V+C's 24 m/s crash on my firmware was graded at the slow roll seconds later and passed. Every run on both firmwares was regraded with it.
- **The disarm timers count from arming,** like PX4's: 2 s after landing, 10 s if it never took off.
- **The parachute rule is off in the flight sim's scenario runs on my firmware.** The scenarios compare my firmware with PX4, which has no such rule, and several fly above 30 m without P. The rule has its own tests.
- **The geofence uses PX4's names and defaults:** GF_MAX_HOR_DIST and GF_MAX_VER_DIST (0 is no fence) and GF_ACTION (hold). The fence is mine for the day, tightened by the limits profile's when it has one. It asks once a breach, and again if the drone leaves after coming back inside. "Terminate" lands instead where termination isn't allowed.
- **Pre-arm checks:** the IMU, barometer and compass all reporting, a position when the mode needs one, the battery above critical (PX4's rule: low only warns), the kill switch off, and a live safety monitor that isn't cutting. The monitor sends its own heartbeat for this. If it goes quiet in flight, the flight controller warns once and flies on, the same as it would with a dead Teensy.
- **The fuel gauge counts mAh, and the voltage can only pull it down.** It reads the charge off the cells' resting-voltage curve too (the terminal voltage plus the current times the pack's resistance, smoothed over 2 s), the curve the sizing model flies on, and takes that when it's lower: a faded pack or a current sensor reading low shows up there first. A pack that just stopped working hard reads high for a while, so the voltage never raises the count. In the flight sim the failsafe still goes by PX4's simulated battery, so the low battery scenario means the same for both firmwares; the gauge goes live with the ADC and the ESC's current telemetry.
- **The payload grab carries the box where the claws would.** Gazebo's attach joint keeps whatever offset it finds, and holding the box rigidly 0.5 m under the drone was a boom that multiplied the roll inertia by five. My rate loop only knows the drone's own inertia, so it swung itself over; PX4's gains coped. The box now moves to just under the feet before the joint closes, and PX4's four payload runs were flown again that way: all pass. My loops hold steady up to about four times the inertia they're told, measured on my PC's model.
- **The ARK FPV runs PX4's clock tree for this board:** 16 MHz crystal, the core at 320 MHz (not 480), the buses at 160 and 80, the timers at 160. The one change is PLL1's input range, set to the reference manual's 8 to 16 MHz for a 16 MHz input where PX4's file says 4 to 8. This caught a bug: the board image timed DShot from a 240 MHz clock, which on this tree would have sent DShot400.
- **The hardware watchdog times out at 20 ms,** twenty missed passes of the 1 kHz loop. It starts once the slow start-up is done.
- **The compass and barometer start the way PX4's drivers do:** the IIS2MDC at 100 Hz with offset cancellation, the BMP388 at 16x pressure and 2x temperature oversampling with no filter. Mine runs the barometer on its own at 25 Hz instead of starting each reading. The compass uses the datasheet's 1.5 milligauss a count (PX4's driver uses 2% more; calibration takes up either), and the barometer's compensation is the datasheet's floating-point form, checked against Bosch's integer form to 0.01 Pa.
- **The flight sim report shows my firmware's runs next to PX4's,** in their own matrix and section, with each cell saying where the two disagree. Each firmware's runs load separately, so neither can leak into the other's verdict.
- **Proposed, waiting for me:** a safety monitor cut stays latched for the rest of the flight, clearing only on the ground, disarmed, with the kill switch off. It's built that way; it's a safety rule, so it's mine to confirm.

### Modules in sim (decided 2026-10-20)

I asked for the open items to keep moving without stopping to ask, so these were my calls, written down as I made them. The reasons are in the [step 6 spec](specs/2026-10-20-modules-in-sim.md).

- **The safety monitor fires the chute,** as the safety rules say it can: on the pilot's chute switch, and from its own triggers once they're out of shadow mode. It cuts the motors first, every time, and it does nothing without P fitted, since cutting the motors for a chute that isn't there would drop the drone. On the drone it takes the release servo's line from P's node (Teensy pin 31) or uses its own release line (pin 37); in the sim it drives the servo the flight controller drives.
- **Its triggers stay in shadow mode.** They've shown no false triggers in the sim, but "shown zero" is a call for real flights, not a sim's clean IMU. Until then only the pilot fires the chute from the monitor.
- **The release latches like the cut,** clearing only on the ground with the flight controller disarmed and the kill switch off. That's the latched-cut rule I still have to confirm, so the same goes for this.
- **Step 6's scenarios fly my firmware only:** the hung flight controller needs my monitor in the loop, and the drop heights and the jolt are about the drone and the chute. They stay out of step 4's matrix and run when they're named.
- **The opening jolt gets two numbers:** the sim's, from Gazebo's ground truth during the opening, and the textbook bound, Cx q CdS with Knacke's 1.7 for a solid canopy at infinite mass. The structure track designs to the bound.
- **HaLow is modeled from Morse Micro's numbers** for the MM6108 module (Heltec publishes no sensitivity for its card), line of sight over flat ground at 915 MHz with the ground's reflection, and a 10 dB fade margin for everything that leaves out.
- **The camera goes on a model only when a scenario asks for it** (V's Camera Module 3, 720p at 30 frames a second, just ahead of the body, tipped 30 degrees down), as a copy of the model's SDF in the run's folder. PX4's server config loads Gazebo's rendering system for every run, so a camera on every model would render in every batch.
- **The live video's budget is 60% of HaLow's rate on the air, less 0.1 Mbps of telemetry,** a rough figure for 802.11's overhead at these rates, encoded as H.264 in software the way the Pi 5 would.
- **The companion computer stays the Pi 5,** with the numbers behind it: neither it nor the Jetson Orin Nano has a hardware video encoder, the jobs that want a GPU run on the laptop, and visual-inertial odometry has been run on older ARM boards than the Pi 5's.

### The build package and the structure's first pass (decided 2026-10-21)

My calls, written down as I made them. The reasons are in the [step 8 spec](specs/2026-10-21-build-package.md), the [structure spec](specs/2026-10-21-structure-beams.md) and their logs.

- **The build package is generated,** by `pcs14 package` into `docs/build/`, from the catalog, the build, the connection list and the reports, so it says what they say.
- **Every bought part carries a fallback,** in the catalog's `fallback` field, with what changes in the design if it's used, and a `buy_note` for what the shop said on the day (stock, pack sizes, a better price elsewhere). Prices drift; the date is beside each one.
- **A part's own lead isn't bought twice.** The connection list marks the motors' leads `own_lead`; the parts list skips them, the wiring guide keeps them.
- **PX4 flies first,** with the flight sim's parameters (less the simulator's own), as lines for PX4's console. My firmware flies only after its register-level drivers pass on the bench against PX4 on the same board.
- **Until the safety monitor's Teensy image exists, it isn't on the drone,** and the first flights are PX4's, tethered. The image needs PJRC's Teensy core, a download for me to approve.
- **Every unproven item carries the first thing to measure,** written in its own report beside the claim; the site and the test plans read the same pairs.
- **The arms' in-plane mode sits near the hover's once-a-turn shake** (80 to 144 Hz against 88 to 103 Hz): balance every prop, check the first tethered gyro log near 90 to 100 Hz, and notch it if it's there.
- **The chute's mount gets a hang test before P flies:** 26 kg (the opening jolt's bound) from the riser's point for a minute, then 39 kg. Steel screws for the module rail (about 3 g more) are suggested, and waiting for my review.

### The drone view (decided 2026-10-21)

The site's home is one 3D drone that never leaves the screen; the design is in the [drone view spec](specs/2026-10-21-the-drone-view.md), the work in its [plan](plans/2026-10-21-the-drone-view.md). The calls I made building it:

- **Every pin's place is catalog data,** in each part's `cad` block as `connectors`, with a source: the maker's drawing, PCB file, STEP model or photos where published, an estimate with its note everywhere else. A plug in a socket sits where its socket does.
- **Detail is a look, never the envelope.** A part's look (chips, plugs, pins, the motor's bell, twisted props, slotted arms) is what the pictures and the site draw; the checks and the mass spread keep the envelope. The props' twisted blades stay out of the mass spread too, since they'd move the inertia 0.07% from what every flight model was made with. A screw head that would stand proud of its part is sunk flush in the look instead, and my printed parts get no look at all, since their solid is what gets printed.
- **Wire routes start and end at their plugs,** and a wire is cut to its whole run, plug to plug, branches included. The rough routes before this missed the plugs by up to 54 mm, and the guide cut wires to the route alone.
- **The extra wire waits for the motor order.** The redrawn routes carry 8.7 g more wire in Base, most of it the motors' own leads crossing the board because the ESC's pads run in Betaflight's order. It goes into the catalog when I decide that, not before, so the sizing reruns once.
- **The animations are the real runs,** liftoff to touchdown, eased to a calm hover at both ends, sped up on a log scale into a 15 to 30 s loop, real time at each kind of event's first appearance. A run that comes down hard (a crash, or under the chute) fades out where it fell instead.
- **The world moves, not the drone.** In Fly it the drone stays in the middle and turns with its attitude; the grid, its trail and the story's props move past it.
- **Nothing is fetched at runtime.** The textures are drawn in code and the reflections come from three.js's own room scene.
- **Fly it shows what's going on** (after my second look): each scenario has a drawing of its run and the first sentence of what it tests; the route hangs in the air with a curtain to the ground; and a strip under the drone has what just happened in plain words, a map from above and its height. The strip runs along the loop as it plays, not the run's clock, so a long quiet stretch takes as little room as it takes to watch and the moments have room. A run's drawing is its path from above only when that path is more than a line (its narrow spread over a quarter of its long one); otherwise it's its height.
- **The whole site reads as one instrument** (after my first look at it): every page and both modes share the mono face in small capitals for headings, labels, controls and numbers, Inter for reading, thin lines, square corners and one accent, with the same bar along the top (the way back, the page's name, the menu). The blueprint's drawings are pinned to the corners of the space the panel leaves, so a wide or short screen can't crop them or hide them under it, and the menu sits above the panel.

### The smart features in sim (decided 2026-10-20 and 2026-10-21)

I asked for the open items to keep moving without stopping to ask, so these were my calls, written down as I made them. The reasons are in the [step 7 spec](specs/2026-10-20-smart-features.md) and the [log](log/2026-10-21-smart-features.md).

- **The sim's mission planner is a local model,** Qwen2.5 7B through Ollama: no key and no network. "The LLM lives on the laptop" below still holds for the drone, and it can still be a cloud model there. The safety rule doesn't move: the model writes a plan, the checker checks it, I approve it, the flight controller flies it.
- **Plans get approved on a map.** The model misread "60 m west of home" into a point north and east, and the checker passed it because it was safe. A checker only catches a plan that's dangerous, so the ground station has to draw the plan before I approve it.
- **The turn-back warning never counts on forward flight being cheaper than a hover.** The sizing model's curve does, Gazebo's rotors don't, and the first prediction came out 39% short. On a real drone this is pessimistic, the side to be wrong on.
- **Self-tuning excites the drone with doublets, not big steps:** a quarter stick each way for a quarter second, three times. Each doublet is fitted in its own window, with its own offset and trend, the motors' lags (12.5 ms up, 25 down in Gazebo; on the drone, from a bench test of the ESC and motor) and a dead time found along with the inertia. The found inertia is the combination's profile, and the gains stay as they are.
- **Anything that needs every motor command reads them at their own rate.** The flight log keeps the commands at 250 Hz alongside the ground truth's timeline, which can be as slow as 50 Hz.
- **Mapping needs the camera pointed straight down,** which V's bracket can't do (it tips the camera 30 degrees for the live video). The CAD needs a mapping position or a tilt servo; which one is a weight question for the build package.
- **Safe spots read off a map get the map's own error on top:** 1 m, what the mapping run places things to within. Safe spots stay on heights, not on the vision model's boxes.
- **GPS-free flight flies slowly:** 3 m/s at 6 m up worked, 15 m/s didn't, and the TF-Luna it needs for its height reads to 8 m at best. A GPS-free mode gets its own speed and height limits, set by the flow estimate, not the airframe.
- **The vision model is a describer, not a detector to act on:** 14 of 20 things boxed, the big ones every time, and boxes on things that aren't there. It answers questions about the video; it doesn't pick where to land.
- **The camera recorder writes frames on its own thread** and waits for all of them before it closes. Writing on Gazebo's callback lost the last 40 s of a run's frames.

### What the electrical build changed (2026-10-18)

- **The safety monitor's IMU is ST's LSM6DSOX** on Adafruit's breakout (1.7 g, in stock). No usable ICM-42688-P breakout is sold.
- **The module plugs sit under the Pi and under the parachute tube,** so the Pi stack rose 6 mm in the V housing and the tube stands on a printed lip 6 mm above the rail. V's and P's sockets sink into the rail. C's socket and the two fuse holders hang off the frame's back edge.
- **The HaLow card costs 1.06 W, not 0.69 W:** its Pi HAT feeds it through a linear regulator from 5 V.
- **No cell fuse links** (decided 2026-10-18): the checks showed none can both survive flat-out flight and open a dead short before the battery leads' insulation burns. A dead short in the leads is on the unproven list.
- **After a takeover, the safety monitor holds the DShot line high between its stop frames** and lets go only while the ESC answers, the way a flight controller does. The ngspice runs showed a floating line between frames breaks bidirectional DShot. A requirement for the monitor's firmware in step 5.
- **Rerun colors each wire by the share of its heating limit it uses,** not its current over its rating (the talk said current). In the 10 s burst every power wire passes its continuous rating while staying cool, so current would light them all magenta while they pass the check.
- **The wiring is weighed from the connection list** (2026-10-19): each wire's length times its gauge's grams per meter, the wire's half of each plug, heat shrink on soldered ends and sleeving on the battery leads, into base-wiring and one wiring entry per module. Base's is 59.7 g, against the 45 g guess.
- **The main path is 3.8 mOhm** from the pack's terminals to the ESC and back, worked out from the connection list, and the electrical cases start at the pack's own terminals so the leads' drop counts once.
- **C's socket and the fuse holders sit on the frame's plates,** not flush with its back edge: touching along a bare edge broke the fused body for the wind tunnel.
- **The branch fuses are soldered inline under heat shrink** (decided 2026-10-19), not in holders: 2.1 g against a 7.1 g guess with holders, with the same MINI fuses and ratings. A blown one takes a soldering iron, but they only blow on a fault.
- **The hardware is a list in design/cad.yaml** (decided 2026-10-19), counted from the CAD's holes and weighed from standard sizes: steel where the joint carries load (the legs, the battery tray, the stack, the chute's base), nylon where it holds only a light part. The CAD puts each piece's weight on the part it holds; the catalog has base-, v- and p-hardware (32.5, 2.7 and 1.7 g). Titanium for the loaded joints would save about 11 g if it's ever needed.
- **The cells are Molicel P45B** (decided 2026-10-19), replacing the P42A. The P42A was picked to keep Max under 2500 g, and Max is report-only now. Same 21700 size and 45 A rating, so the 90 A cap and the electrical design don't change; 42 g heavier, about 1.7 min more pessimistic hover. The catalog's P45B capacity is to 2.5 V and the P42A's to 2.8 V, so the real gain is about 2% smaller.
- **The release servo's feed is an ideal-diode OR** (decided 2026-10-19): TI's LM66200 on Adafruit's breakout (0.5 g) in place of the two 1N5817 Schottkys. On TI's worst-case 60 mOhm the servo gets 5.16 to 5.20 V, and 4.92 V on its backup, against 4.9. The servo is still a stand-in (Hitec's HS-55, 4.8 to 6 V), so the real Harrier servo's range is mine to get from Fruity Chutes.
- **The Pi's 5 V is checked against USB's 5.25 V without the margin** (decided 2026-10-19), through a new `pin_ceilings` check number. Raspberry Pi publishes only "a 5.1V supply" and the 4.63 V undervoltage warning, and the BEC only does 5.2, 8 or 12 V, so the Pi's 5.185 V passes with 65 mV to spare. That the Pi's real maximum is unpublished is on the unproven list.
- **My firmware's current cap gets a heat limit on the XT60** (decided 2026-10-19): it tracks the connector's temperature with the electrical check's own model (I² heating with a 98 s time constant, from the measured current) and eases the 90 A cap as it nears 100 °C, settling near the 29 A the XT60 holds forever. Full current lasts 3.1 s from Max's hover and 4.9 s from Mission's. No weight, and a setting I can tune. It's a requirement for step 5, it rests on a guessed 2.5 g contact mass, and `heat_limited` in the connection list tells the checks about it.
- **The weight now** (2026-10-19): Mission 2414 g, pessimistic hover 22.25 min against 21, a pass; Max 2623 g, over its 2.5 kg limit (report-only).

### The parts (picked 2026-10-17)

I picked the lightest build that passes every setup, Max included, over the sweep's favorite (a Hobbywing 3115 on 6S3P, 660 g heavier, which breaks Max's 2500 g limit). The sweep ranks by headroom, so this one comes in at #33 of 192, and that's fine: it meets every target I set.

| Part | Pick | Mass |
|---|---|---|
| Motors (4) | Emax E3 2814 850KV | 82 g each, without wires |
| Props (4) | Gemfan 1050 3-blade (10 x 5 in) | 16.8 g each |
| Pack | 6S2P Molicel P42A: 8062 mAh, 90 A continuous (P45B since 2026-10-19, see the electrical build's changes) | 858 g with an estimated 60 g of nickel, leads and wrap |
| ESC | Holybro Tekko32 F4 4in1 50A (AM32) | 14 g |
| Frame | iFlight Nazgul XL10 V6 | 343 g |
| Current cap | 90 A, in my firmware (100% of the pack's rating) | |

| Setup | Weight | Hover (published / pessimistic) | Thrust-to-weight at 20% charge |
|---|---|---|---|
| Base | 1732 g | 39.9 / 34.0 min | 3.59 |
| Mission (with the 200 g margin) | 2254 g | 25.7 / 22.2 min (target 21) | 2.76 |
| Max | 2454 g | 22.6 / 19.6 min (target 17) | 2.53 |

- **Why this one:** it's the only kind of build that keeps Max under 2500 g, it's 660 g lighter than the robust pick (less energy in a crash, an easier job for the parachute, 6 fewer cells), and its hover point (564 g per motor) sits inside Emax's measured table, which starts at 545 g.
- **The catch:** thinner margins. Mission's pessimistic hover clears its target by about 6%. And if cruise really is up to 2x optimistic (the honesty check), Mission's 32.8 min cruise could be closer to 16 than 25. That's the first thing a thrust stand and the rotor drag model would check.
- **The growth margin stays 200 g.** Mission passes on the pessimistic numbers up to about 250 g, and turns marginal around 300 g, so 200 g leaves about 50 g of slack for parts that come in heavier than their estimates.

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

*The CAD talk (2026-10-17) settled the details, all in the spec under "Settled in the CAD talk": our own solids from published dimensions, with every part checked for an existing CAD model first; battery underneath and modules on top; printable designs for our own brackets, legs, tray and rail; check limits based on what each one costs; Rerun plus styled stills for watching; the full set of outputs on every run; and rough wire routes now.*

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

**The end goal, in my words (2026-10-19):** a very complete blueprint on a website. An in-depth 3D model of the drone I can click into and explore, from the structure down to the circuits and where everything connects, with every simulation that was run behind it. For the circuits that means the wire routes in 3D with their gauges and currents (`electrical.json` and `cad.json` already carry them), each board's pin map, the harness diagrams and the schematic, and a click on any wire or pin showing both its ends. One gap for later: the CAD places each board but not each connector on it, so a wire's ends in 3D are a route's ends, not the plug itself.

**The simulations shown live (2026-10-20, in my words: "the simulations running in the site, maybe not actually rendering it, but shown live").** The site doesn't run Gazebo, PX4 or the wind tunnel in the browser. It plays their recorded results back as if live: the drone flying each scenario's logged path in 3D, its height, speed and motors scrolling alongside, the events (the chute firing, the link cutting) popping up as they happen, and the wind tunnel's flow animated around the drone. Each flight's data comes from the flight sim's logs and results, and each wind tunnel run from its frames and fields. Everything animated, the 3D drone clickable and free to look around.

**What it's built with (decided 2026-10-20):** Vite, React and TypeScript, as a plain static folder with relative paths; three.js through react-three-fiber for the 3D drone; SVG charts; a `pcs14 site` command that writes the data it reads; Vitest for its tests. The same language as my portfolio (Next.js on React), but not tied to its version. The reasons are in the [project site spec](specs/2026-10-20-project-site.md).

It's built from the data files every step writes, so it grows as the steps finish, starting with the sizing model. The individual sims stay available on their own too: the Rerun recordings, the reports in `docs/reports/`, and the clips.

**Where it lives (decided 2026-10-17):** on my machine while the research runs. It doesn't go live until the project is done, and then it joins my portfolio site, wearechintu.com, as another project. So it's built as a self-contained static site with relative links, which can drop into the portfolio wherever it ends up, with no server needed. Its code lives in this repo like everything else, but the built site isn't published anywhere until the end. What it's built with gets settled in its own spec. (2026-10-22, in my words: "I don't intend to build the drone anytime soon, so this is just an idea." So the site doesn't wait on a build to go public; it goes when I say so, and what it needs for that is ready: the FluidX3D fork is public and the site carries every license it owes.)

**What building it decided (2026-10-20).** I asked for it to be built without stopping to ask, so these were my calls, written down as I made them:

- **It opens from a folder on disk, through scripts.** Browsers won't let a page opened as `file://` fetch anything, so `pcs14 site` writes every data file twice, as JSON and as a small script that hands the same data to the page. The 3D model goes the same way, as base64.
- **The first load is held to 600 kB,** counting the page, what it names and the fonts. The fonts are Latin only, and the pages with three.js in them (the 3D drone and the flights, about 860 kB) load only when they're opened. It was 267 kB then, and 350 kB on 2026-10-22.
- **The model is thinned with gltfpack** at half the triangles, keeping every piece's name: the CAD's 11.9 MB GLB comes to 3.0 MB. The CAD's own GLB stays as the CAD makes it.
- **Nothing is written twice.** A step's page comes from the README's plan, its report, the log and the learning file, matched by name. The unproven list is decisions.md's own table plus each report's "What it can't prove". The wiring page reads every board's pins from `electrical.json`, which the electrical report now writes.
- **The flight pages fly the CAD's model,** in each run's color with only its combination's modules. A light stand-in shows until the model has loaded, so the page doesn't wait on 3 MB.
- **The home page is quiet:** the CAD's three-quarter view without its post header, a line about what this is, one line per step with its status, and one line to what the sims can't prove. (Replaced 2026-10-21 by the drone view.)
- **The wind tunnel's flow plays on the drone in Fly it** (decided 2026-10-22, [spec](specs/2026-10-22-the-wind-tunnel-in-fly-it.md)). My FluidX3D fork writes 64 snapshots of each run's flow over its last half, in a box around the drone on 12 mm cells, with the speed on a plane through the drone at each. This repo loops them seamlessly and carries 2,400 particles through them. Fly it plays the particles as fading trails, with the slice's frames blended on the GPU, slowed 20 times, and the drone held still at the tilt it flies with. My first version traced lines through the flow averaged over time instead. I dropped it: it missed the air going round the drone and through its wake, the lines started out of nowhere, and the wake was a still picture. There are seven cases: the air from the front, behind, each side, above and below at 10 m/s on the body alone, and the hover with its disks. The flow files are FluidX3D output, so they stayed local until the fork went public (2026-10-22), and the force shown with them is said to be visual-grade.
- **The wind tunnel plays its own frames.** My FluidX3D fork writes 40 frames along each run, of the air's speed and of the vortices, each with its time, and the page plays them in order on the clock at 0.02x. Its pictures stayed on my machine until the fork went public on 2026-10-22; with the fork's switch off, the page says so and the build check warns.
- **The 3D drone turns slowly with its props spinning,** each the way PX4's quad X turns it, until someone takes hold of it.


**My altered FluidX3D is public (2026-10-22): [github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum](https://github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum).** A GitHub fork of the original, so its origin shows on the page, whose default branch, `extra-15pc-gum`, is the original's commit `dbf0bb5` plus my changes. What FluidX3D's license asks, and how it's met:

- **The origin, not misrepresented, and the altered source plainly marked:** the fork's README opens by saying it's an altered version and not the original, whose it is and where the original lives, and what I changed, file by file; every change in the source is marked `ALTERED`. The tunnel page, Fly it, the overview's credits and the site's licenses file all credit FluidX3D as Dr. Moritz Lehmann's, with links to the original and to my fork.
- **The altered source published with the results:** that's the fork. Each tunnel run's case file in this repo's outputs says what it ran, and the fork's setup reads it.
- **No commercial or military use, and no training AI models on the source:** the project and its posts are personal research, with nothing sold or paid for; the pictures don't go into paid work. The fork says all three.
- **The license notice kept:** `LICENSE.md` is the original's, unchanged.
- **Citations:** if a scientific publication ever comes out of it, it cites the papers in FluidX3D's references.
- **The turbo colormap's fit in the fork is Google's** (Copyright 2019 Google LLC, Apache-2.0, by Anton Mikhailov and Ruofei Du): credited in the code and in the fork's `THIRD_PARTY_NOTICES.md`.

Before it went public I checked it for secrets and personal details: none in its code, which reads everything relative to its own folder. One early commit had my university email as its author, where every public commit of mine uses my personal one, so I rewrote that author before the first push, dates and code unchanged.

**The site carries the licenses it owes (2026-10-22).** Its build writes `licenses.txt` beside the page, with all 98 packages its code can bundle and each one's license in full (MIT, ISC, BSD-3-Clause, Apache-2.0, and OFL-1.1 for the fonts; nothing copyleft or non-commercial), and the build check fails without it. The overview ends with the credits.

**The docs (decided 2026-10-22, [spec](specs/2026-10-22-the-docs.md), [plan](plans/2026-10-22-the-docs.md)).** The menu is the drone's documentation, in depth, and holds everything the drone view shows as well:

- **Twelve pages in four groups, one home per subject:** the drone (overview, spec sheet, parts, wiring), what was tested (flights, the wind tunnel, what the sims can't prove), the work (every step, Build it) and reference (the library, the data, the math). The catalog went into Parts. Other pages link to a subject's home instead of repeating it.
- **One order and one name for everything.** The combinations always run base, V, P, C, mission, V+C, P+C, max, and the wind tunnel's cases go by the drone view's names.
- **A number on a page is its report's,** formatted the way the report formats it (toward failing), and a test holds the page to the report.
- **A step shows its report now, apart from what I wrote then.** The plan's outcome stays as I wrote it when the step finished, labeled that way. Above it, the report's verdict in its own words, its key numbers and its sections, as they stand today.
- **Links stay on the site** wherever the doc is in the library.
- **A replaced doc says so in its own first lines,** starting "Superseded" or "Partly superseded" and saying by what, and the library marks it from there. Nothing gets deleted.
- **The math page is only the math,** in step order, the functions that explain themselves first, its links pinned to the commit the site was built from.
- **The data page says what every file holds and how big it is,** the site's own files too.
- **The contents stay on screen** (after my first look): on any docs page, the twelve pages run down the left side, pinned as it scrolls, with the one I'm on marked, so moving between them is one click. On a screen too narrow for both, the menu button in the bar stands in for it. Under the page I'm on, and only that one, its sections are listed from its own headings (its sub-headings too when it has only a few main ones): a click scrolls there, and the one I'm reading is marked.
- **The costs say their total plainly** (after my first look): Build it gives each combination all in, the drone plus what's bought once (Base $1,238.77, Max $2,534.28 on 2026-10-22), and Parts gives each line's total, each module's and the whole drone's. They add up from the same lines the package does, and a test holds them to its totals to the cent. The screws and printed parts stay out of the sums, as they do in the package.

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
- It cuts the motors by taking over the four ESC signal lines, not by switching the main power. A switch in a ~100 A power line is a new way to drop a healthy drone. The first plan just disconnected the lines, counting on the ESC to stop when its signal disappears, but AM32 keeps the last throttle for half a second before it does. So (decided 2026-10-18 in the electrical talk) a FET multiplexer hands the lines to the Teensy, which sends DShot stop frames, and the motors stop within a millisecond. It has to pass signals both ways, because bidirectional DShot sends RPM back on the same wire. The electrical spec has the circuit.
- It fails in the useful direction. If the Teensy loses power, the switch passes signals and the drone keeps flying on the flight controller. It takes power from both the flight controller's 5 V and the module supply, through diodes, so it can still fire the chute if the flight controller loses power. The flight controller watches the Teensy's heartbeat, warns me if it goes quiet, and won't arm without it.
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

The frame, motors, ESC and battery are sized for Mission plus a growth margin (decided 2026-10-17, see the targets below), but the drone flies bare first. Modules go on and off depending on what I'm doing that day.

Base is always on: frame, motors, ESC, battery, flight controller, receiver, rangefinder, the safety monitor, and a mount and plug for a Remote ID module. It flies by itself.

| Module | What's in it | Notes |
|---|---|---|
| **V: Vision & nav** | GPS + compass, camera(s), companion computer, HaLow video link | GPS and camera go together, because mapping, safe-spot landing and GPS-free flight all need both |
| **P: Parachute** | The chute and its ejector | The flight controller or the safety monitor can fire it. See the parachute rule below |
| **C: Claws** | Claws + servos | Only if we come up with a unique claw on an actual arm. That conversation waits until the modules step; for now the drone just needs to work. Works without V, but you'll want the camera to see what you're grabbing |

- **The parachute rule:** the firmware checks whether P is fitted, and won't fly autonomous missions or go above about 30 m without it. The chute needs about 10 m to open anyway, so there's no point carrying it for low hover tests.
- **A standard module mount (#17):** one mechanical interface, and one connector carrying power and a data bus.
  - The firmware sees which modules are on and loads a tuning profile to match. The self-tuning controller (#21) then fine-tunes in flight.
  - The bus (decided 2026-10-18): DroneCAN for the modules' parts, plus one serial line for the companion computer's MAVLink. See the electrical spec.
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

**Mission sizes the drone, not Max (decided 2026-10-17).** The claws only happen if a unique claw on an arm comes along, and sizing for Max meant every flight carried motors big enough for claws plus a payload. So the motors and battery get sized for Mission plus a growth margin, starting at 200 g, which leaves room for a light add-on like the Meshtastic relay or a solar panel. Max still gets checked and reported, but it doesn't have to pass. The report shows what each extra 100 g of margin costs in minutes of flight, and the final margin gets picked in step 1d with those numbers in front of me.

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

Max only makes 2.5 kg if most parts land at the light end. Since Mission sizes the drone now (see above), that's a check, not a requirement. If the claws ever happen and Max doesn't fit, the options are raising the cap (it's my own target, not a law), a lighter payload, or bigger motors.

### Roadmap

The steps live in [roadmap.md](roadmap.md), and the live plan with each step's outcome is in the [README](../README.md#the-plan). It's the plan I'm following, and it will change. The full revision on 2026-10-14, with every change tagged R1 to R7 and the reason for each, is in [specs/2026-10-14-plan-revision.md](specs/2026-10-14-plan-revision.md).

## Hardware (draft)

Three layers, plus a safety monitor underneath them all. Each one has to stay safe if the one above it dies:

1. **Flight controller:** the hard real-time stuff. It reads the sensors, runs the PID loops, drives the motors, and handles the failsafes, the parachute and self-tuning (#21). It doesn't depend on anything above it.
2. **Companion computer** (Pi 5 or Jetson Orin Nano): cameras, GPS-free navigation (#24), and photos for mapping. It sends targets down to the flight controller.
3. **Laptop:** telemetry, the map, the LLM (#26), mission approval, 3D map processing, safe spots, and change detection (#11).
4. **Safety monitor:** the Teensy in Base, independent of all three (see above).

Parts so far:

- **Frame (picked 2026-10-17):** the iFlight Nazgul XL10 V6, a real, orderable 10" carbon X frame, with the module mount added. Printed arms would flex too much at this size. If the design hunt finds something unique, the frame goes custom (see above).
- **Motors and props (picked 2026-10-17):** Emax E3 2814 850KV on Gemfan 1050 tri-blades. See "The parts".
- **ESC (picked 2026-10-17):** the Holybro Tekko32 F4 4in1 50A: 6S, bidirectional DShot, so I get RPM from every motor. That's great for filtering and for #21. It runs AM32, open-source ESC firmware, which is a nice bonus.
- **Battery (picked 2026-10-17):** 6S2P Molicel P42A, 8 Ah and about 860 g, with my firmware capping the current at its 90 A rating.
- **Flight controller (decided):** an off-the-shelf STM32H743 flight controller board in the drone, and optionally a Nucleo-H743 on the desk, which gives me a proper debugger, every pin broken out, and hardware-in-the-loop testing. Same chip, same firmware. The board has to be one PX4 supports, with SWD pads I can get a debugger onto. Picked 2026-10-18 in the electrical talk: the ARK FPV (five full serial ports, CAN, a JST-SH debug plug), replacing the Kakute H7 that the CAD started with. The electrical spec has the reasoning.
- **Teensy 4.1:** I already have one lying around. A build would need a second (about $30) so each can keep its own job:
  1. Run the thrust stand (optional, in step 1): read the load cell, current and voltage, drive the ESC, and log to its SD card.
  2. Desk sandbox: dRehmFlight with a cheap IMU and no motors, so I can watch a complete flight controller work before I write mine.
  3. Be the safety monitor in Base (the second Teensy): its own IMU, listening to the receiver, cutting the motors on the ESC signal lines, and firing the chute when P is fitted.

  It could also be a hardware-in-the-loop bridge, pretending to be the GPS, receiver and rangefinder for the sim. It's no good for the wristband, though: no wireless. That's an ESP32 job.
- **Companion computer:** part of module V. A Pi 5 is probably enough now that the LLM and object detection (#39) are on the laptop. The only vision job that has to stay on board is GPS-free flight (#24), because it has to work when the link drops; a Jetson only if #24 needs more. Settled in step 6.
- **IMU:** ICM-42688-P (it's on most modern flight controller boards anyway).
- **Barometer:** on the flight controller board.
- **GPS + compass:** the ARK GPS (u-blox NEO-M9N, BMM150 compass, barometer) on DroneCAN, up on a mast away from the power wires (picked 2026-10-18 in the electrical plan; it replaced a Matek M10Q that went end of life).
- **Rangefinder:** downward lidar (TF-Luna or TFmini-S).
- **Control link:** an ExpressLRS receiver and a handheld transmitter, on 2.4 GHz. HaLow and Meshtastic (below) both use 902–928 MHz in the US, and so does 900 MHz ExpressLRS, so the control link stays off that band. Its protocol (CRSF) is well documented and easy to parse.
- **Data/video link to the laptop:** the lead option (2026-10-14) is Wi-Fi HaLow (802.11ah), which is Wi-Fi on 900 MHz. It has a lot more range than normal Wi-Fi, with a few Mbps up close dropping to hundreds of kbps far out. It carries normal IP traffic, so MAVLink telemetry and real compressed video can share one link from the companion computer, and existing ground station software works while I build my own. The same video could go into ATAK too (the free civilian version runs on Android). One catch: the Pi 5 has no hardware H.264 encoder, so video encoding runs on its CPU, which counts when picking Pi vs Jetson. Confirmed in step 6.
- **Remote ID:** a broadcast module on a mount and 5 V plug in Base. Whether it's fitted is up to me (see the limits profiles).
- **Power:** a dedicated 5 V / 5 A+ supply for the companion computer, and a current sensor (usually on the ESC). The main power path (decided 2026-10-18): the frame's XT60, no main fuse, and small fuses on the branches that tap the battery. The cell fuse links planned in the talk came out in the build: no gauge works at 90 A, so the battery leads are protected only by their routing and sleeving. The 5 V rail: the BEC feeds the Pi and every module, servos included, and the flight-critical parts run on the flight controller's own 5 V. See the electrical spec.
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
- Cruise speed: 10 m/s until the sizing model says otherwise
- How many clean shadow-mode flights a real build would need before the safety monitor's automatic triggers go live
- Whether to get Part 107 (in the build package's legal checklist)
- Data/video link to the laptop: HaLow is the lead option, confirmed in step 6 (the control link is decided: 2.4 GHz ExpressLRS). Heltec's SPI card has no working Pi 5 report; its SDIO version or a USB adapter are the likely swaps
- Where the Meshtastic relay (#30) lives: in V, in Base, or as its own little module
- Exactly what goes in the `us-recreational` limits profile, checked against the current FAA and FCC rules for the build package
- Camera: FPV video, stills for mapping, or both
- What "unique" is allowed to mean for the design hunt (decided after the baseline works)
- Which OpenFOAM: the Foundation release (openfoam.org) or ESI's (openfoam.com). Both have the tutorials I need. Decided when writing the setup script.
- My firmware's height estimate: barometer and accelerometer only, it lets the barometer's noise through at about 6 cm (the sim's 3 Pa), so a hover wanders about 0.2 m where PX4, leaning on the GPS's height, holds 6 cm. Gazebo's GPS has no noise, so the sim flatters PX4 there; a real GPS's height is noisy and slow. Fusing it, or a better height filter, is for when the estimator gets its next look
