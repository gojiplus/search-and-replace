"""High-performance text post-processing with Hyperscan-based pattern matching."""

from __future__ import annotations

import logging
import mmap
import os
import re
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from search_and_replace.hyperscan_engine import HyperscanWordList

logger = logging.getLogger(__name__)

LARGE_FILE_THRESHOLD = 100 * 1024 * 1024

_worker_wordlist: HyperscanWordList | None = None
_worker_replacelist: ReplacementList | None = None


class ReplacementList:
    """Direct string replacements."""

    def __init__(self, replacements: Sequence[tuple[str, str]]) -> None:
        self._patterns: list[tuple[re.Pattern[str], str]] = []
        for search, replace in replacements:
            self._patterns.append((re.compile(re.escape(search), re.UNICODE), replace))

    def apply(self, text: str) -> str:
        """Apply all replacements."""
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text


_BLANK_LINE_PATTERN = re.compile(r"^\s*\r?\n?", re.MULTILINE)
_HYPHEN_PATTERN = re.compile(r"([A-Za-z])[-\u00ad][\r\n]+", re.UNICODE)


def load_wordlist(path: Path) -> list[tuple[str, int]]:
    """Load word list CSV: word,max_errors per line."""
    words: list[tuple[str, int]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 1)
            word = parts[0].strip()
            if not word:
                continue
            try:
                max_errors = int(parts[1].strip()) if len(parts) > 1 else 2
            except ValueError:
                max_errors = 2
            words.append((word, max_errors))
    return words


def load_replacelist(path: Path) -> list[tuple[str, str]]:
    """Load replacement list CSV: search,replace per line."""
    replacements: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "," in line:
                parts = line.split(",", 1)
            elif ";" in line:
                parts = line.split(";", 1)
            else:
                continue
            if len(parts) == 2:
                search, replace = parts[0].strip(), parts[1].strip()
                if search:
                    replacements.append((search, replace))
    return replacements


def _process_text(
    text: str,
    wordlist: HyperscanWordList | None,
    replacelist: ReplacementList | None,
) -> str:
    """Process text: remove blank lines, hyphens, apply replacements."""
    text = _BLANK_LINE_PATTERN.sub("", text)
    text = _HYPHEN_PATTERN.sub(r"\1", text)
    if replacelist:
        text = replacelist.apply(text)
    if wordlist:
        text = wordlist.apply(text)
    return text


def _read_file(path: Path) -> str:
    """Read file, using mmap for large files."""
    file_size = path.stat().st_size
    if file_size == 0:
        return ""
    if file_size > LARGE_FILE_THRESHOLD:
        with path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return mm[:].decode("utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def _process_file(
    input_path: Path,
    output_path: Path,
    wordlist: HyperscanWordList | None,
    replacelist: ReplacementList | None,
    resume: bool,
) -> bool:
    """Process single file. Returns True if processed, False if skipped."""
    if resume and output_path.exists() and output_path.stat().st_size > 0:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = _read_file(input_path)
    processed = _process_text(text, wordlist, replacelist)
    output_path.write_text(processed, encoding="utf-8")
    return True


def _init_worker(
    wordlist_data: Sequence[tuple[str, int]] | None,
    replacelist_data: Sequence[tuple[str, str]] | None,
) -> None:
    """Initialize worker with compiled patterns."""
    global _worker_wordlist, _worker_replacelist
    _worker_wordlist = HyperscanWordList(wordlist_data) if wordlist_data else None
    _worker_replacelist = ReplacementList(replacelist_data) if replacelist_data else None


def _worker_task(
    input_path: Path,
    output_path: Path,
    resume: bool,
) -> tuple[Path, bool]:
    """Worker function for parallel processing."""
    was_processed = _process_file(
        input_path, output_path, _worker_wordlist, _worker_replacelist, resume
    )
    return input_path, was_processed


def process_directory(
    input_dir: Path,
    output_dir: Path,
    wordlist_data: Sequence[tuple[str, int]] | None = None,
    replacelist_data: Sequence[tuple[str, str]] | None = None,
    *,
    pattern: str = "*.txt",
    resume: bool = False,
    jobs: int | None = None,
) -> tuple[int, int]:
    """Process all matching files in parallel.

    Args:
        input_dir: Source directory.
        output_dir: Destination directory.
        wordlist_data: List of (word, max_errors) tuples.
        replacelist_data: List of (search, replace) tuples.
        pattern: Glob pattern (default: *.txt).
        resume: Skip existing output files.
        jobs: Worker count (default: CPU count).

    Returns:
        (processed_count, skipped_count)
    """
    files = list(input_dir.rglob(pattern))
    if not files:
        return 0, 0

    jobs = jobs or os.cpu_count() or 1
    tasks = [(inp, output_dir / inp.relative_to(input_dir)) for inp in files]

    processed, skipped = 0, 0
    with ProcessPoolExecutor(
        max_workers=jobs,
        initializer=_init_worker,
        initargs=(wordlist_data, replacelist_data),
    ) as executor:
        futures = {executor.submit(_worker_task, inp, out, resume): inp for inp, out in tasks}
        for future in as_completed(futures):
            _, was_processed = future.result()
            if was_processed:
                processed += 1
            else:
                skipped += 1

    return processed, skipped
