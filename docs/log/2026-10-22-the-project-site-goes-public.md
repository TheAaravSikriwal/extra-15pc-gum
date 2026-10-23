# 2026-10-22: The project site goes public

*2026-10-22, on the PC. It's at [wearechintu.com/drone](https://wearechintu.com/drone).*

The project site has lived on my machine since 2026-10-20, built to go public only when the project was done. I'm not building the drone anytime soon, so for now this is the project: an idea, done in simulation, as completely as I can. There was nothing left to wait for. Once the wind tunnel's source was public, so FluidX3D's license was met, the site could go too.

## Where it went

My portfolio, [wearechintu.com](https://wearechintu.com), is one plain line per project, and pointing at a line opens that project's numbers and an introduction in the margins, each set in the project's own materials. Extra 15pc Gum is the third line now, after Chintu and Stepwise and before QUIPU and mindcontrol, and its margins are its own: tunnel black, chalk monospace, spearmint, and a little quad seen from above that turns slowly where its line meets the page. The numbers were counted from this repo: 62,942 lines of source, 1,132 tests, 198 recorded flights, 437 electrical checks, and 0 parts bought.

Clicking it opens [/drone](https://wearechintu.com/drone): the whole site, framed edge to edge under a header of its own. The site routes with its address's hash, so the frame passes it through both ways, and a link like [/drone#/flights](https://wearechintu.com/drone#/flights) opens straight on the flights.

## How it got there

The site was always a folder of static files, so it ships the way the portfolio's other projects do: copied into the portfolio's repo, which Vercel deploys. One command does the copy, `npm --prefix site run export-site`. The build is 199 MB, but 83 MB of that is a second copy of the data as scripts, which only exists so the site works when it's opened straight from a folder on disk. The web fetches the data itself, so the export leaves those behind: 1,310 files, 121 MB.

That's still big for a repo, and committed files stay in its history for good. The other choices were thinning the data first, or putting it somewhere else, like Cloudflare's storage, with the portfolio fetching it from there. I kept it simple: one repo, one deploy, nothing else to run. The data only changes when a step's runs do, and that's rare while this is an idea.

The page gets its own security policy, the way each of the portfolio's projects does. The 3D drone needs less than I expected: no WebAssembly, no background workers, no outside fonts or scripts. Just its own files, WebGL, and inline styles for its panels. I tried it all on my machine first: the line and its margins, the move into the page, the drone view, Fly it and the wind tunnel, a deep link, the header on a phone. Then a Vercel preview build, then the merge that deployed it.

## What's next

My own pass over the live site. On a slow connection the first look takes a few seconds while the 3D model and the flow come down, so that's the first thing I'll watch.
