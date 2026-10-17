# 2026-10-17: Eight questions before any code

*PC, Windows side. Still no code, on purpose.*

The sizing model is the first real code in this project. Give it a parts list and it says whether the drone can lift itself, and for how long. Before writing a line of it, I wanted every design question answered, so today was eight of them, one at a time.

| Question | What I picked | Why |
|---|---|---|
| How do we work out the power to hover and cruise? | The real parts' thrust tables for hover, and a forward-flight model fitted to those tables for cruise | It's built on real data instead of guessed efficiencies. The speed that uses the least power falls out of it for free. |
| How do we model the battery? | Each cell's voltage curve plus its internal resistance, stepped through the whole flight | Voltage sag is what shrinks the thrust near empty, and a fixed voltage can't show it |
| How is the parts catalog stored? | One YAML file per real part, with every number tied to a source | Readable, easy to review, and measured data can sit next to the manufacturer's |
| Which parts go in first? | Only parts with public test data: 9" and 10" setups, plus one 8" to prove it loses | Popular parts often don't publish the numbers the model needs |
| What does the report look like? | A Markdown report for the repo, Rerun replays of every test, and a project website | I want to see every test happen, not just read a verdict |
| Where does the website live? | On my machine until the project's done, then on my portfolio site | It's a reveal for the end |
| How is the code organized? | One Python package called 14 pcs left (`pcs14` in the code) | The gum pack is down a piece. Python names can't start with a number, so the code spells it `pcs14`. |
| Which setup sizes the drone? | Mission (vision plus parachute), with 200 g of room to grow | Sizing for the claws would make every flight pay for something that might never exist |

## The bit I'm most excited about

Every test is going to be visible. Each simulated flight streams into a viewer called Rerun as it runs: the battery voltage sagging, the charge draining, the thrust headroom shrinking, right down to the 20% reserve line. I can scrub through any flight afterward too. That applies to every step from here on, not just this one: collisions lit up in the CAD, current through every wire, a clip for every flight test.

All of it rolls up into one website: the drone in 3D (coming apart into an exploded view, with modules switching on and off and the numbers updating as they do), a live spec sheet, and a page per step that explains what it does. It stays on my machine until the project's done.

## Also

The results get three verdicts, not two. Manufacturer data runs 15–20% optimistic, so a setup either passes even with pessimistic numbers, passes only on optimistic ones ("marginal"), or fails. Marginal is the honest answer a lot of the time.

## Next

Writing the implementation plan for the sizing model, then building it test-first.
