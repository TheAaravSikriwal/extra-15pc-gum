# Setting up the PC

The PC is the main machine. Since 2026-10-17 everything happens from its **Windows** side:
- the Linux tools (Gazebo, PX4, OpenFOAM, the Python code) run in **WSL2 Ubuntu 24.04**
- the Windows tools (KiCad, FreeCAD, Blender, ParaView) run natively

The native Ubuntu side of the dual boot stays as a fallback (see the bottom).

It takes about 20 minutes, plus one reboot.

## 1. Turn on WSL2

Open PowerShell as administrator and run:

```powershell
wsl --install -d Ubuntu-24.04
```

Reboot when it asks. Ubuntu then opens on its own and asks for a username and password. Those are just for Ubuntu.

## 2. Give WSL more memory (optional, for the wind tunnel)

WSL gets half the PC's RAM by default (16 GB). For big OpenFOAM runs, give it more by creating `%UserProfile%\.wslconfig` with:

```ini
[wsl2]
memory=24GB
```

Then run `wsl --shutdown` in PowerShell. It applies the next time Ubuntu starts.

## 3. Install the basics inside Ubuntu

In the Ubuntu terminal:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git git-lfs python3-venv mesa-utils pciutils
```

`mesa-utils` and `pciutils` are only there so the machine check can see the graphics properly.

## 4. Check the GPU

```bash
nvidia-smi
```

It should show the RTX 3060. WSL borrows the Windows NVIDIA driver, so **never install an NVIDIA driver inside Ubuntu**. If the card doesn't show up, update the driver on the Windows side.

## 5. The repo

On the PC, the repo lives on the Windows side at `C:\dr\extra-15pc-gum`. The short path matters, because Windows' path-length limit breaks deeper folders. From Ubuntu, it's the same folder at `/mnt/c/dr/extra-15pc-gum`.

- **Run git from Windows** (or from the Claude session), not from inside Ubuntu, so the two sides don't fight over file permissions.
- **Heavy stuff lives in the Ubuntu home folder,** not under `/mnt/c`, because WSL reads Windows files slowly. That covers PX4's source and builds, OpenFOAM runs, and the Linux Python venv. Results that belong in the repo get copied back.
- **Pushing from Windows:** if `git push` hangs on Git's credential manager, push through the GitHub CLI's login instead:

  ```bash
  git -c credential.helper= -c "credential.helper=!gh auth git-credential" push
  ```

  Running `gh auth setup-git` once in Git Bash makes that the default for GitHub.

## 6. Run the same checks the laptop ran

In Ubuntu:

```bash
cd /mnt/c/dr/extra-15pc-gum
scripts/check-machine.sh pc
VENV=~/.venvs/extra-15pc-gum scripts/setup-dev.sh
```

The machine check is read-only and writes `docs/machines/pc.md`. The dev setup makes the Python venv in the Ubuntu home folder, installs the dev tools, and runs the same lint and tests as CI. It asks for your Ubuntu password only if something's missing, and it should end with `12 passed` and `All good.`

## 7. Log it and push

From Windows:

```bash
git add docs/machines/pc.md
git commit -m "Log the PC's WSL2 setup"
git push
```

## 8. Later: the Windows tools

FreeCAD (with CalculiX), Blender and ParaView install on the Windows side. `scripts/setup-windows.ps1` will install them at pinned versions when a step needs them.

The electrical step's tools went on the PC on 2026-10-18:

| Tool | Version | How | Where |
|---|---|---|---|
| Graphviz (WireViz draws with it) | 16.1.0 | `winget install Graphviz.Graphviz` | `C:\Program Files\Graphviz` |
| ngspice | 47 | `ngspice-47_64.7z` from [ngspice.sourceforge.io](https://ngspice.sourceforge.io), unpacked | `%LOCALAPPDATA%\Programs\ngspice` |
| KiCad | 10.0.6 | `winget install KiCad.KiCad` | `%LOCALAPPDATA%\Programs\KiCad` (a per-user install) |

None of them needs to be on the PATH: `pcs14` looks in those places too. `pcs14 electrical --tools` says what it found, and an environment variable (`PCS14_DOT`, `PCS14_NGSPICE`, `PCS14_KICAD_CLI`) can point it anywhere else. On Ubuntu, `scripts/setup-dev.sh` installs Graphviz and ngspice with apt.

## Picking up where things left off

A Claude session on this folder reads `CLAUDE.md` automatically, which says to pull, then read `STATUS.md` and `docs/decisions.md` before doing anything.

## What's not installed yet

The simulation toolchain inside WSL (Gazebo, PX4, OpenFOAM) comes from `scripts/setup-ubuntu.sh`, which hasn't been written yet. It's on the list in `STATUS.md`.

## Fallback: the native Ubuntu side

If WSL's graphics struggle with Gazebo, or a wind tunnel run needs all 32 GB, boot into the Ubuntu side and do steps 3, 4 and 6 there, with three differences:
- If `nvidia-smi` fails, install Ubuntu's recommended driver with `sudo ubuntu-drivers install` and reboot.
- Set the same git name and email as Windows, then log in with `gh auth login` and `gh auth setup-git`.
- Clone the repo into the Linux home folder: `git clone https://github.com/TheAaravSikriwal/extra-15pc-gum.git ~/extra-15pc-gum`.

## Day to day

Pull when you sit down, push when you get up.
