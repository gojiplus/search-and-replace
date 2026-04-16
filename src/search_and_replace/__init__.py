"""High-performance search and replace for text files."""

from search_and_replace.hyperscan_engine import HyperscanWordList
from search_and_replace.postprocess import (
    ReplacementList,
    load_replacelist,
    load_wordlist,
    process_directory,
)

__version__ = "0.4.0"
__all__ = [
    "HyperscanWordList",
    "ReplacementList",
    "__version__",
    "load_replacelist",
    "load_wordlist",
    "process_directory",
]
