# Phase 1: Simulating the design

*Written 2026-10-13, before any code. Revised the same day to add code CAD, aerodynamics, the design hunt, and visuals. Like everything else here, it will change once real numbers show up.*

This is how I'm going to prove the drone works, and then find a better one, before buying a single part.

## What Phase 1 has to produce

1. **A baseline X quad** that passes every target in simulation, across all eight module combinations. The point is to prove the whole pipeline works end to end.
2. **A unique design**, found by an automated build-test-improve loop, that beats the baseline.
3. **A priced parts list** for whichever design wins.
4. **Visuals worth posting** from every layer along the way.

Nothing gets ordered before item 3 exists.

The targets are locked in [decisions.md](../decisions.md) and live in machine-readable form in [design/targets.yaml](../../design/targets.yaml):

| Setup | Modules | Flight time | Other targets |
|---|---|---|---|
| Base | none | ≥ 30 min | Thrust-to-weight ≥ 4:1 |
| Mission | V + P | ≥ 25 min | Top speed ≥ 80 km/h; holds position in 10 m/s wind |
| Max | V + P + C, carrying 250 g | ≥ 20 min | Thrust-to-weight ≥ 3:1; total weight ≤ 2.5 kg |

Every setup lands with at least 20% battery left, and flight time means cruising, not hovering. The other five combinations have to land somewhere between Base and Max.

## The five layers

```
parts + shape → 1 sizing → 2 CAD → 3 aero (CFD) → 4 Gazebo + PX4 → pass/fail → improve → repeat
                                                        └→ 5 my firmware (Phase 2)
```

Layers 1 and 2 take seconds, so they run constantly. Layers 3 and 4 take hours or minutes, so they confirm (or embarrass) what the first two say. Layer 5 is Phase 2, but it reuses everything built here.

## Layer 1: Parts files and the sizing model

### The parts files (`design/`)

One place describes the whole drone, and everything else reads from it.

- **`catalog/`:** candidate parts, one file per type: motors, props, batteries, ESCs, frames, module parts.
  - Every part has a mass and dimensions.
  - Motors and props carry the manufacturer's thrust test data: throttle, thrust and current, at a stated voltage.
  - I'll start it off with 3–4 real candidates of each motor, prop and battery.
- **`build.yaml`:**
  - which part fills each slot
  - the frame's shape parameters
  - where each part sits, in mm from the center of the frame. The axes are x forward, y left, z up, the same as Gazebo and ROS, so nothing needs converting later.
  - what's in V, P and C. The 250 g grabbed object counts as part of C.
- **`targets.yaml`:** the numbers above.

Swapping a part means changing one name in `build.yaml`.

### What it works out

For each of the eight module combinations:

- Total weight, center of gravity and inertia. These are rough estimates at first; the CAD layer replaces them with exact numbers.
- Thrust-to-weight, plus hover throttle, current and power from the thrust tables, scaled to the battery's voltage
- Cruise flight time, from a forward-flight power model plus a Li-ion battery model: usable capacity, voltage sag, and the 20% reserve
- A top-speed estimate, and a check that it can hold position in a 10 m/s wind

Drag starts as a guess from frontal area. The aero layer replaces it with real CFD numbers, and the downwash loss from CFD gets taken off the thrust.

### What comes out

- **A report:** pass/fail for every combination against every target, with margins. It's Markdown, so it reads fine on GitHub.
- **A data file for the other layers:** mass, inertia and motor constants, so everything downstream uses the same numbers.
- **Sweep mode:** it tries every motor × prop × battery in the catalog and ranks them by whether they pass and by how much.
- **Charts** in the project's visual style (see Visuals).

### Known limits

Manufacturer thrust data is usually optimistic, so I'm treating flight times as ±15–20% until the Phase 3 thrust stand gives me real measurements.

### To settle before building it

These are what the sizing model discussion is for:

