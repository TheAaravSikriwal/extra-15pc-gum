# sim/

Layers 3 and 4, the flight sim's hand-written part. Everything else in it is generated: `pcs14 flight-sim` writes each combination's Gazebo model, world and PX4 parameters from `design/`, the sizing model and the CAD (the code is in `src/pcs14/flight/`), and the scenarios live in `src/pcs14/flight/scenarios/`. PX4 runs its stock x500 airframe with those parameters loaded over it, and my own firmware flies the same models through its Gazebo bridge.

- `plugins/pcs14_drag/`: a Gazebo Harmonic plugin for the body's drag and, in P, the parachute: its ejection delay and its canopy opening. It does exactly what `src/pcs14/flight/drag.py` does, and that file's tests are its specification.

The results are in the [flight sim report](../docs/reports/flight-sim/README.md).
