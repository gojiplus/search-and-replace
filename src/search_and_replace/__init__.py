"""High-performance text correction for OCR output."""

from search_and_replace.batch import load_patterns, load_replacements, process_directory
from search_and_replace.correctors import (
    OCRCorrector,
    PatternCorrector,
    Replacer,
    SpellCorrector,
)

__version__ = "0.4.0"
__all__ = [
    "OCRCorrector",
    "PatternCorrector",
    "Replacer",
    "SpellCorrector",
    "__version__",
    "load_patterns",
    "load_replacements",
    "process_directory",
]
