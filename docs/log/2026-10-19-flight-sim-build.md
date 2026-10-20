# 2026-10-19: The flight sim, everything but the flying

*PC, Windows side. Step 4c, tasks 1 to 8.*

The flight sim needs Ubuntu to actually fly, which the PC doesn't have yet. But most of the work is everything around the flying: what passing means, the model PX4 will fly, the math our own plugin will do, turning a flight log into battery drain, the safety monitor's triggers, grading and the report. That's all Python, so it's done and tested first.

## The motors

Gazebo models each rotor as thrust = a constant × its speed squared, with a drag torque in proportion to the thrust. Emax's thrust table gives thrust, current and rpm at each throttle step, so the constant comes from fitting the table. A fit across the whole table was off by 6% at hover, because real props aren't exactly speed-squared, and the top rows pull the line up. The drone never uses those rows anyway: at the 20% reserve with the 90 A cap, the motors top out around 8,800 rpm, so the fit uses only the stretch from just under hover to just over that.

The top speed turned up a small inconsistency in my own sizing model. It works out the capped full-throttle point by scaling from the table's top row with a power law, which gives 8,589 rpm and 13.5 N a motor; the table itself says that speed makes 12.8 N. Thrust is what decides thrust-to-weight, top speed and the wind hold, so the model's top speed is wherever the fitted motor makes the sizing model's 13.5 N. The rpm comes out 4% higher, which only changes how fast the props look. The power-law shortcut is on the open list.

## The model

One Gazebo model per combination, generated from the CAD:
- the mass, center of gravity and inertia, with the pack at its trim
- the rotors on the frame's motor mounts, in PX4's x500 order
- the x500's sensor noise
- a box and four feet to land on
- our drag plugin, with the chute in P and a payload joint in C

Mission flies at 2213 g, the CAD's weight; the sizing model's 2414 g adds the 200 g growth margin, which is room for later parts, not weight the drone carries today. It should hover at 58% throttle, close to the x500's own 60%. PX4 itself stays unmodified: it runs its x500 airframe with our parameters on top, including the 45° tilt limit the sizing model assumes and speed limits high enough for the 80 km/h run.

`pcs14 flight-sim` writes all eight models in about seven seconds, plus a report that lists 78 planned scenario runs, all of them not flown yet ([report](../reports/flight-sim/README.md)).

## The rest

- **Drag and the chute.** The math the C++ plugin will do: drag against the wind from the sizing model's drag area, and a canopy sized from Fruity Chutes' rating (2.5 kg at 4.6 m/s) that opens after a guessed 0.2 s ejection and 1 s of filling.
- **Power afterwards.** Logged rotor speeds become current through the sizing model's own battery model. A synthetic hover lasts as long as the sizing model says, within 1%.
- **The safety monitor's triggers.** A Python reference version: a drop, a tumble and a flip trigger; a punch-out, a throttle chop shorter than its window, a fast yaw and a hard lean don't.
- **Grading.** Every scenario's checks, from hover drift to the parachute's order of events. Building it caught a bug in my own definition: the chute's "settled" descent has to stay settled, or free fall counts as settled on its way past the steady rate.
- **The report and a Rerun replay.** The CAD drone flies its logged path, with its height, speed and motors plotted next to it.

## Next

Tasks 9 to 12 need Ubuntu in WSL2: installing PX4 v1.17.0 and Gazebo Harmonic, building the drag plugin, the runner, then every scenario in every combination.
