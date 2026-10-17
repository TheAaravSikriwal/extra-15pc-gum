"""The `pcs14` command. The size, sweep and report commands arrive with task 14 of the plan."""

import argparse

from pcs14 import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcs14",
        description="14 pcs left: design and simulation tools for the Extra 15pc Gum drone.",
    )
    parser.add_argument("--version", action="version", version=f"pcs14 {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
