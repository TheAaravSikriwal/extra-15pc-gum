"""The CAD layer: the picked drone built as solids in build123d, for every module combination.

build123d takes a while to import (OpenCascade is big), so nothing outside this package
imports it, and the command line only reaches in here when a CAD command runs.
"""
