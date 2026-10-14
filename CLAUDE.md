# CLAUDE.md

Notes for Claude sessions working on this repo. If you're a human reading this: hi. This is how I keep my AI pair-programmer on the same page between my laptop and my PC.

Extra 15pc Gum is a long-range quadcopter with my own flight firmware, built simulation-first and in public. I work on two machines, and this repo is how the work moves between them.

## Every session

1. **Start:** `git pull`, then read `STATUS.md` (where we are) and `docs/decisions.md` (what's decided and why). Don't reopen a settled decision unless I bring it up.
2. **End, or at any real checkpoint:**
   - Update `STATUS.md`: date and machine, current phase, what's next, open questions.
   - Add to the log in `docs/log/YYYY-MM-DD-<topic>.md`: what got done, what got decided, what broke, what's next. These become my posts, so write them so someone outside the project can follow along.
   - Put any new decision in `docs/decisions.md`. If the plan changed, update `docs/roadmap.md` too.
   - Commit and push. I've asked for the repo to stay current this way.

## Voice

Everything here is written as me (Aarav), in the first person, and it's going online. It should sound like a person, not a press release.

- Write like you're explaining the project to a friend who builds stuff. Plain words, short sentences. A joke is fine if it actually lands.
- No hype or filler. Skip words like robust, seamless, leverage, cutting-edge, delve and "it's worth noting".
- Go easy on bold, headers and bullet lists. Paragraphs are fine. Tables are great for numbers.
- No em dashes. No emoji.
- Be honest about what's unknown or didn't work. Failures are content.
- American spelling.
- Commit messages are short and plain: what changed and why.

## Public repo rules

- No secrets: API keys, tokens, `.env` files.
- No home or launch GPS coordinates, ever. Scrub flight logs, maps and screenshots first. Raw flight logs (`*.ulg`, `*.bin`) are gitignored.
- No videos in the repo. They go wherever I'm posting.
- CAD and mesh files go through Git LFS (see `.gitattributes`).
- Respect the licenses of any code we reuse. This repo is GPL-3.0.
- FluidX3D code never goes in this repo. Its license isn't GPL compatible, and it requires publishing any modified source whose results we post. My FluidX3D setup lives in its own public fork, marked as modified.

## Visuals

I post this whole project on LinkedIn (mostly) and Instagram (sometimes), so anything visual has to look good to strangers scrolling by.

- Use the project's visual style (colors, background, type) from `docs/decisions.md` for every render, chart, CFD image and clip.
- Export in the platform sizes: 4:5 (1080×1350), 1:1 (1080×1080), 9:16 (1080×1920), 16:9 (1920×1080). PDF carousels for LinkedIn.
- Curated, compressed stills go in `media/`. Raw renders and videos don't go in the repo.

## Machines

- **Laptop:** Windows 11 + WSL2 Ubuntu 24.04, Intel integrated graphics, 16 GB. The repo lives in OneDrive on the Windows side, so anything bulky stays out of it:
  - The Python venv is at `%USERPROFILE%\.venvs\extra-15pc-gum`.
  - PX4 builds go in the WSL home folder, not under `/mnt/c`.
  - `git push` needs `env -u GH_TOKEN git push` until my fine-grained token gets access to this repo.
- **PC:** dual boot. The sim runs on **native Ubuntu 24.04**, with an RTX 3060 and 32 GB. The repo is cloned into a Linux folder from GitHub, not OneDrive.
- Both run Ubuntu 24.04 for the toolchain, so setup scripts have to work on native Linux and on WSL2.

## Safety rules (these don't bend)

- The LLM runs on the laptop and **never commands the motors**. It writes structured plans; a deterministic checker validates them (geofence, 400 ft ceiling, battery reserve, speed limits); I approve them; the flight controller flies them.
- The flight controller never depends on the companion computer or the laptop. If the companion computer goes quiet, that's a failsafe.
- My RC transmitter and kill switch override everything.
- The parachute can also be fired by an independent monitor (a Teensy 4.1 with its own IMU), and the motors cut before it deploys.
