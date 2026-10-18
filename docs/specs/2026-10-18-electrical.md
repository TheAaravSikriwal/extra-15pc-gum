# Electrical design (step 3)

*Started 2026-10-18 with the electrical talk (step 3a). Like everything else here, it will change once real numbers show up.*

## What this step has to produce

From the [roadmap](../roadmap.md): no custom PCB, so everything is off-the-shelf boards and breakouts. A system schematic in KiCad and harness diagrams from code (WireViz); a pin map for the flight controller and the Teensy; the power design (the battery connector, the ESC, the 5 V supplies, the current sensor, fuses, wire gauges and connector ratings); checks (voltage drop from the CAD's wire lengths, peak and continuous currents in every setup, rough heat, the power budget for every module combination); and an ngspice simulation showing the safety monitor's switch passes bidirectional DShot, including with the Teensy unpowered.

**Done when:** every connection is specified, and every current, voltage and temperature is inside its rating with margin.

## Settled in the electrical talk

Seven questions, one at a time: where the design lives, the flight controller board, the module bus, power, the motor cut circuit, the check limits, and watching it.

**Where the design lives (2026-10-18): one connection list, in code, that generates everything.** `design/electrical.yaml` lists every board and its pins, every connector, every wire with its gauge, and which wire route in `design/cad.yaml` it follows. From that one file the code generates the WireViz harness diagrams, the pin map tables, every check (currents, voltage drop, heat, the power budget), a KiCad schematic (each board a block with its pins, joined by net labels, so KiCad's electrical rules check can run on it), and the wires colored by current in the CAD's 3D view. **Why:** it's the CAD's approach again. One place to change a connection, everything regenerates, it can be tested, and the diffs are readable. A schematic of blocks and net labels looks plainer than a hand-drawn one, and that's the cost.

**The flight controller (2026-10-18): the ARK FPV, replacing the Kakute H7.** The board has to carry the receiver, the GPS, the companion computer and the Teensy on full serial ports, the module bus, the lidar, and four bidirectional DShot outputs. The Kakute H7 V1.5 exposes four full serial ports, and PX4 already uses all of them, so the Teensy link would mean taking over the debug console; it has no CAN at all, and its SWD is bare test points. The ARK FPV has five full serial ports (one is PX4's console) plus two receive-only ones, one CAN port, bidirectional DShot on all motor outputs under PX4, 5 V and 12 V supplies, a 3S to 12S input, and a JST-SH debug plug for SWD. It ships with PX4, from a company that develops it. **Why:** it fits every link with room left over, keeps DroneCAN open for the modules, and the debug plug will matter when my own firmware goes on. **Cost:** $195 against $85, it's on backorder (nothing gets bought by default, so that matters less here), and the cable to the Tekko ESC needs re-pinning, because the ESC plugs' pin orders differ. Swapping it into the catalog and the CAD is a task in the electrical build.
