# Sizing report

*Generated on 2026-10-19 by pcs14 0.1.0, the sizing model in `src/pcs14/sizing/`. Numbers shown as A / B are the published data / the pessimistic version. Rounding always goes toward failing.*

## The verdict

**Marginal.** Every required setup (base, V, P, mission) meets every target on the published numbers, but one check only makes it on the optimistic end: hover time for mission.

The motors and battery are sized for **mission**, carrying an extra 200 g of growth margin. Setups marked optional get checked and reported, but don't have to pass.

![Flight time, every setup](charts/flight-times.png)

## The build

| Part | Pick | Mass | Numbers from |
|---|---|---|---|
| Motors (4) | Emax E3 2814 850KV | 82 g each | [manufacturer](https://emaxmodel.com/motor-detail-dark.html?motor=e3-2814) |
| Props (4) | Gemfan 1050 3-blade (10 x 5 in, 3 blades) | 17 g each | [manufacturer](https://www.gemfanhobby.com/1050-cinelifter-glass-fiber-nylon-3-blade.html) |
| Thrust table | 25 V, 8 rows | | [manufacturer](https://emaxmodel.com/motor-detail-dark.html?motor=e3-2814) |
| Pack | 6S2P Molicel INR-21700-P42A: 8062 mAh, 52 milliohms, 90 A continuous | 858 g | [manufacturer](https://www.molicel.com/wp-content/uploads/INR21700P42A_1.7_Product-Data-Sheet-of-INR-21700-P42A-80092.pdf) |
| ESC | Holybro Tekko32 F4 4in1 50A (AM32) | 14 g | [manufacturer](https://holybro.com/products/tekko32-f4-4in1-50a-esc) |
| Frame | iFlight Nazgul XL10 V6 10-inch frame | 343 g | [manufacturer](https://shop.iflight.com/xl10-v6-10-inch-fpv-frame-Pro1967) |
| Current cap | 90 A, set in my firmware (100% of the pack's rating) | | |

## Every setup

| Setup | Modules | Required | Weight | Hover | Cruise at 10 m/s | Thrust-to-weight at the reserve | Verdict |
|---|---|---|---|---|---|---|---|
| base | none | yes | 1806 g | 37.2 / 31.7 min | 50.1 / 42.9 min | 3.43 / 3.09:1 | pass |
| V | V | yes | 1967 g | 31.3 / 26.8 min | 40.5 / 34.9 min | 3.15 / 2.84:1 | pass |
| P | P | yes | 1979 g | 32.3 / 27.5 min | 42.7 / 36.6 min | 3.13 / 2.82:1 | pass |
| C | C | optional | 2215 g | 27.0 / 23.1 min | 35.2 / 30.2 min | 2.80 / 2.52:1 | pass |
| mission | V+P | yes | 2340 g (with 200 g margin) | 24.2 / 20.9 min | 30.7 / 26.6 min | 2.65 / 2.38:1 | marginal |
| V+C | V+C | optional | 2376 g | 23.6 / 20.3 min | 29.7 / 25.8 min | 2.61 / 2.35:1 | pass |
| P+C | P+C | optional | 2388 g | 24.1 / 20.7 min | 30.9 / 26.7 min | 2.59 / 2.33:1 | pass |
| max | V+P+C | optional | 2549 g | 21.3 / 18.4 min | 26.6 / 23.1 min | 2.43 / 2.19:1 | fail |

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 37.2 / 31.7 min | at least 25.0 min | +49% | pass |
| Cruise time at 10 m/s | 50.1 / 42.9 min | at least 30.0 min | +67% | pass |
| Thrust-to-weight at the reserve | 3.43 / 3.09:1 | at least 2.00:1 | +72% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 12.1 m/s, for 51.2 min of cruise.
- Top speed: 121 km/h on a full pack, 117 at half charge, 115 at the reserve.

</details>

<details>
<summary>V: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 31.3 / 26.8 min | at least 21.0 min | +49% | pass |
| Cruise time at 10 m/s | 40.5 / 34.9 min | at least 25.0 min | +62% | pass |
| Thrust-to-weight at the reserve | 3.15 / 2.84:1 | at least 2.00:1 | +58% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 105 / 102 km/h | at least 80 km/h | +31% | pass |
| Holds position in 10 m/s wind | 3.05 / 2.74x | at least 1.30x | +135% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.5 m/s, for 40.9 min of cruise.
- Top speed: 108 km/h on a full pack, 105 at half charge, 103 at the reserve.

</details>

<details>
<summary>P: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 32.3 / 27.5 min | at least 21.0 min | +54% | pass |
| Cruise time at 10 m/s | 42.7 / 36.6 min | at least 25.0 min | +71% | pass |
| Thrust-to-weight at the reserve | 3.13 / 2.82:1 | at least 2.00:1 | +57% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 112 / 110 km/h | at least 80 km/h | +40% | pass |
| Holds position in 10 m/s wind | 3.05 / 2.74x | at least 1.30x | +135% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 12.1 m/s, for 43.6 min of cruise.
- Top speed: 116 km/h on a full pack, 112 at half charge, 110 at the reserve.

</details>

<details>
<summary>C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 27.0 / 23.1 min | at least 17.0 min | +59% | pass |
| Cruise time at 10 m/s | 35.2 / 30.2 min | at least 20.0 min | +76% | pass |
| Thrust-to-weight at the reserve | 2.80 / 2.52:1 | at least 2.00:1 | +40% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2215 g | at most 2500 g | +11% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 12.5 m/s, for 36.2 min of cruise.
- Top speed: 114 km/h on a full pack, 111 at half charge, 108 at the reserve.

</details>

<details>
<summary>mission: marginal</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 24.2 / 20.9 min | at least 21.0 min | +16% | marginal |
| Cruise time at 10 m/s | 30.7 / 26.6 min | at least 25.0 min | +23% | pass |
| Thrust-to-weight at the reserve | 2.65 / 2.38:1 | at least 2.00:1 | +33% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 102 / 100 km/h | at least 80 km/h | +29% | pass |
| Holds position in 10 m/s wind | 2.57 / 2.31x | at least 1.30x | +98% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 12.1 m/s, for 31.3 min of cruise.
- Top speed: 107 km/h on a full pack, 103 at half charge, 100 at the reserve.

</details>

<details>
<summary>V+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 23.6 / 20.3 min | at least 17.0 min | +39% | pass |
| Cruise time at 10 m/s | 29.7 / 25.8 min | at least 20.0 min | +49% | pass |
| Thrust-to-weight at the reserve | 2.61 / 2.35:1 | at least 2.00:1 | +31% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2376 g | at most 2500 g | +5% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 11.9 m/s, for 30.2 min of cruise.
- Top speed: 104 km/h on a full pack, 101 at half charge, 98 at the reserve.

</details>

<details>
<summary>P+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 24.1 / 20.7 min | at least 17.0 min | +42% | pass |
| Cruise time at 10 m/s | 30.9 / 26.7 min | at least 20.0 min | +55% | pass |
| Thrust-to-weight at the reserve | 2.59 / 2.33:1 | at least 2.00:1 | +30% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2389 g | at most 2500 g | +4% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 12.5 m/s, for 31.8 min of cruise.
- Top speed: 110 km/h on a full pack, 106 at half charge, 103 at the reserve.

</details>

<details>
<summary>max: fail</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 21.3 / 18.4 min | at least 17.0 min | +26% | pass |
| Cruise time at 10 m/s | 26.6 / 23.1 min | at least 20.0 min | +33% | pass |
| Thrust-to-weight at the reserve | 2.43 / 2.19:1 | at least 2.00:1 | +22% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2550 g | at most 2500 g | -2% | fail |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 12.0 m/s, for 27.1 min of cruise.
- Top speed: 102 km/h on a full pack, 98 at half charge, 95 at the reserve.

</details>

## Mass budget: mission

| Line | Mass |
|---|---|
| Frame: iFlight Nazgul XL10 V6 10-inch frame | 343 g |
| 4 motors: Emax E3 2814 850KV | 328 g |
| 4 props: Gemfan 1050 3-blade | 67 g |
| ESC: Holybro Tekko32 F4 4in1 50A (AM32) | 14 g |
| Pack: 6S2P Molicel INR-21700-P42A | 858 g |
| ARK FPV flight controller | 8 g |
| RP2 V2 ExpressLRS 2.4 GHz receiver | 1 g |
| TF-Luna lidar | 5 g |
| Teensy 4.1 (safety monitor) | 15 g |
| LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438) | 2 g |
| TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout | 1 g |
| Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717) | 1 g |
| BAT54C dual Schottky diode (common cathode) on a SOT-23 adapter | 0 g |
| D36V6F3 3.3 V 600 mA step-down regulator (item 3791) | 0 g |
| R111 Remote ID broadcast module | 14 g |
| Base's wiring and the XT60 lead | 60 g |
| Module mount and connector | 12 g |
| BEC12S-PRO 5 V 5 A supply for the Pi | 5 g |
| Module sockets, three slots (an XT30U and an 8-pin JST-GH each) | 4 g |
| Two MINI blade fuses in inline holders | 7 g |
| Landing legs | 26 g |
| Battery tray | 29 g |
| Lidar bracket | 2 g |
| Remote id mount | 1 g |
| Safety monitor carrier | 3 g |
| ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer) | 16 g |
| Folding GPS mast | 5 g |
| Camera Module 3 | 4 g |
| Raspberry Pi 5 (4 GB) companion computer | 46 g |
| Active cooler for the Pi 5 | 15 g |
| HT-HC01P Wi-Fi HaLow card with Pi HAT | 15 g |
| Module V housing and mounts | 40 g |
| Camera cable, Standard-Mini, 200 mm | 2 g |
| 915 MHz dipole antenna with an IPEX pigtail (placeholder) | 12 g |
| Camera bracket | 2 g |
| Module plug (an XT30U and an 8-pin JST-GH) | 1 g |
| Module V's wiring | 2 g |
| Harrier 40-42 parachute bundle | 154 g |
| Module P mount | 8 g |
| ARK CANnode (DroneCAN node with 8 PWM outputs) | 5 g |
| 74LVC1G157 two-input multiplexer on a SOT-23-6 adapter | 0 g |
| D36V6F3 3.3 V 600 mA step-down regulator (item 3791) | 0 g |
| Two 1N5817 Schottky diodes (DO-41, soldered inline) | 1 g |
| Module plug (an XT30U and an 8-pin JST-GH) | 1 g |
| Module P's wiring | 3 g |
| Growth margin | 200 g |
| **Total** | **2340 g** |

## One flight, start to reserve

![One flight, start to reserve](charts/battery.png)

## Power and speed

![Power against airspeed](charts/power.png)

The cruise targets are checked at 10 m/s for now. The speed that actually costs mission the least is 12.1 m/s, where it cruises for 31.3 min.

## The sweep

192 builds tried, ranked by verdict, then by how far their tightest required check clears its limit. The build in this report ranks #58 of 192.

![Every build the sweep tried](charts/sweep.png)

| Rank | Build | Frame | Verdict | Tightest margin | mission cruise |
|---|---|---|---|---|---|
| 1 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +45% | 38.4 min |
| 2 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +44% | 41.2 min |
| 3 | XRotor 3115 900KV / MacroQuad 10x4.5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +35% | 35.2 min |
| 4 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Samsung SDI INR21700-40T | Nazgul XL10 V6 10-inch frame | pass | +33% | 36.9 min |
| 5 | E3 2814 850KV / 1050 3-blade / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +31% | 36.9 min |
| 6 | E3 2814 850KV / 1050 3-blade / 6S3P Samsung SDI INR21700-40T | Nazgul XL10 V6 10-inch frame | pass | +31% | 35.6 min |
| 7 | XRotor 3115 900KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +31% | 34.5 min |
| 8 | XRotor 3115 900KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P45B | Chimera9 ECO 9-inch frame | pass | +29% | 33.9 min |
| 9 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S2P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +29% | 34.5 min |
| 10 | E3 3115 900KV / 1050 3-blade / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +29% | 33.6 min |
| 58 | **E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P42A** | Nazgul XL10 V6 10-inch frame | marginal | +16% | 30.7 min |

## What extra weight costs

![What extra weight costs](charts/margin.png)

Cruise minutes as extra grams go on:

| Setup | +0 g | +100 g | +200 g | +300 g | +400 g | +500 g | +600 g |
|---|---|---|---|---|---|---|---|
| base | 50.1 | 46.0 | 42.3 | 39.1 | 36.2 | 33.7 | 31.4 |
| V | 40.5 | 37.5 | 34.9 | 32.6 | 30.5 | 28.6 | 27.0 |
| P | 42.7 | 39.5 | 36.6 | 34.0 | 31.7 | 29.7 | 28.0 |
| mission | 35.2 | 32.9 | 30.7 | 28.9 | 27.2 | 25.7 | 24.3 |

## How the numbers are made

- **Hover** power comes straight from the thrust table (volts x amps at the table's voltage). The battery model turns it into current with the pack's sag included.
- **Forward flight** splits each prop's power into lifting power, blade drag and the power to push the drone through the air, fitted to the hover table. Real rotors need 15% more lifting power than ideal theory, and blade drag takes 25% of a small prop's hover power.
- **The battery** is each cell's resting-voltage curve plus its internal resistance, scaled to the pack plus the wiring, stepped through the flight a few seconds at a time.
- **Pessimistic data** cuts every thrust in the table: thrust stand 2%, independent test 5%, manufacturer 10%, estimate 15%, made up 10%.
- **Holding position in wind** means flying at that airspeed at the 20% reserve with 30% more thrust available than needed. **Top speed** is checked at 50% charge, and the drone won't lean past 45 degrees.

## What this can't tell you

- Manufacturer thrust data runs optimistic. The pessimistic numbers allow for that, but only a thrust stand can say by how much.
- Cruise is the shakiest number here. The honesty check ([validation.md](validation.md)) flew a published long-range build through the model, and its cruise time came out much longer than the measured one, most likely because the drag of the props at speed isn't modeled yet. Trust the hover numbers more than the cruise ones for now.
- Drag is a guess from frontal area until the wind tunnel side track has real numbers.
- Coming straight down fast (the vortex ring state), cold weather and aging cells aren't modeled.
- The ESC's limits, wiring losses and heat get checked in the electrical step.
