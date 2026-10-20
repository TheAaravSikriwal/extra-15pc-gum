# 2026-10-20: Three wind tunnel cases, and a drone the wind passed straight through

*PC, Windows. The Aero side track's visual half, round two.*

The [first wind tunnel run](2026-10-20-first-wind-tunnel.md) was one hand-written case. This round, `pcs14 tunnel` writes a case file and FluidX3D reads it, so one build runs all three:

| Case | What it is |
|---|---|
| cruise | every module on (Max), nose into a 10 m/s wind, pitched the way it cruises |
| crosswind | the same wind from the side, the one the hover has to hold against |
| hover | still air, all four props spinning at the hover's speed, the clockwise pair mirrored |

## What broke

Two things, in order.

The first run asked FluidX3D for 6000 MB of the RTX 3060's 12 GB, and it refused: the card's OpenCL driver caps any single buffer at a quarter of its memory, and the biggest one (19 numbers per cell) wanted 3.4 GB. At 5000 MB it fits, which is about 78 million cells of 3.7 mm.

The second was better. The pictures came out with the whole tunnel at one speed and no wake at all, as if the drone weren't there. To spin the props I'd turned on FluidX3D's moving boundaries, which let a solid cell carry a velocity. And my setup gave every cell that wasn't exactly "solid" the wind's speed. The body's cells are marked solid plus one more flag, so they weren't exactly solid, so they got the wind's speed too, and the whole drone became a wall moving downwind at 10 m/s, invisible to the air. One check, `!=` where it needed a bit test.

## What it shows now

At cruise, the air bends around the body and leaves a slow, churning wake behind it, with the flow speeding up over the top and bottom edges. From the side, the wake is wider and messier: more drone faces the wind.

FluidX3D reports about 2.0 N of drag at cruise, a drag area near 330 cm², and about 4.1 N side-on. The first run, on coarser cells, said 230 cm². That spread on its own says these aren't measurements. FluidX3D's own docs say its drag runs 1.3 to 2 times high without a wall model, and the sizing model uses 202 cm² for Mission (Max carries more). The drag tables still come from OpenFOAM.

The hover case runs, but its pictures don't work yet. The slice for the speed picture goes through the middle of the drone, which on an X layout is between the props, and the color scale is set for a 10 m/s wind, so the downwash barely shows. The crop also puts the drone at the very top edge. Those are fixable: a slice through a pair of props, a longer run so the downwash reaches further, and a color scale for the hover.

## Where the pictures are

On my PC, not in the repo. FluidX3D's license asks for the altered source to be published with any results that are, so the stills wait until my FluidX3D fork is public, and that's my call to make.

## Next

The hover's visuals, then the fork, then OpenFOAM for numbers I can lean on, starting with a sphere.
