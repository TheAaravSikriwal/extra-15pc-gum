# The test plans

*Generated 2026-10-21 by `pcs14 package`. Bench checks first, props off, in this order; then the first flights, tethered first. Each check says what passes. A check that fails stops everything after it.*

## On the bench, props off

### First power

| Check | Passes when | Safety rule |
|---|---|---|
| The pack through a smoke stopper (a bulb or a fuse in series) on the XT60. | The bulb glows and dims as the ESC's capacitors charge, then stays dim. A bulb that stays bright is a short: unplug at once and go back to the wiring guide's checks. |  |
| The supplies, with a meter: the BEC's 5 V at a module socket, the flight controller's 5 V, the 3.3 V regulators. | 5 V rails between 4.9 and 5.3 V; 3.3 V between 3.2 and 3.4 V. |  |
| The idle current, on the pack's lead. | Under 1 A with the modules off; write it down, it's the avionics' real draw. |  |

### The radio and the kill switch

| Check | Passes when | Safety rule |
|---|---|---|
| Bind the receiver to the transmitter, and set the kill switch on its own two-position switch. | The flight controller sees every stick and the switch. |  |
| The transmitter switched off with the drone armed, props off. | The flight controller's RC failsafe fires (land, or as set) within a second. |  |
| Arm, raise the throttle a little, flip the kill switch. | Every motor stops at once and stays stopped until the switch goes back and the drone is re-armed. | My transmitter and kill switch override everything |

### The motors, props off

| Check | Passes when | Safety rule |
|---|---|---|
| PX4's motor test, one motor at a time. | Each spins in its place (1 front right, 2 back left, 3 front left, 4 back right) and the right way; swap any two of a motor's three wires to reverse it. |  |
| Each prop on a prop balancer before it ever goes on. | It sits level at any angle. The arms ring sideways close to what an unbalanced prop shakes them at in a hover (the structure report). |  |
| The current at a hover's throttle, all four, props off. | A few amps at most: props off, there's no load. This is only a smoke check. |  |

### The sensors

