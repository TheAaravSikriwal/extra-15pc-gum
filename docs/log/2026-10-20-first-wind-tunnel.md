# 2026-10-20: The first look at the air

*PC, Windows. The start of the Aero side track, its visual half.*

The flight sim treats drag as one number: the drag area, pushing back on the drone as a single force. Useful, but you can't see it. So I jumped ahead on the Aero side track and put the drone in a virtual wind tunnel, to see the air itself.

## How

FluidX3D, a lattice Boltzmann fluid solver that runs on the GPU, on the PC's RTX 3060. The drone is the CAD's watertight body with every module on (Max) and the props left out, in a tunnel 1.4 m wide, 3.2 m long and 1.1 m tall, with the wind at the 10 m/s cruise. That's 60 million cells, each 4.3 mm across, at a Reynolds number of about 260,000. It runs at about 3,600 million cell updates a second, so half a second of wind takes four minutes.

FluidX3D lives in its own folder outside this repo, because its license isn't compatible with GPL-3.0. My changes to it (the drone's setup, the project's turbo colors in place of its rainbow, and a few build switches) are marked as altered source, as its license asks, and they go into a public fork before any of its pictures get posted.

## What it shows

The streamlines in the drone's middle plane bend around the body and leave a slow, churning wake behind it. That wake is the drag. The vortices it sheds stretch most of the way down the tunnel.

FluidX3D also reports the force on the body: about 1.4 N at 10 m/s, a drag area of about 230 cm². The sizing model uses 202 cm² for Mission. Same ballpark, but this number isn't one to lean on yet. FluidX3D's own documentation says its drag runs 1.3 to 2 times high without a wall model, and Max carries more than Mission. The drag numbers will come from OpenFOAM, checked on a sphere first, as the roadmap says. These are pictures.

## Next

A side view and post-sized stills, the props spinning (FluidX3D can move solid boundaries), and the 10 m/s crosswind the hover holds against. Then the real Aero track: OpenFOAM, a sphere, then the drone's drag tables.
