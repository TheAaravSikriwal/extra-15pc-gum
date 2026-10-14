# CLAUDE.md

Extra 15pc Gum: a long-range quadcopter with custom flight firmware, built simulation-first and in public. The owner works on two machines (a laptop and a PC), and this repo is how work moves between them.

## Every session

1. **Start:** run `git pull`, then read `STATUS.md` (where we are) and `docs/decisions.md` (what's decided and why). Don't re-open a settled decision unless the owner asks.
2. **End, or at any meaningful checkpoint:**
   - Update `STATUS.md`: last updated (date and machine), current phase, next up, open questions.
   - Add or extend a log entry in `docs/log/YYYY-MM-DD-<topic>.md`: what was done, what was decided, what broke, what's next. These entries become the online posts, so write them so someone outside the project can follow.
   - Record any new decision in `docs/decisions.md`.
   - Commit and push. The owner has asked for the repo to be kept up to date this way.

## Public repo rules

- Never commit secrets: API keys, tokens, `.env` files.
- Never commit home or launch GPS coordinates. Scrub flight logs, maps and screenshots first. Raw flight logs (`*.ulg`, `*.bin`) are gitignored.
- No videos in the repo; they go to the posting platform.
- CAD and mesh files go through Git LFS (see `.gitattributes`).
- Respect the licences of reused code. This repo is GPL-3.0.

## Machines

- **Laptop:** Windows 11 + WSL2 Ubuntu 24.04, Intel integrated graphics, 16 GB. The repo lives in OneDrive on the Windows side. Heavy builds (PX4) go in the WSL home folder, not under `/mnt/c`.
- **PC:** dual boot. Simulation runs on **native Ubuntu 24.04**, with an RTX 3060 and 32 GB. Clone the repo from GitHub into a Linux folder, not OneDrive.
- Both machines use Ubuntu 24.04 for the toolchain, so setup scripts must work on both native Linux and WSL2.

## Non-negotiable safety architecture

- The LLM runs on the laptop and **never commands the motors**. It outputs structured plans; a deterministic checker validates them (geofence, ≤400 ft, battery reserve, speed limits); the pilot approves them; the flight controller executes them.
- The flight controller never depends on the companion computer or the laptop. If the companion computer stops responding, that triggers a failsafe.
- The RC transmitter and kill switch always override everything.
- The parachute is also fired by an independent monitor (a Teensy 4.1 with its own IMU), and the motors are cut before it deploys.
