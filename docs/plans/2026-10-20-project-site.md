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

- **Hash routing** (`#/flights/base/hover`), so every page works from `file://` and from any folder on wearechintu.com, with no server rewrites. (And since browsers won't `fetch()` from `file://`, each data file also comes as a script the page can load with a script tag; decided while building task 4.)
- **The fonts ship with the site,** through the @fontsource packages (the fonts are OFL, the packaging MIT): Space Grotesk, Inter and JetBrains Mono. No Google Fonts call from a page that's meant to work offline.
- **The meshes get thinned on the site's side, with gltfpack** (meshoptimizer's, MIT), in the site's build. It's a JavaScript-world tool for a JavaScript-world file, and the CAD's GLB stays as the CAD makes it. The size budget is set after measuring what gltfpack does to the 28 MB GLB (task 4).
- **The scene is tested through @react-three/test-renderer** (MIT): it builds the three.js scene graph without a GPU, so the tests can check that a click on a part opens its card and that switching a module off hides its parts. The picture itself gets checked by eye, with screenshots in the log.
- **Both firmwares on one playback page.** Decisions say my firmware's plots are laid over PX4's on the same test, so a flight's page plays both runs on the same clock, two drones, two sets of lines.
- **The data files carry a schema version,** and the site refuses a file with the wrong one, saying which command makes the right one. The shapes are pydantic models (`pcs14.site.schema`; pydantic is already a dependency, so no JSON Schema validator joins it): `pcs14 site` builds the files through them, pytest reads them back through them, and `pcs14 site --schema` exports them as JSON Schema into `site/schema/` for the site's TypeScript. A test fails when the exported copy goes stale.
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
| 2026-10-20 | All 13 done, and what the plan left out | Going back over decisions.md after task 13, the plan's tasks had skipped a few things I'd asked for, so they went in too: what the sims can't prove, one quiet line from the home page; each step's topics in the learning file; the weight and hover time following the modules in 3D; the drone turning slowly with its props spinning; the wiring page with every board's pin map, the harness diagrams and the schematic; the spec sheet's checks as pass, marginal or fail; and the flight pages flying the CAD's model instead of a stand-in. Two bugs on the way: the exploded view pushed pieces along the wrong axes inside the GLB's turned frame, and a run's page kept the last run's problem when it moved to another. The tunnel's frames came from a rerun with the fork writing them |
| 2026-10-20 | 5 to 11, and 13; 12's code in | The clock and its controls, the charts, the spec sheet page, the drone in 3D (click a part for its card, switch modules off, pull it apart, the wires colored by how hard they work), every flight as a playback file with both firmwares on one clock, and a page per step built from the README's own plan, so nothing is written twice. The home page is the drone and one quiet line per step. Every page checked at 375 px wide with nothing spilling off the side, a part picker on the 3D page so it works from the keyboard, and a focus outline on everything you can tab to. The first load is 262 of 600 kB; three.js (816 kB) only loads when a 3D page opens. For the wind tunnel I changed my FluidX3D fork to write 40 frames along each run, with each frame's time, and `pcs14 site --tunnel` thins them to JPEGs the page plays on its clock at 0.02x. The tunnel needs a rerun to make those frames, which waits for the flight batch to finish. Its pictures stay on my machine until the fork is public: the page says so, and the build check warns when they're in a build |
| 2026-10-20 | 3 and 4 done | The skeleton: Vite 5, React 18 and TypeScript, Vitest with Testing Library, pinned to exact versions with the lockfile committed, and a `site` job in CI. The style's colors and fonts as CSS variables, with a pytest check that they stay `media/style.yaml`'s; the fonts ship with the site, Latin only. Hash routing, and a home page listing what `index.json` says is there. The build fails on any absolute link or a first load over 600 kB: the skeleton is 329. One finding on the way: browsers won't `fetch()` from a page opened as `file://`, which the plan promised would work, so `pcs14 site` also writes each data file as a small script, and the loader adds that as a script tag when the page is opened from disk. The CAD's 11.9 MB GLB thins to 3.0 MB with gltfpack at half the triangles, all 86 piece names kept; the 3D page's own budget gets set with task 8. Task 3 finished with the CAD and electrical reports rerun: 86 pieces, 28 routes, every one matched to the GLB |
| 2026-10-20 | 1 and 2 done, 3's code in | `pcs14 site` writes `index.json` (each report found or not, from which commit) and `spec.json` (every combination's weights, checks and speeds, and the parts list with counts), through pydantic models exported to `site/schema/`. For task 3 the CAD report now lists its pieces, named as the GLB names its nodes, and the electrical report lists the wires along each CAD route; `parts.json` and `wires.json` get written once both reports are rerun. Task 4 needs `npm install`, which downloads the site's packages, so it waits for my yes |
| 2026-10-20 | none yet | Plan written |
