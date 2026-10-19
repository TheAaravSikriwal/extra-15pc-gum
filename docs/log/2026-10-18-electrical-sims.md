# 2026-10-18: Watching the safety switch in ngspice

*PC, Windows side. Step 3c, the second half of task 8 through task 12.*

Last time the checks found their first problems. This stretch was about drawing the wiring and simulating the one circuit I trust least: the switch that lets the safety monitor take the ESC lines away from the flight controller.

## Routes for every wire

Any wire longer than a short jumper now has a route in the CAD: 16 new ones, from the battery leads to the chute's signal lines. Each route's thickness comes from the wires inside it, using the usual rule of thumb for a round bundle (about 1.15 times the square root of the sum of each wire's diameter squared). `pcs14 electrical --update-cad` writes those thicknesses into the CAD settings, and all eight module combinations still pass the CAD's prop clearance checks with the fatter bundles.

## DShot, by hand first

DShot is how the flight controller talks to the ESC: 16-bit frames at 600 kbit/s, an 11-bit throttle, one bit asking for telemetry, and a 4-bit checksum. In the bidirectional version the ESC answers on the same wire with the motor's period, which the firmware turns into RPM. I wrote an encoder and decoder for both directions and checked them against a frame worked out by hand (throttle 1046 is 0x82C6) before trusting them with anything simulated.

## The switch, simulated

The circuit: the flight controller's DShot pin runs to a TI TS3A5018 analog switch, and the switch runs to the ESC. The Teensy (the safety monitor) listens to the line through a small buffer, and can flip the switch to connect its own pin to the ESC instead and send stop frames. That last part matters because AM32 holds the last throttle for about half a second when its signal just disappears.

I modeled one channel in ngspice: the pins with their capacitance, the pull-ups, the wires at their real lengths from the connection list, the switch's on-resistance and capacitance, and the ESC sending its reply back. Then six cases, each decoded by the DShot code from the simulated voltages.

| Case | The ESC got | The flight controller read back | Result |
|---|---|---|---|
| Teensy on, listening | 1046, 1046 | 1232, 1232 | Pass |
| Teensy unpowered | 1046, 1046 | 1232, 1232 | Pass |
| Teensy cutting | 0, 0 (stop) | nothing | Pass |
| Teensy takes over mid-frame | 1046, one broken frame, 0, 0 | nothing | Pass |
| No buffers, Teensy unpowered | nothing | nothing | Fails, as it should |
| The receiver line, Teensy unpowered | clean | | Pass |

The slowest edge at the ESC takes 2.4 ns, against a bit that's 1667 ns long. The ESC reports a 1234 µs period and the flight controller reads 1232: the reply packs the period into a rounded format, so that's DShot itself, not the circuit.

The "no buffers" case is there to prove the buffers earn their place. An unpowered chip's pins have protection diodes to its own supply, and a dead supply is close to 0 V, so a dead Teensy sitting straight on the line clamps it low and nothing gets through. With a buffer that stays quiet when unpowered, the line doesn't notice.

The sim also taught me something about the firmware. My first model had the Teensy send its stop frames and leave the line floating in between. That fails: bidirectional DShot idles high, and a floating line drifts. A flight controller holds the line high between frames and lets go only while the ESC answers, so the Teensy has to do the same once it takes over. That's now a requirement for the safety monitor's firmware in step 5.

What this can't tell me: the part models are generic ones built from datasheet numbers, and there's no ground bounce or noise from 90 A of motor current in the same frame. A clean sim means the design isn't wrong on paper. It doesn't replace a scope on the real thing.

## Diagrams and a schematic

The connection list now draws its own harness diagrams through WireViz, writes pin maps for the flight controller and the Teensy (what every pin does and where it goes), and draws the power tree from the pack down, with typical and worst currents on each branch. WireViz had two quirks: connector names can't contain a period, and a hex color prints as a label instead of a color, so the DShot wires use WireViz's turquoise code.

It also writes a KiCad schematic: every board a block with its pins, joined by net labels, and unused pins flagged. KiCad's own electrical rules check finds nothing on it: 34 blocks, 78 nets, zero violations. It's a wiring schematic, not a circuit board. Nothing here needs a custom board yet.

## Rerun

The talk said Rerun would color each wire by its current. In the build I colored it by how much of its heating limit it uses instead: its temperature rise over the air, against the rise to its insulation's limit. Current over the continuous rating sounds simpler, but in the 10 second burst every power wire runs past its continuous rating while staying well under its temperature limit, so they'd all glow magenta while passing the check. The heating share goes magenta only when a check fails.

The answer it shows is that almost nothing works hard. At Max's burst, the battery leads use 29% of their heating limit and the motor leads 13%. The one thing in magenta is the XT60, at 147% of its limit by the end of the burst, which matches the open finding from last time. It crosses its limit about 4.4 s in.

Rerun shows one timeline at a time, so the recording has three tabs: the wires stepping through every combination and flight case, the switch sims as scope traces, and the temperatures through the burst. Two smaller fixes along the way: the burst curves took 142 seconds because each point reran the whole burst from zero (now 3 s, one pass), and the scope traces were 58 MB at one point a nanosecond, so they keep only the points where the voltage moves (7.6 MB, edges intact).

## Next

Task 13 is the report and the full `pcs14 electrical` command: every check in every combination, the diagrams, the schematic, the scope traces, every estimate and unknown, and stills in the post sizes. Then step 3d: the wiring's real weight, and the open findings (the release servo's voltage, the Pi's ceiling, the XT60 in the burst, and Max's weight).
