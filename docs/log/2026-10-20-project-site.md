# 2026-10-20: The project site, built in a day

*PC, Windows. The project site side track, all 13 tasks of [its plan](../plans/2026-10-20-project-site.md).*

Everything in this project ends up as a report, a JSON file and a folder of charts. That's fine for me and useless for anyone scrolling past. So the project gets its own site: the drone in 3D that you can click apart, a spec sheet, a page per step, and every simulation played back as if it were happening live. It stays on my machine until the project is done, then joins my portfolio.

## How it's put together

There are two halves. `pcs14 site` is the Python half. It reads the reports, the CAD's model and the flight logs, and it writes the small JSON files the site needs. The site is the other half: Vite, React and TypeScript, three.js for the 3D, and nothing on a server. The build is one static folder.

The rule I set myself was that the site never parses anything hard. It never reads a ULog or a STEP file. The Python side already reads those for the reports, and the graders' own log reader turns each flight into its playback file, so the site and the reports can't disagree about what happened.

The data's shapes are pydantic models on the Python side, exported as JSON Schema, and a test on the TypeScript side fails if its types drift from the schema. Every file carries a version number, and a page refuses a file from another version and says which command makes the right one.

## The pages

**The drone in 3D.** The CAD's model, all 86 pieces, turning slowly with its props spinning the way each one really turns. Click any piece for a card with its maker, mass and price, and a board's card links to its pins. Switch the modules off and the weight, hover time and verdict above follow along. Pull it apart with a slider, and see the wires as lines colored by how hard each one works in the case you pick (hover, cruise, burst, worst). The CAD writes an 11.9 MB GLB, and gltfpack thins it to 3.0 MB at half the triangles with every piece's name kept.

**The spec sheet.** Every module combination's weight, flight times and checks, with each number drawn as a bar against its own limit, so 2.4 kg and 22 minutes can sit on one chart without one of them being a sliver. Spearmint passes, magenta fails, and a hollow bar is marginal: it meets the limit, but not on the pessimistic numbers, which get a tick of their own.

**The wiring.** Every board's pin map (each used pin, what PX4 or the chip calls it, and where it goes), the twelve harness diagrams and the schematic, all generated from the one connection list, so they can't disagree.

**Every flight.** The pass and fail matrix for both firmwares, and a page per run where the CAD's drone flies its logged path in 3D, the height, speed and motor charts scroll with it, and the events (the motor failing, the chute firing) pop up when they happen. PX4's run and mine play together on the same clock, gray and spearmint. A run's file is the ground truth at 20 Hz, about 150 kB.

**A page per step.** Built from the README's own plan table, the reports and this log, matched by name. I didn't want to write each step's story twice, so the site reads what's already here.

**The wind tunnel.** Each case's flow played back on the clock in slow motion, half a second of air over about 25 seconds, with the stills and what each says. More on that below.

**What the sims can't prove.** The list from my decisions file (each with the first thing to measure once a drone exists) and each report's own, 22 things in all. It's one quiet line on the home page, never more than a click away.

**The home page** is quiet on purpose: the drone, a line about what this is, one line per step with its status, and that line about what the sims can't prove. The rest is found by going in. Each step's page also points at its topics in my learning file.

## What broke

**Opening it from a folder.** The plan promised the site would open straight from disk. It doesn't, out of the box: browsers won't let a page opened as `file://` fetch anything, even a file in its own folder. So `pcs14 site` writes every data file twice, as JSON and as a tiny script that hands the same data to the page, and the loader uses the script when it sees it's running from disk. The 3D model goes the same way, as base64.

**The size budget.** I set the first load at 600 kB and blew it on the first build: 735 kB, nearly all fonts, because the font packages pull in every alphabet they have. Latin only fixed that. Then three.js arrived and added about 800 kB, so the 3D pages load only when someone opens them. The first load is now 267 kB.

**Names that changed in transit.** Clicking a part in 3D found nothing. The GLB's node names had spaces ("prop front left"), and three.js's loader quietly swaps spaces for underscores. The site now looks parts up the way the loader names them.

**Up is a different direction.** The CAD and the flight logs are z-up; glTF and three.js are y-up. The flight pages convert each logged position and attitude in one function with a test. The 3D page got it wrong in a sneakier way: the GLB keeps every piece under one node that turns z-up into y-up, and my exploded view pushed pieces out along the world's axes inside that turned frame. So pulling the drone apart sent its top modules forward instead of up. It looked exploded enough that I didn't notice until a test built a model the way the real GLB is built.

**Too many chapters.** A failure detector that raises its flag over and over gave a flight page a wall of chapter marks. Now each event gets one chapter per run, at its first moment, and the graders' window marks ("hold start") stay in the event list but out of the chapters.

**A page that remembered.** Going from a run with no playback file to one with a file kept the first page's "no flown runs" message, because the page was reused and held on to its old problem. It starts clean now when its run changes.

**Phone and keyboard.** I checked every page at 375 px wide for anything that spills off the side, and nothing does. The 3D page had one real gap: you could only pick a part with a mouse. It has a part picker now, so it works from the keyboard, and everything you can tab to gets a spearmint outline.

## The wind tunnel's license

FluidX3D's license asks that anyone posting its results publishes the source they changed. I changed it (my wind tunnel setup lives in a fork), so the tunnel's pictures stay off the repo and off any public build until that fork is public. The tunnel page says so, and the site's build check prints a warning when the pictures are in a build. For the page I changed the fork once more, so it writes 40 frames along each run with each one's time, and `pcs14 site --tunnel` thins them to JPEGs the page plays in order on its clock.

## Numbers

| | |
|---|---|
| Site tests (Vitest) | 78 |
| First load | 267 kB, budget 600 |
| The 3D model | 11.9 MB from the CAD, 3.0 MB thinned |
| Pieces, all clickable | 86 |
| Wire routes | 28 |
| A flight's playback file | about 150 kB |

## What's next

The site is done as planned. What it shows will grow with the project: my firmware's runs as step 5 finishes, the OpenFOAM numbers when they exist, and the tunnel's pictures once the fork is public.
