# The project site

*Partly superseded: its home page and its pages' layout, by [the drone view](2026-10-21-the-drone-view.md) on 2026-10-21 (one 3D drone as the home), then by [the docs](2026-10-22-the-docs.md) on 2026-10-22 (the menu as the drone's manual). What it's built with, the data and the playback still stand.*

*Written 2026-10-20. I asked for the open items to keep moving without stopping to ask, so I made these calls myself and wrote down why. The goal itself was set earlier, in my own words, in [decisions.md](../decisions.md) under "The project site".*

## What it has to be

A complete blueprint of the drone on one website: an in-depth 3D model I can click into and look around, from the structure down to the circuits and where everything connects, a live spec sheet, a page per step, and every simulation that was run, played back as if it were happening live. Everything animated.

The fixed rules, from decisions.md:

- It stays on my machine while the research runs, and goes public only when the project is done, as another project on my portfolio, wearechintu.com.
- So it's a self-contained static site with relative links: a folder of files, no server.
- It's built from the data files every step writes, so it grows as the steps finish.
- The simulations are played back, not run in the browser: the drone flying each scenario's logged path, its height, speed and motors scrolling alongside, the events (the chute firing, the link cutting) popping up as they happen, and the wind tunnel's flow animated around the drone.
- The project's look from [docs/style.md](../style.md): tunnel black, chalk, spearmint, turbo for CFD fields, Space Grotesk, Inter and JetBrains Mono.

## Decided

**What it's built with (2026-10-20): Vite, React and TypeScript.** My portfolio is Next.js 14 on React 18 with TypeScript, Tailwind and Vitest, so the project site speaks the same language and its pieces could move into the portfolio later. But it's built with Vite as a plain static bundle with relative paths (`base: "./"`), not as a Next.js app: then it's just a folder that drops into the portfolio wherever it ends up, and it doesn't care which Next.js version the portfolio runs by then. **Cost:** if I ever want it as pages inside the portfolio itself, the routing gets redone in Next.js.

**The 3D (2026-10-20): three.js through react-three-fiber, with drei's helpers** (all MIT). The CAD already exports a GLB of every piece on every run. The site loads it, lets me orbit, zoom and click any part for its card (what it is, its mass, its catalog entry, where it connects), switch modules on and off, and pull the drone apart into an exploded view. The wire routes from `cad.json` and `electrical.json` become lines in the same scene, colored by how hard each wire works, so a click on a wire shows both its ends. **Why three.js and not my portfolio's ogl:** ogl is a tiny WebGL layer, which suits the portfolio's effects; a model explorer with picking, a GLB loader and an orbit camera is what three.js and drei already do.

**Charts (2026-10-20): SVG drawn by React, with d3-scale and d3-shape for the math** (ISC). The charts are simple (lines over time, bars, a pass/fail table), and plain SVG takes the style guide's colors and fonts directly. No charting framework to fight.

**The data (2026-10-20): a `pcs14 site` command writes everything the site reads** into `site/public/data/`, generated and never committed, like every other build output:

| Data | From |
|---|---|
| The spec sheet: weights, flight times, thrust, the parts list | the sizing report's `sizing.json` and the CAD's `cad.json` |
| The 3D model and its parts | the CAD's GLB, with the meshes thinned for the browser, and `cad.json` |
| Wires, pins and connections | `electrical.json` |
| Each flight, for playback | the flight sim's logs, through the graders' own reader: Gazebo's ground truth at 20 Hz, the motors, and the events and marks, one small file per run |
| The pass/fail tables | the flight sim's results |
| The wind tunnel | the tunnel's frames and fields, later its streamlines as 3D lines |

A run's playback file is a few hundred kilobytes, so all 78 flights come to about 25 MB before compression.

**Playback "shown live" (2026-10-20):** one clock drives a run's page. The drone's model moves and turns along the logged path in the 3D scene, the charts scroll with the clock, and each event appears when its moment comes. It plays at real speed by default, with a scrubber, a speed control and the events as chapter marks. The wind tunnel runs the same way: its frames, then its streamlines, animate on the clock.

**Tests (2026-10-20): Vitest and Testing Library, like the portfolio,** for the site's code, and pytest for `pcs14 site`'s files, checked against the same schema the site reads.

**Where it lives (2026-10-20): `site/` in this repo.** The built site (`site/dist/`) and its data aren't committed. On the portfolio's homepage it'll get one quiet line, like every other project there; the detail lives on its own pages.

## Not settled yet

- The exact pages and their order, past the four the roadmap names (the 3D drone, the spec sheet, a page per step, every sim). Settled in the plan.
- How far to thin the CAD's meshes for the browser, and a size budget for the first load. Measured, then set.
- The connector-level detail: the CAD places each board but not each connector on it, so a wire's ends in 3D are a route's ends, not the plug. Noted in decisions as a gap for later.
- Whether the wind tunnel's flow goes in as frames, as streamlines, or both. Depends on what the tunnel exports well.

## Next

The implementation plan, then the build, test-first, starting with what already has data: the spec sheet and the 3D model from steps 1 to 3, then the flight playback from step 4.
