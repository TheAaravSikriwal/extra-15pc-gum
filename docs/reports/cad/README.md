# The virtual drone (CAD)

*Generated on 2026-10-18 by pcs14 0.1.0, the CAD layer in `src/pcs14/cad/`. Every module combination gets built, its pack slid to where it balances best, and checked: collisions, prop clearance, the parachute's cone, the module rail, balance, and the makers' placement rules.*

![The drone, three-quarter view](views/three-quarter.png)

## The verdict

**Pass.** All 8 combinations pass every check.

Built from E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P42A.

## Every module combination

| Setup | Modules | Weight | Pack at | Center of gravity (x, y, z) | Busiest motor | Verdict |
|---|---|---|---|---|---|---|
| base | none | 1783 g | -11 mm | -0.1, 0.0, -2.5 mm | +0.1% | pass |
| V | V | 1932 g | -7 mm | -0.1, 0.2, 3.2 mm | +0.2% | pass |
| P | P | 1943 g | -18 mm | -0.1, 0.0, 7.2 mm | +0.1% | pass |
| C | C | 1933 g | 11 mm | -0.1, 0.0, -4.5 mm | +0.0% | pass |
| mission | V+P | 2093 g | -14 mm | -0.0, 0.2, 11.8 mm | +0.2% | pass |
| V+C | V+C | 2082 g | 15 mm | -0.0, 0.2, 0.9 mm | +0.2% | pass |
| P+C | P+C | 2093 g | 4 mm | -0.0, 0.0, 4.7 mm | +0.0% | pass |
| max | V+P+C | 2243 g | 8 mm | 0.0, 0.2, 9.1 mm | +0.1% | pass |

The pack's position is along x from the motors' center; it slides to balance each combination. The busiest motor column says how much harder the busiest motor works than the average in a hover (the limit is +5%).

Every check, setup by setup:

<details>
<summary>base: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = -11 mm, the center of gravity sits -0.1 mm along x and +0.0 mm along y, so the busiest motor works 0.1% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>V: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = -7 mm, the center of gravity sits -0.1 mm along x and +0.2 mm along y, so the busiest motor works 0.2% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 3's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire gps is 42.8 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 4's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire gps is 51.2 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| module rail | v housing spans x = -50 to 12 mm, on a rail from -50 to 66 | pass |
| compass distance | the compass is 105 mm from wire battery leads (Matek asks for 100) | pass |
| remote id distance | the Remote ID module is 141 mm from the GPS | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>P: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = -18 mm, the center of gravity sits -0.1 mm along x and +0.0 mm along y, so the busiest motor works 0.1% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire chute servo is 70.4 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire chute servo is 74.4 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire chute servo is 77.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire chute servo is 88.4 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| parachute cone | nothing in the chute's way | pass |
| module rail | p holder spans x = 12 to 64 mm, on a rail from -50 to 66 | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>C: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = 11 mm, the center of gravity sits -0.1 mm along x and +0.0 mm along y, so the busiest motor works 0.0% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>mission: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = -14 mm, the center of gravity sits -0.0 mm along x and +0.2 mm along y, so the busiest motor works 0.2% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 1's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 1's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire chute servo is 70.4 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 2's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 2's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire chute servo is 74.4 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 3's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire gps is 42.8 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire chute servo is 77.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 4's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire gps is 51.2 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire chute servo is 88.4 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| parachute cone | nothing in the chute's way | pass |
| module rail | v housing spans x = -50 to 12 mm, on a rail from -50 to 66 | pass |
| module rail | p holder spans x = 12 to 64 mm, on a rail from -50 to 66 | pass |
| compass distance | the compass is 105 mm from wire battery leads (Matek asks for 100) | pass |
| remote id distance | the Remote ID module is 141 mm from the GPS | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>V+C: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = 15 mm, the center of gravity sits -0.0 mm along x and +0.2 mm along y, so the busiest motor works 0.2% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 3's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire gps is 42.8 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 4's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire gps is 51.2 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| module rail | v housing spans x = -50 to 12 mm, on a rail from -50 to 66 | pass |
| compass distance | the compass is 105 mm from wire battery leads (Matek asks for 100) | pass |
| remote id distance | the Remote ID module is 141 mm from the GPS | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>P+C: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = 4 mm, the center of gravity sits -0.0 mm along x and +0.0 mm along y, so the busiest motor works 0.0% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire chute servo is 70.4 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire chute servo is 74.4 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire chute servo is 77.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire chute servo is 88.4 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| parachute cone | nothing in the chute's way | pass |
| module rail | p holder spans x = 12 to 64 mm, on a rail from -50 to 66 | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

