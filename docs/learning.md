# What I need to learn

Everything I need to understand to build this thing, roughly in the order I'll need it. Offline time is for this file: reading, watching, doing tutorials. Online time is for building. The two shouldn't get in each other's way.

How it works:
- Each topic says **why it matters for this project**, then gives resources: **watch** (videos), **read** (books, articles, papers), and **do** (tutorials I run myself).
- I tick things off as I go.
- When a new concept comes up while building, it gets added here.
- Papers are listed by full citation. If one is paywalled, I get it through my university library.
- I don't need to finish a topic before building with it. Learning just ahead of the build is the goal.

---

## 1. How a quadcopter flies

*Needed now (step 1), and it never stops mattering.*

How four props make a drone go up, tilt, move and turn: thrust, torque, why yaw comes from spinning two props faster than the other two, and what "motor mixing" means.

- [ ] **Watch:** MATLAB Tech Talks, *Drone Simulation and Control* series (Brian Douglas, YouTube). The best plain-English intro there is.
- [ ] **Read:** Oscar Liang's blog ([oscarliang.com](https://oscarliang.com)) for the practical side of how real quads are put together.
- [ ] **Read:** Quan Quan, *Introduction to Multicopter Design and Control* (Springer, 2017). Chapters on how multicopters work and how they're designed.
- [ ] **Read, later:** Randal W. Beard and Timothy W. McLain, *Small Unmanned Aircraft: Theory and Practice* (Princeton University Press, 2012). The serious version. Dip in when something needs more depth.

## 2. Props, motors and batteries

*Needed now: this is the sizing model.*

How much thrust a prop makes and what it costs in power, momentum theory, motor KV, why bigger slower props are more efficient, and Li-ion vs LiPo: capacity, voltage sag, internal resistance.

