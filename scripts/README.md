# scripts/

Setup and helper scripts. Everything here works on native Ubuntu 24.04 (the PC) and on WSL2 (the laptop).

| Script | What it does |
|---|---|
| `check-machine.sh [name]` | Read-only. Reports what a machine has (OS, CPU, GPU, git, Python, sim tools). With a name, saves it to `docs/machines/<name>.md`. |
| `setup-dev.sh` | Sets up the Python venv in `.venv` and runs the same lint and tests as CI. Safe to rerun. |
| `setup-dev.ps1` | The same, for the laptop's Windows side (the venv goes outside OneDrive). |
| `setup-ubuntu.sh` | Coming next. Installs Gazebo, PX4, OpenFOAM, ParaView and Blender at pinned versions. |
