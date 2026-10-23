# 2026-10-22: The wind tunnel's source goes public

*2026-10-22, on the PC. The fork is at [github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum](https://github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum).*

Every wind tunnel picture in this project comes out of FluidX3D, Dr. Moritz Lehmann's GPU fluid solver, and not the stock version: I changed it to read my cases, run the hover with actuator disks, color in turbo and write out the flow moving so the 3D drone can play it. FluidX3D's license is generous for personal and research use, with one catch that matters here. If you publish results from an altered version, you publish the altered source too. So until today, none of the tunnel's pictures could leave my machine, and the site's tunnel page said "local preview".

I'm not planning to build the drone anytime soon. This is an idea, done in simulation, so there's no reason for the pictures to wait. The fork went public first.

## What the license asks

It's short, and I read the whole thing before publishing anything. What it comes down to for me:

| It asks | How it's met |
|---|---|
| Don't misrepresent where it came from, and mark altered source plainly | The fork is a GitHub fork, so "forked from ProjectPhysX/FluidX3D" shows on the page. Its README opens by saying it's an altered version and not the original, whose it is, and what I changed file by file. Every change in the code is marked `ALTERED` |
| Publish the altered source with the results | That's the fork. Its default branch is the original's last commit plus my seven |
| No commercial use | This is a personal research project. Nothing's sold, and the pictures don't go into paid work |
| No military use | None |
| Don't train AI models on the source | I don't, and the fork repeats the rule |
| Keep the license notice | `LICENSE.md` is untouched |
| Cite the papers if a scientific publication comes out of it | Noted in the fork's README, for if that ever happens |

One more thing turned up reading my own changes. The turbo colormap I swapped in is a polynomial fit that Google published under Apache 2.0, and my comment credited it only loosely. The fork now has a `THIRD_PARTY_NOTICES.md` with the proper copyright line, the license, and the two people who made it.

## Checking for secrets first

Publishing is hard to take back, so before anything went up I went through three things: this repo's whole history, the fork's commits, and the built site.

No keys, tokens or passwords anywhere. The one thing a scan flagged was a public download link for a flight controller's 3D model, where "token" is the file host's share code for a public file. No home or launch coordinates: the only coordinates in the project are PX4's own default world origin, near Zurich, which every PX4 sim starts from. The fork's code reads everything relative to its own folder, so no paths from my machines are in it either.

The one real find was in the fork's history. Its first commit had my university email as the author, while every public commit of mine uses my personal one. Since those commits had never been pushed anywhere, I rewrote that one author before the first push, keeping the dates and the code exactly as they were, and checked that nothing else still carried it.

## The site's own licenses

While I was at it I checked what the site owes the code it's built on. Its scripts bundle 98 open source packages: three.js, React, pieces of d3, and everything those pull in, plus the three fonts. All permissive: MIT, ISC, BSD, Apache 2.0, and the Open Font License for the fonts. Nothing copyleft and nothing non-commercial. But most of those licenses ask for their notice to travel with every copy, and a minified bundle drops them. So the site's build now writes a `licenses.txt` beside the page with each package's license in full, and the build fails without it. The overview ends with a short credits section, and the tunnel page and Fly it now credit FluidX3D, with links to the original and to my fork.

## What's next

The tunnel's pictures can go out now, credited. The site itself goes public when I say so: everything it needs for that is in place.
