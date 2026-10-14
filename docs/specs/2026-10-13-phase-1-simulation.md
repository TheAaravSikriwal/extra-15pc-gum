# Phase 1: Simulating the design

*Written 2026-10-13, before any code. Like everything else here, it will change once real numbers show up.*

This is how I'm going to prove the drone works before buying a single part.

## What Phase 1 has to produce

A parts list that passes every target in simulation, across all eight module combinations, with a price on it. Nothing gets ordered before that exists.

The targets are locked in [decisions.md](../decisions.md) and live in machine-readable form in [design/targets.yaml](../../design/targets.yaml):

| Setup | Modules | Flight time | Other targets |
|---|---|---|---|
| Base | none | ≥ 30 min | Thrust-to-weight ≥ 4:1 |
| Mission | V + P | ≥ 25 min | Top speed ≥ 80 km/h; holds position in 10 m/s wind |
| Max | V + P + C, carrying 250 g | ≥ 20 min | Thrust-to-weight ≥ 3:1; total weight ≤ 2.5 kg |

Every setup lands with at least 20% battery left, and flight time means cruising, not hovering. The other five combinations have to land somewhere between Base and Max.

## The loop

```
pick parts → sizing model → CAD → Gazebo + PX4 → pass/fail → swap parts → repeat → price it
```

Layers 1 and 2 are fast and cheap, so I'll run them constantly. Layers 3 and 4 are slower, and their job is to confirm (or embarrass) what the first two say.

## Layer 1: Parts files and the sizing model

### The parts files (`design/`)

One place describes the whole drone, and everything else reads from it.

- **`catalog/`:** candidate parts, one file per type: motors, props, batteries, ESCs, frames, module parts.
  - Every part has a mass and a size.
  - Motors and props carry the manufacturer's thrust test data: throttle, thrust and current, at a stated voltage.
  - I'll start it off with 3–4 real candidates of each motor, prop and battery.
- **`build.yaml`:**
  - which part fills each slot
  - where each part sits, in mm from the center of the frame. The axes are x forward, y left, z up, the same as Gazebo and ROS, so nothing needs converting later.
  - what's in V, P and C. The 250 g grabbed object counts as part of C.
- **`targets.yaml`:** the numbers above.

Swapping a part means changing one name in `build.yaml`.

### What it works out

For each of the eight module combinations:

- Total weight, center of gravity and inertia, estimated from part sizes until CAD numbers replace them
- Thrust-to-weight, plus hover throttle, current and power from the thrust tables, scaled to the battery's voltage
- Cruise flight time, from a forward-flight power model plus a Li-ion battery model: usable capacity, voltage sag, and the 20% reserve
- A top-speed estimate, and a check that it can hold position in a 10 m/s wind

### What comes out

- **A report:** pass/fail for every combination against every target, with margins. It's Markdown, so it reads fine on GitHub.
- **A data file for the sim:** mass, inertia and motor constants, so Gazebo is fed the same numbers.
- **Sweep mode:** it tries every motor × prop × battery in the catalog and ranks them by whether they pass and by how much.

### Known limits

Manufacturer thrust data is usually optimistic, so I'm treating flight times as ±15–20% until the Phase 3 thrust stand gives me real measurements. Drag is a guess from frontal area until CAD gives me something better.

### To settle before building it

These are what the sizing model discussion is for:

- the exact math for cruise power and the battery model, and what I validate them against
- what cruise speed "flight time" actually means
- the catalog file format, and which real parts to seed it with
- what the report looks like
- where the code lives and how it's packaged

## Layer 2: CAD (Onshape)

- I model it in Onshape, using public documents. I'll start from manufacturers' STEP files wherever they exist.
- A short modeling guide keeps the CAD and `build.yaml` in sync: same axes, same units, same part names.
- Onshape's mass properties (mass, center of gravity, inertia) go into `build.yaml` and override the estimates.
- Meshes go into `sim/` through Git LFS, and the renders go into posts.

## Layer 3: Gazebo + PX4

- **A generator** turns `build.yaml` plus the sizing output into a Gazebo model and matching PX4 airframe settings for each module combination. It's modeled on PX4's stock quad (the x500).
- **Scenario scripts** fly PX4 through the same tests every time:
  - hover, and the response to sudden stick inputs
  - a top-speed run
  - 10 m/s wind
  - full endurance
  - failsafes: lost link, low battery
  - a parachute drop
  - a payload grab
- **Flight time:** Gazebo doesn't model electrical power, so I log the rotor speeds, turn them into current using the thrust data, and run that through the same battery model as layer 1. That way both layers agree on what a battery is.
- **Rough edges, on purpose:** the payload grab uses Gazebo's attach/detach joints, and the parachute is a simple drag model. Good enough to test the logic, not the aerodynamics.
- Results come out in the same pass/fail format, and runs can be recorded for posts.

## Layer 4: My firmware in the sim

This is technically Phase 2, but Phase 1 has to leave room for it. The same Gazebo models and scenarios get reused, so my firmware gets compared directly against PX4 on identical tests.

## Where things run

- **Sizing and CAD:** either machine.
- **Gazebo + PX4:** mainly the PC on native Ubuntu 24.04. The laptop's WSL is for light checks only, since its integrated graphics need simple scenes.
- **`scripts/setup-ubuntu.sh`:** safe to rerun, and it pins the versions of PX4, Gazebo Harmonic and the Python packages, so both machines match.
- **GitHub Actions:** reruns the lint and tests on every push, and later the sizing report too.

## Repo layout

```
design/    targets.yaml · catalog/ · build.yaml
sizing/    the sizing model
cad/       Onshape links, mass properties, meshes (LFS)
sim/       model generator, PX4 airframe, worlds, scenarios
scripts/   setup-ubuntu.sh
tests/     tests for all of the above
docs/      decisions, roadmap, specs, log, generated reports
```

## How I'll know the tools themselves work

- **Sizing model:** unit tests with hand-checked numbers, plus a sanity check against a published long-range build with known flight times.
- **Generator:** every generated model has to pass Gazebo's own model check.
- **Scenarios:** a smoke test that flies PX4's stock quad through them before my design goes anywhere near them.

## Not in Phase 1

My own firmware (that's Phase 2), buying anything, the ground station, and the LLM.
