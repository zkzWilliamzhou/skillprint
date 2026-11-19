"""Command line interface for skillprint."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from . import __version__
from .label import LabelError, check, load_skill, render

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillprint",
        description=(
            "Emit a deterministic, pre-install capability label for an "
            "AI agent skill directory. Never performs network calls."
        ),
    )
    parser.add_argument(
        "skill_dir",
        nargs="?",
        default=".",
        help="path to the skill directory containing SKILL.md (default: .)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail (exit 1) if the label is inconsistent or uses undeclared dangerous markers",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="skillprint %s" % __version__,
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        label = load_skill(args.skill_dir)
    except LabelError as exc:
        print("skillprint: error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE_ERROR

    print(render(label, args.format))

    if args.check:
        failures = check(label)
        if failures:
            for failure in failures:
                print("skillprint: check failed: %s" % failure, file=sys.stderr)
            return EXIT_CHECK_FAILED

    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