| Check | Passes when | Safety rule |
|---|---|---|
| The accelerometer, gyro and compass calibrations in QGroundControl, and the attitude on its screen as the drone is tipped by hand. | Tip the nose down and the display's nose goes down; the same for each axis. |  |
| The TF-Luna, held over the floor at known heights. | Within 6 cm under 3 m, and 2% beyond, its datasheet's accuracy. |  |
| The GPS outdoors with a clear sky. | A 3D fix with ten or more satellites. |  |
| The Remote ID module, with a phone app that reads Remote ID (Drone Scanner, or the FAA's list of apps). | The phone shows the module's serial number and the drone's position. |  |

### The safety monitor

| Check | Passes when | Safety rule |
|---|---|---|
| With the motors spinning slowly (props off), the kill switch through the safety monitor alone (the flight controller's own kill path disabled for the test). | The motors stop: the switch reaches them through both boards. | The kill switch reaches the motors through two separate boards |
| The Teensy unplugged while the motors spin slowly. | The motors keep spinning: a dead safety monitor never stops the drone. | If the safety monitor loses power, the drone keeps flying |
| A monitor cut, with a meter on the ESC's signal lines and on the main power. | The signal lines go quiet; the main power never drops. | The safety monitor cuts the ESC signal lines, never the main power |
| The monitor's automatic triggers, shaken and dropped by hand onto a cushion with the motors off. | The log shows each trigger firing, and no cut: shadow mode. | The automatic triggers stay in shadow mode until they've shown zero false triggers |
| The flight controller halted in a debugger with the motors spinning slowly. | The motors stop within the monitor's 0.25 s timeout plus the ESC's own DShot timeout: never stuck at the last throttle. | A hung CPU means the motors stop |

### The companion computer and the parachute

| Check | Passes when | Safety rule |
|---|---|---|
| V's Pi unplugged with the drone armed, props off. | The flight controller's companion-lost failsafe fires, and it keeps flying its own modes. | The flight controller never depends on the companion computer |
| With P fitted: the chute switch, props off, the canopy out of its tube and the release watched. | The motors stop first, then the release servo moves; the log shows the order. Without P fitted the switch does nothing. | The motors cut before the parachute deploys |
| A plan from plain English, never approved, sent to the drone. | It doesn't fly. Only an approved plan the checker passed can. | The LLM never commands the motors |

## The first flights

PX4 first, then my firmware; tethered first, then free; in the `us-recreational` profile, with the props checked before every flight.

| Flight | Passes when |
|---|---|
| PX4, tethered: a hover at 1 m for 30 s, the tether shorter than the props' reach of anything, in a field with nobody inside 30 m. | It holds level and its height; the current stays under the hover current below; a gyro log for the vibration. |
| PX4, tethered: small stick steps in roll and pitch, then three stick doublets (a quarter stick each way, a quarter second). | It settles without oscillating. The doublets' log goes to self-tuning's fit. |
| PX4, free: hover at 3 m, then 10 m, in position mode. | It holds within a meter; the pack's voltage sags no more than the sizing model says. |
| PX4: the failsafes, one at a time, high enough to recover: the transmitter off (return), the pack's low-battery warning (on a part-used pack). | Each does what it's set to. |
| My firmware, after its register-level drivers pass on the bench against PX4 on the same board: the same tethered hover, then everything above again. | The same passes as PX4's. |

The hover current each combination should draw at most, from the electrical report's pessimistic hover at the reserve (a full pack draws less):

| Combination | Hover |
|---|---|
| base | 14.6 A |
| V | 17.4 A |
| P | 16.9 A |
| C | 20.0 A |
| mission | 22.2 A |
| V+C | 22.8 A |
| P+C | 22.3 A |
| max | 25.1 A |

## The unproven list's measurements

What the sims can't prove, and the first thing to measure for each, from decisions.md and every report. Most fit into the checks above; the rest need a thrust stand or a day of their own.

### The whole drone

| What the sim can't prove | First to measure |
|---|---|
| Real thrust and efficiency (manufacturer data runs ±15–20%) | One motor and prop on a thrust stand |
| Vibration reaching the IMU, and the filtering it needs | A gyro log with the props spinning |
| Motor and ESC heat in real air | Temperatures after a full hover |
| The vortex ring state (Gazebo doesn't model it) | Careful descent tests |
| Li-ion in the cold, and as it ages | A pack discharge test |
| Real radio range with trees and terrain | A walk-out range test |
| Compass interference from the power wires | Compass readings against throttle |
| Solder joints, connectors and tolerances | The bench checks |
| Forward-flight power, especially the drag the props add at speed (see the honesty check below) | A GPS-logged cruise at a steady speed, with current logged |
| The chute's opening height: Fruity Chutes' chart puts the Harrier's canopy at 52.5 ft (16 m) at least, against the 10 m the sim saved it from on a guessed 1 s opening | Fruity Chutes' own numbers, then a drop test with a dummy weight |

### Electrical

| What the sim can't prove | First to measure |
|---|---|
| A dead short in the battery leads. Nothing electrical stops it; only the leads' routing and sleeving protect against it. | Inspect the leads' routing and sleeving after every crash and every pack change. |
| The motor cut board's two undocumented 1 kOhm resistors. Check them with a meter; pull-ups would make the board fail the wrong way, which the added pull-down only partly covers. | Measure them with a meter before the board goes in. |
| Powering the Pi 5 through its GPIO 5 V pins, which Raspberry Pi's docs don't describe. | The Pi at full load through its GPIO pins on the bench, its own undervoltage flags logged. |
| The Pi 5's highest safe input. Raspberry Pi publishes only a 5.1 V supply and the 4.63 V undervoltage warning, so its 5.19 V from the BEC is checked against USB's 5.25 V ceiling, with no margin. | The BEC's output at the Pi's pins under full load, with a meter; then ask Raspberry Pi. |
| The ESC cable's re-pinning: Holybro doesn't say which end of its plug is pin 1. | Find pin 1 with a meter against the ESC's pads before the cable is cut. |
| Whether the ARK FPV terminates its CAN port. If it does, the harness's terminator at that end comes off. | CAN_H to CAN_L on the bare board: 120 ohm means it terminates itself. |
| The XT60's contact mass, a 2.5 g guess. The firmware's heat limit and the burst check both rest on it: heavier contacts give the burst more time. | Weigh a contact; and the XT60's temperature after a burst, with a thermocouple. |

### Flight sim

| What the sim can't prove | First to measure |
|---|---|
| The parachute's descent rate. Its drag comes from Fruity Chutes' own rating, so the sim only repeats it; the drop checks the order of events and the height lost. | A drop test of the chute with a dummy weight of the drone's mass, filmed against a tape to time its descent, before the chute ever flies on the drone. |
| The payload grab. Gazebo's attach joint stands in for the claws, which are a placeholder anyway. | Waits for the claws' design. |
| My firmware's current cap and the XT60's heat limit. This is PX4, which has neither, so the motors are held at their worst-case top speed instead. | On the bench, tethered with the props on: the current at full throttle, logged, and the XT60's temperature after a burst, with a thermocouple. |
| The props' in-plane drag, their rolling moment and the motors' spin-up times, which are PX4's x500 values. | One motor and prop on a thrust stand: thrust and current through the throttle, and the spin-up time from a step. |
| Body drag beyond a frontal-area estimate, until the wind tunnel side track has real tables. | A GPS-logged cruise at a steady speed in still air, with the current logged. |
| Vibration, and anything else a real IMU sees that clean Gaussian noise doesn't. | A gyro log with the props spinning, tethered: its spectrum against the arms' frequencies and the props' speeds. |

### Modules in sim

| What the sim can't prove | First to measure |
|---|---|
| The canopy's timing. Fruity Chutes publishes no ejection or opening time, so the 0.2 s and 1.0 s the sim uses are my guesses, and the lowest height the chute saves the drone from rests on them (the table under the drop heights). | Fruity Chutes' own numbers, asked for; then a drop of the canopy with a dummy weight, filmed, to time its opening. |
| The opening jolt. The sim's canopy grows in a straight line and never overshoots, which real canopies do as they fill, so its number is low. The bound uses Knacke's infinite-mass opening coefficient, which is high for a drone this light under a canopy this big. The real number is between them. | A load cell inline on the riser, in the same drop. |
| A hung flight controller here is a frozen process. A real one could hang with its DShot outputs in any state, which the safety monitor's takeover of the lines has to win against; that's tested on the host, not on a board. | On the bench, props off: the ARK FPV halted in a debugger, and the safety monitor taking the ESC lines and stopping the motors. |
| HaLow's range: line of sight over flat ground, with a 10 dB margin standing in for the drone's body, multipath and a laptop held low. No trees, hills or buildings. And the radio's numbers are Morse Micro's for its own module, not Heltec's for its card. | A walk-out range test with the drone on a 10 m mast, logging the link's rate against the distance. |
| The companion computer's comparison is from published numbers, not measured on a board. | The Pi 5 running the video encode and the flow estimate, its CPU load and temperature logged. |

### Smart features

| What the sim can't prove | First to measure |
|---|---|
| Gazebo's rotors don't feel the air: no cheaper forward flight, no lift from rising air on the rotors, no vortex ring state. So the turn-back warning was checked against the sim's power, not a real pack's; soar mode's real saving (about 76 W in a 4 m/s column, by momentum theory) is a number, not a measurement; and the spiral descent's whole reason for being, keeping out of its own downwash, can't be shown here. | The forward-flight power from a GPS-logged cruise with the current logged; a hover in a known updraft (a slope on a windy day) for soar mode; careful descent tests for the vortex ring state. |
| Wind sensing reads the sim's wind exactly because the estimate and Gazebo use the same drag formula. A real drone's drag area and its lean in gusts will make it worse. | A hover beside an anemometer on a mast, the two compared. |
| Self-tuning's 0.3% is a clean sim: motors that follow a first-order lag exactly, a gyro with little noise, no blade flapping or rotor damping. A real drone will do worse, and the fit runs on the ground from the log for now, not on board. | Three stick doublets, tethered and logged, the fit's inertia against the CAD's and against a swing test of the frame on a bifilar pendulum. |
| GPS-free flight's estimate flew over a made-up textured field at 3 m/s and 6 m up, with the sim's true attitude plus noise. No motion blur, no rolling shutter, no light changing, no grass moving. At 15 m/s the frames stopped matching (12.6% drift). The TF-Luna it needs for its height reads to 8 m at best, less in sunlight. And it isn't in the loop yet: my firmware doesn't fly on it. | The same rectangle at 3 m/s over grass, GPS logged but not used, the estimate against it. |
| The maps are orthomosaics from known poses over flat ground: no heights (OpenDroneMap isn't installed), tall things lean on the map, and V's camera had to point straight down, which its bracket can't do (it's tipped 30 degrees for the live video). | A mapping run over a field with markers whose spacing is measured with a tape. |
| Change detection and the safe spots ran on a world of flat colors. Real ground has texture, shadows that move with the sun, and grass that changes between flights. | The same mapping run on two days over the same field, with one thing moved. |
| Object detection ran on colored boxes, not real things: the model calls them cubes and green rectangular objects. It drew a box around the whole frame on an empty one. And it ran on the PC's RTX 3060; how fast the laptop's integrated graphics runs it is unknown. | The model on the real camera's recorded video, scored against boxes drawn by hand, and its speed on the laptop. |
| The plain-English missions' local model, asked for a point 60 m west of home, wrote one north and east. The checker passed it because it was safe. Only my approval, on a map, can catch a plan that's safe but wrong. | A log of what the model gets wrong over many requests; every plan drawn on the map before it's approved. |
| The Meshtastic relay is a link budget over flat ground with a 10 dB margin: no trees, no hills, no other radios. Where the node lives (V, Base or its own module) is still open. | A walk-out range test with two nodes, one on a 10 m mast, then one on the drone. |

### Structure

| What the sim can't prove | First to measure |
|---|---|
| The laminate: iFlight publishes nothing about the Nazgul's carbon, so its stiffness runs 40 to 70 GPa and its strength from 400 MPa, typical woven plate. | A tap test on a spare arm, clamped as on the frame, with a phone's accelerometer or a microphone: its ring frequency gives the stiffness. |
| The clamp: where the arm's free length starts depends on how tightly the plates hold it, swept 10% either way here. | The same tap test on the built frame. |
| The heat-set inserts' pull-out and the printed cradle and rail: guesses, and the weakest links between the chute's riser and the frame. | A hang test before P flies: 26 kg (the jolt's bound) from the riser's point on the mounted cradle for a minute, then 39 kg (one and a half times); nothing cracks, creeps or pulls out. |
| Crashes, and the legs' TPU under a hard landing: no FE model without CalculiX. | Drop tests of the legs with a dummy weight, from 0.25 m up to 1 m. |
