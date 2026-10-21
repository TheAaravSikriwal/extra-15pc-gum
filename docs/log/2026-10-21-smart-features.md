# 2026-10-21: The smart features in sim

*PC, WSL2 Ubuntu and Windows. Step 7: the [spec](../specs/2026-10-20-smart-features.md), the [plan](../plans/2026-10-20-smart-features.md) and the build. The [report](../reports/smart/README.md) has every number.*

Step 7 is the list of things that make this more than a drone that flies: landing modes, a warning that tells me to turn back while I still can, a drone that works out its own inertia, missions from plain English, mapping, finding a safe place to land, spotting what changed, flying without GPS, recognizing things in the camera, a radio relay, soaring in rising air, and a spiral way down. Twelve features, all in the sim, each with a list of what the sim can't prove.

The PC had less of the usual toolkit than the roadmap assumed. No OpenDroneMap, no OpenCV, no Docker, and installing them takes `sudo`, which is mine. So everything here is numpy, SciPy and two local models through Ollama, and the report says where a real tool would do better.

## Landing modes and the turn-back warning

The three ways down are plain on purpose: land now, back to start, and land here, at a point I give it. All three came down within 0.1 m of where they should, at 0.7 to 0.8 m/s.

The turn-back warning is more interesting. Hovering in a steady wind, the drone leans until the sideways part of its thrust matches the drag, so the lean tells you the wind. Then, flying out with the wind behind it, the warning keeps working out the energy it would take to get home into that wind, plus the reserve, and says turn back while there's a quarter more than that left.

The first version predicted the trip home 39% short. The sizing model's power curve gets cheaper in forward flight, the way real rotors do, and Gazebo's rotors don't. So the warning never counts on flying being cheaper than hovering now. It's pessimistic on a real drone, which is the side to be wrong on. In the four combinations with V it lands within 8% of what the flight used.

## Self-tuning, in three tries

My rate loops multiply by the drone's inertia, so if a payload or a module changes the inertia, the loop needs to know. Self-tuning pokes the drone on purpose and works out the inertia from how it answers.

The plan was to use step 4's stick steps, 15 degrees and held for 2 seconds. That came out 9 to 62% off. A step that big has the drone sliding sideways at several m/s, and the rotors' drag, a few centimeters above the center of gravity, makes a roll moment the fit doesn't know about.

So I added a dedicated test: three doublets, a quarter stick one way for a quarter second, then the other. The first fit read 12% low. Before blaming the method I checked Gazebo itself, in a world with no gravity: a known torque on the body gave an inertia of 0.01292 kg m², against the model's 0.01293, and spinning one side's motors gave the torque the motor constant says, within 0.4%. The motors speed up in 12.5 ms and slow down in 25, as configured. Every part matched, so the problem was the fit. It picked its stretches by how busy the torque was and used one trim for the whole flight, and the slow change in trim as the drone drifted got counted as inertia. Fitting each doublet in its own window, with its own offset and trend, fixed base.

Max and mission still read 13% low. That one was the grader: it read the motors' speeds off the ground truth's timeline, which in these logs ticks at 50 Hz, and smoothed away the fast changes the fit needs. Reading them at their own 250 Hz:

| | base | V | P | C | mission | V+C | P+C | max |
|---|---|---|---|---|---|---|---|---|
| Off from the model | -0.1% | -0.1% | -0.3% | -0.3% | -0.1% | -0.1% | -0.3% | -0.2% |

That's a clean sim, though. A real drone's motors aren't a perfect lag, its gyro is noisier, and its rotors flap. And the fit runs on the ground from the log for now, not on the drone.

## A mission from plain English

