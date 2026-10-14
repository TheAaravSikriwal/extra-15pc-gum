# Machine check: laptop (Windows side)

Recorded by hand from the checks run on 2026-10-13 and 2026-10-14. The WSL side has its own generated report in [laptop-wsl.md](laptop-wsl.md).

## System

| | |
|---|---|
| OS | Windows 11 Home (build 26200) |
| Machine | Lenovo 83DJ |
| CPU | Intel Core Ultra 7 155U (12 cores, 14 threads) |
| RAM | 16 GB (WSL gets about 7.6 GB of it) |
| GPU | Intel integrated graphics (driver 32.0.101.8132). No NVIDIA GPU. |
| Free disk | 155 GB on C: |
| WSL | WSL2 with Ubuntu 24.04.3 and WSLg (plus Docker Desktop's distro) |

## Tools

| | |
|---|---|
| git | 2.47.1 (Windows) |
| Git LFS | 3.6.0 |
| GitHub CLI | 2.97.0, logged in |
| Python | 3.14.3 |
| uv | not installed (not needed; plain venv + pip) |
| Project venv | `%USERPROFILE%\.venvs\extra-15pc-gum`, outside OneDrive on purpose |
| pip | 26.2.1 (in the venv) |

## Results

| Check | Result |
|---|---|
| `scripts\setup-dev.ps1` (lint + tests, same as CI) | passes, 8 tests |
| Fresh clone in WSL: file permissions and line endings | correct (scripts are executable, LF endings) |
| `scripts/check-machine.sh` in WSL | works, see [laptop-wsl.md](laptop-wsl.md) |
| `scripts/setup-dev.sh` in WSL | detects missing `python3-venv` and `git-lfs` and asks for sudo to install them (not installed, since the laptop's WSL isn't used for builds yet) |
| GitHub Actions on the same commits | passing |

## Quirks

- **The repo lives in OneDrive here.** Anything bulky (the venv, PX4 builds) stays out of it.
- **Pushing:** the `GH_TOKEN` environment variable holds a fine-grained token that doesn't have access to this repo. Until that's fixed in GitHub's token settings, push with `env -u GH_TOKEN git push`, which uses the GitHub CLI's normal login instead.
- **Limits:** integrated graphics means only light Gazebo scenes and coarse CFD test cases. No Isaac Sim, and no good local LLM.

## One-off checks (not tied to a machine)

| Check | Result | Date |
|---|---|---|
| build123d (code CAD) installs on our Pythons? | Yes: version 0.13.0 supports Python 3.11–3.14, with ready-made installs for Python 3.12 on Linux and 3.14 on Windows | 2026-10-13 |
| FluidX3D license OK for us? | Yes for personal and educational use, but its modified source has to be published, separately from this GPL repo (see [decisions.md](../decisions.md)) | 2026-10-13 |
