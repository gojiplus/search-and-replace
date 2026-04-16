"""Tests for batch processing."""

from __future__ import annotations

from pathlib import Path

import pytest

from search_and_replace import load_patterns, load_replacements, process_directory


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_input_dir(tmp_path: Path) -> Path:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "test1.txt").write_text("Test file one.\n\nBlank lines.", encoding="utf-8")
    subdir = input_dir / "subdir"
    subdir.mkdir()
    (subdir / "test2.txt").write_text("Word with hy-\nphen here.", encoding="utf-8")
    return input_dir


class TestLoadPatterns:
    def test_loads_csv(self, fixtures_dir: Path) -> None:
        patterns = load_patterns(fixtures_dir / "wordlist.csv")
        assert len(patterns) > 0
        assert all(isinstance(p, tuple) and len(p) == 2 for p in patterns)

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_patterns(tmp_path / "nonexistent.csv")


class TestLoadReplacements:
    def test_loads_csv(self, fixtures_dir: Path) -> None:
        replacements = load_replacements(fixtures_dir / "replacelist.csv")
        assert len(replacements) > 0

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_replacements(tmp_path / "nonexistent.csv")


class TestProcessDirectory:
    def test_processes_files(self, temp_input_dir: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        processed, skipped = process_directory(temp_input_dir, output_dir)
        assert processed == 2
        assert skipped == 0
        assert (output_dir / "test1.txt").exists()
        assert (output_dir / "subdir" / "test2.txt").exists()

    def test_with_patterns(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.txt").write_text("Netwxrk error", encoding="utf-8")
        output_dir = tmp_path / "output"

        processed, _ = process_directory(
            input_dir, output_dir, pattern_data=[("Network", 1)], jobs=1
        )

        assert processed == 1
        content = (output_dir / "test.txt").read_text(encoding="utf-8")
        assert "Network" in content

    def test_resume_mode(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.txt").write_text("New", encoding="utf-8")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "test.txt").write_text("Existing", encoding="utf-8")

        processed, skipped = process_directory(input_dir, output_dir, resume=True, jobs=1)

        assert processed == 0
        assert skipped == 1
        assert (output_dir / "test.txt").read_text() == "Existing"

    def test_empty_directory(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        processed, skipped = process_directory(input_dir, output_dir)
        assert processed == 0
        assert skipped == 0