`pcs14 smart "..."` asks a local model (Qwen2.5 7B, on the PC's graphics card) for a plan, and the checker checks it against the limits profile, the drone's pack and its reserve. It's saved unapproved. In the sim the test script approves it and says so in the log; on the drone that's me. My firmware flew both waypoints and came home.

The finding worth more than the pass: asked to fly 60 m west of home, the model wrote a point 20 m north and 40 m east. The checker passed it, because it was safe. A checker can catch a plan that's dangerous, never one that's safe but wrong. That's what my approval is for, and why the plan gets drawn on a map before I give it.

## The spiral and soar mode

The spiral descent comes down a helix 8 m across at 1.5 m/s, its setpoints streamed the way the companion computer would. It stayed within 0.3 m of the circle and sank at 1.48 m/s. Gazebo has no vortex ring state, the thing the spiral exists to avoid, so this checks the path and nothing more.

Soar mode starts as a lift detector: hold a hover and see whether it takes less thrust than it should. In a column of air rising at 4 m/s, Gazebo's rotors don't feel the air at all, so the only signal is the push on the body: a tenth of a newton on 18. Over 12 seconds that was 1.9 standard errors from nothing, and over 30 s, 2.5. Soar mode is for waiting, so averaging a minute is part of the design: 4.7 standard errors, and the updraft read back at 4.2 m/s. A real rotor would save about 76 W in that column, by momentum theory, and that number goes on the unproven list.

## Maps, changes and a safe place to land

For mapping, V's camera points straight down and flies a three-line grid 30 m up. Each frame is laid on the ground from where the camera was and where it pointed, and together they make an orthomosaic. The whole area was seen, and all seven things in it landed on the map within a meter of where they stand. One catch for the CAD: V's bracket tips the camera 30 degrees for the live video, which is too oblique for a map, so it needs a mapping position or a tilt servo.

Fly the grid again with the box moved 22 m, difference the two maps, and the change shows up where the box was and where it went. The first grade counted a third spot. It was the box's own shadow, split off from it, so everything within 1.5 m now counts as one change.

Asked to land on the shed, the drone picks the nearest spot with nothing taller than 15 cm within its footprint plus 3 m, flies there and lands. That's 5.4 m from the shed. The same pick off the orthomosaic first chose a spot 0.4 m inside the shed's clearance, because the map places things to within about a meter. So safe spots read off a map get that meter on top.

![The map](../reports/smart/stills/map-portrait.png)

## Flying without GPS

This is the one I like best. The camera looks down, and between frames the ground slides. Phase correlation finds how far: a shift in a picture is a ramp in the phase of its Fourier transform, so the peak of the two frames' cross-power spectrum is the shift. Evaluating that peak on a finer and finer grid gets it to a hundredth of a pixel. With the drone's attitude and its height from the TF-Luna rangefinder, the shift in pixels becomes a move in meters. Add the moves up and that's a position, with no GPS at all.

Gazebo's ground is one flat color, which gives the correlation nothing to hold, so the test flies over a field I generated: noise with detail at every scale, colored from soil to dry grass. 6 m up, inside the TF-Luna's 8 m, around three sides of a 40 by 20 m rectangle. The attitude is the sim's truth tilted by half a degree of noise, and the height carries the TF-Luna's 2%.

The first flight drifted 12.6%. My firmware flew the legs at its own pace, about 15 m/s: 1.5 m between frames at 6 m up, with the drone tilted 30 degrees, and the frames stopped matching. At 3 m/s it ended 0.17 m off after 103 m, 0.2%, and was never more than 2% off along the way. Flow-only flight is slow flight.

![GPS-free flight](../reports/smart/stills/flow-wide.png)

The run also caught a bug in the camera recorder. Saving a textured frame as a PNG takes about 0.2 s, longer than the 0.1 s between frames, and the recorder did it on Gazebo's own callback. The frames piled up in Gazebo's queue, and when the run ended, the last 40 s of them were lost. It writes on a thread of its own now and waits for every frame before it closes.

## What the model sees

The laptop is meant to run a vision model on V's video. Here it's Qwen2.5-VL 7B, asked for every object in seven of step 6's camera frames, its boxes checked against boxes worked out from where Gazebo put each thing. The prompt mattered a lot. Asking for "every object standing on the ground" found only the shed. Qwen's own grounding prompt boxed five of seven things but called them all "object". Asking for every object, however small, with a label, boxed four and named them.

Over the seven frames it put a box near 14 of the 20 things there, with a median overlap of 0.76, and found the shed every time. It also made three boxes on nothing, one of them around the whole of an empty frame, labeled "dark gray background". So it's a describer and a coarse detector. It's good for "there's a pink cube over there", but not good enough to land by. Safe spots stay on the map's heights.

![Object detection](../reports/smart/stills/detection-wide.png)

## The relay

The Meshtastic relay is a link budget for now, like HaLow's. A node in someone's hand reaches about 5.6 km on LongFast over flat ground. The same node riding on the drone at 100 m reaches about 46 km. Where it lives, V or Base or a module of its own, is still open.

## What's next

Step 8, the build package: the parts list with links and fallbacks, the assembly and wiring guides, test plans and the legal checklist. Then the side tracks, and the site gets a last refresh.
