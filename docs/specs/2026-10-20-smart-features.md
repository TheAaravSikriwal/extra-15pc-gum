# Smart features in sim (step 7)

*Written 2026-10-20. I asked for the open items to keep moving without stopping to ask, so I made these calls myself and wrote down why. The ones that are mine to make stay open below.*

## What it has to do

From the [roadmap](../roadmap.md#step-7-smart-features-in-sim): each feature works in sim, and whatever the sim can't show goes on the unproven list. Twelve of them, from the ideas in [decisions.md](../decisions.md):

| # | Feature | Needs the camera |
|---|---|---|
| 1 | Landing modes: land now, back to start, land here | no |
| 2 | Mapping runs (#7), on simulated camera images, through OpenDroneMap | yes |
| 3 | Safe-spot detection, and the nearest-safe-spot landing | the map |
| 4 | Change detection (#11), in a world where things move | yes |
| 5 | Wind sensing (#10), and the "turn back now" battery warning | no |
| 6 | Self-tuning (#21), a profile for each module combination | no |
| 7 | GPS-free flight (#24), on the simulated camera | yes |
| 8 | Plain-English missions (#26): the plan, the checker, my approval, the flight | no |
| 9 | Object detection on the laptop (#39) | yes |
| 10 | The Meshtastic relay (#30), as a link model | no |
| 11 | Soar mode (#31), with rising air added to Gazebo | no |
| 12 | The spiral descent (#34), its path only | no |

Step 6 got V's camera rendering in Gazebo inside WSL, so all twelve can be tried in the sim. What the PC doesn't have is the vision software the roadmap assumed: no OpenDroneMap, no OpenCV, no Docker to run either in. Installing them means downloads and `sudo`, which are mine, so step 7 does what it can with what's here (numpy and SciPy, and Ollama with two local models), and says where the real tool would do better.

## Calls

- **The LLM for plain-English missions is a local one for the sim:** Qwen2.5 7B Instruct through Ollama, on the PC's RTX 3060. Decisions.md expected a cloud model on the laptop, and that can still be the drone's real setup; the sim only needs a model that writes plans, and a local one needs no key and no network. The safety rule doesn't move: the model writes a structured plan, the deterministic checker validates it against the active limits profile, a person approves it, and the flight controller flies it. In the sim the approval is the test script's, and it says so in the log.
- **Mapping is an orthomosaic from known poses, for now:** each frame of a grid run projected onto the ground from where the camera was and where it pointed, which is what a GPS-tagged mapping run does once its poses are known. That makes a picture of the ground, not a 3D model: OpenDroneMap's photogrammetry, which works out the heights from the overlapping photos, waits for it to be installed.
- **Safe spots come from a height map:** the detection (flat enough, level enough, clear of anything taller than the drone's reach) runs on a height map, and in the sim the first one is the world's own, which is exact. When OpenDroneMap is in, the same detection runs on its surface model, and the difference is a finding.
- **Change detection compares two orthomosaics:** the same grid flown twice with something moved in between, the two pictures differenced where they overlap, and what changed flagged on the map.
- **GPS-free flight starts as optical flow and the rangefinder,** the way PX4 does it with a flow sensor: how far the ground slides between frames (phase correlation, in numpy), times the height from Base's TF-Luna, over the focal length, is the drone's speed over the ground. Integrated, that's a position without GPS. First it's checked against Gazebo's ground truth on recorded flights, then it goes into the loop. Full visual-inertial odometry waits for a real VIO package.
- **Object detection is the local vision model:** Qwen2.5-VL 7B through Ollama, on the camera's frames, asked for what it sees and where. The laptop runs it on the real drone (decisions.md); the PC runs it in the sim.
- **Wind sensing is the hover's lean against the drag model:** holding position in a steady wind, the drone leans until its thrust's sideways part matches the drag, so the lean and the thrust give the wind. The battery warning is then the energy home against the wind, plus the reserve, against what's left.
- **Self-tuning identifies the drone, then sets the gains:** a short, small excitation in the air (a few degrees, a fraction of a second), the inertia worked out from the response, and the gains my rate loop already derives from inertia. Per combination, against the inertia the CAD says.
- **The Meshtastic relay is a link budget, like HaLow:** a LoRa radio's sensitivity at Meshtastic's presets, from Semtech's datasheet for the chip, over the same two-ray path, so the relay's gain is the range a node at 100 m adds over one on the ground.
- **Soar mode starts as the lift detector:** a rising-air column in the drag plugin's wind, the throttle needed to hold height against what the weight predicts, and the saving the drone gets by holding still in it. The kestrel-on-a-hillside part (ridge lift) waits for terrain.
- **The spiral descent is a path in my firmware:** a helix on low throttle from height, straightening up for the last few meters, checked for its path and its sink rate only, since Gazebo has no vortex ring state to avoid.

## Not settled yet

- OpenDroneMap, OpenCV and a VIO package: installing any of them is a download and `sudo`, mine to do. Each feature works without them first, and says where they'd do better.
- Whether the vision model's boxes are good enough to be the detector, or only a describer. The first test is on the sim's own frames, where the truth is known.
- Where the Meshtastic relay lives (V, Base, or its own module): still open in decisions.md, and the link model doesn't need it settled.
