# 2026-10-17: Not building it (yet)

*PC, Windows side. A big change of direction, and no code.*

I've decided not to build this drone, at least not now. Instead, I'm designing all of it in simulation, in depth, as a research project. Every real part gets modeled and connected to the parts around it, the wiring gets worked out wire by wire, and my own firmware flies it in the sim. The one rule: the research has to be good enough that I could build the drone from it one day.

## What "done" means now

Someone could order the parts list, follow the assembly and wiring guides, flash my firmware, and run the bench and first-flight test plans. And they'd get an honest list of what the simulations couldn't prove, with the first thing to measure for each.

That last part matters. Simulation is great, but it can't tell me everything:

| What sim can't prove | First thing to measure when built |
|---|---|
| Real thrust and efficiency (manufacturer data runs ±15–20%) | One motor and prop on a thrust stand |
| Vibration reaching the IMU, and the filtering it needs | A gyro log with the props spinning |
| Motor and ESC heat in real air | Temperatures after a full hover |
| The vortex ring state (Gazebo doesn't model it) | Careful descent tests |
| Li-ion in the cold, and as it ages | A pack discharge test |
| Real radio range with trees and terrain | A walk-out range test |
| Compass interference from the power wires | Compass readings against throttle |
| Solder joints, connectors and tolerances | The bench checks |

## What changed

- **Nothing gets bought by default, and nothing flies.** The FAA registration, Remote ID and the Part 107 question move into a legal checklist in the build package. Two purchases stay optional: a thrust stand (roughly $100–200), which is the one real measurement that makes everything else more believable, and a $30 Nucleo board to run my firmware on the real chip while the sim feeds it data.
- **Two new layers.** Electrical: every wire, pin and connector, with the currents, voltages and heat checked, and the safety monitor's signal switch simulated as a circuit. Structure: stress and vibration in the arms and mount, because an arm that resonates near the props' speed fills the gyro with noise.
- **The plan is steps now.** Sizing and parts, the virtual drone in CAD, electrical, the flight sim, my firmware, modules, smart features, and finally the build package. Structure, the wind tunnel and the design hunt run as side tracks.
- **The bench build and first flights** became written test procedures in the build package.

What didn't change: the targets, the modules, the whole safety design, my own firmware, and the process (talk it through, spec, plan, then build test-first).

## WSL2 on the PC

Most of the tools run on Windows anyway: KiCad, FreeCAD, Blender, ParaView. Only the flight sim (Gazebo and PX4) and the wind tunnel (OpenFOAM) really want Linux. So instead of rebooting into the PC's Ubuntu side, they'll run in WSL2, a real Ubuntu inside Windows, the same way the laptop already works. The Ubuntu side of the dual boot stays as a fallback for the biggest wind tunnel runs.

## Also added

Object detection on the laptop (#39) made the shortlist: boxes and labels on the live video, with all the thinking done on the laptop so the drone carries no AI hardware. A small, fast detector does the finding, and the LLM answers questions about what it found.

## Next

Turn on WSL2 on the PC, then finally the sizing model discussion.
