# sizing/

Layer 1. Give the sizing model a parts list and it tells you whether the thing can lift itself, and for how long.

The code lives in the project's Python package, 14 pcs left, at `src/pcs14/sizing/`. The parts it reads are in `design/catalog/`, and its reports land in `docs/reports/sizing/`. It's being built task by task, following [the plan](../docs/plans/2026-10-17-sizing-model.md).

## Running it

```bash
pcs14 size      # evaluate the build in design/build.yaml: every setup, every check
pcs14 sweep     # try every build the catalog allows, and rank them
pcs14 report    # write the full report to docs/reports/sizing/
```

Every run saves a Rerun recording to `outputs/rerun/`, which opens in the Rerun viewer (`rerun outputs/rerun/<file>.rrd`). Add `--live` to open the viewer and watch the flights and the sweep come in as they run.

To try it on the made-up test parts, point it at them and let them in:

```bash
pcs14 size --catalog tests/fixtures/catalog --build tests/fixtures/build.yaml --allow-made-up
```

Anything made from made-up parts is stamped as made up, and the report command won't write it into `docs/reports/`.
