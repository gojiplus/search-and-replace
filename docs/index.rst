search-and-replace
==================

High-performance text correction for OCR output using Hyperscan and SymSpell.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api

Installation
------------

Requires Hyperscan system library:

.. code-block:: bash

   # macOS
   brew install vectorscan  # ARM
   brew install hyperscan   # Intel

   # Ubuntu/Debian
   apt-get install libhyperscan-dev

Then install via pip:

.. code-block:: bash

   pip install search-and-replace

Quick Start
-----------

.. code-block:: python

   from search_and_replace import SpellCorrector, OCRCorrector, PatternCorrector

   # Fix common OCR confusions (0→O, 1→l, rn→m)
   ocr = OCRCorrector()
   ocr.correct("He11o W0rld")  # "Hello WOrld"

   # Spell correction with bundled dictionary
   spell = SpellCorrector()
   spell.correct("helo")  # "hello"

   # Pattern matching with Hyperscan
   patterns = PatternCorrector([("Network", 1), ("Available", 1)])
   patterns.correct("The Netwxrk is Avxilable")  # "The Network is Available"

CLI
---

.. code-block:: bash

   search-and-replace ./input -o ./output --patterns wordlist.csv

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
