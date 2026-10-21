# The firmware

*Generated 2026-10-21 by `pcs14 package`. PX4 flies first: the ARK FPV runs it out of the box, the flight sim tuned it for this drone, and nothing of mine has flown a real motor yet.*

## 1. PX4 on the ARK FPV

PX4 v1.17.0, the version the flight sim flies. The ARK FPV is in PX4's tree as `boards/ark/fpv`, so the build target is `ark_fpv_default`:

```bash
git clone --branch v1.17.0 --recursive https://github.com/PX4/PX4-Autopilot.git
```

```bash
make -C PX4-Autopilot ark_fpv_default upload
```

Or load the same release from QGroundControl's firmware page. Then, in QGroundControl:

- the airframe: Generic Quadcopter (4001), then this combination's parameters below, pasted into the MAVLink console, and a reboot;
- the Actuators page: motors 1 to 4 on the ESC's outputs, DShot600, and each motor's direction checked with the props off (motor 1 front right, 2 back left, 3 front left, 4 back right, PX4's quad X);
- the sensors' calibration (the compass on the GPS mast, the accelerometer, the level), the radio, and the flight modes, with the kill switch on its own switch;
- the battery: 6 cells, 9000 mAh. PX4's battery defaults are for LiPo; these are Li-ion cells, Molicel INR-21700-P45B, which go down to 2.5 V a cell, so set the empty voltage near 3.0 V a cell and check the percentage against a real discharge before trusting it.

The parameters, one file a combination (the flight sim's, less its simulator's own):

- [px4-pcs14_base.txt](firmware/px4-pcs14_base.txt)
- [px4-pcs14_c.txt](firmware/px4-pcs14_c.txt)
- [px4-pcs14_max.txt](firmware/px4-pcs14_max.txt)
- [px4-pcs14_mission.txt](firmware/px4-pcs14_mission.txt)
- [px4-pcs14_p.txt](firmware/px4-pcs14_p.txt)
- [px4-pcs14_p_c.txt](firmware/px4-pcs14_p_c.txt)
- [px4-pcs14_v.txt](firmware/px4-pcs14_v.txt)
- [px4-pcs14_v_c.txt](firmware/px4-pcs14_v_c.txt)

## 2. My firmware

C++17, in `firmware/`. The core and every driver's logic build and test on any machine:

```bash
cmake -S firmware -B build/firmware
```

```bash
cmake --build build/firmware
```

```bash
ctest --test-dir build/firmware
```

The ARK FPV's image needs the ARM compiler (in WSL: `sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib`), and CI builds it on every push:

```bash
cmake -S firmware -B build/h743 -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=firmware/cmake/arm-none-eabi.cmake
```

```bash
cmake --build build/h743 --target pcs14_h743
```

**It isn't ready to fly.** The image builds, but its register-level drivers (the IMU's SPI, the DShot timers, the SD card's SDMMC) have only run against the host tests, never on a board. They wait for a bench ARK FPV, props off, checked one at a time against PX4 on the same board. Each combination's airframe file, which my firmware reads for its mass, inertia, rotors and motors, is in `firmware/` beside PX4's parameters. Self-tuning (step 7) found the inertia within 0.3% in the sim; on the drone it runs from a log of three stick doublets, on the ground.

## 3. The safety monitor

The Teensy 4.1's core logic is in `firmware/monitor/`, tested on the host and flown in the sim beside my firmware. **Its image for the Teensy isn't built yet:** that needs PJRC's Teensy core for the i.MX RT1062 (or a startup of my own), which is a download I haven't made. Until it's built and has passed its bench tests, the safety monitor isn't on the drone, and the kill switch works through the flight controller alone. The first flights are PX4's, tethered, with that in mind.
