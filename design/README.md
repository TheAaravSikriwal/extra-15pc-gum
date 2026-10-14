# design/

The drone on paper. Once the sizing model exists, this is the one place where the drone's actual spec lives, and everything else reads from it.

- `targets.yaml`: the numbers every setup has to hit. Already here.
- `catalog/`: candidate parts, with their real test data. Arrives with the sizing model.
- `build.yaml`: which parts I picked, where they sit, and what's in each module. Same.

Change a part here, rerun everything, and see what breaks.
