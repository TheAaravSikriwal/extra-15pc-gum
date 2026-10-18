# Sizing report

*Generated on 2026-10-17 by pcs14 0.1.0, the sizing model in `src/pcs14/sizing/`. Numbers shown as A / B are the published data / the pessimistic version. Rounding always goes toward failing.*

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
| Pack | 6S2P Molicel INR-21700-P42A: 8062 mAh, 51 milliohms, 90 A continuous | 858 g | [manufacturer](https://www.molicel.com/wp-content/uploads/INR21700P42A_1.7_Product-Data-Sheet-of-INR-21700-P42A-80092.pdf) |
| ESC | Holybro Tekko32 F4 4in1 50A (AM32) | 14 g | [manufacturer](https://holybro.com/products/tekko32-f4-4in1-50a-esc) |
| Frame | iFlight Nazgul XL10 V6 10-inch frame | 343 g | [manufacturer](https://shop.iflight.com/xl10-v6-10-inch-fpv-frame-Pro1967) |
| Current cap | 90 A, set in my firmware (100% of the pack's rating) | | |

## Every setup

| Setup | Modules | Required | Weight | Hover | Cruise at 10 m/s | Thrust-to-weight at the reserve | Verdict |
|---|---|---|---|---|---|---|---|
| base | none | yes | 1732 g | 39.9 / 34.0 min | 54.1 / 46.3 min | 3.59 / 3.23:1 | pass |
| V | V | yes | 1885 g | 33.5 / 28.7 min | 43.4 / 37.4 min | 3.30 / 2.97:1 | pass |
| P | P | yes | 1901 g | 34.6 / 29.4 min | 46.0 / 39.3 min | 3.27 / 2.94:1 | pass |
| C | C | optional | 2132 g | 28.8 / 24.6 min | 37.7 / 32.3 min | 2.91 / 2.62:1 | pass |
| mission | V+P | yes | 2254 g (with 200 g margin) | 25.7 / 22.1 min | 32.8 / 28.3 min | 2.76 / 2.48:1 | pass |
| V+C | V+C | optional | 2285 g | 25.1 / 21.6 min | 31.7 / 27.4 min | 2.72 / 2.45:1 | pass |
| P+C | P+C | optional | 2301 g | 25.7 / 22.0 min | 33.0 / 28.4 min | 2.70 / 2.43:1 | pass |
| max | V+P+C | optional | 2454 g | 22.6 / 19.5 min | 28.3 / 24.5 min | 2.53 / 2.28:1 | pass |

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 39.9 / 34.0 min | at least 25.0 min | +60% | pass |
| Cruise time at 10 m/s | 54.1 / 46.3 min | at least 30.0 min | +80% | pass |
| Thrust-to-weight at the reserve | 3.59 / 3.23:1 | at least 2.00:1 | +80% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 11.8 m/s, for 55.0 min of cruise.
- Top speed: 120 km/h on a full pack, 117 at half charge, 114 at the reserve.

</details>

<details>
<summary>V: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 33.5 / 28.7 min | at least 21.0 min | +60% | pass |
| Cruise time at 10 m/s | 43.4 / 37.4 min | at least 25.0 min | +74% | pass |
| Thrust-to-weight at the reserve | 3.30 / 2.97:1 | at least 2.00:1 | +65% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 104 / 102 km/h | at least 80 km/h | +31% | pass |
| Holds position in 10 m/s wind | 3.19 / 2.87x | at least 1.30x | +146% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.2 m/s, for 43.8 min of cruise.
- Top speed: 108 km/h on a full pack, 104 at half charge, 102 at the reserve.

</details>

<details>
<summary>P: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 34.6 / 29.4 min | at least 21.0 min | +65% | pass |
| Cruise time at 10 m/s | 46.0 / 39.3 min | at least 25.0 min | +84% | pass |
| Thrust-to-weight at the reserve | 3.27 / 2.94:1 | at least 2.00:1 | +64% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 111 / 109 km/h | at least 80 km/h | +40% | pass |
| Holds position in 10 m/s wind | 3.18 / 2.86x | at least 1.30x | +145% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.9 m/s, for 46.8 min of cruise.
- Top speed: 115 km/h on a full pack, 112 at half charge, 109 at the reserve.

</details>

<details>
<summary>C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 28.8 / 24.6 min | at least 17.0 min | +70% | pass |
| Cruise time at 10 m/s | 37.7 / 32.3 min | at least 20.0 min | +89% | pass |
| Thrust-to-weight at the reserve | 2.91 / 2.62:1 | at least 2.00:1 | +46% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2133 g | at most 2500 g | +15% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 12.2 m/s, for 38.6 min of cruise.
- Top speed: 113 km/h on a full pack, 110 at half charge, 107 at the reserve.

</details>

<details>
<summary>mission: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 25.7 / 22.1 min | at least 21.0 min | +23% | pass |
| Cruise time at 10 m/s | 32.8 / 28.3 min | at least 25.0 min | +31% | pass |
| Thrust-to-weight at the reserve | 2.76 / 2.48:1 | at least 2.00:1 | +38% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Top speed at half charge | 102 / 100 km/h | at least 80 km/h | +28% | pass |
| Holds position in 10 m/s wind | 2.67 / 2.40x | at least 1.30x | +106% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.8 m/s, for 33.3 min of cruise.
- Top speed: 106 km/h on a full pack, 103 at half charge, 100 at the reserve.

</details>

<details>
<summary>V+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 25.1 / 21.6 min | at least 17.0 min | +48% | pass |
| Cruise time at 10 m/s | 31.7 / 27.4 min | at least 20.0 min | +59% | pass |
| Thrust-to-weight at the reserve | 2.72 / 2.45:1 | at least 2.00:1 | +36% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2286 g | at most 2500 g | +9% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 11.7 m/s, for 32.2 min of cruise.
- Top speed: 104 km/h on a full pack, 100 at half charge, 98 at the reserve.

</details>

<details>
<summary>P+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 25.7 / 22.0 min | at least 17.0 min | +51% | pass |
| Cruise time at 10 m/s | 33.0 / 28.4 min | at least 20.0 min | +65% | pass |
| Thrust-to-weight at the reserve | 2.70 / 2.43:1 | at least 2.00:1 | +35% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2302 g | at most 2500 g | +8% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 12.2 m/s, for 33.8 min of cruise.
- Top speed: 109 km/h on a full pack, 106 at half charge, 103 at the reserve.

</details>

<details>
<summary>max: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 22.6 / 19.5 min | at least 17.0 min | +33% | pass |
| Cruise time at 10 m/s | 28.3 / 24.5 min | at least 20.0 min | +42% | pass |
| Thrust-to-weight at the reserve | 2.53 / 2.28:1 | at least 2.00:1 | +27% | pass |
| Full-throttle current | 90.0 A | at most 90.0 A | +0% | pass |
| Takeoff weight | 2455 g | at most 2500 g | +2% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack. The firmware caps it at 90 A; without the cap it would pull 127 A
- Cheapest speed: 11.8 m/s, for 28.7 min of cruise.
- Top speed: 101 km/h on a full pack, 98 at half charge, 95 at the reserve.

</details>

## Mass budget: mission

| Line | Mass |
|---|---|
| Frame: iFlight Nazgul XL10 V6 10-inch frame | 343 g |
| 4 motors: Emax E3 2814 850KV | 328 g |
| 4 props: Gemfan 1050 3-blade | 67 g |
| ESC: Holybro Tekko32 F4 4in1 50A (AM32) | 14 g |
| Pack: 6S2P Molicel INR-21700-P42A | 858 g |
| Kakute H7 V1.5 flight controller | 8 g |
| RP2 V2 ExpressLRS 2.4 GHz receiver | 1 g |
| TF-Luna lidar | 5 g |
| Teensy 4.1 (safety monitor) | 15 g |
| Safety monitor IMU breakout and signal switch | 5 g |
| R111 Remote ID broadcast module | 14 g |
| Wiring, XT60 lead, battery strap and hardware | 45 g |
| Module mount and connector | 30 g |
| M10Q-5883 GPS and compass | 8 g |
| Folding GPS mast | 10 g |
| Camera Module 3 | 4 g |
| Raspberry Pi 5 (4 GB) companion computer | 46 g |
| Active cooler for the Pi 5 | 15 g |
| HT-HC01P Wi-Fi HaLow card with Pi HAT | 15 g |
| BEC12S-PRO 5 V 5 A supply for the Pi | 5 g |
| Module V housing and mounts | 50 g |
| Harrier 40-42 parachute bundle | 154 g |
| Module P mount | 15 g |
| Growth margin | 200 g |
| **Total** | **2254 g** |

## One flight, start to reserve

![One flight, start to reserve](charts/battery.png)

## Power and speed

![Power against airspeed](charts/power.png)

The cruise targets are checked at 10 m/s for now. The speed that actually costs mission the least is 11.8 m/s, where it cruises for 33.3 min.

## The sweep

192 builds tried, ranked by verdict, then by how far their tightest required check clears its limit. The build in this report ranks #33 of 192.

![Every build the sweep tried](charts/sweep.png)

| Rank | Build | Frame | Verdict | Tightest margin | mission cruise |
|---|---|---|---|---|---|
| 1 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +46% | 43.4 min |
| 2 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +45% | 40.5 min |
| 3 | XRotor 3115 900KV / MacroQuad 10x4.5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +42% | 37.1 min |
| 4 | XRotor 3115 900KV / MacroQuad 10x5x3 / 6S3P Samsung SDI INR21700-40T | Nazgul XL10 V6 10-inch frame | pass | +37% | 38.9 min |
| 5 | E3 2814 850KV / 1050 3-blade / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +36% | 38.9 min |
| 6 | E3 2814 850KV / 1050 3-blade / 6S3P Samsung SDI INR21700-40T | Nazgul XL10 V6 10-inch frame | pass | +36% | 37.4 min |
| 7 | XRotor 3115 900KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +36% | 36.3 min |
| 8 | XRotor 3115 900KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +35% | 33.9 min |
| 9 | E3 3115 900KV / 1050 3-blade / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +34% | 35.1 min |
| 10 | XRotor 3115 900KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P45B | Chimera9 ECO 9-inch frame | pass | +34% | 35.7 min |
| 33 | **E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P42A** | Nazgul XL10 V6 10-inch frame | pass | +23% | 32.8 min |

## What extra weight costs

![What extra weight costs](charts/margin.png)

Cruise minutes as extra grams go on:

| Setup | +0 g | +100 g | +200 g | +300 g | +400 g | +500 g | +600 g |
|---|---|---|---|---|---|---|---|
| base | 54.1 | 49.4 | 45.3 | 41.7 | 38.6 | 35.8 | 33.3 |
| V | 43.4 | 40.2 | 37.3 | 34.7 | 32.3 | 30.3 | 28.5 |
| P | 46.0 | 42.3 | 39.1 | 36.2 | 33.7 | 31.5 | 29.5 |
| mission | 37.8 | 35.1 | 32.8 | 30.7 | 28.8 | 27.1 | 25.6 |

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
