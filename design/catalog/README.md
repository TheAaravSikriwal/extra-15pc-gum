# design/catalog/

The real parts the sizing model chooses from. One YAML file per part, in a folder per type:

| Folder | What goes in it |
|---|---|
| `motors/` | Motors, each with thrust tables for the props and voltages they were tested with |
| `props/` | Props: diameter, pitch, blades, mass |
| `cells/` | Li-ion cells: capacity, ratings, internal resistance and a resting-voltage curve. Packs get built from these. |
| `escs/` | 4-in-1 ESCs |
| `frames/` | Frames, with a drag area |
| `components/` | Everything else with a mass: flight controller, receiver, module parts, wiring |
| `wires/` | Hookup wire, as a table of gauges: resistance, outer diameter and grams per meter |

The rules, which `pcs14` checks every time it loads the catalog:

- **Every number has a source.** A part's `source` covers its specs. Thrust tables, voltage curves, resistances, power draws and drag areas each carry their own. A manufacturer or independent-test source needs a link, and an estimate needs a note saying how it was worked out.
- **Numbers carry their unit in the field name:** `mass_g`, `diameter_in`, `capacity_mah`, `thrust_g`. A number without its unit, or any field the format doesn't know, fails with a message saying what went wrong.
- **Thrust has to rise with throttle,** and a voltage curve has to run from empty to full.
- **Electrical blocks (step 3).** A part's `electrical` block lists its connectors and pins (named `CONNECTOR.PIN`, like `CAN.5V`), the current it draws through which pin, the supplies it provides, and its contact rating if it's a connector family or its ratings if it's a fuse family. Every connector names its family, which has to be a part here with a rating (or `pads`). Estimated numbers get named, like `draws[ESC.VBAT].worst_a`, with a note, so the checks resting on them show up in the report. The format is in `src/pcs14/catalog/electrical.py`.
- **No made-up parts.** The made-up parts in `tests/fixtures/catalog/` are for tests only, and the loader refuses them here.

The format is defined in `src/pcs14/catalog/schema.py`, and the decisions behind it are in the [Phase 1 spec](../../docs/specs/2026-10-13-phase-1-simulation.md#settled-in-the-sizing-model-talk). This folder gets filled with real parts in step 1d.
