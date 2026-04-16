search-and-replace
==================

High-performance search and replace for text files using regular expressions and edit distance.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api

Installation
------------

.. code-block:: bash

   pip install search-and-replace

Or with uv:

.. code-block:: bash

   uv add search-and-replace

Quick Start
-----------

Command Line
^^^^^^^^^^^^

Process all text files in a directory:

.. code-block:: bash

   search-and-replace txt_dir -o output_dir

With custom word lists:

.. code-block:: bash

   search-and-replace txt_dir -w wordlist.csv -r replacelist.csv -v

Python API
^^^^^^^^^^

.. code-block:: python

   from search_and_replace import (
       CompiledWordList,
       CompiledReplaceList,
       load_wordlist,
       load_replacelist,
       process_text,
   )

   # Load and compile word lists
   words = load_wordlist(Path("wordlist.csv"))
   wordlist = CompiledWordList(words)

   replacements = load_replacelist(Path("replacelist.csv"))
   replacelist = CompiledReplaceList(replacements)

   # Process text
   result = process_text(text, wordlist, replacelist)

Features
--------

- **Blank line removal**: Cleans up extra whitespace
- **Hyphen handling**: Joins words split across lines
- **Direct replacement**: Fast exact string matching from CSV lists
- **Fuzzy matching**: Regex-based correction with configurable error tolerance

File Formats
------------

wordlist.csv
^^^^^^^^^^^^

Each line contains a word and the maximum number of character errors to tolerate:

.. code-block:: text

   Network,1
   Program,2
   Available,1

replacelist.csv
^^^^^^^^^^^^^^^

Each line contains a search term and its replacement, comma or semicolon separated:

.. code-block:: text

   Networtt,Network
   marlcets,markets

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
