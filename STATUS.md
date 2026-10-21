# Status

**Last updated:** 2026-10-20, on the PC (Windows and WSL2 Ubuntu)
**Step:** steps 4 to 6 are done (step 6 except C, the claws), and so is the project site. Step 7, the smart features, is next.
**Main machine:** the PC, with WSL2 Ubuntu 24.04 for the Linux tools

## Right now

It's a research project (since 2026-10-17): the whole drone designed in simulation, every real part modeled and connected, the wiring worked out, my firmware flying it, and a build package at the end, with an honest list of what the sims can't prove. Nothing gets bought by default.

Where to look: the live plan in the [README](README.md#the-plan), the steps in the [roadmap](docs/roadmap.md), every decision in [docs/decisions.md](docs/decisions.md), and the story in [docs/log](docs/log/). Or the project site: `pcs14 site --flights --tunnel`, then `npm --prefix site run build` and open `site/dist/index.html`.

| Step | Where it is |
|---|---|
| 1. Sizing and parts | Done 2026-10-17. Emax 2814 850KV, Gemfan 1050 tri-blades, a 6S2P Molicel P45B pack, the Nazgul XL10 frame, the current capped at 90 A ([report](docs/reports/sizing/README.md)) |
| 2. CAD | Done 2026-10-18. Every part modeled, every combination passing its checks ([report](docs/reports/cad/README.md)) |
| 3. Electrical | Done 2026-10-19. 438 checks pass in all eight combinations ([report](docs/reports/electrical/README.md)) |
| 4. Flight sim (PX4) | Done 2026-10-20. 62 of 78 runs pass; the misses are three findings ([report](docs/reports/flight-sim/README.md), [log](docs/log/2026-10-20-flight-sim-final.md)) |
| 5. My firmware | Done 2026-10-20. 66 of 78 runs pass, every one PX4 passes among them ([log](docs/log/2026-10-20-firmware-flies.md)) |
| 6. Modules in sim | Done 2026-10-20 for P and V; C waits on the claw conversation. Every P and V scenario passes ([report](docs/reports/modules/README.md), [log](docs/log/2026-10-20-modules-in-sim.md)) |
| Aero side track | The visual half done: FluidX3D's cruise, crosswind and hover, now with frames along each run. The numbers wait for OpenFOAM |
| Project site | Done 2026-10-20: the drone in 3D, the spec sheet, the wiring, every flight played back, a page per step, the tunnel, what the sims can't prove ([log](docs/log/2026-10-20-project-site.md)) |

**The design today (2026-10-20).** Mission is 2408 g in the sizing model (with the 200 g growth margin) and 2208 g in the CAD, and hovers 25.8 min (22.2 pessimistic, against the 21 target).

**Step 4's findings, and what step 5 said about them.** A dead motor without P is a crash (base, V, C, V+C), on PX4 and on mine. A GPS failure on PX4 is a blind descent that ends 22 to 36 m away; on mine it ends 4 to 6 m away, so part of that finding was PX4's estimator in this sim. Cruise endurance runs about 25% under the sizing model on both, because Gazebo's rotors don't gain from forward flight.

**Step 5, my firmware.** C++17: a core with no hardware in it, layers for the sim, the ARK FPV and the safety monitor. It speaks PX4's MAVLink and writes PX4's log format, so the flight sim's runner flies it in PX4's place and the same graders grade it. Rate, self-level, altitude, position, take-off, hold, land, return and offboard; PX4's failsafes by name; the geofence; pre-arm checks that include the safety monitor; the current cap with the XT60's heat limit; the fuel gauge. The ARK FPV's drivers go as far as host tests take them. The ground station talks to it in the sim.

**Step 6.** The safety monitor fires the chute itself now, on the pilot's switch, motors cut first, and only where P is fitted. With my flight controller frozen at 40 m in P, the monitor cut 0.29 s later, the pilot's chute went a second after the hang, and the drone settled at 4.1 m/s with 27 m to spare. Drops from 10 m up all saved, but the height the chute needs rests on its unpublished opening time: 5 m lost at 1 s, 11 m at 2 s. The opening jolt: the sim's 2 g against the textbook bound's 8 to 12 g, which the structure track designs to. HaLow's link model (Morse Micro's numbers for the chip on Heltec's card) holds 7.2 Mbps out to about 1.2 km and its slowest rate to about 5 km, 30 m up over flat ground; in the sim the ground station's link faded within 1.5% of the model, and the drone flew on. V's camera renders in Gazebo inside WSL. The companion computer stays the Pi 5.

**Offline?** Study from [docs/learning.md](docs/learning.md).

## Up next

1. **Step 7, the smart features:** the spec and plan, then the features. The wind estimate and the battery warning, the Meshtastic relay's link, self-tuning's identification and the mission checker already have their math and tests; the local model (Qwen2.5 7B through Ollama) wrote a plan from plain English that the checker passed, and the checker refused one that went over 400 ft.
2. **Step 8, the build package.**
3. **The side tracks:** the structure (beam math first, since there's no CalculiX here), OpenFOAM for the wind tunnel's numbers.

## Waiting on me

- **Two design decisions from step 4:** should P (the chute) be in every combination, since a dead motor without it loses the drone? Should Base get an optical flow sensor, so a GPS failure isn't a blind descent? Both add weight to a design with little margin. Step 5 weakened the case for optical flow in the sim (my firmware's blind descents end 4 to 6 m away, PX4's 22 to 36 m), but a real IMU drifts more than Gazebo's.
- **A safety rule to confirm:** a safety monitor cut stays latched for the rest of the flight, clearing only on the ground, disarmed, with the kill switch off. That's how it's built; it's my call to confirm. The monitor's chute release (new in step 6) latches the same way.
- **The FluidX3D fork:** the wind tunnel stills stay off the repo until my modified FluidX3D is public, as its license asks for any results I post.
- **Fruity Chutes:** ask for the Harrier release servo's voltage range and draw (the design runs on a stand-in, Hitec's HS-55), and how long the canopy takes to fill: the lowest height the chute saves the drone from rests on it.
- **The claws (C):** the roadmap holds C until a unique claw on an actual arm comes up. That conversation is mine.
- **Installs that need sudo:** OpenFOAM and CalculiX in WSL, for the aero and structure side tracks' numbers.
- **The HaLow card (step 6):** Heltec's SPI card has no working Pi 5 report; its SDIO version (on Heltec's HT-HR01 carrier) was reported working once, and USB adapters work through an OpenWrt backport.
- **The ARM compiler on the PC,** if I want to build the H743 image locally (`sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib` in WSL). CI builds it either way.

