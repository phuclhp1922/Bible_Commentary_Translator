"""Smoke tests.

Deliberately few. These assert that the package is importable and that the
console-script entry point resolves -- the two things most likely to be
silently broken by a packaging change.
"""

import bct
from bct.cli import build_parser


def test_package_imports():
    assert bct.__version__


def test_subpackages_import():
    for name in (
        "sources", "corpus", "align", "pipeline", "output", "data", "eval",
    ):
        __import__(f"bct.{name}")


def test_cli_parses_a_translate_command():
    args = build_parser().parse_args(["translate", "Hebrews 12"])
    assert args.reference == "Hebrews 12"
