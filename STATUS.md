# Status

**Last updated:** 2026-10-20, on the PC (Windows and WSL2 Ubuntu)
**Step:** step 4 (the flight sim) is done. Step 5 (my firmware) is well along: it flies the flight sim's scenarios in Gazebo, and its safety monitor works in the sim.
**Main machine:** the PC, with WSL2 Ubuntu 24.04 for the Linux tools

## Right now

It's a research project (since 2026-10-17): the whole drone designed in simulation, every real part modeled and connected, the wiring worked out, my firmware flying it, and a build package at the end, with an honest list of what the sims can't prove. Nothing gets bought by default.

Where to look: the live plan in the [README](README.md#the-plan), the steps in the [roadmap](docs/roadmap.md), every decision in [docs/decisions.md](docs/decisions.md), and the story in [docs/log](docs/log/).

| Step | Where it is |
|---|---|
| 1. Sizing and parts | Done 2026-10-17. Emax 2814 850KV, Gemfan 1050 tri-blades, a 6S2P Molicel P45B pack, the Nazgul XL10 frame, the current capped at 90 A ([report](docs/reports/sizing/README.md)) |
| 2. CAD | Done 2026-10-18. Every part modeled, every combination passing its checks ([report](docs/reports/cad/README.md)) |
| 3. Electrical | Done 2026-10-19. 438 checks pass in all eight combinations ([report](docs/reports/electrical/README.md)) |
| 4. Flight sim (PX4) | Done 2026-10-20. 62 of 78 runs pass; the misses are three findings ([report](docs/reports/flight-sim/README.md), [log](docs/log/2026-10-20-flight-sim-final.md)) |
| 5. My firmware | In progress. Tasks 1 to 10, 12 and 13 have code and tests ([plan](docs/plans/2026-10-20-firmware.md), [log](docs/log/2026-10-20-firmware-start.md)) |
| Aero side track | The visual half: FluidX3D's cruise and crosswind pictures work; the hover's don't yet ([log](docs/log/2026-10-20-wind-tunnel-cases.md)) |
| Project site | Spec written: Vite, React, TypeScript, three.js, every sim played back as if live ([spec](docs/specs/2026-10-20-project-site.md)) |

**The design today (2026-10-20).** Mission is 2408 g in the sizing model (with the 200 g growth margin) and 2208 g in the CAD, and hovers 25.8 min (22.2 pessimistic, against the 21 target). Since step 3: the pack's insides are worked out (nickel-plated copper links, 2.3 mOhm and 43 g), the GPS sits in a printed cradle on its mast, each module locks to the rail with thumb screws into heat-set inserts, and the sizing model reads full throttle straight off the motor's table.

**Step 4's findings.** A dead motor without P is a crash (base, V, C, V+C). A GPS failure is a blind descent that ends 31 to 36 m away in C, mission, V+C and P+C, past the 30 m limit. Cruise endurance is 25% under the sizing model in every combination, because Gazebo's rotors don't gain from forward flight. The hover times agree with the sizing model to 0.1 min, and the safety monitor's triggers had no false triggers in 66 runs.

**Step 5, my firmware, so far.** C++17: a core with no hardware in it, layers for the sim, the ARK FPV and the safety monitor. It speaks PX4's MAVLink and writes PX4's log format, so the flight sim's runner flies it in PX4's place (`pcs14 flight-sim run --firmware mine`) and the same graders grade it.
- Flying: rate, self-level, altitude, position, take-off, hold, land, return and offboard, with Mahony's attitude filter, a barometer height filter and a GPS position filter.
- Passing in Gazebo: smoke, hover (1 mm of drift over 60 s), lost link, the parachute drop, a dead motor in P, the sagging pack; a failed GPS drifts 33 m, like PX4's.
- Failsafes and limits: lost link, low battery, position lost, PX4's attitude failure detector with termination and the chute, the kill switch, the limits profiles, my 30 m parachute rule, and the current cap with the XT60's heat limit (90 A for 3.1 s, then easing to 29 A, as the electrical report has it).
- The safety monitor: its own program on its own IMU, between the flight controller and the motors. Its triggers match the Python reference sample for sample, and it cut a frozen flight controller 0.26 s after it hung.
- The ARK FPV layer: the IMU driver (IIM-42653), CRSF from the receiver and DShot buffers, tested against fakes, and an image for the H743 that builds in CI.
- The ground station: `pcs14 ground` serves live telemetry, live tuning and the active limits profile on a web page.

**Offline?** Study from [docs/learning.md](docs/learning.md).

## Up next

1. **Firmware task 11:** every scenario on my firmware in all eight combinations, laid over PX4's in the report. A first pass of steps, top speed, wind, the payload grab, endurance and low battery was flying when I stopped.
2. **The firmware's remaining pieces:** the geofence, pre-arm checks that include the safety monitor, and the ARK FPV's drivers past the IMU, CRSF and DShot (the clock tree, SPI and timer DMA, the watchdog, I2C for the compass and barometer, DroneCAN, the SD card).
3. **The wind tunnel's hover pictures:** a slice through a pair of props, a longer run, a color scale for the downwash.
4. **The project site's plan,** then its build.

## Waiting on me

- **Two design decisions from step 4:** should P (the chute) be in every combination, since a dead motor without it loses the drone? Should Base get an optical flow sensor, so a GPS failure isn't a blind descent? Both add weight to a design with little margin.
- **A safety rule to confirm:** a safety monitor cut stays latched for the rest of the flight, clearing only on the ground, disarmed, with the kill switch off. That's how it's built; it's my call to confirm.
- **The FluidX3D fork:** the wind tunnel stills stay off the repo until my modified FluidX3D is public, as its license asks for any results I post.
- **Fruity Chutes:** ask for the Harrier release servo's voltage range and draw (the design runs on a stand-in, Hitec's HS-55).
- **The HaLow card (step 6):** Heltec's SPI card has no working Pi 5 report; its SDIO version (on Heltec's HT-HR01 carrier) was reported working once, and USB adapters work through an OpenWrt backport.
- **The ARM compiler on the PC,** if I want to build the H743 image locally (`sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib` in WSL). CI builds it either way.

## Still open

- Rotor drag in forward flight, so cruise numbers get believable (the honesty check's big miss, and now step 4's)
- The weight: Mission passes with 1.2 min of pessimistic hover to spare; Max is 2623 g against its own 2500 g target (report-only)
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
