# Simulating the baseline: sizing, CAD and the flight sim

*Written 2026-10-13, before any code. Revised the same day to add code CAD, aerodynamics, the design hunt, and visuals. Revised again on 2026-10-14 by the [full plan revision](2026-10-14-plan-revision.md): the wind tunnel and the design hunt run alongside instead of blocking, a thrust stand joins Phase 1, and the targets changed. Revised again on 2026-10-17, when the project became a research project: this spec now covers steps 1 (sizing and parts), 2 (CAD) and 4 (flight sim) of the [roadmap](../roadmap.md), plus the aero and design-hunt side tracks. Electrical, structure and the build package get their own specs. Like everything else here, it will change once real numbers show up.*

This is how I'm going to prove the drone works, entirely in simulation and with real, orderable parts, while the search for a better one runs alongside.

## What these steps have to produce

1. **A baseline X quad** that passes every target in sizing, CAD and Gazebo, across all eight module combinations, using real parts' data (measured, if the optional thrust stand happens). The point is to prove the pipeline works end to end, and this is the drone the research is built around.
2. **A priced parts list** for the baseline, which goes into the build package.
3. **Visuals worth posting** from every layer along the way.

Nothing gets ordered by default. The thrust stand is optional: it makes the simulation more accurate, and most of its parts would end up on the drone if I build it.

Running alongside, and not needed for these steps to finish: the wind tunnel layer, and the design hunt for v2.

The targets are in [decisions.md](../decisions.md) and live in machine-readable form in [design/targets.yaml](../../design/targets.yaml):

| Setup | Modules | Cruise time | Hover time | Other |
|---|---|---|---|---|
| Base | none | ≥ 30 min | ≥ 25 min | |
| Mission | V + P | ≥ 25 min | ≥ 21 min | Top speed ≥ 80 km/h; holds position in 10 m/s wind |
| Max | V + P + C, carrying 250 g | ≥ 20 min | ≥ 17 min | Total weight ≤ 2.5 kg |

For every setup: thrust-to-weight of at least 2:1 at the 20% reserve, at full throttle, under load; full-throttle current inside the pack's continuous rating; at least 20% of the battery left on landing, counted in mAh; and cruise means 10 m/s for now. The other five combinations have to land somewhere between Base and Max.

## The five layers

```
parts + shape → 1 sizing → 2 CAD → 4 Gazebo + PX4 → pass/fail → improve → repeat
                  ↑                      └→ 5 my firmware (step 5)
     thrust stand data, and 3 aero (CFD) whenever it has numbers
```

Layers 1 and 2 take seconds, so they run constantly. Layer 4 takes minutes, so it confirms (or embarrasses) what the first two say. Layer 3 takes an hour or two per case, so it runs alongside and feeds its numbers back whenever they're ready. Layer 5 is step 5 of the roadmap, but it reuses everything built here.

## Layer 1: Parts files and the sizing model

### The parts files (`design/`)

One place describes the whole drone, and everything else reads from it.

- **`catalog/`:** real, orderable candidate parts, one YAML file per part, in folders by type: `motors/`, `props/`, `cells/`, `escs/`, `frames/`, `modules/`. The format is under "Settled in the sizing model talk" below.
  - Every part has a mass, dimensions and a price, and every number has a source.
  - Motors carry thrust test data (throttle, thrust, current, RPM) for each prop and voltage they were tested with.
  - I'll start it off with 3–4 real candidates of each motor, prop and cell.
- **`build.yaml`:**
  - which part fills each slot
  - the frame's shape parameters
  - where each part sits, in mm from the center of the frame. The axes are x forward, y left, z up, the same as Gazebo and ROS, so nothing needs converting later.
  - what's in V, P and C. The 250 g grabbed object counts as part of C.
- **`targets.yaml`:** the numbers above.

Swapping a part means changing one name in `build.yaml`.

### What it works out

For each of the eight module combinations:

- Total weight, center of gravity and inertia. These start from the mass budget in [decisions.md](../decisions.md); the CAD layer replaces them with exact numbers.
- Thrust-to-weight at full charge and at the 20% reserve, both under load, plus hover throttle, current and power from the thrust tables, scaled to the battery's voltage
- Whether full-throttle current stays inside the pack's continuous rating
- Hover and cruise flight times (cruise at 10 m/s for now), from a forward-flight power model plus a Li-ion battery model: usable capacity, voltage sag, and the 20% reserve counted in mAh
- The speed that uses the least power, to replace the 10 m/s placeholder
- A top-speed estimate, and a check that it can hold position in a 10 m/s wind

Drag starts as a guess from frontal area. The aero layer replaces it with real CFD numbers, and the downwash loss from CFD gets taken off the thrust.

### What comes out

- **A report:** pass/fail for every combination against every target, with margins. It's Markdown, so it reads fine on GitHub.
- **A data file for the other layers:** mass, inertia and motor constants, so everything downstream uses the same numbers.
- **Sweep mode:** it tries every motor × prop × battery in the catalog (including 6S3P packs) and ranks them by whether they pass and by how much.
- **Charts** in the project's visual style (see Visuals).