- the exact math for cruise power and the battery model, and what I validate them against
- what cruise speed "flight time" actually means
- the catalog file format, and which real parts to seed it with
- what the report looks like
- where the code lives and how it's packaged

## Layer 2: CAD, written as code (`cad/`)

Claude writes the CAD in Python with build123d. It reads `build.yaml` and builds every part as a simple but correctly sized solid:
- the frame plates and arms, from the frame parameters
- motors, prop disks, and the battery pack, sized from its cell layout
- the flight controller stack
- the module mount, and the V, P and C module boxes

**What it checks:**
- prop-to-prop and prop-to-frame clearance
- that everything fits on the mount
- that the center of gravity sits close enough to the center of thrust

**What comes out:**
- **Mass properties per module combination:** each part's catalog mass is spread over its solid, which gives a real center of gravity and inertia. These replace the sizing model's estimates.
- **A STEP assembly**, which opens in any CAD tool (including Onshape, if I want to poke at it).
- **Meshes:** a simplified one for Gazebo, and a watertight surface for CFD.
- **Renders.** Quick previews come straight from Python; hero shots and turntables come from Blender.

The baseline is a plain X, modeled after a real 8–10" frame. If a real frame's STEP file is available, it gets imported instead of approximated.

## Layer 3: Aerodynamics (`aero/`)

The virtual wind tunnel. It's tiered by how much detail is needed.

### Everyday runs: OpenFOAM

The props are modeled as actuator disks: flat disks that push air with the thrust the sizing model says they make. The cases:
- **Forward flight** at several speeds up to 22 m/s (about 80 km/h), each at the tilt the drone would actually fly at
- **Hover in ground effect** at a couple of heights
- **10 m/s crosswind**

**What comes out:**
- drag, lift and moments versus speed and tilt, as lookup tables for the sizing model and Gazebo
- how much thrust the frame and modules steal by sitting in the prop wash
- ParaView images: streamlines, smoke-style traces, pressure on the body

**Runtime:** about an hour or two per case on the PC. So not every combination gets every case: Base and Max get the full sweep, and the others get spot checks.

**The pipeline is scripted end to end:** CAD surface, then mesh (snappyHexMesh), then solve, then post-process. The design hunt can run it without me touching anything.

### Showcase runs: FluidX3D

Fully spinning props on the RTX 3060's GPU, for the tip-vortex visuals that make the posts. They're for seeing, not for the numbers.

Its license allows personal and educational use, but publishing results from a modified copy means publishing the modified source. So my FluidX3D setup lives in a separate public fork, clearly marked as modified, and never in this GPL repo.

The fallback is OpenFOAM with rotating meshes: slower, but one tool.

### Keeping it honest

1. Run OpenFOAM on a sphere and a cylinder first, and make sure it gets their known drag right.
2. Compare it against published drone drag data.
3. Later, compare it against my own flight logs.

## Layer 4: Gazebo + PX4 (`sim/`)

- **A generator** turns `build.yaml`, the sizing output, the CAD mass properties and the aero tables into a Gazebo model and matching PX4 airframe settings for each module combination. It's modeled on PX4's stock quad (the x500).
- **Scenario scripts** fly PX4 through the same tests every time:
  - hover, and the response to sudden stick inputs
  - a top-speed run
  - 10 m/s wind
  - full endurance
  - failsafes: lost link, low battery
  - a parachute drop
  - a payload grab
- **Flight time:** Gazebo doesn't model electrical power, so I log the rotor speeds, turn them into current using the thrust data, and run that through the same battery model as layer 1. That way every layer agrees on what a battery is.
- **Rough edges, on purpose:** the payload grab uses Gazebo's attach/detach joints, and the parachute is a simple drag model. Good enough to test the logic, not the aerodynamics.
- **Results** come out in the same pass/fail format, and runs get recorded as clips for posts.

## Layer 5: My firmware in the sim

This is Phase 2, but Phase 1 leaves room for it. The same Gazebo models and scenarios get reused, so my firmware gets compared directly against PX4 on identical tests.

