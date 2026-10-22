# The wind tunnel in Fly it

*Agreed 2026-10-22, in chat, and redone the same day after my first look: the first version traced lines through the averaged flow, which missed most of the air's movement, had the air appear out of nowhere at its rake, and showed the wake as a still picture. The plan is in [plans/2026-10-22-the-wind-tunnel-in-fly-it.md](../plans/2026-10-22-the-wind-tunnel-in-fly-it.md).*

## What I asked for

To see the wind tunnel on the 3D drone in Fly it: the air resistance from every direction, as smooth animations. It doesn't have to be simulated live, only played back live.

## What it is

Until now the tunnel only made pictures. FluidX3D rendered flat frames from two fixed cameras, and the site's tunnel page played them as a flipbook. There was no flow the 3D drone could carry. So:

1. **The fork exports the flow, moving.** My FluidX3D setup (in `C:\dr\fluidx3d`, never this repo) writes 64 snapshots of the air's velocity over the last half of each run. They cover a box around the drone on 12 mm cells, from 0.6 m ahead of it to 1.6 m behind, with the speed on the plane through the drone at full resolution at each one. It also writes the flow averaged over the last 40%, which gives the drone's outline and the mean force.
2. **Seven cases instead of three.** The air comes from the front (the cruise, pitched the way it flies), from behind (pitched back), from the right (the old crosswind), from the left, from above (the way it meets the drone climbing) and from below (coming down), all at 10 m/s on the body alone, plus the hover with its actuator disks. It's Max, the combination with everything on. The wind cases run 0.64 s of air and the hover 0.4 s, so there's half a run to watch after the wake forms.
3. **This repo carries particles through it** (`pcs14.aero.motion`, GPL like the rest). The snapshots become a loop that eases from its end back into its start. 2,400 particles are released all through the loop: upstream and wide of the drone (most in front of it), some in its wake, and in the hover above it, around it and over each disk. Each is carried through the moving flow until it leaves the box or has lived a loop. Since the flow loops, every particle's path repeats exactly, with no seam. The plane becomes the loop's 64 frames of a slice through the drone.
4. **The site plays it on the drone.** In Fly it, a "Wind tunnel" group lists the seven. Picking one holds the drone still, tilted the way it flies into that air, with its props stopped (or at a hover's speed in the hover). Each particle is a short trail in turbo by the air's speed, fading in as it's released and out as it goes. The slice plays its frames, blended on the GPU, so the wake sheds and flaps, and a switch hides it. It's all slowed 20 times. The panel and the strip under the drone carry the color scale and FluidX3D's force along the wind.

## The rules it keeps

- **FluidX3D's output stays local.** The flow files land in `outputs/tunnel` and `site/public/data`, both gitignored, and the build check already warns about tunnel data in a build. They wait for the fork to go public, like the pictures.
- **Pictures, not measurements.** The force is FluidX3D's own number, said to be visual-grade wherever it shows: it runs 1.3 to 2 times high without a wall model. The drag tables still come from OpenFOAM.
- **No FluidX3D code here.** The export is a few lines in the fork's setup, marked as altered source and committed in that clone.

## Not in this

- **Following the drone's relative wind while a run plays.** That's the next step if I want it, once the seven are in.
- **Vortex surfaces in 3D.** The particles and the slice show the eddies; surfaces of them are for later.
- **Other combinations.** `pcs14 tunnel --setup` runs them; the site lists whatever has been run.
