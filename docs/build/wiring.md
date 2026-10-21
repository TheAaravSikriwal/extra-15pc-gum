# The wiring guide

*Generated 2026-10-21 by `pcs14 package`, from the connection list (`design/electrical.yaml`) and the CAD's wire routes. Every wire is here once, under its harness. The harness drawings and the pin tables are in the [electrical report](../reports/electrical/README.md), and the KiCad schematic beside it. Cut each wire 20 mm longer than its length here, then trim it to fit.*

Before anything: the pack is in another room, and every check below is made with a meter, unpowered. Heat shrink goes on every soldered end before it's soldered, because it can't go on after.

## Main power

The pack's XT60 lead to the ESC's battery pads, 12 AWG. The heaviest joints on the drone: tin both the pad and the wire, and use an iron that can hold its heat on a big pad.

2 wires, 0.37 m in all. The drawing: [main-power.svg](../reports/electrical/harnesses/main-power.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `lead.XT60.+` (Base's wiring and the XT60 lead) | `esc.BAT.VBAT` (Tekko32 F4 4in1 50A (AM32)) | 12 AWG | Silicone hookup wire, UL style 3135 | 183 mm |
| `lead.XT60.-` (Base's wiring and the XT60 lead) | `esc.BAT.GND` (Tekko32 F4 4in1 50A (AM32)) | 12 AWG | Silicone hookup wire, UL style 3135 | 183 mm |

Check with a meter:

- Between the XT60's two contacts: no dead short. The meter may beep for a moment as the ESC's capacitors charge, then it must stop.
- Each lead end to end: under 0.1 ohm on a meter that can read that low.
- The XT60's + to the ESC's VBAT pad, not its GND: the polarity, once more, before the smoke stopper goes on.
- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Battery taps

The small feeds off the main power: the two fuses inline, the BEC's feed and the flight controller's battery sense.

6 wires, 0.43 m in all. The drawing: [battery-taps.svg](../reports/electrical/harnesses/battery-taps.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `esc.BAT.VBAT` (Tekko32 F4 4in1 50A (AM32)) | `fuses.F1.A` (Two MINI blade fuses, soldered inline under heat shrink) | 20 AWG | Silicone hookup wire, UL style 3135 | 90 mm |
| `fuses.F1.B` (Two MINI blade fuses, soldered inline under heat shrink) | `bec.pads.IN` (BEC12S-PRO 5 V 5 A supply for the Pi) | 20 AWG | Silicone hookup wire, UL style 3135 | 48 mm |
| `esc.BAT.GND` (Tekko32 F4 4in1 50A (AM32)) | `bec.pads.G` (BEC12S-PRO 5 V 5 A supply for the Pi) | 20 AWG | Silicone hookup wire, UL style 3135 | 20 mm |
| `esc.BAT.VBAT` (Tekko32 F4 4in1 50A (AM32)) | `fuses.F2.A` (Two MINI blade fuses, soldered inline under heat shrink) | 22 AWG | Silicone hookup wire, UL style 3135 | 119 mm |
| `fuses.F2.B` (Two MINI blade fuses, soldered inline under heat shrink) | `fc.POWER_AUX.VBAT` (ARK FPV flight controller) | 26 AWG | Thin PVC hookup lead for JST plugs | 103 mm |
| `esc.BAT.GND` (Tekko32 F4 4in1 50A (AM32)) | `fc.POWER_AUX.GND` (ARK FPV flight controller) | 26 AWG | Thin PVC hookup lead for JST plugs | 49 mm |

Check with a meter:

- Through each fuse: continuity. Pull a fuse and the line it feeds goes open.
- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Motors

The motors' own leads, cut to their routes along the arms and soldered to the ESC's motor pads. Any two of a motor's three wires swapped reverses it, which the bench checks catch.

12 wires, 2.65 m in all. The drawing: [motors.svg](../reports/electrical/harnesses/motors.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `esc.MOTORS.M1A` (Tekko32 F4 4in1 50A (AM32)) | `m1.leads.A` (E3 2814 850KV) | 18 AWG | the motor's own lead | 212 mm |
| `esc.MOTORS.M1B` (Tekko32 F4 4in1 50A (AM32)) | `m1.leads.B` (E3 2814 850KV) | 18 AWG | the motor's own lead | 205 mm |
| `esc.MOTORS.M1C` (Tekko32 F4 4in1 50A (AM32)) | `m1.leads.C` (E3 2814 850KV) | 18 AWG | the motor's own lead | 212 mm |
| `esc.MOTORS.M2A` (Tekko32 F4 4in1 50A (AM32)) | `m2.leads.A` (E3 2814 850KV) | 18 AWG | the motor's own lead | 234 mm |
| `esc.MOTORS.M2B` (Tekko32 F4 4in1 50A (AM32)) | `m2.leads.B` (E3 2814 850KV) | 18 AWG | the motor's own lead | 228 mm |
| `esc.MOTORS.M2C` (Tekko32 F4 4in1 50A (AM32)) | `m2.leads.C` (E3 2814 850KV) | 18 AWG | the motor's own lead | 234 mm |
| `esc.MOTORS.M3A` (Tekko32 F4 4in1 50A (AM32)) | `m3.leads.A` (E3 2814 850KV) | 18 AWG | the motor's own lead | 212 mm |
| `esc.MOTORS.M3B` (Tekko32 F4 4in1 50A (AM32)) | `m3.leads.B` (E3 2814 850KV) | 18 AWG | the motor's own lead | 206 mm |
| `esc.MOTORS.M3C` (Tekko32 F4 4in1 50A (AM32)) | `m3.leads.C` (E3 2814 850KV) | 18 AWG | the motor's own lead | 212 mm |
| `esc.MOTORS.M4A` (Tekko32 F4 4in1 50A (AM32)) | `m4.leads.A` (E3 2814 850KV) | 18 AWG | the motor's own lead | 234 mm |
| `esc.MOTORS.M4B` (Tekko32 F4 4in1 50A (AM32)) | `m4.leads.B` (E3 2814 850KV) | 18 AWG | the motor's own lead | 228 mm |
| `esc.MOTORS.M4C` (Tekko32 F4 4in1 50A (AM32)) | `m4.leads.C` (E3 2814 850KV) | 18 AWG | the motor's own lead | 234 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Esc cable

The ESC's signal cable to the flight controller goes through the motor cut board: the ESC's side to the switch, the switch to the flight controller. This is the path the safety monitor takes over.

11 wires, 0.65 m in all. The drawing: [esc-cable.svg](../reports/electrical/harnesses/esc-cable.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `fc.ESC.CH1` (ARK FPV flight controller) | `cut.J1.NC1` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 67 mm |
| `fc.ESC.CH2` (ARK FPV flight controller) | `cut.J1.NC2` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `fc.ESC.CH3` (ARK FPV flight controller) | `cut.J1.NC3` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `fc.ESC.CH4` (ARK FPV flight controller) | `cut.J1.NC4` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 67 mm |
| `cut.J1.CM1` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | `esc.FC.M1` (Tekko32 F4 4in1 50A (AM32)) | 28 AWG | Thin PVC hookup lead for JST plugs | 56 mm |
| `cut.J1.CM2` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | `esc.FC.M2` (Tekko32 F4 4in1 50A (AM32)) | 28 AWG | Thin PVC hookup lead for JST plugs | 53 mm |
| `cut.J1.CM3` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | `esc.FC.M3` (Tekko32 F4 4in1 50A (AM32)) | 28 AWG | Thin PVC hookup lead for JST plugs | 53 mm |
| `cut.J1.CM4` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | `esc.FC.M4` (Tekko32 F4 4in1 50A (AM32)) | 28 AWG | Thin PVC hookup lead for JST plugs | 56 mm |
| `esc.FC.CURRENT` (Tekko32 F4 4in1 50A (AM32)) | `fc.ESC.CURR` (ARK FPV flight controller) | 28 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `esc.FC.TLM` (Tekko32 F4 4in1 50A (AM32)) | `fc.ESC.UART4_RX` (ARK FPV flight controller) | 28 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `esc.FC.GND` (Tekko32 F4 4in1 50A (AM32)) | `fc.ESC.GND` (ARK FPV flight controller) | 28 AWG | Thin PVC hookup lead for JST plugs | 60 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Receiver

The receiver's CRSF lines to the flight controller, with the safety monitor's tap on them.

5 wires, 0.50 m in all. The drawing: [receiver.svg](../reports/electrical/harnesses/receiver.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `fc.RC.5V` (ARK FPV flight controller) | `rx.pads.5V` (RP2 V2 ExpressLRS 2.4 GHz receiver) | 26 AWG | Thin PVC hookup lead for JST plugs | 84 mm |
| `fc.RC.GND` (ARK FPV flight controller) | `rx.pads.GND` (RP2 V2 ExpressLRS 2.4 GHz receiver) | 26 AWG | Thin PVC hookup lead for JST plugs | 87 mm |
| `rx.pads.TX` (RP2 V2 ExpressLRS 2.4 GHz receiver) | `fc.RC.USART6_RX` (ARK FPV flight controller) | 26 AWG | Thin PVC hookup lead for JST plugs | 83 mm |
| `fc.RC.USART6_TX` (ARK FPV flight controller) | `rx.pads.RX` (RP2 V2 ExpressLRS 2.4 GHz receiver) | 26 AWG | Thin PVC hookup lead for JST plugs | 85 mm |
| `rx.pads.TX` (RP2 V2 ExpressLRS 2.4 GHz receiver) | `taps.B1.A` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 26 AWG | Thin PVC hookup lead for JST plugs | 159 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Lidar

The TF-Luna's serial lead along the bottom plate to the flight controller.

4 wires, 0.70 m in all. The drawing: [lidar.svg](../reports/electrical/harnesses/lidar.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `fc.GPS.5V` (ARK FPV flight controller) | `lidar.J1.5V` (TF-Luna lidar) | 26 AWG | Thin PVC hookup lead for JST plugs | 177 mm |
| `fc.GPS.GND` (ARK FPV flight controller) | `lidar.J1.GND` (TF-Luna lidar) | 26 AWG | Thin PVC hookup lead for JST plugs | 178 mm |
| `fc.GPS.USART1_TX` (ARK FPV flight controller) | `lidar.J1.RXD` (TF-Luna lidar) | 26 AWG | Thin PVC hookup lead for JST plugs | 174 mm |
| `lidar.J1.TXD` (TF-Luna lidar) | `fc.GPS.USART1_RX` (ARK FPV flight controller) | 26 AWG | Thin PVC hookup lead for JST plugs | 173 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Safety monitor

The Teensy's feeds, its listening taps through the buffers, the cut board's control and its own supply, and the chute lines. The most wires in one place on the drone, and the ones that matter most: check each against the pin table in the electrical report before it's soldered.

35 wires, 1.89 m in all. The drawing: [safety-monitor.svg](../reports/electrical/harnesses/safety-monitor.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `fc.TELEM.5V` (ARK FPV flight controller) | `teensy_feed.D1.A1` (BAT54C dual Schottky diode (common cathode) on a SOT-23 adapter) | 26 AWG | Thin PVC hookup lead for JST plugs | 73 mm |
| `bec.pads.OUT` (BEC12S-PRO 5 V 5 A supply for the Pi) | `teensy_feed.D1.A2` (BAT54C dual Schottky diode (common cathode) on a SOT-23 adapter) | 26 AWG | Thin PVC hookup lead for JST plugs | 111 mm |
| `teensy_feed.D1.K` (BAT54C dual Schottky diode (common cathode) on a SOT-23 adapter) | `teensy.pins.VIN` (Teensy 4.1 (safety monitor)) | 26 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `fc.VTX.GND` (ARK FPV flight controller) | `teensy.pins.GND` (Teensy 4.1 (safety monitor)) | 26 AWG | Thin PVC hookup lead for JST plugs | 120 mm |
| `fc.VTX.UART5_TX` (ARK FPV flight controller) | `taps.B6.A` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 26 AWG | Thin PVC hookup lead for JST plugs | 118 mm |
| `teensy.pins.14` (Teensy 4.1 (safety monitor)) | `fc.VTX.UART5_RX` (ARK FPV flight controller) | 26 AWG | Thin PVC hookup lead for JST plugs | 129 mm |
| `taps.B1.Y` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | `teensy.pins.7` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `taps.B6.Y` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | `teensy.pins.15` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `fc.ESC.CH1` (ARK FPV flight controller) | `taps.B2.A` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 28 AWG | Thin PVC hookup lead for JST plugs | 90 mm |
| `fc.ESC.CH2` (ARK FPV flight controller) | `taps.B3.A` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 28 AWG | Thin PVC hookup lead for JST plugs | 93 mm |
| `fc.ESC.CH3` (ARK FPV flight controller) | `taps.B4.A` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 28 AWG | Thin PVC hookup lead for JST plugs | 93 mm |
| `fc.ESC.CH4` (ARK FPV flight controller) | `taps.B5.A` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 28 AWG | Thin PVC hookup lead for JST plugs | 90 mm |
| `taps.B2.Y` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | `teensy.pins.5` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `taps.B3.Y` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | `teensy.pins.6` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `taps.B4.Y` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | `teensy.pins.24` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `taps.B5.Y` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | `teensy.pins.28` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.GND` (Teensy 4.1 (safety monitor)) | `taps.B1.GND` (Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.22` (Teensy 4.1 (safety monitor)) | `cut.J1.NO1` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.23` (Teensy 4.1 (safety monitor)) | `cut.J1.NO2` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.2` (Teensy 4.1 (safety monitor)) | `cut.J1.NO3` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.4` (Teensy 4.1 (safety monitor)) | `cut.J1.NO4` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.30` (Teensy 4.1 (safety monitor)) | `cut.J1.IN` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `fc.SPI.5V` (ARK FPV flight controller) | `cut_3v3.J1.VIN` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | 28 AWG | Thin PVC hookup lead for JST plugs | 107 mm |
| `fc.SPI.GND` (ARK FPV flight controller) | `cut_3v3.J1.GND` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | 28 AWG | Thin PVC hookup lead for JST plugs | 107 mm |
| `cut_3v3.J1.VOUT` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | `cut.J1.VCC` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 15 mm |
| `cut_3v3.J1.GND` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | `cut.J1.GND` (TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 15 mm |
| `teensy.pins.3V3` (Teensy 4.1 (safety monitor)) | `imu.J1.VIN` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `teensy.pins.GND` (Teensy 4.1 (safety monitor)) | `imu.J1.GND` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `teensy.pins.13` (Teensy 4.1 (safety monitor)) | `imu.J1.SCK` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `teensy.pins.11` (Teensy 4.1 (safety monitor)) | `imu.J1.MOSI` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `imu.J1.MISO` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | `teensy.pins.12` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `teensy.pins.10` (Teensy 4.1 (safety monitor)) | `imu.J1.CS` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `imu.J1.INT1` (LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)) | `teensy.pins.40` (Teensy 4.1 (safety monitor)) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `teensy.pins.31` (Teensy 4.1 (safety monitor)) | `sockets.P_SIGNAL.TAKEOVER` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `teensy.pins.37` (Teensy 4.1 (safety monitor)) | `sockets.P_SIGNAL.CHUTE` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 30 mm |

Check with a meter:

- With the Teensy unpowered, each buffered line still reaches its flight controller pin: the monitor must never load a line it only listens to.
- The cut board's control line to the Teensy, and its pull-down to ground: about 10 kOhm. Also measure the board's two undocumented 1 kOhm resistors (the unproven list).
- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Module power

The BEC's 5 V and the pack's feed to the module sockets.

6 wires, 0.34 m in all. The drawing: [module-power.svg](../reports/electrical/harnesses/module-power.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `bec.pads.OUT` (BEC12S-PRO 5 V 5 A supply for the Pi) | `sockets.V_POWER.5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 18 AWG | Silicone hookup wire, UL style 3135 | 49 mm |
| `bec.pads.G2` (BEC12S-PRO 5 V 5 A supply for the Pi) | `sockets.V_POWER.GND` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 18 AWG | Silicone hookup wire, UL style 3135 | 49 mm |
| `bec.pads.OUT` (BEC12S-PRO 5 V 5 A supply for the Pi) | `sockets.P_POWER.5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 18 AWG | Silicone hookup wire, UL style 3135 | 88 mm |
| `bec.pads.G2` (BEC12S-PRO 5 V 5 A supply for the Pi) | `sockets.P_POWER.GND` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 18 AWG | Silicone hookup wire, UL style 3135 | 88 mm |
| `bec.pads.OUT` (BEC12S-PRO 5 V 5 A supply for the Pi) | `sockets.C_POWER.5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 18 AWG | Silicone hookup wire, UL style 3135 | 31 mm |
| `bec.pads.G2` (BEC12S-PRO 5 V 5 A supply for the Pi) | `sockets.C_POWER.GND` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 18 AWG | Silicone hookup wire, UL style 3135 | 31 mm |

Check with a meter:

- Each socket's 5 V to its GND: no short. Each socket's battery pin to GND: no short.
- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## Module bus

The CAN bus from the flight controller through V's and P's slots to C's, with a terminator at each end.

12 wires, 0.76 m in all. The drawing: [module-bus.svg](../reports/electrical/harnesses/module-bus.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `sockets.FC_CAN.CAN_P` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.V_SIGNAL.CAN_P` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 32 mm |
| `sockets.FC_CAN.CAN_N` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.V_SIGNAL.CAN_N` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 32 mm |
| `sockets.FC_CAN.5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.V_SIGNAL.CAN_5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 35 mm |
| `sockets.FC_CAN.GND` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.V_SIGNAL.GND` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 35 mm |
| `sockets.V_SIGNAL.CAN_P` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.P_SIGNAL.CAN_P` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 43 mm |
| `sockets.V_SIGNAL.CAN_N` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.P_SIGNAL.CAN_N` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 45 mm |
| `sockets.V_SIGNAL.CAN_5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.P_SIGNAL.CAN_5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 46 mm |
| `sockets.P_SIGNAL.CAN_P` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.C_SIGNAL.CAN_P` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 130 mm |
| `sockets.P_SIGNAL.CAN_N` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.C_SIGNAL.CAN_N` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 132 mm |
| `sockets.P_SIGNAL.CAN_5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `sockets.C_SIGNAL.CAN_5V` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 132 mm |
| `fc.TELEM.UART7_TX` (ARK FPV flight controller) | `sockets.V_SIGNAL.TX` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | 26 AWG | Thin PVC hookup lead for JST plugs | 50 mm |
| `sockets.V_SIGNAL.RX` (Module sockets, three slots (an XT30U and an 8-pin JST-GH each)) | `fc.TELEM.UART7_RX` (ARK FPV flight controller) | 26 AWG | Thin PVC hookup lead for JST plugs | 50 mm |

Check with a meter:

- CAN_H to CAN_L across the whole bus, nothing plugged in: about 60 ohm, the two terminators in parallel.
- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## V

V's own wiring, inside its housing.

8 wires, 0.83 m in all. The drawing: [v.svg](../reports/electrical/harnesses/v.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `vplug.POWER.5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `pi.GPIO.5V` (Raspberry Pi 5 (4 GB) companion computer) | 20 AWG | Silicone hookup wire, UL style 3135 | 40 mm |
| `vplug.POWER.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `pi.GPIO.GND` (Raspberry Pi 5 (4 GB) companion computer) | 20 AWG | Silicone hookup wire, UL style 3135 | 40 mm |
| `vplug.SIGNAL.TX` (Module plug (an XT30U and an 8-pin JST-GH)) | `pi.GPIO.GPIO15` (Raspberry Pi 5 (4 GB) companion computer) | 26 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `pi.GPIO.GPIO14` (Raspberry Pi 5 (4 GB) companion computer) | `vplug.SIGNAL.RX` (Module plug (an XT30U and an 8-pin JST-GH)) | 26 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `vplug.SIGNAL.CAN_P` (Module plug (an XT30U and an 8-pin JST-GH)) | `gps.CAN1.CAN_P` (ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer)) | 26 AWG | Thin PVC hookup lead for JST plugs | 165 mm |
| `vplug.SIGNAL.CAN_N` (Module plug (an XT30U and an 8-pin JST-GH)) | `gps.CAN1.CAN_N` (ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer)) | 26 AWG | Thin PVC hookup lead for JST plugs | 165 mm |
| `vplug.SIGNAL.CAN_5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `gps.CAN1.5V` (ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer)) | 26 AWG | Thin PVC hookup lead for JST plugs | 168 mm |
| `vplug.SIGNAL.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `gps.CAN1.GND` (ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer)) | 26 AWG | Thin PVC hookup lead for JST plugs | 168 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## P

P's own wiring: the CANnode, the chute switch, the servo's feed through the ideal-diode board.

17 wires, 0.67 m in all. The drawing: [p.svg](../reports/electrical/harnesses/p.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `pplug.POWER.5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_diodes.pads.VIN1` (LM66200 Ideal Dual Diodes Breakout) | 22 AWG | Silicone hookup wire, UL style 3135 | 40 mm |
| `pplug.SIGNAL.CAN_5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_diodes.pads.VIN2` (LM66200 Ideal Dual Diodes Breakout) | 26 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `p_diodes.pads.VOUT` (LM66200 Ideal Dual Diodes Breakout) | `chute.servo.V+` (Harrier 40-42 parachute bundle) | 22 AWG | Silicone hookup wire, UL style 3135 | 68 mm |
| `pplug.POWER.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_diodes.pads.GND` (LM66200 Ideal Dual Diodes Breakout) | 28 AWG | Thin PVC hookup lead for JST plugs | 20 mm |
| `pplug.POWER.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `chute.servo.GND` (Harrier 40-42 parachute bundle) | 22 AWG | Silicone hookup wire, UL style 3135 | 29 mm |
| `p_diodes.pads.VOUT` (LM66200 Ideal Dual Diodes Breakout) | `p_3v3.J1.VIN` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | 28 AWG | Thin PVC hookup lead for JST plugs | 20 mm |
| `pplug.POWER.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_3v3.J1.GND` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | 28 AWG | Thin PVC hookup lead for JST plugs | 30 mm |
| `p_3v3.J1.VOUT` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | `p_switch.U1.VCC` (74LVC1G157 two-input multiplexer on a SOT-23-6 adapter) | 28 AWG | Thin PVC hookup lead for JST plugs | 15 mm |
| `p_3v3.J1.GND` (D36V6F3 3.3 V 600 mA step-down regulator (item 3791)) | `p_switch.U1.GND` (74LVC1G157 two-input multiplexer on a SOT-23-6 adapter) | 28 AWG | Thin PVC hookup lead for JST plugs | 15 mm |
| `pplug.SIGNAL.CAN_P` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_node.CAN1.CAN_P` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 50 mm |
| `pplug.SIGNAL.CAN_N` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_node.CAN1.CAN_N` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 50 mm |
| `pplug.SIGNAL.CAN_5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_node.CAN1.5V` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 50 mm |
| `pplug.SIGNAL.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_node.CAN1.GND` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 50 mm |
| `p_node.PWM.PWM1` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | `p_switch.U1.I0` (74LVC1G157 two-input multiplexer on a SOT-23-6 adapter) | 28 AWG | Thin PVC hookup lead for JST plugs | 50 mm |
| `pplug.SIGNAL.CHUTE` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_switch.U1.I1` (74LVC1G157 two-input multiplexer on a SOT-23-6 adapter) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `pplug.SIGNAL.TAKEOVER` (Module plug (an XT30U and an 8-pin JST-GH)) | `p_switch.U1.S` (74LVC1G157 two-input multiplexer on a SOT-23-6 adapter) | 28 AWG | Thin PVC hookup lead for JST plugs | 40 mm |
| `p_switch.U1.Y` (74LVC1G157 two-input multiplexer on a SOT-23-6 adapter) | `chute.servo.SIG` (Harrier 40-42 parachute bundle) | 28 AWG | Thin PVC hookup lead for JST plugs | 66 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.

## C

C's own wiring, to the placeholder claws.

10 wires, 0.54 m in all. The drawing: [c.svg](../reports/electrical/harnesses/c.svg).

| From | To | Gauge | Wire | Length |
|---|---|---|---|---|
| `cplug.POWER.5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `claws.servo1.V+` (Claws and servos (placeholder)) | 20 AWG | Silicone hookup wire, UL style 3135 | 40 mm |
| `cplug.POWER.5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `claws.servo2.V+` (Claws and servos (placeholder)) | 20 AWG | Silicone hookup wire, UL style 3135 | 66 mm |
| `cplug.POWER.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `claws.servo1.GND` (Claws and servos (placeholder)) | 20 AWG | Silicone hookup wire, UL style 3135 | 40 mm |
| `cplug.POWER.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `claws.servo2.GND` (Claws and servos (placeholder)) | 20 AWG | Silicone hookup wire, UL style 3135 | 68 mm |
| `cplug.SIGNAL.CAN_P` (Module plug (an XT30U and an 8-pin JST-GH)) | `c_node.CAN1.CAN_P` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `cplug.SIGNAL.CAN_N` (Module plug (an XT30U and an 8-pin JST-GH)) | `c_node.CAN1.CAN_N` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `cplug.SIGNAL.CAN_5V` (Module plug (an XT30U and an 8-pin JST-GH)) | `c_node.CAN1.5V` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `cplug.SIGNAL.GND` (Module plug (an XT30U and an 8-pin JST-GH)) | `c_node.CAN1.GND` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | 26 AWG | Thin PVC hookup lead for JST plugs | 60 mm |
| `c_node.PWM.PWM1` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | `claws.servo1.SIG` (Claws and servos (placeholder)) | 28 AWG | Thin PVC hookup lead for JST plugs | 29 mm |
| `c_node.PWM.PWM2` (ARK CANnode (DroneCAN node with 8 PWM outputs)) | `claws.servo2.SIG` (Claws and servos (placeholder)) | 28 AWG | Thin PVC hookup lead for JST plugs | 55 mm |

Check with a meter:

- Every wire end to end: continuity.
- Every pin of every plug against its neighbors: no shorts.
- Each plug's pin 1 against the board's pinout, before it goes in.
