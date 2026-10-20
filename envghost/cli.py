"""Command-line interface for envghost."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scanner import DEFAULT_ENV_FILES, DEFAULT_EXCLUDE_DIRS, scan


def format_text(result: dict[str, object]) -> str:
    lines = [
        "envghost: "
        f"{len(result['env_files'])} env file(s), "
        f"{len(result['declared'])} declaration(s), "
        f"{len(result['referenced'])} reference(s)",
    ]

    unused = result["unused"]
    missing = result["missing"]

    if unused:
        lines.append("Unused environment variables (declared but not referenced):")
        lines.extend(f"  - {key}" for key in unused)
    else:
        lines.append("No unused environment variables.")

    if missing:
        lines.append("Missing environment variables (referenced but not declared):")
        lines.extend(f"  - {key}" for key in missing)
    else:
        lines.append("No missing environment variables.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envghost",
        description="Find environment variables that are declared but unused, or used but undeclared.",
    )
    parser.add_argument("path", nargs="?", default=".", help="project root to scan")
    parser.add_argument(
        "--env-file",
        action="append",
        dest="env_files",
        metavar="NAME",
        help="env file name to scan; may be repeated",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="directory name to exclude; may be repeated",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument(
        "--fail-on",
        choices=("none", "unused", "missing", "any"),
        default="any",
        help="which findings make the command exit with status 1",
    )

    args = parser.parse_args(argv)
    env_files = args.env_files or list(DEFAULT_ENV_FILES)
    excluded = set(DEFAULT_EXCLUDE_DIRS) | set(args.exclude)
    result = scan(args.path, env_files, excluded)

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_text(result))

    should_fail = False
    if args.fail_on in ("unused", "any") and result["unused"]:
        should_fail = True
    if args.fail_on in ("missing", "any") and result["missing"]:
        should_fail = True

    return 1 if should_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())