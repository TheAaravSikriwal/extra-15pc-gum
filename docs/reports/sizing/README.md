# Sizing report

*Generated on 2026-10-17 by pcs14 0.1.0, the sizing model in `src/pcs14/sizing/`. Numbers shown as A / B are the published data / the pessimistic version. Rounding always goes toward failing.*

## The verdict

**Pass.** Every required setup (base, V, P, mission) meets every target, even with pessimistic data.

The motors and battery are sized for **mission**, carrying an extra 200 g of growth margin. Setups marked optional get checked and reported, but don't have to pass.

![Flight time, every setup](charts/flight-times.png)

## The build

| Part | Pick | Mass | Numbers from |
|---|---|---|---|
| Motors (4) | Flash Hobby Mars M2814 730KV | 87 g each | [manufacturer](https://www.flashhobby.com/mars-2814-brushless-motor.html) |
| Props (4) | HQProp LR10x5x3 (long range) (10 x 5 in, 3 blades) | 18 g each | [manufacturer](https://www.hqprop.com/hqprop-lr10x5x3-2ccw2cw-black-glass-fiber-reinforced-nylon-p0419.html) |
| Thrust table | 24.35 V, 6 rows | | [manufacturer](https://www.flashhobby.com/upload/488/image/20250402/m2814-730kv----02-703971.jpg) |
| Pack | 6S3P Molicel INR-21700-P42A: 12093 mAh, 35 milliohms, 135 A continuous | 1257 g | [manufacturer](https://www.molicel.com/wp-content/uploads/INR21700P42A_1.7_Product-Data-Sheet-of-INR-21700-P42A-80092.pdf) |
| ESC | Holybro Tekko32 F4 4in1 50A (AM32) | 14 g | [manufacturer](https://holybro.com/products/tekko32-f4-4in1-50a-esc) |
| Frame | iFlight Nazgul XL10 V6 10-inch frame | 343 g | [manufacturer](https://shop.iflight.com/xl10-v6-10-inch-fpv-frame-Pro1967) |

## Every setup

| Setup | Modules | Required | Weight | Hover | Cruise at 10 m/s | Thrust-to-weight at the reserve | Verdict |
|---|---|---|---|---|---|---|---|
| base | none | yes | 2156 g | 47.2 / 40.2 min | 62.3 / 53.3 min | 2.92 / 2.63:1 | pass |
| V | V | yes | 2309 g | 41.0 / 35.1 min | 52.2 / 45.0 min | 2.73 / 2.45:1 | pass |
| P | P | yes | 2325 g | 42.1 / 35.8 min | 54.6 / 46.7 min | 2.71 / 2.44:1 | pass |
| C | C | optional | 2556 g | 36.2 / 30.9 min | 46.2 / 39.5 min | 2.46 / 2.22:1 | fail |
| mission | V+P | yes | 2678 g (with 200 g margin) | 32.9 / 28.1 min | 41.2 / 35.3 min | 2.35 / 2.12:1 | pass |
| V+C | V+C | optional | 2709 g | 32.2 / 27.5 min | 40.1 / 34.4 min | 2.32 / 2.09:1 | fail |
| P+C | P+C | optional | 2725 g | 32.9 / 28.0 min | 41.4 / 35.4 min | 2.31 / 2.08:1 | fail |
| max | V+P+C | optional | 2878 g | 29.4 / 25.1 min | 36.2 / 31.1 min | 2.19 / 1.97:1 | fail |

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 47.2 / 40.2 min | at least 25.0 min | +89% | pass |
| Cruise time at 10 m/s | 62.3 / 53.3 min | at least 30.0 min | +108% | pass |
| Thrust-to-weight at the reserve | 2.92 / 2.63:1 | at least 2.00:1 | +46% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 13.1 m/s, for 64.9 min of cruise.
- Top speed: 132 km/h on a full pack, 124 at half charge, 118 at the reserve.

</details>

<details>
<summary>V: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 41.0 / 35.1 min | at least 21.0 min | +96% | pass |
| Cruise time at 10 m/s | 52.2 / 45.0 min | at least 25.0 min | +109% | pass |
| Thrust-to-weight at the reserve | 2.73 / 2.45:1 | at least 2.00:1 | +37% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Top speed at half charge | 110 / 108 km/h | at least 80 km/h | +38% | pass |
| Holds position in 10 m/s wind | 2.65 / 2.39x | at least 1.30x | +105% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 12.4 m/s, for 53.5 min of cruise.
- Top speed: 118 km/h on a full pack, 111 at half charge, 105 at the reserve.

</details>

<details>
<summary>P: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 42.1 / 35.8 min | at least 21.0 min | +101% | pass |
| Cruise time at 10 m/s | 54.6 / 46.7 min | at least 25.0 min | +119% | pass |
| Thrust-to-weight at the reserve | 2.71 / 2.44:1 | at least 2.00:1 | +36% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Top speed at half charge | 118 / 115 km/h | at least 80 km/h | +48% | pass |
| Holds position in 10 m/s wind | 2.65 / 2.38x | at least 1.30x | +104% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 13.0 m/s, for 56.7 min of cruise.
- Top speed: 126 km/h on a full pack, 118 at half charge, 112 at the reserve.

</details>

<details>
<summary>C: fail</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 36.2 / 30.9 min | at least 17.0 min | +113% | pass |
| Cruise time at 10 m/s | 46.2 / 39.5 min | at least 20.0 min | +131% | pass |
| Thrust-to-weight at the reserve | 2.46 / 2.22:1 | at least 2.00:1 | +23% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Takeoff weight | 2557 g | at most 2500 g | -2% | fail |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 13.3 m/s, for 48.3 min of cruise.
- Top speed: 124 km/h on a full pack, 116 at half charge, 110 at the reserve.

</details>

<details>
<summary>mission: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 32.9 / 28.1 min | at least 21.0 min | +57% | pass |
| Cruise time at 10 m/s | 41.2 / 35.3 min | at least 25.0 min | +65% | pass |
| Thrust-to-weight at the reserve | 2.35 / 2.12:1 | at least 2.00:1 | +18% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Top speed at half charge | 107 / 104 km/h | at least 80 km/h | +35% | pass |
| Holds position in 10 m/s wind | 2.29 / 2.06x | at least 1.30x | +76% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 12.9 m/s, for 42.5 min of cruise.
- Top speed: 116 km/h on a full pack, 108 at half charge, 102 at the reserve.

</details>

<details>
<summary>V+C: fail</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 32.2 / 27.5 min | at least 17.0 min | +90% | pass |
| Cruise time at 10 m/s | 40.1 / 34.4 min | at least 20.0 min | +101% | pass |
| Thrust-to-weight at the reserve | 2.32 / 2.09:1 | at least 2.00:1 | +16% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Takeoff weight | 2710 g | at most 2500 g | -8% | fail |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 12.7 m/s, for 41.2 min of cruise.
- Top speed: 113 km/h on a full pack, 105 at half charge, 100 at the reserve.

</details>

<details>
<summary>P+C: fail</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 32.9 / 28.0 min | at least 17.0 min | +94% | pass |
| Cruise time at 10 m/s | 41.4 / 35.4 min | at least 20.0 min | +107% | pass |
| Thrust-to-weight at the reserve | 2.31 / 2.08:1 | at least 2.00:1 | +16% | pass |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Takeoff weight | 2726 g | at most 2500 g | -9% | fail |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 13.3 m/s, for 43.1 min of cruise.
- Top speed: 120 km/h on a full pack, 111 at half charge, 105 at the reserve.

</details>

<details>
<summary>max: fail</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 29.4 / 25.1 min | at least 17.0 min | +73% | pass |
| Cruise time at 10 m/s | 36.2 / 31.1 min | at least 20.0 min | +81% | pass |
| Thrust-to-weight at the reserve | 2.19 / 1.97:1 | at least 2.00:1 | +10% | marginal |
| Full-throttle current | 118.4 A | at most 135.0 A | +12% | pass |
| Takeoff weight | 2879 g | at most 2500 g | -15% | fail |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 12.7 m/s, for 37.2 min of cruise.
- Top speed: 110 km/h on a full pack, 102 at half charge, 96 at the reserve.

</details>

## Mass budget: mission

| Line | Mass |
|---|---|
| Frame: iFlight Nazgul XL10 V6 10-inch frame | 343 g |
| 4 motors: Flash Hobby Mars M2814 730KV | 348 g |
| 4 props: HQProp LR10x5x3 (long range) | 72 g |
| ESC: Holybro Tekko32 F4 4in1 50A (AM32) | 14 g |
| Pack: 6S3P Molicel INR-21700-P42A | 1257 g |
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
| **Total** | **2678 g** |

## One flight, start to reserve

![One flight, start to reserve](charts/battery.png)

## Power and speed

![Power against airspeed](charts/power.png)

The cruise targets are checked at 10 m/s for now. The speed that actually costs mission the least is 12.9 m/s, where it cruises for 42.5 min.

## The sweep

192 builds tried, ranked by verdict, then by how far their tightest required check clears its limit.

![Every build the sweep tried](charts/sweep.png)

| Rank | Build | Frame | Verdict | Tightest margin | mission cruise |
|---|---|---|---|---|---|
| 1 | Mars M2814 730KV / LR10x5x3 (long range) / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +12% | 41.2 min |
| 2 | Mars M2814 730KV / 1050 3-blade / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +11% | 42.5 min |
| 3 | E3 2814 850KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +9% | 32.9 min |
| 4 | E3 2814 850KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P42A | Chimera9 ECO 9-inch frame | pass | +9% | 32.4 min |
| 5 | XRotor 3115 900KV / MacroQuad 9x4x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +9% | 31.8 min |
| 6 | XRotor 3115 900KV / MacroQuad 9x4x3 / 6S3P Molicel INR-21700-P42A | Chimera9 ECO 9-inch frame | pass | +9% | 31.3 min |
| 7 | XRotor 3110 900KV / MacroQuad 9x4x3 / 6S3P Molicel INR-21700-P42A | Nazgul XL10 V6 10-inch frame | pass | +8% | 32.0 min |
| 8 | XRotor 3110 900KV / MacroQuad 9x4x3 / 6S3P Molicel INR-21700-P42A | Chimera9 ECO 9-inch frame | pass | +8% | 31.5 min |
| 9 | E3 2814 850KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P45B | Nazgul XL10 V6 10-inch frame | pass | +7% | 35.3 min |
| 10 | E3 2814 850KV / MacroQuad 9x5x3 / 6S3P Molicel INR-21700-P45B | Chimera9 ECO 9-inch frame | pass | +7% | 34.7 min |

## What extra weight costs

![What extra weight costs](charts/margin.png)

Cruise minutes as extra grams go on:

| Setup | +0 g | +100 g | +200 g | +300 g | +400 g | +500 g | +600 g |
|---|---|---|---|---|---|---|---|
| base | 62.3 | 57.8 | 53.8 | 50.3 | 47.1 | 44.1 | 41.5 |
| V | 52.2 | 48.9 | 45.9 | 43.2 | 40.7 | 38.4 | 36.3 |
| P | 54.6 | 50.9 | 47.7 | 44.7 | 42.0 | 39.6 | 37.4 |
| mission | 46.5 | 43.7 | 41.2 | 38.8 | 36.7 | 34.8 | 33.0 |

## How the numbers are made

- **Hover** power comes straight from the thrust table (volts x amps at the table's voltage). The battery model turns it into current with the pack's sag included.
- **Forward flight** splits each prop's power into lifting power, blade drag and the power to push the drone through the air, fitted to the hover table. Real rotors need 15% more lifting power than ideal theory, and blade drag takes 25% of a small prop's hover power.
- **The battery** is each cell's resting-voltage curve plus its internal resistance, scaled to the pack plus the wiring, stepped through the flight a few seconds at a time.
- **Pessimistic data** cuts every thrust in the table: thrust stand 2%, independent test 5%, manufacturer 10%, estimate 15%, made up 10%.
- **Holding position in wind** means flying at that airspeed at the 20% reserve with 30% more thrust available than needed. **Top speed** is checked at 50% charge, and the drone won't lean past 45 degrees.

## What this can't tell you

- Manufacturer thrust data runs optimistic. The pessimistic numbers allow for that, but only a thrust stand can say by how much.
- mission hovers at 670 g per motor, below the thrust table's first row (1047 g at 50% throttle). Down there the hover power is scaled from that row with momentum theory instead of read from a measured point, and that tends to come out a little low on power, so a little long on flight time.
- Cruise is the shakiest number here. The honesty check ([validation.md](validation.md)) flew a published long-range build through the model, and its cruise time came out much longer than the measured one, most likely because the drag of the props at speed isn't modeled yet. Trust the hover numbers more than the cruise ones for now.
- Drag is a guess from frontal area until the wind tunnel side track has real numbers.
- Coming straight down fast (the vortex ring state), cold weather and aging cells aren't modeled.
- The ESC's limits, wiring losses and heat get checked in the electrical step.
