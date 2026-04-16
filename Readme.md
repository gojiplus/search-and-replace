# search-and-replace

[![CI](https://github.com/soodoku/search-and-replace/actions/workflows/ci.yml/badge.svg)](https://github.com/soodoku/search-and-replace/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/search-and-replace.svg)](https://badge.fury.io/py/search-and-replace)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

High-performance search and replace using [Hyperscan](https://github.com/intel/hyperscan) for multi-pattern matching.

## Installation

Requires Hyperscan system library:

```bash
# macOS (ARM)
brew install vectorscan

# macOS (Intel)
brew install hyperscan

# Ubuntu/Debian
apt-get install libhyperscan-dev
```

Then install the package:

```bash
pip install search-and-replace
```

## Quick Start

### Command Line

```bash
# Process directory with word list
search-and-replace ./input -o ./output -w wordlist.csv

# With replacements and verbose output
search-and-replace ./input -w wordlist.csv -r replacelist.csv -v

# Custom file pattern and worker count
search-and-replace ./input -p "*.txt" -j 8
```

### Python API

```python
from pathlib import Path
from search_and_replace import (
    HyperscanWordList,
    ReplacementList,
    load_wordlist,
    process_directory,
)

# Fix OCR errors in text
wordlist = HyperscanWordList([
    ("Network", 1),    # matches "Netwxrk", "Netvork", etc.
    ("Available", 1),  # matches "Avxilable", "Availxble", etc.
])

text = "The Netwxrk is Avxilable"
fixed = wordlist.apply(text)
# "The Network is Available"

# Direct replacements
replacelist = ReplacementList([
    ("teh", "the"),
    ("recieve", "receive"),
])
fixed = replacelist.apply("I recieve teh package")
# "I receive the package"

# Process entire directory
words = load_wordlist(Path("wordlist.csv"))
processed, skipped = process_directory(
    Path("./input"),
    Path("./output"),
    wordlist_data=words,
    jobs=4,
)
```

## File Formats

### wordlist.csv

Word and max character errors per line:

```csv
Network,1
Available,1
Program,2
```

### replacelist.csv

Search and replace pairs:

```csv
Networtt,Network
marlcets,markets
teh,the
```

## CLI Options

```
search-and-replace [-h] [--version] [-o OUTDIR] [-w WORDLIST]
                   [-r REPLACELIST] [--resume] [-v] [-p PATTERN]
                   [-j JOBS] source_dir

  source_dir          Source directory
  -o, --outdir        Output directory (default: postprocessed)
  -w, --wordlist      Word list CSV (default: wordlist.csv)
  -r, --replacelist   Replacement list CSV (default: replacelist.csv)
  --resume            Skip existing output files
  -v, --verbose       Verbose output
  -p, --pattern       File glob pattern (default: *.txt)
  -j, --jobs          Worker count (default: CPU count)
```

## Use Case: OCR Post-Processing

Designed for cleaning OCR output:

- "Netwxrk" → "Network" (character error)
- "hy-\nphen" → "hyphen" (cross-line splits)
- "marlcets" → "markets" (known OCR errors)

## License

MIT
