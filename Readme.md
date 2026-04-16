# search-and-replace

[![CI](https://github.com/soodoku/search-and-replace/actions/workflows/ci.yml/badge.svg)](https://github.com/soodoku/search-and-replace/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/search-and-replace)](https://pypi.org/project/search-and-replace/)
[![Downloads](https://static.pepy.tech/badge/search-and-replace)](https://pepy.tech/project/search-and-replace)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://soodoku.github.io/search-and-replace/)

High-performance text correction for OCR output using [Hyperscan](https://github.com/intel/hyperscan) and [SymSpell](https://github.com/wolfgarbe/SymSpell).

## Installation

Requires Hyperscan system library:

```bash
# macOS
brew install vectorscan  # ARM
brew install hyperscan   # Intel

# Ubuntu/Debian
apt-get install libhyperscan-dev
```

Then:

```bash
pip install search-and-replace
```

## Quick Start

```python
from search_and_replace import SpellCorrector, OCRCorrector, PatternCorrector

# Fix common OCR confusions (0→O, 1→l, rn→m)
ocr = OCRCorrector()
ocr.correct("He11o W0rld")  # "Hello WOrld"

# Spell correction with bundled dictionary
spell = SpellCorrector()
spell.correct("helo")  # "hello"

# Pattern matching with Hyperscan (fast multi-pattern)
patterns = PatternCorrector([("Network", 1), ("Available", 1)])
patterns.correct("The Netwxrk is Avxilable")  # "The Network is Available"
```

## API

| Class | Description |
|-------|-------------|
| `SpellCorrector` | Levenshtein-based correction (bundled dictionary or custom words) |
| `OCRCorrector` | Fix common OCR character confusions |
| `PatternCorrector` | Hyperscan-based multi-pattern matching |
| `Replacer` | Direct string replacement |

| Function | Description |
|----------|-------------|
| `process_directory()` | Batch process files in parallel |
| `load_patterns()` | Load word,max_errors CSV |
| `load_replacements()` | Load search,replace CSV |

## CLI

```bash
search-and-replace ./input -o ./output --patterns wordlist.csv
search-and-replace ./input --patterns patterns.csv --replacements replacements.csv -v -j 8
```

## OCR Corrections

| OCR Error | Fixed |
|-----------|-------|
| 0 | O |
| 1, l, I | l |
| rn | m |
| cl | d |
| vv | w |

## License

MIT
