"""Pytest fixtures for search-and-replace tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_wordlist(fixtures_dir: Path) -> Path:
    """Return path to sample wordlist.csv."""
    return fixtures_dir / "wordlist.csv"


@pytest.fixture
def sample_replacelist(fixtures_dir: Path) -> Path:
    """Return path to sample replacelist.csv."""
    return fixtures_dir / "replacelist.csv"


@pytest.fixture
def temp_input_dir(tmp_path: Path) -> Path:
    """Create a temporary input directory with sample files."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    (input_dir / "test1.txt").write_text(
        "This is a test file.\n\nWith blank lines.\n\nAnd more text.",
        encoding="utf-8",
    )

    subdir = input_dir / "subdir"
    subdir.mkdir()
    (subdir / "test2.txt").write_text(
        "Word split across\nlines with hy-\nphen here.",
        encoding="utf-8",
    )

    return input_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
