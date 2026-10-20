# 2026-10-20: The flight sim's last batch, and what it says about the design

*PC, WSL2 Ubuntu and Windows. Step 4, tasks 11 and 12: every scenario in every combination, and closing the loop with the sizing model.*

## Some design changes first

Before the last batch I cleared four items off the open list, so the batch flew the drone as it is now:

| Change | Why |
|---|---|
| The pack's insides are worked out | Nickel-plated copper links, welds, solder and leads come to 2.3 mOhm and 43 g, against a 60 g guess |
| The GPS sits in a printed cradle on its mast | It wasn't held by anything. The cradle is its own printed part, because the mast stopped printing flat with it |
| Each module locks to the rail with thumb screws into heat-set inserts | "How the modules lock on" was an open question |
| The sizing model reads full throttle off the motor's table | It used to scale the top row with a power law, about 4% off the table |

Mission is 2408 g in the sizing model now (with the 200 g margin) and 2208 g in the CAD, and still passes.

## The batch

All 78 runs: twelve scenarios in eight module combinations, PX4 v1.17.0 in Gazebo Harmonic, at 4x sim speed, two at a time. It came back with about ten runs that failed in ways that made no sense: a drone that tumbled in the wind, low battery runs that stalled, take-offs where PX4 ran the motors up and the model never left the ground.

The wind one was the giveaway. Its log showed PX4's IMU going quiet for 44 ms of sim time right as the script changed the wind, and then a wobble that grew until it flipped. Two runs at 4x already kept the PC at a load of about 12 on its 16 threads, and every wind change started Gazebo's command-line tool, which costs about a second and a quarter of a CPU second each time. At 4x, a short stall on the PC is four times longer in the sim, and that's long enough to starve PX4's control loop. So the runner now talks to Gazebo through its Python bindings (0.04 s instead of 0.9), and every run that failed oddly flew again, alone. All of them passed. Flying my own firmware alongside the reruns spoiled three more (lesson learned twice), and they passed again on their own.

The runner also now calls a run "the sim failed, not the drone" when PX4 runs the motors up and the model never climbs at all, so that can't be graded as the drone's fault. A drone that climbs and then crashes is still the drone's.

## The result: 62 of 78 pass

The 16 that don't are three real findings, the same ones as before, now in every combination where they apply:

**A dead motor without the chute is a crash** (base, V, C, V+C). A quad can't fly on three motors. With P, PX4's failure detector sees the attitude go, terminates, and the chute brings it down; without P it falls at about 24 m/s.

**Losing GPS means a blind descent** that ends 31 to 36 m from where it happened in four of the eight combinations (C, mission, V+C, P+C), against a 30 m fly-away limit, and just inside it in the other four. There's no optical flow sensor, so nothing holds the position, and a small tilt error carries it off.

**Cruise endurance is about 25% under the sizing model** in all eight. The sizing model says forward flight is cheaper than a hover, as it is for a real prop moving into fresh air. Gazebo's rotors make the same thrust at any airspeed, so in the sim a cruise costs what a hover does. The truth is somewhere in between, and the wind tunnel side track is where it gets pinned down.

Everything else passes: the hover, the stick steps, top speed (88 km/h, PX4's 25 m/s cap), 10 m/s wind, lost link, low battery, the parachute drop, the sagging pack and the payload grab.

## Closing the loop

This is task 12: putting the sim's numbers next to the sizing model's.

The hover times agree to within 0.1 min in all eight combinations (base 33.7 against 33.6, Mission 25.2 against 25.2, Max 22.7 against 22.6), worked from the sim's logged rotor speeds through the same battery model. That's the sizing model's hover holding up in a full physics sim. The cruise doesn't agree, for the reason above.

The safety monitor's reference triggers, replayed over the 66 runs where nothing fails on purpose, fired zero times. The wind tumble that used to show up as a false trigger was the overloaded PC. Where something does fail (a dead motor, a termination), its free-fall trigger would fire 0.42 to 0.51 s after the failure.

One correction to an earlier claim. I raised PX4's attitude gain from the x500's 6.5 to 9 because a stick step took 0.6 s to settle against a 0.5 s target. In this batch the x500's gain settles in 0.29 s and mine in 0.17 s, both inside the target; the 0.6 s came from early runs, before the runner's fixes. The tuned gain stays, because it settles 1.7 times faster with 3% overshoot, but the reason changed, and the still now says so.

## What it means for the design

The two design questions this raises are the same as before, and they're mine to decide: should P (the chute) be in every combination, since a dead motor without it loses the drone, and should Base get an optical flow sensor, so a GPS failure isn't a blind descent? Both add weight to a design with very little margin.

## Next

Step 5 is well under way (its own log), and the report, the stills and a Rerun replay of every run are in [docs/reports/flight-sim](../reports/flight-sim/README.md).
