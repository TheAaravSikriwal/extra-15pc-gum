# The drone view: the site around one 3D drone

*Partly superseded: the corner menu's pages, by [the docs](2026-10-22-the-docs.md) on 2026-10-22, which made them twelve pages in four groups with the catalog merged into Parts. The view itself still stands.*

*Talked through and locked in on 2026-10-21. My answers are the design; the calls marked as mine were made while writing this, and written down why.*

## The idea

A minimal site where the drone is always in view, front and center. One 3D drone, two modes, and only the background and the interface around it change between them.

- **Inside it** (the home page). A classic blueprint background: deep blueprint blue, a fine white grid, and white technical drawings of a generic quad (not this drone), with a title block. The drone is assembled and turning slowly. It merges the old "The drone in 3D" and "The wiring": switch modules off, pull the drone apart, and every wire stays drawn in 3D between its two pins, stretching as the parts spread. Click a board and its wires light up while the rest fade; click a wire and the camera glides to its pin, with both ends, the gauge and the cut length; a harness list isolates one harness; labels appear only up close.
- **Fly it.** The blueprint fades into blank white space and the drone floats in the middle. Pick a simulation and it plays as an animation of the real recorded run, the camera following so the drone stays centered. Its motion shows in its tilt, its props, a fading trail and a faint ground grid far below. Only what a scenario is about appears, in light gray lines: the canopy in a drop, wind streaks, the column of rising air, the shed, box and trees, the helix.
- **Everything else stays where it is,** in one small corner menu: the spec sheet, every step, every flight (with its charts, and a link from each run into the new view), the wind tunnel, what it can't prove, Build it, the library, the catalog, the data and the math. Opening one replaces the view until you come back.

## What was decided, and why

| Question | Answer |
|---|---|
| How motion shows | The camera follows; the drone never leaves the center |
| What the animations are | The real recorded runs, trimmed, smoothed, eased at both ends |
| Which run plays | Every flown scenario; the modules switched on pick the combination; my firmware by default, a PX4 switch where PX4 flew it; a scenario never flown for that combination says so |
| The wires' pins | Researched from the makers' drawings where published (ARK FPV, Teensy 4.1, the ESC, the Pi 5, the receiver, the BEC, the ARK GPS and CANnode, the TF-Luna), estimated elsewhere and marked as estimated; every position in the catalog with its source |
| The blueprint | Classic blueprint blue, white grid and drawings |
| Around the floating drone | The scenario's name and what it tests, height, speed and time, a bar per motor, the result in one line |
| Where it opens | The blueprint, with an Inside it / Fly it switch at the top and the other pages in a corner menu |
| Exploring wires | Click a board, click a wire to fly in, a harness list, labels up close |
| Changing scenario | The drone eases back to a calm hover in about a second, then the next starts; every animation loops from hover to hover |
| Long runs | Sped up to a 15 to 30 second loop with the speed shown, key moments slowed to real time |
| The home page and every flight | The new view is the home; every flight stays, with links into the view |
| Phones | Desktop first, but it works on a phone: touch orbit, pinch zoom, the text in a drawer, lighter wire detail |
| What else appears in the white space | Only what tells the story |

## Calls I made while writing this

- **The blueprint's drawings are mine,** in SVG: a generic X quad's top and side views with dimension lines, a prop disc, a stack, and a title block reading like a drawing sheet. Not this drone, as asked.
- **A crash doesn't ease back to hover.** A run that ends on the ground (the dead motor without P) fades out at its end and fades back in at the hover, so the loop stays honest about how it ended.
- **The transition takes 1.2 s:** the background cross-fades, the camera eases to the floating framing, the interface swaps.
- **Animations are made in the browser** from the flight sim's playback files the site already has (20 samples a second), so nothing gets duplicated: the window, the time warp and the easing are small, tested functions.
- **Key moments** come from each run's own events (a step, a failure, the chute firing, the monitor's cut): within 1.5 s of one, the animation plays at real time.
- **The site's flights grow** to every flown run from steps 4 to 7, both firmwares where both flew, about 50 more runs.
- **Wire ends ride with their boards.** In the pulled-apart view each end moves with the piece it's on; the wire's route points between move with a blend of the two.

## The drone's detail (added 2026-10-21)

The drone should look like a drone, not boxes in flat colors. Decided: my own detail, in stages, plus the makers' free models where their terms allow showing them in public. I approve each download.

1. **Materials and light.** The frame in carbon weave, the motors' bells in anodized metal, the boards as circuit boards (solder mask, gold pads, chips), the wires in their insulation's colors (red and black for power), the printed parts matte, the pack in its wrap, and soft light and shadows. Textures are drawn in code, so nothing is downloaded, and the light is made in the scene, not fetched (drei's ready-made environments load from a CDN).
2. **Real shapes, in my own CAD code,** for the parts that set the look: three-blade props with twisted blades, motors with their bells, cooling holes and windings, the frame's plates with their cutouts, and boards with their chips, connectors and headers where the pins research puts them.
3. **The makers' models, where their terms allow it.** From the CAD step's own research: the ARK GPS and ARK CANnode (BSD-3-Clause), the Raspberry Pi 5 (MIT, 77 MB, so it gets thinned for the web) and the Teensy 4.1 (its author allows it with credit). The others it found (Holybro's ESC, the ARK FPV, Pololu's regulator, the Camera Module 3) reserve their rights, so they stay my own shapes. A model goes in only with its license and credit beside it.

## What it can't do yet

- Some boards publish no drawing (the small breakouts), so their pins are estimates for now, marked as such.
- The simulations are the sims' own flights, so whatever the sims couldn't model (the vortex ring state, rising air on the rotors) isn't in them either. The unproven page still says so.
- The data for every run in both firmwares is tens of megabytes; fine locally, trimmed before anything goes public. The wind tunnel stays local until the FluidX3D fork is public.