## Still open

- Rotor drag in forward flight, so cruise numbers get believable (the honesty check's big miss, and now step 4's)
- The weight: Mission passes with 1.2 min of pessimistic hover to spare; Max is 2623 g against its own 2500 g target (report-only)
- My firmware's height estimate lets about 6 cm of the barometer's noise through (its hovers hold within 0.12 to 0.25 m, against PX4's 0.06 to 0.20 m with Gazebo's noiseless GPS height)
- My firmware's current estimate comes from the thrust table (about 11% under the electrical report at Max's hover); on the drone the ESC's current sensor replaces it
- The XT60's contact mass (a 2.5 g guess): the firmware's heat limit and the burst check both rest on it
- What the motor cut board's two undocumented 1 kOhm resistors do; the design adds its own 10 kOhm pull-down and a meter check, so the board fails safe either way
- The delay between cutting the motors and firing the chute (step 6)
- Which 915 MHz antenna for HaLow, and where the Meshtastic relay (#30) lives
- Exactly what goes in the `us-recreational` profile beyond the 400 ft ceiling, and whether to get Part 107
- Cruise speed: 10 m/s until the sizing model says otherwise
- Which OpenFOAM: the Foundation release or ESI's, decided when writing its setup
- OpenGL in WSL runs on the CPU; headless flights don't care, Gazebo's window and clips will
- MAVSDK-Python 3.17.4 warns that its name now belongs to a new native binding; pinned for now

## Machines

| Machine | What it is | Role | Setup state |
|---|---|---|---|
| PC | Windows 11 + WSL2 Ubuntu 24.04 (dual boot, native Ubuntu as a fallback), Ryzen 7 9800X3D, 32 GB DDR5, RTX 3060 | Main machine: sim, CFD, CAD, renders | WSL2 with PX4 v1.17.0, Gazebo Harmonic and my firmware's build ([pc.md](docs/machines/pc.md)); FluidX3D in `C:\dr\fluidx3d`. The repo is at `C:\dr\extra-15pc-gum` |
| Laptop | Windows 11 + WSL2 Ubuntu 24.04, Core Ultra 7 155U, 16 GB, Intel graphics | Docs, light work, ground station, object detection | Checks pass ([laptop-windows.md](docs/machines/laptop-windows.md), [laptop-wsl.md](docs/machines/laptop-wsl.md)). Pushes need `env -u GH_TOKEN git push` for now |

Flight batches run one at a time at 4x, with nothing else on the PC: two at once, or anything heavy alongside, starves PX4 and spoils runs.

## Switching machines

Pull when you sit down, push when you get up. Update this file, the README's plan and the log before you push.
