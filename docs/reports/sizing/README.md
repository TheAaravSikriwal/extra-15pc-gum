# Sizing report

*Generated on 2026-10-20 by pcs14 0.1.0, the sizing model in `src/pcs14/sizing/`. Numbers shown as A / B are the published data / the pessimistic version. Rounding always goes toward failing.*

## The verdict

**Pass.** Every required setup (base, V, P, mission) meets every target, even with pessimistic data.

The motors and battery are sized for **mission**, carrying an extra 200 g of growth margin. Setups marked optional get checked and reported, but don't have to pass.

![Flight time, every setup](charts/flight-times.png)

## The build

| Part | Pick | Mass | Numbers from |
|---|---|---|---|
| Motors (4) | Emax E3 2814 850KV | 82 g each | [manufacturer](https://emaxmodel.com/motor-detail-dark.html?motor=e3-2814) |
| Props (4) | Gemfan 1050 3-blade (10 x 5 in, 3 blades) | 17 g each | [manufacturer](https://www.gemfanhobby.com/1050-cinelifter-glass-fiber-nylon-3-blade.html) |
| Thrust table | 25 V, 8 rows | | [manufacturer](https://emaxmodel.com/motor-detail-dark.html?motor=e3-2814) |
| Pack | 6S2P Molicel INR-21700-P45B: 9000 mAh, 51 milliohms, 90 A continuous | 883 g | [manufacturer](https://www.molicel.com/wp-content/uploads/INR21700P45B_1.4_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf) |
| ESC | Holybro Tekko32 F4 4in1 50A (AM32) | 14 g | [manufacturer](https://holybro.com/products/tekko32-f4-4in1-50a-esc) |
| Frame | iFlight Nazgul XL10 V6 10-inch frame | 343 g | [manufacturer](https://shop.iflight.com/xl10-v6-10-inch-fpv-frame-Pro1967) |
| Current cap | 90 A, set in my firmware (100% of the pack's rating) | | |

## Every setup

| Setup | Modules | Required | Weight | Hover | Cruise at 10 m/s | Thrust-to-weight at the reserve | Verdict |
|---|---|---|---|---|---|---|---|
| base | none | yes | 1860 g | 39.4 / 33.6 min | 53.0 / 45.4 min | 3.44 / 3.10:1 | pass |
| V | V | yes | 2032 g | 33.1 / 28.3 min | 42.7 / 36.8 min | 3.15 / 2.84:1 | pass |
| P | P | yes | 2036 g | 34.3 / 29.2 min | 45.2 / 38.7 min | 3.15 / 2.83:1 | pass |
| C | C | optional | 2272 g | 28.9 / 24.7 min | 37.4 / 32.2 min | 2.82 / 2.54:1 | pass |
| mission | V+P | yes | 2408 g (with 200 g margin) | 25.8 / 22.2 min | 32.6 / 28.3 min | 2.66 / 2.39:1 | pass |
| V+C | V+C | optional | 2444 g | 25.1 / 21.7 min | 31.6 / 27.4 min | 2.62 / 2.36:1 | pass |
| P+C | P+C | optional | 2448 g | 25.8 / 22.2 min | 33.0 / 28.5 min | 2.62 / 2.35:1 | pass |
| max | V+P+C | optional | 2620 g | 22.8 / 19.7 min | 28.3 / 24.6 min | 2.44 / 2.20:1 | fail |

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 39.4 / 33.6 min | at least 25.0 min | +58% | pass |
| Cruise time at 10 m/s | 53.0 / 45.4 min | at least 30.0 min | +77% | pass |
| Thrust-to-weight at the reserve | 3.44 / 3.10:1 | at least 2.00:1 | +72% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Cheapest speed: 12.3 m/s, for 54.3 min of cruise.
- Top speed: 125 km/h on a full pack, 121 at half charge, 118 at the reserve.

</details>

<details>
<summary>V: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 33.1 / 28.3 min | at least 21.0 min | +58% | pass |
| Cruise time at 10 m/s | 42.7 / 36.8 min | at least 25.0 min | +71% | pass |
| Thrust-to-weight at the reserve | 3.15 / 2.84:1 | at least 2.00:1 | +58% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 108 / 106 km/h | at least 80 km/h | +35% | pass |
| Holds position in 10 m/s wind | 3.06 / 2.75x | at least 1.30x | +136% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.6 m/s, for 43.3 min of cruise.
- Top speed: 112 km/h on a full pack, 108 at half charge, 105 at the reserve.

</details>

<details>
<summary>P: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 34.3 / 29.2 min | at least 21.0 min | +63% | pass |
| Cruise time at 10 m/s | 45.2 / 38.7 min | at least 25.0 min | +81% | pass |
| Thrust-to-weight at the reserve | 3.15 / 2.83:1 | at least 2.00:1 | +58% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 115 / 113 km/h | at least 80 km/h | +45% | pass |
| Holds position in 10 m/s wind | 3.07 / 2.76x | at least 1.30x | +136% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 12.3 m/s, for 46.4 min of cruise.
- Top speed: 120 km/h on a full pack, 116 at half charge, 112 at the reserve.

</details>

<details>
<summary>C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 28.9 / 24.7 min | at least 17.0 min | +70% | pass |
| Cruise time at 10 m/s | 37.4 / 32.2 min | at least 20.0 min | +87% | pass |
| Thrust-to-weight at the reserve | 2.82 / 2.54:1 | at least 2.00:1 | +41% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2272 g | at most 2500 g | +9% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Cheapest speed: 12.6 m/s, for 38.6 min of cruise.
- Top speed: 118 km/h on a full pack, 114 at half charge, 110 at the reserve.

</details>

<details>
<summary>mission: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 25.8 / 22.2 min | at least 21.0 min | +23% | pass |
| Cruise time at 10 m/s | 32.6 / 28.3 min | at least 25.0 min | +31% | pass |
| Thrust-to-weight at the reserve | 2.66 / 2.39:1 | at least 2.00:1 | +33% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 106 / 103 km/h | at least 80 km/h | +33% | pass |
| Holds position in 10 m/s wind | 2.58 / 2.32x | at least 1.30x | +99% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 12.2 m/s, for 33.4 min of cruise.
- Top speed: 110 km/h on a full pack, 106 at half charge, 103 at the reserve.

</details>

<details>
<summary>V+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 25.1 / 21.7 min | at least 17.0 min | +48% | pass |
| Cruise time at 10 m/s | 31.6 / 27.4 min | at least 20.0 min | +58% | pass |
| Thrust-to-weight at the reserve | 2.62 / 2.36:1 | at least 2.00:1 | +31% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2444 g | at most 2500 g | +2% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Cheapest speed: 12.1 m/s, for 32.2 min of cruise.
- Top speed: 108 km/h on a full pack, 104 at half charge, 100 at the reserve.

</details>

<details>
<summary>P+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 25.8 / 22.2 min | at least 17.0 min | +52% | pass |
| Cruise time at 10 m/s | 33.0 / 28.5 min | at least 20.0 min | +65% | pass |
| Thrust-to-weight at the reserve | 2.62 / 2.35:1 | at least 2.00:1 | +31% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2449 g | at most 2500 g | +2% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Cheapest speed: 12.6 m/s, for 34.0 min of cruise.
- Top speed: 114 km/h on a full pack, 110 at half charge, 106 at the reserve.

</details>

<details>
<summary>max: fail</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 22.8 / 19.7 min | at least 17.0 min | +34% | pass |
| Cruise time at 10 m/s | 28.3 / 24.6 min | at least 20.0 min | +42% | pass |
| Thrust-to-weight at the reserve | 2.44 / 2.20:1 | at least 2.00:1 | +22% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2621 g | at most 2500 g | -5% | fail |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 128 A
- Cheapest speed: 12.1 m/s, for 28.9 min of cruise.
- Top speed: 105 km/h on a full pack, 101 at half charge, 98 at the reserve.

</details>

## Mass budget: mission

| Line | Mass |
|---|---|
| Frame: iFlight Nazgul XL10 V6 10-inch frame | 343 g |
| 4 motors: Emax E3 2814 850KV | 328 g |
| 4 props: Gemfan 1050 3-blade | 67 g |
| ESC: Holybro Tekko32 F4 4in1 50A (AM32) | 14 g |
| Pack: 6S2P Molicel INR-21700-P45B | 883 g |
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
| Two MINI blade fuses, soldered inline under heat shrink | 2 g |
| Landing legs | 26 g |
| Battery tray | 29 g |
| Lidar bracket | 2 g |
| Remote id mount | 1 g |
| Safety monitor carrier | 3 g |
| Base's screws, nuts and spacers | 34 g |
| ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer) | 16 g |
| Folding GPS mast | 12 g |
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
| Module V's screws, nuts and spacers | 4 g |
| Harrier 40-42 parachute bundle | 154 g |
| Module P mount | 8 g |
| ARK CANnode (DroneCAN node with 8 PWM outputs) | 5 g |
| 74LVC1G157 two-input multiplexer on a SOT-23-6 adapter | 0 g |
| D36V6F3 3.3 V 600 mA step-down regulator (item 3791) | 0 g |
| LM66200 Ideal Dual Diodes Breakout | 0 g |
| Module plug (an XT30U and an 8-pin JST-GH) | 1 g |
| Module P's wiring | 3 g |
| Module P's screws, nuts and spacers | 4 g |
| Growth margin | 200 g |
| **Total** | **2408 g** |

## One flight, start to reserve

![One flight, start to reserve](charts/battery.png)

## Power and speed

![Power against airspeed](charts/power.png)

The cruise targets are checked at 10 m/s for now. The speed that actually costs mission the least is 12.2 m/s, where it cruises for 33.4 min.

## The sweep

192 builds tried, ranked by verdict, then by how far their tightest required check clears its limit. The build in this report ranks #14 of 192.

![Every build the sweep tried](charts/sweep.png)

| Rank | Build | Frame | Verdict | Tightest margin | mission cruise |
|---|---|---|---|---|---|
| 1 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +49% | 40.6 min |
| 2 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +46% | 37.8 min |
| 3 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Samsung SDI INR21700-40T | Nazgul XL10 V6 10-inch frame | pass | +39% | 36.4 min |
| 4 | E3 2814 850KV / 1050 3-blade / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +35% | 36.4 min |
| 5 | E3 2814 850KV / 1050 3-blade / 6S3P Samsung SDI INR21700-40T | Nazgul XL10 V6 10-inch frame | pass | +34% | 35.0 min |
| 6 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S2P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +29% | 33.9 min |
| 7 | XRotor 3115 900KV / MacroQuad 10x4.5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +28% | 34.7 min |
| 8 | E3 2814 850KV / 1050 3-blade / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +28% | 39.1 min |
| 9 | E3 3115 900KV / 1050 3-blade / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +27% | 33.1 min |
| 10 | E3 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +26% | 32.9 min |
| 14 | **E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P45B** | Nazgul XL10 V6 10-inch frame | pass | +23% | 32.6 min |

## What extra weight costs

![What extra weight costs](charts/margin.png)

Cruise minutes as extra grams go on:

| Setup | +0 g | +100 g | +200 g | +300 g | +400 g | +500 g | +600 g |
|---|---|---|---|---|---|---|---|
| base | 53.0 | 48.7 | 44.9 | 41.6 | 38.6 | 36.0 | 33.7 |
| V | 42.7 | 39.7 | 37.0 | 34.6 | 32.4 | 30.5 | 28.8 |
| P | 45.2 | 41.9 | 38.9 | 36.2 | 33.9 | 31.8 | 29.9 |
| mission | 37.2 | 34.8 | 32.6 | 30.7 | 29.0 | 27.4 | 26.0 |

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
