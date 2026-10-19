# Implementation plan: electrical design

*Step 3b, written and OK'd 2026-10-18. It turns the decisions in the [spec](../specs/2026-10-18-electrical.md#settled-in-the-electrical-talk) into code, one test-first task at a time.*

## What it builds

The electrical layer of `pcs14`. It reads the catalog, `design/build.yaml`, the CAD's wire routes and one connection list, `design/electrical.yaml`, and works out every current in every module combination and flight phase. Then it checks every wire, connector, fuse and supply against its rating, runs the safety monitor's switch through ngspice, and generates the harness diagrams, pin maps, a KiCad schematic, the report and the pictures. Change a connection and everything regenerates. Every run plays in Rerun.

## Where things go

```
src/pcs14/electrical/
  model.py        design/electrical.yaml as objects: boards, connectors, wires, rails, fuses, harnesses
  validate.py     the connection list's own rules: every wire end is a real pin, one driver per line,
                  no supplies tied together without diodes, logic levels that match, a route for every wire
  loads.py        the current in every wire, for every module combination and flight phase
  checks.py       currents, voltage drop, supplies, fuses, and the list of checks resting on estimates
  thermal.py      wire and connector temperatures, steady and through the 10 s burst
  dshot.py        DShot600 frames, bidirectional, with the ESC's RPM reply, to drive and decode the sims
  spice/          the ngspice netlists, the runner and the waveform checks
  wireviz.py      harness diagrams in the project's look
  pinmap.py       pin map tables for the flight controller and the Teensy, plus the power tree
  kicad.py        the schematic (blocks and net labels) and KiCad's electrical rules check
  report.py       the electrical report and electrical.json
src/pcs14/viz/    the electrical Rerun timeline joins the sizing and CAD ones
design/electrical.yaml   the connection list and the check numbers
outputs/electrical/      raw ngspice output and diagram sources (gitignored)
docs/reports/electrical/ the report, electrical.json, the schematic, diagrams and stills (committed)
```

**Part facts live in the catalog, connections live in the list.** Same split as the CAD: each part gets an `electrical` block in the catalog (its pins and connectors, its supply range and draw, its outputs if it's a supply, its ratings if it's a connector, fuse or wire), every number with its source and the estimates named. `design/electrical.yaml` only says what connects to what, with which wire, along which CAD route.

**The schematic gets committed.** A `.kicad_sch` file is small text, and someone browsing the repo can open it in KiCad. Its IDs come from the names of things, not random numbers, so regenerating it only changes what really changed.

**New dependencies:** WireViz (GPL-3.0, the same license as this repo), which needs Graphviz installed; ngspice, called as a program; and KiCad's command line, for the electrical rules check and the schematic's pictures. Every test that needs one of them skips cleanly when it's missing, and CI installs them on Linux. Each gets pinned by the task that first needs it.

**Units:** volts, amps, ohms, watts, meters and seconds inside. Millimeters, milliohms and AWG only in the files and the report.

## What the parts research found

A research pass on 2026-10-18 went through every new part and every pin the connection list needs.

