# scripts/

Setup and helper scripts. The shell scripts work on WSL2 Ubuntu 24.04 (both machines) and on native Ubuntu 24.04 (the PC's fallback).

| Script | What it does |
|---|---|
| `check-machine.sh [name]` | Read-only. Reports what a machine has (OS, CPU, GPU, git, Python, sim tools). With a name, saves it to `docs/machines/<name>.md`. |
| `setup-dev.sh` | Sets up the Python venv (in `.venv`, or wherever `VENV` points; on the PC that's `~/.venvs/extra-15pc-gum` inside WSL) and runs the same lint and tests as CI. Safe to rerun. |
| `setup-dev.ps1` | The same, for the laptop's Windows side (the venv goes outside OneDrive). |
| `setup-ubuntu.sh` | Runs inside WSL2: PX4 v1.17.0 with its toolchain and Gazebo Harmonic, MAVSDK and pyulog, and our drag plugin, at pinned versions. Safe to rerun. OpenFOAM is its second half, still to come. |
| `setup-windows.ps1` | Coming later. Installs the Windows tools at pinned versions: KiCad (with ngspice), FreeCAD (with CalculiX), Blender, ParaView. |
