#!/usr/bin/env python3
"""Example: Fix common OCR errors in text."""

from search_and_replace import HyperscanWordList, ReplacementList

# Simulated OCR output with errors
ocr_text = """
The Netwxrk Administrator confirmed that the systxm is now Avxilable.
Users can accxss the Prxgram through the main portxl.
Contact support if you recieve any error messxges.
"""

# Fuzzy matching for single-character OCR errors
# Format: (correct_word, max_errors)
wordlist = HyperscanWordList([
    ("Network", 1),
    ("system", 1),
    ("Available", 1),
    ("access", 1),
    ("Program", 1),
    ("portal", 1),
    ("messages", 1),
])

# Direct replacements for known OCR mistakes
replacelist = ReplacementList([
    ("recieve", "receive"),
])

# Apply corrections
fixed = wordlist.apply(ocr_text)
fixed = replacelist.apply(fixed)

print("=== Original (OCR output) ===")
print(ocr_text)
print("=== Fixed ===")
print(fixed)
