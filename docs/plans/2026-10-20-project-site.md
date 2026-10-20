# Implementation plan: the project site

*Written 2026-10-20, from the [project site spec](../specs/2026-10-20-project-site.md). Test-first, like every step. I asked for the open items to keep moving, so I made the calls below and wrote down why.*

## Where things go

| What | Where |
|---|---|
| The data command, `pcs14 site` | `src/pcs14/site/`, tests in `tests/test_site_*.py` |
| What it writes | `site/public/data/`, generated, never committed |
| The site: Vite, React, TypeScript | `site/`, with its tests next to the code (`*.test.tsx`) |
| The built site | `site/dist/`, not committed: a folder that opens from disk |
| CI | a `site` job: `npm ci`, the tests, the build, and the size check |

The data side is Python because the data is: the reports, the CAD's exports and the flight logs are all read by `pcs14` already, and the graders' own log reader turns a flight into its playback file. The site never parses a ULog or a STEP file.

## Calls made for the plan

- **Hash routing** (`#/flights/base/hover`), so every page works from `file://` and from any folder on wearechintu.com, with no server rewrites.
- **The fonts ship with the site,** through the @fontsource packages (the fonts are OFL, the packaging MIT): Space Grotesk, Inter and JetBrains Mono. No Google Fonts call from a page that's meant to work offline.
- **The meshes get thinned on the site's side, with gltfpack** (meshoptimizer's, MIT), in the site's build. It's a JavaScript-world tool for a JavaScript-world file, and the CAD's GLB stays as the CAD makes it. The size budget is set after measuring what gltfpack does to the 28 MB GLB (task 4).
- **The scene is tested through @react-three/test-renderer** (MIT): it builds the three.js scene graph without a GPU, so the tests can check that a click on a part opens its card and that switching a module off hides its parts. The picture itself gets checked by eye, with screenshots in the log.
- **Both firmwares on one playback page.** Decisions say my firmware's plots are laid over PX4's on the same test, so a flight's page plays both runs on the same clock, two drones, two sets of lines.
- **The data files carry a schema version,** and the site refuses a file with the wrong one, saying which command makes the right one. pytest checks the files against the same shapes the site's TypeScript types describe (one JSON Schema file, `site/schema/`, read by both).
- **The laptop can do most of this.** Nothing here needs the GPU. The one exception is the flights' data: the logs aren't in the repo (`*.ulg` is gitignored), so the playback files get made on the PC, which has them.

## The tasks

| # | Task | What the tests check |
|---|---|---|
| 1 | **`pcs14 site` and the schema:** the command, `site/schema/*.json`, and `index.json` (what was made, from which commit, with which version of each step's report) | The files it writes pass the schema; a missing report is listed as missing, not an error |
| 2 | **The spec sheet's data:** weights, flight times, thrust, the parts list, per combination, from `sizing.json` and `cad.json` | Every combination is there; the numbers match the reports' own |
| 3 | **The parts and wires:** `parts.json` (each piece's name, kind, mass, catalog entry, module and its node in the GLB) and `wires.json` (each route as a 3D polyline, its current, its two ends) from `cad.json` and `electrical.json` | Every piece in the GLB has a part entry and the other way round; every wire's ends are parts |
| 4 | **The site's skeleton:** Vite with `base: "./"`, React, TypeScript, Vitest and Testing Library, the style tokens from `docs/style.md` as CSS variables, the fonts, the hash router, a page that lists what `index.json` says is there, and gltfpack in the build. Measure the thinned GLB and set the first-load budget | It builds; the built `index.html` has only relative links; the budget check fails the build when it's blown |
| 5 | **The playback clock:** one clock per page, real speed by default, play, pause, a speed control, a scrubber, chapter marks from events | With fake timers: it runs at the set speed, the scrubber seeks, a chapter mark jumps to its event |
| 6 | **The charts:** a time chart (lines over the clock, the current moment marked, scrolling), bars, the pass/fail matrix, all SVG with d3-scale and d3-shape | They draw what the data says, in the style's colors; the time chart's cursor follows the clock |
| 7 | **The spec sheet page** | Every combination's numbers show, and switching combination changes them |
| 8 | **The 3D explorer:** the GLB in react-three-fiber with drei, orbit and zoom, a click on a part for its card, modules on and off, the exploded view, the wires as colored lines with their ends | Scene-graph tests: a click opens the right card, a module switched off hides its parts, a wire's click names both ends |
| 9 | **The flights' data:** a playback file per run, both firmwares (Gazebo's ground truth at 20 Hz, the motors, the events and marks, the result's findings), and the matrices | A run's file matches its log through the graders' reader; the sizes stay near the spec's few hundred kilobytes |
| 10 | **The flight pages:** the matrix, then a run's page with the drone flying its path in 3D, the charts scrolling, the events popping up as they come, PX4's run and mine together | On the clock: the drone is where the log says at a given moment, an event shows at its time, the two runs stay in step |
| 11 | **A page per step,** from each report: what it decided, its numbers, its stills, its log entries | Each step's page names its report's verdict and links its log entries |
| 12 | **The wind tunnel:** its frames on the clock, then its streamlines in 3D when the tunnel exports them | The frames play in order at their time step |
| 13 | **Polish and the size check:** the home page (the drone and one quiet line per step), load times, keyboard use, a phone-width check | The first load stays inside the budget; every page works at 375 px wide |

**Done when:** the whole project opens from a folder on disk, every step has its page, and every flight plays back.

## Where it stands

| Date | Tasks | Notes |
|---|---|---|
| 2026-10-20 | none yet | Plan written |
