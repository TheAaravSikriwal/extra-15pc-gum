# Sizing report

> **Made from made-up test parts.** Every number here comes from invented parts in `tests/fixtures/`, so it says nothing about a real drone. It's here to show what the report looks like.

*Generated on 2026-10-17 by pcs14 0.1.0, the sizing model in `src/pcs14/sizing/`. Numbers shown as A / B are the published data / the pessimistic version. Rounding always goes toward failing.*

## The verdict

**Pass.** Every required setup (base, V, P, mission) meets every target, even with pessimistic data.

The motors and battery are sized for **mission**, carrying an extra 200 g of growth margin. Setups marked optional get checked and reported, but don't have to pass.

![Flight time, every setup](charts/flight-times.png)

## The build

| Part | Pick | Mass | Numbers from |
|---|---|---|---|
| Motors (4) | Testco M2810 900KV | 70 g each | made up |
| Props (4) | Testco P10x4.5 (10 x 4.5 in, 2 blades) | 14 g each | made up |
| Thrust table | 24 V, 9 rows | | made up |
| Pack | 6S2P Testco C21700-45: 9000 mAh, 48 milliohms, 90 A continuous | 900 g | made up |
| ESC | Testco E55 4-in-1 | 25 g | made up |
| Frame | Testco X10 | 300 g | made up |

## Every setup

| Setup | Modules | Required | Weight | Hover | Cruise at 10 m/s | Thrust-to-weight at the reserve | Verdict |
|---|---|---|---|---|---|---|---|
| base | none | yes | 1671 g | 40.0 / 34.9 min | 54.3 / 47.5 min | 3.09 / 2.78:1 | pass |
| V | V | yes | 1856 g | 33.6 / 29.5 min | 43.3 / 38.2 min | 2.78 / 2.50:1 | pass |
| P | P | yes | 1831 g | 35.4 / 30.9 min | 46.8 / 41.0 min | 2.82 / 2.54:1 | pass |
| C | C | optional | 2071 g | 30.1 / 26.4 min | 39.3 / 34.5 min | 2.49 / 2.24:1 | pass |
| mission | V+P | yes | 2216 g (with 200 g margin) | 27.0 / 23.7 min | 34.0 / 30.1 min | 2.33 / 2.10:1 | pass |
| V+C | V+C | optional | 2256 g | 26.3 / 23.1 min | 33.0 / 29.2 min | 2.29 / 2.06:1 | pass |
| P+C | P+C | optional | 2231 g | 27.4 / 24.0 min | 35.0 / 30.9 min | 2.31 / 2.08:1 | pass |
| max | V+P+C | optional | 2416 g | 24.1 / 21.1 min | 29.9 / 26.3 min | 2.14 / 1.92:1 | marginal |

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 40.0 / 34.9 min | at least 25.0 min | +60% | pass |
| Cruise time at 10 m/s | 54.3 / 47.5 min | at least 30.0 min | +81% | pass |
| Thrust-to-weight at the reserve | 3.09 / 2.78:1 | at least 2.00:1 | +55% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 11.3 m/s, for 54.8 min of cruise.
- Top speed: 116 km/h on a full pack, 109 at half charge, 105 at the reserve.

</details>

<details>
<summary>V: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 33.6 / 29.5 min | at least 21.0 min | +60% | pass |
| Cruise time at 10 m/s | 43.3 / 38.2 min | at least 25.0 min | +73% | pass |
| Thrust-to-weight at the reserve | 2.78 / 2.50:1 | at least 2.00:1 | +39% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Top speed at half charge | 96 / 94 km/h | at least 80 km/h | +21% | pass |
| Holds position in 10 m/s wind | 2.67 / 2.40x | at least 1.30x | +106% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 10.6 m/s, for 43.4 min of cruise.
- Top speed: 103 km/h on a full pack, 96 at half charge, 93 at the reserve.

</details>

<details>
<summary>P: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 35.4 / 30.9 min | at least 21.0 min | +69% | pass |
| Cruise time at 10 m/s | 46.8 / 41.0 min | at least 25.0 min | +88% | pass |
| Thrust-to-weight at the reserve | 2.82 / 2.54:1 | at least 2.00:1 | +41% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Top speed at half charge | 101 / 99 km/h | at least 80 km/h | +27% | pass |
| Holds position in 10 m/s wind | 2.72 / 2.45x | at least 1.30x | +110% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.1 m/s, for 47.2 min of cruise.
- Top speed: 109 km/h on a full pack, 102 at half charge, 98 at the reserve.

</details>

<details>
<summary>C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 30.1 / 26.4 min | at least 17.0 min | +77% | pass |
| Cruise time at 10 m/s | 39.3 / 34.5 min | at least 20.0 min | +97% | pass |
| Thrust-to-weight at the reserve | 2.49 / 2.24:1 | at least 2.00:1 | +25% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Takeoff weight | 2071 g | at most 2500 g | +17% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 11.6 m/s, for 39.8 min of cruise.
- Top speed: 109 km/h on a full pack, 102 at half charge, 98 at the reserve.

</details>

