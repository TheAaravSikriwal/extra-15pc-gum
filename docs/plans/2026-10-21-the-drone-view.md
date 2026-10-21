# The drone view: the plan

*Written 2026-10-21, from the [spec](../specs/2026-10-21-the-drone-view.md). Test-first, task by task.*

## Where things go

| What | Where |
|---|---|
| The view: one stage, two modes, the corner menu | `site/src/stage/`, tests beside them |
| The blueprint | `site/src/stage/Blueprint.tsx` |
| The pins' positions | the catalog's `cad` blocks, `connectors`, each with its source |
| Every wire in 3D, as data | `src/pcs14/site/wires3d.py`, writing `wires3d.json`; tests in `tests/test_site_wires3d.py` |
| Every run on the site | `src/pcs14/site/flights.py` |
| The animations | `site/src/fly/clip.ts`, tested on made-up runs |

## The tasks

| # | Task | What the tests check |
|---|---|---|
| 1 | **The stage:** one canvas that never unmounts, two modes by route (`#/` inside, `#/fly/<scenario>`), the Inside it / Fly it switch, the corner menu with every other page, the intro in a corner panel | The route picks the mode; the canvas survives a mode change; the menu has every page |
| 2 | **The blueprint:** the generic quad's drawings, the grid and the title block behind the canvas, cross-fading to white | It's drawn in inside mode and gone in fly mode |
| 3 | **The pins, researched:** each board's connectors placed on it, from the makers' drawings where published, estimated and marked elsewhere | Every connector a wire lands on has a position and a source; estimates are marked |
| 4 | **Every wire in 3D, as data:** each wire's two pins in the drone's frame (the board's placement, the connector's spot, the pin's pitch), its route's points, the pieces its ends ride with, its gauge, type and cut length | Every wire once; its ends on their placed boards; its route from the CAD |
| 5 | **The wires on the model:** a tube per wire from pin to pin through its route, stretching with the pulled-apart view; lighter on phones | An end moves with its piece; the route points blend between the two |
| 6 | **Exploring the wires:** a board lights its wires, a wire flies the camera to its pin and shows its card, the harness list, labels up close | Selection, the camera's target, the harness filter |
| 7 | **Every run on the site:** every flown scenario from steps 4 to 7, both firmwares where both flew, each with what it tests and its result | The runs from steps 6 and 7 are there |
| 8 | **The animations:** each run's window, its time warp (a 15 to 30 s loop, key moments at real time), eased from and to a calm hover; a crash fades and resets | On made-up runs: the loop's length, real time near events, the hover at both ends, the crash's fade |
| 9 | **Fly it:** the white space, the following camera, the trail and the ground grid, each scenario's props, the numbers and motor bars, the scenario list, the PX4 switch, the modules choosing the combination, easing between scenarios | The combination from the modules; a scenario not flown says so; the switch eases to hover first |
| 10 | **The transition:** Inside it to Fly it and back in 1.2 s, the background, the camera and the interface together | The timing's curve; nothing jumps |
| 11 | **Phones:** touch orbit and pinch, the drawer, lighter wires | The layout at phone width |
| 13 | **Materials and light:** carbon weave, anodized bells, circuit boards, the wires' colors, matte prints, soft light and shadows, all drawn in code | Every piece kind gets its material; nothing fetched at runtime |
| 14 | **Real shapes in my own CAD:** twisted props, detailed motors, the frame's cutouts, boards with their chips and connectors | The new shapes keep each part's mass and outline checks passing |
| 15 | **The makers' free models,** after I approve each download: ARK GPS, ARK CANnode, Pi 5, Teensy 4.1, thinned for the web, each with its license and credit | Each model's license is beside it; the site's size stays in budget |
| 12 | **The log, the README and the site rebuilt,** checked in the browser at desktop and phone sizes | It's written, and it works |

## Where it stands

| Date | Tasks | Notes |
|---|---|---|
| 2026-10-21 | 1 and 2 done | The stage: one canvas that stays mounted (a page opens over it, with the way back), the Inside it / Fly it switch, the corner menu with the ten other pages, the intro in a corner. The 3D code loads after the first paint, so the first load stays at 291 kB of the 600 budget. The blueprint: a generic X quad's top and side views, a prop and a motor in detail, dimension lines and a title block on a blueprint-blue grid, the middle kept clear for the drone; it cross-fades to white in 1.2 s when it flies. Tasks 13 to 15 added for the drone's detail |
| 2026-10-21 | none yet | Plan written |