### Known limits

Manufacturer thrust data is usually optimistic, so I'm treating flight times as ±15–20% until the thrust stand (below) gives me real measurements. If I do the optional thrust stand, that happens in step 1.

### To settle before building it

These are what the sizing model discussion is for. Once one is settled, it moves to the next section.

- which real parts to seed the catalog with
- what the report looks like
- where the code lives and how it's packaged

### Settled in the sizing model talk

**Hover and cruise power (2026-10-17).** It's built on the real parts' own data.
- **Hover:** each motor has to lift a quarter of the weight. The model reads the current for that thrust straight from the manufacturer's thrust table (or the thrust stand's, if it exists), then corrects it for the battery's actual voltage under load.
- **Cruise:** the standard momentum-theory model of a rotor in forward flight, fitted so it matches the same table at hover, plus drag from the frame's frontal area. The aero side track swaps that drag guess for real numbers later.
- **The least-power speed falls out of the same model.** It sweeps through speeds and finds the one that costs the least, and that replaces the 10 m/s placeholder.
- **Why this one:** pure physics with guessed efficiencies barely uses the real parts' data, and blade-by-blade prop modeling only works for props with published wind tunnel data. That stays as a later upgrade for the props that have it (the University of Illinois propeller database is the big source).
- **Checked against:** published long-range builds with known flight times, and the thrust stand if I ever do one.

**The battery (2026-10-17).** A voltage curve plus internal resistance.
- Each cell's resting voltage against how charged it is comes from the datasheet's discharge curve, and its internal resistance makes it sag whenever current flows.
- The cells scale up to the pack (6S2P or 6S3P), plus the wiring's resistance from the electrical step.
- The model steps through a flight a few seconds at a time: the motors draw current, the voltage sags, the pack loses charge, repeat. The motors pull more current when the voltage drops, so that feedback is part of every step.
- The reserve is counted in mAh, and thrust-to-weight at the reserve uses the sagged voltage at that moment.
- **Why this one:** a fixed voltage can't show sag at all, and measured discharge tables only exist for some cells. The independent discharge tests published for popular 21700 cells are the check on this model instead.
- **Later upgrades:** a term for how the voltage bounces back a little after a burst of current, and temperature. Cold weather stays on the unproven list.

**The parts catalog (2026-10-17).** One YAML file per part, in folders by type (`design/catalog/motors/`, `props/`, `cells/`, `escs/`, `frames/`, `modules/`). Each file holds:
- **Identity:** maker, model, part number, a link, the price, and the date it was checked.
- **Physical:** mass, dimensions, mounting pattern, and a link to the manufacturer's 3D file if there is one. The CAD step reads these.
- **Ratings:** voltage, continuous and peak current, and KV for motors.
- **Data tables, each tagged with its source** (manufacturer, independent test, or thrust stand) and a link. Thrust tables live with the motor, one per prop and voltage it was tested with, because that's how manufacturers publish them. Measured data sits next to the manufacturer's as its own table. The model uses the best source it has (thrust stand, then independent test, then manufacturer), and the report says which one it used.
- **Cells** carry their voltage curve and internal resistance. Packs aren't separate parts: the model builds them from cells (6S2P, 6S3P), plus a weight allowance for the nickel strips, wires and wrap.

Tests check every file against a fixed format, so a typo can't slip through, and every number has to have a source. **Why this one:** it's readable, changes show up clearly in git, it matches `targets.yaml`, and adding a part is just adding a file. A spreadsheet can't hold a thrust table in one row, and a database is overkill for a few dozen parts and hard to review.

## The thrust stand (optional)

If I do it: once the sizing model has a shortlist, I buy one motor, two or three props, the 4-in-1 ESC, a load cell with an HX711 amplifier, and a current sensor, roughly $100–200. Most of that would end up on the drone if I build it.

- The Teensy drives the ESC and logs thrust, current, voltage and RPM (from bidirectional DShot) across the throttle range, to its SD card.
- It runs off a real 6S pack instead of a bench supply, so the voltage sag gets measured, not guessed.
- The measured data goes into the catalog next to the manufacturer's, and the sizing model uses the measured numbers when it has them.
- The stand gets bolted down, and nobody stands in line with the prop.

## Layer 2: CAD, written as code (`cad/`)

Claude writes the CAD in Python with build123d. It reads `build.yaml` and builds every part as a simple but correctly sized solid:
- the frame plates and arms, from the frame parameters
- motors, prop disks, and the battery pack, sized from its cell layout
- the flight controller stack and the safety monitor
- the module mount, the Remote ID mount, and the V, P and C module boxes
- every antenna: ExpressLRS, HaLow, GPS, and the Meshtastic relay

