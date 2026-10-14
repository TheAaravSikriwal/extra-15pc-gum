# cad/

Layer 2. The drone, written as Python with [build123d](https://github.com/gumyr/build123d). It reads `design/build.yaml`, so when a part changes, the model rebuilds itself.

Out of it come:
- the real center of gravity and inertia
- meshes for Gazebo and CFD (through Git LFS)
- STEP files that open in any CAD tool
- renders

Nothing here yet. The baseline X comes after the sizing model.
