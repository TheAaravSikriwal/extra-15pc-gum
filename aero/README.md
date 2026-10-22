# aero/

Layer 3, the virtual wind tunnel. The code is in `src/pcs14/aero/`, run by `pcs14 tunnel`. This folder is for the OpenFOAM cases, once there are some.

- **The pictures: FluidX3D,** on the PC's RTX 3060, since 2026-10-20. The air from six ways at 10 m/s and the hover's downwash, as stills and as the flow moving on the 3D drone in the site's Fly it. FluidX3D lives in my own fork, outside this repo, because its license doesn't mix with this repo's GPL, and its pictures stay on my machine until that fork is public. They're pictures, not measurements: without a wall model it runs high on force.
- **The numbers: OpenFOAM, next.** The props modeled as disks pushing air. These runs will measure drag at speed and tilt, what the prop wash pushing down on the frame costs, ground effect, and crosswind, and the numbers feed back into the sizing model and Gazebo.
- **Visuals of those: ParaView**, for streamlines and pressure maps.
