#!/usr/bin/env bash
# Get the Python dev environment going on Ubuntu 24.04 (the PC, or WSL),
# then run exactly what CI runs. Safe to rerun.
#
#   scripts/setup-dev.sh
#
# The venv goes in .venv inside the repo (it's gitignored). On the PC the repo
# lives in a normal Linux folder, so that's fine. Set VENV=/some/path to put
# it somewhere else.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
venv="${VENV:-$repo_root/.venv}"

echo "==> System packages"
need=()
python3 -c 'import ensurepip' 2>/dev/null || need+=(python3-venv)
command -v git-lfs >/dev/null 2>&1 || need+=(git-lfs)
if [ ${#need[@]} -gt 0 ]; then
  echo "    Installing ${need[*]} (this needs sudo)"
  sudo apt-get update -qq
  sudo apt-get install -y "${need[@]}"
else
  echo "    Nothing missing"
fi

if git rev-parse --git-dir >/dev/null 2>&1; then
  git lfs install --local >/dev/null
  echo "    Git LFS hooked up for this repo"
fi

echo "==> Python venv at ${venv/#$HOME/\~}"
[ -x "$venv/bin/python" ] || python3 -m venv "$venv"
"$venv/bin/python" -m pip install -q --upgrade pip
"$venv/bin/python" -m pip install -q --group dev
echo "    $("$venv/bin/python" --version), $("$venv/bin/python" -m pip --version | cut -d' ' -f1-2)"

echo "==> Lint (same as CI)"
"$venv/bin/ruff" check .

echo "==> Tests (same as CI)"
"$venv/bin/python" -m pytest -q

echo
echo "All good. Activate the venv with: source ${venv/#$HOME/\~}/bin/activate"
