# The build package: the plan (step 8)

*Written 2026-10-21, from the [spec](../specs/2026-10-21-build-package.md). Test-first, task by task.*

## Where things go

| What | Where |
|---|---|
| The package's code | `src/pcs14/package/`, tests in `tests/test_package_*.py` |
| The command | `pcs14 package`, writing `docs/build/` |
| The parts' links, prices and fallbacks | the catalog, `design/catalog/**/*.yaml` |
| The unproven measurements | each report's own list |

## The tasks

| # | Task | What the tests check |
|---|---|---|
| 1 | **The catalog's fallback field,** and every bought part's link, price and fallback researched and written in | The schema takes a fallback and refuses one without a maker; every bought part in the build has a link, or a note saying why not |
| 2 | **The parts list:** bought parts by module with counts, wire by type and gauge, connectors and small parts, hardware rolled up, printed parts; totals per combination; Markdown and CSV | On a made-up build: the counts, the wire lengths with their slack, the totals, and a part without a price counted as unpriced, not as free |
| 3 | **The assembly guide:** the build order, each step's parts and hardware, a render of the drone built up to it | Every part in the build lands in exactly one step; every hardware line lands with the part it holds |
| 4 | **The wiring guide:** harness by harness, every wire's ends, gauge, type and cut length, and the meter checks | Every wire in the connection list appears once, under its harness |
| 5 | **The firmware guide:** PX4 first, then mine, then the safety monitor, with what isn't built yet | It's written from the firmware's own targets, and names what's missing |
| 6 | **Test plans:** the bench checks and the first flights, with pass criteria | Every safety rule has a test; every unproven item's measurement is in the plan |
| 7 | **The legal checklist** | Every rule links its source and names its setting in the limits profile |
| 8 | **The unproven list with measurements:** (what, measurement) pairs in every report, and the site's page showing both | Each report's items carry a measurement; the site reads them |
| 9 | **`pcs14 package`** writing `docs/build/`, the README walking it in order, and the site's build page | It's written, and the site shows the parts and totals |

**Done when:** someone could build it from the docs alone.

## Where it stands

| Date | Tasks | Notes |
|---|---|---|
| 2026-10-21 | all 9 done | The catalog's fallback field and the research (36 parts, two wire tables and the gear in design/package.yaml, each page opened before it went in, except DigiKey's, whose prices came from its search listings), the parts list (the motors' own leads no longer bought twice), the 16-step assembly guide with its renders, the wiring guide (all 128 wires), the firmware guide (PX4 first; what isn't built named), the test plans (every safety rule tested; every unproven measurement placed), the legal checklist (its links not opened on the day, and it says so), the unproven pairs in every report, and `pcs14 package` with the site's Build it page |
| 2026-10-21 | none yet | Plan written |
