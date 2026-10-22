# design/

The drone on paper. This is the one place where the drone's spec lives, and everything else reads from it.

- `targets.yaml`: the numbers every setup has to hit.
- `catalog/`: every real part the sizing model and the build can choose from, with where each number came from.
- `build.yaml`: which parts I picked, and what's in each module.
- `cad.yaml`: the CAD's own inputs, the numbers that are mine and not a maker's (where things sit, the printed parts, the materials), each with why.
- `electrical.yaml`: the connection list: every board, every wire, what plugs into what. The harness diagrams, pin maps, schematic and every electrical check come from it.
- `package.yaml`: what the build package needs that isn't a catalog part: the ground side, supplies, tools and spares.
- `validation/`: published builds with measured flight times, for the sizing model's honesty check.

Change a part here, rerun everything, and see what breaks.