| Part | Pick | Mass | Why this one | Existing CAD |
|---|---|---|---|---|
| Flight controller | ARK FPV | 7.5 g | Settled in the talk. 36 x 36 mm on 30.5 mm holes. Its 5 V supply is 2 A, and the board uses 0.5 A of it, which answers the talk's open question | Official STEP, no license stated, so cache only |
| GPS and compass | ARK GPS (DroneCAN): u-blox NEO-M9N, BMM150 compass, barometer | 16 g | The lightest DroneCAN GPS with a compass still sold. The Matek M9N-G4-3100 ties at 16 g, but neither PX4 nor Matek documents it working with PX4. **8 g heavier than the M10Q it replaces, see below** | Official STEP, BSD-3 |
| Servo nodes (P and C) | ARK CANnode | 5 g each | Runs PX4's own node firmware, its terminator is a software setting, and ARK documents the PX4 servo setup. The Matek CAN-L4-PWM is 1.5 g lighter, but it counts its outputs from 1 where PX4 counts from 0, and Matek nodes have shipped with a fixed terminator | Official STEP, BSD-3 |
| Motor cut switch | TI TS3A5018 quad two-way switch, on an off-the-shelf CJMCU-5018 board | not published | Four lines, one control, and with its control pins low it connects the flight controller side. That's TI's own reference wiring | None |
| Listening buffers | Six TI SN74LVC1G125 on SOT-23 adapter boards | not published | They specify leaking under 10 µA with their supply off. The quad SN74LVC125A doesn't specify that, so it was out | None |
| P's chute switch | Nexperia 74LVC1G157 on a SOT-23-6 adapter, with a small 3.3 V regulator | not published | TI doesn't make a 1G157. Nexperia's specifies the same unpowered leakage and reads 3.3 V logic at a 3.3 V supply | None |
| Diodes | BAT54C for the Teensy's two feeds; a 1 A Schottky for the release servo's backup feed | 0.008 g (BAT54C) | The BAT54C is rated 200 mA continuous, fine for the Teensy and too little for a stalling servo | n/a |
| Module connector | Amass XT30U (5 V) plus an 8-pin JST-GH (CAN, its 5 V, the Pi's serial pair, the chute's two lines) | from the catalog | Amass rates the XT30U at 20 A and JST rates GH contacts at 1 A on 26 AWG | n/a |
| Branch fuses | Littelfuse MINI blade fuses | 0.57 g each | Published resistance and I²t for every rating, which the fuse check needs. The holder's weight isn't published | n/a |
| Cell links | Fuse wire, sized by Onderdonk's equation | from the wire | No maker publishes fusing data for cell links by size, so these get sized from the equation and go on the unproven list | n/a |
| Wire | Silicone, 200 °C insulation | from the table | Resistance from the US standard copper wire tables (NBS Handbook 100), outer diameter and mass from a maker's sheet | n/a |

**The GPS, and the weight.** A DroneCAN GPS costs 8 g over the M10Q, and the servo nodes add 5 g each. Adding up every new part with rough figures, Mission goes from 2293 g to about 2309 g, which still passes (its pessimistic hover drops from 21.6 to about 21.4 min, against 21). Max goes from 2493 g to about 2514 g, over its 2.5 kg limit. The alternative is ARK's SAM GPS MINI (u-blox SAM-M10Q, IIS2MDC compass, 8 g, the same as the M10Q) on a serial port. That brings Max to about 2506 g, still over, and its six wires have to pass through the module connector, which grows from 8 to 12 pins. The wiring's real weight (step 3d) replaces a 45 g guess, so the final number could move either way. Max only gets reported, it doesn't have to pass (decided 2026-10-17), but I picked these parts because they kept Max under 2500 g. **Decided 2026-10-18: the ARK GPS on DroneCAN.** The lighter serial GPS doesn't get Max under the limit by itself, and it would have cost four more pins in the module connector and a special case in the bus design. Max gets its final number in step 3d.

**Pins, from the makers' docs:**
- **The flight controller's serial ports:** the receiver on the RC port, the lidar on the GPS port (free now the GPS is on CAN), the Pi on TELEM1, the Teensy on the VTX connector's UART5, the ESC's telemetry on UART4's receive-only pin. The debug plug stays PX4's console. One receive-only port is left over.
- **The ESC cable:** the ARK FPV has a 1.25 mm JST-GH 8-pin and the Tekko32 a 1.0 mm 8-pin, in different orders, so the cable is GH to SH, re-pinned. Holybro's pin map doesn't say which end is pin 1, so the cable assumes the battery end and marks it as an estimate for the bench checklist.
- **The current sensor:** the Tekko32's scale depends on its board revision (120 on V1.9, earlier ones 168 or 110), so the build package has to say "check the revision". My firmware's 90 A cap depends on this sensor.
- **The Teensy:** pins aren't 5 V tolerant, its 3.3 V output gives 250 mA, and its eight UARTs and FlexPWM pins are all on PJRC's card. The one public Teensy DShot library (teensyshot, GPL-3.0) is for the 4.0 and doesn't do bidirectional DShot, so step 5 writes my own: the stop frames have to be in the same inverted DShot AM32 locked onto at power-up.
- **The Pi 5:** MAVLink on UART0 (GPIO 14 and 15), with the boot console kept off those pins. Raspberry Pi's docs don't describe powering through the GPIO 5 V pins, which goes on the unproven list.
- **The lidar:** TF-Luna takes 3.7 to 5.2 V, so it sits on the flight controller's 5 V, not the BEC's 5.2.

