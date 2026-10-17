# design/validation/

The honesty check. Each file in `cases/` is a published build with a measured flight time, and `pcs14 validate` flies it through the model to see how far off the model is. The results land in `docs/reports/sizing/validation.md`.

- `cases/`: one YAML file per published build: its motor, prop and pack, its measured takeoff weight, estimates for what wasn't published (drag area, electronics power, with a note saying how), and the measured flight time with the point it stopped at (`until`: a share of the charge used, mAh used, or a voltage per cell under load or at rest). Each one says who measured it: an independent measurement, the builder's own, or a manufacturer's claim.
- `catalog/`: the parts those builds used, in the same format as `design/catalog/`. They live here so they never end up in the real sweep.

Cells in the real catalog can also carry published discharge tests (`discharge_tests` in the cell file), and `pcs14 validate` checks the battery model against those too.
