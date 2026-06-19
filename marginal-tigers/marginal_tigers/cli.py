"""Command-line interface for marginal_tigers.

Exposes the ``marginal`` console command (see ``[project.scripts]`` in
``pyproject.toml``).
"""

import argparse
import sys
from typing import Optional, Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="marginal",
        description="marginal_tigers command-line interface.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    hello = subparsers.add_parser("hello", help="Print a greeting.")
    hello.add_argument(
        "name",
        nargs="?",
        default="world",
        help="Who to greet (default: world).",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "hello":
        print(f"Hello, {args.name}!")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