**Things the build has to solve:**
- **CAN termination:** a CAN bus needs exactly two 120 Ω terminators, one at each end. The GPS can't be an end, because it leaves with V. So the bus runs from the flight controller through the module mount to a terminator fixed at its far end, with a short stub to each module slot, and every node's own terminator off. ARK doesn't say whether the ARK FPV terminates its CAN port; if it doesn't, a second fixed terminator goes at that end.
- **One connector per module slot:** the CAD has one module connector, and V, P and C each need one.
- **The chute latch has to stay shut when its servo goes quiet.** Some servo nodes drop their outputs 200 ms after commands stop. That's for the parachute module's design in step 6, but the electrical report flags it.
- **The switch fails closed, not open.** If the motor cut switch itself loses power, it blocks the lines and the motors stop. It's powered from the flight controller's side, so it shares the flight controller's fate rather than the Teensy's, and it goes on the failure list for the build package.

**Tools:**
- **WireViz 0.4.1** (GPL-3.0). It can set a black background but not the text color, so the diagrams get light boxes with dark text on the project's black.
- **Graphviz:** Ubuntu 24.04 ships 2.42 and Windows has 16.1, so the tests check what goes into WireViz, never the pictures byte for byte.
- **ngspice:** run as `ngspice -b`, with its plain-text output read by my own small reader. PySpice is unmaintained, and InSpice's license is unclear (GPL or AGPL, depending on where you look). Windows gets ngspice 47 from the official archive, and CI gets 42 from Ubuntu's packages.
- **KiCad 10:** `kicad-cli` runs the electrical rules check and exports the schematic to SVG and PDF. The schematic file comes from my own small writer: the Python libraries that write KiCad 10 schematics came out in the last few weeks, and SKiDL now pulls in InSpice. CI installs KiCad in its own job.
- **Rerun:** scope traces work as scalars on a timeline counted in nanoseconds.
- **Installs on the PC,** each one asked before it happens: Graphviz (winget), ngspice 47 (SourceForge archive) and KiCad 10 (winget, a big download).

## The tasks

Each one is test-first: write the tests with hand-checked numbers, make them pass, commit and push with CI green.

