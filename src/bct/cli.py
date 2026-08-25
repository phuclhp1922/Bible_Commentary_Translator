"""Command-line entry point.

The goal this exists to serve: after `pip install -e .`, a chapter can be
translated from a terminal, with no Colab session and no notebook.

    bct translate "Hebrews 12"

Not implemented yet -- the pipeline still lives in the notebooks. This stub
holds the shape so the console-script entry point in pyproject.toml resolves.
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bct", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    translate = sub.add_parser("translate", help="translate one chapter")
    translate.add_argument("reference", help='e.g. "Hebrews 12"')
    translate.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raise SystemExit(f"'{args.command}' is not implemented yet")


if __name__ == "__main__":
    raise SystemExit(main())
