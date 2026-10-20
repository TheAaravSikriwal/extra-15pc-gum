# CLAUDE.md

Notes for Claude sessions working on this repo. If you're a human reading this: hi. This is how I keep my AI pair-programmer on the same page between my laptop and my PC.

Extra 15pc Gum is a long-range quadcopter with my own flight firmware. Since 2026-10-17 it's a research project: every real part modeled, connected and simulated, down to the wiring, complete enough that I could build it one day, and all of it in public. Nothing gets bought by default. I work on two machines, and this repo is how the work moves between them.

## Every session

1. **Start:** `git pull`, then read `STATUS.md` (where we are) and `docs/decisions.md` (what's decided and why). Don't reopen a settled decision unless I bring it up.
2. **End, or at any real checkpoint:**
   - Update `STATUS.md`: date and machine, current phase, what's next, open questions.
   - Add to the log in `docs/log/YYYY-MM-DD-<topic>.md`: what got done, what got decided, what broke, what's next. These become my posts, so write them so someone outside the project can follow along.
   - Put any new decision in `docs/decisions.md`. If the plan changed, update `docs/roadmap.md` too.
   - Keep the plan in `README.md` live. When a step or phase finishes, set its status, write its outcome in a line (with a link to the log entry or the result), and mark the next one "Up next". If the plan itself changed, change the tables to match.
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

## Learning vs. building

I'm learning a lot of this as I go: CFD, control, sensor fusion, embedded. I study offline and build online, and the two stay separate.

- Tutorials are mine to do on my own. They go in `docs/learning.md`, not in the build plan or the roadmap.
- When a new concept comes up while building, add it to `docs/learning.md`: which topic, why it matters here, and a couple of good resources (videos, articles, books or papers). Only list resources you're confident exist. Never make up a citation.
- When explaining something new during a session, keep it plain and short, and point at the learning file for the deep version.

## Public repo rules

- No secrets: API keys, tokens, `.env` files.
- No home or launch GPS coordinates, ever. Scrub flight logs, maps and screenshots first. Raw flight logs (`*.ulg`, `*.bin`) are gitignored.
- No videos in the repo. They go wherever I'm posting.
- Generated meshes and STEP files don't get committed. They're build outputs of the CAD code. Curated ones (the baseline, a v2 winner) go through Git LFS (see `.gitattributes`), and hero STEP files go on a GitHub Release.
- Respect the licenses of any code we reuse. This repo is GPL-3.0.
- FluidX3D code never goes in this repo. Its license isn't GPL compatible, and it requires publishing any modified source whose results we post. My FluidX3D setup lives in its own public fork, marked as modified.

## Visuals

I post this whole project on LinkedIn (mostly) and Instagram (sometimes), so anything visual has to look good to strangers scrolling by.

- Use the project's visual style from `docs/style.md` (scripts read `media/style.yaml`) for every render, chart, CFD image and clip. Black background, spearmint accent, turbo for CFD fields.
- Export in the platform sizes: 4:5 (1080×1350), 1:1 (1080×1080), 9:16 (1080×1920), 16:9 (1920×1080). PDF carousels for LinkedIn.
- Curated, compressed stills go in `media/`. Raw renders and videos don't go in the repo.

## Machines

- **PC (the main machine):** Windows 11 with **WSL2 Ubuntu 24.04** for the Linux tools (decided 2026-10-17). It has an RTX 3060, a Ryzen 7 9800X3D and 32 GB. It's dual boot, and the native Ubuntu side is only a fallback.
  - The repo is at `C:\dr\extra-15pc-gum` (a short path, because Windows' path-length limit breaks deeper folders). From WSL it's `/mnt/c/dr/extra-15pc-gum`.
  - Run git from Windows, not from inside WSL. If `git push` hangs on Git's credential manager, use `git -c credential.helper= -c "credential.helper=!gh auth git-credential" push`.
  - Heavy work (PX4 builds, OpenFOAM runs, the Linux venv at `~/.venvs/extra-15pc-gum`) lives in the WSL home folder, not under `/mnt/c`.
  - Linux commands can be run from Windows with `wsl -d Ubuntu-24.04 -- bash -lc "..."`.
  - First-time setup steps are in `docs/setup-pc.md`.
- **Laptop (secondary):** Windows 11 + WSL2 Ubuntu 24.04, Intel integrated graphics, 16 GB. The repo lives in OneDrive on the Windows side, so anything bulky stays out of it:
  - The venv is at `%USERPROFILE%\.venvs\extra-15pc-gum`, made by `scripts\setup-dev.ps1`.
  - PX4 builds go in the WSL home folder, not under `/mnt/c`.
  - `git push` needs `env -u GH_TOKEN git push` until my fine-grained token gets access to this repo.
- Both machines run the Linux tools in WSL2 Ubuntu 24.04, and the Windows tools (KiCad, FreeCAD, Blender, ParaView) natively. Scripts still have to work on native Linux too, for the PC's fallback.
- **Checking a machine:** `scripts/check-machine.sh <name>` is read-only and writes `docs/machines/<name>.md`. Rerun it and commit the result whenever a machine's tools change.
- **The checks that have to pass on every machine:** `scripts/setup-dev.sh` (or `setup-dev.ps1` on Windows), which runs the same lint and tests as CI.

## Working with me

Notes on how I like to work, so a fresh session on either machine picks up the same way.

- Make the routine choices yourself, the best-suited option each time, and write down what you picked and why (in the spec, the log and decisions). Only ask me about drastic changes: reopening a settled decision, a big change in weight, cost or scope, anything touching the safety rules, or a change of direction (2026-10-19).
- When you do ask, give me options with a clear recommendation and the reason for it. Put the recommended option first.
- Show me the full picture (the whole plan, the pros and cons) before asking me to lock something in.
- Write plans and reviews out in the chat. Don't send me Markdown files to open; they open in VS Code.
- One question at a time. I often answer in free text and add new ideas halfway through. Fold them in rather than restarting.
- Log and push decisions as we go. This repo is my memory between machines, and nothing from a chat carries over unless it's written here.
- I'm posting this publicly, so think about how it'll look and read, not just whether it works.
- The process: talk it through, write a spec, write an implementation plan, then build test-first. Nothing gets built before its design is agreed.

## Government rules are settings, not caps

When planning, take the rules into account (the FAA's altitude ceiling, Remote ID, airspace, FCC radio power) and tell me what they mean for what we're doing. Don't build them in as hard limits, though. Design for what the hardware can physically do, and put the legal numbers in a limits profile I can switch on. I'll tune it down when I want to. The details are in `docs/decisions.md`, under "Government rules are settings, not caps".

## Safety rules (these don't bend)

These are engineering safety, not government rules, so they stay the same whichever limits profile is loaded.

- The LLM runs on the laptop and **never commands the motors**. It writes structured plans; a deterministic checker validates them against the active limits profile (geofence, altitude ceiling, battery reserve, speed limits); I approve them; the flight controller flies them.
- The flight controller never depends on the companion computer or the laptop. If the companion computer goes quiet, that's a failsafe.
- My RC transmitter and kill switch override everything. The kill switch reaches the motors through two separate boards: the flight controller, and the safety monitor.
- The safety monitor (a Teensy 4.1 with its own IMU) lives in Base, not in a module. It cuts the motors by blocking the ESC signal lines, never by switching the main power, and if it loses power the drone keeps flying. Its automatic triggers stay in shadow mode (logging only) until they've shown zero false triggers.
- The parachute can be fired by the flight controller or the safety monitor, and the motors cut before it deploys.
- A hung CPU means the motors stop, not the motors stuck at the last throttle: a hardware watchdog, and fresh DShot frames every loop.