- [ ] **Read:** J. Gordon Leishman, *Principles of Helicopter Aerodynamics* (Cambridge University Press), the chapters on momentum theory and hover/forward-flight performance. This is the actual math behind the sizing model.
- [ ] **Read:** Quan Quan's book (above), the chapter on propulsion and design.
- [ ] **Read:** Battery University ([batteryuniversity.com](https://batteryuniversity.com)) on Li-ion basics, discharge curves, and why cells sag under load.
- [ ] **Watch:** Joshua Bardwell (YouTube) on motors, props and Li-ion packs for long-range builds. The practical, real-world side.
- [ ] **Read, if I go deep on the battery model:** Gregory L. Plett, *Battery Management Systems, Vol. 1: Battery Modeling* (Artech House, 2015). There's also his Battery Management Systems course on Coursera (University of Colorado Boulder).

The quick version of two things the first real sweep ran into (2026-10-17):
- **A cell's continuous current rating** is how hard you can pull on it without cooking it. Put cells in parallel and the ratings add up: one P42A is rated for 45 A, so 6S2P is 90 A and 6S3P is 135 A. Big motors flat out can pull more than that, even after the pack sags under the load. The fixes are more cells in parallel (heavier), or firmware that caps the current (less punch on a full pack).
- **Reading below a thrust table's first row** means guessing. Momentum theory says power goes as thrust to the 1.5, but real motors waste a bit more at light load, so that guess reads a few percent low on power.

- [ ] **Read:** HKJ's battery tests ([lygte-info.dk](https://lygte-info.dk)), the discharge curves at different currents for any 18650 or 21700 cell. Watching the curves drop as the current goes up is the fastest way to get a feel for sag and current ratings.

## 3. Aerodynamics basics

*Needed for the aero side track (the wind tunnel).*

Pressure, drag, lift, the boundary layer, wakes, and the Reynolds number: what all those colors in CFD images are actually showing.

The quick version, from a session:
- **Paint on the surface is pressure.** Red is where air slams into the object and pushes back. Blue is where air rushes past and sucks on it.
- **More drag:** a big red front plus a big blue, swirly wake behind it.
- **The lines are the path the air takes,** colored by speed. Smooth lines mean the air slides past cleanly. A tangled mess behind the object is the wake, and wasted energy.

- [ ] **Watch:** Fluid Mechanics 101 (Aidan Wimshurst, YouTube). Explains fluid and CFD ideas visually and clearly.
- [ ] **Read:** NASA Glenn Research Center, *Beginner's Guide to Aeronautics* (free on the NASA Glenn website). Short pages on drag, lift and pressure.
- [ ] **Read, later:** E. L. Houghton and P. W. Carpenter, *Aerodynamics for Engineering Students* (Butterworth-Heinemann). The textbook version.

## 4. CFD (the virtual wind tunnel)

*Needed for the aero side track (the wind tunnel).*

How CFD works: meshes, solvers, boundary conditions, turbulence models (what RANS and k-omega SST mean), convergence, how to tell a good result from garbage, and how props get faked as "actuator disks."

- [ ] **Watch:** Fluid Mechanics 101 (YouTube) on meshing, turbulence models and convergence.
- [ ] **Watch:** József Nagy (YouTube), hands-on OpenFOAM tutorials.
- [ ] **Do:** Lorena Barba, *CFD Python: 12 Steps to Navier-Stokes* ([github.com/barbagroup/CFDPython](https://github.com/barbagroup/CFDPython)). Writing a tiny solver from scratch in Python, so the big one isn't magic.
- [ ] **Do:** OpenFOAM's built-in tutorials, in this order (on the PC):
  1. **cavity**, the hello world
  2. **pitzDaily**, flow over a step
  3. **motorBike**, a motorcycle and rider in a wind tunnel. It produces the classic pressure-and-streamline images. This is the one.
- [ ] **Read:** the OpenFOAM User Guide (free, ships with OpenFOAM).
- [ ] **Read:** Wolf Dynamics' free OpenFOAM training slides (Joel Guerrero). Long, practical, and great offline.
- [ ] **Read, later:** H. K. Versteeg and W. Malalasekera, *An Introduction to Computational Fluid Dynamics: The Finite Volume Method*, 2nd ed. (Pearson, 2007). The standard textbook.

## 5. Showing data well

*Needed throughout, especially for posts.*

Colormaps, color bars, why rainbow colormaps can lie, and how to make charts people actually understand on a phone.

- [ ] **Do:** Kitware's *ParaView Tutorial* (free, on the ParaView website). Then load my motorBike results and make them look like the wind tunnel style.
- [ ] **Read:** Anton Mikhailov, "Turbo, An Improved Rainbow Colormap for Visualization" (Google Research blog, 2019). Why we use turbo.
- [ ] **Read:** Fabio Crameri, Grace E. Shephard and Philip J. Heron, "The misuse of colour in science communication," *Nature Communications* 11, 5444 (2020).
- [ ] **Read:** Claus O. Wilke, *Fundamentals of Data Visualization* (O'Reilly, 2019). Free to read online.

## 6. CAD as code

*Claude writes it, but I want to be able to read it and tweak it.*

How build123d builds solids from code: sketches, extrusions, positions, assemblies, and how mass properties come out of the geometry.

- [ ] **Do:** the build123d introductory tutorials ([build123d.readthedocs.io](https://build123d.readthedocs.io)).
- [ ] **Do:** open one of the generated STEP files in a regular CAD tool and poke around.

The quick version of what the CAD talk (2026-10-17) leaned on:
- **Center of gravity vs center of thrust.** If the weight sits off center, the motors on the heavy side have to push harder to keep the drone level. The CAD judges the offset by how much harder the busiest motor works in a hover.
- **Inertia** is how hard the drone is to spin about each axis. It comes out of the geometry once every part's mass is spread over its shape, and the flight sim needs it.
- **File formats:** STEP is exact CAD geometry that any CAD tool opens. STL and 3MF are triangle meshes for printing and simulation. GLB (binary glTF) is the 3D format for the web.
- **Print materials:** TPU is rubbery and survives hits (legs, GPS mounts). Carbon-filled PETG is stiff and light (brackets, trays).

- [ ] **Watch:** MIT OpenCourseWare, *2.003SC Engineering Dynamics*, the lectures on center of mass and moments of inertia.
- [ ] **Read:** the Khronos Group's glTF overview ([khronos.org/gltf](https://www.khronos.org/gltf/)), for how GLB files carry named parts to the web.
- [ ] **Read:** Prusa's material guides ([help.prusa3d.com](https://help.prusa3d.com)) on PETG and flexible filaments like TPU.

## 7. 3D rendering

*Needed for hero shots and turntables.*

- [ ] **Do:** Blender Guru's donut tutorial (Andrew Price, YouTube). Everyone starts here, and it teaches the whole Blender workflow.
- [ ] **Read, later:** the Blender Python API docs, to understand the scripts that render the drone.

## 8. Flight simulation

*Needed for step 4 (PX4 flies the design) and step 5 (my firmware does).*

What Gazebo actually simulates, how PX4 runs inside a simulator (SITL), what MAVLink is, and how ground stations talk to drones.

- [ ] **Do:** PX4's Gazebo simulation quickstart ([docs.px4.io](https://docs.px4.io)). Fly the stock x500 quad in sim.
- [ ] **Do:** fly a mission in QGroundControl against the simulated drone.
- [ ] **Read:** the MAVLink developer guide ([mavlink.io](https://mavlink.io)), mostly the overview and the common messages.
- [ ] **Read:** the Gazebo tutorials ([gazebosim.org](https://gazebosim.org)) on worlds, models and plugins.
- [ ] **Watch, if ROS 2 comes into it:** Articulated Robotics (YouTube).

## 9. Control systems and PID

*Needed for step 5: writing my own flight controller.*

Feedback loops, PID (what each term does, and why the D term hates noise), cascaded loops (rate inside angle inside position), and stability.

- [ ] **Watch:** MATLAB Tech Talks, *Understanding PID Control* (Brian Douglas, YouTube).
- [ ] **Watch:** Steve Brunton, *Control Bootcamp* (YouTube).
- [ ] **Read:** Karl Johan Åström and Richard M. Murray, *Feedback Systems: An Introduction for Scientists and Engineers* (Princeton University Press). There's a free PDF from the authors.
- [ ] **Read:** Beard and McLain (from topic 1), the chapters on autopilot design.

## 10. Sensor fusion and state estimation

*Needed for step 5: the drone has to know which way is up.*

What an IMU measures, why gyros drift and accelerometers are noisy, complementary filters, the Madgwick and Mahony filters, and Kalman filters (and the extended kind).

- [ ] **Do:** Roger Labbe, *Kalman and Bayesian Filters in Python* ([github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python](https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python)). A free book you can run.
- [ ] **Watch:** the MATLAB Tech Talks on sensor fusion (Brian Douglas, YouTube).
- [ ] **Read:** Sebastian O. H. Madgwick, "An efficient orientation filter for inertial and inertial/magnetic sensor arrays" (technical report, University of Bristol, 2010).
- [ ] **Read:** Robert Mahony, Tarek Hamel and Jean-Michel Pflimlin, "Nonlinear Complementary Filters on the Special Orthogonal Group," *IEEE Transactions on Automatic Control* 53(5), 2008.
- [ ] **Read, later:** Sebastian Thrun, Wolfram Burgard and Dieter Fox, *Probabilistic Robotics* (MIT Press, 2005).

## 11. Embedded firmware on the STM32

*Needed for step 5, and for anything that gets built.*

Timers, interrupts, DMA, SPI (talking to the IMU), UART (talking to the receiver over CRSF), generating DShot for the ESC, and keeping a control loop on schedule.

- [ ] **Read:** Carmine Noviello, *Mastering STM32* (Leanpub).
- [ ] **Read:** Elecia White, *Making Embedded Systems* (O'Reilly).
- [ ] **Read:** ST's RM0433 reference manual for the STM32H743. Not cover to cover; it's what I look things up in.
- [ ] **Read:** the dRehmFlight source ([github.com/nickrehm/dRehmFlight](https://github.com/nickrehm/dRehmFlight)). A whole flight controller in one readable file.
- [ ] **Do:** run dRehmFlight on the Teensy 4.1 with an IMU breakout and no motors (the optional warm-up in step 5).
- [ ] **Read:** ExpressLRS docs ([expresslrs.org](https://expresslrs.org)) on the CRSF protocol.

## 12. Building and soldering

*Needed if I build it one day.*

Soldering to ESCs and flight controllers, power wiring, keeping noise out of the gyro, and setting up ExpressLRS.

- [ ] **Watch:** Joshua Bardwell (YouTube), soldering and build videos.
- [ ] **Read:** Oscar Liang's build guides ([oscarliang.com](https://oscarliang.com)).
- [ ] **Do:** practice soldering on scrap wire and an old board before touching the real ESC.

## 13. Rules and flying safely

*Needed if I build it one day. It's the build package's legal checklist.*

- [ ] **Do:** the FAA's TRUST test (free, online).
- [ ] **Read:** the FAA's recreational flyer rules and the Remote ID rules ([faa.gov/uas](https://www.faa.gov/uas)).
- [ ] **Do:** get B4UFLY (the FAA's airspace app) and check my flying field. Get LAANC authorization if the field is in controlled airspace.

## 14. Design optimization

*Needed for the design hunt side track.*

How an automated loop actually searches for better designs: design spaces, objective functions, constraints, evolutionary algorithms, Bayesian optimization, and multi-fidelity (cheap checks first, expensive ones only for the best candidates).

- [ ] **Read:** Mykel J. Kochenderfer and Tim A. Wheeler, *Algorithms for Optimization* (MIT Press, 2019). There's a free PDF from the authors.
- [ ] **Read:** Peter I. Frazier, "A Tutorial on Bayesian Optimization" (arXiv, 2018).

## 15. Electrical design

*Needed for step 3: every wire, pin and connector.*

Power distribution, wire gauges and voltage drop, connectors and their current ratings, how a flight controller's timers and serial ports get assigned, reading and drawing schematics, and simulating a small circuit.

- [ ] **Read:** Paul Horowitz and Winfield Hill, *The Art of Electronics*, 3rd ed. (Cambridge University Press, 2015). The reference. Dip in when something needs it.
- [ ] **Do:** the KiCad getting-started guide ([docs.kicad.org](https://docs.kicad.org)), then draw the drone's system schematic.
- [ ] **Read:** the ngspice manual ([ngspice.sourceforge.io](https://ngspice.sourceforge.io)), for simulating the safety monitor's signal switch.
- [ ] **Read:** the WireViz README ([github.com/wireviz/WireViz](https://github.com/wireviz/WireViz)), which turns a text file into a wiring diagram.
- [ ] **Read:** Oscar Liang's guides on power and flight controller wiring ([oscarliang.com](https://oscarliang.com)).

Four things came up in the electrical talk (2026-10-18). DShot, and the bidirectional kind, is the language between the flight controller and the ESC, and the safety monitor now has to speak it too. DroneCAN is how the modules talk to the flight controller. Partial power-down (Ioff) is why a dead Teensy won't drag down the lines it listens to: without it, a chip's protection diodes get powered through its input pins. And fusing current, how fast a wire melts at a given current, is how the pack's cell links get judged.

- [ ] **Read:** Betaflight's DShot page ([betaflight.com/docs/development/API/Dshot](https://betaflight.com/docs/development/API/Dshot)), put together by one of the Bluejay ESC firmware's authors: the frame, the checksum, and how the RPM reply works.
- [ ] **Read:** the DroneCAN docs ([dronecan.github.io](https://dronecan.github.io)), and skim libcanard ([github.com/dronecan/libcanard](https://github.com/dronecan/libcanard)), the small C library my firmware will use to speak it.
- [ ] **Read:** TI's technical article on partial power-down ([ti.com/lit/pdf/ssztap0](https://ti.com/lit/pdf/ssztap0)), then look up "Ioff" in any 74LVC datasheet.
- [ ] **Read:** Signal Integrity Journal's piece on how traces fuse ([signalintegrityjournal.com](https://www.signalintegrityjournal.com/articles/1704-how-do-traces-fuse-melt)), on Onderdonk's equation and where it stops being right. For the deep version: Douglas Brooks and Johannes Adam, *PCB Design Guide to Via and Trace Currents and Temperatures* (Artech House, 2021), chapter 12.

## 16. Structure: stress and vibration

*Needed for the structure side track.*

How parts bend and break, what a finite element model actually is, and why vibration frequencies matter: if an arm's natural frequency lands near the props' rotation speed, the gyro sees noise the filters have to fight.

- [ ] **Read:** R. C. Hibbeler, *Mechanics of Materials* (Pearson). Stress, strain and bending.
- [ ] **Read:** Daryl L. Logan, *A First Course in the Finite Element Method* (Cengage). What the FEA software is doing under the hood.
- [ ] **Read:** Singiresu S. Rao, *Mechanical Vibrations* (Pearson). Natural frequencies and resonance.
- [ ] **Do:** the FreeCAD FEM workbench tutorials on the FreeCAD wiki ([wiki.freecad.org](https://wiki.freecad.org)), which run CalculiX underneath.

## Coming up later

These get filled in properly when I get close to them.

- **Visual navigation and mapping** (steps 6–7):
  - Davide Scaramuzza and Friedrich Fraundorfer, "Visual Odometry: Part I," *IEEE Robotics & Automation Magazine*, 2011
  - the OpenDroneMap docs
- **Surviving a motor failure** (idea #23): Mark W. Mueller and Raffaello D'Andrea, "Stability and control of a quadrocopter despite the complete loss of one, two, or three propellers," *IEEE ICRA*, 2014.
- **LLMs that plan missions** (step 7): tool use, structured output, and validating what a model hands back.
- **Radio links** (steps 6–7, for HaLow and the Meshtastic relay): link budgets, why these radios need line of sight, Fresnel zones, antennas, and why the control link stays off the 900 MHz band.
  - the Meshtastic docs ([meshtastic.org](https://meshtastic.org)), on LoRa settings and range
  - the Wi-Fi Alliance's pages on Wi-Fi HaLow ([wi-fi.org](https://www.wi-fi.org))
  - *The ARRL Antenna Book* (ARRL), for antennas and propagation
- **Object detection** (#39, step 7): how detectors like YOLO work, training them on aerial images, and running models on the laptop's NPU.
  - the Ultralytics docs ([docs.ultralytics.com](https://docs.ultralytics.com))
  - the OpenVINO docs ([docs.openvino.ai](https://docs.openvino.ai))
  - the VisDrone dataset ([github.com/VisDrone/VisDrone-Dataset](https://github.com/VisDrone/VisDrone-Dataset))
- **Rotor drag in forward flight** (the honesty check): why a quad's spinning props add drag that grows with speed, on top of the frame's frontal area, and why that matters for cruise power.
  - Robert Mahony, Vijay Kumar and Peter Corke, "Multirotor Aerial Vehicles: Modeling, Estimation, and Control of Quadrotor," *IEEE Robotics & Automation Magazine*, 2012
  - Philippe Martin and Erwan Salaün, "The true role of accelerometer feedback in quadrotor control," *IEEE ICRA*, 2010
- **Soaring and descending** (soar mode, #31, step 7): where rising air comes from (slope lift, thermals), how a rotor's power changes when the air moves up through it, and the vortex ring state.
  - the FAA's *Glider Flying Handbook* (free on [faa.gov](https://www.faa.gov)), the parts on soaring weather, slope lift and thermals
  - Leishman's *Principles of Helicopter Aerodynamics* (topic 2), the parts on descending flight and the vortex ring state

---

## My notes

Things that clicked, things that didn't, and questions to bring back to a building session.

- 