<details>
<summary>mission: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 27.0 / 23.7 min | at least 21.0 min | +29% | pass |
| Cruise time at 10 m/s | 34.0 / 30.1 min | at least 25.0 min | +36% | pass |
| Thrust-to-weight at the reserve | 2.33 / 2.10:1 | at least 2.00:1 | +17% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Top speed at half charge | 92 / 90 km/h | at least 80 km/h | +16% | pass |
| Holds position in 10 m/s wind | 2.23 / 2.01x | at least 1.30x | +72% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Holds position in 10 m/s wind: Thrust available over thrust needed, at 10 m/s of airspeed and 20% charge
- Cheapest speed: 11.1 m/s, for 34.2 min of cruise.
- Top speed: 100 km/h on a full pack, 93 at half charge, 89 at the reserve.

</details>

<details>
<summary>V+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 26.3 / 23.1 min | at least 17.0 min | +55% | pass |
| Cruise time at 10 m/s | 33.0 / 29.2 min | at least 20.0 min | +65% | pass |
| Thrust-to-weight at the reserve | 2.29 / 2.06:1 | at least 2.00:1 | +15% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Takeoff weight | 2256 g | at most 2500 g | +10% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 11.0 m/s, for 33.2 min of cruise.
- Top speed: 99 km/h on a full pack, 92 at half charge, 88 at the reserve.

</details>

<details>
<summary>P+C: pass</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 27.4 / 24.0 min | at least 17.0 min | +61% | pass |
| Cruise time at 10 m/s | 35.0 / 30.9 min | at least 20.0 min | +75% | pass |
| Thrust-to-weight at the reserve | 2.31 / 2.08:1 | at least 2.00:1 | +16% | pass |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Takeoff weight | 2231 g | at most 2500 g | +11% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 11.4 m/s, for 35.4 min of cruise.
- Top speed: 104 km/h on a full pack, 96 at half charge, 92 at the reserve.

</details>

<details>
<summary>max: marginal</summary>

| Check | Published / pessimistic | Target | Margin | Verdict |
|---|---|---|---|---|
| Hover time | 24.1 / 21.1 min | at least 17.0 min | +42% | pass |
| Cruise time at 10 m/s | 29.9 / 26.3 min | at least 20.0 min | +50% | pass |
| Thrust-to-weight at the reserve | 2.14 / 1.92:1 | at least 2.00:1 | +7% | marginal |
| Full-throttle current | 82.2 A | at most 90.0 A | +9% | pass |
| Takeoff weight | 2416 g | at most 2500 g | +3% | pass |

- Thrust-to-weight at the reserve: Full throttle at 20% charge, with the pack sagging under the load
- Full-throttle current: All four motors flat out on a full pack, against the pack's rating
- Cheapest speed: 11.0 m/s, for 30.1 min of cruise.
- Top speed: 96 km/h on a full pack, 88 at half charge, 84 at the reserve.

</details>

## Mass budget: mission

| Line | Mass |
|---|---|
| Frame: Testco X10 | 300 g |
| 4 motors: Testco M2810 900KV | 280 g |
| 4 props: Testco P10x4.5 | 56 g |
| ESC: Testco E55 4-in-1 | 25 g |
| Pack: 6S2P Testco C21700-45 | 900 g |
| H743 flight controller | 12 g |
| receiver | 3 g |
| downward lidar | 5 g |
| safety monitor | 20 g |
| Remote ID module | 25 g |
| wiring and connectors | 45 g |
| GPS and compass on a mast | 20 g |
| camera | 30 g |
| companion computer | 60 g |
| HaLow radio | 15 g |
| module V housing | 60 g |
| parachute | 120 g |
| parachute ejector | 40 g |
| Growth margin | 200 g |
| **Total** | **2216 g** |

## One flight, start to reserve

![One flight, start to reserve](charts/battery.png)

## Power and speed

![Power against airspeed](charts/power.png)

The cruise targets are checked at 10 m/s for now. The speed that actually costs mission the least is 11.1 m/s, where it cruises for 34.2 min.

## The sweep

2 builds tried, ranked by verdict, then by how far their tightest required check clears its limit. The build in this report ranks #1 of 2.

![Every build the sweep tried](charts/sweep.png)

| Rank | Build | Frame | Verdict | Tightest margin | mission cruise |
|---|---|---|---|---|---|
| 1 | **M2810 900KV / P10x4.5 / 6S2P Testco C21700-45** | X10 | pass | +9% | 34.0 min |
| 2 | M2810 900KV / P10x4.5 / 6S3P Testco C21700-45 | X10 | marginal | +6% | 41.3 min |

## What extra weight costs

![What extra weight costs](charts/margin.png)

Cruise minutes as extra grams go on:

| Setup | +0 g | +100 g | +200 g | +300 g | +400 g |
|---|---|---|---|---|---|
| base | 54.3 | 50.1 | 46.4 | 43.2 | 40.4 |
| V | 43.3 | 40.5 | 38.0 | 35.8 | 33.8 |
| P | 46.8 | 43.6 | 40.7 | 38.2 | 35.9 |
| mission | 38.3 | 36.1 | 34.0 | 32.2 | 30.5 |

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
