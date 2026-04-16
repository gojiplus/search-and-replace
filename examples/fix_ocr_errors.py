#!/usr/bin/env python3
"""Example: Fix OCR errors using multiple correction methods."""

from search_and_replace import OCRCorrector, PatternCorrector, SpellCorrector

ocr_text = """
The Netwxrk Administrator confirmed that the systxm is Avxilable.
He11o W0rld - this has 0CR nurnber confusions.
"""

print("=== Original ===")
print(ocr_text)

# 1. OCR confusion correction (0→O, 1→l, rn→m)
print("=== After OCR Correction ===")
ocr = OCRCorrector()
step1 = ocr.correct(ocr_text)
print(step1)

# 2. Spell correction (Levenshtein)
print("=== After Spell Correction ===")
spell = SpellCorrector()
step2 = spell.correct_text(step1)
print(step2)

# 3. Pattern matching (Hyperscan)
print("=== After Pattern Correction ===")
patterns = PatternCorrector([("Network", 1), ("system", 1), ("Available", 1)])
step3 = patterns.correct(step2)
print(step3)

# 4. Custom spell checker
print("=== Custom SpellCorrector Demo ===")
custom = SpellCorrector(words=["network", "available"])
print(f"'Netwxrk' -> '{custom.correct('Netwxrk')}'")