<details>
<summary>max: pass</summary>

| Check | Result | Verdict |
|---|---|---|
| balance | with the pack at x = 8 mm, the center of gravity sits +0.0 mm along x and +0.2 mm along y, so the busiest motor works 0.1% harder | pass |
| collisions | nothing overlaps | pass |
| prop clearance | frame is 10.6 mm from prop 1's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 1's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 1's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 1's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 1's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 1's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 1's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire motor leads front left is 28.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire lidar is 30.3 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 1's disk (needs 20) | pass |
| prop clearance | wire chute servo is 70.4 mm from prop 1's disk (needs 20) | pass |
| prop clearance | frame is 10.6 mm from prop 2's disk (needs 10) | pass |
| prop clearance | ruko-r111 is 15.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-camera-module-3 is 16.4 mm from prop 2's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 48.2 mm from prop 2's disk (needs 10) | pass |
| prop clearance | fruity-chutes-harrier-40-42 is 38.1 mm from prop 2's disk (needs 10) | pass |
| prop clearance | module rail is 30.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | remote id mount is 11.9 mm from prop 2's disk (needs 10) | pass |
| prop clearance | camera bracket is 11.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | v housing is 43.7 mm from prop 2's disk (needs 10) | pass |
| prop clearance | p holder is 32.0 mm from prop 2's disk (needs 10) | pass |
| prop clearance | wire battery leads is 75.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire motor leads front right is 28.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire lidar is 40.7 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire safety monitor is 61.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire module connector is 84.6 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire camera cable is 20.5 mm from prop 2's disk (needs 20) | pass |
| prop clearance | wire chute servo is 74.4 mm from prop 2's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 3's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 3's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 3's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 3's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 3's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire motor leads back left is 28.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire gps is 42.8 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | wire chute servo is 77.3 mm from prop 3's disk (needs 20) | pass |
| prop clearance | frame is 32.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-5-4gb is 19.7 mm from prop 4's disk (needs 10) | pass |
| prop clearance | rpi-active-cooler is 33.8 mm from prop 4's disk (needs 10) | pass |
| prop clearance | module rail is 38.9 mm from prop 4's disk (needs 10) | pass |
| prop clearance | gps mast is 37.3 mm from prop 4's disk (needs 10) | pass |
| prop clearance | v housing is 15.1 mm from prop 4's disk (needs 10) | pass |
| prop clearance | wire battery leads is 45.1 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire motor leads back right is 28.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire receiver is 55.6 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire gps is 51.2 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire module connector is 77.5 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire camera cable is 78.3 mm from prop 4's disk (needs 20) | pass |
| prop clearance | wire chute servo is 88.4 mm from prop 4's disk (needs 20) | pass |
| prop clearance | props 1 and 2 are 43.0 mm apart | pass |
| prop clearance | props 1 and 3 are 43.0 mm apart | pass |
| prop clearance | props 1 and 4 are 166.0 mm apart | pass |
| prop clearance | props 2 and 3 are 166.0 mm apart | pass |
| prop clearance | props 2 and 4 are 43.0 mm apart | pass |
| prop clearance | props 3 and 4 are 43.0 mm apart | pass |
| parachute cone | nothing in the chute's way | pass |
| module rail | v housing spans x = -50 to 12 mm, on a rail from -50 to 66 | pass |
| module rail | p holder spans x = 12 to 64 mm, on a rail from -50 to 66 | pass |
| compass distance | the compass is 105 mm from wire battery leads (Matek asks for 100) | pass |
| remote id distance | the Remote ID module is 141 mm from the GPS | pass |
| lidar view | the lidar sits 50 mm off the ground when landed, so it can't read the last 150 mm of a landing | pass |

</details>

## Mass properties

Each part's weight spread over its solid, with the pack at its trim. Inertia is about the center of gravity.

