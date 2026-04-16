"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from search_and_replace import __version__
from search_and_replace.batch import load_patterns, load_replacements, process_directory


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="search-and-replace",
        description="High-performance text correction for OCR output",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("source_dir", type=Path, help="Source directory")
    parser.add_argument(
        "-o", "--outdir", type=Path, default=Path("postprocessed"), help="Output directory"
    )
    parser.add_argument(
        "-w", "--patterns", type=Path, default=Path("patterns.csv"), help="Patterns CSV"
    )
    parser.add_argument(
        "-r", "--replacements", type=Path, default=Path("replacements.csv"), help="Replacements CSV"
    )
    parser.add_argument("--resume", action="store_true", help="Skip existing files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-p", "--pattern", default="*.txt", help="File glob")
    parser.add_argument("-j", "--jobs", type=int, help="Worker count")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    if not args.source_dir.is_dir():
        logging.error("Source directory does not exist: %s", args.source_dir)
        return 1

    patterns = load_patterns(args.patterns) if args.patterns.exists() else None
    replacements = load_replacements(args.replacements) if args.replacements.exists() else None

    if patterns:
        logging.info("Loaded %d patterns from %s", len(patterns), args.patterns)
    if replacements:
        logging.info("Loaded %d replacements from %s", len(replacements), args.replacements)

    processed, skipped = process_directory(
        args.source_dir,
        args.outdir,
        patterns,
        replacements,
        pattern=args.pattern,
        resume=args.resume,
        jobs=args.jobs,
    )

    logging.info("Processed %d files, skipped %d files", processed, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
