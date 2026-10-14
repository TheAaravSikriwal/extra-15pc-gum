# Plan revision (2026-10-14)

*Drafted by Claude from today's review, and confirmed by me the same day. It's been split back into the [roadmap](../roadmap.md), the [decisions](../decisions.md), the [targets](../../design/targets.yaml) and the [Phase 1 spec](2026-10-13-phase-1-simulation.md), which are the live versions now. This file stays as the record of what changed and why.*

## What changed, and why

Every change from the current plan has a tag, so I can accept or push back on each one.

| | Change | Why |
|---|---|---|
| **R1** | The Teensy safety monitor moves from module P into Base. It listens to the receiver and can cut the motors on the ESC signal lines. | Otherwise the first flights of brand-new firmware have a kill switch that runs inside that same firmware. |
| **R2** | One thrust-to-weight rule for every setup: at least 2:1 at the 20% reserve, at full throttle, under load. And full-throttle current has to stay inside the battery's rating. | The old 4:1 and 3:1 didn't say when they're measured, and Base's 4:1 never actually limited anything. |
| **R3** | Every setup gets a hover-time target as well as a cruise one. Cruise means a fixed 10 m/s for now. The 20% reserve is counted in mAh, not volts. | Base has no GPS, so its cruise time can't be measured until Phase 6. Hover time can be measured in Phase 4. |
| **R4** | Phase 1 only waits on sizing, CAD and Gazebo. Thrust-stand parts get bought in Phase 1. CFD, the design hunt and the renders run alongside instead of blocking. I buy and fly the plain X, and the hunt designs v2. | As written, Phase 1 would take months before I could buy a $30 dev board, and the CFD only moves flight time by a few percent. |
| **R5** | The PX4 flight in Phase 4 stops being optional. | It proves the hardware before my firmware flies it, and gives clean logs to match the sim to. |
| **R6** | A real mass budget replaces the "1–1.4 kg" guess, with the safety monitor and Remote ID module counted in Base. | Max might not fit under 2.5 kg, and I'd rather know now. |
| **R7** | Smaller ones: a flight controller board with SWD pads, the geofence enforced on the flight controller, a firmware watchdog, antennas in the CAD clearance checks, generated meshes kept out of git, and a Part 107 decision before Phase 3. | Each one is cheap now and painful later. |