| Setup | Weight | Ixx | Iyy | Izz |
|---|---|---|---|---|
| base | 1783 g | 12.7 g m² | 15.2 g m² | 25.6 g m² |
| V | 1932 g | 13.7 g m² | 16.6 g m² | 26.1 g m² |
| P | 1943 g | 15.1 g m² | 18.0 g m² | 26.0 g m² |
| C | 1933 g | 12.9 g m² | 17.8 g m² | 28.1 g m² |
| mission | 2093 g | 15.9 g m² | 19.1 g m² | 26.5 g m² |
| V+C | 2082 g | 13.9 g m² | 19.4 g m² | 28.8 g m² |
| P+C | 2093 g | 15.4 g m² | 20.4 g m² | 28.3 g m² |
| max | 2243 g | 16.2 g m² | 21.8 g m² | 28.9 g m² |

## My printed parts

Weighed from their geometry and material. Where the catalog had a guess, it's next to it.

| Part | Material | Weight | The catalog's guess |
|---|---|---|---|
| leg front left | tpu | 6.6 g | none yet (landing-legs) |
| leg front right | tpu | 6.6 g | none yet (landing-legs) |
| leg back left | tpu | 6.6 g | none yet (landing-legs) |
| leg back right | tpu | 6.6 g | none yet (landing-legs) |
| battery tray | petg_cf | 29.4 g | none yet (battery-tray) |
| module rail | petg_cf | 13.2 g | 30 g (module-mount) |
| gps mast | tpu | 5.2 g | 10 g (gps-mast) |
| lidar bracket | petg_cf | 2.4 g | none yet (lidar-bracket) |
| remote id mount | tpu | 1.4 g | none yet (remote-id-mount) |
| safety monitor carrier | petg_cf | 2.8 g | none yet (safety-monitor-carrier) |
| camera bracket | petg_cf | 2.4 g | none yet (camera-bracket) |
| v housing | petg_cf | 40.2 g | 50 g (v-housing) |
| p holder | petg_cf | 6.4 g | 15 g (p-mount) |

Together they weigh 130 g.

## Wires

Rough routes, until the electrical step picks gauges and connectors.

| Wire | Length |
|---|---|
| battery leads | 159 mm |
| motor leads front left | 183 mm |
| motor leads front right | 183 mm |
| motor leads back left | 183 mm |
| motor leads back right | 183 mm |
| receiver | 41 mm |
| gps | 137 mm |
| lidar | 146 mm |
| safety monitor | 20 mm |
| bec feed | 23 mm |
| module connector | 12 mm |
| camera cable | 179 mm |
| chute servo | 22 mm |

## What's estimated

- emax-e3-2814-850kv: bell_length_mm. Emax doesn't publish how the 45.5 mm splits between the body and the shaft. 31 mm for the base and bell, leaving 14.5 mm of shaft, is a typical split for a 2814, to be checked against Emax's side photos
- gemfan-1050x3: hub_diameter_mm, hub_thickness_mm, blade_width_mm. Gemfan publishes only the size, bore and weight. The 9 mm hub and 22 mm blade width come from a retailer's spec block (rotorvillage.ca), which looks copied from Gemfan. The hub diameter isn't published anywhere; 15 mm is a guess for a 10-inch tri-blade
- holybro-tekko32-f4-50a: thickness_mm, top_mm, bottom_mm. Holybro gives 6 mm overall; the split between the board and its parts, and the hole pattern sitting centered along the 48 mm length, come from Holybro's stack STEP, measured roughly
- iflight-nazgul-xl10-v6: arm_width_mm, motor_pad_mm, body_front_mm, body_back_mm, body_width_mm, nose_from_mm, nose_width_mm. Not published, so traced from iFlight's top-down product render (https://cdn.iflight.com/store/product/Drone-Frame/XL10-V6/XL10-V6-B3.png) with the 420 mm diagonal between motors as the scale. The motors came out 295.5 x 298.9 mm apart against iFlight's 297 x 297, so the scale is good to about 1%. Arms 15 mm wide (15.1 to 16.4 along their length); body plates 36 mm wide, narrowing to 29 mm from about 70 mm ahead of the center, reaching 154 mm ahead of the motors' center and 62 mm behind, not counting the camera cage and the XT60 mount. The motor pads weren't measured; 34 mm is a guess that just carries a 35 mm motor
- holybro-kakute-h7: thickness_mm, top_mm, bottom_mm. Holybro's stack STEP measures 7.4 mm overall with parts on both sides; the split is rough
- pjrc-teensy-41: bottom_mm. The microSD socket's height underneath isn't given; 1.5 mm is a guess
- safety-monitor-extras: length_mm, width_mm, height_mm. A box big enough for a small IMU breakout and a signal switch board
- rpi-camera-module-3: bottom_mm. The 11.3 mm overall depth minus the lens stack and the board
- rpi-5-4gb: thickness_mm, top_mm, bottom_mm. The drawing doesn't give the board thickness or the USB and Ethernet stack's height; these are typical for a Raspberry Pi
- heltec-ht-hc01p: length_mm, width_mm, thickness_mm, top_mm, bottom_mm. The HAT looks HAT-sized in Heltec's photos, so it's drawn as the standard Raspberry Pi HAT (65 x 56.5 mm, holes on 58 x 49 mm), with the card lying on it and a 40-pin header underneath. Heltec only lists Pi 1 to 4 for the HAT
- halow-antenna-915: diameter_mm, length_mm. Physics, not a datasheet: half the wavelength at 915 MHz. A real antenna will be close to this, and it needs a spot clear of the props and the carbon
- claws-placeholder: length_mm, width_mm, height_mm. A box roughly the size of a small claw with its servos

