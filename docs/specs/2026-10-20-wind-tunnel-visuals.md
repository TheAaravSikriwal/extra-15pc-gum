# Wind tunnel visuals (the Aero side track's first half)

*Started 2026-10-20. I wanted to see the drag, not just read the number, so the pictures come before the OpenFOAM numbers this time. I made the routine calls and wrote them down here.*

## What it produces

Pictures of the air around the drone, good enough to post: the drag lines (streamlines) and the wake at the 10 m/s cruise, the crosswind the hover holds against, and the downwash under the spinning props. Not numbers. FluidX3D reports a force, but its own documentation says that force runs 1.3 to 2 times high without a wall model, so it's labeled visual-grade everywhere. The drag tables still come from OpenFOAM, proven on a sphere first, as the roadmap says.

## How

**FluidX3D on the PC's RTX 3060, on Windows.** It's a lattice Boltzmann solver that runs on the GPU: 60 to 90 million cells, a few minutes a case. It lives in `C:\dr\fluidx3d`, outside this repo, because its license isn't GPL-compatible. My changes to it are marked as altered source and committed in that clone:

- one setup that reads the case from `bin/case.txt`, so one build covers every case
- turbo colors (the project's CFD colormap) in place of its rainbow
- build switches: frames written to disk at 2560 x 1440, forces on the body, open tunnel walls, moving solids for the props, and the Smagorinsky subgrid model for the high Reynolds numbers

Its license wants the altered source published with any results, so it becomes a public fork before any picture is posted. Until then the frames and stills stay in `outputs/tunnel/`.

**`pcs14 tunnel`** does the rest from this repo: it exports the combination's watertight body and its four props from the CAD (in meters, in the drone's own frame, so they land together), writes the case, runs FluidX3D, and puts the frames on the project's post canvas in all four sizes. None of FluidX3D's code is in this repo; it only calls the program.

## The cases

| Case | The air | The drone | The box |
|---|---|---|---|
| cruise | 10 m/s head-on | nose into the wind, pitched forward by the sizing model's cruise tilt | 1.4 x 3.2 x 1.1 m, drone a third of the way down |
| crosswind | 10 m/s from the right | level, side on | the same |
| hover | still | the props spinning at the flight sim's hover speed | 1.2 x 1.2 x 2.2 m, drone high up so the downwash has room |

The props are the CAD's three-blade stand-ins (flat blades at the pitch angle), in PX4's quad X: front right and back left counterclockwise, front left and back right clockwise, with the clockwise pair mirrored the way real props come, so all four push air down. Their tips run at about 77 m/s at hover, which sets the lattice's velocity scale in that case.

The first look (Max, the cruise, props static, 4.3 mm cells) came out of an earlier build of the same setup; its [log](../log/2026-10-20-first-wind-tunnel.md).

## Not settled

- Clips. Frames over time make a video for posts, but videos never go in the repo; when they're wanted, they're rendered on request.
- The other combinations. Max (every module on) is the default because it's the busiest shape; any combination runs with `--setup`.