**What it checks:**
- prop-to-prop and prop-to-frame clearance
- prop-to-antenna clearance (in the HaLow video I watched, a prop cut straight through an antenna connector)
- that everything fits on the mount
- that the center of gravity sits close enough to the center of thrust

**What comes out:**
- **Mass properties per module combination:** each part's catalog mass is spread over its solid, which gives a real center of gravity and inertia. These replace the sizing model's estimates.
- **A STEP assembly**, which opens in any CAD tool (including Onshape, if I want to poke at it).
- **Meshes:** a simplified one for Gazebo, and a watertight surface for CFD.
- **Renders.** Quick previews come straight from Python; hero shots and turntables come from Blender.

The baseline is a plain X, modeled after a real 8–10" frame. If a real frame's STEP file is available, it gets imported instead of approximated.

## Layer 3: Aerodynamics (`aero/`)

The virtual wind tunnel. It runs as a side track, instead of inside the loop. At a 10 m/s cruise, drag is roughly 10% of the power, so even a 30% drag error moves flight time by about 3%, which is well inside the thrust data's uncertainty. Its numbers still go back into the sizing model and Gazebo whenever they're ready, and the targets get rechecked.

It's tiered by how much detail is needed.

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

- **A generator** turns `build.yaml`, the sizing output, the CAD mass properties and the aero tables (once they exist; frontal-area guesses until then) into a Gazebo model and matching PX4 airframe settings for each module combination. It's modeled on PX4's stock quad (the x500).
- **Scenario scripts** fly PX4 through the same tests every time:
  - hover, and the response to sudden stick inputs
  - a top-speed run
  - 10 m/s wind
  - hover and cruise endurance
  - failsafes: lost link, low battery
  - a parachute drop
  - a payload grab
- **False-trigger replay:** every scenario's IMU data gets run through the safety monitor's trigger logic (free fall, tumbling), counting how often it would have fired on a healthy drone. That's the first look at false triggers, long before any real flight.
- **Flight time:** Gazebo doesn't model electrical power, so I log the rotor speeds, turn them into current using the thrust data, and run that through the same battery model as layer 1. That way every layer agrees on what a battery is, and the reserve is counted in mAh everywhere.
- **Rough edges, on purpose:** the payload grab uses Gazebo's attach/detach joints, and the parachute is a simple drag model. Good enough to test the logic, not the aerodynamics.
- **Results** come out in the same pass/fail format, and runs get recorded as clips for posts.

## Layer 5: My firmware in the sim

This is step 5, but these steps leave room for it. The same Gazebo models and scenarios get reused, so my firmware gets compared directly against PX4 on identical tests.

## Alongside: the design hunt (`explore/`)

Once the baseline X passes end to end, the automation starts: build, test, read the results, improve, repeat. It runs alongside the later steps and never holds them up. The plain X is what the research is built around, and whatever the hunt finds becomes the v2 research.

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
- **Gazebo + PX4 and OpenFOAM:** the PC, in WSL2 Ubuntu 24.04. The native Ubuntu side of the dual boot is a fallback for really big runs. The laptop's WSL is only for small test cases.
- **FluidX3D and Blender hero renders:** the PC's Windows side, on the RTX 3060.
- **`scripts/setup-ubuntu.sh`:** safe to rerun, and it pins versions so both machines match. It runs inside WSL2 and comes in two halves: Gazebo Harmonic, PX4 and the Python packages first, then OpenFOAM when the CFD work starts. The Windows tools (KiCad, FreeCAD, Blender, ParaView) get their own script, `scripts/setup-windows.ps1`.
- **GitHub Actions:** reruns the lint and tests on every push, and later the sizing report too.

## Repo layout

```
design/    targets.yaml · catalog/ · build.yaml
sizing/    the sizing model
cad/       the CAD code (generated meshes stay out of git; curated ones go through LFS)
aero/      OpenFOAM cases, scripts, post-processing
sim/       Gazebo model generator, PX4 airframe, worlds, scenarios
explore/   the design hunt
media/     curated images for posts
scripts/   setup-ubuntu.sh (WSL2) · setup-windows.ps1
tests/     tests for all of the above
docs/      decisions, roadmap, specs, log, generated reports
```

## How I'll know the tools themselves work

- **Sizing model:** unit tests with hand-checked numbers, a sanity check against a published long-range build with known flight times, and then my own thrust-stand data.
- **CAD:** tests that the total mass matches the parts list, the clearances hold, and the exports are valid.
- **Aero:** the sphere and cylinder checks above, before any drone runs.
- **Generator:** every generated model has to pass Gazebo's own model check.
- **Scenarios:** a smoke test that flies PX4's stock quad through them before my design goes anywhere near them.

## Not in these steps

My own firmware (step 5), buying anything (the thrust stand is optional), the electrical design (step 3), the ground station, and the LLM.

My firmware doesn't have to wait for the baseline. It can start as soon as Gazebo works, flying PX4's stock x500, and switches to my design once the baseline passes. The wind tunnel and the design hunt keep running alongside.
