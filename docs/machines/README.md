# docs/machines/

What each machine has, and whether the project's checks pass on it. When a machine gets new tools installed, rerun the check and commit the new report.

| File | Machine | How it's made |
|---|---|---|
| `pc.md` | The PC (Ubuntu 24.04), the main machine | `scripts/check-machine.sh pc` |
| [laptop-wsl.md](laptop-wsl.md) | The laptop's WSL (Ubuntu 24.04) | `scripts/check-machine.sh laptop-wsl` |
| [laptop-windows.md](laptop-windows.md) | The laptop's Windows side | By hand |

Setting up the PC from scratch: [../setup-pc.md](../setup-pc.md).
