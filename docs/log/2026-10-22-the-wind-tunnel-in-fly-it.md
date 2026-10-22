# The wind tunnel in Fly it

*2026-10-22, on the PC. The [spec](../specs/2026-10-22-the-wind-tunnel-in-fly-it.md) and the [plan](../plans/2026-10-22-the-wind-tunnel-in-fly-it.md).*

I wanted to see the wind tunnel on the 3D drone in Fly it: the air hitting it from every direction, moving. It doesn't have to be simulated in the browser, it just has to play back like it's happening.

## Why it wasn't there

FluidX3D only ever made pictures for me. It rendered flat frames from two fixed cameras, and the site's tunnel page played them as a flipbook. Nothing saved the flow itself, so there was nothing for the 3D drone to carry around with it. The first job was getting the flow out of my FluidX3D fork, which lives in its own folder and never in this repo, since its license doesn't mix with the GPL.

## The first try, and why I threw it out

The first version averaged the flow over the end of each run and traced about 260 streamlines through it from a rake in front of the drone, with bright streaks running down them. It worked, and it looked wrong the moment I saw it. Three things bugged me:

- It missed most of the air. A rake only catches what hits the drone head-on, not the air going round it or tumbling in its wake.
- The air appeared out of nowhere. Every line started dead at the rake, in mid-air.
- The wake was a still picture. Averaging over time smooths away exactly the part that moves: the eddies coming off the frame, the wake flapping.

## What it does now

The fork now writes 64 snapshots of the flow over the last half of each run. Each one covers a box around the drone on 12 mm cells, from 0.6 m in front of it to 1.6 m behind, with the speed on a plane through the drone at full resolution at each snapshot. My code turns those into a loop and carries particles through it.

- **2,400 particles, released all through the loop.** Most start in front of the drone, some wide of it, and 30% in its wake. In the hover they start above it, around it and just over each prop's disk. Each one rides the moving flow until it leaves the box or has lived a whole loop.
- **No seam.** The recorded stretch doesn't end the way it started, so over the loop's first fifth the flow eases from where the stretch ended into where it began. Because the flow loops, every particle's path loops too, and each loop plays exactly the same.
- **Nothing pops.** Each particle fades in when it's released and out before it goes. Air moving at the wind's own speed is drawn faint, so what stands out is the air the drone actually disturbs.
- **A slice that moves.** The plane's 64 frames go to the GPU as one 3D texture, which blends between frames for free. You watch the wake shed and flap instead of looking at a gradient. It fades out over its far end rather than stopping at a line.

Everything plays slowed down 20 times. The real wake goes by too fast to see.

## Making it read as flying

Three more things after another look. The slice used to stop dead at its edges, right where the wake was still strong. Now it runs on nearly to the end of the recorded box and fades out over its far end, with soft edges all round.

The drone hung still while the air blew past, which looked like a statue in a draft. Now it flies. In the horizontal cases the ground slides by under it at exactly the pace the free-stream particles move, so you see it going nose first, tail first or sideways into the air you're watching. Its props turn and it sways a little. The props are only for show, since the tunnel's body had none, and the panel says so. Climbing and coming down don't move the ground; the air alone shows that.

In the hover, the particles drawn in from above all started on one plane. The air up there is slow, so they sat in a flat disk while they faded in. Now they start spread through the air above the drone.

The list in Fly it always shows all seven, with any not run yet greyed out, and a quiet line under the intro says how to look around: a tiny mouse for drag to turn, scroll to zoom and right-drag to slide, or fingers on a touch screen.

## Seven ways the air meets it

The tunnel ran seven cases on Max, the combination with everything on: 10 m/s from the front, behind, each side, above and below, on the body alone, plus the hover with its props as actuator disks. Each wind case is 0.64 s of air, which takes about 8 minutes on the 3060.

FluidX3D's own number for the force along the wind, averaged over the last 40% of each run:

| The air from | Force along it |
|---|---|
| The front (nose first, pitched 3.3 degrees the way it cruises) | 2.0 N |
| Behind (tail first, pitched back) | 2.6 N |
| The right | 4.1 N |
| The left | 3.7 N |
| Above (the way it meets the air climbing) | 23.7 N |
| Below (coming down) | 31.7 N |

These are picture numbers, not measurements. FluidX3D runs 1.3 to 2 times high without a wall model, and the tunnel is small next to the drone seen from above, which pushes the vertical cases up more. The order still makes sense, though. The drone is slimmest nose first, and seen from above it's mostly flat plates, a pack and a frame, so climbing or dropping fast is where it fights the air hardest. OpenFOAM will give the real numbers.

## What broke along the way

- **A file name clash.** Windows doesn't care about case, so `airflow.ts` and `Airflow.tsx` were the same file to it.
- **The fork built for the wrong compiler.** Its project still asked for Visual Studio 2019's tools, so it needed the 2022 toolset passed in.
- **The animation "didn't work" a few times** when the browser pane was hidden. A hidden page pauses its animation frames, so the camera, the fades and the particles all froze.

## What's not done

- **Following the drone's own wind while a run plays.** The flow could switch to whichever way the air meets the drone as it flies. That's next if I want it.
- **The fork going public.** Until it does, the tunnel's pictures and flows stay on my machine. The build check warns when they're in a build.
- **OpenFOAM,** for numbers I'd trust.
