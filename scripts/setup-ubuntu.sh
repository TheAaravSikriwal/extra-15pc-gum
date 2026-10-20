#!/usr/bin/env bash
# The flight sim's tools, inside WSL2 Ubuntu 24.04 (or the PC's native Ubuntu), at pinned
# versions: PX4 v1.17.0 with its own toolchain and Gazebo Harmonic, the Python side (MAVSDK and
# pyulog), and our drag plugin. Safe to rerun. The second half, OpenFOAM, comes with the wind
# tunnel side track.
#
#   scripts/setup-ubuntu.sh
#
# Everything heavy lives in the Ubuntu home folder, not under /mnt/c, because WSL reads
# Windows files slowly: PX4 in ~/px4/PX4-Autopilot, the venv in ~/.venvs/extra-15pc-gum and the
# plugin's build in ~/build/pcs14_drag. Override them with PX4_DIR, VENV and PLUGIN_BUILD.

set -euo pipefail

PX4_TAG=v1.17.0
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
px4_dir="${PX4_DIR:-$HOME/px4/PX4-Autopilot}"
venv="${VENV:-$HOME/.venvs/extra-15pc-gum}"
plugin_build="${PLUGIN_BUILD:-$HOME/build/pcs14_drag}"

echo "==> PX4 $PX4_TAG, in $px4_dir"
if [ ! -d "$px4_dir/.git" ]; then
  mkdir -p "$(dirname "$px4_dir")"
  git clone --recursive --branch "$PX4_TAG" https://github.com/PX4/PX4-Autopilot.git "$px4_dir"
else
  git -C "$px4_dir" fetch --tags --quiet
  git -C "$px4_dir" checkout --quiet "$PX4_TAG"
  git -C "$px4_dir" submodule update --init --recursive --quiet
fi

echo "==> PX4's own setup: its toolchain, and Gazebo Harmonic from OSRF's repository (sudo)"
# --no-nuttx: the flight controller's ARM toolchain isn't needed for the simulator
bash "$px4_dir/Tools/setup/ubuntu.sh" --no-nuttx

echo "==> PX4 for the simulator (px4_sitl)"
make -C "$px4_dir" px4_sitl

echo "==> The Python side, in $venv"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --quiet --upgrade pip
"$venv/bin/python" -m pip install --quiet -e "$repo_root[flight]"

echo "==> Our drag plugin, against Gazebo Harmonic, in $plugin_build"
cmake -S "$repo_root/sim/plugins/pcs14_drag" -B "$plugin_build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$plugin_build" --parallel

echo
echo "Done. Versions:"
git -C "$px4_dir" describe --tags
gz sim --versions 2>/dev/null | head -1 || echo "gz sim: not on the PATH"
"$venv/bin/python" -c "import mavsdk, pyulog; print('mavsdk', mavsdk.__version__ if hasattr(mavsdk, '__version__') else 'installed'); print('pyulog', pyulog.__version__)"
echo "Then rerun: scripts/check-machine.sh pc"