## After the baseline: the design hunt (`explore/`)

Once the baseline X passes end to end, the automation takes over: build, test, read the results, improve, repeat.

1. **Propose:** an optimizer picks a new design from a parameter space. The parameters could include:
   - arm geometry
   - motor positions and tilt
   - where the stack and modules sit
   - body shape
2. **Filter fast:** the sizing model and CAD checks run in seconds, so thousands of candidates can be tried. A cheap drag estimate ranks them.
3. **Test properly:** the best few go through OpenFOAM and Gazebo.
4. **Learn:** the results feed back into the optimizer (Bayesian optimization or an evolutionary search; I'll pick when we get there).
5. **Log everything:** every generation gets recorded, and the best designs get renders. The hunt itself is post material.

**Decided later, once the baseline works:**
- what "unique" is allowed to mean: stay a quad, or open it up to other layouts. Leaving the quad layout changes the firmware too.
- how a custom frame would get made: CNC-cut carbon plates from my files, or carbon tubes with printed joints.

## Visuals

Everything here gets posted, mostly on LinkedIn and sometimes on Instagram, so every layer exports visuals as a normal output, not an extra step.

- **One look across everything:** the "wind tunnel" style in [style.md](../style.md). That means black backgrounds, a spearmint accent, turbo for CFD color fields, and a color bar with units on every CFD image.
- **What the CFD images show:**
  - surface pressure (where the air hits hardest)
  - streamlines colored by speed
  - prop wash
  - a chart of which part costs the most drag
- **Export sizes:**

  | Format | Size |
  |---|---|
  | 4:5 portrait | 1080×1350 (works on both platforms) |
  | 1:1 square | 1080×1080 |
  | 9:16 vertical | 1080×1920 (Reels and Stories) |
  | 16:9 | 1920×1080 (video) |

  Plus PDF carousels for LinkedIn.
- **Tools:** Blender (scripted, rendering on the RTX 3060) for CAD hero shots and turntables, ParaView for CFD, ffmpeg to cut clips to size, and charts styled to match.
- **Scripts read the style from `media/style.yaml`,** so every chart and render matches without anyone thinking about it.
- **Storage:** curated, compressed stills go in `media/`. Raw renders and videos stay out of the repo and go straight to the posts.

## Where things run

- **Sizing, CAD and quick renders:** either machine.
- **OpenFOAM, FluidX3D, Blender hero renders, and Gazebo + PX4:** the PC, on native Ubuntu 24.04. The laptop's WSL is only for small test cases.
- **`scripts/setup-ubuntu.sh`:** safe to rerun. It pins the versions of PX4, Gazebo Harmonic, OpenFOAM, ParaView, Blender and the Python packages, so both machines match.
- **GitHub Actions:** reruns the lint and tests on every push, and later the sizing report too.

## Repo layout

```
design/    targets.yaml · catalog/ · build.yaml
sizing/    the sizing model
cad/       the CAD code and what it exports (meshes through LFS)
aero/      OpenFOAM cases, scripts, post-processing
sim/       Gazebo model generator, PX4 airframe, worlds, scenarios
explore/   the design hunt
media/     curated images for posts
scripts/   setup-ubuntu.sh
tests/     tests for all of the above
docs/      decisions, roadmap, specs, log, generated reports
```

## How I'll know the tools themselves work

- **Sizing model:** unit tests with hand-checked numbers, plus a sanity check against a published long-range build with known flight times.
- **CAD:** tests that the total mass matches the parts list, the clearances hold, and the exports are valid.
- **Aero:** the sphere and cylinder checks above, before any drone runs.
- **Generator:** every generated model has to pass Gazebo's own model check.
- **Scenarios:** a smoke test that flies PX4's stock quad through them before my design goes anywhere near them.

## Not in Phase 1

My own firmware (Phase 2), buying anything, the ground station, and the LLM.

Phase 2 can start as soon as the baseline passes, while the design hunt keeps running alongside it.
