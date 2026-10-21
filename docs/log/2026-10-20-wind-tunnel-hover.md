# 2026-10-20: The hover's downwash, on the third try

*PC, Windows, FluidX3D on the RTX 3060. The wind tunnel's hover case, which the [last tunnel entry](2026-10-20-wind-tunnel-cases.md) left not working.*

The cruise and crosswind pictures came out fine. The hover didn't, and I'd guessed at three reasons: the slice for the speed picture in the wrong place, a color scale set for the wrong speed, and a crop that put the drone on the top edge.

## Two of the three guesses were right

The slice was fine. It already cut through the two front props.

The color scale was the problem. FluidX3D sets its speed colors once, at compile time, and I'd tuned that number for the 10 m/s wind cases. In the hover the fastest thing in the box is the prop tips at about 71 m/s, while the downwash is nearer 7. So everything came out a dim purple. I made the scale a setting each case passes in. The tunnel cases keep exactly what they had, and the hover gets its own.

The framing was the third. FluidX3D's side camera looks at the middle of the box, and the hover's box is tall so the downwash has room, so the drone sat on the top edge of every frame. It's lower in the box now, and the run is 0.3 s instead of 0.12, about 30 turns of the props.

## Then the real problem showed up

With the colors fixed, the picture was clear and wrong. The fastest air shot out sideways at prop height, and the streamlines showed air pulled in from above and below alike, curling back in four big vortices. No column of air going down. That's what a spinning paddle does, not a propeller.

It's resolution. FluidX3D gets about 78 million cells out of the 3060's memory, which at this box size is a cell every 3.4 mm. A 10x5 prop's blade is about 2 cm across, and at that pitch its leading edge sits only about 4 mm above its trailing edge. So the blade's pitch is one cell. Voxelized, the blades are flat plates spinning in a plane, and flat plates fling air outward and push none down. To resolve the pitch I'd want cells several times smaller, which is many times the memory.

## Actuator disks

So the props are now what CFD people call actuator disks. Each prop is a disk of cells, two cells thick and the prop's diameter across, and each cell pushes on the air with its share of the prop's thrust. The thrust is a quarter of the drone's weight: 5.8 N for Max. The blades themselves aren't there anymore.

That gives what momentum theory says a hovering rotor does: air drawn down from above, a column under each prop that narrows as it speeds up, and the columns merging into one turbulent plume under the drone. It's quicker too, under 5 minutes instead of 34, because the fastest thing in the box is now the wake, not the tips.

| Run | What the props were | What came out | Time on the GPU |
|---|---|---|---|
| First | spinning blades | dim purple, drone on the edge | 6 min |
| Second | spinning blades, colors and framing fixed | air flung sideways, no downwash | 34 min |
| Third | actuator disks, 5.8 N each | a downwash column under each prop, merging | 5 min |

What it loses: no blade tip vortices and no swirl, since a disk doesn't turn the air. The stills say the props are modeled as disks. Like everything FluidX3D makes here, it's a picture, not a measurement.

## Still waiting

The stills stay off the repo until my FluidX3D fork is public, as its license asks for any results I post. The fork's changes are committed locally.

## Next

OpenFOAM, for drag numbers I can lean on, starting with a sphere to check the setup against a known answer.