## Existing CAD models

Checked for every part before modeling it. They stay in a local cache that never gets committed, and get compared with my parts by size and hole spacing.

| Part | Found | Terms | Compared with mine |
|---|---|---|---|
| emax-e3-2814-850kv | none |  |  |
| gemfan-1050x3 | none |  |  |
| holybro-tekko32-f4-50a | official | No license on the download page; holybro.com's terms forbid reproducing it without written permission. Fine to download and use locally, not to commit. | not downloaded |
| iflight-nazgul-xl10-v6 | unofficial | Unknown: the site blocked automated access, so its license couldn't be read | not downloaded |
| molicel-p42a | none |  |  |
| holybro-kakute-h7 | official | No license on the download page; holybro.com's terms forbid reproducing it without written permission. Fine to download and use locally, not to commit. | mine 7.4 x 35.0 x 35.0 mm, theirs 20.7 x 37.2 x 48.0 mm; holes line up |
| radiomaster-rp2-v2 | none |  |  |
| benewake-tf-luna | none |  |  |
| pjrc-teensy-41 | unofficial | Its author, Zack Kummer, says in the PJRC forum it can be included with credit | not downloaded |
| safety-monitor-extras | none |  |  |
| ruko-r111 | none |  |  |
| base-wiring | none |  |  |
| module-mount | none |  |  |
| matek-bec12s-pro | none |  |  |
| matek-m10q-5883 | official | No license in the zip or on the page; copyright Matek, so all rights reserved | mine 12.4 x 20.0 x 20.0 mm, theirs 11.4 x 20.0 x 20.0 mm |
| gps-mast | none |  |  |
| rpi-camera-module-3 | official | No license file; Raspberry Pi's site terms reserve all rights. | mine 11.3 x 23.9 x 25.0 mm, theirs 10.2 x 23.9 x 25.0 mm; holes line up |
| rpi-5-4gb | official | MIT license, in the zip: it can be shared, with the copyright notice. It's 77 MB unzipped, so it stays in the local cache | in the cache, but 77 MB is too big to compare on every run |
| rpi-active-cooler | none |  |  |
| heltec-ht-hc01p | none |  |  |
| v-housing | none |  |  |
| rpi-camera-cable-standard-mini | none |  |  |
| halow-antenna-915 | none |  |  |
| fruity-chutes-harrier-40-42 | none |  |  |
| p-mount | none |  |  |
| claws-placeholder | none |  |  |

## Files

Generated on every run, and not committed (they're build outputs):

- `outputs/cad/drone.step`
- `outputs/cad/drone-gazebo.stl`
- `outputs/cad/drone-cfd.stl`
- `outputs/cad/drone.glb`
- `outputs/cad/print/leg-front-left.3mf`
- `outputs/cad/print/leg-front-right.3mf`
- `outputs/cad/print/leg-back-left.3mf`
- `outputs/cad/print/leg-back-right.3mf`
- `outputs/cad/print/battery-tray.3mf`
- `outputs/cad/print/module-rail.3mf`
- `outputs/cad/print/gps-mast-1.3mf`
- `outputs/cad/print/gps-mast-2.3mf`
- `outputs/cad/print/lidar-bracket.3mf`
- `outputs/cad/print/remote-id-mount.3mf`
- `outputs/cad/print/safety-monitor-carrier.3mf`
- `outputs/cad/print/camera-bracket.3mf`
- `outputs/cad/print/v-housing.3mf`
- `outputs/cad/print/p-holder.3mf`

## Views

![Front](views/front.png) ![Side](views/side.png) ![Top](views/top.png) ![Exploded](views/exploded.png)
