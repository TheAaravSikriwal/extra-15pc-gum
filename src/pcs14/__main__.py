"""Lets the package run as `python -m pcs14`, same as the `pcs14` command."""

from pcs14.cli import main

raise SystemExit(main())