| # | Task | What the tests check |
|---|---|---|
| 1 | **Tools in:** WireViz, Graphviz, ngspice and KiCad's command line pinned, the `pcs14.electrical` skeleton, a `pcs14 electrical` command, CI installing the tools | It imports, the command runs, and every tool-dependent test skips cleanly when its tool is missing |
| 2 | **The catalog's `electrical` block:** pins and connectors, supply range, typical and worst-case draw, supply outputs (voltage, continuous and peak current), ratings for connectors, fuses and wire, a wire table per gauge, every number sourced and the estimates named | A good block loads. A pin on a connector that doesn't exist, or an estimate naming a field that doesn't exist, fails with a clear message |
| 3 | **Fill in the catalog:** the ARK FPV in place of the Kakute H7, the DroneCAN GPS in place of the M10Q, the two servo nodes, the module connector parts, the safety monitor's switch board, buffers and diodes, the one-channel switch in P, the branch fuses, the cell links and the wire table, plus an `electrical` block for every part in the build | Every part the connection list needs has an `electrical` block, every source has a date, and the numbers agree where they overlap (each part's typical draw against the power the sizing model already counts, the wire table against the copper standard) |
| 4 | **`design/electrical.yaml` and its rules:** every board, connector and wire (gauge, harness, CAD route), the rails and what feeds them, the fuses, and the check numbers from the spec | Made-up lists that break each rule: a wire to a pin that doesn't exist, two drivers on one line, two supplies tied without diodes, 5 V into a 3.3 V pin, a wire with no route, a CAN bus without exactly two terminators in some module combination. The real list passes |
| 5 | **Loads:** the current in every wire for every module combination and flight phase. The main path comes from the sizing model (hover, cruise and the burst at the cap, nominal and pessimistic, full and at the reserve); the 5 V rails from the catalog's draws, typical and with every servo stalled | Made-up drones worked by hand (a series path and its ground return, both kinds of regulator, a diode-OR, parallel grounds, a fuse's drop), then the real build: the battery leads carry exactly the sizing model's current, and the BEC carries what the talk worked out (about 2.5 A typical and 5.6 A worst in Max) |
| 6 | **The checks:** continuous current at 80% of each rating or less; voltage drop (2% on the main path, every load inside its range with 0.1 V to spare, the Pi above 4.75 V); supplies (80% typical, peak rating for the worst case); fuses (hold 125%, blow before their wire overheats, the cell links by Onderdonk's equation); the list of checks resting on estimates | Each check on a small case with a hand-worked answer, including one that fails |
| 7 | **Heat:** each wire's and connector's temperature in steady state (I²R heating against cooling from its surface, in 40 °C air) and through the 10 s burst at the cap (from the hottest steady state, with the copper's heat capacity), and the ESC's and motors' currents against their ratings | Hand-worked copper numbers for one wire, steady and transient, and a connector at its rated current landing near its published temperature rise |
| 8 | **The CAD catches up:** the ARK FPV, the DroneCAN GPS, the servo nodes, the module connectors, the safety monitor's boards and the fuses placed; new wire routes (the DShot lines through the safety monitor, CAN and the chute lines up to the modules); every wire's thickness from its gauge; all eight combinations rechecked | The CAD's checks still pass in every combination, and every wire in the connection list has a route |
| 9 | **DShot and ngspice:** a DShot600 encoder and decoder (bidirectional, with the GCR reply); netlists for the switch with the Teensy on, off and cutting, the takeover, the Teensy's listening lines with it off (and once without the buffers, to show why they're there) and the receiver's CRSF line; parts modeled from datasheet figures where there's no SPICE model; the signal checks from the spec | The encoder against frames worked by hand from the protocol docs, the waveform reader on an RC circuit with a known time constant, then every real run passes |
| 10 | **Diagrams and tables:** WireViz harness diagrams in the project's look, pin map tables for the flight controller and the Teensy, and the power tree | Every wire in the list appears in a harness, the pin maps match the list, and the diagrams render (skipped without Graphviz) |
| 11 | **The KiCad schematic:** each board a block with its pins, joined by net labels, with IDs from names; KiCad's electrical rules check | Every net in the list is in the schematic, it reads back the same, and the rules check comes back clean (skipped without KiCad, run in CI) |
| 12 | **Rerun:** the CAD drone with every wire colored by its current, stepping through each combination and flight phase, anything past its limit in magenta; temperatures through the burst; the ngspice runs as scope traces | It writes a recording without a viewer open, and every view opens on the whole run |
| 13 | **The report and the command:** `pcs14 electrical` (with `--live`), the report (every check in every combination, the pin maps, harness diagrams, schematic, scope traces, and every estimate and unknown), `electrical.json`, and stills in the post sizes | The report matches a known-good copy for a made-up design, and `electrical.json` matches the results |
| 14 | **Close the loop (step 3d):** the new parts' weights and the wiring's real weight (from each wire's gauge and length) into the catalog, then the CAD and the sizing model rerun and the targets rechecked | It only touches the parts it should and marks their sources. Then the real numbers get written up, including whether Max still fits under 2500 g |

**One change of order (made during the build, 2026-10-18).** The CAD's tests run on the real build, so swapping parts in `build.yaml` has to land together with their CAD placements, or the checks go red in between. So task 8 splits in two. Its parts half (the ARK FPV, ARK GPS, CANnodes, the safety monitor's boards and the module connectors swapped into the build and placed, with every combination rechecked) runs right after task 3, so the build matches the connection list from task 4 on. Its wire-route half stays after task 7.

**Rerun's coloring (changed during the build, 2026-10-18).** Task 12 colors each wire by the share of its heating limit it uses, not by its current over its continuous rating. In the burst every power wire passes its continuous rating while staying well under its temperature limit, so current would have lit them all magenta while they pass. Rerun shows one timeline at a time, so the wires, the scope traces and the burst temperatures each get a tab.

**Done when:** every connection is specified, every current, voltage and temperature is inside its rating with the spec's margins in every module combination, the ngspice runs show DShot passing with the Teensy on, off and cutting, and the new weights are back in the sizing model with the targets rechecked.
