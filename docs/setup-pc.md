# Setting up the PC

The PC is the main machine from 2026-10-14 on. Everything happens on its **Ubuntu 24.04** side. This gets it from nothing to the exact state the laptop was in: repo cloned, same checks passing, ready to build.

It takes about 15 minutes. Every command runs in a terminal on the Ubuntu side.

## 1. Update and install the basics

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git git-lfs gh python3-venv mesa-utils pciutils
```

`mesa-utils` and `pciutils` are only there so the machine check can see the graphics card properly.

## 2. Make sure the RTX 3060 is working

```bash
nvidia-smi
```

If that shows the RTX 3060, skip ahead. If it says command not found, or can't find a GPU, install Ubuntu's recommended NVIDIA driver and reboot:

```bash
sudo ubuntu-drivers install
sudo reboot
```

Gazebo doesn't strictly need it, but FluidX3D, Blender's GPU rendering and smooth Gazebo graphics all do.

## 3. Git identity and GitHub login

Use the same name as on the laptop, so the commit history matches:

```bash
git config --global user.name "Aarav Sikriwal"
git config --global user.email "the same email you use on the laptop"
```

Then log in to GitHub and let git use that login:

```bash
gh auth login
gh auth setup-git
```

In `gh auth login`, pick GitHub.com, HTTPS, and log in with the browser. This avoids the fine-grained token problem the laptop has.

## 4. Clone the repo

Clone it into a normal Linux folder. Don't use OneDrive. If the PC's Windows side shows a synced OneDrive copy of the repo, ignore it; the Linux clone is the real one.

```bash
git clone https://github.com/TheAaravSikriwal/extra-15pc-gum.git ~/extra-15pc-gum
cd ~/extra-15pc-gum
git lfs install
```

## 5. Run the same checks the laptop ran

**The machine check** is read-only. It records what the PC has in `docs/machines/pc.md`:

```bash
scripts/check-machine.sh pc
```

**The dev setup** creates the Python venv in `.venv`, installs the dev tools, and runs the same lint and tests that CI runs. It asks for your sudo password only if something's missing.

```bash
scripts/setup-dev.sh
```

It should end with `8 passed` and `All good.` That's the same result as the laptop, and the same as GitHub Actions.

## 6. Log it and push

```bash
git add docs/machines/pc.md
git commit -m "Log the PC's setup"
git push
```

## 7. Pick up where the laptop left off

Install the Claude Code CLI following Anthropic's Claude Code docs. Then start it inside the repo:

```bash
cd ~/extra-15pc-gum
claude
```

It reads `CLAUDE.md` automatically, which tells it to pull, then read `STATUS.md` and `docs/decisions.md` before doing anything. A good first message: *"Read STATUS.md. We're on the PC now. Let's start the sizing model discussion."*

## What's not installed yet

The simulation toolchain (Gazebo, PX4, OpenFOAM, ParaView, Blender) comes from `scripts/setup-ubuntu.sh`, which hasn't been written yet. It's on the list in `STATUS.md`.

## Day to day

Pull when you sit down, push when you get up:

```bash
git pull
git push
```
