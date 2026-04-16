"""Batch file processing and I/O."""

from __future__ import annotations

import mmap
import os
import re
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from search_and_replace.correctors import PatternCorrector, Replacer

LARGE_FILE_THRESHOLD = 100 * 1024 * 1024

_BLANK_LINE_PATTERN = re.compile(r"^\s*\r?\n?", re.MULTILINE)
_HYPHEN_PATTERN = re.compile(r"([A-Za-z])[-\u00ad][\r\n]+", re.UNICODE)

_worker_patterns: PatternCorrector | None = None
_worker_replacer: Replacer | None = None


def load_patterns(path: Path) -> list[tuple[str, int]]:
    """Load pattern list: word,max_errors per line."""
    patterns: list[tuple[str, int]] = []
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
            patterns.append((word, max_errors))
    return patterns


def load_replacements(path: Path) -> list[tuple[str, str]]:
    """Load replacement list: search,replace per line."""
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


def _read_file(path: Path) -> str:
    size = path.stat().st_size
    if size == 0:
        return ""
    if size > LARGE_FILE_THRESHOLD:
        with path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return mm[:].decode("utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def _process_text(
    text: str,
    patterns: PatternCorrector | None,
    replacer: Replacer | None,
) -> str:
    text = _BLANK_LINE_PATTERN.sub("", text)
    text = _HYPHEN_PATTERN.sub(r"\1", text)
    if replacer:
        text = replacer.correct(text)
    if patterns:
        text = patterns.correct(text)
    return text


def _process_file(
    input_path: Path,
    output_path: Path,
    patterns: PatternCorrector | None,
    replacer: Replacer | None,
    resume: bool,
) -> bool:
    if resume and output_path.exists() and output_path.stat().st_size > 0:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = _read_file(input_path)
    processed = _process_text(text, patterns, replacer)
    output_path.write_text(processed, encoding="utf-8")
    return True


def _init_worker(
    pattern_data: Sequence[tuple[str, int]] | None,
    replacement_data: Sequence[tuple[str, str]] | None,
) -> None:
    global _worker_patterns, _worker_replacer
    _worker_patterns = PatternCorrector(pattern_data) if pattern_data else None
    _worker_replacer = Replacer(replacement_data) if replacement_data else None


def _worker_task(input_path: Path, output_path: Path, resume: bool) -> tuple[Path, bool]:
    processed = _process_file(input_path, output_path, _worker_patterns, _worker_replacer, resume)
    return input_path, processed


def process_directory(
    input_dir: Path,
    output_dir: Path,
    pattern_data: Sequence[tuple[str, int]] | None = None,
    replacement_data: Sequence[tuple[str, str]] | None = None,
    *,
    pattern: str = "*.txt",
    resume: bool = False,
    jobs: int | None = None,
) -> tuple[int, int]:
    """Process all matching files in parallel.

    Args:
        input_dir: Source directory.
        output_dir: Destination directory.
        pattern_data: List of (word, max_errors) for PatternCorrector.
        replacement_data: List of (search, replace) for Replacer.
        pattern: Glob pattern (default: *.txt).
        resume: Skip existing output files.
        jobs: Worker count (default: CPU count).

    Returns:
        (processed_count, skipped_count)
    """
    file_list = list(input_dir.rglob(pattern))
    if not file_list:
        return 0, 0

    jobs = jobs or os.cpu_count() or 1
    tasks = [(f, output_dir / f.relative_to(input_dir)) for f in file_list]

    processed, skipped = 0, 0
    with ProcessPoolExecutor(
        max_workers=jobs,
        initializer=_init_worker,
        initargs=(pattern_data, replacement_data),
    ) as executor:
        futures = {executor.submit(_worker_task, inp, out, resume): inp for inp, out in tasks}
        for future in as_completed(futures):
            _, was_processed = future.result()
            if was_processed:
                processed += 1
            else:
                skipped += 1

    return processed, skipped
