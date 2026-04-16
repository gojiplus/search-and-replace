"""Tests for correctors."""

from __future__ import annotations

from search_and_replace import OCRCorrector, PatternCorrector, Replacer, SpellCorrector


class TestSpellCorrector:
    def test_with_custom_words(self) -> None:
        c = SpellCorrector(words=["hello", "world"])
        assert c.correct("helo") == "hello"

    def test_with_bundled_dictionary(self) -> None:
        c = SpellCorrector()
        result = c.correct("helo")
        assert result in ("hello", "help")

    def test_preserves_capitalization(self) -> None:
        c = SpellCorrector(words=["hello"])
        assert c.correct("Helo") == "Hello"

    def test_correct_text(self) -> None:
        c = SpellCorrector(words=["the", "quick", "brown"])
        result = c.correct_text("teh quikc brwon")
        assert "the" in result or "quick" in result

    def test_no_match(self) -> None:
        c = SpellCorrector(words=["hello"], max_distance=1)
        assert c.correct("xxxxx") == "xxxxx"


class TestOCRCorrector:
    def test_zero_to_o(self) -> None:
        c = OCRCorrector()
        assert c.correct("W0rld") == "WOrld"

    def test_one_to_l(self) -> None:
        c = OCRCorrector()
        assert c.correct("He11o") == "Hello"

    def test_rn_to_m(self) -> None:
        c = OCRCorrector()
        assert c.correct("corning") == "coming"

    def test_preserves_normal(self) -> None:
        c = OCRCorrector()
        assert c.correct("hello") == "hello"


class TestPatternCorrector:
    def test_single_char_error(self) -> None:
        c = PatternCorrector([("Available", 1)])
        assert "Available" in c.correct("Avxilable")

    def test_multiple_patterns(self) -> None:
        c = PatternCorrector([("Network", 1), ("Program", 1)])
        result = c.correct("Netwxrk and Proxram")
        assert "Network" in result
        assert "Program" in result

    def test_empty_patterns(self) -> None:
        c = PatternCorrector([])
        assert c.correct("hello") == "hello"

    def test_empty_text(self) -> None:
        c = PatternCorrector([("Test", 1)])
        assert c.correct("") == ""


class TestReplacer:
    def test_simple(self) -> None:
        r = Replacer([("foo", "bar")])
        assert r.correct("foo baz") == "bar baz"

    def test_multiple(self) -> None:
        r = Replacer([("foo", "bar"), ("baz", "qux")])
        assert r.correct("foo and baz") == "bar and qux"

    def test_empty(self) -> None:
        r = Replacer([])
        assert r.correct("unchanged") == "unchanged"
