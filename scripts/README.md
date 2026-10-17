# scripts/

Setup and helper scripts. The shell scripts work on WSL2 Ubuntu 24.04 (both machines) and on native Ubuntu 24.04 (the PC's fallback).

| Script | What it does |
|---|---|
| `check-machine.sh [name]` | Read-only. Reports what a machine has (OS, CPU, GPU, git, Python, sim tools). With a name, saves it to `docs/machines/<name>.md`. |
| `setup-dev.sh` | Sets up the Python venv (in `.venv`, or wherever `VENV` points; on the PC that's `~/.venvs/extra-15pc-gum` inside WSL) and runs the same lint and tests as CI. Safe to rerun. |
| `setup-dev.ps1` | The same, for the laptop's Windows side (the venv goes outside OneDrive). |
| `setup-ubuntu.sh` | Coming next. Runs inside WSL2: Gazebo, PX4 and the Python tools first, then OpenFOAM, at pinned versions. |
| `setup-windows.ps1` | Coming later. Installs the Windows tools at pinned versions: KiCad (with ngspice), FreeCAD (with CalculiX), Blender, ParaView. |
