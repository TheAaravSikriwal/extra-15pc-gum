#!/usr/bin/env bash
# Builds my firmware on Linux (WSL2 Ubuntu on the PC, or native Ubuntu): the core's host tests
# with the sanitizers, and the sim layer (pcs14_sitl) as a release build, both in the home
# folder rather than under /mnt/c, which WSL reads slowly. Runs the core's tests at the end.
#   scripts/build-firmware.sh            # both
#   JOBS=1 scripts/build-firmware.sh     # gently, while the flight sim is flying
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
jobs="${JOBS:-$(nproc)}"
venv="${PCS14_VENV:-$HOME/.venvs/extra-15pc-gum}"  # its pyulog reads the core's sample log back
python=()
[ -x "$venv/bin/python" ] && python=(-DPython3_EXECUTABLE="$venv/bin/python")
cmake -S "$here/firmware" -B "$HOME/build/fw" -DCMAKE_BUILD_TYPE=Debug "${python[@]}"
cmake --build "$HOME/build/fw" -j "$jobs"
cmake -S "$here/firmware" -B "$HOME/build/fw-sitl" -DCMAKE_BUILD_TYPE=Release \
  -DPCS14_SITL=ON -DPCS14_SANITIZE=OFF
cmake --build "$HOME/build/fw-sitl" -j "$jobs" --target pcs14_sitl pcs14_monitor_sitl
ctest --test-dir "$HOME/build/fw" --output-on-failure
echo "pcs14_sitl: $HOME/build/fw-sitl/sitl/pcs14_sitl"
