"""High-performance multi-pattern matching using Intel Hyperscan.

This module provides an alternative to the regex-based CompiledWordList
that uses Hyperscan to scan text once for all patterns simultaneously.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import hyperscan

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Match:
    """Represents a single pattern match with replacement info."""

    pattern_id: int
    start: int
    end: int
    replacement: str


class HyperscanWordList:
    """Hyperscan-based word list for high-performance multi-pattern matching.

    Compiles all patterns into a single Hyperscan database and scans text
    once to find all matches, then applies replacements.

    Args:
        words: Sequence of (word, max_errors) tuples where max_errors is the
            maximum number of consecutive character errors to tolerate.

    """

    def __init__(self, words: Sequence[tuple[str, int]]) -> None:
        self._db: Any = None
        self._replacements: dict[int, str] = {}
        self._patterns_info: dict[int, str] = {}
        self._compile_patterns(words)

    def _compile_patterns(self, words: Sequence[tuple[str, int]]) -> None:
        """Compile all patterns into a single Hyperscan database.

        Args:
            words: Sequence of (word, max_errors) tuples.
        """
        patterns: list[bytes] = []
        ids: list[int] = []
        flags_list: list[int] = []
        pattern_id = 0

        for word, max_errors in words:
            word = word.strip("\ufeff")
            for i in range(1, len(word) - 1):
                prefix = re.escape(word[:i])
                suffix = re.escape(word[i + 1 :])
                error_pattern = rf".{{0,{max_errors}}}\??[\r\n]*"
                regex = prefix + error_pattern + suffix

                patterns.append(regex.encode("utf-8"))
                ids.append(pattern_id)
                flags_list.append(
                    hyperscan.HS_FLAG_CASELESS
                    | hyperscan.HS_FLAG_DOTALL
                    | hyperscan.HS_FLAG_SOM_LEFTMOST
                )
                self._replacements[pattern_id] = word
                self._patterns_info[pattern_id] = regex
                pattern_id += 1

        if patterns:
            self._db = hyperscan.Database()
            self._db.compile(
                expressions=patterns,
                ids=ids,
                flags=flags_list,
            )

    def _collect_matches(self, text_bytes: bytes) -> list[Match]:
        """Scan text once and collect all matches.

        Args:
            text_bytes: Text encoded as UTF-8 bytes.

        Returns:
            List of Match objects with byte offsets.
        """
        matches: list[Match] = []

        def on_match(pid: int, from_: int, to: int, _flags: int, ctx: list[Match]) -> None:
            ctx.append(Match(pid, from_, to, self._replacements[pid]))

        if self._db:
            self._db.scan(text_bytes, match_event_handler=on_match, context=matches)

        return matches

    def _byte_to_char_offsets(self, text: str, matches: list[Match]) -> list[Match]:
        """Convert Hyperscan byte offsets to Python string character offsets.

        Args:
            text: Original text string.
            matches: List of matches with byte offsets.

        Returns:
            List of matches with character offsets.
        """
        byte_to_char: list[int] = []
        for i, char in enumerate(text):
            byte_to_char.extend([i] * len(char.encode("utf-8")))
        byte_to_char.append(len(text))

        return [
            Match(m.pattern_id, byte_to_char[m.start], byte_to_char[m.end], m.replacement)
            for m in matches
        ]

    def _resolve_overlaps(self, matches: list[Match]) -> list[Match]:
        """Resolve overlapping matches using greedy selection.

        Strategy: Earlier start wins; for ties, longer match wins.

        Args:
            matches: List of potentially overlapping matches.

        Returns:
            List of non-overlapping matches.
        """
        if not matches:
            return []

        sorted_matches = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
        result: list[Match] = []
        last_end = -1

        for m in sorted_matches:
            if m.start >= last_end:
                result.append(m)
                last_end = m.end

        return result

    def apply(self, text: str, verbose: bool = False) -> str:
        """Apply all replacement patterns to the text.

        Args:
            text: The input text to process.
            verbose: If True, log replacement statistics.

        Returns:
            The processed text with all replacements applied.
        """
        if not self._db or not text:
            return text

        text_bytes = text.encode("utf-8")
        matches = self._collect_matches(text_bytes)

        if not matches:
            return text

        matches = self._byte_to_char_offsets(text, matches)
        matches = self._resolve_overlaps(matches)

        replacement_counts: dict[str, int] = {}

        for m in sorted(matches, key=lambda x: -x.start):
            text = text[: m.start] + m.replacement + text[m.end :]

            if verbose:
                key = f"{self._patterns_info[m.pattern_id]} ==> {m.replacement}"
                replacement_counts[key] = replacement_counts.get(key, 0) + 1

        if verbose:
            for pattern_info, count in replacement_counts.items():
                logger.info("PP hyperscan(%d): %s", count, pattern_info)

        return text