Already decided today, so not up for review here: government rules live in limits profiles, HaLow is the lead video link, the Meshtastic relay (#30) is on the shortlist, and ExpressLRS goes on 2.4 GHz.

Two corrections to the review:
- **R2's number.** The review suggested 2.5:1 at the reserve. Working the numbers through properly, voltage sag hits harder than that assumed (see Targets), so this draft uses 2:1.
- **R1's receiver.** The review suggested a second receiver for the safety monitor. Sharing the main one is simpler and still protects against the thing that matters, which is my firmware, not the receiver.

## What I'm building

A long-range quadcopter running flight firmware I wrote myself, on parts I can order. 8–10" props, low-KV motors and a 6S Li-ion pack, aiming for 25–40 minutes. It's modular: the frame carries everything, but it flies bare first, and modules go on depending on the day.

| Module | What's in it |
|---|---|
| **Base** (always on) | Frame, motors, ESC, battery, flight controller, receiver, rangefinder, module mount, the safety monitor (R1), and a mount and plug for a Remote ID module |
| **V: Vision & nav** | GPS + compass, camera(s), companion computer, the HaLow link, a 5 V supply |
| **P: Parachute** | The chute and its ejector. The flight controller or the safety monitor can fire it. |
| **C: Claws** | Claws, servos, and whatever they're holding |

The Meshtastic relay (#30) only needs 5 V and an antenna, so it can ride with any setup. Where it lives gets decided in Phase 7.

## Ground rules

- **Simulate before buying.** Nothing big gets bought until it has flown in simulation. The exception is small test parts that make the simulation more accurate, like the thrust-stand motor (R4). Most of those end up on the drone anyway.
- **Fly the plain one first (R4).** The baseline X is what I buy, build and fly. The design hunt keeps going in the background and designs v2.
- **Government rules are settings, not caps.** I plan around them and write down what they mean, but they live in a limits profile (`us-recreational` or `max`) that I switch from the ground station. The active one is always on screen and goes into every flight log.
- **The safety rules don't bend,** whichever profile is loaded.

## Safety

Four layers, and each one stays safe if the one above it dies:

1. **Laptop:** telemetry, the map, the LLM, mission approval. The LLM writes plans, a deterministic checker validates them against the loaded limits profile, I approve them, and the flight controller flies them. The LLM never commands the motors.
2. **Companion computer:** cameras, GPS-free navigation, video. If it goes quiet, that's a failsafe.
3. **Flight controller:** sensors, control loops, motors, failsafes. It depends on nothing above it, and it enforces the geofence itself, not just the plan checker (R7).
4. **Safety monitor (R1):** the Teensy 4.1, in Base, independent of everything above.

My transmitter and kill switch override all of it.

### The safety monitor (R1)

- It has its own IMU, and it listens to the same receiver as the flight controller (the receiver's output wire splits to both). So the kill switch reaches the motors through two separate boards running separate code.
- It cuts the motors by blocking the four ESC signal lines with an analog switch, not by switching the main power. A switch in a ~100 A power line is a new way to drop a healthy drone, and ESCs stop the motors when their signal disappears (confirmed on the bench in Phase 3). It has to be a switch that passes signals both ways, because bidirectional DShot sends RPM back on the same wire.
- It fails in the useful direction. If the Teensy loses power, the switch passes signals and the drone keeps flying on the flight controller. The flight controller watches the Teensy's heartbeat, warns me if it goes quiet, and won't arm without it.
- The automatic triggers (free fall, tumbling, the flight controller going quiet) start in shadow mode: they log what they would have done, and do nothing. They go live in Phase 5, after enough flights with zero false triggers. A fast descent at low throttle looks a lot like free fall to an accelerometer, so this matters. The 4.1's SD card handles the logging.
- When P is fitted, it can fire the chute too, after cutting the motors.

### Firmware rules (R7)

- A hung CPU has to mean the motors stop, not the motors stuck at the last throttle. That means a hardware watchdog, and DShot frames sent fresh every loop instead of from a free-running DMA loop that keeps resending the last one.
- The low-battery failsafe counts mAh used (R3), with voltage as a backup. Li-ion's flat curve and sag make voltage a bad fuel gauge.

### The parachute rule

Unchanged, and it's my rule, not the government's: no autonomous missions and nothing above about 30 m without P fitted.

## Targets (R2, R3)

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
- The other five module combinations have to land between Base and Max.

**Why the hover times are lower.** A quad uses a bit less power at a gentle cruise than in a hover, because moving forward keeps feeding the props fresh air. So the hover targets sit about 15% under the cruise ones. The sizing model checks that ratio, and the targets move if it's off.

**Why 2:1 at the reserve.** Motor test data is usually measured on a bench supply at full 6S voltage, and full-throttle thrust drops roughly with the square of the voltage. A rough estimate says a Li-ion pack at 20%, under full load, leaves each motor with about 55–60% of its datasheet thrust. So 2:1 at the reserve works out to about 3.5:1 on the datasheet, which already asks more than today's 3:1 for Max. 2.5:1 at the reserve would mean about 4.4:1 on paper, and heavier motors on every flight. The sizing model reports thrust-to-weight at full charge and at the reserve, so the trade is always visible.

The machine-readable version, replacing `design/targets.yaml`:

```yaml
# What every setup has to hit. Revised 2026-10-14 (see docs/decisions.md).
# The sim checks all 8 module combinations. Base and Max are the extremes,
# and every combination in between has to land between them.

reserve_battery_fraction: 0.20 # land with at least 20% left, counted in mAh used
cruise_speed_ms: 10            # for now; the sizing model's least-power speed replaces it

every_setup:
  min_thrust_to_weight: 2.0           # at the 20% reserve, full throttle, under load
  current_within_battery_rating: true # full-throttle draw inside the pack's continuous rating

setups:
  base:
    modules: []
    min_cruise_time_min: 30
    min_hover_time_min: 25

  mission:
    modules: [V, P]
    min_cruise_time_min: 25
    min_hover_time_min: 21
    min_top_speed_kmh: 80
    hold_position_in_wind_ms: 10

  max:
    modules: [V, P, C]
    payload_g: 250 # whatever the claws are holding
    min_cruise_time_min: 20
    min_hover_time_min: 17
    max_takeoff_weight_g: 2500
```

## Mass budget (R6)

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

## The phases

| Phase | What it's for | Done when | What I buy |
|---|---|---|---|
| **0. Planning** (done) | Figure out what I'm building | Decisions written down | Nothing |
| **1. Simulate the baseline** | Prove the plain X works, with real thrust data | The baseline passes sizing, CAD and Gazebo for all eight combinations, and has a price | Thrust-stand parts, most of which end up on the drone |
| **2. My firmware in sim** | Write the flight code and the safety monitor, and prove them | My firmware flies Base in sim and on the real chip, and the safety monitor works in hardware-in-the-loop | Nucleo-H743 (~$30), an IMU breakout (~$10), a second Teensy 4.1 (~$30) |
| **3. Bench build** | Build Base, props off | Every bench check passes on my firmware, and it boots and arms on PX4 | Base parts (most of the money), a Remote ID module |
| **4. First flights** | Fly Base for real | Stable on my firmware, hover times measured | Props, spares |
| **5. Module P** | Parachute | The chute deploys reliably, the automatic triggers are live, and the rule is enforced | P parts |
| **6. Module V** | GPS, camera, companion computer, HaLow | GPS hold, every landing mode, video on the laptop, cruise times measured | V parts |
| **7. Smart features** | Mapping, safe spots, the LLM, self-tuning, the Meshtastic relay | Each one proven in sim, then for real | Not much |
| **8. Module C** | Claws | Grabs and carries 250 g, and perches | C parts |
| **9. Extras** | Wristband and whatever else makes the cut | Decided when I get there | Per extra |
| **10. v2** | Build what the design hunt found, if it's worth building | Decided when there's a winner | Per design |

**Running alongside, never blocking a phase (R4):** the CFD wind tunnel, the design hunt, the FluidX3D showcase runs and the Blender renders. Whenever they produce numbers, those go back into the sizing model and Gazebo, and the targets get rechecked.

Why P before V is unchanged: under the parachute rule, autonomous GPS missions and anything above about 30 m need the parachute fitted, so it has to exist first.

### Phase 1: Simulate the baseline (R4)

1. **Setup script, first half:** Gazebo Harmonic, PX4 and the Python tools on the PC. OpenFOAM, ParaView and Blender come in the second half, when the CFD work starts.
2. **Sizing model:**
   - the parts catalog
   - the revised targets and the mass budget
   - a battery model with sag
   - thrust-to-weight at full charge and at the reserve
   - the current check
   - a sweep over motors, props and batteries, including 6S3P packs in case the extra cells earn their weight
3. **Thrust stand (R4):** once the sizing model has a shortlist, I buy one motor, two or three props, the 4-in-1 ESC, a load cell with an HX711 amplifier, and a current sensor.
   - The Teensy logs thrust, current, voltage and RPM across the throttle range.
   - It runs off a real 6S pack, so the sag gets measured, not guessed.
   - The measured data replaces the manufacturer's in the catalog.
   - The stand gets bolted down, and nobody stands in line with the prop.
4. **CAD (baseline X):** as in the spec, plus the safety monitor, the Remote ID mount, and every antenna (ExpressLRS, HaLow, GPS, Meshtastic) in the clearance checks (R7). In the HaLow video I watched, a prop cut straight through an antenna connector.
5. **Gazebo + PX4:** the model generator and the scenarios from the spec, plus one more. Every scenario's IMU data gets replayed through the safety monitor's trigger logic, so I can count false triggers before any real flight.
6. **The baseline passes:** tag it, price it, order the Base parts.

My firmware doesn't have to wait for step 6. Phase 2 can start as soon as Gazebo works, flying PX4's stock x500, and switches to my design once it passes.

**Done when:** I have a priced parts list for the plain X that passes sizing (with measured thrust data), CAD and Gazebo, across all eight module combinations.

### Phase 2: My firmware in simulation

1. **Architecture:** flight logic kept separate from the drivers, so the same code runs on the PC and on the H743. The watchdog and fresh-every-loop DShot are there from day one (R7).
2. **Warm-up (optional):** dRehmFlight on the Teensy with an IMU breakout.
3. **Flight modes, in order:** rate mode, then self-level, then altitude hold, each against the same tests as PX4.
4. **Arming, failsafes and limits:**
   - pre-arm checks, including a live safety monitor
   - the kill switch
   - lost link
   - low battery by mAh
   - the geofence
   - the limits profiles
5. **Safety monitor firmware (R1):** on a second Teensy 4.1, so the first one can stay on the thrust stand.
   - the kill switch from the receiver
   - the flight controller's heartbeat
   - the automatic triggers, in shadow mode
   - tested in hardware-in-the-loop with sim IMU data and a simulated kill switch
6. **Ground station v1** on the laptop: live telemetry, live PID tuning, and the active limits profile always on screen. It speaks MAVLink, so QGroundControl works from day one.
7. **Hardware-in-the-loop:** the same firmware running on the Nucleo, with the sim feeding it sensor data.

**Done when:** my firmware flies Base in sim and on the real chip, and the safety monitor's kill path works in hardware-in-the-loop.

### Phase 3: Bench build

Props stay off the whole time.

1. **Thrust-stand the other three motors**, so I know all four match.
2. **Build Base:**
   - the ESC, motors, flight controller, receiver and rangefinder
   - the power wiring and the module mount
   - the safety monitor and its signal switch
   - the Remote ID mount
3. **Bench checks:** motor order and direction, sensor readings, ESC telemetry and failsafes, plus:
   - the kill switch through both paths
   - what the ESC does when its signal disappears, and how fast
   - that the signal switch passes signals with the Teensy unpowered
   - that the receiver feeds both boards cleanly
4. **Rules, taken into account (they're settings, not caps):**
   - FAA registration and the TRUST certificate
   - the Remote ID module
   - fill in the `us-recreational` profile from the current FAA and FCC rules
   - decide on Part 107 (the project is partly for my career, and the recreational rules cover flying strictly for fun)
   - find a field, and check the airspace and LAANC

**Done when:** Base passes every bench check on my firmware, and boots and arms on PX4.

### Phase 4: First flights

1. **PX4 first (R5):** fly the real airframe on PX4. Hover, simple maneuvers, and a first hover-endurance run. If something's wrong with the hardware, I find out before my firmware is in the picture.
2. **Match the sim to reality** using the PX4 logs. It's the cleanest comparison, since the sim flies PX4 too.
3. **My firmware, tethered** to a test rig.
4. **Free flight:** low, in an open field. Self-level first, then altitude hold, then rate mode. The kill switch works through both paths, and the automatic triggers stay in shadow mode, logging.
5. **Hover endurance** with ballast standing in for V, P and C, checked against the hover targets.

**Done when:** it flies stably on my firmware and the hover times are measured. If they miss, the targets change here, with the reason written down.

### Phase 5: Module P (parachute)

1. **Sim:** free-fall detection, the motor cut, and how the chute deploys.
2. **Build** the chute and its ejector. The safety monitor is already on the drone.
3. **Drop tests:** with a dummy weight, long before it goes anywhere near the drone.
4. **Automatic triggers go live,** once the shadow-mode logs show enough flights with zero false triggers. The exact number gets picked from the Phase 4 logs.
5. **Enforce the rule:** no autonomous missions or flights above about 30 m without P fitted.

**Done when:** the chute deploys reliably, the automatic triggers are live, and the firmware enforces the rule.

### Phase 6: Module V (vision & nav)

1. **Sim first:** GPS position hold, back to start, land here, and waypoints, all on my firmware.
2. **Pick the hardware:** a Pi 5 or a Jetson, the camera, and the link (HaLow is the lead option).
3. **Build V** onto the mount, with module detection.
4. **Real flights, in order:** position hold, then the landing modes, then waypoints.
5. **Cruise endurance** at 10 m/s, now that GPS can hold the speed, checked against the cruise targets.
6. **Ground station v2:** map, mission planning, and video over HaLow. ATAK can show the same video if I want it.

**Done when:** GPS hold, every landing mode, and video on the laptop all work, and the cruise times are measured.

### Phase 7: Smart features

Each one goes sim first, then real.

1. Mapping runs (#7), processed in OpenDroneMap
2. Safe-spot detection and the "nearest safe spot" landing mode
3. Change detection (#11)
4. Wind sensing (#10) and the "turn back now" battery warning
5. Self-tuning (#21), with a profile for each module combination
6. GPS-free flight (#24)
7. The LLM mission assistant (#26): plan, checker, my approval, then flight
8. The Meshtastic relay (#30), with a range test against a ground mesh

### Phase 8: Module C (claws)

1. **Sim:** grab and release, a sudden mass change, perching.
2. **Make them:** design and print the claws.
3. **Tests, in order:** grip tests on the bench, then flying with empty claws, then grabbing 250 g, then perching.

**Done when:** it grabs and carries 250 g, and perches.

### Phase 9: Extras

Wrist gesture control (#2) first, then whatever else from the ideas pool still sounds fun.

### Phase 10: v2

If the design hunt finds something that's actually better and actually unique, it gets its own build: priced, simulated against the same targets, and flown on the same firmware. If leaving the quad layout means changing the firmware, that work is part of this phase.

## The whole way through

- Every layer exports visuals in the project's look, sized for LinkedIn and Instagram.
- Every phase gets build-log entries in [log/](../log/), and [STATUS.md](../../STATUS.md) always shows where I am.
- Studying stays in [learning.md](../learning.md), on my own time. It gets a new radio topic (link budgets, line of sight, Fresnel zones) for HaLow and Meshtastic.
- Generated meshes and STEP files don't get committed (R7). They're build outputs of the CAD code. Curated ones (the baseline, a v2 winner) go in through Git LFS, and the hero STEP goes on a GitHub Release.
- When the plan changes, the reason goes in [decisions.md](../decisions.md).

## Still open

- Prop size, cell type, and 2P vs 3P: the sizing model decides
- Cruise speed: 10 m/s until the sizing model says otherwise
- Module bus: plain serial or DroneCAN
- Which H743 board: one PX4 supports, with SWD pads
- Which OpenFOAM: decided when the CFD half of the setup script gets written
- Companion computer and camera (Phase 6)
- Where the Meshtastic relay lives (Phase 7)
- What's in the `us-recreational` profile, and whether to get Part 107 (Phase 3)
- How many clean shadow-mode flights before the automatic triggers go live (from the Phase 4 logs)
- What "unique" is allowed to mean for the design hunt

## Where it went

Confirmed on 2026-10-14, and split back into:
- `docs/roadmap.md`: the phases above
- `docs/decisions.md`: R1 to R7, the Teensy's new jobs, and the mass budget
- `design/targets.yaml` and `tests/test_targets.py`: the new targets
- `docs/specs/2026-10-13-phase-1-simulation.md`: the new Phase 1 order, the thrust stand, and what runs alongside
- `CLAUDE.md`: the safety monitor in the safety rules, and the rule about meshes
- `STATUS.md`, the README, and a log entry
