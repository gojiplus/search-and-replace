"""Command-line interface for search-and-replace."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from search_and_replace import __version__
from search_and_replace.postprocess import (
    load_replacelist,
    load_wordlist,
    process_directory,
)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="search-and-replace",
        description="High-performance search and replace for text files",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("source_dir", type=Path, help="Source directory")
    parser.add_argument(
        "-o", "--outdir", type=Path, default=Path("postprocessed"), help="Output directory"
    )
    parser.add_argument(
        "-w", "--wordlist", type=Path, default=Path("wordlist.csv"), help="Word list CSV"
    )
    parser.add_argument(
        "-r",
        "--replacelist",
        type=Path,
        default=Path("replacelist.csv"),
        help="Replacement list CSV",
    )
    parser.add_argument("--resume", action="store_true", help="Skip existing output files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-p", "--pattern", default="*.txt", help="File glob pattern")
    parser.add_argument("-j", "--jobs", type=int, help="Worker count (default: CPU count)")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    if not args.source_dir.is_dir():
        logging.error("Source directory does not exist: %s", args.source_dir)
        return 1

    words = load_wordlist(args.wordlist) if args.wordlist.exists() else None
    replacements = load_replacelist(args.replacelist) if args.replacelist.exists() else None

    if words:
        logging.info("Loaded %d words from %s", len(words), args.wordlist)
    if replacements:
        logging.info("Loaded %d replacements from %s", len(replacements), args.replacelist)

    processed, skipped = process_directory(
        args.source_dir,
        args.outdir,
        words,
        replacements,
        pattern=args.pattern,
        resume=args.resume,
        jobs=args.jobs,
    )

    logging.info("Processed %d files, skipped %d files", processed, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
