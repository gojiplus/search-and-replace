"""Tests for search_and_replace."""

from __future__ import annotations

from pathlib import Path

import pytest

from search_and_replace import (
    HyperscanWordList,
    ReplacementList,
    load_replacelist,
    load_wordlist,
    process_directory,
)


class TestHyperscanWordList:
    def test_corrects_single_char_error(self) -> None:
        words = [("Available", 1)]
        wordlist = HyperscanWordList(words)
        result = wordlist.apply("This is Avxilable now")
        assert "Available" in result

    def test_handles_multiple_words(self) -> None:
        words = [("Network", 1), ("Program", 1)]
        wordlist = HyperscanWordList(words)
        result = wordlist.apply("Netwxrk and Proxram")
        assert "Network" in result
        assert "Program" in result

    def test_respects_error_tolerance(self) -> None:
        words = [("Test", 1)]
        wordlist = HyperscanWordList(words)
        text = "Txxt should not match"
        result = wordlist.apply(text)
        assert result == text

    def test_empty_wordlist(self) -> None:
        words: list[tuple[str, int]] = []
        wordlist = HyperscanWordList(words)
        result = wordlist.apply("Original text")
        assert result == "Original text"

    def test_empty_text(self) -> None:
        words = [("Test", 1)]
        wordlist = HyperscanWordList(words)
        assert wordlist.apply("") == ""

    def test_unicode(self) -> None:
        words = [("résumé", 1)]
        wordlist = HyperscanWordList(words)
        result = wordlist.apply("Submit your résxmé here")
        assert "résumé" in result


class TestReplacementList:
    def test_direct_replacement(self) -> None:
        replacements = [("foo", "bar")]
        replacelist = ReplacementList(replacements)
        assert replacelist.apply("foo baz") == "bar baz"

    def test_multiple_replacements(self) -> None:
        replacements = [("foo", "bar"), ("baz", "qux")]
        replacelist = ReplacementList(replacements)
        assert replacelist.apply("foo and baz") == "bar and qux"

    def test_empty(self) -> None:
        replacelist = ReplacementList([])
        assert replacelist.apply("unchanged") == "unchanged"


class TestLoadWordlist:
    def test_loads_csv(self, sample_wordlist: Path) -> None:
        words = load_wordlist(sample_wordlist)
        assert len(words) > 0
        assert all(isinstance(w, tuple) and len(w) == 2 for w in words)

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_wordlist(tmp_path / "nonexistent.csv")


class TestLoadReplacelist:
    def test_loads_csv(self, sample_replacelist: Path) -> None:
        replacements = load_replacelist(sample_replacelist)
        assert len(replacements) > 0

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_replacelist(tmp_path / "nonexistent.csv")


class TestProcessDirectory:
    def test_processes_files(self, temp_input_dir: Path, temp_output_dir: Path) -> None:
        processed, skipped = process_directory(temp_input_dir, temp_output_dir)
        assert processed == 2
        assert skipped == 0
        assert (temp_output_dir / "test1.txt").exists()
        assert (temp_output_dir / "subdir" / "test2.txt").exists()

    def test_with_wordlist(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.txt").write_text("Netwxrk error", encoding="utf-8")
        output_dir = tmp_path / "output"

        words = [("Network", 1)]
        processed, _ = process_directory(input_dir, output_dir, wordlist_data=words, jobs=1)

        assert processed == 1
        content = (output_dir / "test.txt").read_text(encoding="utf-8")
        assert "Network" in content

    def test_with_replacelist(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.txt").write_text("foo bar", encoding="utf-8")
        output_dir = tmp_path / "output"

        replacements = [("foo", "baz")]
        processed, _ = process_directory(
            input_dir, output_dir, replacelist_data=replacements, jobs=1
        )

        assert processed == 1
        content = (output_dir / "test.txt").read_text(encoding="utf-8")
        assert "baz bar" in content

    def test_resume_mode(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.txt").write_text("New content", encoding="utf-8")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "test.txt").write_text("Existing content", encoding="utf-8")

        processed, skipped = process_directory(input_dir, output_dir, resume=True, jobs=1)

        assert processed == 0
        assert skipped == 1
        assert (output_dir / "test.txt").read_text(encoding="utf-8") == "Existing content"

    def test_empty_directory(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        processed, skipped = process_directory(input_dir, output_dir, jobs=1)

        assert processed == 0
        assert skipped == 0

    def test_custom_pattern(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "file.txt").write_text("txt", encoding="utf-8")
        (input_dir / "file.md").write_text("md", encoding="utf-8")
        output_dir = tmp_path / "output"

        processed, _ = process_directory(input_dir, output_dir, pattern="*.md", jobs=1)

        assert processed == 1
        assert (output_dir / "file.md").exists()
        assert not (output_dir / "file.txt").exists()
