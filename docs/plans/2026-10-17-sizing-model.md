# Implementation plan: the sizing model

*Step 1b, written and OK'd 2026-10-17. It turns the decisions in the [spec](../specs/2026-10-13-phase-1-simulation.md#settled-in-the-sizing-model-talk) into code, one test-first task at a time.*

## What it builds

`pcs14`, the project's Python package ("14 pcs left"), with the sizing model as its first layer. Give it a parts list and it says, for every module combination, whether the drone hits its targets, by how much, and how sure it is. Every simulated flight streams into Rerun as it runs.

## Where things go

```
src/pcs14/
  units.py        conversions, only where data comes in or goes out
  catalog/        the parts files: format checks and loading
  design.py       targets.yaml and build.yaml, as objects
  sizing/
    mass.py       the mass budget for every module combination
    battery.py    cell voltage curve + resistance, scaled to the pack
    rotor.py      thrust tables for hover, the fitted forward-flight model
    drag.py       frontal-area drag, until the aero track has real tables
    flight.py     steps a flight down to the reserve, recording a timeline
    checks.py     every target as a check: pass, marginal or fail
    sweep.py      every motor, prop, cell and pack layout, ranked
  viz/            streaming to Rerun
  report/         the Markdown report, charts, and the data file
  cli.py          pcs14 size, pcs14 sweep, pcs14 report
design/catalog/   motors/ props/ cells/ escs/ frames/ modules/
design/build.yaml which part fills each slot, and what's in V, P and C
docs/reports/sizing/
tests/fixtures/   small made-up parts, clearly labeled, for tests only
```

**New dependencies:** numpy, scipy, pyyaml, pydantic (catalog checks), matplotlib (report charts) and rerun-sdk, all pinned. Each one gets added by the task that first needs it, so every commit stays small. They're all under permissive licenses, which fit this GPL-3.0 repo.

**Units:** meters, kilograms, seconds, newtons and watts everywhere inside. Grams, millimeters, inches, mAh and km/h only exist in the files and the report.

**Made-up test parts never pass for real ones.** They live in `tests/fixtures/`, every one is labeled as made up, and nothing from them ever reaches the real report.

## The tasks

Each one is test-first: write the tests with hand-checked numbers, make them pass, commit and push with CI green.

| # | Task | What the tests check |
|---|---|---|
| 1 | **Package skeleton:** `src/pcs14`, the `pcs14` command in `pyproject.toml`, and CI and the setup scripts installing the package | It imports, and `pcs14 --version` runs |
| 2 | **Units** | Every conversion against hand-worked numbers |
| 3 | **Catalog format and loader:** a format per part type, source tags, unit conversion on load, and the rule that every number has a source | A good file loads. A missing source, a missing unit or a typo fails with a clear message. |
| 4 | **Targets and build file** as objects | They load, and a build that names a part that isn't in the catalog fails clearly |
| 5 | **Mass budget:** all eight module combinations, Max's payload, and the growth margin on the sizing case | Hand-checked sums |
| 6 | **Battery model:** voltage curve, internal resistance, 6S2P and 6S3P, wiring, charge used in mAh | Pack numbers by hand. A steady drain empties at capacity ÷ current. The comparison against a published discharge curve moved to step 1d, since it needs a real cell's sourced data. |
| 7 | **Hover from the thrust tables:** current and power for a thrust at a voltage, maximum thrust at a sagged voltage, and the best data source picked | Hand-checked interpolations, and the source order (thrust stand, then independent test, then manufacturer) |
| 8 | **Forward flight:** the rotor model fitted to the hover table, frontal-area drag, power against speed, the least-power speed, top speed, and holding position in 10 m/s wind | It matches hover at zero speed, power dips then rises with speed, and one hand-worked case |
| 9 | **The flight stepper:** hover and cruise flights stepped down to the reserve, with sag and current feeding each other, recording voltage, charge, current and thrust headroom | A steady-power sanity check, it stops at 80% used, and thrust-to-weight at the reserve |
| 10 | **Rerun:** every flight timeline streams into the viewer as it runs and gets saved as a recording | It writes a recording without a viewer open |
| 11 | **Checks and verdicts:** every target as a check with its margin, and pass, marginal or fail from the uncertainty bands (±15–20% for manufacturer data, tighter for measured) | A made-up drone that should pass, one that should be marginal, one that should fail |
| 12 | **Sweep and ranking:** every combination from the catalog, ranked, plus the margin chart's data (minutes per extra 100 g). The sweep fills in live in Rerun. | A tiny made-up catalog with an obvious winner |
| 13 | **The report:** verdict table, mass budget, data sources, top candidates, charts in the project's look (from `media/style.yaml`), and the data file for later steps | The report matches a known-good copy for the test catalog, and the charts come out at the post sizes |
| 14 | **Command line:** `pcs14 size`, `pcs14 sweep`, `pcs14 report`. CI runs the whole thing on the test catalog on every push. | Smoke tests |
| 15 | **The honesty check:** run the model on two or three published long-range builds with known flight times, and write down how far off it is | If it's way off, I stop and fix the model before step 1d |

**What I can see, and when:** from task 10 on, `pcs14 size` on a test drone plays every flight in Rerun. From task 13 on, there's a report to read and charts to post.

## After this plan

- **Step 1d:** research and add the real parts (about 15–20 files, every number sourced, with the list getting a look before the sweep runs), run the sweep, and pick the parts and the final growth margin.
- **The project site's spec,** so its first pages (the spec sheet, the verdicts, the sweep explorer, the flight replays) can come right after, reading the same data file.
