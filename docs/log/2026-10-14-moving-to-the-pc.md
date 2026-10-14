# 2026-10-14: Moving to the PC

*Laptop, last session before switching. Housekeeping day.*

Everything so far happened on my laptop, but the real work (simulation, CFD, rendering) needs my desktop, with its RTX 3060 and 32 GB of RAM. So today was about making the switch boring.

## Why it matters

My laptop and PC are different machines running different setups, and the only thing connecting them is this repo. If a check I ran on the laptop only lives in a chat window, the PC will never know about it. So everything got turned into either a script or a file.

## What got done

- **`scripts/check-machine.sh`** looks at a machine and writes down what it has: OS, CPU, RAM, GPU, git, Python, and whether the simulation tools are installed yet. It's read-only, and it leaves out anything personal, since the reports go in a public repo.
- **`scripts/setup-dev.sh`** (and a Windows version for the laptop) sets up Python and runs the exact same lint and tests that GitHub runs on every push. If it passes on my machine, it passes on GitHub.
- I tested both from a fresh clone inside the laptop's Ubuntu (WSL), which runs the same Ubuntu version as the PC. The scripts came through executable with the right line endings, the machine check works, and the setup script correctly spotted what was missing.
- **The laptop's results are logged** in `docs/machines/`, so the PC has something to compare against.
- **`docs/setup-pc.md`** is a step-by-step guide to get the PC from nothing to "all checks pass" in about 15 minutes.
- **`CLAUDE.md`** now says the PC is the main machine, and notes how I like to work, so a fresh AI session on the PC doesn't start from zero.

## Next

Set up the PC, then finally talk through the sizing model and start building it.
