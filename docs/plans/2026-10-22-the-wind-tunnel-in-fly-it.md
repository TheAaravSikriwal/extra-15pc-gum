# The wind tunnel in Fly it: the plan

*From the [spec](../specs/2026-10-22-the-wind-tunnel-in-fly-it.md), agreed 2026-10-22.*

| # | Task | Done when | Status |
|---|---|---|---|
| 1 | **The fork exports the flow:** the averaged velocity, each cell's share of solid and the mean force; and 64 snapshots in a box around the drone with the plane's speed at each | A short coarse run writes them, and they read back | Done |
| 2 | **Seven cases:** front, back, right, left, above, below and the hover, each turned in the tunnel by yaw and pitch | The case tests pass | Done |
| 3 | **The moving flow** (`pcs14.aero.motion`): read the snapshots, make the seamless loop, release and carry the particles, cut the slice's frames | The tests on made-up flows pass: a steady wind, a pulsing one across the seam, the bytes | Done |
| 4 | **The site's data:** each case's particles and slice under `tunnel/flow/`, listed in tunnel.json | A made-up case gets both through the schema | Done |
| 5 | **Fly it:** the route, the list, the drone held still, the particle trails, the playing slice and its switch, the scale and the force | The stage tests pass, and it plays in the browser | Done |
| 6 | **Run the seven** on the 3060, about 8 minutes each | Every case has its flow | Done: all seven, about 56 minutes |
| 7 | **The log, the decisions, the README,** checked in the browser | It's written, and it works | Done ([log](../log/2026-10-22-the-wind-tunnel-in-fly-it.md)) |
| 8 | **After my look:** the slice fades at its edges, the drone flies (the ground sliding by, props turning), all seven always listed, the hover's releases spread out, and a controls helper under the intro | Checked in the browser | Done |
