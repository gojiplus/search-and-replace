"""Text correction classes."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import hyperscan
from symspellpy import SymSpell, Verbosity

if TYPE_CHECKING:
    from typing import Any

# OCR confusion pairs
OCR_CONFUSIONS: dict[str, str] = {
    "0": "O",
    "1": "l",
    "|": "l",
    "rn": "m",
    "cl": "d",
    "vv": "w",
    "ii": "u",
    "lj": "y",
}


class SpellCorrector:
    """Levenshtein-based spelling correction using SymSpell.

    Args:
        words: Custom word list. If None and dictionary is None, uses bundled dictionary.
        dictionary: Path to dictionary file (one word per line).
        max_distance: Maximum edit distance (default: 2).
    """

    def __init__(
        self,
        words: list[str] | None = None,
        dictionary: Path | str | None = None,
        max_distance: int = 2,
    ) -> None:
        self.max_distance = max_distance
        self._sym = SymSpell(max_dictionary_edit_distance=max_distance)

        if words is not None:
            for word in words:
                self._sym.create_dictionary_entry(word.lower(), 1)
        elif dictionary is not None:
            self._load_file(Path(dictionary))
        else:
            self._load_bundled()

    def _load_file(self, path: Path) -> None:
        with path.open(encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:
                    self._sym.create_dictionary_entry(word.lower(), 1)

    def _load_bundled(self) -> None:
        data = files("search_and_replace") / "data" / "english_50k.txt"
        with data.open("r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:
                    self._sym.create_dictionary_entry(word.lower(), 1)

    def correct(self, word: str) -> str:
        """Correct a single word."""
        suggestions = self._sym.lookup(
            word.lower(), Verbosity.CLOSEST, max_edit_distance=self.max_distance
        )
        if suggestions:
            corrected: str = suggestions[0].term
            if word and word[0].isupper():
                corrected = corrected.capitalize()
            return corrected
        return word

    def correct_text(self, text: str) -> str:
        """Correct all words in text."""
        tokens = re.findall(r"\b\w+\b|\W+", text)
        return "".join(self.correct(t) if t.isalpha() else t for t in tokens)


class OCRCorrector:
    """Corrects common OCR character confusions (0/O, 1/l, rn/m, etc.)."""

    def correct(self, text: str) -> str:
        """Apply OCR confusion corrections."""
        for wrong, right in OCR_CONFUSIONS.items():
            text = text.replace(wrong, right)
        return text


@dataclass
class _Match:
    pattern_id: int
    start: int
    end: int
    replacement: str


class PatternCorrector:
    """Hyperscan-based pattern matching for fuzzy single-character errors.

    Args:
        patterns: List of (word, max_errors) tuples.
    """

    def __init__(self, patterns: Sequence[tuple[str, int]]) -> None:
        self._db: Any = None
        self._replacements: dict[int, str] = {}
        self._compile(patterns)

    def _compile(self, patterns: Sequence[tuple[str, int]]) -> None:
        expressions: list[bytes] = []
        ids: list[int] = []
        flags: list[int] = []
        pid = 0

        for word, max_errors in patterns:
            word = word.strip("\ufeff")
            if len(word) < 3:
                continue
            for i in range(1, len(word) - 1):
                prefix = re.escape(word[:i])
                suffix = re.escape(word[i + 1 :])
                regex = prefix + rf".{{0,{max_errors}}}\??[\r\n]*" + suffix

                expressions.append(regex.encode("utf-8"))
                ids.append(pid)
                flags.append(
                    hyperscan.HS_FLAG_CASELESS
                    | hyperscan.HS_FLAG_DOTALL
                    | hyperscan.HS_FLAG_SOM_LEFTMOST
                )
                self._replacements[pid] = word
                pid += 1

        if expressions:
            self._db = hyperscan.Database()
            self._db.compile(expressions=expressions, ids=ids, flags=flags)

    def _scan(self, text_bytes: bytes) -> list[_Match]:
        matches: list[_Match] = []

        def on_match(pid: int, start: int, end: int, _flags: int, ctx: list[_Match]) -> None:
            ctx.append(_Match(pid, start, end, self._replacements[pid]))

        if self._db:
            self._db.scan(text_bytes, match_event_handler=on_match, context=matches)
        return matches

    def _byte_to_char(self, text: str, matches: list[_Match]) -> list[_Match]:
        mapping: list[int] = []
        for i, char in enumerate(text):
            mapping.extend([i] * len(char.encode("utf-8")))
        mapping.append(len(text))

        return [
            _Match(
                m.pattern_id, mapping[m.start], mapping[min(m.end, len(mapping) - 1)], m.replacement
            )
            for m in matches
        ]

    def _resolve_overlaps(self, matches: list[_Match]) -> list[_Match]:
        if not matches:
            return []
        sorted_m = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
        result: list[_Match] = []
        last_end = -1
        for m in sorted_m:
            if m.start >= last_end:
                result.append(m)
                last_end = m.end
        return result

    def correct(self, text: str) -> str:
        """Apply pattern corrections."""
        if not self._db or not text:
            return text

        matches = self._scan(text.encode("utf-8"))
        if not matches:
            return text

        matches = self._byte_to_char(text, matches)
        matches = self._resolve_overlaps(matches)

        for m in sorted(matches, key=lambda x: -x.start):
            text = text[: m.start] + m.replacement + text[m.end :]
        return text


class Replacer:
    """Direct string replacement."""

    def __init__(self, replacements: Sequence[tuple[str, str]]) -> None:
        self._patterns: list[tuple[re.Pattern[str], str]] = []
        for search, replace in replacements:
            self._patterns.append((re.compile(re.escape(search), re.UNICODE), replace))

    def correct(self, text: str) -> str:
        """Apply all replacements."""
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text
